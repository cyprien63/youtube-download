import glob
import os
import re
import subprocess
import threading
import time
from typing import Callable, Optional

import yt_dlp

from .utils import log
from .ffmpeg_manager import get_ffmpeg_path

try:
    from pytubefix import YouTube
except ImportError:
    YouTube = None

_SHORTS_RE = re.compile(r'youtube\.com/shorts/([A-Za-z0-9_-]+)')

_YT_CLIENT_STRATEGIES = [
    {
        "label": "android + web",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "player_skip": ["webpage", "configs"],
            }
        },
    },
    {
        "label": "ios",
        "extractor_args": {
            "youtube": {
                "player_client": ["ios"],
                "player_skip": ["webpage", "configs"],
            }
        },
    },
    {
        "label": "web (sans skip)",
        "extractor_args": {
            "youtube": {
                "player_client": ["web"],
                "player_skip": [],
            }
        },
    },
]

RETRY_BACKOFF_SECONDS = 2


class _YtDlpLogger:

    def __init__(self, progress_callback: Callable[[float, Optional[str]], None]) -> None:
        self._progress_callback = progress_callback

    def debug(self, msg: str) -> None:
        self._process_msg(msg)

    def info(self, msg: str) -> None:
        self._process_msg(msg)

    def warning(self, msg: str) -> None:
        log(f"[WARNING] {msg}")

    def error(self, msg: str) -> None:
        log(f"[ERROR] {msg}")

    def _process_msg(self, msg: str) -> None:
        clean = msg.strip()
        if not clean:
            return
        if clean.startswith('[download]'):
            pct = self._extract_pct(clean)
            speed = self._extract_speed(clean)
            eta = self._extract_eta(clean)
            if pct is not None:
                label = self._build_label(pct, speed, eta)
                self._progress_callback(pct / 100, label)
            log(clean)
        elif any(tag in clean for tag in ['[ExtractAudio]', '[Merger]', '[Fixup]', '[VideoConvertor]']):
            self._progress_callback(1.0, "Conversion/Fusion...")
            log(clean)
        else:
            log(clean)

    @staticmethod
    def _extract_pct(text: str) -> Optional[float]:
        try:
            m = re.search(r'(\d+(?:\.\d+)?)%', text)
            return float(m.group(1)) if m else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_speed(text: str) -> Optional[str]:
        m = re.search(r'at\s+([\d.]+\w+/s)', text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_eta(text: str) -> Optional[str]:
        m = re.search(r'ETA\s+(\S+)', text)
        return m.group(1) if m else None

    @staticmethod
    def _build_label(pct: float, speed: Optional[str], eta: Optional[str]) -> str:
        parts = [f"{int(pct)}%"]
        if speed:
            parts.append(speed)
        if eta:
            parts.append(f"ETA {eta}")
        return " | ".join(parts)


def _parse_quality(quality: str) -> int:
    try:
        digits = re.sub(r"[^0-9]", "", quality)
        return int(digits) if digits else 0
    except ValueError:
        return 0


def _is_shorts_url(url: str) -> bool:
    return bool(_SHORTS_RE.search(url))


def _normalize_shorts_url(url: str) -> str:
    m = _SHORTS_RE.search(url)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    return url


def _format_speed(bytes_per_sec: float) -> str:
    if bytes_per_sec > 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.1f} Mo/s"
    elif bytes_per_sec > 1024:
        return f"{bytes_per_sec / 1024:.0f} Ko/s"
    return "..."


class DownloadManager:

    def __init__(self) -> None:
        self._cancel_event = threading.Event()
        self._ydl_instance: Optional[yt_dlp.YoutubeDL] = None

    def cancel(self) -> None:
        self._cancel_event.set()
        ydl = self._ydl_instance
        if ydl is not None:
            try:
                ydl.cancel_download()
            except Exception:
                pass

    def reset_cancel(self) -> None:
        self._cancel_event.clear()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def start_download(
        self,
        url: str,
        path: str,
        mode: str,
        quality: str,
        fmt: str,
        progress_callback: Callable[[float, Optional[str]], None],
    ) -> bool:
        self.reset_cancel()

        if _is_shorts_url(url):
            log("Shorts YouTube detecte, conversion en URL standard...")
            url = _normalize_shorts_url(url)

        log(f"Processus: {mode} | {quality} | {fmt}")
        log(f"Cible: {url}")

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                log(f"Erreur creation dossier: {e}")
                return False

        success = self._download_ytdlp(url, path, mode, quality, fmt, progress_callback)
        if success:
            return True

        if self.is_cancelled:
            return False

        log("Moteur: pytubefix (Secours)...")
        if YouTube is not None:
            try:
                self._download_pytube(url, path, mode, quality, fmt, progress_callback)
                return True
            except Exception as e:
                log(f"[pytubefix] Erreur: {e}")
        else:
            log("[pytubefix] Non disponible.")

        return False

    def _get_ffmpeg_info(self) -> tuple[Optional[str], Optional[str]]:
        ffmpeg_bin = get_ffmpeg_path()
        if ffmpeg_bin is None:
            return None, None
        if ffmpeg_bin == "ffmpeg":
            return ffmpeg_bin, None
        return ffmpeg_bin, os.path.dirname(ffmpeg_bin)

    def _download_ytdlp(
        self,
        url: str,
        path: str,
        mode: str,
        quality: str,
        fmt: str,
        progress_callback: Callable[[float, Optional[str]], None],
    ) -> bool:
        ffmpeg_bin, ffmpeg_dir = self._get_ffmpeg_info()
        has_ffmpeg = ffmpeg_bin is not None
        q_val = _parse_quality(quality)

        if not has_ffmpeg:
            log("ATTENTION: FFmpeg introuvable. Les conversions pourraient echouer.")

        is_playlist_view = "list=" in url and "watch?" not in url and "v=" not in url
        if is_playlist_view:
            log("Mode detecte: Playlist/Album")
        else:
            log("Mode detecte: Video unique")

        for attempt, strategy in enumerate(_YT_CLIENT_STRATEGIES, 1):
            if self.is_cancelled:
                return False

            log(f"Essai {attempt}/{len(_YT_CLIENT_STRATEGIES)}: strategie \"{strategy['label']}\"...")

            pre_files = set(glob.glob(os.path.join(path, '*'))) if os.path.isdir(path) else set()

            opts = self._build_opts(path, is_playlist_view, progress_callback)
            if ffmpeg_dir:
                opts['ffmpeg_location'] = ffmpeg_dir
            opts['extractor_args'] = strategy['extractor_args']

            self._configure_format(opts, mode, fmt, q_val, has_ffmpeg)

            try:
                self._ydl_instance = yt_dlp.YoutubeDL(opts)
                self._ydl_instance.download([url])
                self._ydl_instance = None

                if has_ffmpeg and mode == "Vidéo" and fmt != "mp4":
                    mp4_file = self._find_latest_mp4(path, pre_files)
                    if mp4_file:
                        self._convert_single_video(ffmpeg_bin, mp4_file, fmt, progress_callback)
                    else:
                        log("Aucun fichier MP4 trouve pour la conversion.")

                return True
            except yt_dlp.utils.DownloadError as e:
                self._ydl_instance = None
                if self.is_cancelled:
                    return False
                log(f"[yt-dlp] Echec strategie \"{strategy['label']}\": {e}")
                if attempt < len(_YT_CLIENT_STRATEGIES):
                    log(f"Pause de {RETRY_BACKOFF_SECONDS}s...")
                    time.sleep(RETRY_BACKOFF_SECONDS)
            except Exception as e:
                self._ydl_instance = None
                if self.is_cancelled:
                    return False
                log(f"[yt-dlp] Erreur inattendue: {e}")
                break

        return False

    def _find_latest_mp4(self, path: str, exclude_files: set) -> Optional[str]:
        latest_file = None
        latest_mtime = -1.0
        for entry in os.scandir(path):
            if not entry.is_file():
                continue
            if entry.path in exclude_files:
                continue
            ext = os.path.splitext(entry.name)[1].lstrip('.').lower()
            if ext == 'mp4':
                mtime = entry.stat().st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_file = entry.path
        return latest_file

    def _build_opts(
        self, path: str, is_playlist_view: bool, progress_callback: Callable
    ) -> dict:
        def _progress_hook(d: dict) -> None:
            if self.is_cancelled:
                raise yt_dlp.utils.DownloadError("Annule par l'utilisateur.")

        def _postprocessor_hook(d: dict) -> None:
            status = d.get('status')
            name = d.get('postprocessor', '')
            if status == 'started':
                log(f"[Postprocessor] {name} en cours...")
                progress_callback(1.0, f"{name}...")
            elif status == 'finished':
                log(f"[Postprocessor] {name} termine.")

        return {
            'noplaylist': not is_playlist_view,
            'logger': _YtDlpLogger(progress_callback),
            'paths': {'home': path},
            'outtmpl': '%(title)s.%(ext)s',
            'concurrent_fragment_downloads': 10,
            'retries': 10,
            'fragment_retries': 10,
            'windowsfilenames': True,
            'progress_hooks': [_progress_hook],
            'postprocessor_hooks': [_postprocessor_hook],
            'user_agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        }

    def _configure_format(
        self, opts: dict, mode: str, fmt: str, q_val: int, has_ffmpeg: bool
    ) -> None:
        if mode == "Audio":
            self._configure_audio(opts, fmt, q_val, has_ffmpeg)
        else:
            self._configure_video(opts, fmt, q_val, has_ffmpeg)

    def _configure_audio(self, opts: dict, fmt: str, q_val: int, has_ffmpeg: bool) -> None:
        opts['format'] = 'bestaudio/best'

        if not has_ffmpeg:
            log(f"FFmpeg manquant: impossible de convertir en {fmt}. Telechargement du meilleur audio.")
            return

        audio_codecs = {
            'mp3': ('libmp3lame', '-q:a 2' if q_val <= 0 else f'-b:a {q_val}k'),
            'm4a': ('aac', '-c:a copy' if q_val <= 0 else f'-b:a {q_val}k'),
            'opus': ('libopus', f'-b:a {q_val}k' if q_val > 0 else '-b:a 128k'),
            'wav': ('pcm_s16le', '-ar 44100'),
            'wma': ('wmav2', f'-b:a {q_val}k' if q_val > 0 else '192k'),
        }

        if fmt in audio_codecs:
            codec, extra = audio_codecs[fmt]
            log(f"Conversion audio vers {fmt.upper()} ({codec})...")
            opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': fmt,
            }]
            opts['postprocessor_args'] = {
                'FFmpegVideoConvertor': ['-acodec', codec] + extra.split(),
            }
        else:
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': fmt,
                'preferredquality': str(q_val) if q_val > 0 else '192',
            }]
            log(f"Conversion audio vers {fmt.upper()} via FFmpegExtractAudio...")

    def _configure_video(self, opts: dict, fmt: str, q_val: int, has_ffmpeg: bool) -> None:
        height_filter = f'[height<={q_val}]' if q_val > 0 else ''

        if not has_ffmpeg:
            log("FFmpeg manquant: pas de fusion possible.")
            opts['format'] = f'best{height_filter}/best'
            return

        opts['merge_output_format'] = 'mp4'
        opts['format'] = (
            f'bestvideo{height_filter}+bestaudio/best{height_filter}/best'
        )
        if fmt == 'mp4':
            log(f"Format video: MP4 (merge via FFmpeg)")
        else:
            log(f"Format video: MP4 d'abord, conversion vers {fmt.upper()} apres telechargement")

    def _download_pytube(
        self,
        url: str,
        path: str,
        mode: str,
        quality: str,
        fmt: str,
        progress_callback: Callable[[float, Optional[str]], None],
    ) -> None:
        ffmpeg_bin = get_ffmpeg_path()
        last_progress = [0.0]
        last_time = [time.time()]

        def pytube_progress(stream, chunk, bytes_remaining) -> None:
            if self.is_cancelled:
                raise Exception("Annule par l'utilisateur.")
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            pct = bytes_downloaded / total_size if total_size > 0 else 0
            now = time.time()
            elapsed = now - last_time[0]
            if elapsed > 0.5:
                speed = (bytes_downloaded - last_progress[0] * total_size) / elapsed
                progress_callback(pct, f"{int(pct * 100)}% | {_format_speed(speed)}")
                last_progress[0] = pct
                last_time[0] = now

        yt = YouTube(url, on_progress_callback=pytube_progress)
        q_val = _parse_quality(quality)

        if mode == "Audio":
            log("pytubefix: Telechargement Audio...")
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        else:
            log("pytubefix: Telechargement Video...")
            streams = yt.streams.filter(progressive=True, file_extension='mp4')
            if q_val > 0:
                matching = [s for s in streams if s.resolution and s.resolution.replace('p', '') == str(q_val)]
                if matching:
                    stream = matching[0]
                else:
                    available = [s for s in streams if s.resolution]
                    available.sort(key=lambda s: int(s.resolution.replace('p', '0') or '0'))
                    stream = available[-1] if available else streams.order_by('resolution').desc().first()
            else:
                stream = streams.order_by('resolution').desc().first()

        if stream is None:
            raise Exception("Aucun flux correspondant trouve.")

        log(f"pytubefix: Flux: {getattr(stream, 'resolution', 'N/A')} / {getattr(stream, 'abr', 'N/A')}")

        downloaded_file = stream.download(output_path=path)
        current_ext = os.path.splitext(downloaded_file)[1].replace(".", "")

        if ffmpeg_bin and current_ext != fmt:
            if mode == "Audio":
                self._convert_audio_file(ffmpeg_bin, downloaded_file, fmt, q_val)
            elif mode == "Vidéo" and fmt != "mp4":
                self._convert_single_video(ffmpeg_bin, downloaded_file, fmt, progress_callback)

    def _convert_audio_file(
        self, ffmpeg_bin: str, input_file: str, fmt: str, q_val: int
    ) -> None:
        base_path = os.path.splitext(input_file)[0]
        output_file = f"{base_path}.{fmt}"

        log(f"Conversion audio vers {fmt.upper()}...")

        cmd = [ffmpeg_bin, "-y", "-i", input_file, "-vn"]
        if q_val > 0:
            cmd += ["-b:a", f"{q_val}k"]
        cmd.append(output_file)

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            subprocess.check_call(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
            try:
                os.remove(input_file)
            except OSError:
                pass
            log(f"Conversion reussie: {fmt} cree.")
        except subprocess.CalledProcessError as e:
            log(f"Erreur conversion FFmpeg: {e}")

    def _convert_single_video(
        self, ffmpeg_bin: str, input_file: str, target_fmt: str,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        base_path = os.path.splitext(input_file)[0]
        output_file = f"{base_path}.{target_fmt}"

        log(f"Conversion {os.path.basename(input_file)} -> {target_fmt.upper()}...")
        if progress_callback:
            progress_callback(1.0, f"Conversion vers {target_fmt.upper()}...")

        cmd = [ffmpeg_bin, "-y", "-i", input_file, "-c", "copy", output_file]

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                creationflags=creation_flags,
            )
            if result.returncode != 0:
                log(f"Erreur FFmpeg (code {result.returncode}): {result.stderr.strip()[-300:]}")
                return
            try:
                os.remove(input_file)
            except OSError:
                pass
            log(f"Conversion reussie: {os.path.basename(output_file)}")
        except Exception as e:
            log(f"Erreur conversion FFmpeg: {e}")

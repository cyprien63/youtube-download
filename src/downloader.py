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
    import pytubefix.exceptions
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


class _YtDlpLogger:
    """Logger adapte pour yt-dlp : parse le pourcentage, la vitesse et le temps restant."""

    def __init__(self, progress_callback: Callable[[float, Optional[str]], None]) -> None:
        self._progress_callback = progress_callback
        self._lock = threading.Lock()

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
    """Convertit une URL Shorts en URL watch classique pour plus de compatibilite."""
    m = _SHORTS_RE.search(url)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    return url


class DownloadManager:
    """Gere les telechargements via yt-dlp (primaire, multi-strategie) et pytubefix (secours)."""

    def __init__(self) -> None:
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        self._cancel_event.set()

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

        # 1. yt-dlp avec strategies de retry
        success = self._download_ytdlp_with_retry(url, path, mode, quality, fmt, progress_callback)
        if success:
            return True

        # 2. pytubefix (secours)
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

    # ------------------------------------------------------------------
    # yt-dlp — retry avec strategies multiples
    # ------------------------------------------------------------------
    def _download_ytdlp_with_retry(
        self,
        url: str,
        path: str,
        mode: str,
        quality: str,
        fmt: str,
        progress_callback: Callable[[float, Optional[str]], None],
    ) -> bool:
        ffmpeg_bin = get_ffmpeg_path()
        has_ffmpeg = ffmpeg_bin is not None

        ffmpeg_dir: Optional[str] = None
        if has_ffmpeg and ffmpeg_bin != "ffmpeg":
            ffmpeg_dir = os.path.dirname(ffmpeg_bin)

        if not has_ffmpeg and mode == "Audio" and fmt != "m4a":
            log("ATTENTION: FFmpeg manquant. La conversion audio pourrait echouer.")

        is_playlist_view = "list=" in url and "watch?" not in url and "v=" not in url
        if is_playlist_view:
            log("Mode detecte: Playlist/Album (Telechargement complet)")
        else:
            log("Mode detecte: Video unique")

        q_val = _parse_quality(quality)

        base_opts = self._build_base_opts(path, is_playlist_view, progress_callback)
        if ffmpeg_dir:
            base_opts['ffmpeg_location'] = ffmpeg_dir

        for attempt, strategy in enumerate(_YT_CLIENT_STRATEGIES, 1):
            if self.is_cancelled:
                return False

            log(f"Essai {attempt}/{len(_YT_CLIENT_STRATEGIES)}: strategie \"{strategy['label']}\"...")

            opts = dict(base_opts)
            opts['extractor_args'] = strategy['extractor_args']

            self._apply_format_opts(opts, mode, fmt, q_val, has_ffmpeg)

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                return True
            except yt_dlp.utils.DownloadError as e:
                err_msg = str(e).lower()
                if self.is_cancelled:
                    return False
                log(f"[yt-dlp] Echec strategie \"{strategy['label']}\": {e}")
                if attempt < len(_YT_CLIENT_STRATEGIES):
                    log("Nouvelle tentative avec strategie differente...")
            except Exception as e:
                if self.is_cancelled:
                    return False
                log(f"[yt-dlp] Erreur inattendue: {e}")
                break

        return False

    def _build_base_opts(
        self, path: str, is_playlist_view: bool, progress_callback: Callable
    ) -> dict:
        return {
            'noplaylist': not is_playlist_view,
            'logger': _YtDlpLogger(progress_callback),
            'paths': {'home': path},
            'outtmpl': '%(playlist_title&{}/|)s%(title)s.%(ext)s',
            'concurrent_fragment_downloads': 15,
            'retries': 10,
            'fragment_retries': 10,
            'buffersize': 1024 * 1024,
            'windowsfilenames': True,
            'user_agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        }

    @staticmethod
    def _apply_format_opts(opts: dict, mode: str, fmt: str, q_val: int, has_ffmpeg: bool) -> None:
        log("Initialisation et optimisation du telechargement...")

        if mode == "Audio":
            opts['format'] = 'bestaudio/best'
            if has_ffmpeg:
                opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': fmt,
                    'preferredquality': str(q_val) if q_val > 0 else '192',
                }]
            else:
                if fmt == "m4a":
                    opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
                else:
                    log(f"FFmpeg manquant: impossible de convertir en {fmt}. Telechargement du meilleur audio.")
        else:
            if has_ffmpeg:
                opts['merge_output_format'] = fmt
                if q_val > 0:
                    opts['format'] = f'bestvideo[height<={q_val}]+bestaudio/best[height<={q_val}]'
                else:
                    opts['format'] = 'bestvideo+bestaudio/best'
            else:
                log("FFmpeg manquant: impossible de fusionner les flux haute qualite.")
                if q_val > 1080:
                    log("Le 4K necessite normalement FFmpeg.")
                if q_val > 0:
                    opts['format'] = f'best[ext={fmt}][height<={q_val}]/best[height<={q_val}]'
                else:
                    opts['format'] = f'best[ext={fmt}]/best'

    # ------------------------------------------------------------------
    # pytubefix (secours) — avec filtrage par qualite
    # ------------------------------------------------------------------
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

        def pytube_progress(stream, chunk, bytes_remaining) -> None:
            if self.is_cancelled:
                raise Exception("Annule par l'utilisateur.")
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            pct = bytes_downloaded / total_size
            speed_str = self._estimate_pytube_speed(bytes_downloaded, total_size)
            progress_callback(pct, f"{int(pct * 100)}% | {speed_str}")

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
                    log(f"pytubefix: Flux {q_val}p trouve.")
                else:
                    available = sorted(
                        [s for s in streams if s.resolution],
                        key=lambda s: int(s.resolution.replace('p', '0') or '0'),
                    )
                    if available:
                        best_under = max(available, key=lambda s: int(s.resolution.replace('p', '0') or '0'))
                        stream = best_under
                        log(f"pytubefix: {q_val}p indisponible, utilisation de {best_under.resolution}.")
                    else:
                        stream = streams.order_by('resolution').desc().first()
            else:
                stream = streams.order_by('resolution').desc().first()

        if stream is None:
            raise Exception("Aucun flux correspondant trouve.")

        log(f"pytubefix: Flux selectionne: {getattr(stream, 'resolution', 'N/A')} / {getattr(stream, 'abr', 'N/A')}")

        downloaded_file = stream.download(output_path=path)

        current_ext = os.path.splitext(downloaded_file)[1].replace(".", "")
        if ffmpeg_bin and current_ext != fmt:
            progress_callback(1.0, "Conversion (Secours)...")
            log(f"Conversion de {current_ext} en {fmt}...")

            base_path = os.path.splitext(downloaded_file)[0]
            final_file = f"{base_path}.{fmt}"

            if os.path.exists(final_file):
                try:
                    os.remove(final_file)
                except OSError:
                    pass

            try:
                cmd = [ffmpeg_bin, "-y", "-i", downloaded_file]
                if mode == "Audio":
                    cmd += ["-vn", "-ab", f"{q_val}k" if q_val > 0 else "192k"]
                cmd.append(final_file)

                creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                subprocess.check_call(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creation_flags,
                )

                try:
                    os.remove(downloaded_file)
                except OSError:
                    pass
                log(f"Conversion reussie: {fmt} cree.")
            except subprocess.CalledProcessError as e:
                log(f"Erreur conversion: {e}")

    @staticmethod
    def _estimate_pytube_speed(bytes_downloaded: int, total_size: int) -> str:
        """Formate la vitesse approximative depuis pytube."""
        if total_size == 0:
            return "..."
        kb = bytes_downloaded / 1024
        if kb > 1024:
            return f"{kb / 1024:.1f} Mo"
        return f"{kb:.0f} Ko"

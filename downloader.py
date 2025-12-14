import os
import shutil
import yt_dlp
from utils import log

try:
    from pytubefix import YouTube
    import pytubefix.exceptions
except ImportError:
    YouTube = None

class DownloadManager:
    def __init__(self):
        pass

    def start_download(self, url, path, mode, quality, fmt, progress_callback):
        log(f"Process: {mode} | {quality} | {fmt}")
        log(f"Target: {url}")
        
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                log(f"Error creating directory: {e}")
                return False

        success = False
        
        # 1. Try yt-dlp
        try:
            log("Engine: yt-dlp (Primary)...")
            self._download_ytdlp(url, path, mode, quality, fmt, progress_callback)
            success = True
        except Exception as e:
            log(f"[yt-dlp] Error: {e}")
            log("Engine: pytubefix (Fallback)...")

        # 2. Try pytubefix
        if not success:
            if YouTube:
                try:
                    self._download_pytube(url, path, mode, quality, fmt, progress_callback)
                    success = True
                except Exception as e:
                    log(f"[pytubefix] Error: {e}")
            else:
                log("[pytubefix] Not available.")

        return success

    def _download_ytdlp(self, url, path, mode, quality, fmt, progress_callback):
        has_ffmpeg = shutil.which('ffmpeg') is not None
        
        if not has_ffmpeg and (mode == "Audio" and fmt != "m4a"):
            log("WARNING: FFmpeg missing. Converting to selected audio format might fail.")

        class YtDlpLogger:
            def __init__(self):
                pass
            
            def debug(self, msg): self._process_msg(msg)
            def info(self, msg): self._process_msg(msg)
            def warning(self, msg): log(f"[WARNING] {msg}")
            def error(self, msg): log(f"[ERROR] {msg}")
            
            def _process_msg(self, msg):
                clean_msg = msg.strip()
                if not clean_msg: return
                if clean_msg.startswith('[download]'):
                    try:
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)%', clean_msg)
                        if match:
                            progress_callback(float(match.group(1)) / 100)
                    except: pass
                    log(clean_msg)
                else:
                    log(clean_msg)

        # 1. Base Options & Performance Optimization
        
        # Intelligent Playlist Detection
        # If it's a specific video (has v= or shorts), we generally want just that video
        # even if it's linked from a playlist context.
        # We only download full playlist if it's a playlist view (list= X, no video param).
        is_playlist_view = "list=" in url and "watch?" not in url and "v=" not in url
        
        if is_playlist_view:
            log("Mode detected: Playlist/Album (Full Download)")
        else:
            log("Mode detected: Single Video (Ignoring List params)")

        ydl_opts_base = {
            'noplaylist': not is_playlist_view,
            'logger': YtDlpLogger(),
            # Path handling: force usage of provided path as base
            'paths': {'home': path},
            # Template: If playlist_title exists, create subfolder, else root.
            # Syntax: %(field&{}/|)s -> if field exists, insert "{field}/", else nothing.
            'outtmpl': '%(playlist_title&{}/|)s%(title)s.%(ext)s',
            
            # SPEED OPTIMIZATIONS
            'concurrent_fragment_downloads': 15, # Download 15 segments in parallel
            'retries': 10,
            'fragment_retries': 10,
            'buffersize': 1024 * 1024,
            
            # COMPATIBILITY
            'windowsfilenames': True,
        }

        log("Initializing and Optimizing Download...")
        # (Metadata extraction step removed - integrated into download for speed)

        # 4. Add Format/Quality Options (Same as before)
        import re
        q_val = 0
        try:
            q_clean = re.sub(r"[^0-9]", "", quality)
            if q_clean: q_val = int(q_clean)
        except: pass

        if mode == "Audio":
            ydl_opts_base['format'] = 'bestaudio/best'
            post_args = []
            if has_ffmpeg:
                post_args.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': fmt,
                    'preferredquality': str(q_val) if q_val > 0 else '192',
                })
            else:
                if fmt == "m4a": ydl_opts_base['format'] = 'bestaudio[ext=m4a]/bestaudio'
                else:
                    log(f"FFmpeg missing: Cannot force {fmt} {q_val}k. Downloading best m4a.")
                    ydl_opts_base['format'] = 'bestaudio[ext=m4a]/bestaudio'

            if post_args: ydl_opts_base['postprocessors'] = post_args

        else: # Video
            if has_ffmpeg:
                ydl_opts_base['merge_output_format'] = fmt
                if q_val > 0: ydl_opts_base['format'] = f'bestvideo[height<={q_val}]+bestaudio/best[height<={q_val}]'
                else: ydl_opts_base['format'] = f'bestvideo+bestaudio/best'
            else:
                log("FFmpeg missing: Cannot merge high quality streams.")
                if q_val > 1080: log("4K requires FFmpeg normally.")
                if q_val > 0: ydl_opts_base['format'] = f'best[ext={fmt}][height<={q_val}]/best[height<={q_val}]'
                else: ydl_opts_base['format'] = f'best[ext={fmt}]/best'

        # 5. Run Download
        with yt_dlp.YoutubeDL(ydl_opts_base) as ydl:
            ydl.download([url])

    def _download_pytube(self, url, path, mode, quality, fmt, progress_callback):
        # Pytube is less flexible, we do best effort mapping
        def pytube_progress(stream, chunk, bytes_remaining):
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            val = bytes_downloaded / total_size
            progress_callback(val)

        yt = YouTube(url, on_progress_callback=pytube_progress)
        
        # Parse Quality INT
        import re
        q_val = 0
        try:
            q_clean = re.sub(r"[^0-9]", "", quality)
            if q_clean: q_val = int(q_clean)
        except: pass

        if mode == "Audio":
            # Pytube basically just has "get_audio_only". Bitrate selection is limited.
            # We filter by likely abr if possible, else take best.
            log(f"pytubefix: Downloading Audio (target ~{q_val}k)")
            streams = yt.streams.filter(only_audio=True)
            # Try to find match
            stream = streams.filter(abr=f"{q_val}kbps").first()
            if not stream:
                stream = streams.order_by('abr').desc().first()
            
            # Note: Pytube usually downloads mp4 audio or webm audio. Converting to mp3/wav requires ffmpeg manually.
            # We will just download what it gives (usually m4a/webm) and rename if simple, but real conversion needs tools.
            log(f"Selected: {stream.abr} {stream.mime_type}")
            
        else: # Video
            log(f"pytubefix: Downloading Video (target <={q_val}p, {fmt})")
            # Progressive (single file) usually maxes at 720p
            # Adaptive requires merging (ffmpeg). Pytube doesn't merge auto.
            # So we stick to progressive if likely, or adaptive if we accept separate files (but user wants 1 file).
            # We will force progressive for stability in "Fallback" mode.
            
            streams = yt.streams.filter(progressive=True, file_extension='mp4') # Pytube mostly does mp4 progressive
            
            if q_val >= 1080:
                # Progressive rarely has 1080p.
                stream = streams.get_highest_resolution() 
                log("Note: Pytube progressive limited to 720p usually.")
            elif q_val > 0:
                 stream = streams.filter(res=f"{q_val}p").first()
                 if not stream: stream = streams.get_by_resolution(f"{q_val}p")
                 if not stream: stream = streams.order_by('resolution').desc().first()
            else:
                 stream = streams.get_highest_resolution()

        if stream:
            out_file = stream.download(output_path=path)
            # Basic rename for audio if it came as mp4 but user wanted mp3 (fake rename, not conversion)
            # But dangerous without conversion. We leave it as is for safety in fallback mode.
        else:
            raise Exception("No suitable stream found.")

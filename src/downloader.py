import os
import shutil
import yt_dlp
from .utils import log
from .ffmpeg_manager import get_ffmpeg_path

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
        ffmpeg_bin = get_ffmpeg_path()
        has_ffmpeg = ffmpeg_bin is not None
        
        # Determine ffmpeg folder for yt-dlp
        ffmpeg_dir = None
        if has_ffmpeg:
            if ffmpeg_bin == "ffmpeg":
                ffmpeg_dir = None # Use system PATH
            else:
                ffmpeg_dir = os.path.dirname(ffmpeg_bin)

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
                elif any(x in clean_msg for x in ['[ExtractAudio]', '[Merger]', '[Fixup]', '[VideoConvertor]']):
                    progress_callback(1.0, "Conversion/Fusion...")
                    log(clean_msg)
                else:
                    log(clean_msg)

        # 1. Base Options & Performance Optimization
        is_playlist_view = "list=" in url and "watch?" not in url and "v=" not in url
        
        if is_playlist_view:
            log("Mode detected: Playlist/Album (Full Download)")
        else:
            log("Mode detected: Single Video (Ignoring List params)")

        ydl_opts_base = {
            'noplaylist': not is_playlist_view,
            'logger': YtDlpLogger(),
            'paths': {'home': path},
            'outtmpl': '%(playlist_title&{}/|)s%(title)s.%(ext)s',
            
            # SPEED OPTIMIZATIONS
            'concurrent_fragment_downloads': 15,
            'retries': 10,
            'fragment_retries': 10,
            'buffersize': 1024 * 1024,
            'windowsfilenames': True,
            
            # FIX 403 & RELIABILITY
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs']
                }
            },
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        if ffmpeg_dir:
            ydl_opts_base['ffmpeg_location'] = ffmpeg_dir

        log("Initializing and Optimizing Download...")

        import re
        q_val = 0
        try:
            q_clean = re.sub(r"[^0-9]", "", quality)
            if q_clean: q_val = int(q_clean)
        except: pass

        if mode == "Audio":
            # Force audio extraction
            ydl_opts_base['format'] = 'bestaudio/best'
            if has_ffmpeg:
                ydl_opts_base['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': fmt,
                    'preferredquality': str(q_val) if q_val > 0 else '192',
                }]
            else:
                if fmt == "m4a": 
                    ydl_opts_base['format'] = 'bestaudio[ext=m4a]/bestaudio'
                else:
                    log(f"FFmpeg missing: Cannot convert to {fmt}. Downloading best available audio (m4a/webm).")
                    ydl_opts_base['format'] = 'bestaudio/best'

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
        ffmpeg_bin = get_ffmpeg_path()
        
        def pytube_progress(stream, chunk, bytes_remaining):
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            val = bytes_downloaded / total_size
            progress_callback(val, None)

        yt = YouTube(url, on_progress_callback=pytube_progress)
        
        import re
        q_val = 0
        try:
            q_clean = re.sub(r"[^0-9]", "", quality)
            if q_clean: q_val = int(q_clean)
        except: pass

        if mode == "Audio":
            log(f"pytubefix: Downloading Audio...")
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        else:
            log(f"pytubefix: Downloading Video...")
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        if stream:
            downloaded_file = stream.download(output_path=path)
            
            # CONVERSION STEP (if needed and ffmpeg exists)
            current_ext = os.path.splitext(downloaded_file)[1].replace(".", "")
            if ffmpeg_bin and current_ext != fmt:
                progress_callback(1.0, "Conversion (Secours)...")
                log(f"Converting {current_ext} to {fmt}...")
                
                base_path = os.path.splitext(downloaded_file)[0]
                final_file = f"{base_path}.{fmt}"
                
                # If file already exists, remove it
                if os.path.exists(final_file):
                    try: os.remove(final_file)
                    except: pass
                
                import subprocess
                try:
                    cmd = [ffmpeg_bin, "-y", "-i", downloaded_file]
                    if mode == "Audio":
                        cmd += ["-vn", "-ab", f"{q_val}k" if q_val > 0 else "192k"]
                    cmd.append(final_file)
                    
                    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    
                    # Cleanup original
                    try: os.remove(downloaded_file)
                    except: pass
                    log(f"Success: {fmt} created.")
                except Exception as e:
                    log(f"Conversion error: {e}")
        else:
            raise Exception("No suitable stream found.")

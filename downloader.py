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

        # Custom Logger to capture Text output and Progress
        class YtDlpLogger:
            def __init__(self):
                pass
            
            def debug(self, msg):
                # yt-dlp sends "debug" logs for download progress too (starting with [download])
                # or just std info.
                self._process_msg(msg)

            def info(self, msg):
                self._process_msg(msg)

            def warning(self, msg):
                log(f"[WARNING] {msg}")

            def error(self, msg):
                log(f"[ERROR] {msg}")

            def _process_msg(self, msg):
                # Always log to GUI (except super spammy stuff if needed, but user wants to see it)
                # Filter out carriage returns to avoid mess in text box if possible, 
                # but text widget usually handles \n. yt-dlp uses \r for progress bars.
                # We'll clean it up slightly.
                clean_msg = msg.strip()
                if not clean_msg: return

                # Log it (maybe filter "download" lines if they are too fast, but user asked for them)
                # To prevent GUI freezing from 100s of lines per second, we might check if it's a progress line
                if clean_msg.startswith('[download]'):
                    # Parse Percentage
                    # "[download]  54.9% of ~  54.70MiB at  427.92KiB/s ETA 01:03"
                    try:
                        import re
                        # Search for percentage: 54.9%
                        match = re.search(r'(\d+(?:\.\d+)?)%', clean_msg)
                        if match:
                            val = float(match.group(1)) / 100
                            progress_callback(val)
                    except:
                        pass
                    
                    # Log to GUI (User explicitly asked to see these lines)
                    log(clean_msg)
                else:
                    log(clean_msg)

        ydl_opts = {
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'logger': YtDlpLogger(),
            # 'verbose': True, # Uncomment if needed for more info
        }

        # --- PARSE QUALITY ---
        # "1080p" -> 1080, "2160p (4K)" -> 2160, "320 kbps" -> 320
        import re
        q_val = 0
        try:
            q_clean = re.sub(r"[^0-9]", "", quality) # Remove non-digits
            if q_clean:
                q_val = int(q_clean)
        except:
            pass

        if mode == "Audio":
            # Quality = Bitrate (kbps)
            # 320, 256, 192, 128...
            # Format = mp3, m4a, wav, opus...
            
            ydl_opts['format'] = 'bestaudio/best'
            
            post_args = []
            
            # If we need conversion (mp3, wav, opus usually need it)
            if has_ffmpeg:
                post_args.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': fmt,  # mp3, wav, opus, m4a
                    'preferredquality': str(q_val) if q_val > 0 else '192',
                })
            else:
                if fmt == "m4a":
                     ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
                else:
                    log(f"FFmpeg missing: Cannot force {fmt} {q_val}k. Downloading best m4a.")
                    ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'

            if post_args:
                ydl_opts['postprocessors'] = post_args

        else: # Vidéo
            # Quality = Height (1080, 720...)
            # Format = mp4, mkv, webm
            
            if has_ffmpeg:
                # Merge best video fitting height + best audio
                # e.g., bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]
                
                # Note: yt-dlp syntax for merging to specific functionality
                # often we just select best streams and let 'merge_output_format' do container
                ydl_opts['merge_output_format'] = fmt
                
                if q_val > 0:
                     ydl_opts['format'] = f'bestvideo[height<={q_val}]+bestaudio/best[height<={q_val}]'
                else:
                     ydl_opts['format'] = f'bestvideo+bestaudio/best'
            else:
                # Fallback single file
                log("FFmpeg missing: Cannot merge high quality streams.")
                if q_val > 1080: log("4K requires FFmpeg normally.")
                
                if q_val > 0:
                    ydl_opts['format'] = f'best[ext={fmt}][height<={q_val}]/best[height<={q_val}]'
                else:
                    ydl_opts['format'] = f'best[ext={fmt}]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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

import os
import shutil
import yt_dlp
from utils import log

# Switch to pytubefix for better reliability
try:
    from pytubefix import YouTube
    import pytubefix.exceptions
except ImportError:
    YouTube = None

class DownloadManager:
    def __init__(self):
        pass

    def start_download(self, url, path, mode, quality, progress_callback):
        log(f"Starting download process for: {url}")
        
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                log(f"Created directory: {path}")
            except OSError as e:
                log(f"Error creating directory: {e}")
                return False

        success = False
        
        # 1. Try yt-dlp
        try:
            log("Attempting Primary Engine (yt-dlp)...")
            self._download_ytdlp(url, path, mode, quality, progress_callback)
            success = True
        except Exception as e:
            log(f"[yt-dlp] Failed: {e}")
            log("Switching to Secondary Engine (pytubefix)...")

        # 2. Try pytubefix if yt-dlp failed
        if not success:
            if YouTube:
                try:
                    self._download_pytube(url, path, mode, quality, progress_callback)
                    success = True
                except Exception as e:
                    log(f"[pytubefix] Failed: {e}")
            else:
                log("[pytubefix] Library not installed or unavailable.")

        return success

    def _download_ytdlp(self, url, path, mode, quality, progress_callback):
        # Check for FFmpeg
        has_ffmpeg = shutil.which('ffmpeg') is not None
        if not has_ffmpeg:
            log("WARNING: FFmpeg not found on system.")
            log(" >> High Quality (1080p+) and MP3 conversion require FFmpeg.")
            log(" >> Falling back to compatible mode (Max 720p / m4a).")

        def hook(d):
            if d['status'] == 'downloading':
                try:
                    p = d.get('_percent_str', '0%').replace('%','')
                    val = float(p) / 100
                    progress_callback(val)
                except:
                    pass
            elif d['status'] == 'finished':
                log("yt-dlp: Download complete. Processing...")
                progress_callback(0.99)

        ydl_opts = {
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'progress_hooks': [hook],
            'noplaylist': True,
        }

        if mode == "Audio":
            if has_ffmpeg:
                # Optimal: Convert to MP3
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                # Fallback: Download m4a directly (no conversion needed)
                ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
        else:
            # Video
            if has_ffmpeg:
                # Optimal: Merge Video + Audio
                if quality == "Best":
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                elif quality == "High":
                    ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
                elif quality == "Medium":
                    ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
                elif quality == "Low":
                    ydl_opts['format'] = 'worstvideo+bestaudio/worst'
            else:
                # Fallback: Single file (usually max 720p)
                log("Using single-file format due to missing FFmpeg.")
                ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def _download_pytube(self, url, path, mode, quality, progress_callback):
        def pytube_progress(stream, chunk, bytes_remaining):
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            val = bytes_downloaded / total_size
            progress_callback(val)

        yt = YouTube(url, on_progress_callback=pytube_progress)
        
        if mode == "Audio":
            stream = yt.streams.get_audio_only()
            log(f"pytubefix: Downloading Audio ({stream.abr})")
        else:
            streams = yt.streams.filter(progressive=True, file_extension='mp4')
            if quality in ["Best", "High"]:
                stream = streams.get_highest_resolution()
            elif quality == "Low":
                stream = streams.get_lowest_resolution()
            else:
                stream = streams.first()
            log(f"pytubefix: Downloading Video ({stream.resolution})")

        if stream:
            stream.download(output_path=path)
        else:
            raise Exception("No suitable stream found.")

import os
import shutil
import zipfile
import urllib.request
import ssl
from utils import log

# URL to a static build of FFmpeg for Windows
FFMPEG_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
# Backup URL in case the first one fails or is slow
FFMPEG_URL_BACKUP = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

BIN_DIR = "bin"

def get_ffmpeg_path():
    """
    Returns the path to ffmpeg executable.
    Downloads it if not found locally or in PATH.
    """
    # 1. Check system path
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    
    # 2. Check local bin
    local_ffmpeg = os.path.join(os.getcwd(), BIN_DIR, "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    # 3. Not found. Download.
    return download_ffmpeg()

def download_ffmpeg():
    log("FFmpeg not found. Downloading (this may take a minute)...")
    if not os.path.exists(BIN_DIR):
        try:
            os.makedirs(BIN_DIR)
        except OSError as e:
            log(f"Error creating bin directory: {e}")
            return None

    zip_path = os.path.join(BIN_DIR, "ffmpeg.zip")
    
    try:
        # Create unverified context to avoid SSL errors on some machines
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        log(f"Connect to server...")
        try:
            with urllib.request.urlopen(FFMPEG_URL, context=ctx) as response, open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            log(f"Primary URL failed: {e}. Trying backup...")
            with urllib.request.urlopen(FFMPEG_URL_BACKUP, context=ctx) as response, open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

        log("Download complete. Extracting...")
        
        # Extract
        found_ffmpeg = False
        found_ffprobe = False
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                lower_name = file.lower()
                if lower_name.endswith("bin/ffmpeg.exe") or lower_name.endswith("ffmpeg.exe"):
                    _extract_file(zip_ref, file, "ffmpeg.exe")
                    found_ffmpeg = True
                elif lower_name.endswith("bin/ffprobe.exe") or lower_name.endswith("ffprobe.exe"):
                    _extract_file(zip_ref, file, "ffprobe.exe")
                    found_ffprobe = True
                    
        if found_ffmpeg:
            log("FFmpeg setup complete.")
        else:
            log("ERROR: Could not find ffmpeg.exe in the downloaded archive.")
        
        # Cleanup
        try:
            os.remove(zip_path)
        except: pass
        
        return os.path.join(os.getcwd(), BIN_DIR, "ffmpeg.exe") if found_ffmpeg else None
        
    except Exception as e:
        log(f"Error downloading/installing FFmpeg: {e}")
        return None

def _extract_file(zip_ref, member_name, target_name):
    source = zip_ref.open(member_name)
    target_path = os.path.join(BIN_DIR, target_name)
    with open(target_path, "wb") as target_file:
        shutil.copyfileobj(source, target_file)
    source.close()

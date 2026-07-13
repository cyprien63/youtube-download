import os
import shutil
import zipfile
import urllib.request
import ssl
from typing import Optional

from .utils import log

FFMPEG_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
FFMPEG_URL_BACKUP = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# Dossier du script courant — fonctionne quel que soit le cwd
_SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT: str = os.path.dirname(_SCRIPT_DIR)
BIN_DIR: str = os.path.join(_PROJECT_ROOT, "bin")


def get_ffmpeg_path() -> Optional[str]:
    """Retourne le chemin vers ffmpeg. Le télécharge si absent."""
    if shutil.which("ffmpeg"):
        return "ffmpeg"

    local_ffmpeg = os.path.join(BIN_DIR, "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    return download_ffmpeg()


def download_ffmpeg() -> Optional[str]:
    """Télécharge un build statique de FFmpeg dans bin/."""
    log("FFmpeg introuvable. Telechargement en cours (cela peut prendre une minute)...")
    if not os.path.exists(BIN_DIR):
        try:
            os.makedirs(BIN_DIR)
        except OSError as e:
            log(f"Erreur creation dossier bin: {e}")
            return None

    zip_path = os.path.join(BIN_DIR, "ffmpeg.zip")

    try:
        ctx = ssl.create_default_context()

        log("Connexion au serveur...")
        try:
            with urllib.request.urlopen(FFMPEG_URL, context=ctx, timeout=60) as response, \
                 open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            log(f"URL principale echouee: {e}. Tentative avec l'URL de secours...")
            with urllib.request.urlopen(FFMPEG_URL_BACKUP, context=ctx, timeout=60) as response, \
                 open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

        log("Telechargement termine. Extraction en cours...")

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
            log("FFmpeg installe avec succes.")
        else:
            log("ERREUR: ffmpeg.exe introuvable dans l'archive telechargee.")

        try:
            os.remove(zip_path)
        except OSError:
            pass

        return os.path.join(BIN_DIR, "ffmpeg.exe") if found_ffmpeg else None

    except Exception as e:
        log(f"Erreur telechargement/installation FFmpeg: {e}")
        return None


def _extract_file(zip_ref: zipfile.ZipFile, member_name: str, target_name: str) -> None:
    with zip_ref.open(member_name) as source:
        target_path = os.path.join(BIN_DIR, target_name)
        with open(target_path, "wb") as target_file:
            shutil.copyfileobj(source, target_file)

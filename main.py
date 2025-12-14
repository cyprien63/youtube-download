import sys
import subprocess
import os

# 1. SETUP / AUTO-REPAIR
# 1. SETUP / AUTO-REPAIR
def get_remote_version():
    """Fetches VERSION from remote version.py without pulling."""
    try:
        # Fetch latest meta without merging
        subprocess.check_call(["git", "fetch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Read the file from origin/main
        content = subprocess.check_output(["git", "show", "origin/main:version.py"], stderr=subprocess.STDOUT).decode()
        # Parse it manually (it's just VERSION = "x.y.z")
        for line in content.splitlines():
            if line.startswith("VERSION"):
                return line.split('"')[1]
    except Exception:
        return None
    return None

def is_newer(remote_ver, local_ver):
    """Returns True if remote_ver > local_ver specifically."""
    try:
        r_parts = [int(x) for x in remote_ver.split('.')]
        l_parts = [int(x) for x in local_ver.split('.')]
        return r_parts > l_parts
    except:
        return False

def install_git():
    """Attempts to install Git via Winget, then Direct Download."""
    print("⚠️ Git non trouvé. Tentative d'installation automatique...")
    
    # 1. Try Winget
    print("   [1/2] Essai avec Winget...")
    try:
        subprocess.check_call(["winget", "install", "--id", "Git.Git", "-e", "--source", "winget", "--accept-source-agreements", "--accept-package-agreements"], shell=True)
        print("✅ Git installé avec succès via Winget.")
        return True
    except Exception as e:
        print(f"   ❌ Winget a précisé : {e}")

    # 2. Try Direct Download
    print("   [2/2] Essai par téléchargement direct...")
    try:
        import urllib.request
        import tempfile
        
        # Latest Git for Windows URL (Standard 64-bit)
        url = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
        installer_path = os.path.join(tempfile.gettempdir(), "git_installer.exe")
        
        print(f"   ⬇️ Téléchargement depuis GitHub...")
        urllib.request.urlretrieve(url, installer_path)
        
        print("   📦 Installation silencieuse en cours...")
        # /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS
        subprocess.check_call([installer_path, "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-", "/CLOSEAPPLICATIONS"])
        
        try:
            os.remove(installer_path)
        except: pass
        
        print("✅ Git installé avec succès.")
        return True
    except Exception as e:
        print(f"   ❌ L'installation directe a échoué: {e}")
    
    return False

def update_application():
    """Checks remote version and updates ONLY if superior."""
    if getattr(sys, "frozen", False):
        return

    print("🔍 Vérification des mises à jour (GitHub)...")
    
    # 0. Check Git Existence
    git_exists = False
    try:
        subprocess.check_call(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        git_exists = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Try to install
        if install_git():
            git_exists = True
        else:
            print("⚠️ Git introuvable et impossible à installer. Mises à jour désactivées.")
            return

    try:        
        # 1. Get Local Version
        try:
            from version import VERSION as local_version
        except ImportError:
            local_version = "0.0.0"

        # 2. Get Remote Version
        remote_version = get_remote_version()
        
        if not remote_version:
            print("⚠️ Impossible de lire la version distante.")
            return

        print(f"   ℹ️ Local: {local_version}  |  Distant: {remote_version}")

        # 3. Compare
        if is_newer(remote_version, local_version):
            print("🚀 Nouvelle version supérieure détectée ! Téléchargement...")
            output = subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT).decode()
            print("⬇️  Mise à jour effectuée avec succès.")
            print("ℹ️  Relancez le logiciel pour appliquer.")
        elif remote_version == local_version:
             print("✅  Logiciel à jour.")
        else:
             print("🛡️  Sécurité : Version distante INFÉRIEURE. Mise à jour bloquée.")
            
    except Exception as e:
        print(f"⚠️ Erreur update : {e}")

def install_requirements():
    print("Checking requirements...")
    # Updated to pytubefix which is currently maintained
    reqs = ["customtkinter", "yt-dlp", "pytubefix", "pillow"]
    try:
        import customtkinter
        import yt_dlp
        import pytubefix
    except ImportError:
        print("Missing libraries detected or need update. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + reqs)
            print("Installation complete.")
        except Exception as e:
            print(f"Failed to install requirements: {e}")
            input("Press Enter to exit...")
            sys.exit(1)

if __name__ == "__main__":
    # If frozen (exe), we skip checks usually, but if source, we auto-install
    if not getattr(sys, "frozen", False):
        update_application()
        install_requirements()

    # 2. LAUNCH GUI
    try:
        from gui import YouTubeDownloaderApp
        app = YouTubeDownloaderApp()
        app.mainloop()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to Close")

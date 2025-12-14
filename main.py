import sys
import subprocess
import os

# 1. SETUP / AUTO-REPAIR
def update_application():
    """Pulls latest code from git."""
    if getattr(sys, "frozen", False):
        return

    print("🔍 Vérification des mises à jour (GitHub)...")
    try:
        # Verify git availability
        subprocess.check_call(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Perform pull
        output = subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT).decode()
        
        # Check output
        if "Already up to date" in output or "déjà à jour" in output:
            print("✅  Aucune nouvelle mise à jour.")
        else:
            print(f"[Git] {output.strip()}")
            print("⬇️  Mise à jour téléchargée avec succès.")
            print("ℹ️  Les modifications seront prises en compte au prochain lancement.")
            
    except FileNotFoundError:
        print("⚠️ Git non trouvé. Mise à jour ignorée.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Échec de la mise à jour : {e.output.decode() if e.output else str(e)}")
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification : {e}")

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

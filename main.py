import sys
import subprocess
import os

# 1. SETUP / AUTO-REPAIR
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

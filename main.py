import sys
import subprocess
import os
import threading
import urllib.request
import tempfile
from typing import Optional

GITHUB_REPO = "cyprien63/youtube-download"


def _get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _get_local_version() -> str:
    try:
        from version import VERSION
        return VERSION
    except ImportError:
        return "0.0.0"


def get_remote_version() -> Optional[str]:
    import time
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.py?t={int(time.time())}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            content = response.read().decode('utf-8')
            for line in content.splitlines():
                if line.startswith("VERSION"):
                    return line.split('"')[1]
    except Exception:
        pass
    return None


def install_git() -> bool:
    print("Git non trouve. Tentative d'installation automatique...")

    print("   [1/2] Essai avec Winget...")
    try:
        subprocess.check_call(
            ["winget", "install", "--id", "Git.Git", "-e", "--source", "winget",
             "--accept-source-agreements", "--accept-package-agreements"],
            shell=True,
        )
        print("Git installe avec succes via Winget.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"   Echec Winget: {e}")

    print("   [2/2] Essai par telechargement direct...")
    try:
        url = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
        installer_path = os.path.join(tempfile.gettempdir(), "git_installer.exe")

        print("   Telechargement depuis GitHub...")
        urllib.request.urlretrieve(url, installer_path)

        print("   Installation silencieuse en cours...")
        subprocess.check_call([
            installer_path, "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-",
        ])

        try:
            os.remove(installer_path)
        except OSError:
            pass

        print("Git installe avec succes.")
        return True
    except (subprocess.CalledProcessError, OSError, urllib.error.URLError) as e:
        print(f"   L'installation directe a echoue: {e}")

    return False


def update_application_dev() -> None:
    print("Verification des mises a jour (GitHub)...")

    try:
        subprocess.check_call(
            ["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        if not install_git():
            print("Git introuvable. Mises a jour desactivees.")
            return

    try:
        local_version = _get_local_version()
        remote_version = get_remote_version()

        if remote_version:
            print(f"   Local: {local_version}  |  Distant: {remote_version}")
        else:
            print(f"   Local: {local_version}  |  Distant: indisponible")

        print("Synchronisation avec GitHub...")
        pull_result = subprocess.run(
            ["git", "pull", "--ff-only"],
            capture_output=True, text=True, timeout=30,
        )
        if pull_result.returncode == 0:
            output = pull_result.stdout.strip()
            if "Already up to date" in output or "Deja a jour" in output:
                print("Logiciel a jour.")
            else:
                new_version = _get_local_version()
                print(f"Mise a jour effectuee : {local_version} -> {new_version}")
                print("Relancez le logiciel pour appliquer.")
        else:
            print("Sync impossible. Verifiez votre connexion.")
    except Exception as e:
        print(f"Erreur update: {e}")


def install_requirements() -> None:
    print("Verification des dependances...")
    reqs = ["customtkinter", "yt-dlp", "pytubefix", "pillow"]
    try:
        import customtkinter  # noqa: F401
        import yt_dlp  # noqa: F401
        import pytubefix  # noqa: F401
        import PIL  # noqa: F401
    except ImportError:
        print("Bibliotheques manquantes. Installation en cours...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + reqs)
            print("Installation terminee.")
        except Exception as e:
            print(f"Echec de l'installation: {e}")
            if sys.stdin and sys.stdin.isatty():
                input("Appuyez sur Entree pour quitter...")
            sys.exit(1)


def _thread_excepthook(args) -> None:
    import traceback
    msg = f"[Thread error] {args.thread.name}: {args.exception}\n"
    msg += "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    _log_to_file(msg)


def _log_to_file(msg: str) -> None:
    try:
        log_path = os.path.join(_get_app_dir(), "crash.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    threading.excepthook = _thread_excepthook

    if not getattr(sys, "frozen", False):
        try:
            update_application_dev()
            install_requirements()
        except Exception as e:
            _log_to_file(f"ERREUR UPDATE: {e}")

    try:
        from src.gui import YouTubeDownloaderApp
        app = YouTubeDownloaderApp()
        app.mainloop()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        _log_to_file(f"ERREUR CRITIQUE: {e}\n{tb}")
        print(f"ERREUR CRITIQUE: {e}")
        traceback.print_exc()
        if sys.stdin and sys.stdin.isatty():
            input("Appuyez sur Entree pour fermer...")

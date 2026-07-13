import sys
import subprocess
import os
import threading
import urllib.request
import tempfile
from typing import Optional


def get_remote_version() -> Optional[str]:
    """Recupere la version distante depuis GitHub."""
    url = "https://raw.githubusercontent.com/cyprien63/youtube-download/main/version.py"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            content = response.read().decode('utf-8')
            for line in content.splitlines():
                if line.startswith("VERSION"):
                    return line.split('"')[1]
    except Exception as e:
        print(f"   Erreur lecture distante (urllib): {e}")
        try:
            subprocess.check_call(
                ["git", "fetch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            content = subprocess.check_output(
                ["git", "show", "origin/main:version.py"], stderr=subprocess.STDOUT
            ).decode()
            for line in content.splitlines():
                if line.startswith("VERSION"):
                    return line.split('"')[1]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    return None


def is_newer(remote_ver: str, local_ver: str) -> bool:
    """Renvoie True si remote_ver > local_ver (semantique)."""
    try:
        r_parts = [int(x) for x in remote_ver.split('.')]
        l_parts = [int(x) for x in local_ver.split('.')]
        max_len = max(len(r_parts), len(l_parts))
        r_parts.extend([0] * (max_len - len(r_parts)))
        l_parts.extend([0] * (max_len - len(l_parts)))
        return tuple(r_parts) > tuple(l_parts)
    except (ValueError, AttributeError):
        return False


def install_git() -> bool:
    """Installe Git via Winget ou telechargement direct."""
    print("Git non trouve. Tentative d'installation automatique...")

    # 1. Winget
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

    # 2. Telechargement direct
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


def update_application() -> None:
    """Verifie la version distante et met a jour si superieure."""
    if getattr(sys, "frozen", False):
        return

    print("Verification des mises a jour (GitHub)...")

    git_exists = False
    try:
        subprocess.check_call(
            ["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        git_exists = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        if install_git():
            git_exists = True
        else:
            print("Git introuvable et impossible a installer. Mises a jour desactivees.")
            return

    try:
        try:
            from version import VERSION as local_version
        except ImportError:
            local_version = "0.0.0"

        remote_version = get_remote_version()

        if not remote_version:
            print("Impossible de lire la version distante.")
            return

        print(f"   Local: {local_version}  |  Distant: {remote_version}")

        if is_newer(remote_version, local_version):
            print("Nouvelle version superieure detectee ! Telechargement...")
            result = subprocess.run(
                ["git", "pull", "--ff-only"],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"Echec de la mise a jour: {result.stderr.strip()}")
                print("Veuillez mettre a jour manuellement: git pull")
            else:
                print("Mise a jour effectuee avec succes.")
                print("Relancez le logiciel pour appliquer.")
        elif remote_version == local_version:
            print("Logiciel a jour.")
        else:
            print("Securite: Version distante inferieure. Mise a jour bloquee.")

    except Exception as e:
        print(f"Erreur update: {e}")


def install_requirements() -> None:
    """Verifie et installe les dependances Python manquantes."""
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
            if sys.stdin.isatty():
                input("Appuyez sur Entree pour quitter...")
            sys.exit(1)


def _thread_excepthook(args) -> None:
    import traceback
    print(f"[Thread error] {args.thread.name}: {args.exception}")
    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)


if __name__ == "__main__":
    threading.excepthook = _thread_excepthook

    if not getattr(sys, "frozen", False):
        update_application()
        install_requirements()

    try:
        from src.gui import YouTubeDownloaderApp
        app = YouTubeDownloaderApp()
        app.mainloop()
    except Exception as e:
        print(f"ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        if sys.stdin.isatty():
            input("Appuyez sur Entree pour fermer...")

import sys
import subprocess
import os
import threading
import urllib.request
import tempfile
import json
from typing import Optional

GITHUB_REPO = "cyprien63/youtube-download"

def _get_app_dir() -> str:
    """Retourne le dossier ou se trouvent les donnees persistantes (a cote de l'exe)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _get_local_version() -> str:
    """Lit la version locale."""
    if getattr(sys, "frozen", False):
        try:
            from version import VERSION
            return VERSION
        except ImportError:
            return "0.0.0"
    try:
        from version import VERSION
        return VERSION
    except ImportError:
        return "0.0.0"


def get_remote_version() -> Optional[str]:
    """Recupere la version distante depuis GitHub (raw)."""
    import time
    cache_bust = int(time.time())
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.py?t={cache_bust}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            content = response.read().decode('utf-8')
            for line in content.splitlines():
                if line.startswith("VERSION"):
                    return line.split('"')[1]
    except Exception as e:
        print(f"   Erreur lecture distante (urllib): {e}")
        if not getattr(sys, "frozen", False):
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


def get_github_release_info() -> Optional[dict]:
    """Recupere les infos de la derniere release GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "YouTube-Downloader",
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
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
    """Mode dev : git pull auto puis verification de version."""
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
            print("Git introuvable. Mises a jour desactivees.")
            return

    if not git_exists:
        return

    try:
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
                print("Mise a jour effectuee. Relancez le logiciel.")
        else:
            print("Sync impossible. Verifiez votre connexion.")
    except Exception as e:
        print(f"Erreur update: {e}")


def check_frozen_update(app=None) -> None:
    """Mode exe : verification via GitHub Releases OU version.py + popup si nouvelle version."""
    local_version = _get_local_version()
    print(f"Verification des mises a jour... (v{local_version})")

    remote_version = None
    html_url = ""
    body = ""

    release = get_github_release_info()
    if release:
        remote_version = release.get("tag_name", "").lstrip("v")
        html_url = release.get("html_url", "")
        body = release.get("body", "")[:200]

    if not remote_version:
        remote_version = get_remote_version()
        html_url = f"https://github.com/{GITHUB_REPO}/releases"

    if not remote_version:
        print("Impossible de verifier les mises a jour.")
        return

    print(f"   Local: {local_version}  |  Distant: {remote_version}")

    if not is_newer(remote_version, local_version):
        print("Logiciel a jour.")
        return

    print("Nouvelle version disponible !")

    try:
        import customtkinter as ctk
        if app is not None:
            app.after(0, _show_update_popup, ctk, remote_version, local_version, html_url, body)
        else:
            _show_update_popup(ctk, remote_version, local_version, html_url, body)
    except Exception as e:
        print(f"Impossible d'afficher la popup: {e}")
        print(f"Telechargez manuellement: {html_url}")


def _show_update_popup(ctk, remote_ver: str, local_ver: str, url: str, notes: str) -> None:
    """Affiche une popup pour informer de la mise a jour disponible."""
    popup = ctk.CTkToplevel()
    popup.title("Mise a jour disponible")
    popup.geometry("480x320")
    popup.resizable(False, False)
    popup.attributes("-topmost", True)
    popup.grab_set()

    ctk.CTkLabel(
        popup, text="Mise a jour disponible !",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(pady=(20, 5))

    ctk.CTkLabel(
        popup,
        text=f"Version {local_ver}  ->  {remote_ver}",
        font=ctk.CTkFont(size=13),
    ).pack(pady=(0, 10))

    if notes:
        ctk.CTkTextbox(popup, height=80, font=("Consolas", 11)).pack(padx=20, fill="x")
        # On ne peut pas inserer depuis le constructeur, on le fait apres
        textbox = popup.winfo_children()[-1]
        textbox.configure(state="normal")
        textbox.insert("1.0", notes)
        textbox.configure(state="disabled")

    def open_download():
        import webbrowser
        webbrowser.open(url)
        popup.destroy()

    ctk.CTkButton(
        popup, text="Telecharger", command=open_download,
        height=40, font=ctk.CTkFont(size=14, weight="bold"),
    ).pack(pady=15)

    ctk.CTkButton(
        popup, text="Plus tard", command=popup.destroy,
        height=30,
    ).pack(pady=(0, 10))


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
        if getattr(sys, "frozen", False):
            threading.Thread(target=check_frozen_update, args=(app,), daemon=True).start()
        app.mainloop()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        _log_to_file(f"ERREUR CRITIQUE: {e}\n{tb}")
        print(f"ERREUR CRITIQUE: {e}")
        traceback.print_exc()
        if sys.stdin and sys.stdin.isatty():
            input("Appuyez sur Entree pour fermer...")

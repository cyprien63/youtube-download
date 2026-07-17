import json
import re
import os
import sys
import threading
import urllib.request
import io
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk
import tkinter as tk
from PIL import Image

from .utils import logger, log
from .downloader import DownloadManager
from version import VERSION

APP_NAME = "YouTube Downloader"

_YT_URL_RE = re.compile(
    r'^(https?://)?(www\.)?'
    r'(youtube\.com|youtu\.be|m\.youtube\.com)'
    r'.+'
)

if getattr(sys, 'frozen', False):
    _PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_DEFAULT_DOWNLOAD_DIR = os.path.join(_PROJECT_ROOT, "Downloads_YT")
_SETTINGS_FILE = os.path.join(_PROJECT_ROOT, ".settings")


def _load_settings() -> dict:
    if os.path.isfile(_SETTINGS_FILE):
        try:
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_settings(data: dict) -> None:
    try:
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self) -> None:
        self._settings = _load_settings()

        saved_mode = self._settings.get("theme", "dark")
        ctk.set_appearance_mode(saved_mode)

        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("900x700")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.download_path = tk.StringVar(value=_DEFAULT_DOWNLOAD_DIR)
        self.url_var = tk.StringVar()
        self.format_mode = tk.StringVar(value="Vidéo")
        self.format_var = tk.StringVar(value="mp4")
        self.quality_var = tk.StringVar(value="1080p")

        self.manager = DownloadManager()
        self._downloading = False
        self._dark_mode = (saved_mode == "dark")
        self._preview_job: Optional[str] = None
        self._preview_thumb_image: Optional[ctk.CTkImage] = None
        self._preview_full_image: Optional[Image.Image] = None

        self.setup_ui()

        self.url_var.trace_add("write", self._on_url_changed)

        logger.set_widget(self.log_textbox)
        log("GUI initialise.")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def setup_ui(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")

        ctk.CTkLabel(
            self.sidebar, text=APP_NAME, font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        ctk.CTkLabel(self.sidebar, text="Type de contenu :", anchor="w").grid(
            row=1, column=0, padx=20, pady=(10, 0)
        )
        self.mode_option = ctk.CTkSegmentedButton(
            self.sidebar, values=["Vidéo", "Audio"], command=self.update_options
        )
        self.mode_option.grid(row=2, column=0, padx=20, pady=(5, 10))
        self.mode_option.set("Vidéo")

        ctk.CTkLabel(self.sidebar, text="Format :", anchor="w").grid(
            row=3, column=0, padx=20, pady=(10, 0)
        )
        self.format_menu = ctk.CTkComboBox(self.sidebar, variable=self.format_var)
        self.format_menu.grid(row=4, column=0, padx=20, pady=(0, 10))

        ctk.CTkLabel(self.sidebar, text="Qualite :", anchor="w").grid(
            row=5, column=0, padx=20, pady=(10, 0)
        )
        self.quality_menu = ctk.CTkComboBox(self.sidebar, variable=self.quality_var)
        self.quality_menu.grid(row=6, column=0, padx=20, pady=(0, 20))

        self.update_options("Vidéo")

        theme_label = "Mode: Sombre" if self._dark_mode else "Mode: Claire"
        self.theme_button = ctk.CTkButton(
            self.sidebar, text=theme_label, command=self.toggle_theme, width=160
        )
        self.theme_button.grid(row=7, column=0, padx=20, pady=(10, 20))

        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.main, text="YouTube URL:").grid(row=0, column=0, sticky="w")
        self.url_entry = ctk.CTkEntry(
            self.main, textvariable=self.url_var, placeholder_text="Collez le lien ici..."
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.preview_frame = ctk.CTkFrame(self.main, corner_radius=10)
        self.preview_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.preview_frame.grid_columnconfigure(1, weight=1)
        self.preview_frame.grid_remove()

        self.preview_thumb_label = ctk.CTkLabel(self.preview_frame, text="")
        self.preview_thumb_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        self.preview_thumb_label.bind("<Button-1>", lambda e: self._enlarge_thumbnail())

        self.preview_title_label = ctk.CTkLabel(
            self.preview_frame, text="", font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=500, anchor="w", justify="left",
        )
        self.preview_title_label.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(10, 0))

        self.preview_channel_label = ctk.CTkLabel(
            self.preview_frame, text="", font=ctk.CTkFont(size=12),
            text_color="gray", anchor="w",
        )
        self.preview_channel_label.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=(0, 10))

        path_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        path_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        path_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(
            path_frame, textvariable=self.download_path, state="readonly"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkButton(
            path_frame, text="Browse", command=self.browse, width=100
        ).grid(row=0, column=1)

        self.btn = ctk.CTkButton(
            self.main,
            text="TELECHARGER",
            command=self.start_thread,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.btn.grid(row=4, column=0, sticky="ew", pady=10)

        self.progress = ctk.CTkProgressBar(self.main)
        self.progress.grid(row=5, column=0, sticky="ew", pady=10)
        self.progress.set(0)

        self.pct_label = ctk.CTkLabel(self.main, text="0%")
        self.pct_label.grid(row=6, column=0, sticky="e")

        ctk.CTkLabel(self.main, text="Logs:").grid(row=7, column=0, sticky="w")
        self.log_textbox = ctk.CTkTextbox(self.main, height=200, font=("Consolas", 12))
        self.log_textbox.grid(row=8, column=0, sticky="nsew")
        self.log_textbox.configure(state="disabled")

        self.main.grid_rowconfigure(8, weight=1)

        self.bind("<Return>", lambda e: self.start_thread())
        self.bind("<Control-v>", lambda e: self._paste_url())

    def _paste_url(self) -> None:
        try:
            text = self.clipboard_get()
            if text:
                self.url_var.set(text.strip())
        except tk.TclError:
            pass

    def _on_url_changed(self, *_args) -> None:
        if self._preview_job is not None:
            self.after_cancel(self._preview_job)
        url = self.url_var.get().strip()
        if not url or not self._is_valid_youtube_url(url):
            self._clear_preview()
            return
        self._preview_job = self.after(600, self._start_preview_fetch, url)

    def _start_preview_fetch(self, url: str) -> None:
        self._preview_job = None
        self.preview_frame.grid()
        self.preview_title_label.configure(text="Chargement...")
        self.preview_channel_label.configure(text="")
        self.preview_thumb_label.configure(text="")
        self._preview_full_image = None
        threading.Thread(target=self._fetch_preview, args=(url,), daemon=True).start()

    def _fetch_preview(self, url: str) -> None:
        try:
            import yt_dlp
            opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                self.after(0, self._clear_preview)
                return
            title = info.get("title", "")
            channel = info.get("channel", info.get("uploader", ""))
            thumb_url = info.get("thumbnail", "")
            full_image = None
            if thumb_url:
                try:
                    req = urllib.request.Request(
                        thumb_url,
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = resp.read()
                    full_image = Image.open(io.BytesIO(data))
                except Exception:
                    full_image = None
            self.after(0, self._show_preview, title, channel, full_image)
        except Exception as e:
            log(f"Apercu: {e}")
            self.after(0, self._clear_preview)

    def _show_preview(self, title: str, channel: str, image: Optional[Image.Image]) -> None:
        self.preview_title_label.configure(text=title)
        self.preview_channel_label.configure(text=channel)
        self._preview_full_image = image
        if image:
            thumb = image.copy()
            thumb.thumbnail((120, 90), Image.LANCZOS)
            self._preview_thumb_image = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(120, 90))
            self.preview_thumb_label.configure(image=self._preview_thumb_image, text="", cursor="hand2")
        else:
            self.preview_thumb_label.configure(text="Pas d'image", cursor="")

    def _clear_preview(self) -> None:
        self.preview_frame.grid_remove()
        self._preview_full_image = None

    def _enlarge_thumbnail(self) -> None:
        if not self._preview_full_image:
            return
        win = ctk.CTkToplevel(self)
        win.title("Apercu")
        win.transient(self)
        win.grab_set()
        img = self._preview_full_image.copy()
        max_w, max_h = 960, 720
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        lbl = ctk.CTkLabel(win, image=ctk_img, text="")
        lbl.pack(padx=10, pady=10)

    def toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        mode = "dark" if self._dark_mode else "light"
        label = "Mode: Sombre" if self._dark_mode else "Mode: Claire"

        ctk.set_appearance_mode(mode)
        self.theme_button.configure(text=label)

        self._settings["theme"] = mode
        _save_settings(self._settings)

    def update_options(self, value: str) -> None:
        if value == "Vidéo":
            formats = ["mp4", "mkv"]
            qualities = ["2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
            self.format_var.set("mp4")
            self.quality_var.set("1080p")
        else:
            formats = ["mp3", "m4a", "opus", "wav", "wma"]
            qualities = ["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"]
            self.format_var.set("mp3")
            self.quality_var.set("192 kbps")

        self.format_menu.configure(values=formats)
        self.quality_menu.configure(values=qualities)

    def browse(self) -> None:
        d = filedialog.askdirectory()
        if d:
            self.download_path.set(d)

    # ------------------------------------------------------------------
    # Lancement du telechargement
    # ------------------------------------------------------------------
    @staticmethod
    def _is_valid_youtube_url(url: str) -> bool:
        return bool(_YT_URL_RE.match(url))

    def start_thread(self) -> None:
        if self._downloading:
            return

        url = self.url_var.get().strip()
        if not url:
            log("Erreur: URL vide")
            return
        if not self._is_valid_youtube_url(url):
            log("Erreur: Ce lien ne semble pas etre une URL YouTube valide.")
            return

        self._downloading = True
        self._set_ui_downloading(True)
        threading.Thread(target=self._run_download, args=(url,), daemon=True).start()

    def cancel_download(self) -> None:
        log("Annulation en cours...")
        self.manager.cancel()

    def _set_ui_downloading(self, downloading: bool) -> None:
        if downloading:
            self.btn.configure(
                text="ANNULER", fg_color="#c0392b",
                hover_color="#a93226",
                command=self.cancel_download,
            )
            self.progress.set(0)
            self.pct_label.configure(text="0%")
            self.mode_option.configure(state="disabled")
            self.format_menu.configure(state="disabled")
            self.quality_menu.configure(state="disabled")
            self.url_entry.configure(state="disabled")
        else:
            default_fg = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
            default_hover = ctk.ThemeManager.theme["CTkButton"]["hover_color"]
            self.btn.configure(
                text="TELECHARGER",
                fg_color=default_fg,
                hover_color=default_hover,
                command=self.start_thread,
            )
            self.mode_option.configure(state="normal")
            self.format_menu.configure(state="normal")
            self.quality_menu.configure(state="normal")
            self.url_entry.configure(state="normal")

    def _update_progress(self, val: float, msg: Optional[str] = None) -> None:
        self.progress.set(val)
        if msg:
            self.pct_label.configure(text=msg)
        else:
            self.pct_label.configure(text=f"{int(val * 100)}%")

    def _reset_button(self) -> None:
        self._downloading = False
        self._set_ui_downloading(False)

    def _run_download(self, url: str) -> None:
        path = self.download_path.get()
        mode = self.mode_option.get()
        qual = self.quality_var.get()
        fmt = self.format_var.get()

        def update_prog(val: float, msg: Optional[str] = None) -> None:
            self.after(0, self._update_progress, val, msg)

        res = False
        try:
            res = self.manager.start_download(url, path, mode, qual, fmt, update_prog)
        except Exception as e:
            log(f"Erreur inattendue: {e}")
            res = False

        self.after(0, self._on_download_done, res)

    def _on_download_done(self, res: bool) -> None:
        if self.manager.is_cancelled:
            log("Telechargement annule.")
            self.progress.set(0)
            self.pct_label.configure(text="0%")
        elif res:
            log("Termine avec succes!")
            self.progress.set(1)
            self.pct_label.configure(text="100%")
        else:
            log("Telechargement ECHEC.")

        self._reset_button()

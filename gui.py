import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os
import sys
from utils import logger, log
from downloader import DownloadManager

APP_NAME = "UltraYouTube Downloader"
VERSION = "2.0.0"

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("900x700")
        
        # Grid Config
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # State
        self.download_path = tk.StringVar(value=os.path.join(os.getcwd(), "Downloads_YT"))
        self.url_var = tk.StringVar()
        self.format_mode = tk.StringVar(value="Vidéo") # Default mode
        self.format_var = tk.StringVar(value="mp4") # NEW
        self.quality_var = tk.StringVar(value="1080p")
        
        self.manager = DownloadManager()

        self.setup_ui()
        
        # Wire up the logger to our GUI text box
        logger.set_widget(self.log_textbox)
        log("GUI Initialized.")
        
        self.check_env()

    def check_env(self):
         if not getattr(sys, 'frozen', False):
             if sys.prefix == sys.base_prefix:
                 log("WARNING: Running outside venv.")

    def setup_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text=APP_NAME, font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20,10))
        
        # MODE SELECTION
        ctk.CTkLabel(self.sidebar, text="Type de contenu :", anchor="w").grid(row=1, column=0, padx=20, pady=(10,0))
        self.mode_option = ctk.CTkSegmentedButton(self.sidebar, values=["Vidéo", "Audio"], command=self.update_options)
        self.mode_option.grid(row=2, column=0, padx=20, pady=(5,10))
        self.mode_option.set("Vidéo")

        # FORMAT SELECTION
        ctk.CTkLabel(self.sidebar, text="Format :", anchor="w").grid(row=3, column=0, padx=20, pady=(10,0))
        self.format_menu = ctk.CTkComboBox(self.sidebar, variable=self.format_var)
        self.format_menu.grid(row=4, column=0, padx=20, pady=(0,10))

        # QUALITY SELECTION
        ctk.CTkLabel(self.sidebar, text="Qualité :", anchor="w").grid(row=5, column=0, padx=20, pady=(10,0))
        self.quality_menu = ctk.CTkComboBox(self.sidebar, variable=self.quality_var)
        self.quality_menu.grid(row=6, column=0, padx=20, pady=(0,20))

        # Initial population of menus
        self.update_options("Vidéo")

        # Main Area
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main.grid_columnconfigure(0, weight=1)

    def update_options(self, value):
        if value == "Vidéo":
            formats = ["mp4", "mkv", "webm"]
            qualities = ["2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
            self.format_var.set("mp4")
            self.quality_var.set("1080p")
        else: # Audio
            formats = ["mp3", "m4a", "opus", "wav"]
            qualities = ["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"]
            self.format_var.set("mp3")
            self.quality_var.set("192 kbps")
        
        self.format_menu.configure(values=formats)
        self.quality_menu.configure(values=qualities)
        self.main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main.grid_columnconfigure(0, weight=1)

        # Inputs
        ctk.CTkLabel(self.main, text="YouTube URL:").grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(self.main, textvariable=self.url_var, placeholder_text="Paste link here...").grid(row=1, column=0, sticky="ew", pady=(0,20))

        # Path
        path_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        path_frame.grid(row=2, column=0, sticky="ew", pady=(0,20))
        path_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(path_frame, textvariable=self.download_path, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0,10))
        ctk.CTkButton(path_frame, text="Browse", command=self.browse, width=100).grid(row=0, column=1)

        # Button & Progress
        self.btn = ctk.CTkButton(self.main, text="DOWNLOAD", command=self.start_thread, height=50, font=ctk.CTkFont(size=16, weight="bold"))
        self.btn.grid(row=3, column=0, sticky="ew", pady=10)

        self.progress = ctk.CTkProgressBar(self.main)
        self.progress.grid(row=4, column=0, sticky="ew", pady=10)
        self.progress.set(0)
        
        self.pct_label = ctk.CTkLabel(self.main, text="0%")
        self.pct_label.grid(row=5, column=0, sticky="e")

        # Log
        ctk.CTkLabel(self.main, text="Logs:").grid(row=6, column=0, sticky="w")
        self.log_textbox = ctk.CTkTextbox(self.main, height=200, font=("Consolas", 12))
        self.log_textbox.grid(row=7, column=0, sticky="nsew")
        self.log_textbox.configure(state="disabled")
        
        self.main.grid_rowconfigure(7, weight=1)

    def browse(self):
        d = filedialog.askdirectory()
        if d: self.download_path.set(d)

    def start_thread(self):
        url = self.url_var.get().strip()
        if not url:
            log("Error: Empty URL")
            return
        
        self.btn.configure(state="disabled")
        self.progress.set(0)
        self.pct_label.configure(text="0%")
        
        threading.Thread(target=self.run_process, args=(url,), daemon=True).start()

    def run_process(self, url):
        path = self.download_path.get()
        mode = self.mode_option.get() # Uses SegmentedButton directly
        qual = self.quality_var.get()
        fmt = self.format_var.get()
        
        def update_prog(val):
            self.progress.set(val)
            self.pct_label.configure(text=f"{int(val*100)}%")
        
        res = self.manager.start_download(url, path, mode, qual, fmt, update_prog)
        
        if res:
            log("Finished successfully!")
            self.progress.set(1)
            self.pct_label.configure(text="100%")
        else:
            log("Download FAILED.")
            
        self.btn.configure(state="normal")

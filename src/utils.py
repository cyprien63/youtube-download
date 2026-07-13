import sys
import threading
import datetime
from typing import Optional


class Logger:
    """Redirige les logs vers la zone de texte GUI (thread-safe)."""

    def __init__(self, text_widget=None):
        self.text_widget = text_widget
        self.queue: list[str] = []

    def set_widget(self, widget) -> None:
        self.text_widget = widget
        for msg in self.queue:
            self._write_to_widget(msg)
        self.queue = []

    def write(self, message: str) -> None:
        if not message:
            return

        sys.__stdout__.write(message)

        if not self.text_widget:
            self.queue.append(message)
            return

        self._write_to_widget(message)

    def _write_to_widget(self, message: str) -> None:
        def append() -> None:
            try:
                self.text_widget.configure(state="normal")
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                if message.strip():
                    self.text_widget.insert("end", f"[{timestamp}] {message}")
                else:
                    self.text_widget.insert("end", message)
                self.text_widget.see("end")
                self.text_widget.configure(state="disabled")
            except Exception as e:
                sys.__stderr__.write(f"[Logger] Erreur GUI: {e}\n")

        if threading.current_thread() is threading.main_thread():
            append()
        else:
            try:
                self.text_widget.after(0, append)
            except Exception as e:
                sys.__stderr__.write(f"[Logger] Erreur after(): {e}\n")

    def flush(self) -> None:
        pass


logger: Logger = Logger()


def log(msg: str) -> None:
    logger.write(msg + "\n")

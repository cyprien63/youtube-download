import sys
import threading
import datetime
import os

class Logger:
    """Redirects stdout/logs to the GUI console."""
    def __init__(self, text_widget=None):
        self.text_widget = text_widget
        self.queue = []

    def set_widget(self, widget):
        self.text_widget = widget
        # Flush queue
        for msg in self.queue:
            self.write_to_widget(msg)
        self.queue = []

    def write(self, message):
        if not message: return
        
        # Always print to real stdout for debug
        sys.__stdout__.write(message)

        if not self.text_widget:
            self.queue.append(message)
            return

        self.write_to_widget(message)

    def write_to_widget(self, message):
        def append():
            try:
                self.text_widget.configure(state="normal")
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                if message.strip():
                     self.text_widget.insert("end", f"[{timestamp}] {message}")
                else:
                    self.text_widget.insert("end", message)
                self.text_widget.see("end")
                self.text_widget.configure(state="disabled")
            except:
                pass 
        
        if threading.current_thread() is threading.main_thread():
            append()
        else:
            try:
                self.text_widget.after(0, append)
            except:
                pass

    def flush(self):
        pass

# Global logger instance to be used across modules
logger = Logger()

def log(msg):
    logger.write(msg + "\n")

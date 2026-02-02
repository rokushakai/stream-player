import tkinter as tk
import customtkinter as ctk
import platform


class VideoFrame(ctk.CTkFrame):
    """Container for embedded mpv video output."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="black")
        self.app = app

        if platform.system() == "Windows":
            self.video_container = tk.Frame(self, bg="black")
        else:
            self.video_container = tk.Frame(self, bg="black", container=True)

        self.video_container.pack(fill="both", expand=True)

    def get_wid(self) -> int:
        self.video_container.update_idletasks()
        return int(self.video_container.winfo_id())

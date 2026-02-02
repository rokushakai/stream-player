import customtkinter as ctk


class UrlBar(ctk.CTkFrame):
    """URL input bar with load button."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ctk.CTkLabel(self, text="URL:", width=40).pack(side="left", padx=(5, 2))

        self.url_entry = ctk.CTkEntry(self, placeholder_text="YouTube URL or streaming URL...")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=2)
        self.url_entry.bind("<Return>", lambda e: self._load())

        self.load_btn = ctk.CTkButton(self, text="Load", width=60, command=self._load)
        self.load_btn.pack(side="left", padx=(2, 5))

        self.title_label = ctk.CTkLabel(self, text="", width=200, anchor="w")
        self.title_label.pack(side="left", padx=5)

    def _load(self) -> None:
        url = self.url_entry.get().strip()
        if url:
            self.load_btn.configure(state="disabled", text="Loading...")
            self.app.load_url(url)

    def set_title(self, title: str) -> None:
        self.title_label.configure(text=title)
        self.load_btn.configure(state="normal", text="Load")

    def set_error(self, message: str) -> None:
        self.title_label.configure(text=f"Error: {message}")
        self.load_btn.configure(state="normal", text="Load")

import json
import os
import customtkinter as ctk


class UrlBar(ctk.CTkFrame):
    """URL input bar with load button and history dropdown."""

    HISTORY_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "url_history.json"
    )
    MAX_HISTORY = 50

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._history: list[dict] = []  # [{"url": ..., "title": ...}, ...]
        self._load_history()

        ctk.CTkLabel(self, text="URL:", width=40).pack(side="left", padx=(5, 2))

        self.url_entry = ctk.CTkEntry(self, placeholder_text="YouTube URL or streaming URL...")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=2)
        self.url_entry.bind("<Return>", lambda e: self._load())

        self.load_btn = ctk.CTkButton(self, text="Load", width=60, command=self._load)
        self.load_btn.pack(side="left", padx=(2, 2))

        # History dropdown
        self.history_var = ctk.StringVar(value="")
        history_labels = self._history_labels()
        self.history_menu = ctk.CTkOptionMenu(
            self,
            variable=self.history_var,
            values=history_labels if history_labels else ["(empty)"],
            command=self._on_history_selected,
            width=200
        )
        self.history_menu.pack(side="left", padx=(2, 2))
        if not history_labels:
            self.history_menu.configure(state="disabled")

        self.title_label = ctk.CTkLabel(self, text="", width=200, anchor="w")
        self.title_label.pack(side="left", padx=5)

    def _history_labels(self) -> list[str]:
        """Build display labels for history dropdown."""
        labels = []
        for i, item in enumerate(self._history):
            title = item.get("title", "")
            url = item.get("url", "")
            display = title if title else url
            # Truncate long titles
            if len(display) > 60:
                display = display[:57] + "..."
            labels.append(display)
        return labels

    def _on_history_selected(self, value: str) -> None:
        """When a history item is selected, populate the URL entry."""
        # Find matching history item by display label
        labels = self._history_labels()
        try:
            idx = labels.index(value)
        except ValueError:
            return
        item = self._history[idx]
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, item["url"])

    def _load(self) -> None:
        url = self.url_entry.get().strip()
        if url:
            self.load_btn.configure(state="disabled", text="Loading...")
            self.app.load_url(url)

    def add_to_history(self, url: str, title: str) -> None:
        """Add a URL to history (called after successful load)."""
        # Remove existing entry with same URL
        self._history = [h for h in self._history if h["url"] != url]
        # Insert at front
        self._history.insert(0, {"url": url, "title": title})
        # Trim
        self._history = self._history[:self.MAX_HISTORY]
        self._save_history()
        self._refresh_history_menu()

    def _refresh_history_menu(self) -> None:
        labels = self._history_labels()
        if labels:
            self.history_menu.configure(values=labels, state="normal")
            self.history_var.set("")
        else:
            self.history_menu.configure(values=["(empty)"], state="disabled")

    def _load_history(self) -> None:
        try:
            if os.path.exists(self.HISTORY_FILE):
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
        except Exception:
            self._history = []

    def _save_history(self) -> None:
        try:
            with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[UrlBar] save history error: {e}")

    def set_title(self, title: str) -> None:
        self.title_label.configure(text=title)
        self.load_btn.configure(state="normal", text="Load")

    def set_error(self, message: str) -> None:
        self.title_label.configure(text=f"Error: {message}")
        self.load_btn.configure(state="normal", text="Load")

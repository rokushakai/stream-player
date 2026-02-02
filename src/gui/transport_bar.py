import customtkinter as ctk


class TransportBar(ctk.CTkFrame):
    """Playback transport controls: play/pause, seek, etc."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="left", padx=10)

        self.seek_back_btn = ctk.CTkButton(
            btn_frame, text="\u23EA", width=36,
            command=lambda: app.player and app.player.seek_relative(-5)
        )
        self.seek_back_btn.pack(side="left", padx=2)

        self.play_btn = ctk.CTkButton(
            btn_frame, text="\u25B6", width=50,
            command=self._toggle_play
        )
        self.play_btn.pack(side="left", padx=2)

        self.seek_fwd_btn = ctk.CTkButton(
            btn_frame, text="\u23E9", width=36,
            command=lambda: app.player and app.player.seek_relative(5)
        )
        self.seek_fwd_btn.pack(side="left", padx=2)

        self.stop_btn = ctk.CTkButton(
            btn_frame, text="\u23F9", width=36,
            command=lambda: app.player and app.player.stop()
        )
        self.stop_btn.pack(side="left", padx=2)

        app.event_bus.on("playback_state_changed", self._on_state_changed)

    def _toggle_play(self) -> None:
        if self.app.player:
            self.app.player.toggle_pause()

    def _on_state_changed(self, state: str) -> None:
        text = "\u23F8" if state == "playing" else "\u25B6"
        self.after(0, lambda: self.play_btn.configure(text=text))

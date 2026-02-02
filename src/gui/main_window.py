import customtkinter as ctk
from .url_bar import UrlBar
from .video_frame import VideoFrame
from .timeline_canvas import TimelineCanvas
from .transport_bar import TransportBar
from .marker_panel import MarkerPanel
from .sequence_editor import SequenceEditor
from .effects_panel import EffectsPanel


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title("Stream Player")
        self.geometry("1100x800")
        self.minsize(900, 650)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Row 0: URL bar
        self.url_bar = UrlBar(self, app)
        self.url_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Row 1: Video frame
        self.video_frame = VideoFrame(self, app)
        self.video_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5)

        # Row 2: Timeline
        self.timeline = TimelineCanvas(self, app)
        self.timeline.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)

        # Row 3: Transport bar
        self.transport = TransportBar(self, app)
        self.transport.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=2)

        # Row 4: Bottom panels
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=2)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        self.marker_panel = MarkerPanel(bottom_frame, app)
        self.marker_panel.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        self.sequence_editor = SequenceEditor(bottom_frame, app)
        self.sequence_editor.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        # Row 5: Effects
        self.effects_panel = EffectsPanel(self, app)
        self.effects_panel.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Grid weights
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Keyboard shortcuts
        self.bind("<space>", lambda e: self._on_key_space())
        self.bind("m", lambda e: self.app.add_marker_at_current())
        self.bind("M", lambda e: self.app.add_marker_at_current())
        self.bind("<Left>", lambda e: self._seek_rel(-5))
        self.bind("<Right>", lambda e: self._seek_rel(5))
        self.bind("<Shift-Left>", lambda e: self._seek_rel(-1))
        self.bind("<Shift-Right>", lambda e: self._seek_rel(1))
        self.bind("[", lambda e: self._adjust_tempo(-0.05))
        self.bind("]", lambda e: self._adjust_tempo(0.05))
        self.bind("-", lambda e: self._adjust_transpose(-1))
        self.bind("=", lambda e: self._adjust_transpose(1))
        self.bind("+", lambda e: self._adjust_transpose(1))
        self.bind("l", lambda e: self._toggle_looper())
        self.bind("L", lambda e: self._toggle_looper())
        self.bind("<Escape>", lambda e: self.app.sequence_looper.stop())

    def _on_key_space(self) -> None:
        # Don't toggle if focus is on an entry widget
        if isinstance(self.focus_get(), ctk.CTkEntry):
            return
        if self.app.player:
            self.app.player.toggle_pause()

    def _seek_rel(self, offset: float) -> None:
        if self.app.player:
            self.app.player.seek_relative(offset)

    def _adjust_tempo(self, delta: float) -> None:
        new_val = self.app.audio_effects.tempo + delta
        self.app.audio_effects.tempo = new_val
        self.effects_panel.tempo_slider.set(self.app.audio_effects.tempo)
        self.effects_panel.tempo_label.configure(
            text=f"{self.app.audio_effects.tempo:.2f}x"
        )

    def _adjust_transpose(self, delta: int) -> None:
        new_val = self.app.audio_effects.semitones + delta
        self.app.audio_effects.semitones = new_val
        self.effects_panel.transpose_slider.set(self.app.audio_effects.semitones)
        s = self.app.audio_effects.semitones
        sign = "+" if s > 0 else ""
        self.effects_panel.transpose_label.configure(text=f"{sign}{s} st")

    def _toggle_looper(self) -> None:
        if self.app.sequence_looper.active:
            self.app.sequence_looper.stop()
        else:
            self.app.sequence_looper.start()

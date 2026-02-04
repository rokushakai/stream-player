import tkinter as tk
import customtkinter as ctk
from .url_bar import UrlBar
from .video_frame import VideoFrame
from .timeline_canvas import TimelineCanvas
from .transport_bar import TransportBar
from .marker_panel import MarkerPanel
from .sequence_editor import SequenceEditor
from .effects_panel import EffectsPanel


class MainWindow(ctk.CTk):
    """Main application window with resizable video area and fullscreen support."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title("Stream Player")
        self.geometry("1100x800")
        self.minsize(900, 650)
        self._is_fullscreen = False
        self._pre_fullscreen_geometry = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Top: URL bar (always visible)
        self.url_bar = UrlBar(self, app)
        self.url_bar.pack(fill="x", padx=5, pady=5)

        # Main content area: PanedWindow (vertical) for resizable video/panel split
        self.paned = tk.PanedWindow(
            self, orient=tk.VERTICAL, sashwidth=6, sashrelief=tk.RAISED,
            bg="#2B2B2B", opaqueresize=True
        )
        self.paned.pack(fill="both", expand=True, padx=5)

        # Top pane: Video + Timeline + Transport
        self.top_pane = ctk.CTkFrame(self.paned, fg_color="transparent")

        self.video_frame = VideoFrame(self.top_pane, app)
        self.video_frame.pack(fill="both", expand=True)

        self.timeline = TimelineCanvas(self.top_pane, app)
        self.timeline.pack(fill="x", pady=2)

        self.transport = TransportBar(self.top_pane, app)
        self.transport.pack(fill="x", pady=2)

        self.paned.add(self.top_pane, minsize=150, stretch="always")

        # Bottom pane: Marker panel + Sequence editor + Effects
        self.bottom_pane = ctk.CTkFrame(self.paned, fg_color="transparent")

        panels_frame = ctk.CTkFrame(self.bottom_pane)
        panels_frame.pack(fill="both", expand=True, pady=2)
        panels_frame.grid_columnconfigure(0, weight=1)
        panels_frame.grid_columnconfigure(1, weight=1)

        self.marker_panel = MarkerPanel(panels_frame, app)
        self.marker_panel.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        self.sequence_editor = SequenceEditor(panels_frame, app)
        self.sequence_editor.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        self.effects_panel = EffectsPanel(self.bottom_pane, app)
        self.effects_panel.pack(fill="x", pady=5)

        self.paned.add(self.bottom_pane, minsize=100, stretch="never")

        # Fullscreen button in transport area
        self._fullscreen_btn = ctk.CTkButton(
            self.transport, text="\u26F6", width=36,
            command=self.toggle_fullscreen
        )
        self._fullscreen_btn.pack(side="right", padx=5)

        # Keyboard shortcuts
        self.bind("<space>", lambda e: self._on_key_space())
        self.bind("m", lambda e: self._on_key_marker())
        self.bind("M", lambda e: self._on_key_marker())
        self.bind("<Left>", lambda e: self._seek_rel(-5))
        self.bind("<Right>", lambda e: self._seek_rel(5))
        self.bind("<Shift-Left>", lambda e: self._seek_rel(-1))
        self.bind("<Shift-Right>", lambda e: self._seek_rel(1))
        self.bind("[", lambda e: self._adjust_tempo(-0.05))
        self.bind("]", lambda e: self._adjust_tempo(0.05))
        self.bind("-", lambda e: self._adjust_transpose(-1))
        self.bind("=", lambda e: self._adjust_transpose(1))
        self.bind("+", lambda e: self._adjust_transpose(1))
        self.bind("l", lambda e: self._on_key_looper())
        self.bind("L", lambda e: self._on_key_looper())
        self.bind("<Escape>", lambda e: self._on_escape())
        self.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.bind("<Double-Button-1>", lambda e: self._on_double_click(e))

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode. Hides all UI except video in fullscreen."""
        if self._is_fullscreen:
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()

    def _enter_fullscreen(self) -> None:
        self._is_fullscreen = True
        self._pre_fullscreen_geometry = self.geometry()

        # Hide non-video UI (don't touch video_frame — mpv embed breaks on reparent)
        self.url_bar.pack_forget()
        self.timeline.pack_forget()
        self.transport.pack_forget()

        # Hide the bottom pane by removing from PanedWindow
        self.paned.forget(self.bottom_pane)

        self.attributes("-fullscreen", True)

    def _exit_fullscreen(self) -> None:
        self._is_fullscreen = False
        self.attributes("-fullscreen", False)

        # Restore timeline and transport inside top_pane
        self.timeline.pack(in_=self.top_pane, fill="x", pady=2)
        self.transport.pack(in_=self.top_pane, fill="x", pady=2)

        # Restore bottom pane in PanedWindow
        self.paned.add(self.bottom_pane, minsize=100, stretch="never")

        # Restore URL bar above paned
        self.url_bar.pack(fill="x", padx=5, pady=5, before=self.paned)

        if self._pre_fullscreen_geometry:
            self.geometry(self._pre_fullscreen_geometry)

    def _on_escape(self) -> None:
        if self._is_fullscreen:
            self._exit_fullscreen()
        else:
            self.app.sequence_looper.stop()

    def _on_double_click(self, event) -> None:
        """Double-click on video area toggles fullscreen."""
        # Check if click was on the video frame area
        widget = event.widget
        try:
            if widget == self.video_frame.video_container or widget.master == self.video_frame:
                self.toggle_fullscreen()
        except Exception:
            pass

    def _focus_on_entry(self) -> bool:
        """Check if focus is on a text entry widget."""
        return isinstance(self.focus_get(), (ctk.CTkEntry, tk.Entry))

    def _on_key_space(self) -> None:
        if self._focus_on_entry():
            return
        if self.app.player:
            self.app.player.toggle_pause()

    def _seek_rel(self, offset: float) -> None:
        if self._focus_on_entry():
            return
        if self.app.player:
            self.app.player.seek_relative(offset)

    def _adjust_tempo(self, delta: float) -> None:
        if self._focus_on_entry():
            return
        new_val = self.app.audio_effects.tempo + delta
        self.app.audio_effects.tempo = new_val
        tempo = self.app.audio_effects.tempo
        self.effects_panel.tempo_slider.set(tempo)
        self.effects_panel.tempo_label.configure(text=f"{tempo:.2f}x")
        self.effects_panel._update_preset_highlight(tempo)

    def _adjust_transpose(self, delta: int) -> None:
        if self._focus_on_entry():
            return
        new_val = self.app.audio_effects.semitones + delta
        self.app.audio_effects.semitones = new_val
        self.effects_panel.transpose_slider.set(self.app.audio_effects.semitones)
        s = self.app.audio_effects.semitones
        sign = "+" if s > 0 else ""
        self.effects_panel.transpose_label.configure(text=f"{sign}{s} st")

    def _on_key_marker(self) -> None:
        if self._focus_on_entry():
            return
        self.app.add_marker_at_current()

    def _on_key_looper(self) -> None:
        if self._focus_on_entry():
            return
        if self.app.sequence_looper.active:
            self.app.sequence_looper.stop()
        else:
            self.app.sequence_looper.start()

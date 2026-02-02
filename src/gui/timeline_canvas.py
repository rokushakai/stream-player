import tkinter as tk
import customtkinter as ctk
from ..utils.time_fmt import seconds_to_hms


class TimelineCanvas(ctk.CTkFrame):
    """Custom seekbar with marker visualization."""

    TRACK_HEIGHT = 6
    MARKER_SIZE = 10
    CANVAS_HEIGHT = 44

    def __init__(self, parent, app):
        super().__init__(parent, height=self.CANVAS_HEIGHT)
        self.app = app
        self._duration = 0.0
        self._position = 0.0
        self._markers = []
        self._dragging = False
        self._active_segments = []

        self.canvas = tk.Canvas(
            self, height=self.CANVAS_HEIGHT, bg="#2B2B2B",
            highlightthickness=0, cursor="hand2"
        )
        self.canvas.pack(side="left", fill="x", expand=True)

        self.time_label = ctk.CTkLabel(self, text="00:00 / 00:00", width=130)
        self.time_label.pack(side="right", padx=5)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Configure>", lambda e: self._redraw())

        app.event_bus.on("position_changed", self._on_position_changed)
        app.event_bus.on("duration_changed", self._on_duration_changed)
        app.event_bus.on("markers_changed", self._on_markers_changed)

    def set_active_segments(self, segments):
        self._active_segments = segments
        self._redraw()

    def _pos_to_x(self, pos: float) -> float:
        if self._duration <= 0:
            return 10
        width = self.canvas.winfo_width() - 20
        return 10 + (pos / self._duration) * width

    def _x_to_pos(self, x: float) -> float:
        width = self.canvas.winfo_width() - 20
        if width <= 0:
            return 0
        return max(0, min(self._duration, ((x - 10) / width) * self._duration))

    def _on_position_changed(self, position: float) -> None:
        if not self._dragging:
            self._position = position
            self.after(0, self._redraw)
            self.after(0, lambda: self.time_label.configure(
                text=f"{seconds_to_hms(position)} / {seconds_to_hms(self._duration)}"
            ))

    def _on_duration_changed(self, duration: float) -> None:
        self._duration = duration
        self.after(0, self._redraw)

    def _on_markers_changed(self, markers) -> None:
        self._markers = markers
        self.after(0, self._redraw)

    def _on_click(self, event) -> None:
        self._dragging = True
        pos = self._x_to_pos(event.x)
        self._position = pos
        self._redraw()

    def _on_drag(self, event) -> None:
        if self._dragging:
            pos = self._x_to_pos(event.x)
            self._position = pos
            self._redraw()

    def _on_release(self, event) -> None:
        if self._dragging:
            self._dragging = False
            pos = self._x_to_pos(event.x)
            if self.app.player:
                self.app.player.seek(pos)

    def _redraw(self) -> None:
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        cy = self.CANVAS_HEIGHT // 2

        # Draw active segment regions
        for seg in self._active_segments:
            start_marker = self.app.marker_manager.get_marker(seg.start_label)
            end_marker = self.app.marker_manager.get_marker(seg.end_label)
            if start_marker and end_marker:
                sx = self._pos_to_x(start_marker.position)
                ex = self._pos_to_x(end_marker.position)
                self.canvas.create_rectangle(
                    sx, cy - self.TRACK_HEIGHT - 2,
                    ex, cy + self.TRACK_HEIGHT + 2,
                    fill="#1F6AA5", stipple="gray25", outline=""
                )

        # Track background
        x1, x2 = 10, w - 10
        self.canvas.create_rectangle(
            x1, cy - self.TRACK_HEIGHT // 2,
            x2, cy + self.TRACK_HEIGHT // 2,
            fill="#555555", outline=""
        )

        # Progress
        px = self._pos_to_x(self._position)
        self.canvas.create_rectangle(
            x1, cy - self.TRACK_HEIGHT // 2,
            px, cy + self.TRACK_HEIGHT // 2,
            fill="#1F6AA5", outline=""
        )

        # Playhead
        self.canvas.create_oval(px - 7, cy - 7, px + 7, cy + 7, fill="#FFFFFF", outline="")

        # Markers
        for marker in self._markers:
            mx = self._pos_to_x(marker.position)
            self.canvas.create_polygon(
                mx, cy - self.TRACK_HEIGHT // 2 - 2,
                mx - self.MARKER_SIZE // 2, cy - self.TRACK_HEIGHT // 2 - self.MARKER_SIZE - 2,
                mx + self.MARKER_SIZE // 2, cy - self.TRACK_HEIGHT // 2 - self.MARKER_SIZE - 2,
                fill=marker.color, outline=""
            )
            self.canvas.create_text(
                mx, cy - self.TRACK_HEIGHT // 2 - self.MARKER_SIZE - 5,
                text=marker.label, fill=marker.color, font=("Arial", 8, "bold"),
                anchor="s"
            )

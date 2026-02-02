import threading
from typing import Optional, Callable
from .marker_manager import MarkerManager, Segment
from .events import EventBus


class SequenceLooper:
    """Manages ordered segment sequences and monitors playback position
    to trigger seeks at segment boundaries."""

    LOOP_SEQUENCE = "loop_sequence"
    LOOP_SINGLE = "loop_single"
    PLAY_ONCE = "play_once"

    SEEK_THRESHOLD = 0.15

    def __init__(self, event_bus: EventBus, marker_manager: MarkerManager):
        self._bus = event_bus
        self._markers = marker_manager
        self._segments: list[Segment] = []
        self._current_index: int = 0
        self._active: bool = False
        self._loop_mode: str = self.LOOP_SEQUENCE
        self._seek_callback: Optional[Callable[[float], None]] = None
        self._lock = threading.Lock()

        self._bus.on("position_changed", self._on_position_changed)

    def set_seek_callback(self, callback: Callable[[float], None]) -> None:
        self._seek_callback = callback

    def set_segments(self, segments: list[Segment]) -> None:
        with self._lock:
            self._segments = list(segments)
            self._current_index = 0
            self._bus.emit("sequence_changed", self._segments, self._current_index)

    def add_segment(self, start_label: str, end_label: str) -> None:
        seg = Segment(start_label=start_label, end_label=end_label)
        with self._lock:
            self._segments.append(seg)
            self._bus.emit("sequence_changed", self._segments, self._current_index)

    def remove_segment(self, index: int) -> None:
        with self._lock:
            if 0 <= index < len(self._segments):
                self._segments.pop(index)
                if self._current_index >= len(self._segments) and self._segments:
                    self._current_index = 0
                self._bus.emit("sequence_changed", self._segments, self._current_index)

    def reorder(self, old_index: int, new_index: int) -> None:
        with self._lock:
            if 0 <= old_index < len(self._segments) and 0 <= new_index < len(self._segments):
                seg = self._segments.pop(old_index)
                self._segments.insert(new_index, seg)
                self._bus.emit("sequence_changed", self._segments, self._current_index)

    def start(self) -> None:
        with self._lock:
            if not self._segments:
                return
            self._active = True
            self._current_index = 0
        self._seek_to_current_start()

    def stop(self) -> None:
        with self._lock:
            self._active = False

    @property
    def active(self) -> bool:
        return self._active

    @property
    def loop_mode(self) -> str:
        return self._loop_mode

    @loop_mode.setter
    def loop_mode(self, mode: str) -> None:
        self._loop_mode = mode

    def get_segments(self) -> list[Segment]:
        with self._lock:
            return list(self._segments)

    def get_current_index(self) -> int:
        return self._current_index

    def _on_position_changed(self, position: float) -> None:
        with self._lock:
            if not self._active or not self._segments:
                return

            segment = self._segments[self._current_index]
            end_marker = self._markers.get_marker(segment.end_label)
            if end_marker is None:
                return

            if position >= end_marker.position - self.SEEK_THRESHOLD:
                self._advance_segment()

    def _advance_segment(self) -> None:
        """Move to next segment. Called with lock held."""
        if self._loop_mode == self.LOOP_SINGLE:
            pass  # stay on current, re-seek to start
        elif self._loop_mode == self.LOOP_SEQUENCE:
            self._current_index = (self._current_index + 1) % len(self._segments)
        elif self._loop_mode == self.PLAY_ONCE:
            if self._current_index + 1 >= len(self._segments):
                self._active = False
                self._bus.emit("sequence_changed", self._segments, self._current_index)
                return
            self._current_index += 1

        self._bus.emit("segment_changed", self._current_index)
        threading.Thread(target=self._seek_to_current_start, daemon=True).start()

    def _seek_to_current_start(self) -> None:
        with self._lock:
            if not self._segments:
                return
            segment = self._segments[self._current_index]
        start_marker = self._markers.get_marker(segment.start_label)
        if start_marker and self._seek_callback:
            self._seek_callback(start_marker.position)

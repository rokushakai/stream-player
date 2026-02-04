import threading
import traceback
from typing import Optional, Callable
from .marker_manager import MarkerManager, Segment
from .events import EventBus


class SequenceLooper:
    """Manages ordered segment sequences and monitors playback position
    to trigger seeks at segment boundaries.

    Segments reference markers by immutable ID. Loop ranges are
    normalized to min/max of the two marker positions."""

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
        self._lock = threading.RLock()

        self._bus.on("position_changed", self._on_position_changed)

    def set_seek_callback(self, callback: Callable[[float], None]) -> None:
        self._seek_callback = callback

    def _resolve_range(self, seg: Segment) -> Optional[tuple[float, float]]:
        """Resolve a segment to (start_time, end_time), normalized min/max."""
        m1 = self._markers.get_by_id(seg.start_marker_id)
        m2 = self._markers.get_by_id(seg.end_marker_id)
        if m1 is None or m2 is None:
            return None
        return (min(m1.position, m2.position), max(m1.position, m2.position))

    def get_segment_label(self, seg: Segment) -> str:
        """Get display label like 'AB' from marker IDs."""
        m1 = self._markers.get_by_id(seg.start_marker_id)
        m2 = self._markers.get_by_id(seg.end_marker_id)
        l1 = m1.label if m1 else "?"
        l2 = m2.label if m2 else "?"
        return f"{l1}{l2}"

    def set_segments(self, segments: list[Segment]) -> None:
        with self._lock:
            self._segments = list(segments)
            self._current_index = 0
            self._bus.emit("sequence_changed", self._segments, self._current_index)

    def add_segment(self, start_marker_id: str, end_marker_id: str,
                    display_name: str = "") -> None:
        seg = Segment(start_marker_id=start_marker_id,
                      end_marker_id=end_marker_id,
                      display_name=display_name)
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

    def remove_segments_referencing(self, marker_id: str) -> None:
        """Remove all segments that reference the given marker ID."""
        with self._lock:
            self._segments = [
                s for s in self._segments
                if s.start_marker_id != marker_id and s.end_marker_id != marker_id
            ]
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
                print("[SequenceLooper] start: no segments, ignoring")
                return
            self._active = True
            self._current_index = 0
            print(f"[SequenceLooper] start: active, index=0, segments={len(self._segments)}")
        self._bus.emit("segment_changed", self._current_index)
        self._seek_to_current_start()

    def jump_to(self, index: int) -> None:
        """Jump to a specific segment and continue playback from there."""
        with self._lock:
            if not self._segments or not (0 <= index < len(self._segments)):
                return
            self._active = True
            self._current_index = index
        self._bus.emit("segment_changed", self._current_index)
        self._seek_to_current_start()

    def stop(self) -> None:
        with self._lock:
            was_active = self._active
            self._active = False
        if was_active:
            print("[SequenceLooper] stop: deactivated")
            self._bus.emit("sequence_changed", list(self._segments), self._current_index)
        else:
            print("[SequenceLooper] stop: already inactive")

    @property
    def active(self) -> bool:
        return self._active

    @property
    def loop_mode(self) -> str:
        return self._loop_mode

    @loop_mode.setter
    def loop_mode(self, mode: str) -> None:
        self._loop_mode = mode
        self._bus.emit("sequence_changed", list(self._segments), self._current_index)

    def get_segments(self) -> list[Segment]:
        with self._lock:
            return list(self._segments)

    def get_current_index(self) -> int:
        return self._current_index

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "segments": [
                    {
                        "start_marker_id": s.start_marker_id,
                        "end_marker_id": s.end_marker_id,
                        "display_name": s.display_name,
                    }
                    for s in self._segments
                ],
                "loop_mode": self._loop_mode,
            }

    def from_dict(self, data: dict) -> None:
        with self._lock:
            self._segments = []
            for d in data.get("segments", []):
                self._segments.append(Segment(
                    start_marker_id=d["start_marker_id"],
                    end_marker_id=d["end_marker_id"],
                    display_name=d.get("display_name", ""),
                ))
            self._loop_mode = data.get("loop_mode", self.LOOP_SEQUENCE)
            self._current_index = 0
        self._bus.emit("sequence_changed", list(self._segments), self._current_index)

    def _on_position_changed(self, position: float) -> None:
        with self._lock:
            if not self._active or not self._segments:
                return

            segment = self._segments[self._current_index]
            time_range = self._resolve_range(segment)
            if time_range is None:
                return

            _, end_time = time_range
            if position >= end_time - self.SEEK_THRESHOLD:
                label = self.get_segment_label(segment)
                print(f"[SequenceLooper] boundary reached: {label} end={end_time:.2f} pos={position:.2f}")
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
                print("[SequenceLooper] play_once: finished all segments")
                self._bus.emit("sequence_changed", list(self._segments), self._current_index)
                return
            self._current_index += 1

        seg = self._segments[self._current_index]
        label = self.get_segment_label(seg)
        print(f"[SequenceLooper] advance to index={self._current_index} ({label})")
        self._bus.emit("segment_changed", self._current_index)
        threading.Thread(target=self._seek_to_current_start, daemon=True).start()

    def _seek_to_current_start(self) -> None:
        with self._lock:
            if not self._segments:
                return
            segment = self._segments[self._current_index]
        time_range = self._resolve_range(segment)
        if time_range and self._seek_callback:
            start_time, _ = time_range
            label = self.get_segment_label(segment)
            print(f"[SequenceLooper] seeking to {label} start={start_time:.2f}")
            try:
                self._seek_callback(start_time)
            except Exception as e:
                print(f"[SequenceLooper] seek error: {e}")
                traceback.print_exc()

import string
import uuid
from dataclasses import dataclass, field
from typing import Optional
from .events import EventBus


def _gen_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class Marker:
    id: str
    label: str
    position: float
    color: str = "#FF6B6B"
    memo: str = ""

    def __lt__(self, other: 'Marker') -> bool:
        return self.position < other.position


@dataclass
class Segment:
    start_marker_id: str
    end_marker_id: str
    display_name: str = ""


class MarkerManager:
    """Manages markers with immutable IDs. Labels are display-only."""

    COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
        "#BB8FCE", "#85C1E9", "#F8C471", "#82E0AA",
    ]

    def __init__(self, event_bus: EventBus):
        self._bus = event_bus
        self._markers: list[Marker] = []
        self._label_counter = 0

    def _next_label(self) -> str:
        idx = self._label_counter
        self._label_counter += 1
        if idx < 26:
            return string.ascii_uppercase[idx]
        return string.ascii_uppercase[idx // 26 - 1] + string.ascii_uppercase[idx % 26]

    def add_marker(self, position: float, label: Optional[str] = None) -> Marker:
        if label is None:
            label = self._next_label()
        color = self.COLORS[len(self._markers) % len(self.COLORS)]
        marker = Marker(id=_gen_id(), label=label, position=position, color=color)
        self._markers.append(marker)
        self._markers.sort()
        self._bus.emit("markers_changed", self.get_markers())
        return marker

    def remove_marker(self, marker_id: str) -> None:
        self._markers = [m for m in self._markers if m.id != marker_id]
        self._bus.emit("markers_changed", self.get_markers())

    def get_markers(self) -> list[Marker]:
        return list(self._markers)

    def get_by_id(self, marker_id: str) -> Optional[Marker]:
        for m in self._markers:
            if m.id == marker_id:
                return m
        return None

    def get_by_label(self, label: str) -> Optional[Marker]:
        for m in self._markers:
            if m.label == label:
                return m
        return None

    def update_position(self, marker_id: str, position: float) -> None:
        for m in self._markers:
            if m.id == marker_id:
                m.position = position
                self._markers.sort()
                self._bus.emit("markers_changed", self.get_markers())
                return

    def update_memo(self, marker_id: str, memo: str) -> None:
        for m in self._markers:
            if m.id == marker_id:
                m.memo = memo
                self._bus.emit("markers_changed", self.get_markers())
                return

    def swap_labels(self, id_a: str, id_b: str) -> None:
        ma = self.get_by_id(id_a)
        mb = self.get_by_id(id_b)
        if ma and mb:
            ma.label, mb.label = mb.label, ma.label
            self._bus.emit("markers_changed", self.get_markers())

    def clear(self) -> None:
        self._markers.clear()
        self._label_counter = 0
        self._bus.emit("markers_changed", [])

    def to_dict(self) -> list[dict]:
        return [{'id': m.id, 'label': m.label, 'position': m.position,
                 'color': m.color, 'memo': m.memo}
                for m in self._markers]

    def from_dict(self, data: list[dict]) -> None:
        self._markers = []
        for d in data:
            if 'id' not in d:
                d['id'] = _gen_id()
            self._markers.append(Marker(**d))
        self._markers.sort()
        self._label_counter = len(self._markers)
        self._bus.emit("markers_changed", self.get_markers())

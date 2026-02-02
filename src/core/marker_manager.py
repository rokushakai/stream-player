import string
from dataclasses import dataclass
from typing import Optional
from .events import EventBus


@dataclass
class Marker:
    label: str
    position: float
    color: str = "#FF6B6B"

    def __lt__(self, other: 'Marker') -> bool:
        return self.position < other.position


@dataclass
class Segment:
    start_label: str
    end_label: str

    @property
    def name(self) -> str:
        return f"{self.start_label}{self.end_label}"


class MarkerManager:
    """Manages markers (labeled time points) with CRUD operations."""

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
        marker = Marker(label=label, position=position, color=color)
        self._markers.append(marker)
        self._markers.sort()
        self._bus.emit("markers_changed", self.get_markers())
        return marker

    def remove_marker(self, label: str) -> None:
        self._markers = [m for m in self._markers if m.label != label]
        self._bus.emit("markers_changed", self.get_markers())

    def get_markers(self) -> list[Marker]:
        return list(self._markers)

    def get_marker(self, label: str) -> Optional[Marker]:
        for m in self._markers:
            if m.label == label:
                return m
        return None

    def clear(self) -> None:
        self._markers.clear()
        self._label_counter = 0
        self._bus.emit("markers_changed", [])

    def to_dict(self) -> list[dict]:
        return [{'label': m.label, 'position': m.position, 'color': m.color}
                for m in self._markers]

    def from_dict(self, data: list[dict]) -> None:
        self._markers = [Marker(**d) for d in data]
        self._markers.sort()
        self._label_counter = len(self._markers)
        self._bus.emit("markers_changed", self.get_markers())

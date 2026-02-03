from collections import defaultdict
from typing import Callable, Any


class EventBus:
    """Lightweight pub/sub event bus for decoupling core logic from GUI."""

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable) -> None:
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        try:
            self._listeners[event].remove(callback)
        except ValueError:
            pass

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        for cb in self._listeners.get(event, []):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                import traceback
                print(f"[EventBus] error in '{event}' handler {cb.__qualname__}: {e}")
                traceback.print_exc()

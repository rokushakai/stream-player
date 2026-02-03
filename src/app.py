import threading
from .core.events import EventBus
from .core.player import MpvPlayer
from .core.stream_resolver import StreamResolver
from .core.marker_manager import MarkerManager
from .core.sequence_looper import SequenceLooper
from .core.audio_effects import AudioEffects
from .gui.main_window import MainWindow


class App:
    """Application controller wiring core modules and GUI together."""

    def __init__(self):
        self.event_bus = EventBus()
        self.resolver = StreamResolver()
        self.marker_manager = MarkerManager(self.event_bus)
        self.sequence_looper = SequenceLooper(self.event_bus, self.marker_manager)
        self.audio_effects = AudioEffects(self.event_bus)
        self.player: MpvPlayer = None

    def run(self) -> None:
        self.window = MainWindow(self)
        self.window.update()

        wid = self.window.video_frame.get_wid()
        self.player = MpvPlayer(self.event_bus, wid=wid)

        self.sequence_looper.set_seek_callback(self.player.seek)
        self.audio_effects.set_player(self.player)

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self.window.mainloop()

    def load_url(self, url: str) -> None:
        def _load():
            try:
                info = self.resolver.resolve(url)
                title = info.title
                self.window.after(0, lambda: self.window.url_bar.set_title(title))
                self.window.after(0, lambda: self.window.title(
                    f"Stream Player - {title}"
                ))
                self.window.after(0, lambda: self.window.url_bar.add_to_history(url, title))
                self.player.load(url)
                self.window.after(0, lambda: self.audio_effects.initialize_filter())
            except Exception as e:
                self.window.after(0, lambda: self.window.url_bar.set_error(str(e)))

        threading.Thread(target=_load, daemon=True).start()

    def add_marker_at_current(self) -> None:
        if self.player:
            pos = self.player.time_pos
            if pos is not None:
                self.marker_manager.add_marker(pos)

    def _on_close(self) -> None:
        self.sequence_looper.stop()
        if self.player:
            self.player.shutdown()
        self.window.destroy()

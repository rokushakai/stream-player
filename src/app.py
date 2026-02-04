import threading
from .core.events import EventBus
from .core.player import MpvPlayer
from .core.stream_resolver import StreamResolver
from .core.marker_manager import MarkerManager
from .core.sequence_looper import SequenceLooper
from .core.audio_effects import AudioEffects
from .core.loop_settings_store import LoopSettingsStore
from .gui.main_window import MainWindow


class App:
    """Application controller wiring core modules and GUI together."""

    def __init__(self):
        self.event_bus = EventBus()
        self.resolver = StreamResolver()
        self.marker_manager = MarkerManager(self.event_bus)
        self.sequence_looper = SequenceLooper(self.event_bus, self.marker_manager)
        self.audio_effects = AudioEffects(self.event_bus)
        self.loop_settings_store = LoopSettingsStore()
        self.player: MpvPlayer = None
        self._current_url: str | None = None
        self._restoring = False

        self.event_bus.on("markers_changed", lambda _: self._auto_save_loop_settings())
        self.event_bus.on("sequence_changed", lambda _s, _i: self._auto_save_loop_settings())

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
        self._save_current_settings()

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
                self._current_url = url
                self.window.after(0, lambda: self._restore_loop_settings(url))
            except Exception as e:
                self.window.after(0, lambda: self.window.url_bar.set_error(str(e)))

        threading.Thread(target=_load, daemon=True).start()

    def add_marker_at_current(self) -> None:
        if self.player:
            pos = self.player.time_pos
            if pos is not None:
                self.marker_manager.add_marker(pos)

    def _auto_save_loop_settings(self) -> None:
        if not self._current_url or self._restoring:
            return
        self.loop_settings_store.save_for_url(
            self._current_url,
            markers=self.marker_manager.to_dict(),
            segments=self.sequence_looper.to_dict()["segments"],
            loop_mode=self.sequence_looper.loop_mode,
        )

    def _save_current_settings(self) -> None:
        if not self._current_url:
            return
        self.loop_settings_store.save_for_url(
            self._current_url,
            markers=self.marker_manager.to_dict(),
            segments=self.sequence_looper.to_dict()["segments"],
            loop_mode=self.sequence_looper.loop_mode,
        )

    def _restore_loop_settings(self, url: str) -> None:
        self.sequence_looper.stop()
        self._restoring = True
        try:
            settings = self.loop_settings_store.load_for_url(url)
            if settings:
                self.marker_manager.from_dict(settings.get("markers", []))
                self.sequence_looper.from_dict({
                    "segments": settings.get("segments", []),
                    "loop_mode": settings.get("loop_mode", "loop_sequence"),
                })
            else:
                self.marker_manager.clear()
                self.sequence_looper.set_segments([])
        finally:
            self._restoring = False

    def _on_close(self) -> None:
        self._save_current_settings()
        self.sequence_looper.stop()
        if self.player:
            self.player.shutdown()
        self.window.destroy()

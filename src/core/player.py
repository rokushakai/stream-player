import mpv
import threading
from typing import Optional
from .events import EventBus


class MpvPlayer:
    """Wrapper around mpv.MPV for playback control with property observation."""

    def __init__(self, event_bus: EventBus, wid: Optional[int] = None):
        self._bus = event_bus
        self._lock = threading.Lock()

        mpv_kwargs = {
            'input_default_bindings': False,
            'input_vo_keyboard': False,
            'osc': False,
            'ytdl': True,
            'audio_pitch_correction': True,
        }
        if wid is not None:
            mpv_kwargs['wid'] = str(wid)

        self._mpv = mpv.MPV(**mpv_kwargs)

        self._mpv.observe_property('time-pos', self._on_time_pos)
        self._mpv.observe_property('duration', self._on_duration)
        self._mpv.observe_property('pause', self._on_pause_change)

    def _on_time_pos(self, _name: str, value: Optional[float]) -> None:
        if value is not None:
            self._bus.emit("position_changed", value)

    def _on_duration(self, _name: str, value: Optional[float]) -> None:
        if value is not None:
            self._bus.emit("duration_changed", value)

    def _on_pause_change(self, _name: str, value: Optional[bool]) -> None:
        state = "paused" if value else "playing"
        self._bus.emit("playback_state_changed", state)

    def load(self, url: str) -> None:
        self._mpv.play(url)

    def play(self) -> None:
        self._mpv.pause = False

    def pause(self) -> None:
        self._mpv.pause = True

    def toggle_pause(self) -> None:
        self._mpv.pause = not self._mpv.pause

    def stop(self) -> None:
        self._mpv.stop()

    def seek(self, position: float, reference: str = "absolute+exact") -> None:
        try:
            self._mpv.seek(position, reference)
        except Exception as e:
            print(f"[MpvPlayer] seek error: {e}")

    def seek_relative(self, offset: float) -> None:
        self._mpv.seek(offset, "relative+exact")

    @property
    def time_pos(self) -> Optional[float]:
        return self._mpv.time_pos

    @property
    def duration(self) -> Optional[float]:
        return self._mpv.duration

    @property
    def paused(self) -> bool:
        return self._mpv.pause

    @property
    def speed(self) -> float:
        return self._mpv.speed

    @speed.setter
    def speed(self, value: float) -> None:
        self._mpv.speed = max(0.25, min(2.0, value))

    def set_af(self, filter_string: str) -> None:
        self._mpv.af = filter_string

    def af_command(self, label: str, command: str, value: str) -> None:
        self._mpv.command('af-command', label, command, value)

    def shutdown(self) -> None:
        try:
            self._mpv.unobserve_property('time-pos', self._on_time_pos)
            self._mpv.unobserve_property('duration', self._on_duration)
            self._mpv.unobserve_property('pause', self._on_pause_change)
        except Exception:
            pass
        try:
            self._mpv.terminate()
        except Exception:
            pass

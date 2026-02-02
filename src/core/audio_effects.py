import math
from .events import EventBus


class AudioEffects:
    """Manages tempo and transpose via mpv's rubberband audio filter.

    - Tempo: mpv's speed property (rubberband preserves pitch)
    - Transpose: rubberband's pitch-scale parameter
    - Formula: pitch_scale = 2^(semitones/12)
    """

    FILTER_LABEL = "rb"
    MIN_TEMPO = 0.25
    MAX_TEMPO = 2.0
    MIN_SEMITONES = -12
    MAX_SEMITONES = 12

    def __init__(self, event_bus: EventBus):
        self._bus = event_bus
        self._tempo: float = 1.0
        self._semitones: int = 0
        self._player = None

    def set_player(self, player) -> None:
        self._player = player

    def initialize_filter(self) -> None:
        if self._player:
            try:
                self._player.set_af(f'@{self.FILTER_LABEL}:rubberband')
            except Exception:
                pass

    @property
    def tempo(self) -> float:
        return self._tempo

    @tempo.setter
    def tempo(self, value: float) -> None:
        value = max(self.MIN_TEMPO, min(self.MAX_TEMPO, value))
        self._tempo = value
        if self._player:
            self._player.speed = value
        self._bus.emit("effects_changed", self._tempo, self._semitones)

    @property
    def semitones(self) -> int:
        return self._semitones

    @semitones.setter
    def semitones(self, value: int) -> None:
        value = max(self.MIN_SEMITONES, min(self.MAX_SEMITONES, value))
        self._semitones = value
        pitch_scale = self._semitones_to_pitch_scale(value)
        if self._player:
            try:
                self._player.af_command(
                    self.FILTER_LABEL, 'set-pitch', str(pitch_scale)
                )
            except Exception:
                pass
        self._bus.emit("effects_changed", self._tempo, self._semitones)

    @staticmethod
    def _semitones_to_pitch_scale(semitones: int) -> float:
        return math.pow(2.0, semitones / 12.0)

    def reset(self) -> None:
        self.tempo = 1.0
        self.semitones = 0

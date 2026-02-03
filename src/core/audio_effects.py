import math
from .events import EventBus


class AudioEffects:
    """Manages tempo and transpose for mpv playback.

    - Tempo: mpv's speed property with audio_pitch_correction=True
      (mpv uses scaletempo2 internally to preserve pitch)
    - Transpose: lavfi asetrate + aresample for pitch shifting
    """

    MIN_TEMPO = 0.25
    MAX_TEMPO = 2.0
    MIN_SEMITONES = -12
    MAX_SEMITONES = 12
    SAMPLE_RATE = 48000

    def __init__(self, event_bus: EventBus):
        self._bus = event_bus
        self._tempo: float = 1.0
        self._semitones: int = 0
        self._player = None

    def set_player(self, player) -> None:
        self._player = player

    def initialize_filter(self) -> None:
        """Apply initial audio filter. Called after media loads."""
        self._apply_af()

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
        self._apply_af()
        self._bus.emit("effects_changed", self._tempo, self._semitones)

    def _apply_af(self) -> None:
        """Apply pitch shift using lavfi asetrate + aresample."""
        if not self._player:
            return

        if self._semitones == 0:
            af_str = ""
        else:
            # Pitch shift via sample rate manipulation
            # To shift up: increase asetrate (plays faster at higher pitch)
            # then aresample back to original rate (restores speed, keeps pitch)
            pitch_ratio = math.pow(2.0, self._semitones / 12.0)
            new_rate = int(self.SAMPLE_RATE * pitch_ratio)
            af_str = f"lavfi=[asetrate={new_rate},aresample={self.SAMPLE_RATE}]"

        try:
            self._player.set_af(af_str)
            print(f"[AudioEffects] af='{af_str}' semitones={self._semitones}")
        except Exception as e:
            print(f"[AudioEffects] set_af error: {e}")

    @staticmethod
    def _semitones_to_pitch_scale(semitones: int) -> float:
        return math.pow(2.0, semitones / 12.0)

    def reset(self) -> None:
        self._tempo = 1.0
        self._semitones = 0
        if self._player:
            self._player.speed = 1.0
        self._apply_af()
        self._bus.emit("effects_changed", self._tempo, self._semitones)

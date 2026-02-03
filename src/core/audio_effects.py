import math
from .events import EventBus


class AudioEffects:
    """Manages tempo and transpose for mpv playback.

    - Tempo: mpv's speed property with audio_pitch_correction=True
      (mpv uses scaletempo2 internally to preserve pitch)
    - Transpose: lavfi rubberband filter for pitch shifting
    """

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
        """Apply pitch shift using asetrate + atempo filters."""
        if not self._player:
            return

        if self._semitones == 0:
            af_str = ""
        else:
            # Compensate for observed +1 semitone offset
            # The system produces (input + 1) semitones, so use (desired - 1)
            adjusted = self._semitones - 1
            pitch_ratio = math.pow(2, adjusted / 12.0)
            new_rate = int(48000 * pitch_ratio)
            tempo_comp = 1.0 / pitch_ratio
            af_str = f'lavfi="asetrate={new_rate},atempo={tempo_comp:.6f}"'

        try:
            self._player.set_af(af_str)
            print(f"[AudioEffects] af='{af_str}' semitones={self._semitones} adjusted={self._semitones - 1 if self._semitones != 0 else 0}")
        except Exception as e:
            print(f"[AudioEffects] set_af error: {e}")

    def reset(self) -> None:
        self._tempo = 1.0
        self._semitones = 0
        if self._player:
            self._player.speed = 1.0
        self._apply_af()
        self._bus.emit("effects_changed", self._tempo, self._semitones)

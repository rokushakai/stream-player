import customtkinter as ctk


class EffectsPanel(ctk.CTkFrame):
    """Tempo and transpose controls."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Tempo presets + slider
        tempo_frame = ctk.CTkFrame(self, fg_color="transparent")
        tempo_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(tempo_frame, text="Tempo:", width=80).pack(side="left")

        self.PRESETS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        self._preset_btns = []
        for speed in self.PRESETS:
            btn = ctk.CTkButton(
                tempo_frame, text=f"{speed}x", width=42, height=26,
                font=("Arial", 11),
                fg_color="#1F6AA5" if speed == 1.0 else "#333333",
                command=lambda s=speed: self._set_tempo_preset(s)
            )
            btn.pack(side="left", padx=1)
            self._preset_btns.append((speed, btn))

        self.tempo_slider = ctk.CTkSlider(
            tempo_frame, from_=0.25, to=2.0, number_of_steps=35,
            command=self._on_tempo_change
        )
        self.tempo_slider.set(1.0)
        self.tempo_slider.pack(side="left", fill="x", expand=True, padx=10)
        self.tempo_label = ctk.CTkLabel(tempo_frame, text="1.00x", width=60)
        self.tempo_label.pack(side="left")

        # Transpose
        transpose_frame = ctk.CTkFrame(self, fg_color="transparent")
        transpose_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(transpose_frame, text="Transpose:", width=80).pack(side="left")

        # - button
        ctk.CTkButton(
            transpose_frame, text="-", width=32, height=26,
            command=lambda: self._adjust_transpose(-1)
        ).pack(side="left", padx=1)

        self.transpose_slider = ctk.CTkSlider(
            transpose_frame, from_=-12, to=12, number_of_steps=24,
            command=self._on_transpose_change
        )
        self.transpose_slider.set(0)
        self.transpose_slider.pack(side="left", fill="x", expand=True, padx=5)

        # + button
        ctk.CTkButton(
            transpose_frame, text="+", width=32, height=26,
            command=lambda: self._adjust_transpose(1)
        ).pack(side="left", padx=1)

        self.transpose_label = ctk.CTkLabel(transpose_frame, text="0 st", width=60)
        self.transpose_label.pack(side="left")

        # Reset
        ctk.CTkButton(self, text="Reset Effects", width=120, command=self._reset).pack(pady=5)

    def _set_tempo_preset(self, speed: float) -> None:
        self.app.audio_effects.tempo = speed
        self.tempo_slider.set(speed)
        self.tempo_label.configure(text=f"{speed:.2f}x")
        self._update_preset_highlight(speed)

    def _update_preset_highlight(self, active_speed: float) -> None:
        for speed, btn in self._preset_btns:
            if abs(speed - active_speed) < 0.01:
                btn.configure(fg_color="#1F6AA5")
            else:
                btn.configure(fg_color="#333333")

    def _on_tempo_change(self, value: float) -> None:
        self.app.audio_effects.tempo = value
        self.tempo_label.configure(text=f"{value:.2f}x")
        self._update_preset_highlight(value)

    def _on_transpose_change(self, value: float) -> None:
        semitones = int(round(value))
        self.app.audio_effects.semitones = semitones
        self._update_transpose_label(semitones)

    def _adjust_transpose(self, delta: int) -> None:
        new_val = self.app.audio_effects.semitones + delta
        self.app.audio_effects.semitones = new_val
        semitones = self.app.audio_effects.semitones
        self.transpose_slider.set(semitones)
        self._update_transpose_label(semitones)

    def _update_transpose_label(self, semitones: int) -> None:
        sign = "+" if semitones > 0 else ""
        self.transpose_label.configure(text=f"{sign}{semitones} st")

    def _reset(self) -> None:
        self.app.audio_effects.reset()
        self.tempo_slider.set(1.0)
        self.transpose_slider.set(0)
        self.tempo_label.configure(text="1.00x")
        self.transpose_label.configure(text="0 st")
        self._update_preset_highlight(1.0)

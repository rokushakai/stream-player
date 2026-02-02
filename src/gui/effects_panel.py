import customtkinter as ctk


class EffectsPanel(ctk.CTkFrame):
    """Tempo and transpose controls."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Tempo
        tempo_frame = ctk.CTkFrame(self, fg_color="transparent")
        tempo_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(tempo_frame, text="Tempo:", width=80).pack(side="left")
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
        self.transpose_slider = ctk.CTkSlider(
            transpose_frame, from_=-12, to=12, number_of_steps=24,
            command=self._on_transpose_change
        )
        self.transpose_slider.set(0)
        self.transpose_slider.pack(side="left", fill="x", expand=True, padx=10)
        self.transpose_label = ctk.CTkLabel(transpose_frame, text="0 st", width=60)
        self.transpose_label.pack(side="left")

        # Reset
        ctk.CTkButton(self, text="Reset Effects", width=120, command=self._reset).pack(pady=5)

    def _on_tempo_change(self, value: float) -> None:
        self.app.audio_effects.tempo = value
        self.tempo_label.configure(text=f"{value:.2f}x")

    def _on_transpose_change(self, value: float) -> None:
        semitones = int(round(value))
        self.app.audio_effects.semitones = semitones
        sign = "+" if semitones > 0 else ""
        self.transpose_label.configure(text=f"{sign}{semitones} st")

    def _reset(self) -> None:
        self.app.audio_effects.reset()
        self.tempo_slider.set(1.0)
        self.transpose_slider.set(0)
        self.tempo_label.configure(text="1.00x")
        self.transpose_label.configure(text="0 st")

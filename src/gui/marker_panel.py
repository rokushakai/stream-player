import customtkinter as ctk
from ..utils.time_fmt import seconds_to_mmss


class MarkerPanel(ctk.CTkFrame):
    """Panel for displaying and managing markers."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(5, 2))
        ctk.CTkLabel(header, text="Markers", font=("Arial", 14, "bold")).pack(side="left")
        ctk.CTkButton(
            header, text="+ Add", width=60,
            command=self._add_marker
        ).pack(side="right")
        ctk.CTkButton(
            header, text="Clear", width=60, fg_color="#666666",
            command=self._clear_markers
        ).pack(side="right", padx=2)

        self.list_frame = ctk.CTkScrollableFrame(self, height=150)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=2)

        app.event_bus.on("markers_changed", self._on_markers_changed)

    def _add_marker(self) -> None:
        self.app.add_marker_at_current()

    def _clear_markers(self) -> None:
        self.app.marker_manager.clear()

    def _on_markers_changed(self, markers) -> None:
        self.after(0, lambda: self._rebuild_list(markers))

    def _rebuild_list(self, markers) -> None:
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for marker in markers:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)

            color_box = ctk.CTkLabel(row, text="\u2588", text_color=marker.color, width=20)
            color_box.pack(side="left", padx=2)

            ctk.CTkLabel(row, text=marker.label, width=30,
                         font=("Courier", 13, "bold")).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=seconds_to_mmss(marker.position),
                         width=90).pack(side="left", padx=2)

            memo_entry = ctk.CTkEntry(row, width=140, placeholder_text="memo...")
            if marker.memo:
                memo_entry.insert(0, marker.memo)
            memo_entry.pack(side="left", padx=2)
            memo_entry.bind("<FocusOut>",
                            lambda e, lbl=marker.label, ent=memo_entry:
                            self.app.marker_manager.update_memo(lbl, ent.get().strip()))
            memo_entry.bind("<Return>",
                            lambda e, lbl=marker.label, ent=memo_entry:
                            self.app.marker_manager.update_memo(lbl, ent.get().strip()))

            ctk.CTkButton(
                row, text="\u2192", width=28,
                command=lambda p=marker.position: self._seek_to(p)
            ).pack(side="left", padx=1)

            ctk.CTkButton(
                row, text="\u00D7", width=28, fg_color="#CC3333",
                command=lambda lbl=marker.label: self.app.marker_manager.remove_marker(lbl)
            ).pack(side="left", padx=1)

    def _seek_to(self, position: float) -> None:
        if self.app.player:
            self.app.player.seek(position)

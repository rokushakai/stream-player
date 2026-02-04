import customtkinter as ctk
from ..utils.time_fmt import seconds_to_mmss


class MarkerPanel(ctk.CTkFrame):
    """Panel for displaying and managing markers. Uses marker IDs internally."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._swap_selection = None  # marker ID selected for swap
        self._rebuilding = False
        self._memo_entries = {}  # marker_id -> entry widget

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

        # Swap status label
        self.swap_label = ctk.CTkLabel(self, text="", height=20)
        self.swap_label.pack(fill="x", padx=5)

        app.event_bus.on("markers_changed", self._on_markers_changed)

    def _add_marker(self) -> None:
        self.app.add_marker_at_current()

    def _clear_markers(self) -> None:
        self._swap_selection = None
        self.swap_label.configure(text="")
        self.app.marker_manager.clear()

    def _on_markers_changed(self, markers) -> None:
        self.after(0, lambda: self._rebuild_list(markers))

    def _rebuild_list(self, markers) -> None:
        # Save pending memo values before destroying widgets
        self._rebuilding = True
        for mid, entry in self._memo_entries.items():
            try:
                val = entry.get().strip()
                m = self.app.marker_manager.get_by_id(mid)
                if m and m.memo != val:
                    m.memo = val  # Direct set without emitting event
            except Exception:
                pass
        self._memo_entries = {}

        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self._rebuilding = False

        for marker in markers:
            is_swap_selected = (marker.id == self._swap_selection)
            fg = "#2A4A6B" if is_swap_selected else "transparent"
            row = ctk.CTkFrame(self.list_frame, fg_color=fg)
            row.pack(fill="x", pady=1)

            color_box = ctk.CTkLabel(row, text="\u2588", text_color=marker.color, width=20)
            color_box.pack(side="left", padx=2)

            ctk.CTkLabel(row, text=marker.label, width=30,
                         font=("Courier", 13, "bold")).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=seconds_to_mmss(marker.position),
                         width=90).pack(side="left", padx=2)

            memo_entry = ctk.CTkEntry(row, width=120, placeholder_text="memo...")
            if marker.memo:
                memo_entry.insert(0, marker.memo)
            memo_entry.pack(side="left", padx=2)
            self._memo_entries[marker.id] = memo_entry
            memo_entry.bind("<FocusOut>",
                            lambda e, mid=marker.id, ent=memo_entry:
                            self._on_memo_focus_out(mid, ent))
            memo_entry.bind("<Return>",
                            lambda e, mid=marker.id, ent=memo_entry:
                            self.app.marker_manager.update_memo(mid, ent.get().strip()))

            # Swap label button
            swap_text = "\u2194" if not is_swap_selected else "\u2714"
            ctk.CTkButton(
                row, text=swap_text, width=28,
                fg_color="#DAA520" if is_swap_selected else None,
                command=lambda mid=marker.id: self._on_swap_click(mid)
            ).pack(side="left", padx=1)

            # Seek button
            ctk.CTkButton(
                row, text="\u2192", width=28,
                command=lambda p=marker.position: self._seek_to(p)
            ).pack(side="left", padx=1)

            # Delete button
            ctk.CTkButton(
                row, text="\u00D7", width=28, fg_color="#CC3333",
                command=lambda mid=marker.id: self._delete_marker(mid)
            ).pack(side="left", padx=1)

    def _on_memo_focus_out(self, marker_id: str, entry) -> None:
        if self._rebuilding:
            return
        try:
            val = entry.get().strip()
        except Exception:
            return
        self.app.marker_manager.update_memo(marker_id, val)

    def _on_swap_click(self, marker_id: str) -> None:
        if self._swap_selection is None:
            self._swap_selection = marker_id
            m = self.app.marker_manager.get_by_id(marker_id)
            lbl = m.label if m else "?"
            self.swap_label.configure(text=f"Swap: select another to swap with {lbl}")
            self._rebuild_list(self.app.marker_manager.get_markers())
        elif self._swap_selection == marker_id:
            # Deselect
            self._swap_selection = None
            self.swap_label.configure(text="")
            self._rebuild_list(self.app.marker_manager.get_markers())
        else:
            # Perform swap
            self.app.marker_manager.swap_labels(self._swap_selection, marker_id)
            self._swap_selection = None
            self.swap_label.configure(text="")

    def _delete_marker(self, marker_id: str) -> None:
        self.app.sequence_looper.remove_segments_referencing(marker_id)
        self.app.marker_manager.remove_marker(marker_id)
        if self._swap_selection == marker_id:
            self._swap_selection = None
            self.swap_label.configure(text="")

    def _seek_to(self, position: float) -> None:
        if self.app.player:
            self.app.player.seek(position)

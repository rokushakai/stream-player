import re
import customtkinter as ctk
from ..core.sequence_looper import SequenceLooper


class SequenceEditor(ctk.CTkFrame):
    """Sequence definition and reordering UI. Uses marker IDs internally,
    displays labels in dropdowns for user convenience."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._current_index = 0
        self._marker_id_map = {}  # label -> id

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(5, 2))
        ctk.CTkLabel(header, text="Sequence", font=("Arial", 14, "bold")).pack(side="left")

        # Loop mode
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(mode_frame, text="Loop:").pack(side="left", padx=2)
        self.loop_mode_var = ctk.StringVar(value="Loop Sequence")
        self.loop_mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            values=["Loop Sequence", "Loop Single", "Play Once"],
            variable=self.loop_mode_var,
            command=self._on_loop_mode_changed,
            width=140
        )
        self.loop_mode_menu.pack(side="left", padx=2)

        # Segment list
        self.list_frame = ctk.CTkScrollableFrame(self, height=120)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=2)

        # Add segment (dropdowns show labels, resolve to IDs on add)
        add_label = ctk.CTkLabel(self, text="Add Segment (select Start/End markers):",
                                 font=("Arial", 11), anchor="w")
        add_label.pack(fill="x", padx=8, pady=(4, 0))

        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(add_frame, text="Start:").pack(side="left", padx=2)
        self.start_var = ctk.StringVar()
        self.start_menu = ctk.CTkOptionMenu(add_frame, variable=self.start_var, values=[""], width=60)
        self.start_menu.pack(side="left", padx=2)
        ctk.CTkLabel(add_frame, text="End:").pack(side="left", padx=2)
        self.end_var = ctk.StringVar()
        self.end_menu = ctk.CTkOptionMenu(add_frame, variable=self.end_var, values=[""], width=60)
        self.end_menu.pack(side="left", padx=2)
        ctk.CTkButton(add_frame, text="+ Add", width=60, command=self._add_segment).pack(side="left", padx=4)

        # Segment name input
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", padx=5, pady=1)
        ctk.CTkLabel(name_frame, text="Name:").pack(side="left", padx=2)
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="e.g. 要件定義まとめ")
        self.name_entry.pack(side="left", fill="x", expand=True, padx=2)

        # Batch input
        batch_label = ctk.CTkLabel(self, text="Batch:  AB,CD,EF  or  AB:name,CD:name",
                                   font=("Arial", 10), anchor="w",
                                   text_color="#888888")
        batch_label.pack(fill="x", padx=8, pady=(6, 0))
        batch_frame = ctk.CTkFrame(self, fg_color="transparent")
        batch_frame.pack(fill="x", padx=5, pady=2)
        self.batch_entry = ctk.CTkEntry(
            batch_frame, placeholder_text="e.g. AB,CD,BC  or  ab:intro cd:verse ef"
        )
        self.batch_entry.pack(side="left", fill="x", expand=True, padx=2)
        self.batch_entry.bind("<Return>", lambda e: self._batch_add())
        ctk.CTkButton(batch_frame, text="Batch Add", width=80,
                       command=self._batch_add).pack(side="left", padx=4)
        self.batch_status = ctk.CTkLabel(self, text="", height=16,
                                          font=("Arial", 10), text_color="#FF6B6B")
        self.batch_status.pack(fill="x", padx=8)

        # Control buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)
        self.start_btn = ctk.CTkButton(
            btn_frame, text="\u25B6 Start", command=self._start_sequence
        )
        self.start_btn.pack(side="left", padx=5, expand=True, fill="x")
        self.stop_btn = ctk.CTkButton(
            btn_frame, text="\u23F9 Stop", fg_color="#CC3333",
            command=self._stop_sequence
        )
        self.stop_btn.pack(side="left", padx=5, expand=True, fill="x")

        app.event_bus.on("markers_changed", self._on_markers_changed)
        app.event_bus.on("sequence_changed", self._on_sequence_changed)
        app.event_bus.on("segment_changed", self._on_segment_changed)

    def _on_loop_mode_changed(self, value: str) -> None:
        mode_map = {
            "Loop Sequence": SequenceLooper.LOOP_SEQUENCE,
            "Loop Single": SequenceLooper.LOOP_SINGLE,
            "Play Once": SequenceLooper.PLAY_ONCE,
        }
        self.app.sequence_looper.loop_mode = mode_map.get(value, SequenceLooper.LOOP_SEQUENCE)

    def _on_markers_changed(self, markers) -> None:
        self._marker_id_map = {m.label: m.id for m in markers}
        labels = [m.label for m in markers]
        self.after(0, lambda: self._update_dropdowns(labels))
        # Also refresh segment list since labels may have changed
        segments = self.app.sequence_looper.get_segments()
        self.after(0, lambda: self._rebuild_list(segments))

    def _update_dropdowns(self, labels) -> None:
        if not labels:
            labels = [""]
        self.start_menu.configure(values=labels)
        self.end_menu.configure(values=labels)

    def _add_segment(self) -> None:
        start_label = self.start_var.get()
        end_label = self.end_var.get()
        start_id = self._marker_id_map.get(start_label)
        end_id = self._marker_id_map.get(end_label)
        if start_id and end_id and start_id != end_id:
            display_name = self.name_entry.get().strip()
            self.app.sequence_looper.add_segment(start_id, end_id, display_name)
            self.name_entry.delete(0, "end")

    def _parse_batch(self, text: str) -> list[tuple[str, str, str]]:
        """Parse batch input text into list of (start_label, end_label, name).

        Supported formats:
          AB CD EF        (space-separated)
          AB,CD,EF        (comma-separated)
          AB/CD/EF        (slash-separated)
          AB:intro,CD:verse  (colon attaches a name)
          Mixed delimiters and case are OK.
        """
        # Split by comma, space, or slash (but not colon — that's for names)
        tokens = re.split(r'[,\s/]+', text.strip())
        results = []
        for token in tokens:
            if not token:
                continue
            # Split name by colon: "AB:intro" -> ("AB", "intro")
            if ':' in token:
                pair_part, name_part = token.split(':', 1)
            else:
                pair_part, name_part = token, ""
            pair_part = pair_part.upper()
            if len(pair_part) < 2:
                continue
            # Support single-letter labels: "AB" -> ("A", "B")
            # Support multi-letter labels: "AAAB" -> ("AA", "AB") when labels are 2-char
            # Simple approach: try 1-char + 1-char first, then 2+2, etc.
            start_lbl, end_lbl = self._split_label_pair(pair_part)
            if start_lbl and end_lbl:
                results.append((start_lbl, end_lbl, name_part.strip()))
        return results

    def _split_label_pair(self, pair: str) -> tuple[str, str]:
        """Split a label pair like 'AB' or 'AAAB' into (start, end).

        Tries all possible split points and picks the one where both
        halves match known marker labels.
        """
        for i in range(1, len(pair)):
            left = pair[:i]
            right = pair[i:]
            if left in self._marker_id_map and right in self._marker_id_map:
                return (left, right)
        return ("", "")

    def _batch_add(self) -> None:
        text = self.batch_entry.get().strip()
        if not text:
            return
        parsed = self._parse_batch(text)
        if not parsed:
            self.batch_status.configure(
                text="No valid segments found. Use marker labels like AB,CD,EF",
                text_color="#FF6B6B")
            return

        added = 0
        skipped = []
        for start_lbl, end_lbl, name in parsed:
            start_id = self._marker_id_map.get(start_lbl)
            end_id = self._marker_id_map.get(end_lbl)
            if start_id and end_id and start_id != end_id:
                self.app.sequence_looper.add_segment(start_id, end_id, name)
                added += 1
            else:
                skipped.append(f"{start_lbl}{end_lbl}")

        self.batch_entry.delete(0, "end")
        if skipped:
            self.batch_status.configure(
                text=f"Added {added}, skipped: {', '.join(skipped)}",
                text_color="#DAA520")
        else:
            self.batch_status.configure(
                text=f"Added {added} segment(s)",
                text_color="#4ECDC4")

    def _start_sequence(self) -> None:
        self.app.sequence_looper.start()
        # Ensure playback is running (unpause if paused)
        if self.app.player and self.app.player.paused:
            self.app.player.play()

    def _stop_sequence(self) -> None:
        self.app.sequence_looper.stop()

    def _on_sequence_changed(self, segments, current_index) -> None:
        self._current_index = current_index
        self.after(0, lambda: self._rebuild_list(segments))

    def _on_segment_changed(self, index) -> None:
        self._current_index = index
        segments = self.app.sequence_looper.get_segments()
        self.after(0, lambda: self._rebuild_list(segments))

    def _rebuild_list(self, segments) -> None:
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for i, seg in enumerate(segments):
            is_active = (i == self._current_index and self.app.sequence_looper.active)
            fg = "#1F6AA5" if is_active else "transparent"
            row = ctk.CTkFrame(self.list_frame, fg_color=fg)
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(row, text=f"{i+1}.", width=30).pack(side="left", padx=2)

            # Resolve labels from IDs
            range_label = self.app.sequence_looper.get_segment_label(seg)
            ctk.CTkLabel(row, text=range_label, width=40,
                         font=("Courier", 13, "bold")).pack(side="left", padx=2)
            if seg.display_name:
                ctk.CTkLabel(row, text=seg.display_name, width=120,
                             anchor="w").pack(side="left", padx=2)

            ctk.CTkButton(
                row, text="\u25B2", width=28,
                command=lambda idx=i: self._move(idx, idx - 1)
            ).pack(side="left", padx=1)
            ctk.CTkButton(
                row, text="\u25BC", width=28,
                command=lambda idx=i: self._move(idx, idx + 1)
            ).pack(side="left", padx=1)
            ctk.CTkButton(
                row, text="\u00D7", width=28, fg_color="#CC3333",
                command=lambda idx=i: self.app.sequence_looper.remove_segment(idx)
            ).pack(side="left", padx=1)

    def _move(self, old_idx: int, new_idx: int) -> None:
        segments = self.app.sequence_looper.get_segments()
        if 0 <= new_idx < len(segments):
            self.app.sequence_looper.reorder(old_idx, new_idx)

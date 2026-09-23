# =============================================================================
# gui/analysis_frame.py
# FORENSEQUENCE - AI Forward Chaining & Risk Analysis (Placeholder Frame)
# =============================================================================

import tkinter as tk
import ttkbootstrap as ttk

from gui.theme import (
    VOID,
    ABYSS,
    DEEP,
    STEEL,
    CYAN,
    PINK,
    PEACH,
    PURPLE,
    PLUM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_FALLBACK,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_SECTION,
    FONT_BODY,
    FONT_SMALL,
    SP_2,
    SP_3,
    SP_4,
    SP_6,
    SP_8,
    create_glass_frame,
    create_section_header,
    create_badge,
    create_divider,
    create_neon_button,
)


class AnalysisFrame(ttk.Frame):
    """
    AI Rule Engine & Risk Analysis screen.
    Runs Propositional Logic and Forward Chaining across extracted facts
    to derive explainable forensic conclusions and calculate risk indices.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell

        self._build_ui()

    def _build_ui(self) -> None:
        """Render the AI Analysis interface."""
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))

        create_section_header(header_frame, "AI RULE ENGINE & REASONING").pack(anchor="w")

        title_row = ttk.Frame(header_frame, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, SP_2))

        ttk.Label(
            title_row,
            text="Deterministic Knowledge-Based Inference",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        badge = create_badge(title_row, "FORWARD CHAINING", PURPLE)
        badge.pack(side="left", padx=(SP_4, 0))

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Main AI glass panel
        glass = create_glass_frame(self, width=820, height=320, border_color=PURPLE, fill_color=DEEP)
        glass.pack(anchor="w", padx=SP_6, pady=(0, SP_6))
        inner = glass.inner_frame

        ttk.Label(
            inner,
            text="Forensic Propositional Logic Engine",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        ttk.Label(
            inner,
            text="FORENSEQUENCE utilizes a deterministic rule-based expert system (`rules.py`).\n"
                 "Facts extracted from diverse evidence streams are matched against logical antecedents\n"
                 "to produce rigorous, explainable findings with complete audit trails.",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        # Rule engine metrics preview
        metric_box = ttk.Frame(inner, style="Card.TFrame")
        metric_box.pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        create_badge(metric_box, "ACTIVE RULES: 16", PURPLE).pack(side="left", padx=(0, SP_2))
        create_badge(metric_box, "EXPLANATION TRACE: ACTIVE", CYAN).pack(side="left", padx=(0, SP_2))
        create_badge(metric_box, "CONFIDENCE: 100% DETERMINISTIC", PEACH).pack(side="left")

        # Action Buttons
        btn_row = ttk.Frame(inner, style="Card.TFrame")
        btn_row.pack(anchor="w", padx=SP_4, pady=(SP_3, 0))

        btn_run = create_neon_button(btn_row, text="EXECUTE INFERENCE ENGINE", variant="primary")
        btn_run.pack(side="left", padx=(0, SP_3))

        btn_trace = create_neon_button(btn_row, text="VIEW RULE DEFINITIONS", variant="secondary")
        btn_trace.pack(side="left")

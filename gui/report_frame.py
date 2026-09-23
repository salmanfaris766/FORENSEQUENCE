# =============================================================================
# gui/report_frame.py
# FORENSEQUENCE - Forensic Report Generator & PDF Export (Placeholder Frame)
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


class ReportFrame(ttk.Frame):
    """
    Forensic Investigation Report Generator screen.
    Compiles executive summaries, timeline graphs, AI explanation traces,
    and court-admissible PDF reports via ReportLab.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell

        self._build_ui()

    def _build_ui(self) -> None:
        """Render the Report Generator interface."""
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))

        create_section_header(header_frame, "FORENSIC REPORT GENERATOR").pack(anchor="w")

        title_row = ttk.Frame(header_frame, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, SP_2))

        ttk.Label(
            title_row,
            text="Court-Admissible Investigation Reports",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        badge = create_badge(title_row, "REPORTLAB PDF", PEACH)
        badge.pack(side="left", padx=(SP_4, 0))

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Main Report Glass Card
        glass = create_glass_frame(self, width=820, height=320, border_color=PEACH, fill_color=DEEP)
        glass.pack(anchor="w", padx=SP_6, pady=(0, SP_6))
        inner = glass.inner_frame

        ttk.Label(
            inner,
            text="Automated Forensic Report Compilation",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        ttk.Label(
            inner,
            text="Generates comprehensive digital forensic reports containing:\n"
                 "• Executive summary & risk scoring breakdown\n"
                 "• Chronological timeline reconstruction\n"
                 "• Chain-of-custody verification hashes\n"
                 "• Explainable AI rule traces & evidence provenance",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        # Format badges
        format_box = ttk.Frame(inner, style="Card.TFrame")
        format_box.pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        create_badge(format_box, "PDF DOCUMENT", PEACH).pack(side="left", padx=(0, SP_2))
        create_badge(format_box, "JSON AUDIT LOG", CYAN).pack(side="left", padx=(0, SP_2))
        create_badge(format_box, "TIMELINE PLOT", PURPLE).pack(side="left")

        # Action Buttons
        btn_row = ttk.Frame(inner, style="Card.TFrame")
        btn_row.pack(anchor="w", padx=SP_4, pady=(SP_3, 0))

        btn_pdf = create_neon_button(btn_row, text="GENERATE PDF REPORT", variant="primary")
        btn_pdf.pack(side="left", padx=(0, SP_3))

        btn_preview = create_neon_button(btn_row, text="PREVIEW IN-APP", variant="secondary")
        btn_preview.pack(side="left")

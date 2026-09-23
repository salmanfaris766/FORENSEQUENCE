# =============================================================================
# gui/about_frame.py
# FORENSEQUENCE - About & Architecture Credits (Placeholder Frame)
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
)


class AboutFrame(ttk.Frame):
    """
    About screen displaying project architecture, team roles,
    and technological overview.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell

        self._build_ui()

    def _build_ui(self) -> None:
        """Render the About interface."""
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))

        create_section_header(header_frame, "SYSTEM ARCHITECTURE & CREDITS").pack(anchor="w")

        title_row = ttk.Frame(header_frame, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, SP_2))

        ttk.Label(
            title_row,
            text="About FORENSEQUENCE",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        badge = create_badge(title_row, "VERSION 1.0", CYAN)
        badge.pack(side="left", padx=(SP_4, 0))

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Main About Glass Panel
        glass = create_glass_frame(self, width=820, height=360, border_color=PURPLE, fill_color=DEEP)
        glass.pack(anchor="w", padx=SP_6, pady=(0, SP_6))
        inner = glass.inner_frame

        ttk.Label(
            inner,
            text="AI-Based Digital Forensic Investigation & Real-Time Report Assistant",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        ttk.Label(
            inner,
            text="FORENSEQUENCE is a deterministic, knowledge-based expert system designed for high-integrity\n"
                 "incident response and forensic artifact analysis using Propositional Logic and Forward Chaining.",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(0, SP_4))

        # Engineering Team Roles
        team_frame = ttk.Frame(inner, style="Card.TFrame")
        team_frame.pack(fill="x", padx=SP_4, pady=(0, SP_2))

        ttk.Label(
            team_frame,
            text="Investigation & Development Team:",
            foreground=CYAN,
            background=DEEP,
            font=(FONT_FALLBACK, 10, "bold"),
        ).pack(anchor="w", pady=(0, SP_2))

        ttk.Label(
            team_frame,
            text="• Salman: UI/UX Glassmorphism Engineering, Evidence Parsers, Case Management & Live Watcher\n"
                 "• Kavya: Knowledge Base Engineering, Forward Chaining Inference, Risk Scoring & ReportLab PDF",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SMALL,
            justify="left",
        ).pack(anchor="w")

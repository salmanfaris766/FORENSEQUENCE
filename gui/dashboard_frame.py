# =============================================================================
# gui/dashboard_frame.py
# FORENSEQUENCE - Executive Forensic Dashboard (Placeholder Frame)
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
    FONT_MONO_BODY,
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


class DashboardFrame(ttk.Frame):
    """
    Executive Forensic Dashboard overview screen.
    Displays active case status, risk indices, timeline summary,
    and quick actions.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell

        self._build_ui()

    def _build_ui(self) -> None:
        """Render the dashboard layout."""
        # Top Header Section
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))

        create_section_header(header_frame, "INVESTIGATION DASHBOARD").pack(anchor="w")

        title_row = ttk.Frame(header_frame, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, SP_2))

        ttk.Label(
            title_row,
            text="Executive Forensic Overview",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        # Status badge
        badge = create_badge(title_row, "PHASE 4 READY", CYAN)
        badge.pack(side="left", padx=(SP_4, 0))

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Main metrics row
        cards_row = ttk.Frame(self, style="TFrame")
        cards_row.pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Card 1: Active Cases
        card1 = create_glass_frame(cards_row, width=260, height=120, border_color=CYAN)
        card1.pack(side="left", padx=(0, SP_4))
        inner1 = card1.inner_frame
        ttk.Label(
            inner1, text="ACTIVE CASES", foreground=TEXT_SECONDARY,
            background=DEEP, font=FONT_SMALL
        ).pack(anchor="w", padx=SP_4, pady=(SP_3, 0))
        ttk.Label(
            inner1, text="0", foreground=CYAN,
            background=DEEP, font=(FONT_FALLBACK, 24, "bold")
        ).pack(anchor="w", padx=SP_4)
        ttk.Label(
            inner1, text="Database initialization pending", foreground=TEXT_MUTED,
            background=DEEP, font=FONT_SMALL
        ).pack(anchor="w", padx=SP_4)

        # Card 2: AI Reasoning Findings
        card2 = create_glass_frame(cards_row, width=260, height=120, border_color=PURPLE)
        card2.pack(side="left", padx=(0, SP_4))
        inner2 = card2.inner_frame
        ttk.Label(
            inner2, text="AI FINDINGS", foreground=TEXT_SECONDARY,
            background=DEEP, font=FONT_SMALL
        ).pack(anchor="w", padx=SP_4, pady=(SP_3, 0))
        ttk.Label(
            inner2, text="0 INFERRED", foreground=PURPLE,
            background=DEEP, font=(FONT_FALLBACK, 24, "bold")
        ).pack(anchor="w", padx=SP_4)
        ttk.Label(
            inner2, text="Forward Chaining rules ready", foreground=TEXT_MUTED,
            background=DEEP, font=FONT_SMALL
        ).pack(anchor="w", padx=SP_4)

        # Card 3: Real-Time Risk Score
        card3 = create_glass_frame(cards_row, width=260, height=120, border_color=PEACH)
        card3.pack(side="left")
        inner3 = card3.inner_frame
        ttk.Label(
            inner3, text="RISK INDEX", foreground=TEXT_SECONDARY,
            background=DEEP, font=FONT_SMALL
        ).pack(anchor="w", padx=SP_4, pady=(SP_3, 0))
        ttk.Label(
            inner3, text="-- / 100", foreground=PEACH,
            background=DEEP, font=(FONT_FALLBACK, 24, "bold")
        ).pack(anchor="w", padx=SP_4)
        ttk.Label(
            inner3, text="No active evidence stream", foreground=TEXT_MUTED,
            background=DEEP, font=FONT_SMALL
        ).pack(anchor="w", padx=SP_4)

        # Detailed Module Status Panel
        panel = create_glass_frame(self, width=800, height=260, border_color=STEEL, fill_color=ABYSS)
        panel.pack(fill="x", padx=SP_6, pady=(0, SP_6))
        inner_panel = panel.inner_frame

        ttk.Label(
            inner_panel,
            text="System Architecture Status",
            foreground=TEXT_PRIMARY,
            background=ABYSS,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        ttk.Label(
            inner_panel,
            text="The shell, navigation routing, and visual primitives are loaded.\n"
                 "Select a module from the sidebar to inspect workspace frames.",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_BODY,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        # Action button inside dashboard
        btn_row = ttk.Frame(inner_panel, style="Panel.TFrame")
        btn_row.pack(anchor="w", padx=SP_4, pady=(0, SP_3))

        if self.shell:
            def _go_cases():
                self.shell.show_screen("Cases")
            btn = create_neon_button(btn_row, text="CREATE NEW CASE", command=_go_cases, variant="primary")
            btn.pack(side="left")

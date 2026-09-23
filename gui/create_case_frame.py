# =============================================================================
# gui/create_case_frame.py
# FORENSEQUENCE - Case Management & Intake (Placeholder Frame)
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
    create_styled_entry,
)


class CreateCaseFrame(ttk.Frame):
    """
    Case Management & Intake screen.
    Handles case creation, SHA-256 evidence ingestion,
    and chain-of-custody verification.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell

        self._build_ui()

    def _build_ui(self) -> None:
        """Render the Cases / Case intake interface."""
        # Top Header Section
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))

        create_section_header(header_frame, "CASE MANAGEMENT & INTAKE").pack(anchor="w")

        title_row = ttk.Frame(header_frame, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, SP_2))

        ttk.Label(
            title_row,
            text="Evidence Sources & Chain of Custody",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        badge = create_badge(title_row, "PHASE 5 READY", CYAN)
        badge.pack(side="left", padx=(SP_4, 0))

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Main Form / Overview glass panel
        glass = create_glass_frame(self, width=820, height=360, border_color=CYAN, fill_color=DEEP)
        glass.pack(anchor="w", padx=SP_6, pady=(0, SP_6))
        inner = glass.inner_frame

        ttk.Label(
            inner,
            text="Create New Investigation Case",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        ttk.Label(
            inner,
            text="Register a new digital forensic investigation. Ingest logs, file system artifacts,\n"
                 "browser history, and email dumps with automated SHA-256 integrity verification.",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        # Preview inputs
        form_row1 = ttk.Frame(inner, style="Card.TFrame")
        form_row1.pack(fill="x", padx=SP_4, pady=(0, SP_3))

        ttk.Label(
            form_row1,
            text="Case Name:",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_SMALL,
            width=14,
            anchor="w",
        ).pack(side="left")

        entry1 = create_styled_entry(form_row1, placeholder="e.g., CASE-2026-ALPHA-01")
        entry1.pack(side="left", fill="x", expand=True, ipady=SP_1)

        form_row2 = ttk.Frame(inner, style="Card.TFrame")
        form_row2.pack(fill="x", padx=SP_4, pady=(0, SP_4))

        ttk.Label(
            form_row2,
            text="Investigator:",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_SMALL,
            width=14,
            anchor="w",
        ).pack(side="left")

        entry2 = create_styled_entry(form_row2, placeholder="Lead Forensic Analyst")
        entry2.pack(side="left", fill="x", expand=True, ipady=SP_1)

        # Action Buttons
        btn_row = ttk.Frame(inner, style="Card.TFrame")
        btn_row.pack(anchor="w", padx=SP_4, pady=(SP_2, 0))

        btn_create = create_neon_button(btn_row, text="INITIALIZE CASE", variant="primary")
        btn_create.pack(side="left", padx=(0, SP_3))

        btn_browse = create_neon_button(btn_row, text="IMPORT EVIDENCE ARCHIVE", variant="secondary")
        btn_browse.pack(side="left")

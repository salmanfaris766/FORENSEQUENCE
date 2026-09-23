# =============================================================================
# gui/settings_frame.py
# FORENSEQUENCE - Application Configuration & Settings (Placeholder Frame)
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
    create_neon_button,
    create_styled_entry,
)


class SettingsFrame(ttk.Frame):
    """
    Application Settings & Preferences screen.
    Configure evidence storage paths, log verbosity, and AI reasoning parameters.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell

        self._build_ui()

    def _build_ui(self) -> None:
        """Render the Settings interface."""
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))

        create_section_header(header_frame, "CONFIGURATION & SETTINGS").pack(anchor="w")

        title_row = ttk.Frame(header_frame, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, SP_2))

        ttk.Label(
            title_row,
            text="Preferences & System Paths",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Main Settings Glass Panel
        glass = create_glass_frame(self, width=820, height=320, border_color=CYAN, fill_color=DEEP)
        glass.pack(anchor="w", padx=SP_6, pady=(0, SP_6))
        inner = glass.inner_frame

        ttk.Label(
            inner,
            text="Workspace Configuration",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        ttk.Label(
            inner,
            text="Default evidence repository and knowledge base preferences.",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        # Path setting
        form_row = ttk.Frame(inner, style="Card.TFrame")
        form_row.pack(fill="x", padx=SP_4, pady=(0, SP_4))

        ttk.Label(
            form_row,
            text="Evidence Store:",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_SMALL,
            width=14,
            anchor="w",
        ).pack(side="left")

        entry = create_styled_entry(form_row, placeholder="c:\\Users\\DELL\\FORENSEQUENCE\\evidence")
        entry.pack(side="left", fill="x", expand=True, ipady=SP_1)

        # Action Buttons
        btn_row = ttk.Frame(inner, style="Card.TFrame")
        btn_row.pack(anchor="w", padx=SP_4, pady=(SP_3, 0))

        btn_save = create_neon_button(btn_row, text="SAVE PREFERENCES", variant="primary")
        btn_save.pack(side="left", padx=(0, SP_3))

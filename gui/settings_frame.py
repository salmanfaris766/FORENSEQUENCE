# =============================================================================
# gui/settings_frame.py
# FORENSEQUENCE - Application Configuration & Settings
# =============================================================================

from __future__ import annotations

import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional

from config import ConfigManager
from gui.theme import (
    VOID,
    ABYSS,
    DEEP,
    STEEL,
    CYAN,
    PINK,
    PURPLE,
    PLUM,
    PEACH,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_FALLBACK,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_SECTION,
    FONT_BODY,
    FONT_SMALL,
    SP_1,
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
    bind_tooltip,
)


class SettingsFrame(ttk.Frame):
    """
    Application Settings & Preferences screen.
    Configure evidence storage paths, investigator profile, and live telemetry parameters.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell

        self.investigator_var = tk.StringVar()
        self.export_dir_var = tk.StringVar()
        self.poll_interval_var = tk.StringVar()
        self.toast_duration_var = tk.StringVar()
        self.auto_run_var = tk.BooleanVar()

        self._load_current_settings()
        self._build_ui()

    def _load_current_settings(self) -> None:
        """Load values from ConfigManager into variables."""
        cfg = ConfigManager.as_dict()
        self.investigator_var.set(str(cfg.get("default_investigator", "Salman")))
        self.export_dir_var.set(str(cfg.get("export_directory", "uploads")))
        self.poll_interval_var.set(str(cfg.get("live_poll_interval_ms", 200)))
        self.toast_duration_var.set(str(cfg.get("toast_duration_ms", 5000)))
        self.auto_run_var.set(bool(cfg.get("auto_run_analysis", True)))

    def _build_ui(self) -> None:
        """Render the Settings interface."""
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))

        create_section_header(header_frame, "CONFIGURATION & SETTINGS").pack(anchor="w")

        title_row = ttk.Frame(header_frame, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, SP_2))

        ttk.Label(
            title_row,
            text="Preferences & System Controls",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        self.status_msg_label = ttk.Label(
            title_row,
            text="",
            foreground=CYAN,
            background=VOID,
            font=FONT_SMALL,
        )
        self.status_msg_label.pack(side="right", padx=SP_4)

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Main Settings Glass Panel
        glass = create_glass_frame(self, width=860, height=480, border_color=CYAN, fill_color=DEEP)
        glass.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_6))
        inner = glass.inner_frame

        ttk.Label(
            inner,
            text="Investigation Workspace & Telemetry Profiles",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        ttk.Label(
            inner,
            text="Manage default investigator assignments, storage repositories, and event monitoring cadence.",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(0, SP_4))

        # Form Container
        form_frame = ttk.Frame(inner, style="Card.TFrame")
        form_frame.pack(fill="both", expand=True, padx=SP_4, pady=(0, SP_2))

        # 1. Investigator Name
        r1 = ttk.Frame(form_frame, style="Card.TFrame")
        r1.pack(fill="x", pady=SP_2)
        ttk.Label(
            r1,
            text="Default Investigator:",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            width=22,
            anchor="w",
        ).pack(side="left")
        self.ent_investigator = tk.Entry(
            r1,
            textvariable=self.investigator_var,
            bg=ABYSS,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            bd=0,
            font=FONT_BODY,
            highlightthickness=1,
            highlightbackground=PLUM,
            highlightcolor=CYAN,
        )
        self.ent_investigator.pack(side="left", fill="x", expand=True, ipady=SP_1)
        bind_tooltip(self.ent_investigator, "Default examiner name auto-populated during case intake.")

        # 2. Export / Evidence Directory
        r2 = ttk.Frame(form_frame, style="Card.TFrame")
        r2.pack(fill="x", pady=SP_2)
        ttk.Label(
            r2,
            text="Evidence Store Dir:",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            width=22,
            anchor="w",
        ).pack(side="left")
        self.ent_export_dir = tk.Entry(
            r2,
            textvariable=self.export_dir_var,
            bg=ABYSS,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            bd=0,
            font=FONT_BODY,
            highlightthickness=1,
            highlightbackground=PLUM,
            highlightcolor=CYAN,
        )
        self.ent_export_dir.pack(side="left", fill="x", expand=True, ipady=SP_1)
        bind_tooltip(self.ent_export_dir, "Target subdirectory for uploaded evidence and report artifacts.")

        # 3. Live Poll Interval
        r3 = ttk.Frame(form_frame, style="Card.TFrame")
        r3.pack(fill="x", pady=SP_2)
        ttk.Label(
            r3,
            text="Live Poll Interval (ms):",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            width=22,
            anchor="w",
        ).pack(side="left")
        self.ent_poll = tk.Entry(
            r3,
            textvariable=self.poll_interval_var,
            bg=ABYSS,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            bd=0,
            font=FONT_BODY,
            highlightthickness=1,
            highlightbackground=PLUM,
            highlightcolor=CYAN,
        )
        self.ent_poll.pack(side="left", fill="x", expand=True, ipady=SP_1)
        bind_tooltip(self.ent_poll, "Background event polling cycle cadence in milliseconds (default 200).")

        # 4. Toast Duration
        r4 = ttk.Frame(form_frame, style="Card.TFrame")
        r4.pack(fill="x", pady=SP_2)
        ttk.Label(
            r4,
            text="Toast Duration (ms):",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            width=22,
            anchor="w",
        ).pack(side="left")
        self.ent_toast = tk.Entry(
            r4,
            textvariable=self.toast_duration_var,
            bg=ABYSS,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            bd=0,
            font=FONT_BODY,
            highlightthickness=1,
            highlightbackground=PLUM,
            highlightcolor=CYAN,
        )
        self.ent_toast.pack(side="left", fill="x", expand=True, ipady=SP_1)
        bind_tooltip(self.ent_toast, "Persistence duration for bottom-right cybernetic toast cards.")

        # 5. Auto Run Analysis Checkbox
        r5 = ttk.Frame(form_frame, style="Card.TFrame")
        r5.pack(fill="x", pady=SP_2)
        ttk.Label(
            r5,
            text="Automation Rules:",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            width=22,
            anchor="w",
        ).pack(side="left")

        chk = tk.Checkbutton(
            r5,
            text="Automatically execute Forward Chaining inference upon evidence upload",
            variable=self.auto_run_var,
            bg=DEEP,
            fg=TEXT_PRIMARY,
            selectcolor=ABYSS,
            activebackground=DEEP,
            activeforeground=CYAN,
            font=FONT_BODY,
            bd=0,
            highlightthickness=0,
        )
        chk.pack(side="left", anchor="w")
        bind_tooltip(chk, "When enabled, triggers deterministic rule deduction immediately after evidence ingest.")

        # Action Buttons
        btn_row = ttk.Frame(inner, style="Card.TFrame")
        btn_row.pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        btn_save = create_neon_button(
            btn_row,
            text="SAVE PREFERENCES",
            variant="primary",
            command=self._save_settings,
        )
        btn_save.pack(side="left", padx=(0, SP_3))

        btn_reset = create_neon_button(
            btn_row,
            text="RESET TO DEFAULTS",
            variant="secondary",
            command=self._reset_defaults,
        )
        btn_reset.pack(side="left", padx=(0, SP_3))

    def _save_settings(self) -> None:
        """Persist settings to ConfigManager."""
        try:
            poll_ms = int(self.poll_interval_var.get().strip() or "200")
            toast_ms = int(self.toast_duration_var.get().strip() or "5000")
        except ValueError:
            self.status_msg_label.config(text="ERROR: INTERVAL VALUES MUST BE NUMERIC", foreground=PINK)
            return

        ConfigManager.set("default_investigator", self.investigator_var.get().strip())
        ConfigManager.set("export_directory", self.export_dir_var.get().strip() or "uploads")
        ConfigManager.set("live_poll_interval_ms", poll_ms)
        ConfigManager.set("toast_duration_ms", toast_ms)
        ConfigManager.set("auto_run_analysis", self.auto_run_var.get())

        self.status_msg_label.config(text="CONFIG PERSISTED TO CONFIG.JSON", foreground=CYAN)
        if self.shell and hasattr(self.shell, "set_status"):
            self.shell.set_status("CONFIG: PREFERENCES PERSISTED")

    def _reset_defaults(self) -> None:
        """Reset ConfigManager to defaults and update fields."""
        ConfigManager.reset_to_defaults()
        self._load_current_settings()
        self.status_msg_label.config(text="CONFIG RESET TO SYSTEM DEFAULTS", foreground=PEACH)
        if self.shell and hasattr(self.shell, "set_status"):
            self.shell.set_status("CONFIG: RESTORED FACTORY DEFAULTS")

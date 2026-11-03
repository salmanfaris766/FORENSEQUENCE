# =============================================================================
# gui/settings_frame.py
# FORENSEQUENCE - Workstation Preferences & Telemetry Configuration
# =============================================================================

from __future__ import annotations

import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional

from config import ConfigManager
from gui.theme import (
    APP_BG,
    BG_SECONDARY,
    PANEL_BG,
    PANEL_ELEVATED,
    BORDER,
    BORDER_SECONDARY,
    MINT,
    CYAN,
    TEAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    CRITICAL,
    HIGH,
    FONT_FALLBACK,
    FONT_MONO_FALLBACK,
    FS_XS,
    FS_SM,
    FS_BASE,
    FS_MD,
    FS_XL,
    SP_1,
    SP_2,
    SP_3,
    SP_4,
    SP_6,
    SP_8,
    create_soc_panel,
    create_soc_button,
    create_soc_badge,
    create_section_header,
    create_divider,
    bind_tooltip,
)


class SettingsFrame(ttk.Frame):
    """
    Workstation Preferences & Telemetry Configuration screen.
    Manages investigator profiles, evidence storage paths, and live telemetry parameters.
    Persists configuration to config.json via ConfigManager.
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
        """Load values from ConfigManager into tkinter variables."""
        cfg = ConfigManager.as_dict()
        self.investigator_var.set(str(cfg.get("default_investigator", "Salman")))
        self.export_dir_var.set(str(cfg.get("export_directory", "uploads")))
        self.poll_interval_var.set(str(cfg.get("live_poll_interval_ms", 200)))
        self.toast_duration_var.set(str(cfg.get("toast_duration_ms", 5000)))
        self.auto_run_var.set(bool(cfg.get("auto_run_analysis", True)))

    # =========================================================================
    # Layout
    # =========================================================================

    def _build_ui(self) -> None:
        self.configure(style="TFrame")

        # Header Bar
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))

        ttk.Label(
            header,
            text="SYSTEM / SETTINGS",
            foreground=TEXT_MUTED,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_XS, "normal"),
        ).pack(anchor="w")

        title_row = ttk.Frame(header, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, 0))

        ttk.Label(
            title_row,
            text="Workstation Preferences & Telemetry",
            foreground=TEXT_PRIMARY,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_XL, "bold"),
        ).pack(side="left")

        self.status_msg = ttk.Label(
            title_row,
            text="",
            foreground=CYAN,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_SM, "bold"),
        )
        self.status_msg.pack(side="right", padx=SP_4)

        ttk.Label(
            header,
            text="Manage default investigator assignments, storage repositories, and event monitoring cadence.",
            foreground=TEXT_MUTED,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
        ).pack(anchor="w", pady=(2, 0))

        create_divider(self, color=BORDER).pack(fill="x", padx=SP_6, pady=(SP_3, SP_4))

        # Two-column layout
        body = ttk.Frame(self, style="TFrame")
        body.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_6))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        # Left Panel: Investigation Workspace
        left_col = ttk.Frame(body, style="TFrame")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, SP_3))
        self._build_workspace_panel(left_col)

        # Right Panel: Real-time Telemetry
        right_col = ttk.Frame(body, style="TFrame")
        right_col.grid(row=0, column=1, sticky="nsew")
        self._build_telemetry_panel(right_col)

    # =========================================================================
    # Left Panel: Investigation Workspace Preferences
    # =========================================================================

    def _build_workspace_panel(self, parent: ttk.Frame) -> None:
        panel = create_soc_panel(parent, border_color=CYAN, bg=PANEL_BG)
        panel.pack(fill="both", expand=True)
        inner = panel.inner_frame

        create_section_header(inner, "INVESTIGATION WORKSPACE PREFERENCES").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )
        ttk.Label(
            inner,
            text="Default investigator profile and evidence storage configuration.",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_3))

        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(0, SP_3))

        # Field: Default Investigator
        self._build_field_row(inner, "DEFAULT INVESTIGATOR", self.investigator_var,
                              "Default examiner name auto-populated during case intake.")

        # Field: Evidence Store Directory
        self._build_field_row(inner, "EVIDENCE STORE DIRECTORY", self.export_dir_var,
                              "Target subdirectory for uploaded evidence and report artifacts.")

        # Checkbox: Auto-Run Analysis
        chk_frame = ttk.Frame(inner, style="Card.TFrame")
        chk_frame._custom_bg = PANEL_BG
        chk_frame.pack(fill="x", padx=SP_4, pady=SP_2)

        chk = tk.Checkbutton(
            chk_frame,
            text="Automatically execute Forward Chaining inference upon evidence upload",
            variable=self.auto_run_var,
            bg=PANEL_BG,
            fg=TEXT_PRIMARY,
            selectcolor=BG_SECONDARY,
            activebackground=PANEL_BG,
            activeforeground=CYAN,
            font=(FONT_FALLBACK, FS_SM, "normal"),
            bd=0,
            highlightthickness=0,
        )
        chk.pack(anchor="w")
        bind_tooltip(chk, "When enabled, triggers deterministic rule deduction immediately after evidence ingest.")

        # Action Buttons
        btn_row = ttk.Frame(inner, style="Card.TFrame")
        btn_row._custom_bg = PANEL_BG
        btn_row.pack(anchor="w", padx=SP_4, pady=(SP_6, SP_3))

        btn_save = create_soc_button(
            btn_row,
            text="SAVE CONFIGURATION",
            variant="primary",
            command=self._save_settings,
            bg=PANEL_BG,
        )
        btn_save.pack(side="left", padx=(0, SP_3))

        btn_reset = create_soc_button(
            btn_row,
            text="RESET DEFAULTS",
            variant="secondary",
            command=self._reset_defaults,
            bg=PANEL_BG,
        )
        btn_reset.pack(side="left")

    # =========================================================================
    # Right Panel: Real-time Telemetry
    # =========================================================================

    def _build_telemetry_panel(self, parent: ttk.Frame) -> None:
        panel = create_soc_panel(parent, border_color=BORDER_SECONDARY, bg=PANEL_BG)
        panel.pack(fill="both", expand=True)
        inner = panel.inner_frame

        create_section_header(inner, "REAL-TIME TELEMETRY CONFIGURATION").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )
        ttk.Label(
            inner,
            text="Event polling cadence and notification persistence controls.",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_3))

        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(0, SP_3))

        # Field: Live Poll Interval
        self._build_field_row(inner, "LIVE POLL INTERVAL (MS)", self.poll_interval_var,
                              "Background event polling cycle cadence in milliseconds (default 200).")

        # Field: Toast Duration
        self._build_field_row(inner, "TOAST DISPLAY DURATION (MS)", self.toast_duration_var,
                              "Persistence duration for toast notification cards (default 5000).")

        # Current config display
        info_box = tk.Frame(inner, bg=BG_SECONDARY, highlightthickness=1, highlightbackground=BORDER, bd=0)
        info_box.pack(fill="x", padx=SP_4, pady=(SP_6, SP_3))

        ttk.Label(
            info_box,
            text="ACTIVE CONFIGURATION FILE: config.json",
            foreground=TEXT_MUTED,
            background=BG_SECONDARY,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
        ).pack(anchor="w", padx=SP_3, pady=(SP_2, SP_1))

        self.lbl_config_info = ttk.Label(
            info_box,
            text="Configuration loaded from local workspace.",
            foreground=TEXT_SECONDARY,
            background=BG_SECONDARY,
            font=(FONT_FALLBACK, FS_SM, "normal"),
        )
        self.lbl_config_info.pack(anchor="w", padx=SP_3, pady=(0, SP_2))

    # =========================================================================
    # Shared field builder
    # =========================================================================

    def _build_field_row(
        self, parent: tk.Misc, label_text: str, var: tk.StringVar, tooltip: str
    ) -> tk.Entry:
        ttk.Label(
            parent,
            text=label_text,
            foreground=TEXT_SECONDARY,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

        entry = tk.Entry(
            parent,
            textvariable=var,
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            bd=0,
            font=(FONT_FALLBACK, FS_BASE, "normal"),
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=CYAN,
        )
        entry.pack(fill="x", padx=SP_4, pady=(0, SP_3), ipady=SP_1)
        bind_tooltip(entry, tooltip)
        return entry

    # =========================================================================
    # Logic
    # =========================================================================

    def _save_settings(self) -> None:
        """Persist settings to ConfigManager and config.json."""
        try:
            poll_ms = int(self.poll_interval_var.get().strip() or "200")
            toast_ms = int(self.toast_duration_var.get().strip() or "5000")
        except ValueError:
            self.status_msg.config(text="ERROR: INTERVAL VALUES MUST BE NUMERIC", foreground=CRITICAL)
            return

        cfg = ConfigManager.as_dict()
        cfg["default_investigator"] = self.investigator_var.get().strip()
        cfg["export_directory"] = self.export_dir_var.get().strip() or "uploads"
        cfg["live_poll_interval_ms"] = poll_ms
        cfg["toast_duration_ms"] = toast_ms
        cfg["auto_run_analysis"] = self.auto_run_var.get()
        try:
            ConfigManager._write(cfg)
        except PermissionError:
            import time
            time.sleep(0.1)
            ConfigManager._write(cfg)

        self.status_msg.config(text="CONFIG PERSISTED TO CONFIG.JSON", foreground=CYAN)
        if self.shell and hasattr(self.shell, "set_status"):
            self.shell.set_status("CONFIG: PREFERENCES PERSISTED")

    def _reset_defaults(self) -> None:
        """Reset ConfigManager to defaults and update fields."""
        ConfigManager.reset_to_defaults()
        self._load_current_settings()
        self.status_msg.config(text="CONFIG RESET TO SYSTEM DEFAULTS", foreground=HIGH)
        if self.shell and hasattr(self.shell, "set_status"):
            self.shell.set_status("CONFIG: RESTORED FACTORY DEFAULTS")

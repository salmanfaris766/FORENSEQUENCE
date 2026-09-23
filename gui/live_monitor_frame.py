# =============================================================================
# gui/live_monitor_frame.py
# FORENSEQUENCE - Real-Time File Watcher & Live Reasoning (Placeholder Frame)
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


class LiveMonitorFrame(ttk.Frame):
    """
    Flagship Live Evidence Monitor screen.
    Monitors folders and log files in real time via watchdog,
    triggering instant Forward Chaining reasoning and UI alert pulses.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell

        self._build_ui()

    def _build_ui(self) -> None:
        """Render the Live Monitor interface."""
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))

        create_section_header(header_frame, "FLAGSHIP: REAL-TIME EVIDENCE MONITOR").pack(anchor="w")

        title_row = ttk.Frame(header_frame, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, SP_2))

        ttk.Label(
            title_row,
            text="Live File Watcher & Automated Reasoning",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        badge = create_badge(title_row, "THREADED WATCHDOG", PINK)
        badge.pack(side="left", padx=(SP_4, 0))

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(0, SP_6))

        # Main Monitor Glass Card (Pink glow for alert capability)
        glass = create_glass_frame(self, width=820, height=320, border_color=PINK, fill_color=DEEP)
        glass.pack(anchor="w", padx=SP_6, pady=(0, SP_6))
        inner = glass.inner_frame

        ttk.Label(
            inner,
            text="Active Evidence Stream Watcher",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_4, pady=(SP_4, SP_2))

        ttk.Label(
            inner,
            text="The live watcher operates on non-blocking background threads utilizing watchdog and thread-safe queues.\n"
                 "As new logs, downloaded files, or network captures arrive in the watched directory, facts are extracted\n"
                 "instantly and fed into the AI rule engine to trigger real-time alerts.",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        # Status indicators
        tag_box = ttk.Frame(inner, style="Card.TFrame")
        tag_box.pack(anchor="w", padx=SP_4, pady=(0, SP_4))

        create_badge(tag_box, "WATCHER: STANDBY", CYAN).pack(side="left", padx=(0, SP_2))
        create_badge(tag_box, "EVENT QUEUE: EMPTY", PURPLE).pack(side="left", padx=(0, SP_2))
        create_badge(tag_box, "AUTO-REASONING: ENABLED", PINK).pack(side="left")

        # Action Buttons
        btn_row = ttk.Frame(inner, style="Card.TFrame")
        btn_row.pack(anchor="w", padx=SP_4, pady=(SP_3, 0))

        def _toggle_live():
            if self.shell:
                # Toggle demo live indicator
                self.shell.set_live_state(True)
                self.shell.set_status("LIVE MONITOR: ACTIVE (WATCHING)")

        btn_start = create_neon_button(btn_row, text="START LIVE MONITORING", command=_toggle_live, variant="primary")
        btn_start.pack(side="left", padx=(0, SP_3))

        def _stop_live():
            if self.shell:
                self.shell.set_live_state(False)
                self.shell.set_status("STATUS: IDLE")

        btn_stop = create_neon_button(btn_row, text="STOP WATCHER", command=_stop_live, variant="danger")
        btn_stop.pack(side="left")

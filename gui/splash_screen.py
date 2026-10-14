# =============================================================================
# gui/splash_screen.py
# FORENSEQUENCE - Restrained SOC Boot Screen
# =============================================================================

from __future__ import annotations

import tkinter as tk
import ttkbootstrap as ttk
from typing import Callable, Optional

from gui.theme import (
    APP_BG,
    PANEL_BG,
    BORDER,
    MINT,
    TEXT_PRIMARY,
    TEXT_MUTED,
    FONT_DISPLAY,
    FONT_FALLBACK,
    FONT_MONO_FALLBACK,
    SP_2,
    SP_4,
    SP_6,
)


class SplashScreen(ttk.Frame):
    """
    Startup splash screen with restrained SOC boot animation.
    Renders a centered minimalist wordmark, initializing status,
    and a slim MINT progress bar filling over approximately 1.5 seconds.
    """

    def __init__(self, parent: tk.Misc, on_complete: Optional[Callable[[], None]] = None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.on_complete = on_complete

        self._progress = 0.0
        self._is_active = True

        self._init_steps = [
            ("INITIALIZING FORENSIC KERNEL...", 0.15),
            ("CONNECTING KNOWLEDGE BASE RULES...", 0.35),
            ("INDEXING MULTI-SOURCE EVIDENCE ENGINES...", 0.55),
            ("CONFIGURING INFERENCE ENGINE...", 0.75),
            ("ENGAGING THREAT INTELLIGENCE WORKSPACE...", 0.90),
            ("SYSTEM READY.", 1.00),
        ]

        self._build_ui()
        self._start_animation()

    def _build_ui(self) -> None:
        """Construct the restrained SOC splash screen centered in the window."""
        self.configure(style="TFrame")

        # Center wrapper
        center_frame = ttk.Frame(self, style="TFrame")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Wordmark: FORENSEQUENCE in Orbitron / clean sans 24px bold (#F2F7F6)
        self.title_label = tk.Label(
            center_frame,
            text="FORENSEQUENCE",
            fg=TEXT_PRIMARY,
            bg=APP_BG,
            font=(FONT_DISPLAY, 24, "bold"),
            anchor="center",
        )
        self.title_label.pack(pady=(0, SP_2))

        # Subtitle: > INITIALIZING FORENSIC KERNEL & THREAT INTELLIGENCE WORKSPACE... (#7B918D)
        self.subtitle_label = tk.Label(
            center_frame,
            text="> INITIALIZING FORENSIC KERNEL & THREAT INTELLIGENCE WORKSPACE...",
            fg=TEXT_MUTED,
            bg=APP_BG,
            font=(FONT_MONO_FALLBACK, 10, "normal"),
            anchor="center",
        )
        self.subtitle_label.pack(pady=(0, SP_6))

        # Slim progress bar container in #2DE3C8
        self.bar_width = 380
        self.bar_height = 4
        self.bar_canvas = tk.Canvas(
            center_frame,
            width=self.bar_width,
            height=self.bar_height,
            bg=PANEL_BG,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )
        self.bar_canvas.pack(pady=(0, SP_4))

        # Fill bar in MINT (#2DE3C8)
        self.fill_bar = self.bar_canvas.create_rectangle(
            0, 0, 0, self.bar_height,
            fill=MINT, outline=""
        )

        # Status text line
        self.status_label = tk.Label(
            center_frame,
            text="[BOOT] Core system bootstrap in progress...",
            fg=TEXT_MUTED,
            bg=APP_BG,
            font=(FONT_MONO_FALLBACK, 9, "normal"),
            anchor="center",
        )
        self.status_label.pack()

    def _start_animation(self) -> None:
        """Advance progress bar across approximately 1.5 seconds (~45 ticks of 30ms)."""
        self._tick(0)

    def _tick(self, count: int) -> None:
        if not self._is_active:
            return

        total_ticks = 45  # ~1.35-1.5s total duration
        progress = min(1.0, count / total_ticks)
        fill_w = int(self.bar_width * progress)
        self.bar_canvas.coords(self.fill_bar, 0, 0, fill_w, self.bar_height)

        for step_text, thresh in self._init_steps:
            if progress <= thresh:
                self.status_label.config(text=f"[BOOT] {step_text}")
                break

        if count < total_ticks:
            self.after(30, lambda: self._tick(count + 1))
        else:
            self.after(100, self._finish)

    def _finish(self) -> None:
        """Transition into the main shell."""
        self._is_active = False
        if self.on_complete:
            self.on_complete()

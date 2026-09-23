# =============================================================================
# gui/splash_screen.py
# FORENSEQUENCE - Startup Splash Screen with Cyberpunk Loading Animation
# =============================================================================

import tkinter as tk
import ttkbootstrap as ttk
from typing import Callable, Optional

from gui.theme import (
    VOID,
    ABYSS,
    DEEP,
    CYAN,
    ICE,
    PINK,
    PURPLE,
    PLUM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_FALLBACK,
    FONT_MONO_FALLBACK,
    FONT_HEADING,
    FONT_BODY,
    FONT_SMALL,
    FONT_MONO_BODY,
    FONT_MONO_SM,
    SP_1,
    SP_2,
    SP_3,
    SP_4,
    SP_6,
    SP_8,
)


class SplashScreen(ttk.Frame):
    """
    Startup splash screen with animated kernel initialization progress.
    Renders a centered Cyberpunk Glassmorphism banner, terminal logs,
    and a glowing neon loading bar before routing into the main application shell.
    """

    def __init__(self, parent: tk.Misc, on_complete: Optional[Callable[[], None]] = None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.on_complete = on_complete

        self._progress = 0.0
        self._step_index = 0
        self._is_active = True

        self._init_steps = [
            ("Initializing forensic memory space...", 0.15),
            ("Loading Knowledge Base rules (rules.py)...", 0.35),
            ("Mounting modular evidence analyzers...", 0.55),
            ("Configuring Forward Chaining AI engine...", 0.75),
            ("Activating real-time watchdog subsystem...", 0.90),
            ("Forensic Kernel Ready. Launching workspace...", 1.00),
        ]

        self._build_ui()
        self._start_animation()

    def _build_ui(self) -> None:
        """Construct the splash screen layout centered on the screen."""
        self.configure(style="TFrame")

        # Center wrapper
        center_frame = ttk.Frame(self, style="TFrame")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Top tag
        self.top_tag = ttk.Label(
            center_frame,
            text="AI-ASSISTED DIGITAL FORENSIC SUITE",
            foreground=PURPLE,
            background=VOID,
            font=(FONT_FALLBACK, 9, "bold"),
            anchor="center",
        )
        self.top_tag.pack(pady=(0, SP_2))

        # Main Wordmark
        self.title_label = ttk.Label(
            center_frame,
            text="FORENSEQUENCE",
            foreground=CYAN,
            background=VOID,
            font=(FONT_FALLBACK, 36, "bold"),
            anchor="center",
        )
        self.title_label.pack(pady=(0, SP_1))

        # Underline neon hairline canvas
        self.line_canvas = tk.Canvas(
            center_frame,
            width=480,
            height=3,
            bg=VOID,
            highlightthickness=0,
            bd=0,
        )
        self.line_canvas.pack(pady=(0, SP_4))
        self.line_canvas.create_line(0, 1, 480, 1, fill=CYAN, width=2)

        # Subtitle
        self.subtitle_label = ttk.Label(
            center_frame,
            text="> INITIALIZING FORENSIC KERNEL...",
            foreground=TEXT_SECONDARY,
            background=VOID,
            font=(FONT_MONO_FALLBACK, 11, "normal"),
            anchor="center",
        )
        self.subtitle_label.pack(pady=(0, SP_6))

        # Progress bar canvas container
        self.bar_width = 460
        self.bar_height = 6
        self.bar_canvas = tk.Canvas(
            center_frame,
            width=self.bar_width,
            height=self.bar_height + 4,
            bg=VOID,
            highlightthickness=0,
            bd=0,
        )
        self.bar_canvas.pack(pady=(0, SP_4))

        # Trough
        self.bar_canvas.create_rectangle(
            0, 2, self.bar_width, self.bar_height + 2,
            fill=ABYSS, outline=PLUM, width=1
        )
        # Fill bar
        self.fill_bar = self.bar_canvas.create_rectangle(
            0, 2, 0, self.bar_height + 2,
            fill=CYAN, outline=""
        )

        # Terminal log label (shows current init step)
        self.log_label = ttk.Label(
            center_frame,
            text="[BOOT] Core system bootstrap in progress...",
            foreground=TEXT_MUTED,
            background=VOID,
            font=(FONT_MONO_FALLBACK, 9, "normal"),
            anchor="center",
        )
        self.log_label.pack(pady=(0, SP_2))

        # Percentage label
        self.pct_label = ttk.Label(
            center_frame,
            text="0%",
            foreground=CYAN,
            background=VOID,
            font=(FONT_MONO_FALLBACK, 10, "bold"),
            anchor="center",
        )
        self.pct_label.pack()

    def _start_animation(self) -> None:
        """Begin the timer ticks for kernel initialization."""
        self._tick_step()

    def _tick_step(self) -> None:
        """Advance progress and update log output."""
        if not self._is_active:
            return

        if self._step_index < len(self._init_steps):
            text, target_pct = self._init_steps[self._step_index]
            self.log_label.config(text=f"> {text}")
            
            # Smoothly interpolate progress toward target
            self._animate_to_target(target_pct)
        else:
            # Completed
            self._finish_splash()

    def _animate_to_target(self, target: float) -> None:
        """Step progress smoothly towards target."""
        if not self._is_active:
            return

        if self._progress < target:
            self._progress = min(target, self._progress + 0.04)
            self._update_progress_display()
            self.after(30, lambda: self._animate_to_target(target))
        else:
            self._step_index += 1
            self.after(140, self._tick_step)

    def _update_progress_display(self) -> None:
        """Redraw the glowing progress bar."""
        current_w = int(self._progress * self.bar_width)
        self.bar_canvas.coords(self.fill_bar, 0, 2, current_w, self.bar_height + 2)
        pct_int = int(self._progress * 100)
        self.pct_label.config(text=f"{pct_int}%")

    def _finish_splash(self) -> None:
        """Conclude splash and invoke callback."""
        self._is_active = False
        self.log_label.config(text="> Forensic Kernel Online.")
        self.after(200, self._trigger_callback)

    def _trigger_callback(self) -> None:
        """Destroy splash frame and notify parent."""
        self.destroy()
        if self.on_complete:
            self.on_complete()

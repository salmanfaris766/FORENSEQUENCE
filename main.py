# =============================================================================
# main.py
# FORENSEQUENCE - Main Entry Point & Standard OS Workstation Runtime
# =============================================================================

from __future__ import annotations

import sys
import tkinter as tk
import ttkbootstrap as ttk

from gui.theme import (
    APP_BG,
    apply_theme,
)
from gui.splash_screen import SplashScreen
from gui.shell import AppShell


class ForensequenceApp:
    """
    Core Application Controller.
    Manages the root desktop window, global SOC theme initialization,
    boot splash sequence, and main application shell mounting.
    """

    def __init__(self):
        self.root = ttk.Window(themename="darkly")
        self.root.title("FORENSEQUENCE — Cyber Forensics & Threat Intelligence Workstation")

        # Dimensions: 1440x900 default, 1024x640 minimum
        self.width = 1440
        self.height = 900
        self.min_width = 1024
        self.min_height = 640

        # Center on screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        start_x = max(0, (screen_w - self.width) // 2)
        start_y = max(0, (screen_h - self.height) // 2)

        self.root.geometry(f"{self.width}x{self.height}+{start_x}+{start_y}")
        self.root.minsize(self.min_width, self.min_height)

        # Apply global SOC theme tokens
        apply_theme(self.root)

        # Main Workspace Container
        self.workspace_frame = ttk.Frame(self.root, style="TFrame")
        self.workspace_frame.pack(fill="both", expand=True)

        # Mount Splash Screen first
        self.splash = SplashScreen(self.workspace_frame, on_complete=self._mount_main_shell)
        self.splash.pack(fill="both", expand=True)

        self.shell: AppShell | None = None

    def _mount_main_shell(self) -> None:
        """Called upon completion of the splash screen animation."""
        if self.splash is not None:
            self.splash.destroy()
            self.splash = None

        self.shell = AppShell(self.workspace_frame)
        self.shell.pack(fill="both", expand=True)

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()


def main() -> None:
    app = ForensequenceApp()
    app.run()


if __name__ == "__main__":
    main()

# =============================================================================
# main.py
# FORENSEQUENCE - Main Entry Point & Custom Frameless Shell Runtime
# =============================================================================

import sys
import tkinter as tk
import ttkbootstrap as ttk

from gui.theme import (
    VOID,
    ABYSS,
    DEEP,
    STEEL,
    CYAN,
    ICE,
    PINK,
    MAGENTA,
    PURPLE,
    PLUM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_FALLBACK,
    FONT_HEADING,
    FONT_SECTION,
    FONT_BODY,
    FONT_SMALL,
    SP_1,
    SP_2,
    SP_3,
    SP_4,
    apply_theme,
)
from gui.splash_screen import SplashScreen
from gui.shell import AppShell


class CustomTitleBar(ttk.Frame):
    """
    Custom title bar for the frameless application window.
    Provides window dragging, maximize/restore, minimize, and close controls
    with Cyberpunk neon hover effects.
    """

    def __init__(self, parent: tk.Tk, on_close_callback=None):
        super().__init__(parent, height=36, style="Panel.TFrame")
        self.parent = parent
        self.on_close_callback = on_close_callback

        self.pack_propagate(False)
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_maximized = False
        self._normal_geometry = "1280x800+100+100"

        self._build_ui()
        self._bind_drag_events()

    def _build_ui(self) -> None:
        """Render the custom title bar elements."""
        # Left branding
        left_box = ttk.Frame(self, style="Panel.TFrame")
        left_box.pack(side="left", padx=SP_4, fill="y")

        # Cyan Accent Block
        accent_canvas = tk.Canvas(
            left_box, width=4, height=18, bg=ABYSS, highlightthickness=0, bd=0
        )
        accent_canvas.pack(side="left", padx=(0, SP_2), pady=9)
        accent_canvas.create_rectangle(0, 0, 4, 18, fill=CYAN, outline="")

        title_lbl = ttk.Label(
            left_box,
            text="FORENSEQUENCE",
            foreground=CYAN,
            background=ABYSS,
            font=(FONT_FALLBACK, 10, "bold"),
        )
        title_lbl.pack(side="left", pady=8)

        sep_lbl = ttk.Label(
            left_box,
            text="|",
            foreground=PLUM,
            background=ABYSS,
            font=(FONT_FALLBACK, 10, "normal"),
        )
        sep_lbl.pack(side="left", padx=SP_2, pady=8)

        sub_lbl = ttk.Label(
            left_box,
            text="DIGITAL FORENSIC INVESTIGATION SUITE",
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=(FONT_FALLBACK, 8, "normal"),
        )
        sub_lbl.pack(side="left", pady=8)

        # Right Window Control Buttons
        ctrl_box = ttk.Frame(self, style="Panel.TFrame")
        ctrl_box.pack(side="right", fill="y")

        # Minimize Button
        self.btn_min = self._create_ctrl_btn(
            ctrl_box, symbol="—", command=self._minimize_window, hover_color=CYAN
        )
        self.btn_min.pack(side="left")

        # Maximize / Restore Button
        self.btn_max = self._create_ctrl_btn(
            ctrl_box, symbol="□", command=self._toggle_maximize, hover_color=CYAN
        )
        self.btn_max.pack(side="left")

        # Close Button
        self.btn_close = self._create_ctrl_btn(
            ctrl_box, symbol="✕", command=self._close_window, hover_color=PINK, is_close=True
        )
        self.btn_close.pack(side="left")

    def _create_ctrl_btn(
        self,
        parent: tk.Misc,
        symbol: str,
        command,
        hover_color: str,
        is_close: bool = False,
    ) -> tk.Canvas:
        """Create a canvas-based window control button with neon hover."""
        w, h = 46, 36
        c = tk.Canvas(
            parent,
            width=w,
            height=h,
            bg=ABYSS,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )

        def draw(bg: str, fg: str):
            c.delete("all")
            c.create_rectangle(0, 0, w, h, fill=bg, outline="")
            c.create_text(
                w // 2,
                h // 2,
                text=symbol,
                fill=fg,
                font=(FONT_FALLBACK, 10, "bold" if is_close else "normal"),
                anchor="center",
            )

        draw(ABYSS, TEXT_SECONDARY)

        def on_enter(_):
            if is_close:
                draw("#4a0f2b", PINK)
            else:
                draw(DEEP, hover_color)

        def on_leave(_):
            draw(ABYSS, TEXT_SECONDARY)

        def on_click(_):
            command()

        c.bind("<Enter>", on_enter)
        c.bind("<Leave>", on_leave)
        c.bind("<Button-1>", on_click)

        return c

    def _bind_drag_events(self) -> None:
        """Bind mouse events to allow window dragging and double-click maximize."""
        self.bind("<ButtonPress-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<Double-Button-1>", lambda e: self._toggle_maximize())

    def _on_drag_start(self, event) -> None:
        self._drag_start_x = event.x_root - self.parent.winfo_x()
        self._drag_start_y = event.y_root - self.parent.winfo_y()

    def _on_drag_motion(self, event) -> None:
        if self._is_maximized:
            # Restore before dragging if maximized
            self._toggle_maximize()
            self._drag_start_x = event.x_root - self.parent.winfo_x()
            self._drag_start_y = event.y_root - self.parent.winfo_y()

        new_x = event.x_root - self._drag_start_x
        new_y = event.y_root - self._drag_start_y
        self.parent.geometry(f"+{new_x}+{new_y}")

    def _minimize_window(self) -> None:
        """Minimize frameless window."""
        try:
            self.parent.overrideredirect(False)
            self.parent.iconify()
        except Exception:
            self.parent.iconify()

    def _toggle_maximize(self) -> None:
        """Toggle maximize/restore state."""
        if not self._is_maximized:
            self._normal_geometry = self.parent.geometry()
            screen_w = self.parent.winfo_screenwidth()
            screen_h = self.parent.winfo_screenheight()
            self.parent.geometry(f"{screen_w}x{screen_h-40}+0+0")
            self._is_maximized = True
        else:
            self.parent.geometry(self._normal_geometry)
            self._is_maximized = False

    def _close_window(self) -> None:
        if self.on_close_callback:
            self.on_close_callback()
        else:
            self.parent.destroy()


class ForensequenceApp:
    """
    Core Application Controller.
    Manages the root frameless window, custom titlebar,
    splash screen sequence, and main application shell mounting.
    """

    def __init__(self):
        self.root = ttk.Window(themename="darkly")
        self.root.title("FORENSEQUENCE - Digital Forensic Suite")
        
        # Dimensions
        self.width = 1280
        self.height = 800
        self.min_width = 1200
        self.min_height = 760

        # Center on screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        start_x = max(0, (screen_w - self.width) // 2)
        start_y = max(0, (screen_h - self.height) // 2)

        self.root.geometry(f"{self.width}x{self.height}+{start_x}+{start_y}")
        self.root.minsize(self.min_width, self.min_height)

        # Apply global theme tokens
        apply_theme(self.root)

        # Enable frameless window with custom titlebar
        self._setup_frameless()

        # Top Custom Titlebar
        self.titlebar = CustomTitleBar(self.root, on_close_callback=self._on_close)
        self.titlebar.pack(fill="x", side="top")

        # Main Workspace Container
        self.workspace_frame = ttk.Frame(self.root, style="TFrame")
        self.workspace_frame.pack(fill="both", expand=True)

        # Mount Splash Screen first
        self.splash = SplashScreen(self.workspace_frame, on_complete=self._mount_main_shell)
        self.splash.pack(fill="both", expand=True)

        self.shell: AppShell | None = None

    def _setup_frameless(self) -> None:
        """Configure frameless window behavior with taskbar restoration."""
        try:
            self.root.overrideredirect(True)

            def _on_map(event):
                if self.root.state() == "normal":
                    self.root.overrideredirect(True)

            self.root.bind("<Map>", _on_map)
        except Exception:
            # Safe fallback to standard window if overrideredirect unsupported
            pass

    def _mount_main_shell(self) -> None:
        """Called upon completion of the splash screen animation."""
        self.shell = AppShell(self.workspace_frame)
        self.shell.pack(fill="both", expand=True)

    def _on_close(self) -> None:
        """Gracefully terminate background jobs and close application."""
        self.root.destroy()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()


def main() -> None:
    app = ForensequenceApp()
    app.run()


if __name__ == "__main__":
    main()

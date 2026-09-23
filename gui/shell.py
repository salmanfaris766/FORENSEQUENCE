# =============================================================================
# gui/shell.py
# FORENSEQUENCE - Main Application Shell & Navigation Chrome
# =============================================================================

import datetime
import tkinter as tk
import ttkbootstrap as ttk
from typing import Dict, Type, Optional

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
    PEACH,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_FALLBACK,
    FONT_MONO_FALLBACK,
    FONT_HEADING,
    FONT_SECTION,
    FONT_BODY,
    FONT_SMALL,
    FONT_MONO_SM,
    SP_1,
    SP_2,
    SP_3,
    SP_4,
    SP_6,
    create_divider,
)

from gui.dashboard_frame import DashboardFrame
from gui.create_case_frame import CreateCaseFrame
from gui.case_detail_frame import CaseDetailFrame
from gui.analysis_frame import AnalysisFrame
from gui.live_monitor_frame import LiveMonitorFrame
from gui.report_frame import ReportFrame
from gui.settings_frame import SettingsFrame
from gui.about_frame import AboutFrame


class NavItem(tk.Canvas):
    """
    Sidebar navigation item with Cyberpunk interactive states:
    - Default: TEXT_SECONDARY text, dark ABYSS background
    - Hover: TEXT_PRIMARY text, glowing CYAN left indicator bar
    - Active: TEXT_PRIMARY bold, DEEP background wash, solid CYAN/PINK left bar
    """

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        route_name: str,
        on_click_callback,
        width: int = 240,
        height: int = 42,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=ABYSS,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.item_text = text
        self.route_name = route_name
        self.on_click_callback = on_click_callback
        self.w = width
        self.h = height

        self.is_active = False
        self.is_hovered = False

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        self.redraw()

    def set_active(self, active: bool) -> None:
        """Update active status and redraw."""
        self.is_active = active
        self.redraw()

    def _on_enter(self, event) -> None:
        self.is_hovered = True
        self.redraw()

    def _on_leave(self, event) -> None:
        self.is_hovered = False
        self.redraw()

    def _on_click(self, event) -> None:
        if self.on_click_callback:
            self.on_click_callback(self.route_name)

    def redraw(self) -> None:
        """Render the nav item canvas state."""
        self.delete("all")

        # Background wash
        if self.is_active:
            bg_color = DEEP
        elif self.is_hovered:
            bg_color = "#0c2b54"
        else:
            bg_color = ABYSS

        self.create_rectangle(0, 0, self.w, self.h, fill=bg_color, outline="")

        # Left accent indicator bar
        if self.is_active:
            accent_color = CYAN if self.route_name != "Live Monitor" else PINK
            self.create_rectangle(0, 0, 4, self.h, fill=accent_color, outline="")
        elif self.is_hovered:
            self.create_rectangle(0, 0, 3, self.h, fill=CYAN, outline="")

        # Text label
        if self.is_active:
            fg_color = TEXT_PRIMARY
            font_spec = (FONT_FALLBACK, 11, "bold")
        elif self.is_hovered:
            fg_color = TEXT_PRIMARY
            font_spec = (FONT_FALLBACK, 11, "normal")
        else:
            fg_color = TEXT_SECONDARY
            font_spec = (FONT_FALLBACK, 11, "normal")

        self.create_text(
            24,
            self.h // 2,
            text=self.item_text,
            anchor="w",
            fill=fg_color,
            font=font_spec,
        )


class AppShell(ttk.Frame):
    """
    Main Application Shell featuring:
    - 240px Fixed Left Sidebar with styled nav items
    - Dynamic central Content Area with instantaneous screen routing
    - 32px Bottom Status Bar with real-time clock and live monitoring state
    """

    def __init__(self, parent: tk.Misc):
        super().__init__(parent, style="TFrame")
        self.parent = parent

        # Screen Routing Registry
        self._routes: Dict[str, Type[ttk.Frame]] = {
            "Dashboard": DashboardFrame,
            "Cases": CreateCaseFrame,
            "Evidence": CaseDetailFrame,
            "Analysis": AnalysisFrame,
            "Live Monitor": LiveMonitorFrame,
            "Reports": ReportFrame,
            "Settings": SettingsFrame,
            "About": AboutFrame,
        }

        self._nav_items: Dict[str, NavItem] = {}
        self._current_screen_name: Optional[str] = None
        self._current_screen_widget: Optional[ttk.Frame] = None
        self._is_live_active = False

        self._build_layout()
        self._init_clock()

        # Route to default screen
        self.show_screen("Dashboard")

    def _build_layout(self) -> None:
        """Assemble the shell chrome: sidebar, content area, and status bar."""
        self.configure(style="TFrame")

        # Top Body Container (Sidebar + Content)
        self.body_container = ttk.Frame(self, style="TFrame")
        self.body_container.pack(fill="both", expand=True)

        # ---------------------------------------------------------------------
        # 1. Left Sidebar
        # ---------------------------------------------------------------------
        self.sidebar = ttk.Frame(self.body_container, width=240, style="Panel.TFrame")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar Header Branding
        brand_frame = ttk.Frame(self.sidebar, style="Panel.TFrame")
        brand_frame.pack(fill="x", padx=SP_4, pady=(SP_6, SP_3))

        ttk.Label(
            brand_frame,
            text="FORENSEQUENCE",
            foreground=CYAN,
            background=ABYSS,
            font=(FONT_FALLBACK, 12, "bold"),
            anchor="w",
        ).pack(fill="x")

        ttk.Label(
            brand_frame,
            text="FORENSIC ASSISTANT",
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=(FONT_FALLBACK, 8, "bold"),
            anchor="w",
        ).pack(fill="x")

        create_divider(self.sidebar, color=PLUM).pack(fill="x", padx=SP_3, pady=(SP_2, SP_4))

        # Main Navigation Group
        main_nav_spec = [
            ("Dashboard", "Dashboard"),
            ("Cases", "Cases"),
            ("Evidence Detail", "Evidence"),
            ("AI Analysis", "Analysis"),
            ("Live Monitor", "Live Monitor"),
            ("Reports", "Reports"),
        ]

        for display_label, route_key in main_nav_spec:
            nav_btn = NavItem(
                self.sidebar,
                text=display_label,
                route_name=route_key,
                on_click_callback=self.show_screen,
                width=240,
                height=40,
            )
            nav_btn.pack(fill="x", pady=1)
            self._nav_items[route_key] = nav_btn

        # Spacer pushing settings/about to bottom
        spacer = ttk.Frame(self.sidebar, style="Panel.TFrame")
        spacer.pack(fill="both", expand=True)

        create_divider(self.sidebar, color=PLUM).pack(fill="x", padx=SP_3, pady=(SP_2, SP_3))

        # Bottom Navigation Group
        bottom_nav_spec = [
            ("Settings", "Settings"),
            ("About", "About"),
        ]

        for display_label, route_key in bottom_nav_spec:
            nav_btn = NavItem(
                self.sidebar,
                text=display_label,
                route_name=route_key,
                on_click_callback=self.show_screen,
                width=240,
                height=38,
            )
            nav_btn.pack(fill="x", pady=1)
            self._nav_items[route_key] = nav_btn

        ttk.Frame(self.sidebar, height=SP_4, style="Panel.TFrame").pack()

        # Vertical Divider between Sidebar and Content Area
        v_divider = tk.Canvas(
            self.body_container, width=1, bg=PLUM, highlightthickness=0, bd=0
        )
        v_divider.pack(side="left", fill="y")

        # ---------------------------------------------------------------------
        # 2. Central Content Area
        # ---------------------------------------------------------------------
        self.content_container = ttk.Frame(self.body_container, style="TFrame")
        self.content_container.pack(side="left", fill="both", expand=True)

        # ---------------------------------------------------------------------
        # 3. Bottom Status Bar
        # ---------------------------------------------------------------------
        h_divider = tk.Canvas(
            self, height=1, bg=PLUM, highlightthickness=0, bd=0
        )
        h_divider.pack(fill="x")

        self.status_bar = ttk.Frame(self, height=32, style="Panel.TFrame")
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        # Left: Live / Idle Indicator Dot + Status Message
        status_left = ttk.Frame(self.status_bar, style="Panel.TFrame")
        status_left.pack(side="left", padx=SP_4, pady=SP_1)

        self.dot_canvas = tk.Canvas(
            status_left, width=14, height=14, bg=ABYSS, highlightthickness=0, bd=0
        )
        self.dot_canvas.pack(side="left", padx=(0, SP_2))
        self.dot_item = self.dot_canvas.create_oval(3, 3, 11, 11, fill=CYAN, outline="")

        self.status_label = ttk.Label(
            status_left,
            text="STATUS: IDLE",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_MONO_SM,
        )
        self.status_label.pack(side="left")

        # Center: Current Case Context
        self.case_context_label = ttk.Label(
            self.status_bar,
            text="No active case selected",
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=FONT_SMALL,
        )
        self.case_context_label.pack(side="left", expand=True)

        # Right: Real-Time Clock
        status_right = ttk.Frame(self.status_bar, style="Panel.TFrame")
        status_right.pack(side="right", padx=SP_4, pady=SP_1)

        self.clock_label = ttk.Label(
            status_right,
            text="--:--:-- UTC",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_MONO_SM,
        )
        self.clock_label.pack(side="right")

    # -------------------------------------------------------------------------
    # Screen Routing
    # -------------------------------------------------------------------------

    def show_screen(self, route_name: str) -> None:
        """
        Switch visible screen to the requested route.
        Updates sidebar active indicators and mounts the frame in the content area.
        """
        if route_name not in self._routes:
            return

        if self._current_screen_name == route_name and self._current_screen_widget:
            return

        # Destroy or unpack previous screen
        if self._current_screen_widget is not None:
            self._current_screen_widget.destroy()
            self._current_screen_widget = None

        # Update sidebar active states
        for key, nav_item in self._nav_items.items():
            nav_item.set_active(key == route_name)

        # Instantiate and display the new frame
        frame_class = self._routes[route_name]
        self._current_screen_widget = frame_class(self.content_container, shell=self)
        self._current_screen_widget.pack(fill="both", expand=True)
        self._current_screen_name = route_name

    # -------------------------------------------------------------------------
    # Status Bar API
    # -------------------------------------------------------------------------

    def set_status(self, text: str) -> None:
        """Update the left status text."""
        self.status_label.config(text=text.upper())

    def set_case_context(self, text: str) -> None:
        """Update the central case context label."""
        self.case_context_label.config(text=text)

    def set_live_state(self, is_live: bool) -> None:
        """
        Switch status bar live monitoring dot between IDLE (CYAN) and LIVE (PINK).
        """
        self._is_live_active = is_live
        if is_live:
            self.dot_canvas.itemconfig(self.dot_item, fill=PINK)
            self.set_status("LIVE MONITOR: WATCHING")
        else:
            self.dot_canvas.itemconfig(self.dot_item, fill=CYAN)
            self.set_status("STATUS: IDLE")

    # -------------------------------------------------------------------------
    # Clock Helper
    # -------------------------------------------------------------------------

    def _init_clock(self) -> None:
        """Start the real-time UTC clock updater."""
        self._update_clock()

    def _update_clock(self) -> None:
        """Tick UTC clock display every second."""
        now = datetime.datetime.now(datetime.timezone.utc)
        time_str = now.strftime("%Y-%m-%d  %H:%M:%S UTC")
        self.clock_label.config(text=time_str)
        self.after(1000, self._update_clock)

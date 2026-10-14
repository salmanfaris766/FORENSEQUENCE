# =============================================================================
# gui/shell.py
# FORENSEQUENCE - Premium SOC Workstation Desktop Chrome & Navigation
# =============================================================================

from __future__ import annotations

import datetime
import tkinter as tk
from typing import Dict, Optional, Callable
import ttkbootstrap as ttk

from gui.theme import (
    APP_BG,
    BG_SECONDARY,
    SIDEBAR_BG,
    PANEL_BG,
    PANEL_ELEVATED,
    PANEL_HOVER,
    CYAN,
    CYAN_NEON,
    MINT,
    TEAL,
    TEAL_MID,
    TEAL_DARK,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    BORDER,
    BORDER_SECONDARY,
    BORDER_HOVER,
    CRITICAL,
    HIGH,
    MEDIUM,
    LOW,
    FONT_DISPLAY,
    FONT_FALLBACK,
    FONT_MONO_FALLBACK,
    FS_XS,
    FS_SM,
    FS_BASE,
    SP_1,
    SP_2,
    SP_3,
    SP_4,
    SP_6,
    create_soc_badge,
    create_soc_entry,
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

from database import get_case_by_id


# =============================================================================
# ROUTE SPECIFICATION & ALIASES
# =============================================================================

ROUTE_ALIASES: Dict[str, str] = {
    "Cases": "Case Investigation",
    "create_case": "Case Investigation",
    "create": "Case Investigation",
    "Evidence": "Evidence Explorer",
    "Analysis": "AI Analysis",
    "Live Monitor": "Real-time Monitor",
}

ROUTE_CATEGORIES: Dict[str, str] = {
    "Dashboard": "WORKSPACE",
    "Case Investigation": "WORKSPACE",
    "Evidence Explorer": "WORKSPACE",
    "AI Analysis": "OPERATIONS",
    "Real-time Monitor": "OPERATIONS",
    "Reports": "OPERATIONS",
    "Settings": "SYSTEM",
    "About": "SYSTEM",
}


# =============================================================================
# SIDEBAR NAVIGATION ITEM
# =============================================================================

class SOCNavItem(tk.Canvas):
    """
    SOC Workstation sidebar navigation button with stateful indicator:
    - Default: TEXT_SECONDARY text, SIDEBAR_BG
    - Hover: TEXT_PRIMARY text, PANEL_ELEVATED background
    - Selected: MINT text, PANEL_HOVER background, MINT active pill indicator
    """

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        route_name: str,
        on_click_callback: Callable[[str], None],
        width: int = 225,
        height: int = 36,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=SIDEBAR_BG,
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
        """Update active status and redraw item."""
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
        """Render SOC nav item state."""
        self.delete("all")

        # Background wash
        if self.is_active:
            bg_color = PANEL_HOVER
        elif self.is_hovered:
            bg_color = PANEL_ELEVATED
        else:
            bg_color = SIDEBAR_BG

        self.create_rectangle(0, 0, self.w, self.h, fill=bg_color, outline="")

        # Left indicator dot/pill for active item
        if self.is_active:
            self.create_rectangle(0, 4, 3, self.h - 4, fill=MINT, outline="")
        elif self.is_hovered:
            self.create_rectangle(0, 8, 2, self.h - 8, fill=BORDER_HOVER, outline="")

        # Text label
        if self.is_active:
            fg_color = MINT
            font_spec = (FONT_FALLBACK, FS_BASE, "bold")
        elif self.is_hovered:
            fg_color = TEXT_PRIMARY
            font_spec = (FONT_FALLBACK, FS_BASE, "normal")
        else:
            fg_color = TEXT_SECONDARY
            font_spec = (FONT_FALLBACK, FS_BASE, "normal")

        # 12px horizontal padding
        self.create_text(
            16,
            self.h // 2,
            text=self.item_text,
            anchor="w",
            fill=fg_color,
            font=font_spec,
        )


# Legacy alias
NavItem = SOCNavItem


# =============================================================================
# MAIN APPLICATION SHELL
# =============================================================================

class AppShell(ttk.Frame):
    """
    SOC Workstation Application Shell featuring:
    - 225px Fixed Left Sidebar with grouped category navigation
    - 42px Top Toolbar with Breadcrumb, Search Input, Case Badge, and Live Status Dot
    - Dynamic Central Content Area supporting instantaneous screen routing
    - 26px Bottom Status Bar with system telemetry and real-time UTC clock
    """

    def __init__(self, parent: tk.Misc):
        super().__init__(parent, style="TFrame")
        self.parent = parent

        # Screen Routing Registry
        self._routes: Dict[str, type] = {
            "Dashboard": DashboardFrame,
            "Case Investigation": CreateCaseFrame,
            "Evidence Explorer": CaseDetailFrame,
            "AI Analysis": AnalysisFrame,
            "Real-time Monitor": LiveMonitorFrame,
            "Reports": ReportFrame,
            "Settings": SettingsFrame,
            "About": AboutFrame,
        }

        self._nav_items: Dict[str, SOCNavItem] = {}
        self._current_screen_name: Optional[str] = None
        self._current_screen_widget: Optional[ttk.Frame] = None
        self._is_live_active = False
        self.selected_case_id: Optional[int] = None

        self._build_layout()
        self._init_clock()
        self._bind_shortcuts()

        # Route to default screen
        self.show_screen("Dashboard")

    # -------------------------------------------------------------------------
    # Layout Builder
    # -------------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Assemble SOC workstation desktop chrome: sidebar, top toolbar, content, status bar."""
        self.configure(style="TFrame")

        # Outer horizontal split container: Sidebar (Left) + Workstation Main (Right)
        self.outer_split = ttk.Frame(self, style="TFrame")
        self.outer_split.pack(fill="both", expand=True)

        # ---------------------------------------------------------------------
        # 1. Left Sidebar (225px Fixed Width, #050C0B, Right Border 1px #1B302D)
        # ---------------------------------------------------------------------
        self.sidebar_container = ttk.Frame(self.outer_split, width=225, style="Panel.TFrame")
        self.sidebar_container._custom_bg = SIDEBAR_BG
        self.sidebar_container.pack(side="left", fill="y")
        self.sidebar_container.pack_propagate(False)

        # Right border line on sidebar
        v_divider = tk.Canvas(
            self.outer_split, width=1, bg=BORDER, highlightthickness=0, bd=0
        )
        v_divider.pack(side="left", fill="y")

        # Top Branding Header in Sidebar
        brand_frame = tk.Frame(self.sidebar_container, bg=SIDEBAR_BG, padx=SP_4, pady=SP_4)
        brand_frame.pack(fill="x")

        tk.Label(
            brand_frame,
            text="FORENSEQUENCE",
            fg=TEXT_PRIMARY,
            bg=SIDEBAR_BG,
            font=(FONT_DISPLAY, 14, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            brand_frame,
            text="v1.0 SOC WORKSTATION",
            fg=TEXT_MUTED,
            bg=SIDEBAR_BG,
            font=(FONT_FALLBACK, 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        create_divider(self.sidebar_container, color=BORDER).pack(fill="x", padx=SP_3, pady=(SP_2, SP_3))

        # Grouped Navigation Sections
        nav_groups = [
            ("WORKSPACE", [
                ("Dashboard", "Dashboard"),
                ("Case Investigation", "Case Investigation"),
                ("Evidence Explorer", "Evidence Explorer"),
            ]),
            ("OPERATIONS", [
                ("AI Analysis", "AI Analysis"),
                ("Real-time Monitor", "Real-time Monitor"),
                ("Reports", "Reports"),
            ]),
            ("SYSTEM", [
                ("Settings", "Settings"),
                ("About", "About"),
            ]),
        ]

        for group_label, items in nav_groups:
            # Category Header Label
            cat_label = tk.Label(
                self.sidebar_container,
                text=group_label,
                fg=TEXT_MUTED,
                bg=SIDEBAR_BG,
                font=(FONT_FALLBACK, 10, "bold"),
                anchor="w",
                padx=16,
            )
            cat_label.pack(fill="x", pady=(SP_2, 2))

            for display_name, route_key in items:
                nav_btn = SOCNavItem(
                    self.sidebar_container,
                    text=display_name,
                    route_name=route_key,
                    on_click_callback=self.show_screen,
                    width=225,
                    height=36,
                )
                nav_btn.pack(fill="x", pady=1)
                self._nav_items[route_key] = nav_btn

        # Bottom spacer pushing sidebar elements up
        spacer = ttk.Frame(self.sidebar_container, style="Panel.TFrame")
        spacer._custom_bg = SIDEBAR_BG
        spacer.pack(fill="both", expand=True)

        # ---------------------------------------------------------------------
        # 2. Main Right Workstation Area (Top Toolbar + Content + Status Bar)
        # ---------------------------------------------------------------------
        self.workstation_area = ttk.Frame(self.outer_split, style="TFrame")
        self.workstation_area.pack(side="left", fill="both", expand=True)

        # --- Top Toolbar (Height ~42px, #061211, Bottom Border 1px #1B302D) ---
        self.top_toolbar = tk.Frame(self.workstation_area, height=42, bg=BG_SECONDARY)
        self.top_toolbar.pack(fill="x", side="top")
        self.top_toolbar.pack_propagate(False)

        # Left Toolbar: Breadcrumb Trail
        self.breadcrumb_frame = tk.Frame(self.top_toolbar, bg=BG_SECONDARY)
        self.breadcrumb_frame.pack(side="left", padx=SP_4, fill="y")

        self.lbl_breadcrumb_prefix = tk.Label(
            self.breadcrumb_frame,
            text="WORKSTATION /",
            fg=TEXT_MUTED,
            bg=BG_SECONDARY,
            font=(FONT_FALLBACK, FS_SM, "bold"),
        )
        self.lbl_breadcrumb_prefix.pack(side="left", pady=10)

        self.lbl_breadcrumb_active = tk.Label(
            self.breadcrumb_frame,
            text="DASHBOARD",
            fg=TEXT_PRIMARY,
            bg=BG_SECONDARY,
            font=(FONT_FALLBACK, FS_SM, "bold"),
        )
        self.lbl_breadcrumb_active.pack(side="left", padx=(4, 0), pady=10)

        # Center Toolbar: Compact Search Input Box
        self.search_container = tk.Frame(self.top_toolbar, bg=BG_SECONDARY)
        self.search_container.pack(side="left", expand=True, padx=SP_4)

        self.entry_search = create_soc_entry(
            self.search_container,
            placeholder="Search cases, hashes, indicators...",
            width=36,
        )
        self.entry_search.pack(pady=7, ipady=2)
        self.entry_search.bind("<Return>", self._on_global_search)

        # Right Toolbar: Case Context Badge + Live Status Indicator Dot
        self.toolbar_right = tk.Frame(self.top_toolbar, bg=BG_SECONDARY)
        self.toolbar_right.pack(side="right", padx=SP_4, fill="y")

        self.case_badge_container = tk.Frame(self.toolbar_right, bg=BG_SECONDARY)
        self.case_badge_container.pack(side="left", padx=(0, SP_3), pady=8)
        self.case_badge = create_soc_badge(self.case_badge_container, "NO ACTIVE CASE", color=TEAL_MID, bg=BG_SECONDARY)
        self.case_badge.pack(side="left")

        # Live Status Indicator Dot & Label
        self.status_box = tk.Frame(self.toolbar_right, bg=BG_SECONDARY)
        self.status_box.pack(side="left", pady=10)

        self.dot_canvas = tk.Canvas(
            self.status_box, width=12, height=12, bg=BG_SECONDARY, highlightthickness=0, bd=0
        )
        self.dot_canvas.pack(side="left", padx=(0, 6))
        self.dot_item = self.dot_canvas.create_oval(2, 2, 10, 10, fill=CYAN, outline="")

        self.status_label = tk.Label(
            self.status_box,
            text="STATUS: IDLE",
            fg=TEXT_SECONDARY,
            bg=BG_SECONDARY,
            font=(FONT_MONO_FALLBACK, FS_XS, "bold"),
        )
        self.status_label.pack(side="left")

        # Toolbar Bottom Divider
        create_divider(self.workstation_area, color=BORDER).pack(fill="x", side="top")

        # --- Bottom Status Bar (Height 26px, #050C0B, Top Border 1px #1B302D) ---
        create_divider(self.workstation_area, color=BORDER).pack(fill="x", side="bottom")

        self.status_bar = tk.Frame(self.workstation_area, height=26, bg=SIDEBAR_BG)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        # Left Status Bar Info
        self.lbl_system_status = tk.Label(
            self.status_bar,
            text="SYSTEM STATUS: ONLINE | KNOWLEDGE BASE: 9 RULES ACTIVE",
            fg=TEXT_MUTED,
            bg=SIDEBAR_BG,
            font=(FONT_MONO_FALLBACK, 8, "normal"),
        )
        self.lbl_system_status.pack(side="left", padx=SP_4)

        # Center Status Bar Summary
        self.case_context_label = tk.Label(
            self.status_bar,
            text="FORENSIC WORKSTATION | THREAT INTELLIGENCE ENGINE",
            fg=TEXT_MUTED,
            bg=SIDEBAR_BG,
            font=(FONT_FALLBACK, 8, "normal"),
        )
        self.case_context_label.pack(side="left", expand=True)

        # Right Real-time UTC Clock
        self.clock_label = tk.Label(
            self.status_bar,
            text="--:--:-- UTC",
            fg=TEXT_SECONDARY,
            bg=SIDEBAR_BG,
            font=(FONT_MONO_FALLBACK, 9, "bold"),
        )
        self.clock_label.pack(side="right", padx=SP_4)

        # --- Central Screen Container Area ---
        self.content_container = ttk.Frame(self.workstation_area, style="TFrame")
        self.content_container.pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # Screen Routing & Lifecycle
    # -------------------------------------------------------------------------

    def show_screen(self, route_name: str) -> None:
        """
        Transition the workstation view to the requested route.
        Resolves aliases for full backward compatibility, updates sidebar indicators,
        and synchronizes breadcrumb labels.
        """
        resolved_route = ROUTE_ALIASES.get(route_name, route_name)
        if resolved_route not in self._routes:
            return

        # Avoid redundant re-instantiation
        if self._current_screen_name == resolved_route and self._current_screen_widget:
            if resolved_route in ("Evidence Explorer", "AI Analysis", "Reports") and hasattr(self._current_screen_widget, "set_case"):
                self._current_screen_widget.set_case(self.selected_case_id)
            elif hasattr(self._current_screen_widget, "refresh_data"):
                self._current_screen_widget.refresh_data()
            return

        # Destroy previous screen cleanly
        if self._current_screen_widget is not None:
            self._current_screen_widget.destroy()
            self._current_screen_widget = None

        # Update sidebar active states
        for key, nav_item in self._nav_items.items():
            nav_item.set_active(key == resolved_route)

        # Update Toolbar Breadcrumbs
        category = ROUTE_CATEGORIES.get(resolved_route, "WORKSTATION")
        self.lbl_breadcrumb_prefix.config(text=f"{category} /")
        self.lbl_breadcrumb_active.config(text=resolved_route.upper())

        # Instantiate requested screen widget
        frame_class = self._routes[resolved_route]
        if resolved_route == "Dashboard":
            self._current_screen_widget = frame_class(
                self.content_container,
                on_navigate_callback=self._handle_dashboard_navigate,
                on_select_case_callback=self._handle_dashboard_select_case,
                shell=self,
            )
        elif resolved_route == "Case Investigation":
            self._current_screen_widget = frame_class(
                self.content_container,
                on_navigate=self.show_screen,
                on_case_created=self._handle_case_created,
                on_open_case=self._handle_dashboard_select_case,
                shell=self,
            )
        elif resolved_route in ("Evidence Explorer", "AI Analysis", "Reports"):
            self._current_screen_widget = frame_class(
                self.content_container,
                case_id=self.selected_case_id,
                on_navigate=self.show_screen,
                shell=self,
            )
        else:
            self._current_screen_widget = frame_class(self.content_container, shell=self)

        self._current_screen_widget.pack(fill="both", expand=True)
        self._current_screen_name = resolved_route

    # -------------------------------------------------------------------------
    # Case Context & Navigation Callbacks
    # -------------------------------------------------------------------------

    def _handle_case_created(self, case_id: int) -> None:
        """Update case context badge when a new case is registered."""
        self.selected_case_id = case_id
        case = get_case_by_id(case_id)
        if case:
            self.set_case_context(f"CASE: {case['case_number']} | {case['case_name']}")
            self._update_toolbar_case_badge(case['case_number'])

    def _handle_dashboard_navigate(self, target: str) -> None:
        """Handle screen navigation requests initiated by the Dashboard."""
        self.show_screen(target)

    def _handle_dashboard_select_case(self, case_id: int) -> None:
        """Handle case selection from Dashboard, setting context and opening Evidence Explorer."""
        self.selected_case_id = case_id
        case = get_case_by_id(case_id)
        if case:
            self.set_case_context(f"CASE: {case['case_number']} | {case['case_name']}")
            self._update_toolbar_case_badge(case['case_number'])
        else:
            self.set_case_context(f"CASE #{case_id}")
            self._update_toolbar_case_badge(f"CASE #{case_id}")

        if (
            self._current_screen_name == "Evidence Explorer"
            and self._current_screen_widget
            and hasattr(self._current_screen_widget, "set_case")
        ):
            self._current_screen_widget.set_case(case_id)
        else:
            self.show_screen("Evidence Explorer")

    def _update_toolbar_case_badge(self, case_text: str) -> None:
        """Refresh case pill in top toolbar."""
        for child in self.case_badge_container.winfo_children():
            child.destroy()
        self.case_badge = create_soc_badge(
            self.case_badge_container,
            f"CASE: {case_text}" if not case_text.startswith("CASE") else case_text,
            color=TEAL_MID,
            bg=BG_SECONDARY,
        )
        self.case_badge.pack(side="left")

    def _on_global_search(self, event=None) -> None:
        """Handle global search input submission."""
        query = self.entry_search.get().strip()
        if query:
            self.flash_alert(f"SEARCHING: '{query}'")

    # -------------------------------------------------------------------------
    # Status Bar & Live Monitoring API
    # -------------------------------------------------------------------------

    def set_status(self, text: str) -> None:
        """Update status bar or toolbar status text."""
        self.status_label.config(text=text.upper())

    def set_case_context(self, text: str) -> None:
        """Update the central case context label."""
        self.case_context_label.config(text=text)

    def set_live_state(self, is_live: bool, file_path: str = "") -> None:
        """Switch status bar live monitoring dot between IDLE (CYAN) and LIVE (CRITICAL)."""
        self._is_live_active = is_live
        if is_live:
            self.dot_canvas.itemconfig(self.dot_item, fill=CRITICAL)
            self.status_label.config(text="LIVE MONITORING", fg=CRITICAL)
        else:
            self.dot_canvas.itemconfig(self.dot_item, fill=CYAN)
            self.status_label.config(text="STATUS: IDLE", fg=TEXT_SECONDARY)

    def flash_alert(self, message: str, duration_ms: int = 4000) -> None:
        """Briefly display an alert message in the toolbar using CRITICAL text."""
        try:
            prev_text = self.status_label.cget("text")
            prev_fg = self.status_label.cget("foreground")
        except Exception:
            prev_text = "STATUS: IDLE"
            prev_fg = TEXT_SECONDARY

        self.status_label.config(text=message[:60].upper(), fg=CRITICAL)
        self.dot_canvas.itemconfig(self.dot_item, fill=CRITICAL)

        def _restore():
            try:
                if self.status_label.winfo_exists():
                    self.status_label.config(text=prev_text, foreground=prev_fg)
                    if not self._is_live_active:
                        self.dot_canvas.itemconfig(self.dot_item, fill=CYAN)
            except Exception:
                pass

        self.after(duration_ms, _restore)

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

    # -------------------------------------------------------------------------
    # Global Keyboard Shortcuts
    # -------------------------------------------------------------------------

    def _bind_shortcuts(self) -> None:
        """Bind global application keyboard shortcuts to root window."""
        top = self.winfo_toplevel()
        top.bind("<Control-d>", lambda e: self.show_screen("Dashboard"))
        top.bind("<Control-D>", lambda e: self.show_screen("Dashboard"))
        top.bind("<Control-n>", lambda e: self.show_screen("Case Investigation"))
        top.bind("<Control-N>", lambda e: self.show_screen("Case Investigation"))
        top.bind("<Control-r>", lambda e: self.show_screen("Reports"))
        top.bind("<Control-R>", lambda e: self.show_screen("Reports"))
        top.bind("<Control-m>", lambda e: self.show_screen("Real-time Monitor"))
        top.bind("<Control-M>", lambda e: self.show_screen("Real-time Monitor"))
        top.bind("<F11>", self._toggle_fullscreen)
        top.bind("<Escape>", self._exit_fullscreen)

    def _toggle_fullscreen(self, event=None) -> None:
        """Toggle fullscreen display mode."""
        top = self.winfo_toplevel()
        is_fs = bool(top.attributes("-fullscreen"))
        top.attributes("-fullscreen", not is_fs)

    def _exit_fullscreen(self, event=None) -> None:
        """Exit fullscreen display mode."""
        top = self.winfo_toplevel()
        top.attributes("-fullscreen", False)

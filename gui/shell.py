# =============================================================================
# gui/shell.py
# FORENSEQUENCE - Premium SOC Workstation Desktop Chrome & Navigation
# =============================================================================

from __future__ import annotations

import datetime
import math
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
    create_liquid_squircle,
    create_soc_button,
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
# ANIMATED WAVE BACKGROUND
# =============================================================================

class AnimatedWaveBackground(tk.Canvas):
    """
    Animated flowing background rendering overlapping sine wave polygons in dark teal
    (#04100F, #061514, #0A2422) over a pure black (#000000) canvas.
    Animates smoothly via after(30, self._animate) without CPU overhead.
    """

    def __init__(self, parent: tk.Misc, **kwargs):
        super().__init__(
            parent,
            bg="#000000",
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.time_offset = 0.0
        self._anim_id: Optional[str] = None
        self._poly_ids = []

        # Wave layer specs: (fill_color, line_color, base_y_ratio, amp_ratio, freq, speed, phase)
        self._wave_specs = [
            ("#062523", "#0E8A80", 0.52, 0.12, 0.004, 0.015, 0.0),
            ("#0A3936", "#14B8A6", 0.68, 0.10, 0.005, 0.022, 1.8),
            ("#0F4E4A", "#22D3C5", 0.84, 0.08, 0.006, 0.028, 3.5),
        ]

        self.bind("<Destroy>", self._on_destroy)
        self._animate()

    def _animate(self) -> None:
        if not self.winfo_exists():
            return

        w = self.winfo_width()
        h = self.winfo_height()

        if w > 10 and h > 10:
            self.time_offset += 1.0

            step_px = max(15, w // 45)
            x_pts = list(range(0, w + step_px, step_px))
            if x_pts[-1] < w:
                x_pts.append(w)

            for i, (fill_c, line_c, base_r, amp_r, freq, speed, phase) in enumerate(self._wave_specs):
                base_y = h * base_r
                amp = max(18.0, h * amp_r)
                t = self.time_offset * speed + phase

                coords = [0, h]
                for x in x_pts:
                    y = base_y + amp * math.sin(x * freq + t)
                    coords.extend([x, y])
                coords.extend([w, h])

                if i >= len(self._poly_ids):
                    pid = self.create_polygon(coords, fill=fill_c, outline=line_c, width=1.5, smooth=True)
                    self._poly_ids.append(pid)
                else:
                    self.coords(self._poly_ids[i], *coords)

        self._anim_id = self.after(30, self._animate)

    def _on_destroy(self, event=None) -> None:
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None


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
        width: int = 280,
        height: int = 38,
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

        # 20px horizontal padding for 280px sidebar
        self.create_text(
            20,
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
    - Flowing animated wave background placed across the entire root window
    - 280px Fixed Left Sidebar with grouped category navigation
    - Transparent Top Toolbar with Breadcrumb, Floating Squircle Pill Search, and Live Status
    - Dynamic Central Content Area with border removal letting background waves show through
    - Modal Slide-In Navigation for drill-down case investigation
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
        self._active_slide_panel: Optional[tk.Widget] = None

        self._build_layout()
        self._init_clock()
        self._bind_shortcuts()

        # Route to default screen
        self.show_screen("Dashboard")

    # -------------------------------------------------------------------------
    # Layout Builder
    # -------------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Assemble liquid cool workstation desktop chrome: animated background, 280px sidebar, glass search, content."""
        self.configure(style="TFrame")

        # ---------------------------------------------------------------------
        # 1. Left Sidebar (280px Fixed Width, Liquid Glass styling)
        # ---------------------------------------------------------------------
        self.sidebar_container = ttk.Frame(self, width=280, style="Panel.TFrame")
        self.sidebar_container._custom_bg = SIDEBAR_BG
        self.sidebar_container.pack(side="left", fill="y")
        self.sidebar_container.pack_propagate(False)

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

        # Grouped Navigation Sections (About screen removed)
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
            ]),
        ]

        for group_label, items in nav_groups:
            cat_label = tk.Label(
                self.sidebar_container,
                text=group_label,
                fg=TEXT_MUTED,
                bg=SIDEBAR_BG,
                font=(FONT_FALLBACK, 10, "bold"),
                anchor="w",
                padx=20,
            )
            cat_label.pack(fill="x", pady=(SP_2, 2))

            for display_name, route_key in items:
                nav_btn = SOCNavItem(
                    self.sidebar_container,
                    text=display_name,
                    route_name=route_key,
                    on_click_callback=self.show_screen,
                    width=280,
                    height=38,
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
        self.workstation_area = tk.Frame(self, bg="#000000")
        self.workstation_area.pack(side="left", fill="both", expand=True)

        # --- Top Toolbar (Transparent feel, floating glass squircle search bar) ---
        self.top_toolbar = tk.Frame(self.workstation_area, height=48, bg="#000000")
        self.top_toolbar.pack(fill="x", side="top")
        self.top_toolbar.pack_propagate(False)

        # Left Toolbar: Breadcrumb Trail
        self.breadcrumb_frame = tk.Frame(self.top_toolbar, bg="#000000")
        self.breadcrumb_frame.pack(side="left", padx=SP_4, fill="y")

        self.lbl_breadcrumb_prefix = tk.Label(
            self.breadcrumb_frame,
            text="WORKSTATION /",
            fg=TEXT_MUTED,
            bg="#000000",
            font=(FONT_FALLBACK, FS_SM, "bold"),
        )
        self.lbl_breadcrumb_prefix.pack(side="left", pady=13)

        self.lbl_breadcrumb_active = tk.Label(
            self.breadcrumb_frame,
            text="DASHBOARD",
            fg=TEXT_PRIMARY,
            bg="#000000",
            font=(FONT_FALLBACK, FS_SM, "bold"),
        )
        self.lbl_breadcrumb_active.pack(side="left", padx=(4, 0), pady=13)

        # Center Toolbar: Floating liquid squircle pill search bar (radius=18)
        self.search_pill = create_liquid_squircle(
            self.top_toolbar,
            width=360,
            height=36,
            radius=18,
            alpha=35,
            tint=TEAL,
            border_color=BORDER_SECONDARY,
        )
        self.search_pill.pack(side="left", expand=True, pady=6)

        search_placeholder = "Search cases, hashes, indicators..."
        self.entry_search = tk.Entry(
            self.search_pill.inner_frame,
            bg=PANEL_BG,
            fg=TEXT_MUTED,
            insertbackground=CYAN,
            bd=0,
            highlightthickness=0,
            font=(FONT_FALLBACK, FS_BASE),
        )
        self.entry_search.pack(fill="both", expand=True, padx=12, pady=4)
        self.entry_search.insert(0, search_placeholder)

        def _on_search_focus_in(event):
            if self.entry_search.get() == search_placeholder:
                self.entry_search.delete(0, tk.END)
                self.entry_search.config(fg=TEXT_PRIMARY)

        def _on_search_focus_out(event):
            if not self.entry_search.get().strip():
                self.entry_search.delete(0, tk.END)
                self.entry_search.insert(0, search_placeholder)
                self.entry_search.config(fg=TEXT_MUTED)

        self.entry_search.bind("<FocusIn>", _on_search_focus_in)
        self.entry_search.bind("<FocusOut>", _on_search_focus_out)
        self.entry_search.bind("<Return>", self._on_global_search)

        # Right Toolbar: Case Context Badge + Live Status Indicator Dot
        self.toolbar_right = tk.Frame(self.top_toolbar, bg="#000000")
        self.toolbar_right.pack(side="right", padx=SP_4, fill="y")

        self.case_badge_container = tk.Frame(self.toolbar_right, bg="#000000")
        self.case_badge_container.pack(side="left", padx=(0, SP_3), pady=8)
        self.case_badge = create_soc_badge(self.case_badge_container, "NO ACTIVE CASE", color=TEAL_MID, bg="#000000")
        self.case_badge.pack(side="left")

        # Live Status Indicator Dot & Label
        self.status_box = tk.Frame(self.toolbar_right, bg="#000000")
        self.status_box.pack(side="left", pady=13)

        self.dot_canvas = tk.Canvas(
            self.status_box, width=12, height=12, bg="#000000", highlightthickness=0, bd=0
        )
        self.dot_canvas.pack(side="left", padx=(0, 6))
        self.dot_item = self.dot_canvas.create_oval(2, 2, 10, 10, fill=CYAN, outline="")

        self.status_label = tk.Label(
            self.status_box,
            text="STATUS: IDLE",
            fg=TEXT_SECONDARY,
            bg="#000000",
            font=(FONT_MONO_FALLBACK, FS_XS, "bold"),
        )
        self.status_label.pack(side="left")

        # --- Bottom Status Bar (Height 26px, #050C0B, no harsh border) ---
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

        # --- Central Screen Container Area with animated wave background ---
        # The wave canvas is embedded INSIDE the content container so it's
        # actually visible (Tkinter frames are always opaque, so placing a
        # canvas behind a Frame makes it invisible).
        self.content_container = tk.Frame(self.workstation_area, bg="#000000")
        self.content_container.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        # Animated wave background fills the content area
        self.wave_bg = AnimatedWaveBackground(self.content_container)
        self.wave_bg.place(x=0, y=0, relwidth=1.0, relheight=1.0)

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

        # Dismiss any active slide-in panel when navigating routes
        if getattr(self, "_active_slide_panel", None):
            self.close_slide_in_panel()

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
    # Slide-In Navigation (Modal Drill-Down Mechanism)
    # -------------------------------------------------------------------------

    def show_slide_in_panel(self, frame_class: type, **kwargs) -> tk.Widget:
        """
        Instantiate a modal slide-in panel and animate it in from the right edge.
        relx animates from 1.0 down to 0.05 over 250ms with easing, leaving
        the left sidebar visible for layered drill-down navigation.
        Features a top chrome bar with [< BACK] dismiss button.
        """
        if getattr(self, "_active_slide_panel", None):
            try:
                self._active_slide_panel.destroy()
            except Exception:
                pass
            self._active_slide_panel = None

        panel_container = tk.Frame(
            self,
            bg=PANEL_BG,
            highlightthickness=1,
            highlightbackground=TEAL_DARK,
            bd=0,
        )
        self._active_slide_panel = panel_container
        panel_container.place(relx=1.0, rely=0.0, relwidth=0.95, relheight=1.0)
        panel_container.lift()

        # Header bar with [< BACK] button
        header_bar = tk.Frame(panel_container, bg=BG_SECONDARY, height=44)
        header_bar.pack(fill="x", side="top")
        header_bar.pack_propagate(False)

        back_btn = create_soc_button(
            header_bar,
            text="[< BACK]",
            variant="secondary",
            command=self.close_slide_in_panel,
        )
        back_btn.pack(side="left", padx=SP_3, pady=6)

        title_lbl = tk.Label(
            header_bar,
            text="DRILL-DOWN DETAIL VIEW",
            fg=CYAN,
            bg=BG_SECONDARY,
            font=(FONT_FALLBACK, FS_BASE, "bold"),
        )
        title_lbl.pack(side="left", padx=SP_2)

        create_divider(panel_container, color=BORDER).pack(fill="x", side="top")

        # Inner body for the frame class
        body = ttk.Frame(panel_container, style="TFrame")
        body.pack(fill="both", expand=True)

        try:
            instance = frame_class(body, shell=self, on_navigate=self.show_screen, **kwargs)
        except TypeError:
            instance = frame_class(body, **kwargs)
        instance.pack(fill="both", expand=True)
        panel_container._child_instance = instance

        # Animate relx from 1.0 to 0.05 over 250ms
        start_time = [None]
        duration_ms = 250.0

        def _step_in():
            if not panel_container.winfo_exists():
                return
            now = datetime.datetime.now().timestamp() * 1000.0
            if start_time[0] is None:
                start_time[0] = now
            elapsed = now - start_time[0]
            progress = min(1.0, elapsed / duration_ms)
            eased = 1.0 - (1.0 - progress) ** 3
            cur_relx = 1.0 - (0.95 * eased)
            panel_container.place_configure(relx=cur_relx)
            if progress < 1.0:
                self.after(20, _step_in)
            else:
                panel_container.place_configure(relx=0.05)

        _step_in()
        return panel_container

    def close_slide_in_panel(self) -> None:
        """Animate the active slide-in panel off-screen to the right and destroy it."""
        panel = getattr(self, "_active_slide_panel", None)
        if not panel or not panel.winfo_exists():
            self._active_slide_panel = None
            return

        start_time = [None]
        duration_ms = 200.0
        start_relx = 0.05

        def _step_out():
            if not panel.winfo_exists():
                self._active_slide_panel = None
                return
            now = datetime.datetime.now().timestamp() * 1000.0
            if start_time[0] is None:
                start_time[0] = now
            elapsed = now - start_time[0]
            progress = min(1.0, elapsed / duration_ms)
            eased = progress ** 2
            cur_relx = start_relx + (1.0 - start_relx) * eased
            panel.place_configure(relx=cur_relx)
            if progress < 1.0:
                self.after(20, _step_out)
            else:
                panel.destroy()
                self._active_slide_panel = None

        _step_out()

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
        """Handle case selection from Dashboard, setting context and opening Evidence Explorer via slide-in."""
        self.selected_case_id = case_id
        case = get_case_by_id(case_id)
        if case:
            self.set_case_context(f"CASE: {case['case_number']} | {case['case_name']}")
            self._update_toolbar_case_badge(case['case_number'])
        else:
            self.set_case_context(f"CASE #{case_id}")
            self._update_toolbar_case_badge(f"CASE #{case_id}")

        self.show_slide_in_panel(CaseDetailFrame, case_id=case_id)

    def _update_toolbar_case_badge(self, case_text: str) -> None:
        """Refresh case pill in top toolbar."""
        for child in self.case_badge_container.winfo_children():
            child.destroy()
        self.case_badge = create_soc_badge(
            self.case_badge_container,
            f"CASE: {case_text}" if not case_text.startswith("CASE") else case_text,
            color=TEAL_MID,
            bg=APP_BG,
        )
        self.case_badge.pack(side="left")

    def _on_global_search(self, event=None) -> None:
        """Handle global search input submission."""
        query = self.entry_search.get().strip()
        if query and query != "Search cases, hashes, indicators...":
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


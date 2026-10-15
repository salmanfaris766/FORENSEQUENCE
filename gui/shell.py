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
    BG_DEEP,
    CARD_BG,
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
    TEXT_MAIN,
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
    draw_squircle,
    LiquidButton,
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
# FLUID DRIFTING ORB BACKGROUND (60 FPS NATIVE CANVAS)
# =============================================================================

class FluidBackground(tk.Canvas):
    """
    Animated flowing background rendering 4 massive, soft drifting ovals
    (#061C1A, #041211, #05221F, #031413) over deep obsidian (#020505).
    Drifts smoothly across the screen using math.sin/cos and time variables,
    updating via root.after(30) to create a liquid wave effect behind the UI.
    """

    def __init__(self, parent: tk.Misc, **kwargs):
        super().__init__(
            parent,
            bg=BG_DEEP,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.time_offset = 0.0
        self._anim_id: Optional[str] = None
        self._orb_ids: list = []

        # (fill_color, center_x_ratio, center_y_ratio, rx_ratio, ry_ratio, amp_x, amp_y, speed_x, speed_y, phase)
        self._orb_specs = [
            ("#061C1A", 0.22, 0.28, 0.40, 0.36, 110.0, 80.0, 0.016, 0.012, 0.0),
            ("#041211", 0.78, 0.32, 0.44, 0.40, 120.0, 90.0, 0.018, 0.015, 1.8),
            ("#05221F", 0.38, 0.76, 0.42, 0.38, 130.0, 75.0, 0.014, 0.018, 3.4),
            ("#031413", 0.84, 0.82, 0.36, 0.34, 95.0, 85.0, 0.022, 0.014, 5.0),
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

            for i, (col, bx_r, by_r, rx_r, ry_r, amp_x, amp_y, sp_x, sp_y, ph) in enumerate(self._orb_specs):
                t_x = self.time_offset * sp_x + ph
                t_y = self.time_offset * sp_y + ph * 0.7
                cx = w * bx_r + amp_x * math.sin(t_x)
                cy = h * by_r + amp_y * math.cos(t_y)
                rx = max(100.0, w * rx_r)
                ry = max(80.0, h * ry_r)

                x1, y1 = cx - rx, cy - ry
                x2, y2 = cx + rx, cy + ry

                if i >= len(self._orb_ids):
                    oid = self.create_oval(x1, y1, x2, y2, fill=col, outline="")
                    self._orb_ids.append(oid)
                else:
                    self.coords(self._orb_ids[i], x1, y1, x2, y2)

        self._anim_id = self.after(30, self._animate)

    def _on_destroy(self, event=None) -> None:
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None


# Compatibility Alias
AnimatedWaveBackground = FluidBackground


# =============================================================================
# SIDEBAR NAVIGATION ITEM (SQUIRCLE PILL)
# =============================================================================

class SOCNavItem(tk.Canvas):
    """
    SOC Workstation sidebar navigation button with smooth squircle pill styling:
    - Default: TEXT_SECONDARY text, CARD_BG
    - Hover: TEXT_PRIMARY text, PANEL_ELEVATED background pill
    - Selected: MINT text, PANEL_HOVER background pill, MINT active pill dot
    """

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        route_name: str,
        on_click_callback: Callable[[str], None],
        width: int = 240,
        height: int = 38,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=CARD_BG,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.item_text = text
        self.route_name = route_name
        self.on_click_callback = on_click_callback
        self.item_width = width
        self.item_height = height

        self.is_active = False
        self.is_hovered = False

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        self.redraw()

    def _on_configure(self, event) -> None:
        if event.width > 2 and event.height > 2:
            if event.width != self.item_width or event.height != self.item_height:
                self.item_width = event.width
                self.item_height = event.height
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
        """Render SOC nav item squircle state."""
        self.delete("all")
        w, h = self.item_width, self.item_height

        if self.is_active:
            bg_pill = PANEL_HOVER
            outline_pill = BORDER_SECONDARY
            fg_color = MINT
            font_spec = (FONT_FALLBACK, FS_BASE, "bold")
        elif self.is_hovered:
            bg_pill = PANEL_ELEVATED
            outline_pill = BORDER
            fg_color = TEXT_PRIMARY
            font_spec = (FONT_FALLBACK, FS_BASE, "normal")
        else:
            bg_pill = ""
            outline_pill = ""
            fg_color = TEXT_SECONDARY
            font_spec = (FONT_FALLBACK, FS_BASE, "normal")

        if bg_pill:
            draw_squircle(
                self,
                4, 2, w - 4, h - 2,
                radius=10,
                fill=bg_pill,
                outline=outline_pill,
                width=1,
            )

        # Left indicator dot for active item
        if self.is_active:
            self.create_oval(14, h // 2 - 3, 20, h // 2 + 3, fill=MINT, outline="")
            text_x = 28
        else:
            text_x = 20

        self.create_text(
            text_x,
            h // 2,
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
    - Flowing animated fluid background with drifting glowing orbs across the entire screen
    - Floating Squircle Left Sidebar with 15px margins from edges
    - Floating Squircle Pill Search with magnifying glass vector icon
    - Ultra-clean minimalist layout without redundant breadcrumbs
    - Modal Slide-In Navigation for drill-down case investigation
    - Minimalist Bottom Status Bar with system telemetry and real-time UTC clock
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
        """Assemble liquid glassmorphic workstation chrome with floating squircle sidebar and floating search pill."""
        self.configure(style="TFrame")

        # Full-window Fluid Animated Background Canvas
        self.fluid_bg = FluidBackground(self)
        self.fluid_bg.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        # ---------------------------------------------------------------------
        # 1. Floating Left Sidebar (Squircle Panel with margin=15px from edges)
        # ---------------------------------------------------------------------
        self.sidebar_outer = tk.Frame(self, bg=BG_DEEP, width=260)
        self.sidebar_outer.pack(side="left", fill="y", padx=(15, 10), pady=15)
        self.sidebar_outer.pack_propagate(False)

        # Vector Canvas drawing floating squircle container
        self.sidebar_canvas = tk.Canvas(
            self.sidebar_outer,
            width=260,
            bg=BG_DEEP,
            highlightthickness=0,
            bd=0,
        )
        self.sidebar_canvas.pack(fill="both", expand=True)

        self.sidebar_container = tk.Frame(self.sidebar_canvas, bg=CARD_BG)
        self._sidebar_win_id = self.sidebar_canvas.create_window(
            130, 200, window=self.sidebar_container, anchor="center"
        )

        def _on_sidebar_configure(event):
            sw = event.width
            sh = event.height
            self.sidebar_canvas.delete("bg_squircle")
            draw_squircle(
                self.sidebar_canvas,
                1, 1, sw - 1, sh - 1,
                radius=24,
                fill=CARD_BG,
                outline=BORDER,
                width=1,
                tags="bg_squircle",
            )
            self.sidebar_canvas.tag_lower("bg_squircle")
            self.sidebar_canvas.coords(self._sidebar_win_id, sw // 2, sh // 2)
            self.sidebar_canvas.itemconfigure(
                self._sidebar_win_id,
                width=max(1, sw - 6),
                height=max(1, sh - 6),
            )

        self.sidebar_canvas.bind("<Configure>", _on_sidebar_configure)

        # Top Branding Header in Sidebar
        brand_frame = tk.Frame(self.sidebar_container, bg=CARD_BG, padx=SP_4, pady=SP_3)
        brand_frame.pack(fill="x")

        tk.Label(
            brand_frame,
            text="FORENSEQUENCE",
            fg=TEXT_MAIN,
            bg=CARD_BG,
            font=(FONT_DISPLAY, 13, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            brand_frame,
            text="v1.0 SOC WORKSTATION",
            fg=TEXT_MUTED,
            bg=CARD_BG,
            font=(FONT_FALLBACK, 9, "bold"),
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
            ]),
        ]

        for group_label, items in nav_groups:
            cat_label = tk.Label(
                self.sidebar_container,
                text=group_label,
                fg=TEXT_MUTED,
                bg=CARD_BG,
                font=(FONT_FALLBACK, 9, "bold"),
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
                    width=240,
                    height=36,
                )
                nav_btn.pack(fill="x", pady=1, padx=4)
                self._nav_items[route_key] = nav_btn

        # Spacer pushing content up
        spacer = tk.Frame(self.sidebar_container, bg=CARD_BG)
        spacer.pack(fill="both", expand=True)

        # ---------------------------------------------------------------------
        # 2. Main Right Workstation Area (Top Toolbar + Content + Status Bar)
        # ---------------------------------------------------------------------
        self.workstation_area = tk.Frame(self, bg=BG_DEEP)
        self.workstation_area.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=15)

        # --- Top Toolbar (Minimalist iOS Style, Floating Pill Search) ---
        self.top_toolbar = tk.Frame(self.workstation_area, height=48, bg=BG_DEEP)
        self.top_toolbar.pack(fill="x", side="top")
        self.top_toolbar.pack_propagate(False)

        # Breadcrumb placeholders (kept for compatibility with show_screen)
        self.lbl_breadcrumb_prefix = tk.Label(self.top_toolbar, text="", bg=BG_DEEP)
        self.lbl_breadcrumb_active = tk.Label(self.top_toolbar, text="", bg=BG_DEEP)

        # Left Header Title in Toolbar
        self.toolbar_title = tk.Label(
            self.top_toolbar,
            text="FORENSIC NEXUS",
            fg=TEXT_MUTED,
            bg=BG_DEEP,
            font=(FONT_FALLBACK, 10, "bold"),
        )
        self.toolbar_title.pack(side="left", padx=SP_2)

        # Center Toolbar: Floating Rounded Pill Search Bar with Vector Magnifying Glass
        self.search_pill_frame = tk.Frame(self.top_toolbar, bg=BG_DEEP)
        self.search_pill_frame.pack(side="left", expand=True)

        self.search_canvas = tk.Canvas(
            self.search_pill_frame,
            width=360,
            height=36,
            bg=BG_DEEP,
            highlightthickness=0,
            bd=0,
        )
        self.search_canvas.pack()

        self._search_pill_id = draw_squircle(
            self.search_canvas,
            1, 1, 359, 35,
            radius=18,
            fill=CARD_BG,
            outline=BORDER_SECONDARY,
            width=1,
            tags="search_pill",
        )

        # Vector magnifying glass icon
        self.search_canvas.create_oval(14, 11, 23, 20, outline=TEXT_MUTED, width=1.6, tags="glass_icon")
        self.search_canvas.create_line(21, 19, 27, 25, fill=TEXT_MUTED, width=2.0, tags="glass_icon")

        search_placeholder = "Search cases, indicators..."
        self.entry_search = tk.Entry(
            self.search_canvas,
            bg=CARD_BG,
            fg=TEXT_MUTED,
            insertbackground=CYAN,
            bd=0,
            highlightthickness=0,
            font=(FONT_FALLBACK, FS_BASE),
        )
        self.search_canvas.create_window(195, 18, window=self.entry_search, width=310, height=24)
        self.entry_search.insert(0, search_placeholder)

        def _on_search_focus_in(event):
            self.search_canvas.itemconfig(self._search_pill_id, outline=CYAN)
            if self.entry_search.get() == search_placeholder:
                self.entry_search.delete(0, tk.END)
                self.entry_search.config(fg=TEXT_MAIN)

        def _on_search_focus_out(event):
            self.search_canvas.itemconfig(self._search_pill_id, outline=BORDER_SECONDARY)
            if not self.entry_search.get().strip():
                self.entry_search.delete(0, tk.END)
                self.entry_search.insert(0, search_placeholder)
                self.entry_search.config(fg=TEXT_MUTED)

        self.entry_search.bind("<FocusIn>", _on_search_focus_in)
        self.entry_search.bind("<FocusOut>", _on_search_focus_out)
        self.entry_search.bind("<Return>", self._on_global_search)

        # Right Toolbar: Case Context Badge + Live Status Dot
        self.toolbar_right = tk.Frame(self.top_toolbar, bg=BG_DEEP)
        self.toolbar_right.pack(side="right", padx=SP_2, fill="y")

        self.case_badge_container = tk.Frame(self.toolbar_right, bg=BG_DEEP)
        self.case_badge_container.pack(side="left", padx=(0, SP_3), pady=8)
        self.case_badge = create_soc_badge(self.case_badge_container, "NO ACTIVE CASE", color=TEAL_MID, bg=BG_DEEP)
        self.case_badge.pack(side="left")

        # Live Status Indicator Dot & Label
        self.status_box = tk.Frame(self.toolbar_right, bg=BG_DEEP)
        self.status_box.pack(side="left", pady=13)

        self.dot_canvas = tk.Canvas(
            self.status_box, width=12, height=12, bg=BG_DEEP, highlightthickness=0, bd=0
        )
        self.dot_canvas.pack(side="left", padx=(0, 6))
        self.dot_item = self.dot_canvas.create_oval(2, 2, 10, 10, fill=CYAN, outline="")

        self.status_label = tk.Label(
            self.status_box,
            text="ONLINE",
            fg=TEXT_SECONDARY,
            bg=BG_DEEP,
            font=(FONT_MONO_FALLBACK, FS_XS, "bold"),
        )
        self.status_label.pack(side="left")

        # --- Bottom Status Bar (Height 26px, CARD_BG, floating feel) ---
        self.status_bar = tk.Frame(self.workstation_area, height=26, bg=CARD_BG)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        # Left Status Bar Info
        self.lbl_system_status = tk.Label(
            self.status_bar,
            text="SYSTEM STATUS: ONLINE | KNOWLEDGE BASE: 9 RULES ACTIVE",
            fg=TEXT_MUTED,
            bg=CARD_BG,
            font=(FONT_MONO_FALLBACK, 8, "normal"),
        )
        self.lbl_system_status.pack(side="left", padx=SP_4)

        # Center Status Bar Summary
        self.case_context_label = tk.Label(
            self.status_bar,
            text="FORENSIC WORKSTATION | THREAT INTELLIGENCE ENGINE",
            fg=TEXT_MUTED,
            bg=CARD_BG,
            font=(FONT_FALLBACK, 8, "normal"),
        )
        self.case_context_label.pack(side="left", expand=True)

        # Right Real-time UTC Clock
        self.clock_label = tk.Label(
            self.status_bar,
            text="--:--:-- UTC",
            fg=TEXT_SECONDARY,
            bg=CARD_BG,
            font=(FONT_MONO_FALLBACK, 9, "bold"),
        )
        self.clock_label.pack(side="right", padx=SP_4)

        # --- Central Screen Container Area with flowing fluid background ---
        self.content_container = tk.Frame(self.workstation_area, bg=BG_DEEP)
        self.content_container.pack(fill="both", expand=True, pady=(6, 4))

        # Fluid background also fills content container so gaps between cards reveal flowing waves
        self.wave_bg = FluidBackground(self.content_container)
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


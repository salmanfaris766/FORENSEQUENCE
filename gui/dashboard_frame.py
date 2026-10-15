# =============================================================================
# gui/dashboard_frame.py
# FORENSEQUENCE - Security Operations Dashboard
# iOS Liquid Glassmorphism Minimalist Architecture
# Custom Canvas vector graphics, 60FPS fluid animations, Zero Matplotlib
# =============================================================================

from __future__ import annotations

import datetime
import math
import tkinter as tk
from typing import Optional, Callable, Dict, Any, List
import ttkbootstrap as ttk

from gui.theme import (
    BG_DEEP,
    CARD_BG,
    TEXT_MAIN,
    TEXT_MUTED,
    CYAN,
    CYAN_GLOW,
    MINT,
    TEAL,
    TEAL_MID,
    TEAL_DARK,
    TEAL_DEEP,
    CRITICAL,
    HIGH,
    MEDIUM,
    LOW,
    BORDER,
    BORDER_SECONDARY,
    BORDER_HOVER,
    FONT_DISPLAY,
    FONT_FALLBACK,
    FONT_MONO_FALLBACK,
    FS_XS,
    FS_SM,
    FS_BASE,
    FS_MD,
    FS_LG,
    FS_XL,
    FS_2XL,
    SP_1,
    SP_2,
    SP_3,
    SP_4,
    SP_6,
    draw_squircle,
    LiquidButton,
    create_soc_badge,
    create_divider,
    _lerp_color,
)

from database import (
    initialize_db,
    get_all_cases,
    get_evidence_for_case,
    get_findings_for_case,
    get_case_by_id,
)


# =============================================================================
# VECTOR KPI SQUIRCLE CARD (CANVAS BASED, 2PX HOVER LIFT)
# =============================================================================

class KPISquircleCard(tk.Canvas):
    """
    Floating iOS Squircle Metric Card rendered entirely on Canvas.
    - Large 36px bold typographic figure
    - Minimal 10px uppercase muted label
    - Subtle 2px upward hover lift with smooth outline illumination
    """

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        val_color: str,
        initial_val: str = "0",
        **kwargs,
    ):
        super().__init__(
            parent,
            height=106,
            bg=BG_DEEP,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            **kwargs,
        )
        self.title = title
        self.val_color = val_color
        self.val = str(initial_val)
        self._curr_w = 220
        self._curr_h = 106
        self._is_hovered = False
        self._y_lift = 0

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_configure(self, event) -> None:
        if event.width > 10 and event.height > 10:
            if event.width != self._curr_w or event.height != self._curr_h:
                self._curr_w = event.width
                self._curr_h = event.height
                self._redraw()

    def set_value(self, val: Any) -> None:
        self.val = str(val)
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        w, h = self._curr_w, self._curr_h
        pad = 2
        outline_color = (CYAN if self.val_color != CRITICAL else CRITICAL) if self._is_hovered else BORDER_SECONDARY
        outline_w = 1.5 if self._is_hovered else 1.0

        # Background Squircle Surface
        draw_squircle(
            self,
            pad, pad, w - pad, h - pad,
            radius=20,
            fill=CARD_BG,
            outline=outline_color,
            width=outline_w,
            tags="card_bg",
        )

        # Huge High-Contrast Number (36px bold)
        self.create_text(
            22, 42 + self._y_lift,
            anchor="w",
            text=self.val,
            fill=self.val_color,
            font=(FONT_FALLBACK, 34, "bold"),
            tags="kpi_num",
        )

        # Minimal Upper Label
        self.create_text(
            22, 80 + self._y_lift,
            anchor="w",
            text=self.title.upper(),
            fill=TEXT_MUTED,
            font=(FONT_FALLBACK, 9, "bold"),
            tags="kpi_label",
        )

    def _on_enter(self, event=None) -> None:
        if not self._is_hovered:
            self._is_hovered = True
            self._y_lift = -2
            self.move("kpi_num", 0, -2)
            self.move("kpi_label", 0, -2)
            active_outline = CYAN if self.val_color != CRITICAL else CRITICAL
            self.itemconfig("card_bg", outline=active_outline, width=1.5)

    def _on_leave(self, event=None) -> None:
        if self._is_hovered:
            self._is_hovered = False
            self._y_lift = 0
            self.move("kpi_num", 0, 2)
            self.move("kpi_label", 0, 2)
            self.itemconfig("card_bg", outline=BORDER_SECONDARY, width=1.0)


# =============================================================================
# CUSTOM CANVAS ACTIVITY BEZIER TIMELINE CHART (NO MATPLOTLIB)
# =============================================================================

class ActivityTimelineCanvas(tk.Canvas):
    """
    Custom smooth bezier intrusion frequency chart.
    Features:
    - Floating squircle panel frame
    - Animated left-to-right line draw-in
    - Multi-layered oceanic teal gradient underglow
    - Glowing telemetry markers
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(
            parent,
            height=250,
            bg=BG_DEEP,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._curr_w = 540
        self._curr_h = 250
        self._time_labels = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "23:59"]
        self._data_points: List[float] = [1.0, 1.0, 3.0, 5.0, 2.0, 1.0, 1.0]
        self._anim_step = 0
        self._total_anim_steps = 12
        self._anim_id: Optional[str] = None

        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event) -> None:
        if event.width > 20 and event.height > 20:
            if event.width != self._curr_w or event.height != self._curr_h:
                self._curr_w = event.width
                self._curr_h = event.height
                self._render_static()

    def update_data(self, cases_count: int, findings_count: int) -> None:
        """Derive responsive telemetry curve and trigger draw-in animation."""
        base = cases_count * 3 + findings_count
        if base > 0:
            self._data_points = [
                max(1.0, base * 0.10),
                max(1.0, base * 0.08),
                max(2.0, base * 0.22),
                max(3.0, base * 0.35),
                max(2.0, base * 0.16),
                max(1.0, base * 0.06),
                max(1.0, base * 0.03),
            ]
        else:
            self._data_points = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self._start_draw_animation()

    def _start_draw_animation(self) -> None:
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None

        self._anim_step = 1

        def _step():
            if not self.winfo_exists():
                return
            progress = self._anim_step / float(self._total_anim_steps)
            self._render_curve(progress=progress)
            if self._anim_step < self._total_anim_steps:
                self._anim_step += 1
                self._anim_id = self.after(22, _step)
            else:
                self._anim_id = None

        _step()

    def _render_static(self) -> None:
        self._render_curve(progress=1.0)

    def _render_curve(self, progress: float = 1.0) -> None:
        self.delete("all")
        w, h = self._curr_w, self._curr_h
        pad = 2

        # 1. Background Squircle Surface
        draw_squircle(
            self,
            pad, pad, w - pad, h - pad,
            radius=20,
            fill=CARD_BG,
            outline=BORDER_SECONDARY,
            width=1,
            tags="panel_bg",
        )

        # 2. Header
        self.create_text(
            24, 26,
            anchor="w",
            text="EVENT FREQUENCY & INTRUSION TIMELINE",
            fill=TEXT_MAIN,
            font=(FONT_FALLBACK, 11, "bold"),
        )

        # Right Live Telemetry Badge
        self.create_oval(w - 130, 23, w - 124, 29, fill=CYAN, outline="")
        self.create_text(
            w - 118, 26,
            anchor="w",
            text="LIVE TELEMETRY",
            fill=CYAN,
            font=(FONT_MONO_FALLBACK, 8, "bold"),
        )

        # 3. Chart Coordinates
        left_m = 48
        right_m = 32
        top_m = 56
        bot_m = 42

        chart_w = max(10, w - left_m - right_m)
        chart_h = max(10, h - top_m - bot_m)
        baseline_y = h - bot_m

        max_val = max(max(self._data_points), 4.0)

        # Subtle Horizontal Grid Lines
        for g in range(3):
            gy = baseline_y - (chart_h / 2.0) * g
            self.create_line(
                left_m, gy, w - right_m, gy,
                fill="#0B1E1C",
                dash=(3, 3),
                width=1,
            )
            # Label
            val_label = str(int((max_val / 2.0) * g))
            self.create_text(
                left_m - 10, gy,
                anchor="e",
                text=val_label,
                fill=TEXT_MUTED,
                font=(FONT_MONO_FALLBACK, 8, "normal"),
            )

        # Time labels
        n_pts = len(self._data_points)
        x_coords = []
        y_coords = []
        for idx in range(n_pts):
            cx = left_m + (chart_w / float(n_pts - 1)) * idx
            cy = baseline_y - (self._data_points[idx] / max_val) * chart_h
            x_coords.append(cx)
            y_coords.append(cy)

            self.create_text(
                cx, baseline_y + 16,
                anchor="center",
                text=self._time_labels[idx],
                fill=TEXT_MUTED,
                font=(FONT_MONO_FALLBACK, 8, "normal"),
            )

        # Compute animated coordinates
        if progress < 1.0:
            max_x = left_m + chart_w * progress
            anim_x = []
            anim_y = []
            for i in range(n_pts):
                if x_coords[i] <= max_x:
                    anim_x.append(x_coords[i])
                    anim_y.append(y_coords[i])
                else:
                    # Interpolate last point
                    prev_x = x_coords[i - 1]
                    prev_y = y_coords[i - 1]
                    cur_x = x_coords[i]
                    cur_y = y_coords[i]
                    factor = (max_x - prev_x) / float(cur_x - prev_x)
                    inter_y = prev_y + (cur_y - prev_y) * factor
                    anim_x.append(max_x)
                    anim_y.append(inter_y)
                    break
        else:
            anim_x = x_coords
            anim_y = y_coords

        if len(anim_x) >= 2:
            # 4. Multi-layered Teal Gradient Polygon under the curve
            # Layer 1 (Bottom deep oceanic wash)
            poly1 = [anim_x[0], baseline_y]
            for ax, ay in zip(anim_x, anim_y):
                poly1.extend([ax, ay])
            poly1.extend([anim_x[-1], baseline_y])
            self.create_polygon(poly1, smooth=True, fill="#051E1C", outline="", tags="gradient1")

            # Layer 2 (Mid-level teal illumination)
            poly2 = [anim_x[0], baseline_y]
            for ax, ay in zip(anim_x, anim_y):
                mid_y = baseline_y - (baseline_y - ay) * 0.65
                poly2.extend([ax, mid_y])
            poly2.extend([anim_x[-1], baseline_y])
            self.create_polygon(poly2, smooth=True, fill="#082A27", outline="", tags="gradient2")

            # Layer 3 (Upper luminous ribbon near curve)
            poly3 = [anim_x[0], baseline_y]
            for ax, ay in zip(anim_x, anim_y):
                up_y = baseline_y - (baseline_y - ay) * 0.90
                poly3.extend([ax, up_y])
            poly3.extend([anim_x[-1], baseline_y])
            self.create_polygon(poly3, smooth=True, fill="#0C3B37", outline="", tags="gradient3")

            # 5. Primary Smooth Bezier Line
            line_coords = []
            for ax, ay in zip(anim_x, anim_y):
                line_coords.extend([ax, ay])
            self.create_line(
                line_coords,
                smooth=True,
                fill=CYAN,
                width=2.5,
                tags="bezier_line",
            )

        # 6. Glowing Telemetry Nodes
        if progress >= 0.95:
            for idx in range(n_pts):
                nx, ny = x_coords[idx], y_coords[idx]
                val = self._data_points[idx]
                node_col = CRITICAL if val >= (max_val * 0.6 and val >= 3.0) else CYAN

                # Outer halo
                self.create_oval(nx - 5, ny - 5, nx + 5, ny + 5, fill=BG_DEEP, outline=node_col, width=1.5)
                # Inner glow core
                self.create_oval(nx - 2.5, ny - 2.5, nx + 2.5, ny + 2.5, fill=node_col, outline="")


# =============================================================================
# CUSTOM CANVAS SEVERITY BREAKDOWN CHART (EXPANDING HORIZONTAL PILL BARS)
# =============================================================================

class SeverityBreakdownCanvas(tk.Canvas):
    """
    Custom animated horizontal pill-bar severity breakdown chart.
    Features:
    - Floating squircle container
    - Colors: Low (#2DE3C8 Mint), Medium (#0E8A80 Teal), High (#0A524C Deep Teal), Critical (#FF2A55 Red)
    - Zero yellow / orange
    - Smooth animated bar expansion on update
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(
            parent,
            height=250,
            bg=BG_DEEP,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._curr_w = 380
        self._curr_h = 250
        self._categories = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self._cat_colors = {
            "LOW": LOW,          # #2DE3C8 Mint
            "MEDIUM": MEDIUM,    # #0E8A80 Mid Teal
            "HIGH": HIGH,        # #0A524C Deep Teal
            "CRITICAL": CRITICAL # #FF2A55 Neon Red
        }
        self._counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        self._total_findings = 0
        self._anim_step = 0
        self._total_anim_steps = 10
        self._anim_id: Optional[str] = None

        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event) -> None:
        if event.width > 20 and event.height > 20:
            if event.width != self._curr_w or event.height != self._curr_h:
                self._curr_w = event.width
                self._curr_h = event.height
                self._render_static()

    def update_counts(self, counts: Dict[str, int], total: int) -> None:
        self._counts = counts
        self._total_findings = total
        self._start_expansion_animation()

    def _start_expansion_animation(self) -> None:
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None

        self._anim_step = 1

        def _step():
            if not self.winfo_exists():
                return
            progress = self._anim_step / float(self._total_anim_steps)
            ease_prog = 1.0 - (1.0 - progress) ** 3
            self._render_bars(progress=ease_prog)
            if self._anim_step < self._total_anim_steps:
                self._anim_step += 1
                self._anim_id = self.after(20, _step)
            else:
                self._anim_id = None

        _step()

    def _render_static(self) -> None:
        self._render_bars(progress=1.0)

    def _render_bars(self, progress: float = 1.0) -> None:
        self.delete("all")
        w, h = self._curr_w, self._curr_h
        pad = 2

        # 1. Background Squircle Surface
        draw_squircle(
            self,
            pad, pad, w - pad, h - pad,
            radius=20,
            fill=CARD_BG,
            outline=BORDER_SECONDARY,
            width=1,
            tags="panel_bg",
        )

        # 2. Header
        self.create_text(
            22, 26,
            anchor="w",
            text="THREAT SEVERITY BREAKDOWN",
            fill=TEXT_MAIN,
            font=(FONT_FALLBACK, 11, "bold"),
        )

        self.create_text(
            w - 22, 26,
            anchor="e",
            text=f"{self._total_findings} FINDINGS",
            fill=TEXT_MUTED,
            font=(FONT_MONO_FALLBACK, 8, "bold"),
        )

        # 3. Bar Geometry
        bar_left = 95
        bar_right = w - 48
        max_bar_w = max(10, bar_right - bar_left)
        max_count = max(max(self._counts.values()) if self._counts else 0, 4)

        row_y_start = 64
        row_gap = 42

        for idx, cat in enumerate(self._categories):
            ry = row_y_start + idx * row_gap
            cnt = self._counts.get(cat, 0)
            color = self._cat_colors[cat]

            # Category Indicator & Text
            self.create_oval(22, ry - 4, 30, ry + 4, fill=color, outline="")
            self.create_text(
                36, ry,
                anchor="w",
                text=cat,
                fill=TEXT_MAIN,
                font=(FONT_FALLBACK, 9, "bold"),
            )

            # Background Inset Track Pill
            track_h = 14
            track_y1 = ry - track_h // 2
            track_y2 = ry + track_h // 2
            draw_squircle(
                self,
                bar_left, track_y1, bar_right, track_y2,
                radius=7,
                fill="#051211",
                outline="#0D2220",
                width=1,
            )

            # Filled Foreground Pill Bar
            target_w = (cnt / float(max_count)) * max_bar_w
            curr_w = target_w * progress

            if cnt > 0 and curr_w > 0:
                curr_w = max(14.0, curr_w)
                draw_squircle(
                    self,
                    bar_left, track_y1, bar_left + curr_w, track_y2,
                    radius=7,
                    fill=color,
                    outline="",
                    width=0,
                )

            # Numeric Value Label on Right
            self.create_text(
                w - 18, ry,
                anchor="e",
                text=str(cnt),
                fill=TEXT_MAIN if cnt > 0 else TEXT_MUTED,
                font=(FONT_MONO_FALLBACK, 9, "bold"),
            )


# =============================================================================
# RECENT ACTIVITY SQUIRCLE ROW CARD (CANVAS BASED, NEON DOT STATUS)
# =============================================================================

class RecentActivityRowCard(tk.Canvas):
    """
    Minimalist floating squircle row displaying a single forensic investigation.
    Features:
    - Glowing neon status dot (no boxy badge)
    - High-contrast typography & clean metadata
    - Liquid pill button for investigation drilldown
    - 60FPS hover outline illumination
    """

    def __init__(
        self,
        parent: tk.Widget,
        case: Dict[str, Any],
        ev_count: int,
        findings_count: int,
        on_view_callback: Callable[[int], None],
        **kwargs,
    ):
        super().__init__(
            parent,
            height=62,
            bg=CARD_BG,
            highlightthickness=0,
            bd=0,
            cursor="arrow",
            **kwargs,
        )
        self.case = case
        self.cid = case.get("id", 0)
        self.ev_count = ev_count
        self.findings_count = findings_count
        self.on_view_callback = on_view_callback

        self._curr_w = 800
        self._curr_h = 62
        self._is_hovered = False

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_configure(self, event) -> None:
        if event.width > 20 and event.height > 20:
            if event.width != self._curr_w or event.height != self._curr_h:
                self._curr_w = event.width
                self._curr_h = event.height
                self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        w, h = self._curr_w, self._curr_h
        pad = 2

        outline_c = BORDER_HOVER if self._is_hovered else BORDER_SECONDARY
        outline_w = 1.5 if self._is_hovered else 1.0

        # Background Squircle Surface
        draw_squircle(
            self,
            pad, pad, w - pad, h - pad,
            radius=14,
            fill="#091A18" if self._is_hovered else "#061514",
            outline=outline_c,
            width=outline_w,
            tags="card_bg",
        )

        status = str(self.case.get("status", "OPEN")).upper()
        if status == "OPEN":
            dot_color = CYAN
        elif status == "INVESTIGATING":
            dot_color = MINT
        elif status == "CLOSED":
            dot_color = TEXT_MUTED
        else:
            dot_color = TEAL_MID

        # Left Glowing Status Dot
        self.create_oval(18, h // 2 - 4, 26, h // 2 + 4, fill=dot_color, outline="")

        # Case Number & Title
        c_num = self.case.get("case_number", "CASE-UNKNOWN")
        c_name = self.case.get("case_name", "Untitled Case")
        inv = self.case.get("investigator", "Unassigned")

        self.create_text(
            36, h // 2 - 10,
            anchor="w",
            text=c_num,
            fill=TEXT_MAIN,
            font=(FONT_FALLBACK, 10, "bold"),
        )
        self.create_text(
            36, h // 2 + 10,
            anchor="w",
            text=f"{c_name}  •  Lead: {inv}",
            fill="#8BA7A3",
            font=(FONT_FALLBACK, 9, "normal"),
        )

        # Right Section: Badges, Status Text, Button
        btn_w = 110
        btn_x = w - btn_w - 18
        cy = h // 2

        # View Button (LiquidButton)
        if not hasattr(self, "_btn_view") or self._btn_view is None:
            self._btn_view = LiquidButton(
                self,
                text="INVESTIGATE",
                command=lambda: self.on_view_callback(self.cid),
                width=btn_w,
                height=32,
                radius=16,
                bg="#061514",
                fill_color=TEAL_DARK,
                hover_color=CYAN,
                text_color=TEXT_MAIN,
                hover_text_color=BG_DEEP,
                border_color=BORDER_SECONDARY,
                border_width=1,
                font=(FONT_FALLBACK, 9, "bold"),
            )
        self.create_window(btn_x + btn_w // 2, cy, window=self._btn_view)

        # Status text with subtle label
        self.create_text(
            btn_x - 24, cy,
            anchor="e",
            text=status,
            fill=dot_color,
            font=(FONT_FALLBACK, 9, "bold"),
        )

        # Artifacts & Findings Pills
        findings_str = f"{self.findings_count} FINDINGS"
        ev_str = f"{self.ev_count} EVIDENCE"

        self.create_text(
            btn_x - 140, cy,
            anchor="e",
            text=findings_str,
            fill=TEAL,
            font=(FONT_MONO_FALLBACK, 9, "bold"),
        )

        self.create_text(
            btn_x - 250, cy,
            anchor="e",
            text=ev_str,
            fill=MINT,
            font=(FONT_MONO_FALLBACK, 9, "bold"),
        )

    def _on_enter(self, event=None) -> None:
        if not self._is_hovered:
            self._is_hovered = True
            self.itemconfig("card_bg", outline=BORDER_HOVER, fill="#091A18", width=1.5)
            if hasattr(self, "_btn_view") and self._btn_view:
                self._btn_view.configure(bg="#091A18")

    def _on_leave(self, event=None) -> None:
        if self._is_hovered:
            self._is_hovered = False
            self.itemconfig("card_bg", outline=BORDER_SECONDARY, fill="#061514", width=1.0)
            if hasattr(self, "_btn_view") and self._btn_view:
                self._btn_view.configure(bg="#061514")


# =============================================================================
# MAIN DASHBOARD FRAME (IOS LIQUID GLASSMORPHISM)
# =============================================================================

class DashboardFrame(ttk.Frame):
    """
    Security Operations Dashboard Screen.
    Minimalist iOS liquid glassmorphism experience:
    - Transparent-simulated background revealing the animated fluid orb engine
    - Single large typographic header 'Security Operations' (28px bold white)
    - 4 Vector KPI squircle cards with 2px hover lift
    - Custom Canvas bezier activity curve and horizontal pill-bar severity chart
    - Floating squircle recent activity rows with neon status indicators
    """

    def __init__(
        self,
        parent: tk.Misc,
        on_navigate_callback: Optional[Callable[[str], None]] = None,
        on_select_case_callback: Optional[Callable[[int], None]] = None,
        shell=None,
    ):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.on_navigate_callback = on_navigate_callback
        self.on_select_case_callback = on_select_case_callback
        self.shell = shell

        self.active_time_range = "ALL"
        self._time_range_buttons: Dict[str, tk.Label] = {}

        initialize_db()
        self._build_ui()
        self.refresh_data()

    # -------------------------------------------------------------------------
    # Layout Builder
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct the complete minimalist iOS layout."""
        self.configure(style="TFrame")

        # Scrollable host on Canvas so fluid background shows through
        self._outer_canvas = tk.Canvas(self, bg=BG_DEEP, highlightthickness=0, bd=0)
        self._outer_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._outer_canvas.yview)
        self._outer_canvas.configure(yscrollcommand=self._outer_scrollbar.set)

        self._scroll_host = tk.Frame(self._outer_canvas, bg=BG_DEEP)
        self._scroll_window_id = self._outer_canvas.create_window(
            (0, 0), window=self._scroll_host, anchor="nw"
        )

        def _on_host_configure(event):
            self._outer_canvas.configure(scrollregion=self._outer_canvas.bbox("all"))

        def _on_canvas_configure(event):
            self._outer_canvas.itemconfig(self._scroll_window_id, width=event.width)

        self._scroll_host.bind("<Configure>", _on_host_configure)
        self._outer_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            try:
                if self._outer_canvas.winfo_exists():
                    self._outer_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        self._outer_canvas.bind("<Enter>", lambda _: self._outer_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self._outer_canvas.bind("<Leave>", lambda _: self._outer_canvas.unbind_all("<MouseWheel>"))

        self._outer_scrollbar.pack(side="right", fill="y")
        self._outer_canvas.pack(side="left", fill="both", expand=True)

        host = self._scroll_host

        # ---------------------------------------------------------------------
        # 1. Header Bar: Single Title "Security Operations" in 28px Bold White
        # ---------------------------------------------------------------------
        self.header_bar = tk.Frame(host, bg=BG_DEEP)
        self.header_bar.pack(fill="x", padx=SP_4, pady=(SP_3, SP_3))

        # Single large clean title without subtitles or breadcrumbs
        self.lbl_title = tk.Label(
            self.header_bar,
            text="Security Operations",
            fg=TEXT_MAIN,
            bg=BG_DEEP,
            font=(FONT_FALLBACK, 28, "bold"),
            anchor="w",
        )
        self.lbl_title.pack(side="left", anchor="center")

        # Right Header: Minimalist Time Range Pill Filter + [+ NEW CASE] LiquidButton
        header_right = tk.Frame(self.header_bar, bg=BG_DEEP)
        header_right.pack(side="right", anchor="center")

        # Time range segmented pill container
        self.filter_container = tk.Frame(
            header_right,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=BORDER_SECONDARY,
            bd=0,
        )
        self.filter_container.pack(side="left", padx=(0, SP_4))

        for tr_key in ("24H", "7D", "30D", "ALL"):
            btn = tk.Label(
                self.filter_container,
                text=tr_key,
                font=(FONT_MONO_FALLBACK, 9, "bold"),
                bg=MINT if tr_key == self.active_time_range else CARD_BG,
                fg=BG_DEEP if tr_key == self.active_time_range else TEXT_MUTED,
                cursor="hand2",
                padx=10,
                pady=5,
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=tr_key: self._set_time_range(k))
            self._time_range_buttons[tr_key] = btn

        # [+ NEW CASE] LiquidButton
        self.btn_new_case = LiquidButton(
            header_right,
            text="+ NEW CASE",
            command=self._handle_new_case,
            width=120,
            height=34,
            radius=17,
            bg=BG_DEEP,
            fill_color=TEAL,
            hover_color=CYAN,
            text_color=TEXT_MAIN,
            hover_text_color=BG_DEEP,
            border_color=BORDER_SECONDARY,
            border_width=1,
            font=(FONT_FALLBACK, 9, "bold"),
        )
        self.btn_new_case.pack(side="left")

        # ---------------------------------------------------------------------
        # 2. 4 Vector KPI Squircle Cards Row (Fullscreen Grid Scalable)
        # ---------------------------------------------------------------------
        self.kpi_row = tk.Frame(host, bg=BG_DEEP)
        self.kpi_row.pack(fill="x", padx=SP_4, pady=(0, SP_3))

        for col_idx in range(4):
            self.kpi_row.grid_columnconfigure(col_idx, weight=1)

        # 1. Active Investigations (Cyan / Mint)
        self.kpi_active = KPISquircleCard(
            self.kpi_row,
            title="Active Investigations",
            val_color=MINT,
        )
        self.kpi_active.grid(row=0, column=0, sticky="nsew", padx=4, pady=2)

        # 2. Evidence Artifacts (Cyan)
        self.kpi_evidence = KPISquircleCard(
            self.kpi_row,
            title="Evidence Artifacts",
            val_color=CYAN,
        )
        self.kpi_evidence.grid(row=0, column=1, sticky="nsew", padx=4, pady=2)

        # 3. Threat Indicators (Teal)
        self.kpi_indicators = KPISquircleCard(
            self.kpi_row,
            title="Threat Indicators",
            val_color=TEAL,
        )
        self.kpi_indicators.grid(row=0, column=2, sticky="nsew", padx=4, pady=2)

        # 4. Critical Threats (Red ONLY for Critical)
        self.kpi_critical = KPISquircleCard(
            self.kpi_row,
            title="Critical Threats",
            val_color=CRITICAL,
        )
        self.kpi_critical.grid(row=0, column=3, sticky="nsew", padx=4, pady=2)

        # ---------------------------------------------------------------------
        # 3. Custom Vector Canvas Charts Row (60% / 40% Split)
        # ---------------------------------------------------------------------
        self.charts_row = tk.Frame(host, bg=BG_DEEP)
        self.charts_row.pack(fill="x", padx=SP_4, pady=(0, SP_3))
        self.charts_row.grid_rowconfigure(0, weight=1)
        self.charts_row.grid_columnconfigure(0, weight=6)
        self.charts_row.grid_columnconfigure(1, weight=4)

        # Left 60%: Activity Timeline Custom Bezier Curve Canvas
        self.timeline_chart = ActivityTimelineCanvas(self.charts_row)
        self.timeline_chart.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=2)

        # Right 40%: Derived Severity Breakdown Custom Animated Pill-Bars Canvas
        self.severity_chart = SeverityBreakdownCanvas(self.charts_row)
        self.severity_chart.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=2)

        # ---------------------------------------------------------------------
        # 4. Recent Forensic Activity Section (Floating Squircle Rows)
        # ---------------------------------------------------------------------
        self._build_recent_activity_section(host)

    def _build_recent_activity_section(self, host: tk.Widget) -> None:
        """Construct the activity list container."""
        self.activity_container = tk.Frame(host, bg=BG_DEEP)
        self.activity_container.pack(fill="both", expand=True, padx=SP_4, pady=(0, SP_4))

        # Section Header Row
        hdr_row = tk.Frame(self.activity_container, bg=BG_DEEP)
        hdr_row.pack(fill="x", pady=(SP_2, SP_2))

        tk.Label(
            hdr_row,
            text="RECENT ACTIVITY",
            fg=TEXT_MAIN,
            bg=BG_DEEP,
            font=(FONT_FALLBACK, 12, "bold"),
            anchor="w",
        ).pack(side="left")

        self.lbl_case_count_badge = tk.Label(
            hdr_row,
            text="0 ACTIVE CASES",
            fg=TEXT_MUTED,
            bg=BG_DEEP,
            font=(FONT_MONO_FALLBACK, 9, "bold"),
        )
        self.lbl_case_count_badge.pack(side="right")

        # Container for rows
        self.rows_host = tk.Frame(self.activity_container, bg=BG_DEEP)
        self.rows_host.pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # Handlers & Actions
    # -------------------------------------------------------------------------

    def _set_time_range(self, time_range: str) -> None:
        self.active_time_range = time_range
        for k, btn in self._time_range_buttons.items():
            if k == time_range:
                btn.config(bg=MINT, fg=BG_DEEP)
            else:
                btn.config(bg=CARD_BG, fg=TEXT_MUTED)
        self.refresh_data()

    def _handle_new_case(self) -> None:
        if self.on_navigate_callback:
            self.on_navigate_callback("Case Investigation")

    def _handle_view_case(self, case_id: int) -> None:
        if self.on_select_case_callback:
            self.on_select_case_callback(case_id)
        if self.on_navigate_callback:
            self.on_navigate_callback("Evidence Explorer")

    # -------------------------------------------------------------------------
    # Data Refresh & Live Query
    # -------------------------------------------------------------------------

    def refresh_data(self) -> None:
        """
        Re-query SQLite database for cases, evidence, and findings.
        Updates 4 KPI figures, redraws custom canvas charts, and repopulates
        floating squircle activity rows.
        """
        cases: List[Dict[str, Any]] = get_all_cases()

        # 1. Active Cases
        active_cases = [c for c in cases if str(c.get("status", "OPEN")).upper() != "CLOSED"]
        self.kpi_active.set_value(len(active_cases))

        # 2. Total Evidence
        total_evidence = 0
        case_evidence_map: Dict[int, List[Dict[str, Any]]] = {}
        for c in cases:
            cid = c["id"]
            ev_list = get_evidence_for_case(cid)
            case_evidence_map[cid] = ev_list
            total_evidence += len(ev_list)

        self.kpi_evidence.set_value(total_evidence)

        # 3. Threat Indicators & Critical Threats
        all_findings: List[Dict[str, Any]] = []
        case_findings_map: Dict[int, List[Dict[str, Any]]] = {}
        critical_count = 0
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for c in cases:
            cid = c["id"]
            findings = get_findings_for_case(cid)
            case_findings_map[cid] = findings
            all_findings.extend(findings)
            for f in findings:
                sev = f.get("severity", 0)
                try:
                    sev = int(sev)
                except (ValueError, TypeError):
                    sev = 0

                if sev >= 25:
                    severity_counts["CRITICAL"] += 1
                    critical_count += 1
                elif sev >= 15:
                    severity_counts["HIGH"] += 1
                    critical_count += 1
                elif sev >= 10:
                    severity_counts["MEDIUM"] += 1
                else:
                    severity_counts["LOW"] += 1

        self.kpi_indicators.set_value(len(all_findings))
        self.kpi_critical.set_value(critical_count)

        # 4. Redraw Custom Bezier Activity Timeline Chart
        self.timeline_chart.update_data(len(cases), len(all_findings))

        # 5. Redraw Custom Horizontal Pill-Bars Severity Breakdown Chart
        self.severity_chart.update_counts(severity_counts, len(all_findings))

        # 6. Repopulate Recent Activity Rows
        self._render_activity_rows(cases, case_evidence_map, case_findings_map)

    def _render_activity_rows(
        self,
        cases: List[Dict[str, Any]],
        case_evidence_map: Dict[int, List[Dict[str, Any]]],
        case_findings_map: Dict[int, List[Dict[str, Any]]],
    ) -> None:
        for child in self.rows_host.winfo_children():
            child.destroy()

        self.lbl_case_count_badge.config(text=f"{len(cases)} ACTIVE CASES")

        if not cases:
            # Minimalist Empty State
            empty_canvas = tk.Canvas(
                self.rows_host,
                height=90,
                bg=BG_DEEP,
                highlightthickness=0,
                bd=0,
            )
            empty_canvas.pack(fill="x", pady=SP_2)

            def _on_empty_config(e):
                empty_canvas.delete("all")
                draw_squircle(
                    empty_canvas,
                    2, 2, e.width - 2, e.height - 2,
                    radius=16,
                    fill=CARD_BG,
                    outline=BORDER_SECONDARY,
                    width=1,
                )
                empty_canvas.create_text(
                    24, 34,
                    anchor="w",
                    text="NO ACTIVE FORENSIC INVESTIGATIONS",
                    fill=TEXT_MAIN,
                    font=(FONT_FALLBACK, 11, "bold"),
                )
                empty_canvas.create_text(
                    24, 58,
                    anchor="w",
                    text="Click [+ NEW CASE] in the top header to initialize an investigation.",
                    fill=TEXT_MUTED,
                    font=(FONT_FALLBACK, 9, "normal"),
                )

            empty_canvas.bind("<Configure>", _on_empty_config)
            return

        for case in cases:
            cid = case.get("id", 0)
            ev_count = len(case_evidence_map.get(cid, []))
            findings_count = len(case_findings_map.get(cid, []))

            row_card = RecentActivityRowCard(
                self.rows_host,
                case=case,
                ev_count=ev_count,
                findings_count=findings_count,
                on_view_callback=self._handle_view_case,
            )
            row_card.pack(fill="x", pady=4)

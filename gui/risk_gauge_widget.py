# =============================================================================
# gui/risk_gauge_widget.py
# FORENSEQUENCE - Animated Cyberpunk Semi-Circular Risk Gauge Canvas Widget
# =============================================================================

import math
import tkinter as tk
from typing import Optional

from gui.theme import (
    VOID,
    ABYSS,
    DEEP,
    STEEL,
    CYAN,
    PINK,
    PEACH,
    PLUM,
    PURPLE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
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
    risk_color,
    risk_label,
)


# =============================================================================
# DRAWING CONSTANTS
# =============================================================================

# The gauge arc spans 240 degrees total (from 150 deg to 390 deg clockwise)
_ARC_START_DEG  = 150.0   # canvas convention: 0=right, measured CCW from East
_ARC_TOTAL_DEG  = 240.0   # sweep span

# Tick geometry
_TICK_COUNT      = 11    # 0, 10, 20 ... 100  (11 major ticks)
_TICK_MAJOR_LEN  = 10
_TICK_MINOR_LEN  = 6
_TICK_MINOR_DIV  = 5     # 5 minor ticks between each major pair

# Glow simulation: draw arc twice with wider, dimmer under-arc
_GLOW_WIDTH  = 6
_ARC_WIDTH   = 3


def _score_to_angle_deg(score: float) -> float:
    """
    Map a risk score (0-100) to a canvas arc angle in degrees.

    Canvas arc angles in tkinter use the convention:
      - 0 degrees = East (3 o'clock)
      - angles increase counter-clockwise

    The gauge starts at 150 degrees (bottom-left) and sweeps 240 degrees
    counter-clockwise to 390 degrees (bottom-right), measured in standard
    math convention (CCW from East).  Tkinter's ``create_arc`` extent is
    expressed in the same CCW convention.

    Returns the EXTENT (negative value = CW sweep) to use as arc ``start``
    when combined with ``extent``.
    """
    # fraction of the full sweep
    fraction = max(0.0, min(1.0, score / 100.0))
    return fraction * _ARC_TOTAL_DEG


def _polar_to_xy(cx: float, cy: float, radius: float, angle_deg: float):
    """
    Convert polar coordinates (standard math: 0=East, CCW positive)
    to canvas (cx, cy) Cartesian coordinates.

    Canvas Y axis is flipped (positive = downward), so we negate sin.
    """
    rad = math.radians(angle_deg)
    x = cx + radius * math.cos(rad)
    y = cy - radius * math.sin(rad)
    return x, y


# =============================================================================
# WIDGET
# =============================================================================

class CyberpunkRiskGauge(tk.Canvas):
    """
    Animated, semi-circular Cyberpunk Risk Gauge drawn on a Tkinter Canvas.

    The gauge sweeps 240 degrees.  A glowing colored arc advances from the
    low end to the current score, and a needle pointer is drawn at the exact
    score angle.  All updates can be animated via smooth ``after()`` steps.

    Parameters
    ----------
    parent : tk.Misc
        Parent widget.
    size : int
        Pixel diameter of the gauge (canvas will be size x size//1.3 approx).
    score : int
        Initial score to display (0-100).
    compact : bool
        When True, suppresses tick labels and uses a smaller font, suitable
        for embedding in dashboard stat cards.
    bg : str
        Canvas background color (default: VOID).
    """

    def __init__(
        self,
        parent: tk.Misc,
        size: int = 220,
        score: int = 0,
        compact: bool = False,
        bg: str = VOID,
        **kwargs,
    ):
        # Canvas height is ~75% of size so gauge fits without dead vertical space
        canvas_h = int(size * 0.78)
        super().__init__(
            parent,
            width=size,
            height=canvas_h,
            bg=bg,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )

        self._size    = size
        self._compact = compact
        self._bg      = bg

        # Gauge geometry
        margin = size * 0.09
        self._cx = size / 2.0
        self._cy = size / 2.0 - margin * 0.4
        self._r_outer = size / 2.0 - margin         # outer arc radius
        self._r_inner = self._r_outer * 0.72        # inner arc for track
        self._r_needle = self._r_outer * 0.58       # needle length
        self._r_tick_outer = self._r_outer + 2
        self._r_tick_inner_maj = self._r_outer - _TICK_MAJOR_LEN
        self._r_tick_inner_min = self._r_outer - _TICK_MINOR_LEN

        # State
        self._current_score = 0
        self._target_score  = 0
        self._current_level = "LOW"
        self._anim_id: Optional[str] = None

        # Draw initial state
        self._draw_gauge(self._current_score)

        # Apply requested initial score
        if score != 0:
            self.set_score(score)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def set_score(
        self,
        score: int,
        level: Optional[str] = None,
        animate: bool = True,
    ) -> None:
        """
        Update the gauge to display the given risk score.

        Parameters
        ----------
        score : int
            New score (0-100).  Clamped automatically.
        level : str, optional
            Override risk level string ('LOW', 'MEDIUM', 'HIGH').  If None,
            the level is derived from the score using theme helpers.
        animate : bool
            If True, animate the needle and arc smoothly to the new value.
            If False, jump directly to the final state.
        """
        self._target_score = max(0, min(100, int(score)))
        self._current_level = level if level else risk_label(self._target_score)

        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

        if animate:
            self._animate_step()
        else:
            self._current_score = self._target_score
            self._draw_gauge(self._current_score)

    # -------------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------------

    def _animate_step(self) -> None:
        """Advance the gauge one animation frame toward the target score."""
        if not self.winfo_exists():
            return

        diff = self._target_score - self._current_score
        if abs(diff) < 1:
            self._current_score = self._target_score
            self._draw_gauge(self._current_score)
            return

        # Ease-out: move a fraction of the remaining distance each frame
        step = max(1.0, abs(diff) * 0.12)
        if diff > 0:
            self._current_score = min(self._target_score, self._current_score + step)
        else:
            self._current_score = max(self._target_score, self._current_score - step)

        self._draw_gauge(self._current_score)
        self._anim_id = self.after(16, self._animate_step)  # ~60 FPS

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def _draw_gauge(self, score: float) -> None:
        """Fully redraw the gauge canvas for the given score value."""
        self.delete("all")

        cx   = self._cx
        cy   = self._cy
        ro   = self._r_outer
        ri   = self._r_inner
        size = self._size

        # The arc bounding box
        x0 = cx - ro
        y0 = cy - ro
        x1 = cx + ro
        y1 = cy + ro

        arc_color = risk_color(int(score))

        # ------------------------------------------------------------------
        # 1. Background track arc (full 240-degree dark ring)
        # ------------------------------------------------------------------
        self.create_arc(
            x0, y0, x1, y1,
            start=_ARC_START_DEG,
            extent=_ARC_TOTAL_DEG,
            style="arc",
            outline=DEEP,
            width=_ARC_WIDTH + _GLOW_WIDTH,
        )
        self.create_arc(
            x0, y0, x1, y1,
            start=_ARC_START_DEG,
            extent=_ARC_TOTAL_DEG,
            style="arc",
            outline=STEEL,
            width=1,
        )

        # ------------------------------------------------------------------
        # 2. Active arc (glow underlay then crisp top arc)
        # ------------------------------------------------------------------
        active_extent = _score_to_angle_deg(score / 100.0 * 100.0)

        if active_extent > 0.5:
            # Glow layer (wider, dimmer)
            glow_color = self._hex_dim(arc_color, 0.28)
            self.create_arc(
                x0, y0, x1, y1,
                start=_ARC_START_DEG,
                extent=active_extent,
                style="arc",
                outline=glow_color,
                width=_ARC_WIDTH + _GLOW_WIDTH + 4,
            )
            # Crisp active arc
            self.create_arc(
                x0, y0, x1, y1,
                start=_ARC_START_DEG,
                extent=active_extent,
                style="arc",
                outline=arc_color,
                width=_ARC_WIDTH,
            )

        # ------------------------------------------------------------------
        # 3. Tick marks
        # ------------------------------------------------------------------
        self._draw_ticks(cx, cy, arc_color, score)

        # ------------------------------------------------------------------
        # 4. Center donut hole (decorative filled circle)
        # ------------------------------------------------------------------
        donut_r = ri * 0.80
        self.create_oval(
            cx - donut_r, cy - donut_r,
            cx + donut_r, cy + donut_r,
            fill=ABYSS,
            outline=PLUM,
            width=1,
        )
        # Inner ring accent
        inner_ring_r = donut_r * 0.88
        self.create_oval(
            cx - inner_ring_r, cy - inner_ring_r,
            cx + inner_ring_r, cy + inner_ring_r,
            fill=VOID,
            outline=DEEP,
            width=1,
        )

        # ------------------------------------------------------------------
        # 5. Needle
        # ------------------------------------------------------------------
        self._draw_needle(cx, cy, score, arc_color)

        # ------------------------------------------------------------------
        # 6. Center text: numeric score + level label
        # ------------------------------------------------------------------
        self._draw_center_labels(cx, cy, score, arc_color)

    def _draw_ticks(self, cx: float, cy: float, active_color: str, score: float) -> None:
        """Draw major and minor tick marks around the gauge perimeter."""
        total_minor = _TICK_COUNT * _TICK_MINOR_DIV  # total minor subdivisions

        for tick_i in range(total_minor + 1):
            fraction = tick_i / total_minor
            angle = _ARC_START_DEG + fraction * _ARC_TOTAL_DEG

            is_major = (tick_i % _TICK_MINOR_DIV == 0)
            tick_len = _TICK_MAJOR_LEN if is_major else _TICK_MINOR_LEN

            r_outer = self._r_tick_outer
            r_inner = self._r_tick_inner_maj if is_major else self._r_tick_inner_min

            ox, oy = _polar_to_xy(cx, cy, r_outer, angle)
            ix, iy = _polar_to_xy(cx, cy, r_inner, angle)

            # Color: active sector gets arc color, inactive is muted
            tick_score_val = fraction * 100.0
            if tick_score_val <= score:
                tick_color = active_color
                tick_width = 2 if is_major else 1
            else:
                tick_color = STEEL
                tick_width = 1

            self.create_line(ox, oy, ix, iy, fill=tick_color, width=tick_width)

            # Tick labels for major ticks (skip in compact mode)
            if is_major and not self._compact:
                tick_val = int(fraction * 100)
                label_r = self._r_tick_outer + (14 if tick_val in (0, 100) else 12)
                lx, ly = _polar_to_xy(cx, cy, label_r, angle)
                self.create_text(
                    lx, ly,
                    text=str(tick_val),
                    fill=TEXT_MUTED,
                    font=(FONT_MONO_FALLBACK, FS_XS),
                    anchor="center",
                )

    def _draw_needle(self, cx: float, cy: float, score: float, color: str) -> None:
        """Draw the needle pointer aligned to the current score angle."""
        fraction = max(0.0, min(1.0, score / 100.0))
        angle = _ARC_START_DEG + fraction * _ARC_TOTAL_DEG

        # Needle tip
        tip_x, tip_y = _polar_to_xy(cx, cy, self._r_needle, angle)

        # Needle base: small offset in opposite direction
        base_r = self._r_inner * 0.22
        base_angle = angle + 180.0
        base_x, base_y = _polar_to_xy(cx, cy, base_r, base_angle)

        # Glow shadow behind needle
        glow_col = self._hex_dim(color, 0.4)
        self.create_line(
            base_x, base_y, tip_x, tip_y,
            fill=glow_col,
            width=4,
            capstyle="round",
        )
        # Main needle line
        self.create_line(
            base_x, base_y, tip_x, tip_y,
            fill=color,
            width=2,
            capstyle="round",
        )

        # Pivot dot
        piv_r = self._r_inner * 0.10
        self.create_oval(
            cx - piv_r, cy - piv_r,
            cx + piv_r, cy + piv_r,
            fill=color,
            outline=ABYSS,
            width=1,
        )

    def _draw_center_labels(
        self, cx: float, cy: float, score: float, color: str
    ) -> None:
        """Render the numeric score and risk band label in the gauge center."""
        level_text = risk_label(int(score))

        if self._compact:
            score_font_size = max(FS_LG, int(self._size * 0.13))
            label_font_size = FS_XS
            y_offset_score = -2
            y_offset_label = score_font_size * 0.9
        else:
            score_font_size = max(FS_XL, int(self._size * 0.15))
            label_font_size = FS_SM
            y_offset_score = -4
            y_offset_label = score_font_size * 0.95

        # Main score number
        self.create_text(
            cx,
            cy + y_offset_score,
            text=f"{int(score)}",
            fill=color,
            font=(FONT_DISPLAY, score_font_size, "bold"),
            anchor="center",
        )

        # Level text below score
        self.create_text(
            cx,
            cy + y_offset_label,
            text=f"{level_text} RISK",
            fill=TEXT_SECONDARY,
            font=(FONT_FALLBACK, label_font_size, "bold"),
            anchor="center",
        )

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _hex_dim(hex_color: str, alpha: float) -> str:
        """
        Blend a hex color toward black by the given alpha factor (0.0-1.0).
        Used to simulate a glow effect without tkinter alpha compositing.
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * alpha)
        g = int(g * alpha)
        b = int(b * alpha)
        return f"#{r:02x}{g:02x}{b:02x}"


# =============================================================================
# STANDALONE TEST / PREVIEW
# =============================================================================

if __name__ == "__main__":
    import ttkbootstrap as ttk
    from gui.theme import apply_theme

    root = ttk.Window()
    apply_theme(root)
    root.title("FORENSEQUENCE - Risk Gauge Preview")
    root.configure(bg=VOID)

    frame = tk.Frame(root, bg=VOID, padx=20, pady=20)
    frame.pack()

    tk.Label(
        frame,
        text="STANDARD GAUGE (size=240)",
        fg=TEXT_MUTED,
        bg=VOID,
        font=(FONT_FALLBACK, FS_XS, "bold"),
    ).pack(pady=(0, 4))

    gauge_full = CyberpunkRiskGauge(frame, size=240, score=0, compact=False, bg=VOID)
    gauge_full.pack()

    tk.Label(
        frame,
        text="COMPACT GAUGE (size=140)",
        fg=TEXT_MUTED,
        bg=VOID,
        font=(FONT_FALLBACK, FS_XS, "bold"),
    ).pack(pady=(12, 4))

    gauge_compact = CyberpunkRiskGauge(frame, size=140, score=0, compact=True, bg=DEEP)
    gauge_compact.pack()

    def _animate_demo():
        for score, level in [(25, "LOW"), (55, "MEDIUM"), (88, "HIGH"), (0, "LOW")]:
            root.after(
                ([(25, "LOW"), (55, "MEDIUM"), (88, "HIGH"), (0, "LOW")].index((score, level)) + 1) * 2000,
                lambda s=score, lv=level: (
                    gauge_full.set_score(s, lv),
                    gauge_compact.set_score(s, lv),
                ),
            )

    _animate_demo()
    root.mainloop()

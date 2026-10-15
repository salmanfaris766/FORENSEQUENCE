# =============================================================================
# gui/theme.py
# FORENSEQUENCE - Premium SOC Workstation Design System
# =============================================================================

from __future__ import annotations

import math
import tkinter as tk
from typing import Optional, Callable
from PIL import Image, ImageDraw, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.style import Style


# =============================================================================
# MINIMALIST IOS LIQUID GLASSMORPHISM PALETTE
# =============================================================================

BG_DEEP           = "#020505"  # Pure deep obsidian canvas
CARD_BG           = "#071413"  # Translucent squircle card surface
TEXT_MAIN         = "#FFFFFF"  # High-contrast primary typographic tone
TEXT_MUTED        = "#507571"  # Sophisticated muted tertiary tone

# Semantic Severity Scale (RED strictly reserved for CRITICAL; Mint/Teal/Cyan for all else)
CRITICAL          = "#FF2A55"  # iOS Vivid Neon Red
HIGH              = "#0A524C"  # Deep Emerald Teal
MEDIUM            = "#0E8A80"  # Vibrant Mid Teal
LOW               = "#2DE3C8"  # Mint Cyan
INFORMATIONAL     = "#507571"
CHART_GRID        = "#0B1E1C"

# Liquid Accents & Glazes
CYAN              = "#00F0FF"  # Electric iOS Cyan
CYAN_GLOW         = "#5EEAD4"
CYAN_NEON         = "#00F0FF"
MINT              = "#2DE3C8"  # Mint Accent
TEAL              = "#0E8A80"  # Deep Oceanic Teal
TEAL_MID          = "#0E8A80"
TEAL_DARK         = "#0A524C"
TEAL_DEEP         = "#062220"
TEAL_BG           = "#0A2825"
TEAL_DEEP_BG      = "#051A18"

# SOC Surface & Border Tokens (backward-compatible mappings)
APP_BG            = BG_DEEP
BG_SECONDARY      = "#040A09"
SIDEBAR_BG        = CARD_BG
PANEL_BG          = CARD_BG
PANEL_ELEVATED    = "#0A1B19"
PANEL_HOVER       = "#0E2623"

TEXT_PRIMARY      = TEXT_MAIN
TEXT_SECONDARY    = "#9AB4B0"
TEXT_DISABLED     = "#354E4A"

BORDER            = "#122A27"
BORDER_SECONDARY  = "#1B3B37"
BORDER_HOVER      = "#285852"

# Legacy Color Aliases (for backward compatibility across existing frames)
VOID              = APP_BG
ABYSS             = BG_SECONDARY
DEEP              = PANEL_BG
STEEL             = BORDER
ICE               = CYAN_GLOW
PINK              = CRITICAL
MAGENTA           = CRITICAL
PURPLE            = TEAL_MID
PLUM              = BORDER
PEACH             = HIGH
RISK_LOW          = LOW
RISK_MED          = MEDIUM
RISK_HIGH         = HIGH


# =============================================================================
# TYPOGRAPHY
# =============================================================================

FONT_DISPLAY       = "Orbitron"
FONT_UI            = "Segoe UI"
FONT_MONO          = "JetBrains Mono"
FONT_FALLBACK      = "Segoe UI"
FONT_MONO_FALLBACK = "Consolas"

# Font size scale (pt)
FS_XS   = 8
FS_SM   = 10
FS_BASE = 11
FS_MD   = 12
FS_LG   = 14
FS_XL   = 18
FS_2XL  = 24
FS_3XL  = 32

# Convenience tuples: (family, size, weight)
FONT_HEADING    = (FONT_FALLBACK, FS_2XL,  "bold")
FONT_SUBHEADING = (FONT_FALLBACK, FS_XL,   "bold")
FONT_SECTION    = (FONT_FALLBACK, FS_MD,   "bold")
FONT_BODY       = (FONT_FALLBACK, FS_BASE, "normal")
FONT_SMALL      = (FONT_FALLBACK, FS_SM,   "normal")
FONT_MONO_BODY  = (FONT_MONO_FALLBACK, FS_BASE, "normal")
FONT_MONO_SM    = (FONT_MONO_FALLBACK, FS_SM,   "normal")


# =============================================================================
# SPACING SCALE (pixels)
# =============================================================================

SP_1 = 4
SP_2 = 8
SP_3 = 12
SP_4 = 16
SP_6 = 24
SP_8 = 32
SP_12 = 48


# =============================================================================
# RADIUS SCALE (pixels)
# =============================================================================

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12


# =============================================================================
# APPLY THEME
# Configure ttkbootstrap Style with SOC Workstation tokens.
# =============================================================================

def apply_theme(app: ttk.Window) -> None:
    """
    Apply the FORENSEQUENCE SOC Workstation theme to a ttkbootstrap Window.
    Configures tk/ttk widget styles globally so every widget inherits correctly.
    """
    style = app.style

    # -- Root window background --
    app.configure(background=APP_BG)

    # -- TFrame --
    style.configure("TFrame", background=APP_BG, borderwidth=0, relief="flat")
    style.configure("Card.TFrame", background=PANEL_BG, borderwidth=0, relief="flat")
    style.configure("Panel.TFrame", background=SIDEBAR_BG, borderwidth=0, relief="flat")

    # -- TLabel --
    style.configure("TLabel", background=APP_BG, foreground=TEXT_PRIMARY, font=FONT_BODY, borderwidth=0)
    style.configure("Card.TLabel", background=PANEL_BG, foreground=TEXT_PRIMARY, font=FONT_BODY, borderwidth=0)
    style.configure("Panel.TLabel", background=SIDEBAR_BG, foreground=TEXT_PRIMARY, font=FONT_BODY, borderwidth=0)
    style.configure("Secondary.TLabel", background=APP_BG, foreground=TEXT_SECONDARY, font=FONT_BODY, borderwidth=0)
    style.configure("Muted.TLabel", background=APP_BG, foreground=TEXT_MUTED, font=FONT_SMALL, borderwidth=0)
    style.configure("Heading.TLabel", background=APP_BG, foreground=TEXT_PRIMARY, font=FONT_HEADING, borderwidth=0)
    style.configure("Section.TLabel", background=APP_BG, foreground=CYAN, font=FONT_SECTION, borderwidth=0)

    # -- TButton --
    style.configure(
        "TButton",
        background=PANEL_ELEVATED,
        foreground=TEXT_PRIMARY,
        borderwidth=1,
        bordercolor=BORDER,
        focuscolor=MINT,
        font=FONT_BODY,
    )
    style.map(
        "TButton",
        background=[("active", PANEL_HOVER)],
        foreground=[("active", MINT)],
    )

    # -- TEntry --
    style.configure(
        "TEntry",
        fieldbackground=PANEL_BG,
        foreground=TEXT_PRIMARY,
        insertcolor=CYAN,
        borderwidth=1,
        bordercolor=BORDER,
        relief="flat",
        font=FONT_BODY,
    )
    style.map(
        "TEntry",
        fieldbackground=[("focus", PANEL_BG)],
        bordercolor=[("focus", CYAN)],
    )

    # -- Treeview --
    style.configure(
        "Treeview",
        background=PANEL_BG,
        fieldbackground=PANEL_BG,
        foreground=TEXT_PRIMARY,
        rowheight=28,
        borderwidth=0,
        highlightthickness=0,
        font=FONT_BODY,
    )
    style.configure(
        "Treeview.Heading",
        background=PANEL_ELEVATED,
        foreground=MINT,
        borderwidth=0,
        relief="flat",
        font=FONT_SECTION,
    )
    style.map(
        "Treeview",
        background=[("selected", PANEL_HOVER)],
        foreground=[("selected", MINT)],
    )

    # -- TScrollbar --
    style.configure(
        "TScrollbar",
        background=PANEL_BG,
        troughcolor=APP_BG,
        arrowcolor=TEXT_MUTED,
        borderwidth=0,
    )
    style.map(
        "TScrollbar",
        background=[("active", TEAL_MID)],
    )

    # -- TNotebook --
    style.configure(
        "TNotebook",
        background=APP_BG,
        borderwidth=0,
        tabmargins=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=BG_SECONDARY,
        foreground=TEXT_SECONDARY,
        padding=(SP_4, SP_2),
        font=FONT_BODY,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", PANEL_BG)],
        foreground=[("selected", MINT)],
    )

    # -- TCombobox --
    style.configure(
        "TCombobox",
        fieldbackground=PANEL_BG,
        background=PANEL_BG,
        foreground=TEXT_PRIMARY,
        arrowcolor=CYAN,
        selectbackground=PANEL_HOVER,
        selectforeground=MINT,
        font=FONT_BODY,
    )

    # -- TCheckbutton / TRadiobutton --
    style.configure("TCheckbutton", background=APP_BG, foreground=TEXT_PRIMARY, font=FONT_BODY)
    style.configure("TRadiobutton", background=APP_BG, foreground=TEXT_PRIMARY, font=FONT_BODY)

    # -- TProgressbar --
    style.configure("TProgressbar", background=MINT, troughcolor=PANEL_BG, borderwidth=0)


# =============================================================================
# RISK HELPERS
# =============================================================================

def risk_color(score: int) -> str:
    """
    Return the SOC severity color corresponding to a 0-100 forensic risk score.
    0-33   -> LOW (MINT #2DE3C8)
    34-66  -> MEDIUM (MID TEAL #18A999)
    67-84  -> HIGH (DEEP TEAL #0E8A80)
    85-100 -> CRITICAL (RED #FF5B5B)
    """
    if score <= 33:
        return LOW
    elif score <= 66:
        return MEDIUM
    elif score <= 84:
        return HIGH
    else:
        return CRITICAL


def risk_label(score: int) -> str:
    """
    Return the text severity label for a 0-100 forensic risk score.
    """
    if score <= 33:
        return "LOW"
    elif score <= 66:
        return "MEDIUM"
    elif score <= 84:
        return "HIGH"
    else:
        return "CRITICAL"


# =============================================================================
# INTERNAL DRAWING HELPERS
# =============================================================================

def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert a #RRGGBB hex string to an (r, g, b) integer tuple."""
    if not hex_color:
        return (0, 0, 0)
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple) -> str:
    """Convert an (r, g, b) integer tuple to a #RRGGBB hex string."""
    return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"


def _hex_lerp(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex color strings."""
    if not c1:
        return c2 or ""
    if not c2:
        return c1 or ""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    t = max(0.0, min(1.0, t))
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

_lerp_color = _hex_lerp


def draw_squircle(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float = 24,
    **kwargs,
) -> int:
    """
    Draw a mathematically smooth rounded rectangle / squircle natively on a Canvas.
    Uses multi-point corner arc sampling with canvas.create_polygon(..., smooth=True).
    Returns the canvas item ID of the polygon.
    """
    w = max(0.0, float(x2 - x1))
    h = max(0.0, float(y2 - y1))
    r = min(float(radius), w / 2.0, h / 2.0)
    if r <= 0:
        return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)

    points = []
    steps = 6

    # Top-right corner arc (-pi/2 to 0)
    cx, cy = x2 - r, y1 + r
    for i in range(steps + 1):
        ang = -math.pi / 2.0 + (math.pi / 2.0) * (i / steps)
        points.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])

    # Bottom-right corner arc (0 to pi/2)
    cx, cy = x2 - r, y2 - r
    for i in range(steps + 1):
        ang = (math.pi / 2.0) * (i / steps)
        points.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])

    # Bottom-left corner arc (pi/2 to pi)
    cx, cy = x1 + r, y2 - r
    for i in range(steps + 1):
        ang = math.pi / 2.0 + (math.pi / 2.0) * (i / steps)
        points.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])

    # Top-left corner arc (pi to 3*pi/2)
    cx, cy = x1 + r, y1 + r
    for i in range(steps + 1):
        ang = math.pi + (math.pi / 2.0) * (i / steps)
        points.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])

    return canvas.create_polygon(points, smooth=True, **kwargs)


def _draw_rounded_rect(
    canvas: tk.Canvas,
    x1: int, y1: int,
    x2: int, y2: int,
    radius: int,
    **kwargs,
) -> int:
    """
    Draw a filled rounded rectangle / squircle on a Canvas.
    Returns the canvas item ID of the polygon.
    """
    return draw_squircle(canvas, x1, y1, x2, y2, radius=radius, **kwargs)


class LiquidButton(tk.Canvas):
    """
    A Canvas-based pill-shaped button with iOS Liquid Glassmorphism styling.
    Features:
    - Native squircle / pill vector drawing via draw_squircle
    - Smooth 150ms color interpolation on <Enter> and <Leave> via after()
    - Crisp vector typography, 60fps performance, no PIL resizing lag
    """

    def __init__(
        self,
        parent,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        width: int = 140,
        height: int = 38,
        radius: Optional[int] = None,
        bg: str = BG_DEEP,
        fill_color: str = TEAL,
        hover_color: str = CYAN,
        text_color: str = TEXT_MAIN,
        hover_text_color: str = BG_DEEP,
        border_color: Optional[str] = BORDER_SECONDARY,
        border_width: int = 1,
        font: tuple = (FONT_FALLBACK, 10, "bold"),
        cursor: str = "hand2",
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor=cursor,
            **kwargs,
        )
        self.text = text
        self.command = command
        self.radius = radius if radius is not None else height // 2
        self.bg_color = bg
        self.fill_color = fill_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hover_text_color = hover_text_color
        self.border_color = border_color
        self.border_width = border_width
        self.font = font

        self._curr_w = width
        self._curr_h = height
        self._current_fill = fill_color
        self._current_text = text_color
        self._is_hovered = False
        self._anim_id: Optional[str] = None
        self._total_steps = 6  # 6 frames * 25ms = 150ms

        self._redraw()

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_configure(self, event):
        if event.width > 2 and event.height > 2:
            if event.width != self._curr_w or event.height != self._curr_h:
                self._curr_w = event.width
                self._curr_h = event.height
                self._redraw()

    def _redraw(self):
        self.delete("all")
        pad = max(1, self.border_width)
        r = min(self.radius, (self._curr_h - pad * 2) // 2, (self._curr_w - pad * 2) // 2)
        draw_squircle(
            self,
            pad,
            pad,
            self._curr_w - pad,
            self._curr_h - pad,
            radius=r,
            fill=self._current_fill,
            outline=self.border_color or "",
            width=self.border_width,
            tags="pill",
        )
        self.create_text(
            self._curr_w // 2,
            self._curr_h // 2,
            text=self.text,
            fill=self._current_text,
            font=self.font,
            tags="label",
        )

    def _on_enter(self, event=None):
        if not self._is_hovered:
            self._is_hovered = True
            self._start_tween(target_hover=True)

    def _on_leave(self, event=None):
        if event is not None:
            if 0 <= event.x < self._curr_w and 0 <= event.y < self._curr_h:
                return
        if self._is_hovered:
            self._is_hovered = False
            self._start_tween(target_hover=False)

    def _start_tween(self, target_hover: bool):
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None

        def _step(i: int):
            if not self.winfo_exists():
                return
            t = i / float(self._total_steps)
            ease_t = 1.0 - (1.0 - t) ** 3
            if target_hover:
                self._current_fill = _lerp_color(self.fill_color, self.hover_color, ease_t)
                self._current_text = _lerp_color(self.text_color, self.hover_text_color, ease_t)
            else:
                self._current_fill = _lerp_color(self.hover_color, self.fill_color, ease_t)
                self._current_text = _lerp_color(self.hover_text_color, self.text_color, ease_t)

            self.itemconfig("pill", fill=self._current_fill)
            self.itemconfig("label", fill=self._current_text)

            if i < self._total_steps:
                self._anim_id = self.after(25, lambda: _step(i + 1))
            else:
                self._anim_id = None

        _step(1)

    def _on_click(self, event=None):
        if self.command:
            self.command()

    def set_text(self, text: str):
        self.text = text
        self.itemconfig("label", text=text)

    def set_fill(self, fill_color: str, hover_color: Optional[str] = None):
        self.fill_color = fill_color
        if hover_color:
            self.hover_color = hover_color
        self._current_fill = fill_color
        self.itemconfig("pill", fill=self._current_fill)


def _draw_glow_border(
    canvas: tk.Canvas,
    x1: int, y1: int,
    x2: int, y2: int,
    radius: int,
    glow_color: str,
    layers: int = 2,
    **kwargs,
) -> None:
    """Draw subtle border glow outline around panel perimeter."""
    r, g, b = _hex_to_rgb(glow_color)
    for i in range(layers, 0, -1):
        spread = i
        factor = (layers - i + 1) / (layers + 2)
        vr, vg, vb = _hex_to_rgb(APP_BG)
        br = int(r * factor + vr * (1 - factor))
        bg_ = int(g * factor + vg * (1 - factor))
        bb = int(b * factor + vb * (1 - factor))
        blended = f"#{br:02x}{bg_:02x}{bb:02x}"
        _draw_rounded_rect(
            canvas,
            x1 - spread, y1 - spread,
            x2 + spread, y2 + spread,
            radius + spread,
            fill="",
            outline=blended,
            width=1,
            **kwargs,
        )


# =============================================================================
# SOC WORKSTATION UI PRIMITIVE FACTORIES
# =============================================================================

def create_liquid_squircle(
    parent,
    width: Optional[int] = None,
    height: Optional[int] = None,
    radius: int = 24,
    alpha: int = 40,
    tint: str = "#14B8A6",
    border_color: Optional[str] = None,
    border_width: int = 1,
    **kwargs,
) -> tk.Canvas:
    """
    Create a PIL-based 'Liquid Squircle' translucent glass card.
    Uses Pillow to render anti-aliased translucent rounded rectangles with a subtle teal tint,
    placing the image on a Canvas and offering smooth 150ms alpha hover transitions.
    Includes an .inner_frame container for child widgets.
    """
    if "fill_color" in kwargs and kwargs["fill_color"]:
        tint = kwargs["fill_color"]
    if "border_color" in kwargs and kwargs["border_color"]:
        border_color = kwargs["border_color"]
    if border_color is None:
        border_color = "#22D3C5"

    init_w = width if width is not None and width > 0 else 400
    init_h = height if height is not None and height > 0 else 200

    canvas_bg = _get_parent_bg(parent)
    canvas = tk.Canvas(
        parent,
        width=init_w,
        height=init_h,
        bg=canvas_bg,
        highlightthickness=0,
        bd=0,
    )

    pad = 4
    inner = ttk.Frame(canvas, style="Card.TFrame")
    inner._custom_bg = PANEL_BG
    canvas.inner_frame = inner

    win_id = canvas.create_window(
        init_w // 2, init_h // 2,
        window=inner,
        width=max(1, init_w - pad * 2),
        height=max(1, init_h - pad * 2),
    )

    canvas._photo_frames = []
    canvas._current_step = 0
    canvas._anim_id = None
    canvas._img_item = None
    last_dims = [init_w, init_h]

    def _render_frames(w: int, h: int):
        if w <= pad * 2 or h <= pad * 2:
            return
        base_a = max(5, min(250, alpha))
        hover_a = min(255, int(base_a * 1.6) + 15)
        alpha_steps = [int(base_a + (hover_a - base_a) * (i / 4.0)) for i in range(5)]

        frames = []
        scale = 2
        sw, sh, sr = w * scale, h * scale, radius * scale
        tr, tg, tb = _hex_to_rgb(tint)
        br, bg_, bb = _hex_to_rgb(border_color)

        for a in alpha_steps:
            img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle(
                [1 * scale, 1 * scale, sw - 1 * scale, sh - 1 * scale],
                radius=sr,
                fill=(tr, tg, tb, a),
                outline=None,
            )
            outline_a = min(255, int(a * 1.3) + 30)
            draw.rounded_rectangle(
                [1 * scale, 1 * scale, sw - 1 * scale, sh - 1 * scale],
                radius=sr,
                fill=None,
                outline=(br, bg_, bb, outline_a),
                width=max(1, border_width * scale),
            )
            res = img.resize((w, h), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(res))

        canvas._photo_frames = frames
        if canvas._img_item is None:
            canvas._img_item = canvas.create_image(0, 0, image=frames[canvas._current_step], anchor="nw")
            canvas.tag_lower(canvas._img_item)
        else:
            canvas.itemconfig(canvas._img_item, image=frames[canvas._current_step])

        canvas.coords(win_id, w // 2, h // 2)
        canvas.itemconfigure(
            win_id,
            width=max(1, w - pad * 2),
            height=max(1, h - pad * 2),
        )

    _render_frames(init_w, init_h)

    def _step_anim(target_step: int):
        if not canvas.winfo_exists():
            return
        if canvas._current_step == target_step:
            canvas._anim_id = None
            return
        if canvas._current_step < target_step:
            canvas._current_step += 1
        else:
            canvas._current_step -= 1
        if canvas._photo_frames and 0 <= canvas._current_step < len(canvas._photo_frames):
            canvas.itemconfig(canvas._img_item, image=canvas._photo_frames[canvas._current_step])
        canvas._anim_id = canvas.after(30, lambda: _step_anim(target_step))

    def on_enter(_):
        if canvas._anim_id is not None:
            canvas.after_cancel(canvas._anim_id)
            canvas._anim_id = None
        _step_anim(4)

    def on_leave(_):
        if canvas._anim_id is not None:
            canvas.after_cancel(canvas._anim_id)
            canvas._anim_id = None
        _step_anim(0)

    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)

    def _on_canvas_configure(event):
        if event.widget == canvas:
            if event.width != last_dims[0] or event.height != last_dims[1]:
                last_dims[0] = event.width
                last_dims[1] = event.height
                _render_frames(event.width, event.height)

    canvas.bind("<Configure>", _on_canvas_configure)
    return canvas


def create_soc_panel(
    parent,
    width: Optional[int] = None,
    height: Optional[int] = None,
    bg: str = PANEL_BG,
    border_color: str = BORDER,
    radius: int = RADIUS_SM,
    **kwargs,
) -> tk.Canvas:
    """
    Create a SOC workstation panel widget with rounded borders and inner frame.
    Supports dynamic resizing via <Configure> and backward-compatible parameters.
    """
    if "fill_color" in kwargs:
        bg = kwargs["fill_color"]
    if "border_color" in kwargs:
        border_color = kwargs["border_color"]

    init_w = width if width is not None and width > 0 else 400
    init_h = height if height is not None and height > 0 else 200

    canvas_bg = _get_parent_bg(parent)
    canvas = tk.Canvas(
        parent,
        width=init_w,
        height=init_h,
        bg=canvas_bg,
        highlightthickness=0,
        bd=0,
    )

    pad = 2

    inner = ttk.Frame(canvas, style="Card.TFrame")
    inner._custom_bg = bg
    canvas.inner_frame = inner

    win_id = canvas.create_window(
        init_w // 2, init_h // 2,
        window=inner,
        width=max(1, init_w - (pad * 2) - 2),
        height=max(1, init_h - (pad * 2) - 2),
    )

    def _render(w: int, h: int):
        canvas.delete("panel_shape")
        if w <= (pad * 2) + 2 or h <= (pad * 2) + 2:
            return

        # Background fill
        _draw_rounded_rect(
            canvas,
            pad, pad,
            w - pad, h - pad,
            radius,
            fill=bg,
            outline="",
            tags="panel_shape",
        )
        # Hairline border outline
        _draw_rounded_rect(
            canvas,
            pad, pad,
            w - pad, h - pad,
            radius,
            fill="",
            outline=border_color,
            width=1,
            tags="panel_shape",
        )
        canvas.tag_lower("panel_shape")
        canvas.coords(win_id, w // 2, h // 2)
        canvas.itemconfigure(
            win_id,
            width=max(1, w - (pad * 2) - 2),
            height=max(1, h - (pad * 2) - 2),
        )

    _render(init_w, init_h)

    last_dims = [init_w, init_h]

    def _on_canvas_configure(event):
        if event.widget == canvas:
            if event.width != last_dims[0] or event.height != last_dims[1]:
                last_dims[0] = event.width
                last_dims[1] = event.height
                _render(event.width, event.height)

    canvas.bind("<Configure>", _on_canvas_configure)
    return canvas


def create_soc_button(
    parent,
    text: str,
    command=None,
    variant: str = "primary",
    bg: Optional[str] = None,
) -> tk.Canvas:
    """
    Create a Canvas-based SOC workstation button with rounded squircle styling
    and smooth 150ms color tweens on hover.

    Variants:
      primary   - MINT (#2DE3C8) fill, APP_BG text
      secondary - PANEL_ELEVATED (#0D1D1B) fill, BORDER_SECONDARY border, TEXT_PRIMARY text
      danger    - PANEL_BG fill, CRITICAL (#FF5B5B) border + text
      ghost     - Transparent fill, TEXT_MUTED text, no border
    """
    pad_x = SP_4 + 2
    pad_y = SP_2 + 2
    radius = RADIUS_MD + 2
    font_spec = (FONT_FALLBACK, FS_BASE, "bold")

    tmp = tk.Label(parent, text=text, font=font_spec)
    tmp.update_idletasks()
    tw = tmp.winfo_reqwidth()
    th = tmp.winfo_reqheight()
    tmp.destroy()

    btn_w = tw + pad_x * 2 + 8
    btn_h = th + pad_y * 2 + 4

    variant_styles = {
        "primary":   {"fill": MINT,           "border": MINT,             "fg": APP_BG,         "hover_fill": CYAN_NEON,    "hover_border": CYAN_NEON,    "hover_fg": APP_BG},
        "secondary": {"fill": PANEL_ELEVATED, "border": BORDER_SECONDARY, "fg": TEXT_PRIMARY,   "hover_fill": PANEL_HOVER,  "hover_border": BORDER_HOVER, "hover_fg": TEXT_PRIMARY},
        "danger":    {"fill": PANEL_BG,       "border": CRITICAL,         "fg": CRITICAL,       "hover_fill": PANEL_HOVER,  "hover_border": CRITICAL,     "hover_fg": CRITICAL},
        "ghost":     {"fill": "",             "border": "",               "fg": TEXT_MUTED,     "hover_fill": PANEL_HOVER,  "hover_border": BORDER,       "hover_fg": TEXT_PRIMARY},
    }
    s = variant_styles.get(variant, variant_styles["secondary"])

    canvas_bg = bg if bg is not None else _get_parent_bg(parent)
    canvas = tk.Canvas(
        parent,
        width=btn_w,
        height=btn_h,
        bg=canvas_bg,
        highlightthickness=0,
        bd=0,
        cursor="hand2",
    )

    def _draw(fill_col, border_col, text_col):
        canvas.delete("all")
        if fill_col or border_col:
            _draw_rounded_rect(
                canvas,
                1, 1, btn_w - 1, btn_h - 1,
                radius,
                fill=fill_col if fill_col else "",
                outline=border_col if border_col else "",
                width=1 if border_col else 0,
            )
        canvas.create_text(
            btn_w // 2, btn_h // 2,
            text=text,
            fill=text_col,
            font=font_spec,
            anchor="center",
        )

    _draw(s["fill"], s["border"], s["fg"])

    canvas._t = 0.0
    canvas._tween_id = None

    def _tween(target: float):
        if not canvas.winfo_exists():
            return
        step_delta = 0.2
        if abs(canvas._t - target) <= step_delta:
            canvas._t = target
            cur_fill = _hex_lerp(s["fill"], s["hover_fill"], canvas._t) if (s["fill"] or s["hover_fill"]) else ""
            cur_border = _hex_lerp(s["border"], s["hover_border"], canvas._t) if (s["border"] or s["hover_border"]) else ""
            cur_fg = _hex_lerp(s["fg"], s["hover_fg"], canvas._t)
            _draw(cur_fill, cur_border, cur_fg)
            canvas._tween_id = None
            return

        if canvas._t < target:
            canvas._t = min(target, canvas._t + step_delta)
        else:
            canvas._t = max(target, canvas._t - step_delta)

        cur_fill = _hex_lerp(s["fill"], s["hover_fill"], canvas._t) if (s["fill"] or s["hover_fill"]) else ""
        cur_border = _hex_lerp(s["border"], s["hover_border"], canvas._t) if (s["border"] or s["hover_border"]) else ""
        cur_fg = _hex_lerp(s["fg"], s["hover_fg"], canvas._t)
        _draw(cur_fill, cur_border, cur_fg)

        canvas._tween_id = canvas.after(30, lambda: _tween(target))

    def on_enter(_):
        if canvas._tween_id is not None:
            canvas.after_cancel(canvas._tween_id)
            canvas._tween_id = None
        _tween(1.0)

    def on_leave(_):
        if canvas._tween_id is not None:
            canvas.after_cancel(canvas._tween_id)
            canvas._tween_id = None
        _tween(0.0)

    def on_click(_):
        if command:
            command()

    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", on_click)

    return canvas


def create_soc_entry(parent, placeholder: str = "", width: Optional[int] = None) -> tk.Entry:
    """
    Return a tk.Entry styled with SOC Workstation tokens (PANEL_BG fill, BORDER outline, CYAN focus highlight).
    """
    entry_kwargs = {
        "bg": PANEL_BG,
        "fg": TEXT_PRIMARY,
        "insertbackground": CYAN,
        "relief": "flat",
        "bd": 0,
        "font": FONT_BODY,
        "highlightthickness": 1,
        "highlightbackground": BORDER,
        "highlightcolor": CYAN,
    }
    if width is not None:
        entry_kwargs["width"] = width

    entry = tk.Entry(parent, **entry_kwargs)

    if placeholder:
        entry.insert(0, placeholder)
        entry.config(fg=TEXT_MUTED)

        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg=TEXT_PRIMARY)

        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=TEXT_MUTED)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    return entry


def create_soc_badge(parent, text: str, color: str = TEAL, bg: Optional[str] = None) -> tk.Canvas:
    """
    Create a pill-shaped SOC status badge.
    """
    font_spec = (FONT_FALLBACK, FS_XS, "bold")
    tmp = tk.Label(parent, text=text, font=font_spec)
    tmp.update_idletasks()
    tw = tmp.winfo_reqwidth()
    th = tmp.winfo_reqheight()
    tmp.destroy()

    pad_x = 8
    pad_y = 2
    w = tw + pad_x * 2
    h = th + pad_y * 2
    radius = h // 2

    canvas_bg = bg if bg is not None else _get_parent_bg(parent)
    canvas = tk.Canvas(
        parent,
        width=w,
        height=h,
        bg=canvas_bg,
        highlightthickness=0,
        bd=0,
    )

    r, g, b = _hex_to_rgb(color)
    vr, vg, vb = _hex_to_rgb(APP_BG)
    factor = 0.15
    fr = int(r * factor + vr * (1 - factor))
    fg_ = int(g * factor + vg * (1 - factor))
    fb = int(b * factor + vb * (1 - factor))
    fill_tint = f"#{fr:02x}{fg_:02x}{fb:02x}"

    _draw_rounded_rect(canvas, 1, 1, w - 1, h - 1, radius, fill=fill_tint, outline=color, width=1)
    canvas.create_text(w // 2, h // 2, text=text, fill=color, font=font_spec, anchor="center")
    return canvas


def create_section_header(parent, text: str) -> ttk.Label:
    """
    Return an 11px uppercase tracked #7B918D label.
    """
    return ttk.Label(
        parent,
        text=text.upper(),
        foreground=TEXT_MUTED,
        background=_get_parent_bg(parent),
        font=(FONT_FALLBACK, FS_XS + 1, "bold"),
        anchor="w",
    )


def create_divider(parent, color: str = BORDER, orient: str = "horizontal") -> tk.Canvas:
    """
    Return a 1px horizontal or vertical separator line canvas widget.
    """
    if orient == "vertical":
        line = tk.Canvas(
            parent,
            width=1,
            bg=color,
            highlightthickness=0,
            bd=0,
        )
    else:
        line = tk.Canvas(
            parent,
            height=1,
            bg=color,
            highlightthickness=0,
            bd=0,
        )
    return line


# =============================================================================
# BACKWARD COMPATIBILITY FACTORY ALIASES
# =============================================================================

create_glass_frame  = create_soc_panel
create_neon_button  = create_soc_button
create_styled_entry = create_soc_entry
create_badge        = create_soc_badge


# =============================================================================
# INTERNAL UTILITIES
# =============================================================================

def _get_parent_bg(parent) -> str:
    """
    Attempt to retrieve the background color of a parent widget.
    Traverses parent hierarchy looking for _custom_bg or configured background.
    Falls back to APP_BG if unavailable.
    """
    curr = parent
    while curr is not None:
        if hasattr(curr, "_custom_bg") and curr._custom_bg:
            return curr._custom_bg
        try:
            bg = curr.cget("background")
            if bg and bg not in ("", "SystemButtonFace"):
                return bg
        except Exception:
            pass
        curr = getattr(curr, "master", None)
    return APP_BG


# =============================================================================
# TOOLTIP HELPER
# =============================================================================

class CyberpunkTooltip:
    """Floating tooltip with cyberpunk glass effect.

    The tooltip appears near the mouse cursor when the user hovers over a widget.
    It uses a semi-transparent dark background with a cyan hairline border.
    The tooltip is automatically destroyed when the mouse leaves the widget.
    """

    def __init__(self, widget: tk.Widget, text: str, *, delay: int = 400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None
        widget.bind("<Enter>", self._schedule_show)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule_show(self, event=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self) -> None:
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        if self.tooltip or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        self.tooltip.configure(bg=PANEL_BG)

        frame = tk.Frame(
            self.tooltip,
            bg=PANEL_BG,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=8,
            pady=4,
        )
        frame.pack()

        label = tk.Label(
            frame,
            text=self.text,
            bg=PANEL_BG,
            fg=TEXT_PRIMARY,
            font=FONT_SMALL,
            justify="left",
            wraplength=300,
        )
        label.pack()

    def _hide(self, event=None) -> None:
        self._cancel()
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def bind_tooltip(widget: tk.Widget, text: str, *, delay: int = 400) -> CyberpunkTooltip:
    """Convenience helper to attach a CyberpunkTooltip to any widget."""
    return CyberpunkTooltip(widget, text, delay=delay)

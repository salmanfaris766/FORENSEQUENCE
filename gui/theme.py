# =============================================================================
# gui/theme.py
# FORENSEQUENCE - Premium SOC Workstation Design System
# =============================================================================

from __future__ import annotations

import tkinter as tk
from typing import Optional
import ttkbootstrap as ttk
from ttkbootstrap.style import Style


# =============================================================================
# SOC COLOR TOKENS (Master Design Blueprint)
# =============================================================================

APP_BG            = "#030707"
BG_SECONDARY      = "#061211"
SIDEBAR_BG        = "#050C0B"
PANEL_BG          = "#0A1716"
PANEL_ELEVATED    = "#0D1D1B"
PANEL_HOVER       = "#122522"

CYAN_GLOW         = "#5EEAD4"
CYAN_NEON         = "#1FF2C9"
MINT              = "#2DE3C8"
CYAN              = "#22D3C5"
TEAL              = "#14B8A6"
TEAL_MID          = "#18A999"
TEAL_DARK         = "#0E8A80"
TEAL_DEEP         = "#0F6E66"
TEAL_BG           = "#126B6B"
TEAL_DEEP_BG      = "#0A3A3C"

TEXT_PRIMARY      = "#F2F7F6"
TEXT_SECONDARY    = "#B0C2BF"
TEXT_MUTED        = "#7B918D"
TEXT_DISABLED     = "#50635F"

BORDER            = "#1B302D"
BORDER_SECONDARY  = "#263F3B"
BORDER_HOVER      = "#35635C"

CRITICAL          = "#FF5B5B"
HIGH              = "#F2A65A"
MEDIUM            = "#E5D477"
LOW               = "#2DE3C8"
INFORMATIONAL     = "#7B918D"
CHART_GRID        = "#142724"

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
    34-66  -> MEDIUM (#E5D477)
    67-84  -> HIGH (#F2A65A)
    85-100 -> CRITICAL (#FF5B5B)
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
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _draw_rounded_rect(
    canvas: tk.Canvas,
    x1: int, y1: int,
    x2: int, y2: int,
    radius: int,
    **kwargs,
) -> int:
    """
    Draw a filled rounded rectangle on a Canvas.
    Returns the canvas item ID of the polygon.
    """
    r = radius
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


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
    Create a Canvas-based SOC workstation button.

    Variants:
      primary   - MINT (#2DE3C8) fill, APP_BG text
      secondary - PANEL_ELEVATED (#0D1D1B) fill, BORDER_SECONDARY border, TEXT_PRIMARY text
      danger    - PANEL_BG fill, CRITICAL (#FF5B5B) border + text
      ghost     - Transparent fill, TEXT_MUTED text, no border
    """
    pad_x = SP_4
    pad_y = SP_2
    radius = RADIUS_SM
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
        "ghost":     {"fill": "",             "border": "",               "fg": TEXT_MUTED,     "hover_fill": PANEL_HOVER,  "hover_border": "",           "hover_fg": TEXT_PRIMARY},
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

    def _draw(fill, border, fg):
        canvas.delete("all")
        if fill or border:
            _draw_rounded_rect(
                canvas,
                1, 1, btn_w - 1, btn_h - 1,
                radius,
                fill=fill if fill else "",
                outline=border if border else "",
                width=1 if border else 0,
            )
        canvas.create_text(
            btn_w // 2, btn_h // 2,
            text=text,
            fill=fg,
            font=font_spec,
            anchor="center",
        )

    _draw(s["fill"], s["border"], s["fg"])

    def on_enter(_):
        _draw(s["hover_fill"], s["hover_border"], s["hover_fg"])

    def on_leave(_):
        _draw(s["fill"], s["border"], s["fg"])

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

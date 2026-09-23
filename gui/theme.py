# =============================================================================
# gui/theme.py
# FORENSEQUENCE - Design System: Color Tokens, Typography, Spacing, Primitives
# =============================================================================

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.style import Style


# =============================================================================
# COLOR PALETTE
# =============================================================================

# -- Primary Bases --
VOID    = "#0B0F2B"   # App background (deepest layer)
ABYSS   = "#042142"   # Sidebar / secondary panels
DEEP    = "#153C6A"   # Card base
STEEL   = "#2475AC"   # Elevated surface

# -- Neon Accents --
CYAN    = "#00F0FF"   # Primary actions, active states, live indicators
ICE     = "#3DE0FC"   # Hover cyan
PINK    = "#FF5CA8"   # Alerts, high severity, live indicators
MAGENTA = "#E977F5"   # Selection / hover pink
PURPLE  = "#BC6CFF"   # AI reasoning highlights
PLUM    = "#733E85"   # Muted dividers
PEACH   = "#FFB86B"   # Medium risk / warnings

# -- Text --
TEXT_PRIMARY   = "#EAF6FF"
TEXT_SECONDARY = "#8FA3C7"
TEXT_MUTED     = "#5A6B8C"

# -- Risk Bands --
RISK_LOW  = CYAN
RISK_MED  = PEACH
RISK_HIGH = PINK


# =============================================================================
# TYPOGRAPHY
# =============================================================================

# Production-safe fallback families (swap when font files are added to assets/)
FONT_DISPLAY  = "Orbitron"          # Headings / branding - swap when available
FONT_UI       = "Rajdhani"          # UI labels / buttons - swap when available
FONT_MONO     = "JetBrains Mono"    # Log output / code - swap when available
FONT_FALLBACK = "Segoe UI"          # Safe Windows system fallback
FONT_MONO_FALLBACK = "Courier New"  # Safe monospace fallback

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

RADIUS_SM = 8
RADIUS_MD = 14
RADIUS_LG = 20


# =============================================================================
# APPLY THEME
# Configure ttkbootstrap Style with FORENSEQUENCE cyberpunk dark tokens.
# =============================================================================

def apply_theme(app: ttk.Window) -> None:
    """
    Apply the FORENSEQUENCE dark cyberpunk theme to a ttkbootstrap Window.
    Configures tk/ttk widget styles globally so every widget inherits correctly.
    """
    style = app.style

    # -- Root window background --
    app.configure(background=VOID)

    # -- TFrame --
    style.configure("TFrame", background=VOID)
    style.configure("Card.TFrame", background=DEEP)
    style.configure("Panel.TFrame", background=ABYSS)

    # -- TLabel --
    style.configure(
        "TLabel",
        background=VOID,
        foreground=TEXT_PRIMARY,
        font=FONT_BODY,
    )
    style.configure(
        "Secondary.TLabel",
        background=VOID,
        foreground=TEXT_SECONDARY,
        font=FONT_BODY,
    )
    style.configure(
        "Muted.TLabel",
        background=VOID,
        foreground=TEXT_MUTED,
        font=FONT_SMALL,
    )
    style.configure(
        "Heading.TLabel",
        background=VOID,
        foreground=TEXT_PRIMARY,
        font=FONT_HEADING,
    )
    style.configure(
        "Section.TLabel",
        background=VOID,
        foreground=CYAN,
        font=FONT_SECTION,
    )

    # -- TButton --
    style.configure(
        "TButton",
        background=DEEP,
        foreground=TEXT_PRIMARY,
        borderwidth=1,
        focuscolor=CYAN,
        font=FONT_BODY,
    )
    style.map(
        "TButton",
        background=[("active", STEEL)],
        foreground=[("active", CYAN)],
    )

    # -- TEntry --
    style.configure(
        "TEntry",
        fieldbackground=ABYSS,
        foreground=TEXT_PRIMARY,
        insertcolor=CYAN,
        borderwidth=1,
        relief="flat",
        font=FONT_BODY,
    )
    style.map(
        "TEntry",
        fieldbackground=[("focus", DEEP)],
        bordercolor=[("focus", CYAN)],
    )

    # -- Treeview --
    style.configure(
        "Treeview",
        background=ABYSS,
        fieldbackground=ABYSS,
        foreground=TEXT_PRIMARY,
        rowheight=28,
        borderwidth=0,
        font=FONT_BODY,
    )
    style.configure(
        "Treeview.Heading",
        background=DEEP,
        foreground=CYAN,
        borderwidth=0,
        font=FONT_SECTION,
    )
    style.map(
        "Treeview",
        background=[("selected", STEEL)],
        foreground=[("selected", CYAN)],
    )

    # -- TScrollbar --
    style.configure(
        "TScrollbar",
        background=ABYSS,
        troughcolor=VOID,
        arrowcolor=TEXT_MUTED,
        borderwidth=0,
    )
    style.map(
        "TScrollbar",
        background=[("active", PLUM)],
    )

    # -- TNotebook --
    style.configure(
        "TNotebook",
        background=VOID,
        borderwidth=0,
        tabmargins=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=ABYSS,
        foreground=TEXT_SECONDARY,
        padding=(SP_4, SP_2),
        font=FONT_BODY,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", DEEP)],
        foreground=[("selected", CYAN)],
    )

    # -- TCombobox --
    style.configure(
        "TCombobox",
        fieldbackground=ABYSS,
        background=ABYSS,
        foreground=TEXT_PRIMARY,
        arrowcolor=CYAN,
        selectbackground=DEEP,
        selectforeground=CYAN,
        font=FONT_BODY,
    )

    # -- TCheckbutton / TRadiobutton --
    style.configure(
        "TCheckbutton",
        background=VOID,
        foreground=TEXT_PRIMARY,
        font=FONT_BODY,
    )
    style.configure(
        "TRadiobutton",
        background=VOID,
        foreground=TEXT_PRIMARY,
        font=FONT_BODY,
    )

    # -- TProgressbar --
    style.configure(
        "TProgressbar",
        background=CYAN,
        troughcolor=ABYSS,
        borderwidth=0,
    )


# =============================================================================
# RISK HELPERS
# =============================================================================

def risk_color(score: int) -> str:
    """
    Return the neon accent color corresponding to a 0-100 forensic risk score.
    0-33  -> RISK_LOW  (CYAN)
    34-66 -> RISK_MED  (PEACH)
    67-100 -> RISK_HIGH (PINK)
    """
    if score <= 33:
        return RISK_LOW
    elif score <= 66:
        return RISK_MED
    else:
        return RISK_HIGH


def risk_label(score: int) -> str:
    """
    Return the text severity label for a 0-100 forensic risk score.
    """
    if score <= 33:
        return "LOW"
    elif score <= 66:
        return "MEDIUM"
    else:
        return "HIGH"


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
    layers: int = 3,
) -> None:
    """
    Simulate a neon outer glow by drawing progressively larger, more-transparent
    rounded rectangle outlines behind the main border.
    """
    r, g, b = _hex_to_rgb(glow_color)
    for i in range(layers, 0, -1):
        spread = i * 2
        # Approximate alpha dimming via color blending toward VOID background
        factor = (layers - i + 1) / (layers + 1)
        vr, vg, vb = _hex_to_rgb(VOID)
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
        )


# =============================================================================
# UI PRIMITIVE FACTORIES
# =============================================================================

def create_glass_frame(
    parent,
    width: int = 400,
    height: int = 200,
    radius: int = RADIUS_MD,
    border_color: str = CYAN,
    fill_color: str = DEEP,
    alpha_hint: float = 0.35,
) -> tk.Canvas:
    """
    Create a Canvas-based glassmorphism panel.

    Renders a rounded rectangle with:
      - A dark translucent fill (DEEP or custom fill_color)
      - A 1px neon hairline border
      - Layered glow simulation around the border

    Returns the Canvas widget. Attach child widgets using canvas.create_window().
    A convenience attribute canvas.inner_frame (ttk.Frame) is placed inside
    the canvas so callers can pack/grid normal widgets into it.
    """
    canvas = tk.Canvas(
        parent,
        width=width,
        height=height,
        bg=_get_parent_bg(parent),
        highlightthickness=0,
        bd=0,
    )

    pad = 6  # Glow bleed padding

    # Glow layers
    _draw_glow_border(
        canvas,
        pad, pad,
        width - pad, height - pad,
        radius,
        glow_color=border_color,
        layers=3,
    )

    # Glass fill
    _draw_rounded_rect(
        canvas,
        pad, pad,
        width - pad, height - pad,
        radius,
        fill=fill_color,
        outline="",
    )

    # Hairline neon border
    _draw_rounded_rect(
        canvas,
        pad, pad,
        width - pad, height - pad,
        radius,
        fill="",
        outline=border_color,
        width=1,
    )

    # Inner frame for child widgets
    inner = ttk.Frame(canvas, style="Card.TFrame")
    canvas.create_window(
        width // 2, height // 2,
        window=inner,
        width=width - (pad * 2) - 4,
        height=height - (pad * 2) - 4,
    )
    canvas.inner_frame = inner

    return canvas


def create_neon_button(
    parent,
    text: str,
    command=None,
    variant: str = "primary",
) -> tk.Canvas:
    """
    Create a Canvas-based neon-styled button.

    Variants:
      primary   - Filled CYAN background, VOID text
      secondary - VOID fill, CYAN outline + CYAN text
      danger    - VOID fill, PINK outline + PINK text
      ghost     - Transparent, TEXT_SECONDARY text, no border drawn
    """
    pad_x = SP_4
    pad_y = SP_2
    radius = RADIUS_SM
    font_spec = FONT_SECTION

    # Measure text to auto-size the button
    tmp = tk.Label(parent, text=text, font=font_spec)
    tmp.update_idletasks()
    tw = tmp.winfo_reqwidth()
    th = tmp.winfo_reqheight()
    tmp.destroy()

    btn_w = tw + pad_x * 2 + 8
    btn_h = th + pad_y * 2 + 4

    variant_styles = {
        "primary":   {"fill": CYAN,  "border": CYAN,  "fg": VOID,         "hover_border": ICE,  "hover_fill": ICE},
        "secondary": {"fill": VOID,  "border": CYAN,  "fg": CYAN,         "hover_border": ICE,  "hover_fill": DEEP},
        "danger":    {"fill": VOID,  "border": PINK,  "fg": PINK,         "hover_border": MAGENTA, "hover_fill": DEEP},
        "ghost":     {"fill": VOID,  "border": "",    "fg": TEXT_SECONDARY,"hover_border": "", "hover_fill": DEEP},
    }
    s = variant_styles.get(variant, variant_styles["secondary"])

    canvas = tk.Canvas(
        parent,
        width=btn_w,
        height=btn_h,
        bg=_get_parent_bg(parent),
        highlightthickness=0,
        bd=0,
        cursor="hand2",
    )

    def _draw(fill, border, fg):
        canvas.delete("all")
        if variant != "ghost":
            _draw_rounded_rect(
                canvas,
                1, 1, btn_w - 1, btn_h - 1,
                radius,
                fill=fill,
                outline=border,
                width=1,
            )
        canvas.create_text(
            btn_w // 2, btn_h // 2,
            text=text,
            fill=fg,
            font=font_spec,
            anchor="center",
            tags="btn_text",
        )

    _draw(s["fill"], s["border"], s["fg"])

    def on_enter(_):
        _draw(s["hover_fill"], s["hover_border"], s["fg"] if variant != "primary" else VOID)

    def on_leave(_):
        _draw(s["fill"], s["border"], s["fg"])

    def on_click(_):
        if command:
            command()

    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", on_click)

    return canvas


def create_section_header(parent, text: str) -> ttk.Label:
    """
    Return a tracked-uppercase section label styled in CYAN with the heading font.
    """
    label = ttk.Label(
        parent,
        text=text.upper(),
        foreground=CYAN,
        background=_get_parent_bg(parent),
        font=(FONT_FALLBACK, FS_SM, "bold"),
        anchor="w",
    )
    return label


def create_badge(parent, text: str, color: str) -> tk.Canvas:
    """
    Create a pill-shaped badge with a colored border and matching text.
    Used for evidence type tags and severity indicators.
    """
    font_spec = (FONT_FALLBACK, FS_XS, "bold")
    tmp = tk.Label(parent, text=text, font=font_spec)
    tmp.update_idletasks()
    tw = tmp.winfo_reqwidth()
    th = tmp.winfo_reqheight()
    tmp.destroy()

    pad_x = 10
    pad_y = 3
    w = tw + pad_x * 2
    h = th + pad_y * 2
    radius = h // 2

    canvas = tk.Canvas(
        parent,
        width=w,
        height=h,
        bg=_get_parent_bg(parent),
        highlightthickness=0,
        bd=0,
    )

    # Blended fill: color mixed toward VOID for subtle tint
    r, g, b = _hex_to_rgb(color)
    vr, vg, vb = _hex_to_rgb(VOID)
    factor = 0.18
    fr = int(r * factor + vr * (1 - factor))
    fg_ = int(g * factor + vg * (1 - factor))
    fb = int(b * factor + vb * (1 - factor))
    fill_tint = f"#{fr:02x}{fg_:02x}{fb:02x}"

    _draw_rounded_rect(canvas, 1, 1, w - 1, h - 1, radius, fill=fill_tint, outline=color, width=1)
    canvas.create_text(w // 2, h // 2, text=text, fill=color, font=font_spec, anchor="center")

    return canvas


def create_styled_entry(parent, placeholder: str = "") -> tk.Entry:
    """
    Return a tk.Entry styled with FORENSEQUENCE dark tokens and CYAN focus glow.
    A placeholder is simulated via FocusIn/FocusOut bindings.
    """
    entry = tk.Entry(
        parent,
        bg=ABYSS,
        fg=TEXT_PRIMARY,
        insertbackground=CYAN,
        relief="flat",
        bd=0,
        font=FONT_BODY,
        highlightthickness=1,
        highlightbackground=PLUM,
        highlightcolor=CYAN,
    )

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


def create_divider(parent, color: str = PLUM) -> tk.Canvas:
    """
    Return a 1px horizontal separator line canvas widget.
    """
    line = tk.Canvas(
        parent,
        height=1,
        bg=color,
        highlightthickness=0,
        bd=0,
    )
    return line


# =============================================================================
# INTERNAL UTILITIES
# =============================================================================

def _get_parent_bg(parent) -> str:
    """
    Attempt to retrieve the background color of a parent widget.
    Falls back to VOID if unavailable.
    """
    try:
        bg = parent.cget("background")
        if bg:
            return bg
    except Exception:
        pass
    return VOID

# =============================================================================
# main.py
# FORENSEQUENCE - Phase 1 Theme Lab
# Visual QA harness for all design system primitives.
# =============================================================================

import tkinter as tk
import ttkbootstrap as ttk

from gui.theme import (
    # Color tokens
    VOID, DEEP, ABYSS, STEEL,
    CYAN, PINK, PEACH, PURPLE, PLUM,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    # Spacing
    SP_2, SP_3, SP_4, SP_6, SP_8, SP_12,
    # Font specs
    FONT_HEADING, FONT_BODY, FONT_MONO_BODY, FONT_SMALL, FS_XS,
    FONT_FALLBACK,
    # Helpers
    apply_theme, risk_color, risk_label,
    # Primitives
    create_glass_frame,
    create_neon_button,
    create_section_header,
    create_badge,
    create_styled_entry,
    create_divider,
)


def build_theme_lab(app: ttk.Window) -> None:
    """
    Construct the Phase 1 Theme Lab layout.
    Every primitive is exercised exactly once so the palette and components
    can be visually verified before any screens are built.
    """

    # -- Root scroll canvas so content is accessible at any window size --
    root_canvas = tk.Canvas(app, bg=VOID, highlightthickness=0)
    scrollbar = ttk.Scrollbar(app, orient="vertical", command=root_canvas.yview)
    root_canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    root_canvas.pack(side="left", fill="both", expand=True)

    # Scrollable inner container
    container = ttk.Frame(root_canvas, style="TFrame")
    container_id = root_canvas.create_window((0, 0), window=container, anchor="nw")

    def _on_configure(event):
        root_canvas.configure(scrollregion=root_canvas.bbox("all"))
        root_canvas.itemconfig(container_id, width=root_canvas.winfo_width())

    container.bind("<Configure>", _on_configure)
    root_canvas.bind("<Configure>", lambda e: root_canvas.itemconfig(container_id, width=e.width))

    def _on_mousewheel(event):
        root_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    root_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # -- Page padding wrapper --
    page = ttk.Frame(container, style="TFrame", padding=(SP_8, SP_8, SP_8, SP_8))
    page.pack(fill="both", expand=True)

    # =========================================================================
    # SECTION 1: Application Title
    # =========================================================================

    ttk.Label(
        page,
        text="FORENSEQUENCE",
        foreground=CYAN,
        background=VOID,
        font=(FONT_FALLBACK, 28, "bold"),
        anchor="w",
    ).pack(fill="x", pady=(0, SP_2))

    ttk.Label(
        page,
        text="Phase 1 — Theme Lab & Design System Verification",
        foreground=TEXT_SECONDARY,
        background=VOID,
        font=FONT_BODY,
        anchor="w",
    ).pack(fill="x", pady=(0, SP_4))

    create_divider(page, color=CYAN).pack(fill="x", pady=(0, SP_6))

    # =========================================================================
    # SECTION 2: Glass Panel
    # =========================================================================

    _section(page, "GLASS PANEL PRIMITIVE")

    glass = create_glass_frame(page, width=720, height=140, radius=14, border_color=CYAN)
    glass.pack(anchor="w", pady=(SP_3, SP_6))

    inner = glass.inner_frame
    ttk.Label(
        inner,
        text="Glass Panel — Card.TFrame surface rendered on Canvas",
        foreground=TEXT_PRIMARY,
        background=DEEP,
        font=(FONT_FALLBACK, 11, "bold"),
        anchor="w",
    ).pack(fill="x", padx=SP_4, pady=(SP_4, SP_2))

    ttk.Label(
        inner,
        text="Neon hairline border  |  Layered glow simulation  |  Rounded corners  |  Dark translucent fill",
        foreground=TEXT_SECONDARY,
        background=DEEP,
        font=FONT_SMALL,
        anchor="w",
    ).pack(fill="x", padx=SP_4)

    # Pink-variant glass
    glass_pink = create_glass_frame(
        page, width=720, height=80, radius=14, border_color=PINK, fill_color=ABYSS
    )
    glass_pink.pack(anchor="w", pady=(0, SP_6))

    inner_pink = glass_pink.inner_frame
    ttk.Label(
        inner_pink,
        text="Pink border variant — ABYSS fill  |  Used for alert / high-severity panels",
        foreground=PINK,
        background=ABYSS,
        font=FONT_SMALL,
        anchor="w",
    ).pack(fill="x", padx=SP_4, pady=SP_3)

    # =========================================================================
    # SECTION 3: Neon Buttons
    # =========================================================================

    _section(page, "NEON BUTTON VARIANTS")

    btn_row = ttk.Frame(page, style="TFrame")
    btn_row.pack(anchor="w", pady=(SP_3, SP_6))

    variants = [
        ("RUN ANALYSIS", "primary"),
        ("EXPORT REPORT", "secondary"),
        ("DELETE CASE", "danger"),
        ("VIEW LOG", "ghost"),
    ]
    for label_text, var in variants:
        btn = create_neon_button(btn_row, text=label_text, variant=var)
        btn.pack(side="left", padx=(0, SP_3))

    ttk.Label(
        page,
        text="Hover each button to verify glow / fill transitions",
        foreground=TEXT_MUTED,
        background=VOID,
        font=FONT_SMALL,
        anchor="w",
    ).pack(fill="x", pady=(0, SP_6))

    # =========================================================================
    # SECTION 4: Section Headers
    # =========================================================================

    _section(page, "SECTION HEADER COMPONENT")

    for sample in ["Evidence Summary", "AI Findings", "Case Timeline", "Live Monitor"]:
        create_section_header(page, sample).pack(anchor="w", pady=(0, SP_2))

    _spacer(page)

    # =========================================================================
    # SECTION 5: Badges
    # =========================================================================

    _section(page, "BADGE COMPONENTS")

    badge_row = ttk.Frame(page, style="TFrame")
    badge_row.pack(anchor="w", pady=(SP_3, SP_6))

    badges = [
        ("LOG", CYAN),
        ("FILE", PURPLE),
        ("BROWSER", PEACH),
        ("EMAIL", PINK),
        ("HIGH", PINK),
        ("MEDIUM", PEACH),
        ("LOW", CYAN),
        ("AI INFERRED", PURPLE),
    ]
    for b_text, b_color in badges:
        badge = create_badge(badge_row, text=b_text, color=b_color)
        badge.pack(side="left", padx=(0, SP_2))

    # =========================================================================
    # SECTION 6: Styled Entry
    # =========================================================================

    _section(page, "STYLED ENTRY — CYAN FOCUS GLOW")

    entry_row = ttk.Frame(page, style="TFrame")
    entry_row.pack(fill="x", pady=(SP_3, SP_6))

    e1 = create_styled_entry(entry_row, placeholder="Search evidence files...")
    e1.pack(side="left", fill="x", expand=True, padx=(0, SP_4), ipady=SP_2)

    e2 = create_styled_entry(entry_row, placeholder="Case identifier...")
    e2.pack(side="left", fill="x", expand=True, ipady=SP_2)

    ttk.Label(
        page,
        text="Click an entry field to see the CYAN highlight border activate",
        foreground=TEXT_MUTED,
        background=VOID,
        font=FONT_SMALL,
        anchor="w",
    ).pack(fill="x", pady=(0, SP_6))

    # =========================================================================
    # SECTION 7: Divider
    # =========================================================================

    _section(page, "DIVIDER COMPONENT")

    create_divider(page, color=PLUM).pack(fill="x", pady=(SP_3, SP_2))
    create_divider(page, color=CYAN).pack(fill="x", pady=(SP_2, SP_2))
    create_divider(page, color=PINK).pack(fill="x", pady=(SP_2, SP_6))

    ttk.Label(
        page, text="PLUM / CYAN / PINK divider variants shown above",
        foreground=TEXT_MUTED, background=VOID, font=FONT_SMALL, anchor="w",
    ).pack(fill="x", pady=(0, SP_6))

    # =========================================================================
    # SECTION 8: Typography Scale
    # =========================================================================

    _section(page, "TYPOGRAPHY & TEXT HIERARCHY")

    type_rows = [
        ("TEXT_PRIMARY   #EAF6FF", TEXT_PRIMARY, FONT_BODY),
        ("TEXT_SECONDARY #8FA3C7", TEXT_SECONDARY, FONT_BODY),
        ("TEXT_MUTED     #5A6B8C", TEXT_MUTED,    FONT_SMALL),
        ("MONO BODY — log output / code traces", TEXT_PRIMARY, (FONT_FALLBACK, 11, "normal")),
    ]
    for t, color, font in type_rows:
        ttk.Label(
            page, text=t,
            foreground=color, background=VOID, font=font, anchor="w",
        ).pack(fill="x", pady=(0, SP_2))

    _spacer(page)

    # =========================================================================
    # SECTION 9: Risk Band Verification
    # =========================================================================

    _section(page, "RISK SCORING ENGINE VERIFICATION")

    risk_scores = [10, 45, 80]
    risk_row = ttk.Frame(page, style="TFrame")
    risk_row.pack(anchor="w", pady=(SP_3, SP_6))

    for score in risk_scores:
        color  = risk_color(score)
        label  = risk_label(score)

        swatch_frame = ttk.Frame(risk_row, style="TFrame")
        swatch_frame.pack(side="left", padx=(0, SP_6))

        # Color swatch
        swatch = tk.Canvas(
            swatch_frame, width=56, height=56,
            bg=VOID, highlightthickness=0, bd=0,
        )
        swatch.pack(pady=(0, SP_2))
        swatch.create_rectangle(4, 4, 52, 52, fill=color, outline=color)

        ttk.Label(
            swatch_frame,
            text=f"Score: {score}",
            foreground=TEXT_SECONDARY, background=VOID, font=FONT_SMALL, anchor="center",
        ).pack()
        ttk.Label(
            swatch_frame,
            text=label,
            foreground=color, background=VOID, font=(FONT_FALLBACK, 10, "bold"), anchor="center",
        ).pack()

    create_divider(page, color=PLUM).pack(fill="x", pady=(SP_6, SP_4))

    ttk.Label(
        page,
        text="Phase 1 verification complete — all primitives rendered. Proceed to Phase 2.",
        foreground=TEXT_MUTED,
        background=VOID,
        font=FONT_SMALL,
        anchor="w",
    ).pack(fill="x", pady=(0, SP_8))


# =============================================================================
# LAYOUT HELPERS (internal to main.py only)
# =============================================================================

def _section(parent, text: str) -> None:
    """Render a section header + thin divider."""
    create_section_header(parent, text).pack(fill="x", pady=(0, SP_2))
    create_divider(parent, color=PLUM).pack(fill="x", pady=(0, SP_3))


def _spacer(parent, height: int = 16) -> None:
    ttk.Frame(parent, style="TFrame", height=height).pack()


# =============================================================================
# ENTRY POINT
# =============================================================================

def main() -> None:
    app = ttk.Window(themename="darkly")
    app.title("FORENSEQUENCE - Theme Lab")
    app.geometry("1200x760")
    app.minsize(900, 600)

    apply_theme(app)
    build_theme_lab(app)

    app.mainloop()


if __name__ == "__main__":
    main()

# =============================================================================
# gui/toast_notification.py
# FORENSEQUENCE - Thread-Safe Animated Cyberpunk Toast Notification System
# =============================================================================
#
# Provides a ToastNotificationManager that renders non-blocking overlay toast
# cards anchored to the bottom-right corner of any Tk window. Key properties:
#
#   - Framed tk.Toplevel overlay windows with overrideredirect(True)
#   - Severity-coded left accent edge bar: PINK (HIGH), PEACH (MED), CYAN (LOW)
#   - Neon PURPLE rule-code badge, bold finding title, monospace explanation
#   - Auto-dismiss after 5000 ms via a Canvas progress-line drain animation
#   - Manual close button [X] with PINK hover
#   - Vertical stacking of multiple simultaneous toasts without overlap
#   - All positioning and animation happen exclusively on the main Tkinter thread
# =============================================================================

import os
import sys
import tkinter as tk
from typing import Callable, Dict, Any, List

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_MODULE_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from gui.theme import (
    VOID, ABYSS, DEEP, STEEL, CYAN, ICE, PINK, MAGENTA, PURPLE, PLUM, PEACH,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    FONT_FALLBACK, FONT_MONO_FALLBACK,
    FS_XS, FS_SM, _hex_to_rgb, create_badge,
)

TOAST_WIDTH         = 380
TOAST_MARGIN_RIGHT  = 20
TOAST_MARGIN_BTM    = 48
TOAST_GAP           = 8
TOAST_DURATION_MS   = 5000
TOAST_FADE_STEPS    = 30
TOAST_FADE_DELAY_MS = 16
PROGRESS_STEPS      = 100
PROGRESS_DELAY_MS   = TOAST_DURATION_MS // PROGRESS_STEPS
ACCENT_EDGE_W       = 5


class ToastCard:
    """
    A single overlay toast notification window rendered as a frameless
    tk.Toplevel positioned at the bottom-right corner of the root window.

    Parameters
    ----------
    root : tk.Misc
        Root Tk window used to resolve screen geometry.
    finding : dict
        Forensic finding dict with keys: rule_code, name, description,
        severity, explanation.
    stack_index : int
        Zero-based index in the active toast stack (0 = bottommost).
    on_close : Callable
        Invoked with this card instance when it dismisses so the manager
        can update the stack.
    """

    def __init__(
        self,
        root: tk.Misc,
        finding: Dict[str, Any],
        stack_index: int,
        on_close: Callable,
    ) -> None:
        self._root = root
        self._finding = finding
        self._stack_index = stack_index
        self._on_close = on_close
        self._dismissed = False
        self._after_ids: List[str] = []
        self._drag_x = 0
        self._drag_y = 0

        severity = int(finding.get("severity", 0))
        if severity >= 25:
            self._accent = PINK
            self._level_text = "HIGH"
        elif severity >= 15:
            self._accent = PEACH
            self._level_text = "MED"
        else:
            self._accent = CYAN
            self._level_text = "LOW"

        self._build_window()
        self._start_progress_drain()

    def _build_window(self) -> None:
        """Construct the Toplevel window and all child widgets."""
        self._win = tk.Toplevel(self._root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        try:
            self._win.attributes("-alpha", 0.97)
        except Exception:
            pass
        self._win.configure(bg=VOID)

        rule_code = self._finding.get("rule_code", "R000")
        name      = self._finding.get("name", "Unknown Finding")
        severity  = int(self._finding.get("severity", 0))
        expl_raw  = self._finding.get("explanation", "")
        expl_text = (expl_raw[:110] + "...") if len(expl_raw) > 113 else expl_raw

        outer = tk.Frame(
            self._win, bg=DEEP,
            highlightthickness=1, highlightbackground=STEEL,
        )
        outer.pack(fill="both", expand=True)

        accent_col = tk.Frame(outer, bg=self._accent, width=ACCENT_EDGE_W)
        accent_col.pack(side="left", fill="y")
        accent_col.pack_propagate(False)
        self._draw_accent_glow(accent_col)

        content = tk.Frame(outer, bg=DEEP, padx=10, pady=8)
        content.pack(side="left", fill="both", expand=True)

        top_row = tk.Frame(content, bg=DEEP)
        top_row.pack(fill="x")

        badge = create_badge(top_row, f"ALERT: {rule_code}", PURPLE, bg=DEEP)
        badge.pack(side="left", padx=(0, 6))

        tk.Label(
            top_row, text=self._level_text,
            fg=self._accent, bg=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(side="left")

        self._close_lbl = tk.Label(
            top_row, text="[X]",
            fg=PINK, bg=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
            cursor="hand2",
        )
        self._close_lbl.pack(side="right")
        self._close_lbl.bind("<Enter>", lambda _: self._close_lbl.configure(fg=MAGENTA))
        self._close_lbl.bind("<Leave>", lambda _: self._close_lbl.configure(fg=PINK))
        self._close_lbl.bind("<Button-1>", lambda _: self.dismiss())

        tk.Label(
            content, text=name,
            fg=TEXT_PRIMARY, bg=DEEP,
            font=(FONT_FALLBACK, FS_SM, "bold"),
            anchor="w",
            wraplength=TOAST_WIDTH - ACCENT_EDGE_W - 32,
            justify="left",
        ).pack(fill="x", pady=(4, 0))

        sev_row = tk.Frame(content, bg=DEEP)
        sev_row.pack(fill="x", pady=(2, 0))
        tk.Label(
            sev_row, text=f"SEVERITY +{severity} PTS",
            fg=self._accent, bg=DEEP,
            font=(FONT_MONO_FALLBACK, FS_XS, "bold"),
        ).pack(side="left")

        if expl_text:
            tk.Label(
                content, text=expl_text,
                fg=TEXT_SECONDARY, bg=DEEP,
                font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
                anchor="w",
                wraplength=TOAST_WIDTH - ACCENT_EDGE_W - 32,
                justify="left",
            ).pack(fill="x", pady=(4, 0))

        prog_host = tk.Frame(outer, bg=ABYSS, height=3)
        prog_host.pack(side="bottom", fill="x")
        prog_host.pack_propagate(False)

        self._prog_canvas = tk.Canvas(
            prog_host, height=3, bg=ABYSS, highlightthickness=0, bd=0
        )
        self._prog_canvas.pack(fill="both", expand=True)
        self._prog_bar = self._prog_canvas.create_rectangle(
            0, 0, TOAST_WIDTH, 3, fill=self._accent, outline=""
        )

        for widget in (outer, content, top_row, sev_row):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)

        self._win.update_idletasks()
        self._position_window()

    def _draw_accent_glow(self, parent: tk.Frame) -> None:
        """Render layered glow lines on the accent bar canvas."""
        glow = tk.Canvas(
            parent, width=ACCENT_EDGE_W, bg=self._accent,
            highlightthickness=0, bd=0,
        )
        glow.pack(fill="both", expand=True)
        r, g, b = _hex_to_rgb(self._accent)
        vr, vg, vb = _hex_to_rgb(DEEP)
        for i in range(1, 4):
            factor = (4 - i) / 5.0
            br = int(r * factor + vr * (1 - factor))
            bg_ = int(g * factor + vg * (1 - factor))
            bb = int(b * factor + vb * (1 - factor))
            glow.create_line(
                ACCENT_EDGE_W - i, 0, ACCENT_EDGE_W - i, 1000,
                fill=f"#{br:02x}{bg_:02x}{bb:02x}", width=1,
            )

    def _position_window(self) -> None:
        """Anchor this toast at the correct stacked bottom-right position."""
        try:
            root_x = self._root.winfo_rootx()
            root_y = self._root.winfo_rooty()
            root_w = self._root.winfo_width()
            root_h = self._root.winfo_height()
        except Exception:
            return
        card_h = self._win.winfo_reqheight()
        x = root_x + root_w - TOAST_WIDTH - TOAST_MARGIN_RIGHT
        y = (root_y + root_h - TOAST_MARGIN_BTM - card_h
             - self._stack_index * (card_h + TOAST_GAP))
        self._win.geometry(f"{TOAST_WIDTH}x{card_h}+{x}+{y}")

    def update_stack_index(self, new_index: int) -> None:
        """Reposition this toast after stack order changes."""
        self._stack_index = new_index
        if not self._dismissed:
            try:
                if self._win.winfo_exists():
                    self._position_window()
            except Exception:
                pass

    def _start_progress_drain(self) -> None:
        """Begin the shrinking progress bar countdown."""
        self._progress_step = 0
        self._drain_step()

    def _drain_step(self) -> None:
        """Advance progress bar one step toward zero."""
        if self._dismissed:
            return
        self._progress_step += 1
        fraction = max(0.0, 1.0 - self._progress_step / PROGRESS_STEPS)
        bar_w = int(TOAST_WIDTH * fraction)
        try:
            self._prog_canvas.coords(self._prog_bar, 0, 0, bar_w, 3)
        except Exception:
            return
        if self._progress_step >= PROGRESS_STEPS:
            self._start_fade_out()
        else:
            aid = self._prog_canvas.after(PROGRESS_DELAY_MS, self._drain_step)
            self._after_ids.append(str(aid))

    def _start_fade_out(self) -> None:
        """Begin alpha fade-out animation."""
        self._fade_step = 0
        self._fade_out_tick()

    def _fade_out_tick(self) -> None:
        """Reduce window alpha by one increment."""
        if self._dismissed:
            return
        self._fade_step += 1
        alpha = max(0.0, 0.97 - (self._fade_step / TOAST_FADE_STEPS) * 0.97)
        try:
            if self._win.winfo_exists():
                self._win.attributes("-alpha", alpha)
            else:
                self._finalize_dismiss()
                return
        except Exception:
            self._finalize_dismiss()
            return
        if self._fade_step >= TOAST_FADE_STEPS:
            self._finalize_dismiss()
        else:
            aid = self._win.after(TOAST_FADE_DELAY_MS, self._fade_out_tick)
            self._after_ids.append(str(aid))

    def dismiss(self) -> None:
        """
        Immediately dismiss this card, cancelling all callbacks
        and destroying the Toplevel window.
        """
        if self._dismissed:
            return
        self._dismissed = True
        for aid in self._after_ids:
            try:
                self._win.after_cancel(aid)
            except Exception:
                pass
        self._after_ids.clear()
        try:
            if self._win.winfo_exists():
                self._win.destroy()
        except Exception:
            pass
        if self._on_close:
            self._on_close(self)

    def _finalize_dismiss(self) -> None:
        self.dismiss()

    def _on_drag_start(self, event) -> None:
        self._drag_x = event.x_root - self._win.winfo_x()
        self._drag_y = event.y_root - self._win.winfo_y()

    def _on_drag_motion(self, event) -> None:
        self._win.geometry(
            f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}"
        )

    @property
    def is_alive(self) -> bool:
        """True if this card has not yet been dismissed."""
        return not self._dismissed


class ToastNotificationManager:
    """
    Manages the lifecycle and vertical stacking of all active ToastCard
    overlays anchored to the bottom-right corner of a given root window.

    Thread-safety contract
    ----------------------
    All public methods MUST be called from the main Tkinter thread.
    Wire calls through queue polling / root.after callbacks, never
    directly from watchdog or background threads.

    Usage
    -----
        manager = ToastNotificationManager(root_window)
        manager.show_alert(finding_dict)
    """

    def __init__(self, root: tk.Misc) -> None:
        """
        Parameters
        ----------
        root : tk.Misc
            Application root or main shell window used for geometry resolution.
        """
        self._root = root
        self._stack: List[ToastCard] = []

    def show_alert(self, finding: Dict[str, Any]) -> None:
        """
        Spawn a new ToastCard for a forensic finding.

        Parameters
        ----------
        finding : dict
            Finding dict with keys: rule_code, name, description,
            severity, explanation.
        """
        stack_idx = len(self._stack)
        card = ToastCard(
            root=self._root,
            finding=finding,
            stack_index=stack_idx,
            on_close=self._on_card_closed,
        )
        self._stack.append(card)

    def _on_card_closed(self, card: ToastCard) -> None:
        """
        Remove the closed card and reindex all remaining cards
        so they reposition upward to fill any gap.
        """
        if card in self._stack:
            self._stack.remove(card)
        alive = [c for c in self._stack if c.is_alive]
        self._stack = alive
        for idx, c in enumerate(alive):
            c.update_stack_index(idx)

    def dismiss_all(self) -> None:
        """Immediately dismiss every active toast card."""
        for card in list(self._stack):
            card.dismiss()
        self._stack.clear()

    @property
    def active_count(self) -> int:
        """Number of currently visible toast cards."""
        return sum(1 for c in self._stack if c.is_alive)


if __name__ == "__main__":
    import ttkbootstrap as ttk
    from gui.theme import apply_theme

    print("=" * 60)
    print("FORENSEQUENCE - Toast Notification Standalone Test")
    print("=" * 60)

    root = ttk.Window(themename="darkly")
    root.title("Toast Test Harness")
    root.geometry("900x600+200+150")
    root.configure(bg=VOID)
    apply_theme(root)

    manager = ToastNotificationManager(root)

    sample_findings = [
        {
            "rule_code": "R009",
            "name": "Incremental File Deletion Activity",
            "description": "Sequential deletion of files detected.",
            "severity": 10,
            "explanation": "deleted_files=7 (threshold=3) | paths=[/var/log/auth.log]",
        },
        {
            "rule_code": "R001",
            "name": "Brute Force Authentication Attempt",
            "description": "Multiple consecutive failed login attempts detected.",
            "severity": 20,
            "explanation": "failed_logins=12 (threshold=5) | ips=[192.168.1.105] | users=[root]",
        },
        {
            "rule_code": "R005",
            "name": "Suspicious Domain Communication",
            "description": "Outbound connection to flagged suspicious domain observed.",
            "severity": 25,
            "explanation": "suspicious_domains=1 | domain=malware-c2.xyz | protocol=HTTP",
        },
    ]

    main_lbl = ttk.Label(
        root,
        text="Toast Notification Test - click buttons to fire alerts",
        foreground=TEXT_SECONDARY, background=VOID,
        font=(FONT_FALLBACK, 12, "normal"),
    )
    main_lbl.pack(pady=50)

    btn_row = tk.Frame(root, bg=VOID)
    btn_row.pack()

    def fire(idx: int) -> None:
        manager.show_alert(sample_findings[idx])
        print(f"Fired finding[{idx}] severity={sample_findings[idx]['severity']}. Active: {manager.active_count}")

    def fire_all() -> None:
        for f in sample_findings:
            manager.show_alert(f)
        print(f"Fired all 3 stacked toasts. Active: {manager.active_count}")

    for txt, cmd, col in [
        ("[LOW ALERT]",    lambda: fire(0), CYAN),
        ("[MEDIUM ALERT]", lambda: fire(1), PEACH),
        ("[HIGH ALERT]",   lambda: fire(2), PINK),
        ("[FIRE ALL 3]",   fire_all,        PURPLE),
    ]:
        b = tk.Label(
            btn_row, text=txt, fg=col, bg=ABYSS,
            font=(FONT_FALLBACK, 11, "bold"),
            padx=12, pady=6, cursor="hand2",
            bd=1, relief="solid",
            highlightthickness=1, highlightbackground=col,
        )
        b.pack(side="left", padx=8, pady=8)
        b.bind("<Button-1>", lambda _, c=cmd: c())
        b.bind("<Enter>", lambda e, w=b: w.configure(bg=DEEP))
        b.bind("<Leave>", lambda e, w=b: w.configure(bg=ABYSS))

    dismiss_lbl = ttk.Label(
        root, text="[DISMISS ALL]",
        foreground=TEXT_MUTED, background=VOID,
        font=(FONT_FALLBACK, 10, "normal"), cursor="hand2",
    )
    dismiss_lbl.pack(pady=6)
    dismiss_lbl.bind("<Button-1>", lambda _: manager.dismiss_all())

    ttk.Label(
        root,
        text="Toasts auto-dismiss after 5 seconds. Stacking shown with [FIRE ALL 3].",
        foreground=TEXT_MUTED, background=VOID,
        font=(FONT_FALLBACK, 9, "normal"),
    ).pack(pady=(8, 0))

    print("Test window launched. Check bottom-right corner.")
    root.mainloop()

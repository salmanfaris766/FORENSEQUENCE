# =============================================================================
# gui/analysis_frame.py
# FORENSEQUENCE - Forward Chaining AI Reasoning & Analysis Screen
# =============================================================================

import os
import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional, Callable, Dict, Any, List

from gui.risk_gauge_widget import CyberpunkRiskGauge
from analysis.risk_engine import calculate_risk

from gui.theme import (
    VOID,
    ABYSS,
    DEEP,
    STEEL,
    CYAN,
    ICE,
    PINK,
    MAGENTA,
    PURPLE,
    PLUM,
    PEACH,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_FALLBACK,
    FONT_DISPLAY,
    FONT_MONO_FALLBACK,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_SECTION,
    FONT_BODY,
    FONT_SMALL,
    FONT_MONO_SM,
    FONT_MONO_BODY,
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
    SP_8,
    RADIUS_SM,
    RADIUS_MD,
    create_glass_frame,
    create_section_header,
    create_badge,
    create_divider,
    create_neon_button,
    risk_color,
    risk_label,
)

from analyzers.log_analyzer import parse_log_file
from ai.rule_engine import ForwardChainingEngine
from database import (
    get_case_by_id,
    get_evidence_for_case,
    add_finding,
    get_findings_for_case,
    clear_findings_for_case,
)
from analysis.timeline import (
    build_timeline,
    filter_timeline,
    summarize_timeline,
    TimelineBuilder,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AnalysisFrame(ttk.Frame):
    """
    Forward Chaining AI Reasoning Analysis Screen.
    Executes deterministic propositional inference over extracted case facts,
    persists derived findings into SQLite, and renders human-explainable proof traces.
    """

    def __init__(
        self,
        parent: tk.Misc,
        case_id: Optional[int] = None,
        on_navigate: Optional[Callable[[str], None]] = None,
        shell=None,
        **kwargs,
    ):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.case_id = case_id
        self.on_navigate = on_navigate
        self.shell = shell

        # Inherit selected case context from shell if available
        if self.case_id is None and self.shell and getattr(self.shell, "selected_case_id", None):
            self.case_id = self.shell.selected_case_id

        self._is_analyzing = False
        self.latest_facts: Dict[str, Any] = {}
        self.latest_result: Dict[str, Any] = {}
        self.raw_timeline: List[Dict[str, Any]] = []
        self.active_timeline_filter: str = "ALL"
        self.timeline_sort_ascending: bool = True
        self._filter_chips: Dict[str, tk.Widget] = {}

        self._build_ui()
        self.refresh_data()

    def set_case(self, case_id: Optional[int]) -> None:
        """Update active investigation case and reload findings."""
        self.case_id = case_id
        self.refresh_data()

    # -------------------------------------------------------------------------
    # Layout Builder
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct the visual hierarchy of the AI Analysis interface."""
        self.configure(style="TFrame")

        # ---------------------------------------------------------------------
        # 1. Top Header & Control Bar
        # ---------------------------------------------------------------------
        header_card = create_glass_frame(
            self, width=960, height=130, border_color=PURPLE, fill_color=DEEP
        )
        header_card.pack(fill="x", padx=SP_6, pady=(SP_6, SP_3))
        inner_h = header_card.inner_frame

        # Left Header Block: Title + Case Badge + Risk Badge
        left_h = ttk.Frame(inner_h, style="Card.TFrame")
        left_h._custom_bg = DEEP
        left_h.pack(side="left", fill="both", expand=True, padx=SP_4, pady=SP_2)

        create_section_header(left_h, "FORWARD CHAINING AI REASONING ENGINE").pack(anchor="w")

        info_row = ttk.Frame(left_h, style="Card.TFrame")
        info_row._custom_bg = DEEP
        info_row.pack(anchor="w", pady=(2, 0))

        # Case Context Badge
        self.case_badge_container = ttk.Frame(info_row, style="Card.TFrame")
        self.case_badge_container._custom_bg = DEEP
        self.case_badge_container.pack(side="left", padx=(0, SP_2))
        self.badge_case = create_badge(self.case_badge_container, "NO ACTIVE CASE", TEXT_MUTED, bg=DEEP)
        self.badge_case.pack(side="left")

        # Risk Band Badge
        self.risk_badge_container = ttk.Frame(info_row, style="Card.TFrame")
        self.risk_badge_container._custom_bg = DEEP
        self.risk_badge_container.pack(side="left", padx=(0, SP_3))
        self.badge_risk = create_badge(self.risk_badge_container, "RISK: --", TEXT_MUTED, bg=DEEP)
        self.badge_risk.pack(side="left")

        # Numeric Risk Score Display
        self.lbl_risk_score = ttk.Label(
            info_row,
            text="SCORE: -- / 100",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_DISPLAY, FS_SM, "bold"),
        )
        self.lbl_risk_score.pack(side="left")

        # Center: Compact Risk Gauge
        gauge_frame = ttk.Frame(inner_h, style="Card.TFrame")
        gauge_frame._custom_bg = DEEP
        gauge_frame.pack(side="left", fill="y", padx=SP_3, pady=SP_1)

        self.header_gauge = CyberpunkRiskGauge(
            gauge_frame,
            size=140,
            score=0,
            compact=True,
            bg=DEEP,
        )
        self.header_gauge.pack()

        # Right Action Bar: [RUN FORWARD CHAINING] & [CLEAR FINDINGS]
        right_h = ttk.Frame(inner_h, style="Card.TFrame")
        right_h._custom_bg = DEEP
        right_h.pack(side="right", fill="y", padx=SP_4, pady=SP_2)

        self.btn_run = create_neon_button(
            right_h,
            text="[RUN FORWARD CHAINING ANALYSIS]",
            command=self.run_analysis,
            variant="primary",
            bg=DEEP,
        )
        self.btn_run.pack(side="top", fill="x", pady=(0, 2))

        self.btn_clear = create_neon_button(
            right_h,
            text="[CLEAR FINDINGS]",
            command=self._handle_clear_findings,
            variant="ghost",
            bg=DEEP,
        )
        self.btn_clear.pack(side="top", fill="x")

        # ---------------------------------------------------------------------
        # 2. Main Two-Column Content Workspace
        # ---------------------------------------------------------------------
        self.body_container = ttk.Frame(self, style="TFrame")
        self.body_container.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_4))

        # --- Left Column (38% width): Section A - Extracted Evidence Facts ---
        self.left_column = ttk.Frame(self.body_container, style="TFrame", width=380)
        self.left_column.pack(side="left", fill="both", expand=False, padx=(0, SP_3))
        self.left_column.pack_propagate(False)

        self._build_facts_panel()

        # --- Right Column (62% width): Section B, Section C & Section D ---
        self.right_column = ttk.Frame(self.body_container, style="TFrame")
        self.right_column.pack(side="left", fill="both", expand=True)

        self._build_findings_panel()
        self._build_timeline_panel()
        self._build_trace_panel()

    # -------------------------------------------------------------------------
    # Section A: Extracted Evidence Facts
    # -------------------------------------------------------------------------

    def _build_facts_panel(self) -> None:
        """Render the evidence facts metric panel."""
        glass = create_glass_frame(
            self.left_column, width=380, height=530, border_color=CYAN, fill_color=DEEP
        )
        glass.pack(fill="both", expand=True)
        inner = glass.inner_frame

        create_section_header(inner, "EXTRACTED EVIDENCE FACTS").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )

        ttk.Label(
            inner,
            text="Deterministic signals harvested across case evidence artifacts.",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_SMALL,
            wraplength=340,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_2))

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(0, SP_2))

        # Facts Display Box
        self.facts_box = ttk.Frame(inner, style="Card.TFrame")
        self.facts_box._custom_bg = DEEP
        self.facts_box.pack(fill="both", expand=True, padx=SP_4, pady=(0, SP_3))

        self.fact_metric_labels = {}
        metrics_spec = [
            ("total_lines", "TOTAL LINES PARSED", TEXT_PRIMARY),
            ("failed_logins", "FAILED AUTH ATTEMPTS", CYAN),
            ("successful_logins", "SUCCESSFUL LOGINS", ICE),
            ("usb_connections", "USB MEDIA ATTACHMENTS", PEACH),
            ("executable_events", "SUSPICIOUS EXECUTIONS", PINK),
            ("deleted_files", "FILE DELETION EVENTS", PINK),
        ]

        for key, title, col in metrics_spec:
            row = tk.Frame(self.facts_box, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL, bd=0)
            row.pack(fill="x", pady=2)

            ttk.Label(
                row,
                text=title,
                foreground=TEXT_SECONDARY,
                background=ABYSS,
                font=(FONT_FALLBACK, FS_XS, "bold"),
            ).pack(side="left", padx=SP_3, pady=4)

            lbl_val = ttk.Label(
                row,
                text="--",
                foreground=col,
                background=ABYSS,
                font=(FONT_DISPLAY, FS_BASE, "bold"),
            )
            lbl_val.pack(side="right", padx=SP_3, pady=4)
            self.fact_metric_labels[key] = lbl_val

        # Monospace Lists for IPs and Users
        chip_box = tk.Frame(self.facts_box, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL, bd=0)
        chip_box.pack(fill="x", pady=(SP_2, 2))

        ttk.Label(
            chip_box,
            text="FLAGGED IP ADDRESSES",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_3, pady=(4, 1))

        self.lbl_ips = ttk.Label(
            chip_box,
            text="None detected",
            foreground=CYAN,
            background=ABYSS,
            font=FONT_MONO_SM,
            wraplength=330,
        )
        self.lbl_ips.pack(anchor="w", padx=SP_3, pady=(0, 4))

        user_box = tk.Frame(self.facts_box, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL, bd=0)
        user_box.pack(fill="x", pady=2)

        ttk.Label(
            user_box,
            text="FLAGGED USER ACCOUNTS",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_3, pady=(4, 1))

        self.lbl_users = ttk.Label(
            user_box,
            text="None detected",
            foreground=ICE,
            background=ABYSS,
            font=FONT_MONO_SM,
            wraplength=330,
        )
        self.lbl_users.pack(anchor="w", padx=SP_3, pady=(0, 4))

    # -------------------------------------------------------------------------
    # Section B: Derived Forensic Findings
    # -------------------------------------------------------------------------

    def _build_findings_panel(self) -> None:
        """Render the scrollable list of derived findings with proof cards."""
        glass = create_glass_frame(
            self.right_column, width=580, height=210, border_color=STEEL, fill_color=DEEP
        )
        glass.pack(fill="both", expand=True, pady=(0, SP_2))
        inner = glass.inner_frame

        # Header Row
        hdr_row = ttk.Frame(inner, style="Card.TFrame")
        hdr_row._custom_bg = DEEP
        hdr_row.pack(fill="x", padx=SP_4, pady=(SP_3, SP_1))

        create_section_header(hdr_row, "DERIVED FORENSIC FINDINGS").pack(side="left")

        self.lbl_findings_count = ttk.Label(
            hdr_row,
            text="0 FINDINGS",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_MONO_SM,
        )
        self.lbl_findings_count.pack(side="right")

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(0, SP_2))

        # Scrollable container for findings
        scroll_wrapper = ttk.Frame(inner, style="Card.TFrame")
        scroll_wrapper._custom_bg = DEEP
        scroll_wrapper.pack(fill="both", expand=True, padx=SP_2, pady=(0, SP_2))

        self.findings_canvas = tk.Canvas(scroll_wrapper, bg=DEEP, highlightthickness=0, bd=0)
        self.findings_scrollbar = ttk.Scrollbar(
            scroll_wrapper, orient="vertical", command=self.findings_canvas.yview
        )
        self.findings_canvas.configure(yscrollcommand=self.findings_scrollbar.set)

        self.findings_content = ttk.Frame(self.findings_canvas, style="Card.TFrame")
        self.findings_content._custom_bg = DEEP
        self.findings_win_id = self.findings_canvas.create_window(
            (0, 0), window=self.findings_content, anchor="nw"
        )

        def _on_findings_configure(event):
            self.findings_canvas.configure(scrollregion=self.findings_canvas.bbox("all"))

        def _on_findings_canvas_configure(event):
            self.findings_canvas.itemconfig(self.findings_win_id, width=event.width)

        self.findings_content.bind("<Configure>", _on_findings_configure)
        self.findings_canvas.bind("<Configure>", _on_findings_canvas_configure)

        def _on_findings_mousewheel(event):
            try:
                if self.findings_canvas.winfo_exists():
                    self.findings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        self.findings_canvas.bind(
            "<Enter>", lambda _: self.findings_canvas.bind_all("<MouseWheel>", _on_findings_mousewheel)
        )
        self.findings_canvas.bind(
            "<Leave>", lambda _: self.findings_canvas.unbind_all("<MouseWheel>")
        )

        self.findings_canvas.pack(side="left", fill="both", expand=True)
        self.findings_scrollbar.pack(side="right", fill="y")

    # -------------------------------------------------------------------------
    # Section C: Chronological Event Sequence Timeline
    # -------------------------------------------------------------------------

    def _build_timeline_panel(self) -> None:
        """Render the scrollable chronological timeline sequence with filter chips and neon spine."""
        glass = create_glass_frame(
            self.right_column, width=580, height=230, border_color=CYAN, fill_color=DEEP
        )
        glass.pack(fill="both", expand=True, pady=(0, SP_2))
        inner = glass.inner_frame

        # Header Row: Title + Sort Toggle + Event Count
        hdr_row = ttk.Frame(inner, style="Card.TFrame")
        hdr_row._custom_bg = DEEP
        hdr_row.pack(fill="x", padx=SP_4, pady=(SP_2, 2))

        create_section_header(hdr_row, "CHRONOLOGICAL EVENT SEQUENCE").pack(side="left")

        right_hdr = ttk.Frame(hdr_row, style="Card.TFrame")
        right_hdr._custom_bg = DEEP
        right_hdr.pack(side="right")

        self.btn_sort_order = tk.Label(
            right_hdr,
            text="[OLDEST FIRST]",
            font=(FONT_FALLBACK, FS_XS, "bold"),
            bg=DEEP,
            fg=CYAN,
            cursor="hand2",
            padx=6,
            pady=2,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=PLUM,
        )
        self.btn_sort_order.pack(side="left", padx=(0, SP_2))
        self.btn_sort_order.bind("<Enter>", lambda _: self.btn_sort_order.configure(fg=ICE, bg=ABYSS))
        self.btn_sort_order.bind("<Leave>", lambda _: self.btn_sort_order.configure(fg=CYAN, bg=DEEP))
        self.btn_sort_order.bind("<Button-1>", lambda _: self._toggle_sort_order())

        self.lbl_timeline_count = ttk.Label(
            right_hdr,
            text="0 EVENTS",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_MONO_SM,
        )
        self.lbl_timeline_count.pack(side="left")

        # Category Filter Chips Bar
        self._build_filter_chips(inner)

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(2, SP_2))

        # Scrollable container for timeline events
        scroll_wrapper = ttk.Frame(inner, style="Card.TFrame")
        scroll_wrapper._custom_bg = DEEP
        scroll_wrapper.pack(fill="both", expand=True, padx=SP_2, pady=(0, SP_2))

        self.timeline_canvas = tk.Canvas(scroll_wrapper, bg=DEEP, highlightthickness=0, bd=0)
        self.timeline_scrollbar = ttk.Scrollbar(
            scroll_wrapper, orient="vertical", command=self.timeline_canvas.yview
        )
        self.timeline_canvas.configure(yscrollcommand=self.timeline_scrollbar.set)

        self.timeline_content = ttk.Frame(self.timeline_canvas, style="Card.TFrame")
        self.timeline_content._custom_bg = DEEP
        self.timeline_win_id = self.timeline_canvas.create_window(
            (0, 0), window=self.timeline_content, anchor="nw"
        )

        def _on_timeline_configure(event):
            self.timeline_canvas.configure(scrollregion=self.timeline_canvas.bbox("all"))

        def _on_timeline_canvas_configure(event):
            self.timeline_canvas.itemconfig(self.timeline_win_id, width=event.width)

        self.timeline_content.bind("<Configure>", _on_timeline_configure)
        self.timeline_canvas.bind("<Configure>", _on_timeline_canvas_configure)

        def _on_timeline_mousewheel(event):
            try:
                if self.timeline_canvas.winfo_exists():
                    self.timeline_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        self.timeline_canvas.bind(
            "<Enter>", lambda _: self.timeline_canvas.bind_all("<MouseWheel>", _on_timeline_mousewheel)
        )
        self.timeline_canvas.bind(
            "<Leave>", lambda _: self.timeline_canvas.unbind_all("<MouseWheel>")
        )

        self.timeline_canvas.pack(side="left", fill="both", expand=True)
        self.timeline_scrollbar.pack(side="right", fill="y")

    def _build_filter_chips(self, parent: tk.Widget) -> None:
        """Render interactive category filter chips for forensic event sequence."""
        chips_frame = ttk.Frame(parent, style="Card.TFrame")
        chips_frame._custom_bg = DEEP
        chips_frame.pack(fill="x", padx=SP_4, pady=(2, 2))

        ttk.Label(
            chips_frame,
            text="FILTER:",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(side="left", padx=(0, SP_2))

        categories = [
            ("ALL", "ALL"),
            ("AUTH", "AUTH"),
            ("EXEC", "EXEC"),
            ("USB", "USB"),
            ("DELETE", "DELETE"),
            ("AI FINDINGS", "AI FINDINGS"),
        ]

        self._filter_chips = {}
        for code, label in categories:
            btn = tk.Label(
                chips_frame,
                text=label,
                font=(FONT_FALLBACK, FS_XS, "bold"),
                padx=6,
                pady=1,
                cursor="hand2",
                bd=1,
                relief="solid",
                bg=ABYSS,
                fg=TEXT_SECONDARY,
                highlightthickness=1,
                highlightbackground=STEEL,
            )
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, c=code: self._set_timeline_filter(c))
            self._filter_chips[code] = btn

        self._update_filter_chip_styles()

    def _set_timeline_filter(self, category_code: str) -> None:
        """Update active category filter and re-render sequence."""
        self.active_timeline_filter = category_code
        self._update_filter_chip_styles()
        self._render_timeline_entries()

    def _update_filter_chip_styles(self) -> None:
        """Refresh highlight borders and colors across filter chips."""
        for code, btn in self._filter_chips.items():
            if code == self.active_timeline_filter:
                btn.configure(
                    bg=CYAN,
                    fg=VOID,
                    highlightbackground=ICE,
                )
            else:
                btn.configure(
                    bg=ABYSS,
                    fg=TEXT_SECONDARY,
                    highlightbackground=STEEL,
                )

    def _toggle_sort_order(self) -> None:
        """Toggle timeline sorting order between chronological ascending and descending."""
        self.timeline_sort_ascending = not self.timeline_sort_ascending
        btn_text = "[OLDEST FIRST]" if self.timeline_sort_ascending else "[NEWEST FIRST]"
        self.btn_sort_order.config(text=btn_text)
        self._render_timeline_entries()

    def _get_category_node_color(self, category: str, severity: int = 0) -> str:
        """Map event categories to Cyberpunk neon palette indicators."""
        cat = category.lower()
        if cat == "failed_login":
            return PINK
        elif cat == "successful_login":
            return CYAN
        elif cat == "usb_connection":
            return PEACH
        elif cat == "executable_event":
            return PURPLE
        elif cat == "deleted_file":
            return MAGENTA
        elif cat == "finding":
            if severity >= 25:
                return PINK
            elif severity >= 15:
                return PEACH
            return PURPLE
        return CYAN

    def _render_timeline_entries(self) -> None:
        """Render all matching timeline entries onto the scrollable canvas with neon spine lines."""
        for child in self.timeline_content.winfo_children():
            child.destroy()

        if not self.raw_timeline:
            empty_box = ttk.Frame(self.timeline_content, style="Card.TFrame")
            empty_box._custom_bg = DEEP
            empty_box.pack(fill="x", padx=SP_4, pady=SP_4)

            ttk.Label(
                empty_box,
                text="NO TIMELINE EVENTS AVAILABLE",
                foreground=TEXT_SECONDARY,
                background=DEEP,
                font=(FONT_FALLBACK, FS_MD, "bold"),
            ).pack(anchor="w", pady=(0, 2))

            ttk.Label(
                empty_box,
                text="No timeline events available. Run analysis on evidence with timestamps.",
                foreground=TEXT_MUTED,
                background=DEEP,
                font=FONT_BODY,
            ).pack(anchor="w")
            self.lbl_timeline_count.config(text="0 EVENTS")
            return

        # Map filter code to category list
        cat_map = {
            "ALL": None,
            "AUTH": ["failed_login", "successful_login"],
            "EXEC": ["executable_event"],
            "USB": ["usb_connection"],
            "DELETE": ["deleted_file"],
            "AI FINDINGS": ["finding"],
        }
        filter_cats = cat_map.get(self.active_timeline_filter, None)
        filtered = filter_timeline(self.raw_timeline, categories=filter_cats)

        if not self.timeline_sort_ascending:
            filtered = list(reversed(filtered))

        self.lbl_timeline_count.config(text=f"{len(filtered)} EVENTS")

        if not filtered:
            empty_box = ttk.Frame(self.timeline_content, style="Card.TFrame")
            empty_box._custom_bg = DEEP
            empty_box.pack(fill="x", padx=SP_4, pady=SP_4)

            ttk.Label(
                empty_box,
                text="NO MATCHING EVENTS",
                foreground=TEXT_SECONDARY,
                background=DEEP,
                font=(FONT_FALLBACK, FS_MD, "bold"),
            ).pack(anchor="w", pady=(0, 2))

            ttk.Label(
                empty_box,
                text=f"No forensic events match the active '{self.active_timeline_filter}' filter.",
                foreground=TEXT_MUTED,
                background=DEEP,
                font=FONT_BODY,
            ).pack(anchor="w")
            return

        total_items = len(filtered)
        for idx, entry in enumerate(filtered):
            self._render_timeline_row(entry, idx, total_items)

    def _render_timeline_row(self, entry: Dict[str, Any], idx: int, total_items: int) -> None:
        """Render a single event card along the vertical neon spine line."""
        is_first = (idx == 0)
        is_last = (idx == total_items - 1)
        severity = int(entry.get("severity", 0))
        cat = entry.get("category", "info")
        node_color = self._get_category_node_color(cat, severity)

        if severity >= 25:
            accent_col = PINK
        elif severity >= 15:
            accent_col = PEACH
        else:
            accent_col = CYAN

        row = tk.Frame(
            self.timeline_content,
            bg=ABYSS,
            highlightthickness=1,
            highlightbackground=STEEL,
            bd=0,
        )
        row.pack(fill="x", padx=SP_2, pady=2)

        # Left Neon Spine Canvas
        spine_cv = tk.Canvas(row, width=28, bg=ABYSS, highlightthickness=0, bd=0)
        spine_cv.pack(side="left", fill="y")

        def _draw_spine(event, cv=spine_cv, fst=is_first, lst=is_last, col=node_color):
            h = max(28, event.height)
            cv.delete("all")
            # Vertical spine line
            if fst and lst:
                pass
            elif fst:
                cv.create_line(14, 14, 14, h, fill=PLUM, width=2)
            elif lst:
                cv.create_line(14, 0, 14, 14, fill=PLUM, width=2)
            else:
                cv.create_line(14, 0, 14, h, fill=PLUM, width=2)

            # Circular node with outer ring and inner glow
            cv.create_oval(8, 8, 20, 20, fill=col, outline=VOID, width=1)
            cv.create_oval(11, 11, 17, 17, fill=ICE, outline="")

        spine_cv.bind("<Configure>", _draw_spine)

        # Card Content Body
        card_body = tk.Frame(row, bg=ABYSS)
        card_body.pack(side="left", fill="both", expand=True, padx=(SP_1, SP_3), pady=4)

        # Top Metadata Line: Timestamp + Badges
        top_line = tk.Frame(card_body, bg=ABYSS)
        top_line.pack(fill="x", pady=(0, 2))

        ts_text = entry.get("timestamp") or "TIMESTAMP N/A"
        ttk.Label(
            top_line,
            text=ts_text,
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="left", padx=(0, SP_2))

        # Source badge
        source = entry.get("source", "evidence")
        if source == "ai_inference":
            src_badge = create_badge(top_line, "AI INFERENCE", PURPLE, bg=ABYSS)
        else:
            src_badge = create_badge(top_line, "EVIDENCE", CYAN, bg=ABYSS)
        src_badge.pack(side="left", padx=(0, 4))

        # Rule badge if present
        rule_code = entry.get("rule_code")
        if rule_code:
            r_badge = create_badge(top_line, rule_code, PURPLE, bg=ABYSS)
            r_badge.pack(side="left", padx=(0, 4))

        # Severity badge if present
        if severity > 0:
            sev_badge = create_badge(top_line, f"+{severity} PTS", accent_col, bg=ABYSS)
            sev_badge.pack(side="right")

        # Title Line
        title_text = entry.get("title", "Forensic Event")
        ttk.Label(
            card_body,
            text=title_text,
            foreground=TEXT_PRIMARY,
            background=ABYSS,
            font=(FONT_FALLBACK, FS_SM, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        # Description Line
        desc_text = entry.get("description", "")
        if desc_text:
            ttk.Label(
                card_body,
                text=desc_text,
                foreground=TEXT_SECONDARY,
                background=ABYSS,
                font=FONT_SMALL,
                anchor="w",
                wraplength=460,
                justify="left",
            ).pack(fill="x")

        # Raw log line preview if present
        raw_text = entry.get("raw")
        if raw_text:
            raw_preview = raw_text.strip()
            if len(raw_preview) > 100:
                raw_preview = raw_preview[:97] + "..."
            ttk.Label(
                card_body,
                text=f"RAW: {raw_preview}",
                foreground=TEXT_MUTED,
                background=ABYSS,
                font=FONT_MONO_SM,
                anchor="w",
                wraplength=460,
                justify="left",
            ).pack(fill="x", pady=(2, 0))

    # -------------------------------------------------------------------------
    # Section D: Forward Chaining Reasoning Trace Terminal
    # -------------------------------------------------------------------------

    def _build_trace_panel(self) -> None:
        """Render the dark monospace terminal displaying the deduction proof log."""
        glass = create_glass_frame(
            self.right_column, width=580, height=150, border_color=PURPLE, fill_color=ABYSS
        )
        glass.pack(fill="both", expand=True)
        inner = glass.inner_frame

        # Terminal Header
        hdr_row = ttk.Frame(inner, style="Panel.TFrame")
        hdr_row._custom_bg = ABYSS
        hdr_row.pack(fill="x", padx=SP_4, pady=(SP_2, 2))

        create_section_header(hdr_row, "EXPLAINABLE INFERENCE PROOF LOG").pack(side="left")

        ttk.Label(
            hdr_row,
            text="FORWARD CHAINING PROOF TRACE",
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="right")

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(2, 4))

        # Monospace Text Box
        term_frame = ttk.Frame(inner, style="Panel.TFrame")
        term_frame._custom_bg = ABYSS
        term_frame.pack(fill="both", expand=True, padx=SP_3, pady=(0, SP_2))

        self.txt_trace = tk.Text(
            term_frame,
            bg=VOID,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            font=FONT_MONO_SM,
            highlightthickness=1,
            highlightbackground=PLUM,
            highlightcolor=PURPLE,
            wrap="word",
        )
        trace_scroll = ttk.Scrollbar(term_frame, orient="vertical", command=self.txt_trace.yview)
        self.txt_trace.configure(yscrollcommand=trace_scroll.set)

        # Syntax Highlighting Tags
        self.txt_trace.tag_configure("iteration", foreground=PURPLE, font=(FONT_MONO_FALLBACK, FS_SM, "bold"))
        self.txt_trace.tag_configure("rule", foreground=CYAN, font=(FONT_MONO_FALLBACK, FS_SM, "bold"))
        self.txt_trace.tag_configure("fact", foreground=PEACH)
        self.txt_trace.tag_configure("expl", foreground=TEXT_SECONDARY)
        self.txt_trace.tag_configure("summary", foreground=ICE, font=(FONT_MONO_FALLBACK, FS_SM, "bold"))
        self.txt_trace.tag_configure("info", foreground=TEXT_MUTED)

        self.txt_trace.pack(side="left", fill="both", expand=True)
        trace_scroll.pack(side="right", fill="y")

    # -------------------------------------------------------------------------
    # Analysis Execution & Database Integration
    # -------------------------------------------------------------------------

    def run_analysis(self) -> None:
        """
        Dynamically execute log analysis, forward chaining reasoning,
        and database synchronization.
        """
        if self._is_analyzing:
            return

        self._is_analyzing = True
        self.btn_run.config(cursor="watch")
        self.update_idletasks()

        try:
            # 1. Resolve active case context
            target_case_id = self.case_id
            if target_case_id is None and self.shell and getattr(self.shell, "selected_case_id", None):
                target_case_id = self.shell.selected_case_id
                self.case_id = target_case_id

            evidence_items = []
            if target_case_id is not None:
                evidence_items = get_evidence_for_case(target_case_id)

            # 2. Extract facts from evidence artifacts
            merged_facts = {
                "evidence_type": "log",
                "total_lines": 0,
                "failed_logins": 0,
                "successful_logins": 0,
                "usb_connections": 0,
                "executable_events": 0,
                "deleted_files": 0,
                "suspicious_domains": 0,
                "unknown_sender": False,
                "executable_attachment": False,
                "ip_addresses": [],
                "users_flagged": [],
                "timeline_events": [],
            }

            all_ips = set()
            all_users = set()
            evidence_found = False

            for item in evidence_items:
                f_path = item.get("file_path", "")
                if f_path and os.path.exists(f_path):
                    try:
                        facts = parse_log_file(f_path)
                        evidence_found = True
                        merged_facts["total_lines"] += facts.get("total_lines", 0)
                        merged_facts["failed_logins"] += facts.get("failed_logins", 0)
                        merged_facts["successful_logins"] += facts.get("successful_logins", 0)
                        merged_facts["usb_connections"] += facts.get("usb_connections", 0)
                        merged_facts["executable_events"] += facts.get("executable_events", 0)
                        merged_facts["deleted_files"] += facts.get("deleted_files", 0)
                        merged_facts["suspicious_domains"] += facts.get("suspicious_domains", 0)
                        for ip in facts.get("ip_addresses", []):
                            all_ips.add(ip)
                        for u in facts.get("users_flagged", []):
                            all_users.add(u)
                        merged_facts["timeline_events"].extend(facts.get("timeline_events", []))
                    except Exception:
                        pass

            # Fallback to sample_evidence/system.log if case has no uploaded logs yet
            if not evidence_found:
                sample_log = os.path.join(PROJECT_ROOT, "sample_evidence", "system.log")
                if os.path.exists(sample_log):
                    facts = parse_log_file(sample_log)
                    merged_facts = facts
                    for ip in facts.get("ip_addresses", []):
                        all_ips.add(ip)
                    for u in facts.get("users_flagged", []):
                        all_users.add(u)

            merged_facts["ip_addresses"] = sorted(list(all_ips))
            merged_facts["users_flagged"] = sorted(list(all_users))
            self.latest_facts = merged_facts

            # 3. Execute Forward Chaining Inference Engine
            engine = ForwardChainingEngine()
            result = engine.evaluate(merged_facts)
            self.latest_result = result

            # 4. Compile Chronological Event Sequence Timeline
            self.raw_timeline = build_timeline(merged_facts, result.get("findings", []))

            # 5. Synchronize findings with SQLite
            if target_case_id is not None:
                clear_findings_for_case(target_case_id)
                for f in result["findings"]:
                    add_finding(
                        case_id=target_case_id,
                        rule_code=f["rule_code"],
                        finding=f"{f['name']}: {f['description']}",
                        severity=f["severity"],
                    )

            # 6. Update UI View
            self._render_analysis_state(merged_facts, result)

        finally:
            self._is_analyzing = False
            self.btn_run.config(cursor="hand2")

    def _render_analysis_state(self, facts: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Update all visual panels with inference results."""
        # 1. Update Header Badges, Risk Score & Gauge
        risk_score = result.get("risk_score", 0)
        risk_lvl = result.get("risk_level", "LOW")
        r_color = risk_color(risk_score)

        self.lbl_risk_score.config(text=f"SCORE: {risk_score} / 100", foreground=r_color)

        for child in self.risk_badge_container.winfo_children():
            child.destroy()
        badge = create_badge(self.risk_badge_container, f"RISK: {risk_lvl}", r_color, bg=DEEP)
        badge.pack(side="left")

        # Animate the compact header gauge
        self.header_gauge.set_score(risk_score, level=risk_lvl, animate=True)

        # 2. Update Section A Metrics
        for key, lbl in self.fact_metric_labels.items():
            val = facts.get(key, 0)
            lbl.config(text=str(val))

        ips = facts.get("ip_addresses", [])
        self.lbl_ips.config(text=", ".join(ips) if ips else "None detected")

        users = facts.get("users_flagged", [])
        self.lbl_users.config(text=", ".join(users) if users else "None detected")

        # 3. Update Section B Findings List
        findings = result.get("findings", [])
        self.lbl_findings_count.config(text=f"{len(findings)} FINDINGS")

        for child in self.findings_content.winfo_children():
            child.destroy()

        if not findings:
            empty_box = ttk.Frame(self.findings_content, style="Card.TFrame")
            empty_box._custom_bg = DEEP
            empty_box.pack(fill="x", padx=SP_4, pady=SP_6)

            ttk.Label(
                empty_box,
                text="NO RISK FINDINGS DERIVED",
                foreground=TEXT_SECONDARY,
                background=DEEP,
                font=(FONT_FALLBACK, FS_MD, "bold"),
            ).pack(anchor="w", pady=(0, 2))

            ttk.Label(
                empty_box,
                text="Forward Chaining rules evaluated without triggering risk thresholds.",
                foreground=TEXT_MUTED,
                background=DEEP,
                font=FONT_BODY,
            ).pack(anchor="w")
        else:
            for item in findings:
                self._render_finding_card(item)

        # 4. Update Section C Proof Terminal
        self.txt_trace.config(state="normal")
        self.txt_trace.delete("1.0", tk.END)

        self.txt_trace.insert(tk.END, "=== FORWARD CHAINING DEDUCTION EXECUTION ===\n\n", "summary")

        for step in result.get("reasoning_trace", []):
            it = step["iteration"]
            code = step["rule_code"]
            name = step["name"]
            fact = step["derived_fact"]
            sev = step["severity_added"]
            expl = step["explanation"]

            self.txt_trace.insert(tk.END, f"[ITERATION {it}] ", "iteration")
            self.txt_trace.insert(tk.END, f"Rule {code} ({name}) FIRED (+{sev} pts)\n", "rule")
            self.txt_trace.insert(tk.END, f"             --> Asserted Fact : {fact} = True\n", "fact")
            self.txt_trace.insert(tk.END, f"             --> Proof Logic   : {expl}\n\n", "expl")

        conv_iter = result.get("iterations_to_fixpoint", 1)
        tot_sev = result.get("total_severity", 0)
        self.txt_trace.insert(tk.END, f"[CONVERGENCE] Fixpoint reached in {conv_iter} inference iteration(s).\n", "summary")
        self.txt_trace.insert(
            tk.END,
            f"[OUTCOME] Total Severity: {tot_sev} | Normalized Score: {risk_score}/100 | Level: {risk_lvl}\n",
            "summary",
        )
        self.txt_trace.config(state="disabled")

        # 5. Update Section C Chronological Timeline Sequence
        self._render_timeline_entries()

    def _render_finding_card(self, finding: Dict[str, Any]) -> None:
        """Render a single derived finding card with proof breakdown."""
        severity = int(finding.get("severity", 0))
        if severity >= 25:
            accent_col = PINK
        elif severity >= 15:
            accent_col = PEACH
        else:
            accent_col = CYAN

        card = tk.Frame(
            self.findings_content,
            bg=ABYSS,
            highlightthickness=1,
            highlightbackground=STEEL,
            bd=0,
        )
        card.pack(fill="x", padx=SP_2, pady=SP_2)

        # Left color bar
        accent_bar = tk.Canvas(card, width=4, bg=accent_col, highlightthickness=0, bd=0)
        accent_bar.pack(side="left", fill="y")

        card_body = tk.Frame(card, bg=ABYSS)
        card_body.pack(side="left", fill="both", expand=True, padx=SP_3, pady=SP_2)

        # Top Line: Rule Badge + Title + Severity Weight
        top_line = tk.Frame(card_body, bg=ABYSS)
        top_line.pack(fill="x", pady=(0, 2))

        rule_badge = create_badge(top_line, finding.get("rule_code", "R000"), PURPLE, bg=ABYSS)
        rule_badge.pack(side="left", padx=(0, SP_2))

        ttk.Label(
            top_line,
            text=finding.get("name", "Unknown Finding"),
            foreground=TEXT_PRIMARY,
            background=ABYSS,
            font=(FONT_FALLBACK, FS_BASE, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        sev_badge = create_badge(top_line, f"+{severity} PTS", accent_col, bg=ABYSS)
        sev_badge.pack(side="right")

        # Description
        ttk.Label(
            card_body,
            text=finding.get("description", ""),
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_SMALL,
            anchor="w",
            wraplength=480,
            justify="left",
        ).pack(fill="x", pady=(0, 4))

        # Explanation / Proof Box
        proof_box = tk.Frame(card_body, bg=DEEP, padx=6, pady=4)
        proof_box.pack(fill="x")

        ttk.Label(
            proof_box,
            text="WHY THIS FIRED (FACT PROOF):",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
            anchor="w",
        ).pack(fill="x")

        ttk.Label(
            proof_box,
            text=finding.get("explanation", ""),
            foreground=ICE,
            background=DEEP,
            font=FONT_MONO_SM,
            wraplength=460,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(1, 0))

    def _handle_clear_findings(self) -> None:
        """Clear findings from database and reset screen state."""
        if self.case_id is not None:
            clear_findings_for_case(self.case_id)

        self.latest_facts = {}
        self.latest_result = {}

        # Reset badges & headers
        for child in self.risk_badge_container.winfo_children():
            child.destroy()
        badge = create_badge(self.risk_badge_container, "RISK: --", TEXT_MUTED, bg=DEEP)
        badge.pack(side="left")
        self.lbl_risk_score.config(text="SCORE: -- / 100", foreground=TEXT_SECONDARY)

        # Reset fact counters
        for lbl in self.fact_metric_labels.values():
            lbl.config(text="--")
        self.lbl_ips.config(text="None detected")
        self.lbl_users.config(text="None detected")

        # Reset findings
        self.lbl_findings_count.config(text="0 FINDINGS")
        for child in self.findings_content.winfo_children():
            child.destroy()

        empty_box = ttk.Frame(self.findings_content, style="Card.TFrame")
        empty_box._custom_bg = DEEP
        empty_box.pack(fill="x", padx=SP_4, pady=SP_6)

        ttk.Label(
            empty_box,
            text="NO ANALYSIS PERFORMED YET",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_MD, "bold"),
        ).pack(anchor="w", pady=(0, 2))

        ttk.Label(
            empty_box,
            text="Click [RUN FORWARD CHAINING ANALYSIS] to evaluate forensic evidence.",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_BODY,
        ).pack(anchor="w")

        # Reset terminal trace
        self.txt_trace.config(state="normal")
        self.txt_trace.delete("1.0", tk.END)
        self.txt_trace.insert(
            tk.END,
            "[STANDBY] Findings cleared. Ready to execute forward chaining analysis.\n",
            "info",
        )
        self.txt_trace.config(state="disabled")

        # Reset timeline
        self.raw_timeline = []
        self._render_timeline_entries()

    def refresh_data(self) -> None:
        """Refresh active case header context and reload saved findings if available."""
        # 1. Update Case Context Badge
        case = get_case_by_id(self.case_id) if self.case_id is not None else None

        for child in self.case_badge_container.winfo_children():
            child.destroy()

        if case:
            c_text = f"CASE: {case['case_number']}"
            c_badge = create_badge(self.case_badge_container, c_text, CYAN, bg=DEEP)
            c_badge.pack(side="left")
        else:
            c_badge = create_badge(self.case_badge_container, "NO ACTIVE CASE", TEXT_MUTED, bg=DEEP)
            c_badge.pack(side="left")

        # 2. Check existing findings in SQLite
        if self.case_id is not None:
            db_findings = get_findings_for_case(self.case_id)
            if db_findings and not self.latest_result:
                # Reconstruct findings view from SQLite
                tot_sev = sum(f["severity"] for f in db_findings)
                score = min(100, tot_sev)
                r_color = risk_color(score)
                r_lbl = risk_label(score)

                self.lbl_risk_score.config(text=f"SCORE: {score} / 100", foreground=r_color)
                for child in self.risk_badge_container.winfo_children():
                    child.destroy()
                badge = create_badge(self.risk_badge_container, f"RISK: {r_lbl}", r_color, bg=DEEP)
                badge.pack(side="left")

                # Animate the header gauge for the loaded DB findings
                self.header_gauge.set_score(score, level=r_lbl, animate=True)

                self.lbl_findings_count.config(text=f"{len(db_findings)} FINDINGS")
                for child in self.findings_content.winfo_children():
                    child.destroy()

                parsed_findings_for_timeline = []
                for f in db_findings:
                    parsed_item = {
                        "rule_code": f["rule_code"],
                        "name": f["finding"].split(":")[0] if ":" in f["finding"] else f["finding"],
                        "description": f["finding"],
                        "severity": f["severity"],
                        "explanation": f"Persisted rule finding retrieved from forensic database (Rule {f['rule_code']}).",
                    }
                    self._render_finding_card(parsed_item)
                    parsed_findings_for_timeline.append(parsed_item)

                self.raw_timeline = build_timeline({"timeline_events": []}, parsed_findings_for_timeline)
                self._render_timeline_entries()
                return

        if not self.latest_result:
            self._handle_clear_findings()

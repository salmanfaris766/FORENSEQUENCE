# =============================================================================
# gui/analysis_frame.py
# FORENSEQUENCE - Forward Chaining AI Reasoning & Analysis Screen
# =============================================================================

from __future__ import annotations

import os
import tkinter as tk
from typing import Optional, Callable, Dict, Any, List
import ttkbootstrap as ttk

from gui.risk_gauge_widget import CyberpunkRiskGauge
from analysis.risk_engine import calculate_risk

from gui.theme import (
    APP_BG,
    BG_SECONDARY,
    PANEL_BG,
    PANEL_ELEVATED,
    PANEL_HOVER,
    BORDER,
    BORDER_SECONDARY,
    MINT,
    CYAN,
    CYAN_GLOW,
    TEAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    CRITICAL,
    HIGH,
    MEDIUM,
    LOW,
    FONT_FALLBACK,
    FONT_MONO_FALLBACK,
    FS_XS,
    FS_SM,
    FS_BASE,
    FS_MD,
    FS_LG,
    FS_XL,
    SP_1,
    SP_2,
    SP_3,
    SP_4,
    SP_6,
    SP_8,
    create_soc_panel,
    create_soc_button,
    create_soc_badge,
    create_section_header,
    create_divider,
    risk_color,
    risk_label,
    # Backward compatibility aliases
    VOID,
    ABYSS,
    DEEP,
    STEEL,
    create_glass_frame,
    create_neon_button,
    create_badge,
)

from analyzers import parse_evidence_item, merge_facts_list
from analyzers.dispatcher import detect_evidence_type
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
        # 1. Header Bar
        # ---------------------------------------------------------------------
        self.header_bar = ttk.Frame(self, style="TFrame")
        self.header_bar.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))

        ttk.Label(
            self.header_bar,
            text="OPERATIONS / AI THREAT ANALYSIS",
            foreground=TEXT_MUTED,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_XS, "normal"),
        ).pack(anchor="w")

        title_row = ttk.Frame(self.header_bar, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, 0))

        ttk.Label(
            title_row,
            text="Forward Chaining Reasoning Engine",
            foreground=TEXT_PRIMARY,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_XL, "bold"),
        ).pack(side="left")

        badge = create_soc_badge(title_row, "EXPERT SYSTEM INFERENCE", color=MINT, bg=APP_BG)
        badge.pack(side="left", padx=(SP_4, 0))

        ttk.Label(
            self.header_bar,
            text="Deterministic propositional inference, explainable proof traces, and forensic event reconstruction.",
            foreground=TEXT_MUTED,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
        ).pack(anchor="w", pady=(2, 0))

        create_divider(self, color=BORDER).pack(fill="x", padx=SP_6, pady=(SP_3, SP_3))

        # ---------------------------------------------------------------------
        # 2. Top Control Bar (SOC Panel)
        # ---------------------------------------------------------------------
        ctrl_card = create_soc_panel(
            self, width=960, height=115, border_color=BORDER, bg=PANEL_BG
        )
        ctrl_card.pack(fill="x", padx=SP_6, pady=(0, SP_3))
        inner_h = ctrl_card.inner_frame

        # Left Header Block: Case Context + Risk Badges + Score
        left_h = ttk.Frame(inner_h, style="Card.TFrame")
        left_h._custom_bg = PANEL_BG
        left_h.pack(side="left", fill="both", expand=True, padx=SP_4, pady=SP_2)

        create_section_header(left_h, "ACTIVE INVESTIGATION ANALYSIS CONTROLS").pack(anchor="w")

        info_row = ttk.Frame(left_h, style="Card.TFrame")
        info_row._custom_bg = PANEL_BG
        info_row.pack(anchor="w", pady=(SP_2, 0))

        # Case Context Badge
        self.case_badge_container = ttk.Frame(info_row, style="Card.TFrame")
        self.case_badge_container._custom_bg = PANEL_BG
        self.case_badge_container.pack(side="left", padx=(0, SP_2))
        self.badge_case = create_soc_badge(self.case_badge_container, "NO ACTIVE CASE", color=TEXT_MUTED, bg=PANEL_BG)
        self.badge_case.pack(side="left")

        # Risk Band Badge
        self.risk_badge_container = ttk.Frame(info_row, style="Card.TFrame")
        self.risk_badge_container._custom_bg = PANEL_BG
        self.risk_badge_container.pack(side="left", padx=(0, SP_3))
        self.badge_risk = create_soc_badge(self.risk_badge_container, "RISK: --", color=TEXT_MUTED, bg=PANEL_BG)
        self.badge_risk.pack(side="left")

        # Numeric Risk Score Display
        self.lbl_risk_score = ttk.Label(
            info_row,
            text="SCORE: -- / 100",
            foreground=TEXT_SECONDARY,
            background=PANEL_BG,
            font=(FONT_MONO_FALLBACK, FS_BASE, "bold"),
        )
        self.lbl_risk_score.pack(side="left")

        # Center: Compact Cyberpunk Risk Gauge
        gauge_frame = ttk.Frame(inner_h, style="Card.TFrame")
        gauge_frame._custom_bg = PANEL_BG
        gauge_frame.pack(side="left", fill="y", padx=SP_3, pady=SP_1)

        self.header_gauge = CyberpunkRiskGauge(
            gauge_frame,
            size=130,
            score=0,
            compact=True,
            bg=PANEL_BG,
        )
        self.header_gauge.pack()

        # Right Action Bar: [RUN FORWARD CHAINING ANALYSIS] & [CLEAR FINDINGS]
        right_h = ttk.Frame(inner_h, style="Card.TFrame")
        right_h._custom_bg = PANEL_BG
        right_h.pack(side="right", fill="y", padx=SP_4, pady=SP_2)

        self.btn_run = create_soc_button(
            right_h,
            text="[RUN FORWARD CHAINING ANALYSIS]",
            command=self.run_analysis,
            variant="primary",
            bg=PANEL_BG,
        )
        self.btn_run.pack(side="top", fill="x", pady=(0, 4))

        self.btn_clear = create_soc_button(
            right_h,
            text="[CLEAR FINDINGS]",
            command=self._handle_clear_findings,
            variant="ghost",
            bg=PANEL_BG,
        )
        self.btn_clear.pack(side="top", fill="x")

        # ---------------------------------------------------------------------
        # 3. Main Two-Column Content Workspace
        # ---------------------------------------------------------------------
        self.body_container = ttk.Frame(self, style="TFrame")
        self.body_container.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_4))
        self.body_container.grid_rowconfigure(0, weight=1)
        self.body_container.grid_columnconfigure(0, weight=4)
        self.body_container.grid_columnconfigure(1, weight=6)

        # --- Left Column (40% width): Section A - Extracted Evidence Facts ---
        self.left_column = ttk.Frame(self.body_container, style="TFrame")
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=(0, SP_3))

        self._build_facts_panel()

        # --- Right Column (60% width): Section B, Section C & Section D ---
        self.right_column = ttk.Frame(self.body_container, style="TFrame")
        self.right_column.grid(row=0, column=1, sticky="nsew")

        self._build_findings_panel()
        self._build_timeline_panel()
        self._build_trace_panel()

    # -------------------------------------------------------------------------
    # Section A: Extracted Evidence Facts
    # -------------------------------------------------------------------------

    def _build_facts_panel(self) -> None:
        """Render the multi-source evidence facts metric panel."""
        panel = create_soc_panel(
            self.left_column, width=380, height=530, border_color=BORDER, bg=PANEL_BG
        )
        panel.pack(fill="both", expand=True)
        inner = panel.inner_frame

        create_section_header(inner, "EXTRACTED EVIDENCE FACTS").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )

        ttk.Label(
            inner,
            text="Deterministic signals harvested across multi-source evidence artifacts.",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
            wraplength=340,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_2))

        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(0, SP_2))

        # Scrollable container for facts
        scroll_wrapper = ttk.Frame(inner, style="Card.TFrame")
        scroll_wrapper._custom_bg = PANEL_BG
        scroll_wrapper.pack(fill="both", expand=True, padx=SP_2, pady=(0, SP_3))

        self.facts_canvas = tk.Canvas(scroll_wrapper, bg=PANEL_BG, highlightthickness=0, bd=0)
        self.facts_scrollbar = ttk.Scrollbar(
            scroll_wrapper, orient="vertical", command=self.facts_canvas.yview
        )
        self.facts_canvas.configure(yscrollcommand=self.facts_scrollbar.set)

        self.facts_content = ttk.Frame(self.facts_canvas, style="Card.TFrame")
        self.facts_content._custom_bg = PANEL_BG
        self.facts_window_id = self.facts_canvas.create_window(
            (0, 0), window=self.facts_content, anchor="nw"
        )

        def _on_facts_content_configure(event):
            self.facts_canvas.configure(scrollregion=self.facts_canvas.bbox("all"))

        def _on_facts_canvas_configure(event):
            self.facts_canvas.itemconfig(self.facts_window_id, width=event.width)

        self.facts_content.bind("<Configure>", _on_facts_content_configure)
        self.facts_canvas.bind("<Configure>", _on_facts_canvas_configure)

        def _on_facts_mousewheel(event):
            try:
                if self.facts_canvas.winfo_exists():
                    self.facts_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        self.facts_canvas.bind("<Enter>", lambda _: self.facts_canvas.bind_all("<MouseWheel>", _on_facts_mousewheel))
        self.facts_canvas.bind("<Leave>", lambda _: self.facts_canvas.unbind_all("<MouseWheel>"))

        self.facts_canvas.pack(side="left", fill="both", expand=True)
        self.facts_scrollbar.pack(side="right", fill="y")

        # 1. Multi-Source Ingestion Badges Row
        src_row = tk.Frame(self.facts_content, bg=PANEL_ELEVATED, highlightthickness=1, highlightbackground=BORDER, bd=0)
        src_row.pack(fill="x", padx=SP_2, pady=(0, SP_2))

        ttk.Label(
            src_row,
            text="EVIDENCE SOURCES INGESTED",
            foreground=TEXT_SECONDARY,
            background=PANEL_ELEVATED,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_3, pady=(4, 2))

        badges_flow = tk.Frame(src_row, bg=PANEL_ELEVATED)
        badges_flow.pack(fill="x", padx=SP_2, pady=(0, 4))

        self.badge_src_log_container = tk.Frame(badges_flow, bg=PANEL_ELEVATED)
        self.badge_src_log_container.pack(side="left", padx=2, pady=1)
        self.badge_src_log = create_soc_badge(self.badge_src_log_container, "LOG: 0", color=CYAN, bg=PANEL_ELEVATED)
        self.badge_src_log.pack()

        self.badge_src_file_container = tk.Frame(badges_flow, bg=PANEL_ELEVATED)
        self.badge_src_file_container.pack(side="left", padx=2, pady=1)
        self.badge_src_file = create_soc_badge(self.badge_src_file_container, "FILE: 0", color=HIGH, bg=PANEL_ELEVATED)
        self.badge_src_file.pack()

        self.badge_src_browser_container = tk.Frame(badges_flow, bg=PANEL_ELEVATED)
        self.badge_src_browser_container.pack(side="left", padx=2, pady=1)
        self.badge_src_browser = create_soc_badge(self.badge_src_browser_container, "BROWSER: 0", color=TEAL, bg=PANEL_ELEVATED)
        self.badge_src_browser.pack()

        self.badge_src_email_container = tk.Frame(badges_flow, bg=PANEL_ELEVATED)
        self.badge_src_email_container.pack(side="left", padx=2, pady=1)
        self.badge_src_email = create_soc_badge(self.badge_src_email_container, "EMAIL: 0", color=CRITICAL, bg=PANEL_ELEVATED)
        self.badge_src_email.pack()

        # 2. Metric spec cards
        self.fact_metric_labels = {}
        metrics_spec = [
            ("failed_logins", "FAILED AUTH ATTEMPTS", CYAN),
            ("successful_logins", "SUCCESSFUL LOGINS", MINT),
            ("usb_connections", "USB MEDIA ATTACHMENTS", HIGH),
            ("executable_events", "SUSPICIOUS EXECUTIONS", CRITICAL),
            ("deleted_files", "FILE DELETION EVENTS", CRITICAL),
            ("suspicious_domains", "SUSPICIOUS DOMAINS / BEACONS", HIGH),
            ("hidden_files", "HIDDEN FORENSIC FILES", HIGH),
            ("autorun_entries", "AUTORUN PERSISTENCE ARTIFACTS", TEAL),
            ("unknown_sender_count", "UNKNOWN SENDER EMAILS", CRITICAL),
            ("executable_attachment_count", "EXECUTABLE ATTACHMENTS", CRITICAL),
            ("urgent_subjects_count", "URGENT / COERCIVE EMAILS", HIGH),
            ("suspicious_searches_count", "SUSPICIOUS SEARCH QUERIES", CYAN),
        ]

        for key, title, col in metrics_spec:
            row = tk.Frame(self.facts_content, bg=PANEL_ELEVATED, highlightthickness=1, highlightbackground=BORDER, bd=0)
            row.pack(fill="x", padx=SP_2, pady=2)

            ttk.Label(
                row,
                text=title,
                foreground=TEXT_SECONDARY,
                background=PANEL_ELEVATED,
                font=(FONT_FALLBACK, FS_XS, "bold"),
            ).pack(side="left", padx=SP_3, pady=4)

            lbl_val = ttk.Label(
                row,
                text="--",
                foreground=col,
                background=PANEL_ELEVATED,
                font=(FONT_MONO_FALLBACK, FS_BASE, "bold"),
            )
            lbl_val.pack(side="right", padx=SP_3, pady=4)
            self.fact_metric_labels[key] = lbl_val

        # Flagged IPs
        chip_box = tk.Frame(self.facts_content, bg=PANEL_ELEVATED, highlightthickness=1, highlightbackground=BORDER, bd=0)
        chip_box.pack(fill="x", padx=SP_2, pady=(SP_2, 2))
        ttk.Label(
            chip_box,
            text="FLAGGED IP ADDRESSES",
            foreground=TEXT_SECONDARY,
            background=PANEL_ELEVATED,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_3, pady=(4, 1))
        self.lbl_ips = ttk.Label(
            chip_box,
            text="None detected",
            foreground=CYAN,
            background=PANEL_ELEVATED,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
            wraplength=330,
        )
        self.lbl_ips.pack(anchor="w", padx=SP_3, pady=(0, 4))

        # Flagged Users
        user_box = tk.Frame(self.facts_content, bg=PANEL_ELEVATED, highlightthickness=1, highlightbackground=BORDER, bd=0)
        user_box.pack(fill="x", padx=SP_2, pady=2)
        ttk.Label(
            user_box,
            text="FLAGGED USER ACCOUNTS",
            foreground=TEXT_SECONDARY,
            background=PANEL_ELEVATED,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_3, pady=(4, 1))
        self.lbl_users = ttk.Label(
            user_box,
            text="None detected",
            foreground=MINT,
            background=PANEL_ELEVATED,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
            wraplength=330,
        )
        self.lbl_users.pack(anchor="w", padx=SP_3, pady=(0, 4))

        # Flagged Domains & URLs
        url_box = tk.Frame(self.facts_content, bg=PANEL_ELEVATED, highlightthickness=1, highlightbackground=BORDER, bd=0)
        url_box.pack(fill="x", padx=SP_2, pady=2)
        ttk.Label(
            url_box,
            text="FLAGGED DOMAINS & EXFIL URLS",
            foreground=TEXT_SECONDARY,
            background=PANEL_ELEVATED,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_3, pady=(4, 1))
        self.lbl_urls = ttk.Label(
            url_box,
            text="None detected",
            foreground=HIGH,
            background=PANEL_ELEVATED,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
            wraplength=330,
        )
        self.lbl_urls.pack(anchor="w", padx=SP_3, pady=(0, 4))

        # Malicious Email Senders
        mail_box = tk.Frame(self.facts_content, bg=PANEL_ELEVATED, highlightthickness=1, highlightbackground=BORDER, bd=0)
        mail_box.pack(fill="x", padx=SP_2, pady=(2, SP_3))
        ttk.Label(
            mail_box,
            text="MALICIOUS EMAIL SENDER VECTORS",
            foreground=TEXT_SECONDARY,
            background=PANEL_ELEVATED,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_3, pady=(4, 1))
        self.lbl_emails = ttk.Label(
            mail_box,
            text="None detected",
            foreground=CRITICAL,
            background=PANEL_ELEVATED,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
            wraplength=330,
        )
        self.lbl_emails.pack(anchor="w", padx=SP_3, pady=(0, 4))

    # -------------------------------------------------------------------------
    # Section B: Derived Forensic Findings
    # -------------------------------------------------------------------------

    def _build_findings_panel(self) -> None:
        """Render the scrollable list of derived findings with proof cards."""
        panel = create_soc_panel(
            self.right_column, width=580, height=210, border_color=BORDER, bg=PANEL_BG
        )
        panel.pack(fill="both", expand=True, pady=(0, SP_2))
        inner = panel.inner_frame

        # Header Row
        hdr_row = ttk.Frame(inner, style="Card.TFrame")
        hdr_row._custom_bg = PANEL_BG
        hdr_row.pack(fill="x", padx=SP_4, pady=(SP_3, SP_1))

        create_section_header(hdr_row, "DERIVED FORENSIC FINDINGS").pack(side="left")

        self.lbl_findings_count = ttk.Label(
            hdr_row,
            text="0 FINDINGS",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
        )
        self.lbl_findings_count.pack(side="right")

        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(0, SP_2))

        # Scrollable container for findings
        scroll_wrapper = ttk.Frame(inner, style="Card.TFrame")
        scroll_wrapper._custom_bg = PANEL_BG
        scroll_wrapper.pack(fill="both", expand=True, padx=SP_2, pady=(0, SP_2))

        self.findings_canvas = tk.Canvas(scroll_wrapper, bg=PANEL_BG, highlightthickness=0, bd=0)
        self.findings_scrollbar = ttk.Scrollbar(
            scroll_wrapper, orient="vertical", command=self.findings_canvas.yview
        )
        self.findings_canvas.configure(yscrollcommand=self.findings_scrollbar.set)

        self.findings_content = ttk.Frame(self.findings_canvas, style="Card.TFrame")
        self.findings_content._custom_bg = PANEL_BG
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
        """Render the scrollable chronological timeline sequence with filter chips and SOC spine."""
        panel = create_soc_panel(
            self.right_column, width=580, height=230, border_color=BORDER, bg=PANEL_BG
        )
        panel.pack(fill="both", expand=True, pady=(0, SP_2))
        inner = panel.inner_frame

        # Header Row: Title + Sort Toggle + Event Count
        hdr_row = ttk.Frame(inner, style="Card.TFrame")
        hdr_row._custom_bg = PANEL_BG
        hdr_row.pack(fill="x", padx=SP_4, pady=(SP_2, 2))

        create_section_header(hdr_row, "CHRONOLOGICAL EVENT SEQUENCE").pack(side="left")

        right_hdr = ttk.Frame(hdr_row, style="Card.TFrame")
        right_hdr._custom_bg = PANEL_BG
        right_hdr.pack(side="right")

        self.btn_sort_order = tk.Label(
            right_hdr,
            text="[OLDEST FIRST]",
            font=(FONT_FALLBACK, FS_XS, "bold"),
            bg=PANEL_ELEVATED,
            fg=CYAN,
            cursor="hand2",
            padx=6,
            pady=2,
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.btn_sort_order.pack(side="left", padx=(0, SP_2))
        self.btn_sort_order.bind("<Enter>", lambda _: self.btn_sort_order.configure(fg=MINT, bg=PANEL_HOVER))
        self.btn_sort_order.bind("<Leave>", lambda _: self.btn_sort_order.configure(fg=CYAN, bg=PANEL_ELEVATED))
        self.btn_sort_order.bind("<Button-1>", lambda _: self._toggle_sort_order())

        self.lbl_timeline_count = ttk.Label(
            right_hdr,
            text="0 EVENTS",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
        )
        self.lbl_timeline_count.pack(side="left")

        # Category Filter Chips Bar
        self._build_filter_chips(inner)

        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(2, SP_2))

        # Scrollable container for timeline events
        scroll_wrapper = ttk.Frame(inner, style="Card.TFrame")
        scroll_wrapper._custom_bg = PANEL_BG
        scroll_wrapper.pack(fill="both", expand=True, padx=SP_2, pady=(0, SP_2))

        self.timeline_canvas = tk.Canvas(scroll_wrapper, bg=PANEL_BG, highlightthickness=0, bd=0)
        self.timeline_scrollbar = ttk.Scrollbar(
            scroll_wrapper, orient="vertical", command=self.timeline_canvas.yview
        )
        self.timeline_canvas.configure(yscrollcommand=self.timeline_scrollbar.set)

        self.timeline_content = ttk.Frame(self.timeline_canvas, style="Card.TFrame")
        self.timeline_content._custom_bg = PANEL_BG
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
        chips_frame._custom_bg = PANEL_BG
        chips_frame.pack(fill="x", padx=SP_4, pady=(2, 2))

        ttk.Label(
            chips_frame,
            text="FILTER:",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(side="left", padx=(0, SP_2))

        categories = [
            ("ALL", "ALL"),
            ("AUTH", "AUTH"),
            ("EXEC", "EXEC"),
            ("USB", "USB"),
            ("DELETE", "DELETE"),
            ("WEB", "WEB"),
            ("EMAIL", "EMAIL"),
            ("FILES", "FILES"),
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
                bd=0,
                bg=PANEL_ELEVATED,
                fg=TEXT_SECONDARY,
                highlightthickness=1,
                highlightbackground=BORDER,
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
                    bg=MINT,
                    fg=APP_BG,
                    highlightbackground=MINT,
                )
            else:
                btn.configure(
                    bg=PANEL_ELEVATED,
                    fg=TEXT_SECONDARY,
                    highlightbackground=BORDER,
                )

    def _toggle_sort_order(self) -> None:
        """Toggle timeline sorting order between chronological ascending and descending."""
        self.timeline_sort_ascending = not self.timeline_sort_ascending
        btn_text = "[OLDEST FIRST]" if self.timeline_sort_ascending else "[NEWEST FIRST]"
        self.btn_sort_order.config(text=btn_text)
        self._render_timeline_entries()

    def _get_category_node_color(self, category: str, severity: int = 0) -> str:
        """Map event categories to SOC palette indicators."""
        cat = category.lower()
        if cat == "failed_login":
            return CRITICAL
        elif cat == "successful_login":
            return MINT
        elif cat == "usb_connection":
            return HIGH
        elif cat == "executable_event":
            return HIGH
        elif cat == "deleted_file":
            return CRITICAL
        elif cat == "browser_navigation":
            return CYAN
        elif cat == "malicious_email":
            return CRITICAL
        elif cat in ("hidden_file", "autorun_entry", "suspicious_extension"):
            return HIGH
        elif cat == "large_file":
            return TEAL
        elif cat == "finding":
            if severity >= 25:
                return CRITICAL
            elif severity >= 15:
                return HIGH
            return MEDIUM
        return CYAN

    def _render_timeline_entries(self) -> None:
        """Render all matching timeline entries onto the scrollable canvas with vertical spine line."""
        for child in self.timeline_content.winfo_children():
            child.destroy()

        if not self.raw_timeline:
            empty_box = ttk.Frame(self.timeline_content, style="Card.TFrame")
            empty_box._custom_bg = PANEL_BG
            empty_box.pack(fill="x", padx=SP_4, pady=SP_4)

            ttk.Label(
                empty_box,
                text="NO TIMELINE EVENTS AVAILABLE",
                foreground=TEXT_SECONDARY,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_MD, "bold"),
            ).pack(anchor="w", pady=(0, 2))

            ttk.Label(
                empty_box,
                text="No timeline events available. Run analysis on evidence with timestamps.",
                foreground=TEXT_MUTED,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_BASE, "normal"),
            ).pack(anchor="w")
            self.lbl_timeline_count.config(text="0 EVENTS")
            return

        cat_map = {
            "ALL": None,
            "AUTH": ["failed_login", "successful_login"],
            "EXEC": ["executable_event"],
            "USB": ["usb_connection"],
            "DELETE": ["deleted_file"],
            "WEB": ["browser_navigation"],
            "EMAIL": ["malicious_email"],
            "FILES": ["hidden_file", "autorun_entry", "large_file", "suspicious_extension"],
            "AI FINDINGS": ["finding"],
        }
        filter_cats = cat_map.get(self.active_timeline_filter, None)
        filtered = filter_timeline(self.raw_timeline, categories=filter_cats)

        if not self.timeline_sort_ascending:
            filtered = list(reversed(filtered))

        self.lbl_timeline_count.config(text=f"{len(filtered)} EVENTS")

        if not filtered:
            empty_box = ttk.Frame(self.timeline_content, style="Card.TFrame")
            empty_box._custom_bg = PANEL_BG
            empty_box.pack(fill="x", padx=SP_4, pady=SP_4)

            ttk.Label(
                empty_box,
                text="NO MATCHING EVENTS",
                foreground=TEXT_SECONDARY,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_MD, "bold"),
            ).pack(anchor="w", pady=(0, 2))

            ttk.Label(
                empty_box,
                text=f"No forensic events match the active '{self.active_timeline_filter}' filter.",
                foreground=TEXT_MUTED,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_BASE, "normal"),
            ).pack(anchor="w")
            return

        total_items = len(filtered)
        for idx, entry in enumerate(filtered):
            self._render_timeline_row(entry, idx, total_items)

    def _render_timeline_row(self, entry: Dict[str, Any], idx: int, total_items: int) -> None:
        """Render a single event card along the vertical spine line."""
        is_first = (idx == 0)
        is_last = (idx == total_items - 1)
        severity = int(entry.get("severity", 0))
        cat = entry.get("category", "info")
        node_color = self._get_category_node_color(cat, severity)

        if severity >= 25:
            accent_col = CRITICAL
        elif severity >= 15:
            accent_col = HIGH
        else:
            accent_col = CYAN

        row = tk.Frame(
            self.timeline_content,
            bg=PANEL_ELEVATED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )
        row.pack(fill="x", padx=SP_2, pady=2)

        # Left Spine Canvas
        spine_cv = tk.Canvas(row, width=28, bg=PANEL_ELEVATED, highlightthickness=0, bd=0)
        spine_cv.pack(side="left", fill="y")

        def _draw_spine(event, cv=spine_cv, fst=is_first, lst=is_last, col=node_color):
            h = max(28, event.height)
            cv.delete("all")
            # Vertical spine line
            if fst and lst:
                pass
            elif fst:
                cv.create_line(14, 14, 14, h, fill=BORDER, width=2)
            elif lst:
                cv.create_line(14, 0, 14, 14, fill=BORDER, width=2)
            else:
                cv.create_line(14, 0, 14, h, fill=BORDER, width=2)

            # Circular node
            cv.create_oval(8, 8, 20, 20, fill=col, outline=APP_BG, width=1)
            cv.create_oval(11, 11, 17, 17, fill=MINT, outline="")

        spine_cv.bind("<Configure>", _draw_spine)

        # Card Content Body
        card_body = tk.Frame(row, bg=PANEL_ELEVATED)
        card_body.pack(side="left", fill="both", expand=True, padx=(SP_1, SP_3), pady=4)

        # Top Metadata Line: Timestamp + Badges
        top_line = tk.Frame(card_body, bg=PANEL_ELEVATED)
        top_line.pack(fill="x", pady=(0, 2))

        ts_text = entry.get("timestamp") or "TIMESTAMP N/A"
        ttk.Label(
            top_line,
            text=ts_text,
            foreground=TEXT_MUTED,
            background=PANEL_ELEVATED,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
        ).pack(side="left", padx=(0, SP_2))

        # Source badge
        source = entry.get("source", "evidence")
        if source == "ai_inference":
            src_badge = create_soc_badge(top_line, "AI INFERENCE", color=TEAL, bg=PANEL_ELEVATED)
        else:
            src_badge = create_soc_badge(top_line, "EVIDENCE", color=CYAN, bg=PANEL_ELEVATED)
        src_badge.pack(side="left", padx=(0, 4))

        # Rule badge if present
        rule_code = entry.get("rule_code")
        if rule_code:
            r_badge = create_soc_badge(top_line, rule_code, color=MINT, bg=PANEL_ELEVATED)
            r_badge.pack(side="left", padx=(0, 4))

        # Severity badge if present
        if severity > 0:
            sev_badge = create_soc_badge(top_line, f"+{severity} PTS", color=accent_col, bg=PANEL_ELEVATED)
            sev_badge.pack(side="right")

        # Title Line
        title_text = entry.get("title", "Forensic Event")
        ttk.Label(
            card_body,
            text=title_text,
            foreground=TEXT_PRIMARY,
            background=PANEL_ELEVATED,
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
                background=PANEL_ELEVATED,
                font=(FONT_FALLBACK, FS_SM, "normal"),
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
                background=PANEL_ELEVATED,
                font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
                anchor="w",
                wraplength=460,
                justify="left",
            ).pack(fill="x", pady=(2, 0))

    # -------------------------------------------------------------------------
    # Section D: Forward Chaining Reasoning Trace Terminal
    # -------------------------------------------------------------------------

    def _build_trace_panel(self) -> None:
        """Render the dark monospace terminal displaying the deduction proof log."""
        panel = create_soc_panel(
            self.right_column, width=580, height=150, border_color=BORDER, bg=PANEL_BG
        )
        panel.pack(fill="both", expand=True)
        inner = panel.inner_frame

        # Terminal Header
        hdr_row = ttk.Frame(inner, style="Card.TFrame")
        hdr_row._custom_bg = PANEL_BG
        hdr_row.pack(fill="x", padx=SP_4, pady=(SP_2, 2))

        create_section_header(hdr_row, "EXPLAINABLE INFERENCE PROOF LOG").pack(side="left")

        ttk.Label(
            hdr_row,
            text="FORWARD CHAINING PROOF TRACE",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
        ).pack(side="right")

        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(2, 4))

        # Monospace Text Box
        term_frame = ttk.Frame(inner, style="Card.TFrame")
        term_frame._custom_bg = PANEL_BG
        term_frame.pack(fill="both", expand=True, padx=SP_3, pady=(0, SP_2))

        self.txt_trace = tk.Text(
            term_frame,
            bg=APP_BG,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            font=(FONT_MONO_FALLBACK, FS_SM, "normal"),
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=CYAN,
            wrap="word",
        )
        trace_scroll = ttk.Scrollbar(term_frame, orient="vertical", command=self.txt_trace.yview)
        self.txt_trace.configure(yscrollcommand=trace_scroll.set)

        # Syntax Highlighting Tags
        self.txt_trace.tag_configure("iteration", foreground=CYAN, font=(FONT_MONO_FALLBACK, FS_SM, "bold"))
        self.txt_trace.tag_configure("rule", foreground=MINT, font=(FONT_MONO_FALLBACK, FS_SM, "bold"))
        self.txt_trace.tag_configure("fact", foreground=HIGH)
        self.txt_trace.tag_configure("expl", foreground=TEXT_SECONDARY)
        self.txt_trace.tag_configure("summary", foreground=CYAN_GLOW, font=(FONT_MONO_FALLBACK, FS_SM, "bold"))
        self.txt_trace.tag_configure("info", foreground=TEXT_MUTED)

        self.txt_trace.pack(side="left", fill="both", expand=True)
        trace_scroll.pack(side="right", fill="y")

    # -------------------------------------------------------------------------
    # Analysis Execution & Database Integration
    # -------------------------------------------------------------------------

    def run_analysis(self) -> None:
        """
        Dynamically execute multi-source evidence extraction, forward chaining reasoning,
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

            # 2. Extract facts from evidence artifacts via Unified Evidence Dispatcher
            facts_list: List[Dict[str, Any]] = []

            for item in evidence_items:
                f_path = item.get("file_path", "")
                ev_type = item.get("evidence_type", "")
                if f_path and os.path.exists(f_path):
                    parsed = parse_evidence_item(ev_type, f_path)
                    facts_list.append(parsed)

            # Fallback to all 4 sample evidence items if case has no uploaded evidence
            if not facts_list:
                sample_dir = os.path.join(PROJECT_ROOT, "sample_evidence")
                sample_defs = [
                    ("log", os.path.join(sample_dir, "system.log")),
                    ("file", os.path.join(sample_dir, "evidence_folder")),
                    ("browser", os.path.join(sample_dir, "browser_history.csv")),
                    ("email", os.path.join(sample_dir, "emails.csv")),
                ]
                for s_type, s_path in sample_defs:
                    if os.path.exists(s_path):
                        parsed = parse_evidence_item(s_type, s_path)
                        facts_list.append(parsed)

            # 3. Merge facts into single unified facts dictionary
            unified_facts = merge_facts_list(facts_list)
            self.latest_facts = unified_facts

            # 4. Execute Forward Chaining Inference Engine
            engine = ForwardChainingEngine()
            result = engine.evaluate(unified_facts)
            self.latest_result = result

            # 5. Compile Chronological Event Sequence Timeline
            self.raw_timeline = build_timeline(unified_facts, result.get("findings", []))

            # 6. Synchronize findings with SQLite
            if target_case_id is not None:
                clear_findings_for_case(target_case_id)
                for f in result["findings"]:
                    add_finding(
                        case_id=target_case_id,
                        rule_code=f["rule_code"],
                        finding=f"{f['name']}: {f['description']}",
                        severity=f["severity"],
                    )

            # 7. Update UI View
            self._render_analysis_state(unified_facts, result)

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
        badge = create_soc_badge(self.risk_badge_container, f"RISK: {risk_lvl}", color=r_color, bg=PANEL_BG)
        badge.pack(side="left")

        # Animate the compact header gauge
        self.header_gauge.set_score(risk_score, level=risk_lvl, animate=True)

        # 2. Update Source Breakdown Badges
        if hasattr(self, "badge_src_log_container"):
            for child in self.badge_src_log_container.winfo_children():
                child.destroy()
            create_soc_badge(self.badge_src_log_container, f"LOG: {facts.get('total_lines', 0)}", color=CYAN, bg=PANEL_ELEVATED).pack()

            for child in self.badge_src_file_container.winfo_children():
                child.destroy()
            create_soc_badge(self.badge_src_file_container, f"FILE: {facts.get('total_files', 0)}", color=HIGH, bg=PANEL_ELEVATED).pack()

            for child in self.badge_src_browser_container.winfo_children():
                child.destroy()
            create_soc_badge(self.badge_src_browser_container, f"BROWSER: {facts.get('total_visits', 0)}", color=TEAL, bg=PANEL_ELEVATED).pack()

            for child in self.badge_src_email_container.winfo_children():
                child.destroy()
            create_soc_badge(self.badge_src_email_container, f"EMAIL: {facts.get('total_emails', 0)}", color=CRITICAL, bg=PANEL_ELEVATED).pack()

        # 3. Update Metrics Counters
        for key, lbl in self.fact_metric_labels.items():
            val = facts.get(key, 0)
            lbl.config(text=str(val))

        ips = facts.get("ip_addresses", [])
        self.lbl_ips.config(text=", ".join(ips) if ips else "None detected")

        users = facts.get("users_flagged", [])
        self.lbl_users.config(text=", ".join(users) if users else "None detected")

        flagged_urls = facts.get("flagged_urls", [])
        if flagged_urls:
            url_summaries = [f"{u.get('url', '')[:45]}..." if len(u.get('url', '')) > 45 else u.get('url', '') for u in flagged_urls[:3]]
            if len(flagged_urls) > 3:
                url_summaries.append(f"(+{len(flagged_urls) - 3} more)")
            self.lbl_urls.config(text="\n".join(url_summaries))
        else:
            self.lbl_urls.config(text="None detected")

        flagged_emails = facts.get("flagged_emails", [])
        if flagged_emails:
            email_summaries = [f"{e.get('sender', '')} -> {e.get('subject', '')[:30]}" for e in flagged_emails[:3]]
            if len(flagged_emails) > 3:
                email_summaries.append(f"(+{len(flagged_emails) - 3} more)")
            self.lbl_emails.config(text="\n".join(email_summaries))
        else:
            self.lbl_emails.config(text="None detected")

        # 4. Update Section B Findings List
        findings = result.get("findings", [])
        self.lbl_findings_count.config(text=f"{len(findings)} FINDINGS")

        for child in self.findings_content.winfo_children():
            child.destroy()

        if not findings:
            empty_box = ttk.Frame(self.findings_content, style="Card.TFrame")
            empty_box._custom_bg = PANEL_BG
            empty_box.pack(fill="x", padx=SP_4, pady=SP_6)

            ttk.Label(
                empty_box,
                text="NO RISK FINDINGS DERIVED",
                foreground=TEXT_SECONDARY,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_MD, "bold"),
            ).pack(anchor="w", pady=(0, 2))

            ttk.Label(
                empty_box,
                text="Forward Chaining rules evaluated without triggering risk thresholds.",
                foreground=TEXT_MUTED,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_BASE, "normal"),
            ).pack(anchor="w")
        else:
            for item in findings:
                self._render_finding_card(item)

        # 5. Update Section D Proof Terminal
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

        # 6. Update Section C Chronological Timeline Sequence
        self._render_timeline_entries()

    def _render_finding_card(self, finding: Dict[str, Any]) -> None:
        """Render a single derived finding card with proof breakdown."""
        severity = int(finding.get("severity", 0))
        if severity >= 25:
            accent_col = CRITICAL
        elif severity >= 15:
            accent_col = HIGH
        else:
            accent_col = CYAN

        card = tk.Frame(
            self.findings_content,
            bg=PANEL_ELEVATED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )
        card.pack(fill="x", padx=SP_2, pady=SP_2)

        # Left color bar
        accent_bar = tk.Canvas(card, width=4, bg=accent_col, highlightthickness=0, bd=0)
        accent_bar.pack(side="left", fill="y")

        card_body = tk.Frame(card, bg=PANEL_ELEVATED)
        card_body.pack(side="left", fill="both", expand=True, padx=SP_3, pady=SP_2)

        # Top Line: Rule Badge + Title + Severity Weight
        top_line = tk.Frame(card_body, bg=PANEL_ELEVATED)
        top_line.pack(fill="x", pady=(0, 2))

        rule_badge = create_soc_badge(top_line, finding.get("rule_code", "R000"), color=MINT, bg=PANEL_ELEVATED)
        rule_badge.pack(side="left", padx=(0, SP_2))

        ttk.Label(
            top_line,
            text=finding.get("name", "Unknown Finding"),
            foreground=TEXT_PRIMARY,
            background=PANEL_ELEVATED,
            font=(FONT_FALLBACK, FS_BASE, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        sev_badge = create_soc_badge(top_line, f"+{severity} PTS", color=accent_col, bg=PANEL_ELEVATED)
        sev_badge.pack(side="right")

        # Description
        ttk.Label(
            card_body,
            text=finding.get("description", ""),
            foreground=TEXT_SECONDARY,
            background=PANEL_ELEVATED,
            font=(FONT_FALLBACK, FS_SM, "normal"),
            anchor="w",
            wraplength=480,
            justify="left",
        ).pack(fill="x", pady=(0, 4))

        # Explanation / Proof Box
        proof_box = tk.Frame(card_body, bg=PANEL_BG, padx=6, pady=4)
        proof_box.pack(fill="x")

        ttk.Label(
            proof_box,
            text="WHY THIS FIRED (FACT PROOF):",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_XS, "bold"),
            anchor="w",
        ).pack(fill="x")

        ttk.Label(
            proof_box,
            text=finding.get("explanation", ""),
            foreground=MINT,
            background=PANEL_BG,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
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
        badge = create_soc_badge(self.risk_badge_container, "RISK: --", color=TEXT_MUTED, bg=PANEL_BG)
        badge.pack(side="left")
        self.lbl_risk_score.config(text="SCORE: -- / 100", foreground=TEXT_SECONDARY)

        # Reset fact counters
        for lbl in self.fact_metric_labels.values():
            lbl.config(text="--")
        self.lbl_ips.config(text="None detected")
        self.lbl_users.config(text="None detected")
        self.lbl_urls.config(text="None detected")
        self.lbl_emails.config(text="None detected")

        # Reset findings
        self.lbl_findings_count.config(text="0 FINDINGS")
        for child in self.findings_content.winfo_children():
            child.destroy()

        empty_box = ttk.Frame(self.findings_content, style="Card.TFrame")
        empty_box._custom_bg = PANEL_BG
        empty_box.pack(fill="x", padx=SP_4, pady=SP_6)

        ttk.Label(
            empty_box,
            text="NO ANALYSIS PERFORMED YET",
            foreground=TEXT_SECONDARY,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_MD, "bold"),
        ).pack(anchor="w", pady=(0, 2))

        ttk.Label(
            empty_box,
            text="Click [RUN FORWARD CHAINING ANALYSIS] to evaluate forensic evidence.",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_BASE, "normal"),
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
            c_badge = create_soc_badge(self.case_badge_container, c_text, color=CYAN, bg=PANEL_BG)
            c_badge.pack(side="left")
        else:
            c_badge = create_soc_badge(self.case_badge_container, "NO ACTIVE CASE", color=TEXT_MUTED, bg=PANEL_BG)
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
                badge = create_soc_badge(self.risk_badge_container, f"RISK: {r_lbl}", color=r_color, bg=PANEL_BG)
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

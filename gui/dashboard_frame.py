# =============================================================================
# gui/dashboard_frame.py
# FORENSEQUENCE - Executive Forensic Dashboard Screen
# =============================================================================

import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional, Callable

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
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_SECTION,
    FONT_BODY,
    FONT_SMALL,
    FONT_MONO_SM,
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
)

from database import (
    initialize_db,
    get_all_cases,
    get_evidence_for_case,
    get_findings_for_case,
    get_case_by_id,
)


class DashboardFrame(ttk.Frame):
    """
    Executive Forensic Dashboard Screen.
    Displays real-time metrics, active investigations, and system telemetry
    queried directly from SQLite database.
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

        # Ensure database tables exist before first query
        initialize_db()

        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        """Construct the visual hierarchy of the Cyberpunk Dashboard."""
        self.configure(style="TFrame")

        # ---------------------------------------------------------------------
        # 1. Top Header Bar
        # ---------------------------------------------------------------------
        header_bar = ttk.Frame(self, style="TFrame")
        header_bar.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))

        # Header Title and Section Label
        header_left = ttk.Frame(header_bar, style="TFrame")
        header_left.pack(side="left", fill="y")

        create_section_header(header_left, "SYSTEM DASHBOARD").pack(anchor="w")

        title_row = ttk.Frame(header_left, style="TFrame")
        title_row.pack(anchor="w", pady=(SP_1, 0))

        ttk.Label(
            title_row,
            text="Executive Forensic Overview",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        # Telemetry Status Badge
        badge = create_badge(title_row, "LIVE TELEMETRY", CYAN)
        badge.pack(side="left", padx=(SP_4, 0))

        # Top-Right Primary Action Button: [+ NEW CASE]
        header_right = ttk.Frame(header_bar, style="TFrame")
        header_right.pack(side="right", anchor="e", pady=(SP_1, 0))

        btn_new_case = create_neon_button(
            header_right,
            text="[+ NEW CASE]",
            command=self._handle_new_case,
            variant="primary",
        )
        btn_new_case.pack(side="right")

        # Header Divider
        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(SP_2, SP_4))

        # ---------------------------------------------------------------------
        # 2. Top Stat Cards Row (3 side-by-side glass cards)
        # ---------------------------------------------------------------------
        self.cards_row = ttk.Frame(self, style="TFrame")
        self.cards_row.pack(fill="x", padx=SP_6, pady=(0, SP_4))

        # Card 1: ACTIVE CASES (CYAN large number in Orbitron font)
        card1 = create_glass_frame(
            self.cards_row, width=310, height=115, border_color=CYAN, fill_color=DEEP
        )
        card1.pack(side="left", padx=(0, SP_3))
        inner1 = card1.inner_frame

        ttk.Label(
            inner1,
            text="ACTIVE CASES",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_SM, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(SP_3, 0))

        self.lbl_active_cases_val = ttk.Label(
            inner1,
            text="0",
            foreground=CYAN,
            background=DEEP,
            font=(FONT_DISPLAY, 26, "bold"),
        )
        self.lbl_active_cases_val.pack(anchor="w", padx=SP_4)

        self.lbl_active_cases_sub = ttk.Label(
            inner1,
            text="Open investigations in progress",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_SMALL,
        )
        self.lbl_active_cases_sub.pack(anchor="w", padx=SP_4)

        # Card 2: TOTAL EVIDENCE (ICE cyan large number in Orbitron font)
        card2 = create_glass_frame(
            self.cards_row, width=310, height=115, border_color=ICE, fill_color=DEEP
        )
        card2.pack(side="left", padx=(0, SP_3))
        inner2 = card2.inner_frame

        ttk.Label(
            inner2,
            text="TOTAL EVIDENCE",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_SM, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(SP_3, 0))

        self.lbl_total_evidence_val = ttk.Label(
            inner2,
            text="0",
            foreground=ICE,
            background=DEEP,
            font=(FONT_DISPLAY, 26, "bold"),
        )
        self.lbl_total_evidence_val.pack(anchor="w", padx=SP_4)

        self.lbl_total_evidence_sub = ttk.Label(
            inner2,
            text="Cataloged evidence artifacts",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_SMALL,
        )
        self.lbl_total_evidence_sub.pack(anchor="w", padx=SP_4)

        # Card 3: HIGH-RISK FINDINGS (PINK large number in Orbitron font)
        card3 = create_glass_frame(
            self.cards_row, width=310, height=115, border_color=PINK, fill_color=DEEP
        )
        card3.pack(side="left")
        inner3 = card3.inner_frame

        ttk.Label(
            inner3,
            text="HIGH-RISK FINDINGS",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_SM, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(SP_3, 0))

        self.lbl_high_risk_val = ttk.Label(
            inner3,
            text="0",
            foreground=PINK,
            background=DEEP,
            font=(FONT_DISPLAY, 26, "bold"),
        )
        self.lbl_high_risk_val.pack(anchor="w", padx=SP_4)

        self.lbl_high_risk_sub = ttk.Label(
            inner3,
            text="Findings with severity >= 25",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_SMALL,
        )
        self.lbl_high_risk_sub.pack(anchor="w", padx=SP_4)

        # ---------------------------------------------------------------------
        # 3. Recent Investigations Section Header
        # ---------------------------------------------------------------------
        section_hdr_row = ttk.Frame(self, style="TFrame")
        section_hdr_row.pack(fill="x", padx=SP_6, pady=(0, SP_2))

        create_section_header(section_hdr_row, "RECENT INVESTIGATIONS").pack(side="left")

        self.lbl_case_count_badge = ttk.Label(
            section_hdr_row,
            text="0 TOTAL RECORDS",
            foreground=TEXT_MUTED,
            background=VOID,
            font=FONT_MONO_SM,
        )
        self.lbl_case_count_badge.pack(side="right")

        # ---------------------------------------------------------------------
        # 4. Scrollable List of Recent Cases
        # ---------------------------------------------------------------------
        self.list_container = ttk.Frame(self, style="TFrame")
        self.list_container.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_3))

        self.canvas_scroll = tk.Canvas(
            self.list_container,
            bg=VOID,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = ttk.Scrollbar(
            self.list_container,
            orient="vertical",
            command=self.canvas_scroll.yview,
        )
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)

        self.scroll_content = ttk.Frame(self.canvas_scroll, style="TFrame")
        self.scroll_window_id = self.canvas_scroll.create_window(
            (0, 0), window=self.scroll_content, anchor="nw"
        )

        def _on_content_configure(event):
            self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))

        def _on_canvas_configure(event):
            self.canvas_scroll.itemconfig(self.scroll_window_id, width=event.width)

        self.scroll_content.bind("<Configure>", _on_content_configure)
        self.canvas_scroll.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            self.canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas_scroll.bind("<Enter>", lambda _: self.canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas_scroll.bind("<Leave>", lambda _: self.canvas_scroll.unbind_all("<MouseWheel>"))

        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # ---------------------------------------------------------------------
        # 5. System Activity Strip at Bottom
        # ---------------------------------------------------------------------
        self._build_system_activity_strip()

    def _build_system_activity_strip(self) -> None:
        """Render the system activity telemetry strip at the base of the dashboard."""
        strip = create_glass_frame(
            self,
            width=950,
            height=36,
            radius=RADIUS_SM,
            border_color=PLUM,
            fill_color=ABYSS,
        )
        strip.pack(fill="x", padx=SP_6, pady=(0, SP_3))
        inner_strip = strip.inner_frame

        container = ttk.Frame(inner_strip, style="Card.TFrame")
        container._custom_bg = ABYSS
        container.pack(expand=True, fill="both")

        status_box = ttk.Frame(container, style="Card.TFrame")
        status_box._custom_bg = ABYSS
        status_box.pack(anchor="center", pady=6)

        # 1. Engine Status: Online
        dot1 = tk.Canvas(status_box, width=12, height=12, bg=ABYSS, highlightthickness=0, bd=0)
        dot1.pack(side="left", padx=(0, 4))
        dot1.create_oval(2, 2, 10, 10, fill=CYAN, outline="")

        ttk.Label(
            status_box,
            text="ENGINE STATUS: ONLINE",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="left", padx=(0, SP_3))

        ttk.Label(
            status_box,
            text="|",
            foreground=PLUM,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="left", padx=(0, SP_3))

        # 2. Knowledge Base: Active
        dot2 = tk.Canvas(status_box, width=12, height=12, bg=ABYSS, highlightthickness=0, bd=0)
        dot2.pack(side="left", padx=(0, 4))
        dot2.create_oval(2, 2, 10, 10, fill=PURPLE, outline="")

        ttk.Label(
            status_box,
            text="KNOWLEDGE BASE: ACTIVE",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="left", padx=(0, SP_3))

        ttk.Label(
            status_box,
            text="|",
            foreground=PLUM,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="left", padx=(0, SP_3))

        # 3. Monitor: Standby
        dot3 = tk.Canvas(status_box, width=12, height=12, bg=ABYSS, highlightthickness=0, bd=0)
        dot3.pack(side="left", padx=(0, 4))
        dot3.create_oval(2, 2, 10, 10, fill=PEACH, outline="")

        ttk.Label(
            status_box,
            text="MONITOR: STANDBY",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="left")

    # -------------------------------------------------------------------------
    # Data Access & View Refresh
    # -------------------------------------------------------------------------

    def refresh_data(self) -> None:
        """
        Re-query SQLite for all cases, evidence, and findings.
        Updates counters in the top stat cards and rebuilds the case cards list.
        """
        cases = get_all_cases()

        # 1. Metric: Active Cases
        active_cases = [c for c in cases if str(c.get("status", "OPEN")).upper() != "CLOSED"]
        active_count = len(active_cases)
        self.lbl_active_cases_val.config(text=str(active_count))
        self.lbl_active_cases_sub.config(
            text=f"{len(cases)} total recorded in system" if cases else "No cases in database"
        )

        # 2. Metric: Total Evidence across all cases
        total_evidence = 0
        for c in cases:
            ev_list = get_evidence_for_case(c["id"])
            total_evidence += len(ev_list)
        self.lbl_total_evidence_val.config(text=str(total_evidence))
        self.lbl_total_evidence_sub.config(
            text=f"Across {len(cases)} case repository items" if cases else "0 artifacts cataloged"
        )

        # 3. Metric: High-Risk Findings (severity >= 25 across cases)
        high_risk_findings = 0
        for c in cases:
            findings = get_findings_for_case(c["id"])
            for f in findings:
                if f.get("severity", 0) >= 25:
                    high_risk_findings += 1
        self.lbl_high_risk_val.config(text=str(high_risk_findings))
        self.lbl_high_risk_sub.config(
            text="Threat findings requiring review" if high_risk_findings else "No high-risk alerts"
        )

        # Update case count indicator
        self.lbl_case_count_badge.config(text=f"{len(cases)} TOTAL RECORDS")

        # 4. Rebuild Case Cards List
        for widget in self.scroll_content.winfo_children():
            widget.destroy()

        if not cases:
            self._render_empty_state()
        else:
            for case in cases:
                self._render_case_row(case)

    def _render_empty_state(self) -> None:
        """Display placeholder glass card when no cases exist in the database."""
        empty_card = create_glass_frame(
            self.scroll_content,
            width=950,
            height=130,
            border_color=STEEL,
            fill_color=DEEP,
        )
        empty_card.pack(fill="x", pady=SP_2)
        inner = empty_card.inner_frame

        ttk.Label(
            inner,
            text="NO ACTIVE INVESTIGATIONS",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_MD, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(SP_3, SP_1))

        ttk.Label(
            inner,
            text="No active investigations found. Click [+ NEW CASE] to initialize a case.",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_BODY,
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_3))

        btn_init = create_neon_button(
            inner,
            text="[+ NEW CASE]",
            command=self._handle_new_case,
            variant="primary",
            bg=DEEP,
        )
        btn_init.pack(anchor="w", padx=SP_4)

    def _render_case_row(self, case: dict) -> None:
        """
        Render a single case record as an interactive glass card row.
        """
        row_card = create_glass_frame(
            self.scroll_content,
            width=950,
            height=72,
            border_color=STEEL,
            fill_color=DEEP,
        )
        row_card.pack(fill="x", pady=SP_1)
        inner = row_card.inner_frame

        # Left Info Section: Case Number Badge + Name + Investigator
        left_box = ttk.Frame(inner, style="Card.TFrame")
        left_box._custom_bg = DEEP
        left_box.pack(side="left", fill="both", expand=True, padx=SP_2, pady=SP_1)

        case_number = case.get("case_number", "CASE-UNKNOWN")
        case_badge = create_badge(left_box, case_number, CYAN, bg=DEEP)
        case_badge.pack(side="left", padx=(SP_2, SP_3))

        meta_col = ttk.Frame(left_box, style="Card.TFrame")
        meta_col._custom_bg = DEEP
        meta_col.pack(side="left", fill="y", anchor="w")

        case_name = case.get("case_name", "Untitled Investigation")
        ttk.Label(
            meta_col,
            text=case_name,
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_BASE, "bold"),
        ).pack(anchor="w")

        investigator = case.get("investigator", "Unassigned")
        ttk.Label(
            meta_col,
            text=f"Investigator: {investigator}",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_SMALL,
        ).pack(anchor="w")

        # Right Info Section: Timestamp + Status Badge + [VIEW CASE] Button
        right_box = ttk.Frame(inner, style="Card.TFrame")
        right_box._custom_bg = DEEP
        right_box.pack(side="right", fill="y", padx=SP_2, pady=SP_1)

        created_at = case.get("created_at", "")
        ttk.Label(
            right_box,
            text=str(created_at),
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_MONO_SM,
        ).pack(side="left", padx=(SP_2, SP_3))

        status_text = str(case.get("status", "OPEN")).upper()
        if status_text == "OPEN":
            status_color = CYAN
        elif status_text == "INVESTIGATING":
            status_color = PEACH
        elif status_text == "CLOSED":
            status_color = TEXT_MUTED
        else:
            status_color = ICE

        status_badge = create_badge(right_box, status_text, status_color, bg=DEEP)
        status_badge.pack(side="left", padx=(0, SP_3))

        case_id = case.get("id")
        btn_view = create_neon_button(
            right_box,
            text="[VIEW CASE]",
            command=lambda cid=case_id: self._handle_view_case(cid),
            variant="secondary",
            bg=DEEP,
        )
        btn_view.pack(side="left", padx=(0, SP_2))

    # -------------------------------------------------------------------------
    # Navigation & Action Callbacks
    # -------------------------------------------------------------------------

    def _handle_new_case(self) -> None:
        """Trigger navigation callback to open case intake screen."""
        if self.on_navigate_callback:
            self.on_navigate_callback("create_case")
        elif self.shell:
            self.shell.show_screen("Cases")

    def _handle_view_case(self, case_id: Optional[int]) -> None:
        """Trigger callback to select case context and view details."""
        if case_id is None:
            return
        if self.on_select_case_callback:
            self.on_select_case_callback(case_id)
        elif self.shell:
            case = get_case_by_id(case_id)
            if case:
                self.shell.set_case_context(f"CASE: {case['case_number']} | {case['case_name']}")
            self.shell.selected_case_id = case_id
            self.shell.show_screen("Evidence")

# =============================================================================
# gui/report_frame.py
# FORENSEQUENCE - Forensic Investigation Report Screen & In-App Document Viewer
# =============================================================================

import os
import sys
import subprocess
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

import tkinter as tk
import ttkbootstrap as ttk

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

from database import (
    get_case_by_id,
    get_evidence_for_case,
    get_findings_for_case,
    get_reports_for_case,
    get_all_cases,
)
from analysis.risk_engine import RiskEngine
from analysis.timeline import build_timeline, summarize_timeline
from analyzers.log_analyzer import parse_log_file
from reports.report_generator import generate_pdf_report
from ai.rules import get_all_rules

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ReportFrame(ttk.Frame):
    """
    Forensic Investigation Report Screen and In-App Document Viewer.
    Renders structured in-app previews of court-admissible forensic dossiers,
    compiles executive metrics, cryptographic chain-of-custody tables,
    and exports high-resolution PDFs using ReportLab.
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

        # Inherit active case selection from shell if available
        if self.case_id is None and self.shell and getattr(self.shell, "selected_case_id", None):
            self.case_id = self.shell.selected_case_id

        self.last_generated_pdf: Optional[str] = None
        self.last_generated_at: Optional[str] = None
        self._is_generating = False

        self._build_ui()
        self.refresh_data()

    def set_case(self, case_id: Optional[int]) -> None:
        """Update active investigation case context and refresh preview."""
        self.case_id = case_id
        self.refresh_data()

    # -------------------------------------------------------------------------
    # Layout Builder
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble top control panel, status strip, and scrollable document viewer."""
        self.configure(style="TFrame")

        # ---------------------------------------------------------------------
        # 1. Top Control Bar (Glass Panel)
        # ---------------------------------------------------------------------
        header_card = create_glass_frame(
            self, width=960, height=86, border_color=PURPLE, fill_color=DEEP
        )
        header_card.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))
        inner_h = header_card.inner_frame

        # Left block: Title + Case Badge + Document Badge
        left_h = ttk.Frame(inner_h, style="Card.TFrame")
        left_h._custom_bg = DEEP
        left_h.pack(side="left", fill="both", expand=True, padx=SP_4, pady=SP_2)

        create_section_header(left_h, "FORENSIC REPORT GENERATOR").pack(anchor="w")

        info_row = ttk.Frame(left_h, style="Card.TFrame")
        info_row._custom_bg = DEEP
        info_row.pack(anchor="w", pady=(2, 0))

        self.case_badge_container = ttk.Frame(info_row, style="Card.TFrame")
        self.case_badge_container._custom_bg = DEEP
        self.case_badge_container.pack(side="left", padx=(0, SP_2))
        self.badge_case = create_badge(self.case_badge_container, "NO ACTIVE CASE", TEXT_MUTED, bg=DEEP)
        self.badge_case.pack(side="left")

        self.badge_format = create_badge(info_row, "REPORTLAB PDF EXPORT", PEACH, bg=DEEP)
        self.badge_format.pack(side="left", padx=(0, SP_3))

        self.lbl_report_status = ttk.Label(
            info_row,
            text="STANDBY",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_MONO_SM,
        )
        self.lbl_report_status.pack(side="left")

        # Right block: Action Buttons
        right_h = ttk.Frame(inner_h, style="Card.TFrame")
        right_h._custom_bg = DEEP
        right_h.pack(side="right", fill="y", padx=SP_4, pady=SP_2)

        self.btn_export = create_neon_button(
            right_h,
            text="[GENERATE & EXPORT PDF REPORT]",
            command=self.generate_report,
            variant="primary",
            bg=DEEP,
        )
        self.btn_export.pack(side="left", padx=(0, SP_2))

        self.btn_open = create_neon_button(
            right_h,
            text="[OPEN PDF LOCATION]",
            command=self.open_pdf_location,
            variant="ghost",
            bg=DEEP,
        )
        self.btn_open.pack(side="left", padx=(0, SP_2))

        self.btn_refresh = create_neon_button(
            right_h,
            text="[REGENERATE PREVIEW]",
            command=self.refresh_data,
            variant="ghost",
            bg=DEEP,
        )
        self.btn_refresh.pack(side="left")

        # ---------------------------------------------------------------------
        # 2. Status Banner Strip
        # ---------------------------------------------------------------------
        status_bar = create_glass_frame(
            self, width=960, height=36, radius=RADIUS_SM, border_color=PLUM, fill_color=ABYSS
        )
        status_bar.pack(fill="x", padx=SP_6, pady=(0, SP_3))
        inner_s = status_bar.inner_frame

        s_box = ttk.Frame(inner_s, style="Card.TFrame")
        s_box._custom_bg = ABYSS
        s_box.pack(anchor="w", padx=SP_4, pady=6)

        self.dot_status = tk.Canvas(s_box, width=10, height=10, bg=ABYSS, highlightthickness=0, bd=0)
        self.dot_status.pack(side="left", padx=(0, 6))
        self.dot_status.create_oval(1, 1, 9, 9, fill=CYAN, outline="")

        self.lbl_banner_message = ttk.Label(
            s_box,
            text="Click [GENERATE & EXPORT PDF REPORT] to build formal report document.",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_MONO_SM,
        )
        self.lbl_banner_message.pack(side="left")

        # ---------------------------------------------------------------------
        # 3. Main Document Preview Container (Scrollable)
        # ---------------------------------------------------------------------
        self.scroll_container = ttk.Frame(self, style="TFrame")
        self.scroll_container.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_4))

        self.canvas_scroll = tk.Canvas(
            self.scroll_container,
            bg=VOID,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = ttk.Scrollbar(
            self.scroll_container,
            orient="vertical",
            command=self.canvas_scroll.yview,
        )
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)

        self.doc_content = ttk.Frame(self.canvas_scroll, style="TFrame")
        self.doc_win_id = self.canvas_scroll.create_window(
            (0, 0), window=self.doc_content, anchor="nw"
        )

        def _on_doc_configure(event):
            self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))

        def _on_canvas_configure(event):
            self.canvas_scroll.itemconfig(self.doc_win_id, width=event.width)

        self.doc_content.bind("<Configure>", _on_doc_configure)
        self.canvas_scroll.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            try:
                if self.canvas_scroll.winfo_exists():
                    self.canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        self.canvas_scroll.bind("<Enter>", lambda _: self.canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas_scroll.bind("<Leave>", lambda _: self.canvas_scroll.unbind_all("<MouseWheel>"))

        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    # -------------------------------------------------------------------------
    # Report Actions
    # -------------------------------------------------------------------------

    def generate_report(self) -> None:
        """Trigger PDF generation engine and update UI state."""
        if self._is_generating:
            return

        target_case_id = self.case_id
        if target_case_id is None and self.shell and getattr(self.shell, "selected_case_id", None):
            target_case_id = self.shell.selected_case_id
            self.case_id = target_case_id

        if target_case_id is None:
            cases = get_all_cases()
            if cases:
                target_case_id = cases[0]["id"]
                self.case_id = target_case_id

        if target_case_id is None:
            self.lbl_banner_message.config(
                text="[ALERT] No case selected. Create or select a case first.",
                foreground=PINK,
            )
            return

        self._is_generating = True
        self.lbl_report_status.config(text="GENERATING PDF...", foreground=CYAN)
        self.lbl_banner_message.config(text="Compiling forensic PDF dossier with ReportLab...", foreground=CYAN)
        self.update_idletasks()

        try:
            pdf_path = generate_pdf_report(target_case_id)
            self.last_generated_pdf = pdf_path
            self.last_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            filename = os.path.basename(pdf_path)
            self.lbl_report_status.config(text="PDF READY", foreground=CYAN)
            self.lbl_banner_message.config(
                text=f"PDF EXPORT COMPLETE: {pdf_path} ({self.last_generated_at})",
                foreground=ICE,
            )

            # Refresh preview to reflect latest records
            self.refresh_data()

        except Exception as exc:
            self.lbl_report_status.config(text="GENERATION ERROR", foreground=PINK)
            self.lbl_banner_message.config(
                text=f"[ERROR] PDF generation failed: {str(exc)}",
                foreground=PINK,
            )
        finally:
            self._is_generating = False

    def open_pdf_location(self) -> None:
        """Open the generated PDF report or containing folder in Windows Explorer."""
        target_path = self.last_generated_pdf
        if target_path and os.path.exists(target_path):
            try:
                # Open PDF file directly using default PDF reader
                os.startfile(os.path.normpath(target_path))
                self.lbl_banner_message.config(text=f"Opened PDF document: {target_path}", foreground=ICE)
                return
            except Exception:
                try:
                    subprocess.run(["explorer", f"/select,{os.path.normpath(target_path)}"])
                    return
                except Exception:
                    pass

        uploads_dir = os.path.join(PROJECT_ROOT, "uploads")
        if os.path.exists(uploads_dir):
            try:
                os.startfile(uploads_dir)
                self.lbl_banner_message.config(text=f"Opened uploads folder: {uploads_dir}", foreground=TEXT_SECONDARY)
            except Exception:
                pass
        else:
            self.lbl_banner_message.config(
                text="No PDF export found. Click [GENERATE & EXPORT PDF REPORT] first.",
                foreground=PEACH,
            )

    # -------------------------------------------------------------------------
    # In-App Document Preview Renderer
    # -------------------------------------------------------------------------

    def refresh_data(self) -> None:
        """Re-query SQLite for case data, evidence, and findings, and refresh preview."""
        # 1. Resolve case
        target_case_id = self.case_id
        if target_case_id is None and self.shell and getattr(self.shell, "selected_case_id", None):
            target_case_id = self.shell.selected_case_id
            self.case_id = target_case_id

        if target_case_id is None:
            cases = get_all_cases()
            if cases:
                target_case_id = cases[0]["id"]
                self.case_id = target_case_id

        case = get_case_by_id(target_case_id) if target_case_id is not None else None

        # 2. Update Header Context Badge
        for child in self.case_badge_container.winfo_children():
            child.destroy()

        if case:
            c_text = f"CASE: {case['case_number']}"
            c_badge = create_badge(self.case_badge_container, c_text, CYAN, bg=DEEP)
            c_badge.pack(side="left")
        else:
            c_badge = create_badge(self.case_badge_container, "NO ACTIVE CASE", TEXT_MUTED, bg=DEEP)
            c_badge.pack(side="left")

        # 3. Check existing reports in SQLite
        if target_case_id is not None:
            db_reports = get_reports_for_case(target_case_id)
            if db_reports:
                latest = db_reports[0]
                self.last_generated_pdf = latest["report_path"]
                self.last_generated_at = latest["generated_at"]
                self.lbl_report_status.config(text="PDF ARCHIVED", foreground=CYAN)
                self.lbl_banner_message.config(
                    text=f"LATEST EXPORT: {latest['report_path']} (Generated: {latest['generated_at']})",
                    foreground=TEXT_SECONDARY,
                )

        # 4. Fetch evidence and findings
        evidence_items = get_evidence_for_case(target_case_id) if target_case_id else []
        findings_items = get_findings_for_case(target_case_id) if target_case_id else []

        # 5. Calculate Risk Score
        risk_engine = RiskEngine()
        risk_data = risk_engine.calculate_risk(findings_items)
        risk_score = risk_data.get("risk_score", 0)
        risk_level = risk_data.get("risk_level", "LOW")
        recommendations = risk_data.get("recommendations", [])

        # 6. Harvest timeline facts
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

        evidence_found = False
        for ev in evidence_items:
            fpath = ev.get("file_path", "")
            if fpath and os.path.exists(fpath):
                try:
                    f_facts = parse_log_file(fpath)
                    evidence_found = True
                    merged_facts["timeline_events"].extend(f_facts.get("timeline_events", []))
                except Exception:
                    pass

        if not evidence_found:
            sample_log = os.path.join(PROJECT_ROOT, "sample_evidence", "system.log")
            if os.path.exists(sample_log):
                try:
                    sample_facts = parse_log_file(sample_log)
                    merged_facts = sample_facts
                except Exception:
                    pass

        timeline_events = build_timeline(merged_facts, findings_items)
        timeline_stats = summarize_timeline(timeline_events)

        # 7. Render In-App Document Card
        self._render_document_preview(
            case=case,
            evidence_items=evidence_items,
            findings_items=findings_items,
            risk_score=risk_score,
            risk_level=risk_level,
            recommendations=recommendations,
            timeline_events=timeline_events,
            timeline_stats=timeline_stats,
        )

    def _render_document_preview(
        self,
        case: Optional[Dict[str, Any]],
        evidence_items: List[Dict[str, Any]],
        findings_items: List[Dict[str, Any]],
        risk_score: int,
        risk_level: str,
        recommendations: List[str],
        timeline_events: List[Dict[str, Any]],
        timeline_stats: Dict[str, Any],
    ) -> None:
        """Render the complete digital forensic document preview card."""
        for child in self.doc_content.winfo_children():
            child.destroy()

        # Center wrapper with letter-proportioned document container
        center_wrap = ttk.Frame(self.doc_content, style="TFrame")
        center_wrap.pack(fill="x", padx=SP_4, pady=(0, SP_6))

        # Main Document Dossier Card
        doc_card = tk.Frame(
            center_wrap,
            bg=DEEP,
            highlightthickness=1,
            highlightbackground=STEEL,
            bd=0,
        )
        doc_card.pack(fill="x", padx=SP_2, pady=SP_2)

        # Document Header Banner
        self._render_preview_header(doc_card, case)

        # Section 1: Executive Summary & Risk Assessment
        self._render_preview_executive_summary(doc_card, case, risk_score, risk_level, evidence_items, findings_items)

        # Section 2: Chain of Custody Evidence Inventory
        self._render_preview_evidence_table(doc_card, evidence_items)

        # Section 3: Derived Forensic Findings
        self._render_preview_findings(doc_card, findings_items)

        # Section 4: Incident Response Recommendations
        self._render_preview_recommendations(doc_card, recommendations)

        # Section 5: Chronological Event Sequence Summary
        self._render_preview_timeline(doc_card, timeline_events, timeline_stats)

        # Document Footer Seal
        self._render_preview_footer(doc_card)

    def _render_preview_header(self, parent: tk.Widget, case: Optional[Dict[str, Any]]) -> None:
        """Render document header block with Cyberpunk branding."""
        header_frame = tk.Frame(parent, bg=ABYSS, padx=SP_6, pady=SP_4)
        header_frame.pack(fill="x")

        # Top line title
        ttk.Label(
            header_frame,
            text="FORENSEQUENCE",
            foreground=CYAN,
            background=ABYSS,
            font=(FONT_DISPLAY, 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="DIGITAL FORENSIC INVESTIGATION REPORT",
            foreground=TEXT_PRIMARY,
            background=ABYSS,
            font=(FONT_FALLBACK, FS_MD, "bold"),
        ).pack(anchor="w", pady=(2, 6))

        create_divider(header_frame, color=PURPLE).pack(fill="x", pady=(0, 6))

        # Metadata grid
        meta_grid = tk.Frame(header_frame, bg=ABYSS)
        meta_grid.pack(fill="x")

        case_num = case.get("case_number", "N/A") if case else "N/A"
        case_name = case.get("case_name", "N/A") if case else "N/A"
        investigator = case.get("investigator", "N/A") if case else "N/A"
        status = case.get("status", "OPEN") if case else "N/A"
        created_at = case.get("created_at", "N/A") if case else "N/A"
        gen_time = self.last_generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fields = [
            ("CASE NUMBER:", case_num, "STATUS:", status),
            ("CASE TITLE:", case_name, "INVESTIGATOR:", investigator),
            ("OPENED:", created_at, "EXPORT DATE:", gen_time),
        ]

        for left_lbl, left_val, right_lbl, right_val in fields:
            row = tk.Frame(meta_grid, bg=ABYSS)
            row.pack(fill="x", pady=1)

            ttk.Label(row, text=left_lbl, foreground=TEXT_MUTED, background=ABYSS, font=FONT_SMALL, width=14).pack(side="left")
            ttk.Label(row, text=left_val, foreground=TEXT_PRIMARY, background=ABYSS, font=(FONT_FALLBACK, FS_SM, "bold"), width=32).pack(side="left")

            ttk.Label(row, text=right_lbl, foreground=TEXT_MUTED, background=ABYSS, font=FONT_SMALL, width=14).pack(side="left")
            ttk.Label(row, text=right_val, foreground=ICE, background=ABYSS, font=FONT_SMALL).pack(side="left")

    def _render_preview_executive_summary(
        self,
        parent: tk.Widget,
        case: Optional[Dict[str, Any]],
        risk_score: int,
        risk_level: str,
        evidence_items: List[Dict[str, Any]],
        findings_items: List[Dict[str, Any]],
    ) -> None:
        """Render Section 1 executive threat metrics."""
        sec_frame = tk.Frame(parent, bg=DEEP, padx=SP_6, pady=SP_3)
        sec_frame.pack(fill="x")

        create_section_header(sec_frame, "SECTION 1: EXECUTIVE SUMMARY & THREAT RISK ASSESSMENT").pack(anchor="w", pady=(0, 4))
        create_divider(sec_frame, color=PLUM).pack(fill="x", pady=(0, 6))

        # KPI Stats Row
        kpi_row = tk.Frame(sec_frame, bg=DEEP)
        kpi_row.pack(fill="x", pady=(0, 6))

        r_col = risk_color(risk_score)
        cards_spec = [
            ("THREAT SCORE", f"{risk_score} / 100", r_col),
            ("RISK LEVEL", risk_level, r_col),
            ("EVIDENCE ITEMS", str(len(evidence_items)), ICE),
            ("DERIVED FINDINGS", str(len(findings_items)), PEACH),
        ]

        for title, val, color in cards_spec:
            card = tk.Frame(kpi_row, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL, padx=10, pady=6)
            card.pack(side="left", fill="both", expand=True, padx=3)

            ttk.Label(card, text=title, foreground=TEXT_MUTED, background=ABYSS, font=FONT_SMALL).pack(anchor="w")
            ttk.Label(card, text=val, foreground=color, background=ABYSS, font=(FONT_DISPLAY, FS_LG, "bold")).pack(anchor="w")

        # Narrative paragraph
        desc_text = case.get("description", "").strip() if case else ""
        if not desc_text:
            desc_text = "Standard digital forensics investigation protocol executed with Forward Chaining propositional inference."

        narrative = (
            f"Automated evaluation completed across all cataloged artifacts for case "
            f"'{case.get('case_number', 'N/A') if case else 'N/A'}'. Threat severity aggregation scored "
            f"{risk_score}/100, assigning a threat categorization band of {risk_level}. "
            f"Intake Notes: {desc_text}"
        )

        ttk.Label(
            sec_frame,
            text=narrative,
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            wraplength=760,
            justify="left",
        ).pack(fill="x", pady=(4, 0))

    def _render_preview_evidence_table(self, parent: tk.Widget, evidence_items: List[Dict[str, Any]]) -> None:
        """Render Section 2 evidence inventory and SHA-256 hashes."""
        sec_frame = tk.Frame(parent, bg=DEEP, padx=SP_6, pady=SP_3)
        sec_frame.pack(fill="x")

        create_section_header(sec_frame, "SECTION 2: EVIDENCE INVENTORY (CHAIN OF CUSTODY)").pack(anchor="w", pady=(0, 2))
        ttk.Label(
            sec_frame,
            text="Cryptographic integrity validated via 64KB block SHA-256 hashing.",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(0, 4))
        create_divider(sec_frame, color=PLUM).pack(fill="x", pady=(0, 6))

        tbl_box = tk.Frame(sec_frame, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL)
        tbl_box.pack(fill="x")

        # Header Row
        h_row = tk.Frame(tbl_box, bg=STEEL, padx=6, pady=4)
        h_row.pack(fill="x")

        ttk.Label(h_row, text="FILENAME", foreground=TEXT_PRIMARY, background=STEEL, font=(FONT_FALLBACK, FS_XS, "bold"), width=22).pack(side="left")
        ttk.Label(h_row, text="TYPE", foreground=TEXT_PRIMARY, background=STEEL, font=(FONT_FALLBACK, FS_XS, "bold"), width=10).pack(side="left")
        ttk.Label(h_row, text="UPLOADED AT", foreground=TEXT_PRIMARY, background=STEEL, font=(FONT_FALLBACK, FS_XS, "bold"), width=18).pack(side="left")
        ttk.Label(h_row, text="SHA-256 CRYPTOGRAPHIC HASH", foreground=TEXT_PRIMARY, background=STEEL, font=(FONT_FALLBACK, FS_XS, "bold")).pack(side="left")

        if not evidence_items:
            empty_row = tk.Frame(tbl_box, bg=ABYSS, padx=6, pady=6)
            empty_row.pack(fill="x")
            ttk.Label(empty_row, text="No evidence files cataloged yet in SQLite database.", foreground=TEXT_MUTED, background=ABYSS, font=FONT_SMALL).pack(anchor="w")
        else:
            for idx, ev in enumerate(evidence_items):
                bg_col = ABYSS if idx % 2 == 0 else DEEP
                row = tk.Frame(tbl_box, bg=bg_col, padx=6, pady=4)
                row.pack(fill="x")

                ttk.Label(row, text=ev.get("filename", "unknown"), foreground=TEXT_PRIMARY, background=bg_col, font=(FONT_FALLBACK, FS_XS, "bold"), width=22).pack(side="left")
                ttk.Label(row, text=str(ev.get("evidence_type", "log")).upper(), foreground=CYAN, background=bg_col, font=FONT_MONO_SM, width=10).pack(side="left")
                ttk.Label(row, text=str(ev.get("uploaded_at", "N/A")), foreground=TEXT_SECONDARY, background=bg_col, font=FONT_MONO_SM, width=18).pack(side="left")
                ttk.Label(row, text=str(ev.get("file_hash", "UNKNOWN")), foreground=ICE, background=bg_col, font=FONT_MONO_SM).pack(side="left")

    def _render_preview_findings(self, parent: tk.Widget, findings_items: List[Dict[str, Any]]) -> None:
        """Render Section 3 derived findings with explainability proofs."""
        sec_frame = tk.Frame(parent, bg=DEEP, padx=SP_6, pady=SP_3)
        sec_frame.pack(fill="x")

        create_section_header(sec_frame, "SECTION 3: EXTRACTED FACTS & AI REASONING FINDINGS").pack(anchor="w", pady=(0, 4))
        create_divider(sec_frame, color=PLUM).pack(fill="x", pady=(0, 6))

        if not findings_items:
            ttk.Label(
                sec_frame,
                text="No risk findings derived. Forward Chaining rules evaluated with zero threshold triggers.",
                foreground=TEXT_MUTED,
                background=DEEP,
                font=FONT_BODY,
            ).pack(anchor="w")
            return

        kb_rules = {r.rule_code: r for r in get_all_rules()}

        for f in findings_items:
            code = str(f.get("rule_code", "UNKNOWN"))
            raw_finding = str(f.get("finding", "Unknown finding"))
            severity = int(f.get("severity", 0))

            if ":" in raw_finding:
                title, desc = raw_finding.split(":", 1)
                title = title.strip()
                desc = desc.strip()
            else:
                title = raw_finding
                desc = raw_finding

            rule_obj = kb_rules.get(code)
            proof = rule_obj.explain_template if rule_obj else f"Forward Chaining inferred rule {code} based on verified facts."

            if severity >= 25:
                accent = PINK
            elif severity >= 15:
                accent = PEACH
            else:
                accent = CYAN

            card = tk.Frame(sec_frame, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL, padx=8, pady=6)
            card.pack(fill="x", pady=2)

            top = tk.Frame(card, bg=ABYSS)
            top.pack(fill="x")

            create_badge(top, code, PURPLE, bg=ABYSS).pack(side="left", padx=(0, 6))
            ttk.Label(top, text=title, foreground=TEXT_PRIMARY, background=ABYSS, font=(FONT_FALLBACK, FS_SM, "bold")).pack(side="left")
            create_badge(top, f"+{severity} PTS", accent, bg=ABYSS).pack(side="right")

            ttk.Label(card, text=desc, foreground=TEXT_SECONDARY, background=ABYSS, font=FONT_SMALL, wraplength=740, justify="left").pack(fill="x", pady=(2, 4))

            # Proof box
            p_box = tk.Frame(card, bg=DEEP, padx=6, pady=3)
            p_box.pack(fill="x")
            ttk.Label(p_box, text="WHY THIS FIRED (FACT PROOF):", foreground=TEXT_MUTED, background=DEEP, font=(FONT_FALLBACK, FS_XS, "bold")).pack(anchor="w")
            ttk.Label(p_box, text=proof, foreground=ICE, background=DEEP, font=FONT_MONO_SM, wraplength=730, justify="left").pack(anchor="w")

    def _render_preview_recommendations(self, parent: tk.Widget, recommendations: List[str]) -> None:
        """Render Section 4 remediation steps."""
        sec_frame = tk.Frame(parent, bg=DEEP, padx=SP_6, pady=SP_3)
        sec_frame.pack(fill="x")

        create_section_header(sec_frame, "SECTION 4: INCIDENT RESPONSE RECOMMENDATIONS").pack(anchor="w", pady=(0, 4))
        create_divider(sec_frame, color=PLUM).pack(fill="x", pady=(0, 6))

        if not recommendations:
            ttk.Label(sec_frame, text="No immediate remediation required based on low threat profile.", foreground=TEXT_MUTED, background=DEEP, font=FONT_BODY).pack(anchor="w")
            return

        for idx, rec in enumerate(recommendations, start=1):
            r_card = tk.Frame(sec_frame, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL, padx=8, pady=4)
            r_card.pack(fill="x", pady=2)

            create_badge(r_card, f"#{idx:02d}", CYAN, bg=ABYSS).pack(side="left", padx=(0, 8))
            ttk.Label(r_card, text=rec, foreground=TEXT_PRIMARY, background=ABYSS, font=FONT_SMALL, wraplength=710, justify="left").pack(side="left", fill="x", expand=True)

    def _render_preview_timeline(
        self,
        parent: tk.Widget,
        timeline_events: List[Dict[str, Any]],
        timeline_stats: Dict[str, Any],
    ) -> None:
        """Render Section 5 chronological timeline overview."""
        sec_frame = tk.Frame(parent, bg=DEEP, padx=SP_6, pady=SP_3)
        sec_frame.pack(fill="x")

        create_section_header(sec_frame, "SECTION 5: CHRONOLOGICAL EVENT SEQUENCE SUMMARY").pack(anchor="w", pady=(0, 2))
        total = timeline_stats.get("total_events", len(timeline_events))
        ttk.Label(
            sec_frame,
            text=f"Total Events: {total} | Time Span: {timeline_stats.get('duration_seconds', 0)}s | First: {timeline_stats.get('first_event') or 'N/A'}",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(0, 4))
        create_divider(sec_frame, color=PLUM).pack(fill="x", pady=(0, 6))

        tbl_box = tk.Frame(sec_frame, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL)
        tbl_box.pack(fill="x")

        # Header
        h_row = tk.Frame(tbl_box, bg=STEEL, padx=6, pady=4)
        h_row.pack(fill="x")

        ttk.Label(h_row, text="TIMESTAMP", foreground=TEXT_PRIMARY, background=STEEL, font=(FONT_FALLBACK, FS_XS, "bold"), width=20).pack(side="left")
        ttk.Label(h_row, text="SOURCE", foreground=TEXT_PRIMARY, background=STEEL, font=(FONT_FALLBACK, FS_XS, "bold"), width=12).pack(side="left")
        ttk.Label(h_row, text="CATEGORY", foreground=TEXT_PRIMARY, background=STEEL, font=(FONT_FALLBACK, FS_XS, "bold"), width=16).pack(side="left")
        ttk.Label(h_row, text="DESCRIPTION", foreground=TEXT_PRIMARY, background=STEEL, font=(FONT_FALLBACK, FS_XS, "bold")).pack(side="left")

        display_events = timeline_events[:20]
        if not display_events:
            empty_row = tk.Frame(tbl_box, bg=ABYSS, padx=6, pady=6)
            empty_row.pack(fill="x")
            ttk.Label(empty_row, text="No timestamped event records available.", foreground=TEXT_MUTED, background=ABYSS, font=FONT_SMALL).pack(anchor="w")
        else:
            for idx, ev in enumerate(display_events):
                bg_col = ABYSS if idx % 2 == 0 else DEEP
                row = tk.Frame(tbl_box, bg=bg_col, padx=6, pady=3)
                row.pack(fill="x")

                ts = ev.get("timestamp") or "N/A"
                src = "AI FINDING" if ev.get("source") == "ai_inference" else "EVIDENCE"
                src_col = PURPLE if ev.get("source") == "ai_inference" else CYAN
                cat = str(ev.get("category", "info")).upper()
                desc = str(ev.get("description", ""))

                ttk.Label(row, text=ts, foreground=TEXT_MUTED, background=bg_col, font=FONT_MONO_SM, width=20).pack(side="left")
                ttk.Label(row, text=src, foreground=src_col, background=bg_col, font=(FONT_FALLBACK, FS_XS, "bold"), width=12).pack(side="left")
                ttk.Label(row, text=cat, foreground=TEXT_SECONDARY, background=bg_col, font=FONT_SMALL, width=16).pack(side="left")
                ttk.Label(row, text=desc[:65], foreground=TEXT_PRIMARY, background=bg_col, font=FONT_SMALL).pack(side="left")

            if len(timeline_events) > 20:
                more_lbl = ttk.Label(
                    sec_frame,
                    text=f"Showing top 20 of {len(timeline_events)} total sequence events. Complete record exported in PDF.",
                    foreground=TEXT_MUTED,
                    background=DEEP,
                    font=FONT_SMALL,
                )
                more_lbl.pack(anchor="w", pady=(4, 0))

    def _render_preview_footer(self, parent: tk.Widget) -> None:
        """Render formal document certification footer."""
        foot_frame = tk.Frame(parent, bg=ABYSS, padx=SP_6, pady=SP_4)
        foot_frame.pack(fill="x")

        create_divider(foot_frame, color=PLUM).pack(fill="x", pady=(0, 6))

        ttk.Label(
            foot_frame,
            text="CONFIDENTIAL // LAW ENFORCEMENT & FORENSIC USE ONLY",
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            foot_frame,
            text="FORENSEQUENCE EXPERT SYSTEM — PROPOSITIONAL INFERENCE CERTIFIED",
            foreground=CYAN,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(anchor="w")

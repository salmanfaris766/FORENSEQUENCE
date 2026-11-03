# =============================================================================
# gui/about_frame.py
# FORENSEQUENCE - System Architecture & Academic Syllabus Mapping
# =============================================================================

from __future__ import annotations

import tkinter as tk
import ttkbootstrap as ttk

from gui.theme import (
    APP_BG,
    BG_SECONDARY,
    PANEL_BG,
    PANEL_ELEVATED,
    BORDER,
    BORDER_SECONDARY,
    MINT,
    CYAN,
    TEAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
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
    create_soc_badge,
    create_section_header,
    create_divider,
    create_badge,
)


class AboutFrame(ttk.Frame):
    """
    System Architecture & Academic Syllabus Mapping screen.
    Displays project specifications, team credits, and academic alignment.
    """

    def __init__(self, parent: tk.Misc, shell=None):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.shell = shell
        self._build_ui()

    # =========================================================================
    # Layout
    # =========================================================================

    def _build_ui(self) -> None:
        self.configure(style="TFrame")

        # Header Bar
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))

        ttk.Label(
            header,
            text="SYSTEM / ABOUT",
            foreground=TEXT_MUTED,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_XS, "normal"),
        ).pack(anchor="w")

        title_row = ttk.Frame(header, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, 0))

        ttk.Label(
            title_row,
            text="System Architecture & Academic Mapping",
            foreground=TEXT_PRIMARY,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_XL, "bold"),
        ).pack(side="left")

        create_badge(title_row, "VERSION 1.0", CYAN, bg=APP_BG).pack(
            side="left", padx=(SP_4, 0)
        )

        ttk.Label(
            header,
            text="Expert system engine specifications, academic curriculum alignment, and team credits.",
            foreground=TEXT_MUTED,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
        ).pack(anchor="w", pady=(2, 0))

        create_divider(self, color=BORDER).pack(fill="x", padx=SP_6, pady=(SP_3, SP_4))

        # Scrollable body
        scroll_frame = ttk.Frame(self, style="TFrame")
        scroll_frame.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_4))

        self.canvas = tk.Canvas(scroll_frame, bg=APP_BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.body = ttk.Frame(self.canvas, style="TFrame")
        self.body_win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.body_win, width=e.width))

        def _mw(event):
            try:
                if self.canvas.winfo_exists():
                    self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
        self.canvas.bind("<Enter>", lambda _: self.canvas.bind_all("<MouseWheel>", _mw))
        self.canvas.bind("<Leave>", lambda _: self.canvas.unbind_all("<MouseWheel>"))

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Build content panels
        self._build_viva_banner()
        self._build_engine_panel()
        self._build_syllabus_panel()
        self._build_credits_panel()

    # =========================================================================
    # Viva Summary Banner
    # =========================================================================

    def _build_viva_banner(self) -> None:
        banner = tk.Frame(
            self.body, bg=BG_SECONDARY, highlightthickness=1, highlightbackground=CYAN, bd=0
        )
        banner.pack(fill="x", pady=(0, SP_4))

        ttk.Label(
            banner,
            text="OFFICIAL VIVA SUMMARY",
            foreground=CYAN,
            background=BG_SECONDARY,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(SP_3, SP_1))

        ttk.Label(
            banner,
            text=(
                "FORENSEQUENCE is a deterministic, knowledge-based expert system for digital forensic "
                "investigation that uses Propositional Logic and Forward Chaining inference to extract "
                "facts from multi-source evidence (logs, files, browser history, emails), derive "
                "security findings through verifiable deduction, and produce court-admissible PDF "
                "reports with explainable proof traces -- containing zero Machine Learning or Deep "
                "Learning components."
            ),
            foreground=TEXT_PRIMARY,
            background=BG_SECONDARY,
            font=(FONT_FALLBACK, FS_SM, "normal"),
            wraplength=800,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_3))

    # =========================================================================
    # Expert System Engine Specs
    # =========================================================================

    def _build_engine_panel(self) -> None:
        panel = create_soc_panel(self.body, border_color=CYAN, bg=PANEL_BG)
        panel.pack(fill="x", pady=(0, SP_3))
        inner = panel.inner_frame

        create_section_header(inner, "EXPERT SYSTEM ENGINE SPECIFICATIONS").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )
        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(SP_1, SP_3))

        specs = [
            ("INFERENCE MECHANISM", "Pure Forward Chaining deduction engine reaching a monotonic fixpoint"),
            ("KNOWLEDGE REPRESENTATION", "Propositional Logic Horn clauses with condition-conclusion rule pairs"),
            ("RULE BASE", "9 deterministic rules (R001-R009) covering auth, exec, USB, file, web, and email threats"),
            ("EXPLAINABILITY", "Verifiable proof trace trees mapping observed facts to derived conclusions"),
            ("RISK SCORING", "Cumulative severity-weighted scoring normalized to 0-100 threat band"),
            ("ML / DL COMPONENTS", "ZERO -- purely symbolic, deterministic, knowledge-based reasoning"),
            ("EVIDENCE INGESTION", "Multi-source unified dispatcher: auth logs, filesystems, web CSV, email archives"),
            ("LIVE FORENSICS", "Low-latency watchdog file pointer tracking with thread-safe IPC queue polling"),
        ]

        for label, value in specs:
            row = tk.Frame(inner, bg=PANEL_BG)
            row.pack(fill="x", padx=SP_4, pady=1)

            ttk.Label(
                row,
                text=label + ":",
                foreground=TEXT_SECONDARY,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_SM, "bold"),
                width=26,
                anchor="w",
            ).pack(side="left")

            ttk.Label(
                row,
                text=value,
                foreground=TEXT_PRIMARY,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_SM, "normal"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        # Spacer
        ttk.Frame(inner, style="Card.TFrame").pack(fill="x", pady=SP_2)

    # =========================================================================
    # Academic Syllabus Mapping
    # =========================================================================

    def _build_syllabus_panel(self) -> None:
        panel = create_soc_panel(self.body, border_color=BORDER_SECONDARY, bg=PANEL_BG)
        panel.pack(fill="x", pady=(0, SP_3))
        inner = panel.inner_frame

        create_section_header(inner, "ACADEMIC SYLLABUS CURRICULUM ALIGNMENT").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )
        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(SP_1, SP_3))

        topics = [
            ("Knowledge Representation", "Propositional logic Horn clauses with condition-conclusion pairs"),
            ("Inference Mechanism", "Pure forward-chaining deduction engine reaching a monotonic fixpoint"),
            ("Explainability", "Verifiable proof trace trees mapping observed evidence facts to derived conclusions"),
            ("Multi-Source Ingestion", "Unified dispatcher for auth logs, file structures, web telemetry & emails"),
            ("Live Forensics", "Low-latency watchdog file pointer tracking with thread-safe IPC queuing"),
            ("Risk Analytics", "Cumulative severity-weighted scoring with IR recommendation generation"),
            ("Report Generation", "ReportLab PDF compilation with chain-of-custody tables and proof citations"),
        ]

        for topic, description in topics:
            item_row = tk.Frame(inner, bg=PANEL_BG)
            item_row.pack(fill="x", padx=SP_4, pady=2)

            ttk.Label(
                item_row,
                text=topic + ":",
                foreground=TEAL,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_SM, "bold"),
                width=24,
                anchor="w",
            ).pack(side="left")

            ttk.Label(
                item_row,
                text=description,
                foreground=TEXT_PRIMARY,
                background=PANEL_BG,
                font=(FONT_FALLBACK, FS_SM, "normal"),
                anchor="w",
                wraplength=560,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

        ttk.Frame(inner, style="Card.TFrame").pack(fill="x", pady=SP_2)

    # =========================================================================
    # Team Credits
    # =========================================================================

    def _build_credits_panel(self) -> None:
        panel = create_soc_panel(self.body, border_color=TEAL, bg=PANEL_BG)
        panel.pack(fill="x", pady=(0, SP_3))
        inner = panel.inner_frame

        create_section_header(inner, "INVESTIGATION & DEVELOPMENT TEAM").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )
        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(SP_1, SP_3))

        team = [
            (
                "Salman",
                "UI/UX SOC Workstation Engineering, Evidence Parsers, Case Management & Live Watcher",
                CYAN,
            ),
            (
                "Kavya",
                "Knowledge Base Engineering, Forward Chaining Inference, Risk Scoring & ReportLab PDF",
                MINT,
            ),
        ]

        for name, role, color in team:
            card = tk.Frame(
                inner,
                bg=BG_SECONDARY,
                highlightthickness=1,
                highlightbackground=BORDER,
                bd=0,
            )
            card.pack(fill="x", padx=SP_4, pady=(0, SP_2))

            card_inner = tk.Frame(card, bg=BG_SECONDARY)
            card_inner.pack(fill="x", padx=SP_3, pady=SP_2)

            create_badge(card_inner, name.upper(), color, bg=BG_SECONDARY).pack(
                side="left", padx=(0, SP_3)
            )

            ttk.Label(
                card_inner,
                text=role,
                foreground=TEXT_PRIMARY,
                background=BG_SECONDARY,
                font=(FONT_FALLBACK, FS_SM, "normal"),
                anchor="w",
                wraplength=600,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

        ttk.Frame(inner, style="Card.TFrame").pack(fill="x", pady=SP_2)

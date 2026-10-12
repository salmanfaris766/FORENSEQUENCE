# =============================================================================
# gui/case_detail_frame.py
# FORENSEQUENCE - Case Detail & Evidence Management Screen
# =============================================================================

import hashlib
import os
import shutil
import tkinter as tk
from tkinter import filedialog
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
    create_styled_entry,
)

from database import (
    get_case_by_id,
    add_evidence,
    get_evidence_for_case,
    get_findings_for_case,
    get_all_cases,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hexadecimal digest of a file in 64KB chunks
    for memory efficiency and forensic chain-of-custody verification.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


class CaseDetailFrame(ttk.Frame):
    """
    Case Detail & Evidence Management screen.
    Displays granular case metadata, provides an evidence ingestion interface
    with automated SHA-256 hashing, and maintains an interactive inventory.
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

        # Inherit selected case context from shell if not explicitly provided
        if self.case_id is None and self.shell and getattr(self.shell, "selected_case_id", None):
            self.case_id = self.shell.selected_case_id

        self.selected_evidence_type = "log"
        self.type_buttons = {}
        self.selected_file_path = ""
        self._is_importing = False

        self._build_ui()
        self.refresh_data()

    def set_case(self, case_id: Optional[int]) -> None:
        """Update active investigation case and reload all views."""
        self.case_id = case_id
        self.refresh_data()

    # -------------------------------------------------------------------------
    # Layout Builder
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct the visual hierarchy."""
        self.configure(style="TFrame")

        # Top section bar
        self.header_bar = ttk.Frame(self, style="TFrame")
        self.header_bar.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))

        header_left = ttk.Frame(self.header_bar, style="TFrame")
        header_left.pack(side="left", fill="y")

        create_section_header(header_left, "INVESTIGATION EVIDENCE MANAGEMENT").pack(anchor="w")

        title_row = ttk.Frame(header_left, style="TFrame")
        title_row.pack(anchor="w", pady=(SP_1, 0))

        ttk.Label(
            title_row,
            text="Chain of Custody & Evidence Explorer",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        badge = create_badge(title_row, "SHA-256 VERIFIED", PURPLE)
        badge.pack(side="left", padx=(SP_4, 0))

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(SP_2, SP_4))

        # Dynamic Content Container (swapped between Empty State and Case Detail)
        self.main_content = ttk.Frame(self, style="TFrame")
        self.main_content.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_4))

    # -------------------------------------------------------------------------
    # View State Rendering
    # -------------------------------------------------------------------------

    def refresh_data(self) -> None:
        """Reload case details and inventory list from SQLite."""
        for child in self.main_content.winfo_children():
            child.destroy()

        case = get_case_by_id(self.case_id) if self.case_id is not None else None

        if not case:
            self._render_no_case_state()
            return

        self._render_active_case_layout(case)

    def _render_no_case_state(self) -> None:
        """Display placeholder glass card when no case context is active."""
        center_box = ttk.Frame(self.main_content, style="TFrame")
        center_box.pack(expand=True, fill="both")

        glass = create_glass_frame(
            center_box,
            width=800,
            height=280,
            border_color=STEEL,
            fill_color=DEEP,
        )
        glass.pack(anchor="center", pady=SP_8)
        inner = glass.inner_frame

        create_section_header(inner, "NO ACTIVE CASE CONTEXT").pack(
            anchor="w", padx=SP_6, pady=(SP_6, SP_2)
        )

        ttk.Label(
            inner,
            text="No Investigation Case Selected",
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=FONT_SUBHEADING,
        ).pack(anchor="w", padx=SP_6, pady=(0, SP_2))

        ttk.Label(
            inner,
            text="Select an investigation from the Dashboard or Case Archive to view,\n"
                 "catalog, and compute SHA-256 integrity hashes for evidence artifacts.",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_BODY,
            justify="left",
        ).pack(anchor="w", padx=SP_6, pady=(0, SP_6))

        btn_box = ttk.Frame(inner, style="Card.TFrame")
        btn_box._custom_bg = DEEP
        btn_box.pack(anchor="w", padx=SP_6)

        btn_goto_archive = create_neon_button(
            btn_box,
            text="[GOTO CASE ARCHIVE]",
            command=lambda: self._navigate("Cases"),
            variant="primary",
            bg=DEEP,
        )
        btn_goto_archive.pack(side="left", padx=(0, SP_3))

        btn_dashboard = create_neon_button(
            btn_box,
            text="[VIEW DASHBOARD]",
            command=lambda: self._navigate("Dashboard"),
            variant="secondary",
            bg=DEEP,
        )
        btn_dashboard.pack(side="left")

    def _render_active_case_layout(self, case: dict) -> None:
        """Render the complete investigation header and two-column evidence workspace."""
        # 1. Top Case Header Card (Glass Panel)
        header_card = create_glass_frame(
            self.main_content,
            width=960,
            height=110,
            border_color=PURPLE,
            fill_color=DEEP,
        )
        header_card.pack(fill="x", pady=(0, SP_3))
        inner_h = header_card.inner_frame

        # Left Info Block: Badges, Name, Investigator, Timestamp
        left_meta = ttk.Frame(inner_h, style="Card.TFrame")
        left_meta._custom_bg = DEEP
        left_meta.pack(side="left", fill="both", expand=True, padx=SP_4, pady=SP_2)

        meta_top = ttk.Frame(left_meta, style="Card.TFrame")
        meta_top._custom_bg = DEEP
        meta_top.pack(fill="x", pady=(0, 2))

        case_num = case.get("case_number", "CASE-UNKNOWN")
        badge_num = create_badge(meta_top, case_num, CYAN, bg=DEEP)
        badge_num.pack(side="left", padx=(0, SP_2))

        status_str = str(case.get("status", "OPEN")).upper()
        status_color = CYAN if status_str == "OPEN" else (PEACH if status_str == "INVESTIGATING" else TEXT_MUTED)
        badge_st = create_badge(meta_top, status_str, status_color, bg=DEEP)
        badge_st.pack(side="left", padx=(0, SP_3))

        created_at = str(case.get("created_at", ""))
        ttk.Label(
            meta_top,
            text=f"INITIALIZED: {created_at}",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_MONO_SM,
        ).pack(side="left")

        # Case Name & Investigator
        case_name = case.get("case_name", "Untitled Case")
        ttk.Label(
            left_meta,
            text=case_name,
            foreground=TEXT_PRIMARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_MD, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 1))

        inv_text = f"Investigator: {case.get('investigator', 'Unassigned')}"
        desc_text = str(case.get("description", "") or "").strip()
        sub_text = f"{inv_text}  |  {desc_text[:60]}..." if desc_text else inv_text
        ttk.Label(
            left_meta,
            text=sub_text,
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x")

        # Right Action Bar: Quick Nav Buttons
        right_actions = ttk.Frame(inner_h, style="Card.TFrame")
        right_actions._custom_bg = DEEP
        right_actions.pack(side="right", fill="y", padx=SP_4, pady=SP_3)

        btn_ai = create_neon_button(
            right_actions,
            text="[RUN AI ANALYSIS]",
            command=lambda: self._navigate("Analysis"),
            variant="primary",
            bg=DEEP,
        )
        btn_ai.pack(side="top", fill="x", pady=(0, 3))

        sub_btns = ttk.Frame(right_actions, style="Card.TFrame")
        sub_btns._custom_bg = DEEP
        sub_btns.pack(side="top", fill="x")

        btn_monitor = create_neon_button(
            sub_btns,
            text="[LIVE MONITOR]",
            command=lambda: self._navigate("Live Monitor"),
            variant="secondary",
            bg=DEEP,
        )
        btn_monitor.pack(side="left", padx=(0, 3))

        btn_back = create_neon_button(
            sub_btns,
            text="[BACK TO CASES]",
            command=lambda: self._navigate("Cases"),
            variant="ghost",
            bg=DEEP,
        )
        btn_back.pack(side="left")

        # ---------------------------------------------------------------------
        # 2. Two-Column Body Layout (Import Evidence & Evidence Inventory)
        # ---------------------------------------------------------------------
        cols_container = ttk.Frame(self.main_content, style="TFrame")
        cols_container.pack(fill="both", expand=True)

        # Left Column (40% width): Import Evidence
        left_col = ttk.Frame(cols_container, style="TFrame", width=420)
        left_col.pack(side="left", fill="both", expand=False, padx=(0, SP_3))
        left_col.pack_propagate(False)

        self._build_import_panel(left_col)

        # Right Column (60% width): Evidence Inventory
        right_col = ttk.Frame(cols_container, style="TFrame")
        right_col.pack(side="left", fill="both", expand=True)

        self._build_inventory_panel(right_col)

    # -------------------------------------------------------------------------
    # Panel 1: Import Evidence
    # -------------------------------------------------------------------------

    def _build_import_panel(self, parent_col: ttk.Frame) -> None:
        """Render the evidence upload and hashing form."""
        glass = create_glass_frame(
            parent_col,
            width=420,
            height=490,
            border_color=CYAN,
            fill_color=DEEP,
        )
        glass.pack(fill="both", expand=True)
        inner = glass.inner_frame

        create_section_header(inner, "IMPORT EVIDENCE ARTIFACT").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )

        ttk.Label(
            inner,
            text="Select forensic artifacts for SHA-256 integrity validation and ingestion.",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_SMALL,
            wraplength=380,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_3))

        # File Picker Row
        ttk.Label(
            inner,
            text="TARGET ARTIFACT FILE *",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

        picker_box = ttk.Frame(inner, style="Card.TFrame")
        picker_box._custom_bg = DEEP
        picker_box.pack(fill="x", padx=SP_4, pady=(0, SP_3))

        self.entry_path = create_styled_entry(picker_box, placeholder="No file selected")
        self.entry_path.config(state="readonly")
        self.entry_path.pack(side="left", fill="x", expand=True, ipady=3, padx=(0, SP_2))

        btn_browse = create_neon_button(
            picker_box,
            text="[BROWSE]",
            command=self._handle_browse_file,
            variant="secondary",
            bg=DEEP,
        )
        btn_browse.pack(side="right")

        # Evidence Type Selector
        ttk.Label(
            inner,
            text="EVIDENCE CATEGORY",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

        type_box = ttk.Frame(inner, style="Card.TFrame")
        type_box._custom_bg = DEEP
        type_box.pack(fill="x", padx=SP_4, pady=(0, SP_3))

        type_specs = [
            ("log", "LOG", CYAN),
            ("file", "FILE", PEACH),
            ("browser", "BROWSER", PURPLE),
            ("email", "EMAIL", PINK),
        ]

        self.type_buttons = {}
        for cat_id, cat_label, cat_color in type_specs:
            btn = tk.Button(
                type_box,
                text=cat_label,
                font=(FONT_FALLBACK, FS_XS, "bold"),
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda cid=cat_id: self._select_evidence_type(cid),
            )
            btn.pack(side="left", padx=(0, 4), ipadx=6, ipady=3)
            self.type_buttons[cat_id] = (btn, cat_color)

        self._select_evidence_type("log")

        # Action Button: [IMPORT & HASH EVIDENCE]
        btn_action_box = ttk.Frame(inner, style="Card.TFrame")
        btn_action_box._custom_bg = DEEP
        btn_action_box.pack(anchor="w", padx=SP_4, pady=(SP_1, SP_3))

        self.btn_import = create_neon_button(
            btn_action_box,
            text="[IMPORT & HASH EVIDENCE]",
            command=self._handle_import_submit,
            variant="primary",
            bg=DEEP,
        )
        self.btn_import.pack(side="left")

        # Status & SHA-256 Result Box
        self.status_box = tk.Frame(
            inner,
            bg=ABYSS,
            highlightthickness=1,
            highlightbackground=PLUM,
            bd=0,
        )
        self.status_box.pack(fill="x", padx=SP_4, pady=(SP_1, SP_2))

        self.lbl_import_status = ttk.Label(
            self.status_box,
            text="STATUS: READY FOR INGESTION",
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=FONT_MONO_SM,
            anchor="w",
        )
        self.lbl_import_status.pack(fill="x", padx=SP_3, pady=(SP_2, 2))

        self.lbl_hash_display = ttk.Label(
            self.status_box,
            text="SHA-256: --",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_MONO_SM,
            wraplength=370,
            anchor="w",
        )
        self.lbl_hash_display.pack(fill="x", padx=SP_3, pady=(0, SP_2))

    def _select_evidence_type(self, type_id: str) -> None:
        """Update active category selection and toggle button highlights."""
        self.selected_evidence_type = type_id
        for cat_id, (btn, color) in self.type_buttons.items():
            if cat_id == type_id:
                btn.config(
                    bg=DEEP,
                    fg=color,
                    activebackground=DEEP,
                    activeforeground=color,
                    highlightthickness=1,
                    highlightbackground=color,
                )
            else:
                btn.config(
                    bg=ABYSS,
                    fg=TEXT_MUTED,
                    activebackground=ABYSS,
                    activeforeground=TEXT_SECONDARY,
                    highlightthickness=1,
                    highlightbackground=PLUM,
                )

    def _detect_evidence_type(self, filename: str) -> str:
        """Infer evidence category from filename extension."""
        ext = os.path.splitext(filename)[1].lower()
        if ext in (".log", ".evt", ".evtx", ".txt"):
            return "log"
        elif ext in (".csv", ".sqlite", ".sqlite3", ".db", ".history"):
            return "browser"
        elif ext in (".eml", ".msg", ".mbox", ".pst", ".ost"):
            return "email"
        else:
            return "file"

    def _handle_browse_file(self) -> None:
        """Open system file picker and populate selection."""
        filetypes = [
            ("Forensic Evidence", "*.log;*.txt;*.csv;*.json;*.dat;*.pcap;*.eml;*.msg;*.sqlite;*.db"),
            ("Log Files", "*.log;*.txt;*.evt;*.evtx"),
            ("Browser & Data", "*.csv;*.sqlite;*.sqlite3;*.json;*.db"),
            ("Email Archives", "*.eml;*.msg;*.mbox"),
            ("All Files", "*.*"),
        ]
        chosen = filedialog.askopenfilename(
            title="Select Forensic Evidence File",
            filetypes=filetypes,
        )
        if chosen:
            self.selected_file_path = chosen
            self.entry_path.config(state="normal")
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, chosen)
            self.entry_path.config(state="readonly")

            # Auto-detect category
            detected = self._detect_evidence_type(os.path.basename(chosen))
            self._select_evidence_type(detected)

            self.lbl_import_status.config(
                text=f"SELECTED: {os.path.basename(chosen)}", foreground=CYAN
            )
            self.lbl_hash_display.config(text="SHA-256: [PENDING VERIFICATION]", foreground=TEXT_MUTED)

    # -------------------------------------------------------------------------
    # Panel 2: Evidence Inventory
    # -------------------------------------------------------------------------

    def _build_inventory_panel(self, parent_col: ttk.Frame) -> None:
        """Render the scrollable evidence repository list."""
        glass = create_glass_frame(
            parent_col,
            width=540,
            height=490,
            border_color=STEEL,
            fill_color=DEEP,
        )
        glass.pack(fill="both", expand=True)
        inner = glass.inner_frame

        # Header Row
        inv_hdr = ttk.Frame(inner, style="Card.TFrame")
        inv_hdr._custom_bg = DEEP
        inv_hdr.pack(fill="x", padx=SP_4, pady=(SP_3, SP_1))

        create_section_header(inv_hdr, "EVIDENCE INVENTORY").pack(side="left")

        self.lbl_inv_count = ttk.Label(
            inv_hdr,
            text="0 ARTIFACTS",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_MONO_SM,
        )
        self.lbl_inv_count.pack(side="right")

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(SP_1, SP_2))

        # Scrollable Canvas
        scroll_wrapper = ttk.Frame(inner, style="Card.TFrame")
        scroll_wrapper._custom_bg = DEEP
        scroll_wrapper.pack(fill="both", expand=True, padx=SP_2, pady=(0, SP_2))

        self.inv_canvas = tk.Canvas(scroll_wrapper, bg=DEEP, highlightthickness=0, bd=0)
        self.inv_scrollbar = ttk.Scrollbar(
            scroll_wrapper, orient="vertical", command=self.inv_canvas.yview
        )
        self.inv_canvas.configure(yscrollcommand=self.inv_scrollbar.set)

        self.inv_content = ttk.Frame(self.inv_canvas, style="Card.TFrame")
        self.inv_content._custom_bg = DEEP
        self.inv_window_id = self.inv_canvas.create_window(
            (0, 0), window=self.inv_content, anchor="nw"
        )

        def _on_inv_content_configure(event):
            self.inv_canvas.configure(scrollregion=self.inv_canvas.bbox("all"))

        def _on_inv_canvas_configure(event):
            self.inv_canvas.itemconfig(self.inv_window_id, width=event.width)

        self.inv_content.bind("<Configure>", _on_inv_content_configure)
        self.inv_canvas.bind("<Configure>", _on_inv_canvas_configure)

        def _on_mousewheel(event):
            self.inv_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.inv_canvas.bind("<Enter>", lambda _: self.inv_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.inv_canvas.bind("<Leave>", lambda _: self.inv_canvas.unbind_all("<MouseWheel>"))

        self.inv_canvas.pack(side="left", fill="both", expand=True)
        self.inv_scrollbar.pack(side="right", fill="y")

        self.refresh_evidence_list()

    def refresh_evidence_list(self) -> None:
        """Re-query SQLite for this case's evidence and rebuild inventory cards."""
        if not hasattr(self, "inv_content") or not self.inv_content.winfo_exists():
            return

        for child in self.inv_content.winfo_children():
            child.destroy()

        if self.case_id is None:
            return

        evidence_items = get_evidence_for_case(self.case_id)
        self.lbl_inv_count.config(text=f"{len(evidence_items)} ARTIFACTS")

        if not evidence_items:
            empty_box = ttk.Frame(self.inv_content, style="Card.TFrame")
            empty_box._custom_bg = DEEP
            empty_box.pack(fill="x", padx=SP_4, pady=SP_6)

            ttk.Label(
                empty_box,
                text="NO EVIDENCE IMPORTED",
                foreground=TEXT_SECONDARY,
                background=DEEP,
                font=(FONT_FALLBACK, FS_MD, "bold"),
            ).pack(anchor="w", pady=(0, SP_1))

            ttk.Label(
                empty_box,
                text="No evidence imported for this case. Use the Import Evidence form to upload logs, files, browser CSVs, or emails.",
                foreground=TEXT_MUTED,
                background=DEEP,
                font=FONT_BODY,
                wraplength=480,
                justify="left",
            ).pack(anchor="w")
            return

        for item in evidence_items:
            self._render_evidence_card(item)

    def _render_evidence_card(self, item: dict) -> None:
        """Render a single evidence artifact item card."""
        card = tk.Frame(
            self.inv_content,
            bg=ABYSS,
            highlightthickness=1,
            highlightbackground=STEEL,
            bd=0,
        )
        card.pack(fill="x", padx=SP_2, pady=SP_2)

        # Header Line: Type Badge + Uploaded Timestamp
        top_line = tk.Frame(card, bg=ABYSS)
        top_line.pack(fill="x", padx=SP_3, pady=(SP_2, 2))

        ev_type = str(item.get("evidence_type", "FILE")).upper()
        type_colors = {"LOG": CYAN, "FILE": PEACH, "BROWSER": PURPLE, "EMAIL": PINK}
        type_color = type_colors.get(ev_type, CYAN)

        badge_type = create_badge(top_line, ev_type, type_color, bg=ABYSS)
        badge_type.pack(side="left", padx=(0, SP_2))

        uploaded_at = str(item.get("uploaded_at", ""))
        ttk.Label(
            top_line,
            text=uploaded_at,
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="right")

        # Filename
        filename = item.get("filename", "Unknown File")
        ttk.Label(
            card,
            text=filename,
            foreground=TEXT_PRIMARY,
            background=ABYSS,
            font=(FONT_FALLBACK, FS_BASE, "bold"),
            anchor="w",
        ).pack(fill="x", padx=SP_3, pady=(0, 1))

        # Stored Path (truncated if long)
        file_path = str(item.get("file_path", ""))
        display_path = file_path if len(file_path) <= 60 else "..." + file_path[-57:]
        ttk.Label(
            card,
            text=f"PATH: {display_path}",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x", padx=SP_3, pady=(0, 2))

        # SHA-256 Hash Box + Copy Button
        hash_val = str(item.get("file_hash", ""))
        hash_box = tk.Frame(card, bg=DEEP)
        hash_box.pack(fill="x", padx=SP_3, pady=(0, SP_2))

        ttk.Label(
            hash_box,
            text=f"SHA-256: {hash_val}",
            foreground=ICE,
            background=DEEP,
            font=FONT_MONO_SM,
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=SP_2, pady=2)

        def _copy_hash():
            self.clipboard_clear()
            self.clipboard_append(hash_val)

        btn_copy = create_neon_button(
            hash_box,
            text="[COPY]",
            command=_copy_hash,
            variant="ghost",
            bg=DEEP,
        )
        btn_copy.pack(side="right", padx=(0, SP_1), pady=1)

    # -------------------------------------------------------------------------
    # Core Logic: Ingestion & Hashing
    # -------------------------------------------------------------------------

    def _handle_import_submit(self) -> None:
        """Validate selection, compute SHA-256, store in uploads/, and record in SQLite."""
        if self._is_importing:
            return

        if not self.case_id:
            self._show_import_error("No active investigation selected.")
            return

        src_path = self.selected_file_path.strip()
        if not src_path or not os.path.exists(src_path):
            self._show_import_error("Please browse and select a valid evidence file.")
            return

        self._is_importing = True
        self.lbl_import_status.config(text="COMPUTING SHA-256 HASH...", foreground=PINK)
        self.status_box.config(highlightbackground=PINK)
        self.update_idletasks()

        try:
            filename = os.path.basename(src_path)
            file_hash = calculate_sha256(src_path)

            os.makedirs(UPLOADS_DIR, exist_ok=True)
            dest_filename = f"{self.case_id}_{filename}"
            dest_path = os.path.join(UPLOADS_DIR, dest_filename)

            if os.path.abspath(src_path) != os.path.abspath(dest_path):
                shutil.copy2(src_path, dest_path)

            evidence_id = add_evidence(
                case_id=self.case_id,
                filename=filename,
                evidence_type=self.selected_evidence_type,
                file_path=dest_path,
                file_hash=file_hash,
            )

            # Success confirmation
            self.lbl_import_status.config(
                text=f"REGISTERED #{evidence_id}: {filename}", foreground=CYAN
            )
            self.lbl_hash_display.config(text=f"SHA-256: {file_hash}", foreground=ICE)
            self.status_box.config(highlightbackground=CYAN)

            # Clear entry and refresh list
            self.selected_file_path = ""
            self.entry_path.config(state="normal")
            self.entry_path.delete(0, tk.END)
            self.entry_path.config(state="readonly")

            self.refresh_evidence_list()

        except Exception as ex:
            self._show_import_error(f"Import Failed: {str(ex)}")
        finally:
            self._is_importing = False

    def _show_import_error(self, message: str) -> None:
        """Display an ingestion error in pink."""
        self.lbl_import_status.config(text=f"ERROR: {message}", foreground=PINK)
        self.lbl_hash_display.config(text="SHA-256: --", foreground=TEXT_MUTED)
        self.status_box.config(highlightbackground=PINK)

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def _navigate(self, route_name: str) -> None:
        """Route to another application screen."""
        if self.on_navigate:
            self.on_navigate(route_name)
        elif self.shell:
            self.shell.show_screen(route_name)

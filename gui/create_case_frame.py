# =============================================================================
# gui/create_case_frame.py
# FORENSEQUENCE - Case Investigation & Repository Screen
# =============================================================================

from __future__ import annotations

import sqlite3
import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional, Callable

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
    RADIUS_SM,
    create_soc_panel,
    create_soc_button,
    create_soc_badge,
    create_soc_entry,
    create_section_header,
    create_divider,
    # Legacy aliases kept for backward-compatible theme helpers
    VOID, ABYSS, DEEP, STEEL, PINK, PEACH, PURPLE, PLUM, ICE,
    FONT_HEADING, FONT_SUBHEADING, FONT_SECTION, FONT_BODY, FONT_SMALL, FONT_MONO_SM,
    create_glass_frame, create_neon_button, create_badge, create_styled_entry,
)

from database import (
    initialize_db,
    create_case,
    get_all_cases,
    update_case_status,
    get_case_by_id,
)


_STATUS_COLORS = {
    "OPEN": CYAN,
    "INVESTIGATING": HIGH,
    "CLOSED": TEXT_MUTED,
}


class CreateCaseFrame(ttk.Frame):
    """
    Case Investigation & Repository screen.
    Validated intake form for registering digital forensic investigations
    and a scrollable archive panel for browsing and opening cases.
    """

    def __init__(
        self,
        parent: tk.Misc,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_case_created: Optional[Callable[[int], None]] = None,
        on_open_case: Optional[Callable[[int], None]] = None,
        shell=None,
        **kwargs,
    ):
        super().__init__(parent, style="TFrame")
        self.parent = parent
        self.on_navigate = on_navigate
        self.on_case_created = on_case_created
        self.on_open_case = on_open_case
        self.shell = shell

        self._is_saving = False
        self.selected_status = "OPEN"
        self.status_buttons: dict = {}

        initialize_db()
        self._build_ui()
        self.refresh_data()

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
            text="WORKSPACE / CASE INVESTIGATION",
            foreground=TEXT_MUTED,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_XS, "normal"),
        ).pack(anchor="w")

        title_row = ttk.Frame(header, style="TFrame")
        title_row.pack(fill="x", pady=(SP_1, 0))

        ttk.Label(
            title_row,
            text="Case Intake & Repository",
            foreground=TEXT_PRIMARY,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_XL, "bold"),
        ).pack(side="left")

        self.badge_count = create_badge(title_row, "0 CASES", TEXT_MUTED, bg=APP_BG)
        self.badge_count.pack(side="left", padx=(SP_4, 0))

        ttk.Label(
            header,
            text="Register new forensic investigations and manage active case files.",
            foreground=TEXT_MUTED,
            background=APP_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
        ).pack(anchor="w", pady=(2, 0))

        create_divider(self, color=BORDER).pack(fill="x", padx=SP_6, pady=(SP_3, SP_4))

        # Two-column body
        self.main_container = ttk.Frame(self, style="TFrame")
        self.main_container.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_4))
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=4)
        self.main_container.grid_columnconfigure(1, weight=6)

        left_col = ttk.Frame(self.main_container, style="TFrame")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, SP_3))
        self._build_intake_panel(left_col)

        right_col = ttk.Frame(self.main_container, style="TFrame")
        right_col.grid(row=0, column=1, sticky="nsew")
        self._build_archive_panel(right_col)

    # =========================================================================
    # Left Panel: NEW CASE INTAKE
    # =========================================================================

    def _build_intake_panel(self, parent: ttk.Frame) -> None:
        panel = create_soc_panel(parent, border_color=CYAN, bg=PANEL_BG)
        panel.pack(fill="both", expand=True)
        inner = panel.inner_frame

        create_section_header(inner, "NEW CASE INTAKE").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )
        ttk.Label(
            inner,
            text="Initialize a forensic case and record chain-of-custody metadata.",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
            wraplength=380,
            justify="left",
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_3))

        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(0, SP_3))

        self._field_label(inner, "CASE NUMBER *")
        self.entry_case_num = create_soc_entry(inner, placeholder="CASE-2025-001")
        self.entry_case_num.pack(fill="x", padx=SP_4, pady=(0, SP_3), ipady=3)
        self.entry_case_num.bind("<Return>", lambda e: self._on_submit())

        self._field_label(inner, "CASE NAME *")
        self.entry_case_name = create_soc_entry(
            inner, placeholder="e.g., Operation Nightfall Intrusion"
        )
        self.entry_case_name.pack(fill="x", padx=SP_4, pady=(0, SP_3), ipady=3)
        self.entry_case_name.bind("<Return>", lambda e: self._on_submit())

        self._field_label(inner, "ASSIGNED INVESTIGATOR *")
        self.entry_investigator = create_soc_entry(inner, placeholder="")
        self.entry_investigator.insert(0, "Salman")
        self.entry_investigator.config(fg=TEXT_PRIMARY)
        self.entry_investigator.pack(fill="x", padx=SP_4, pady=(0, SP_3), ipady=3)
        self.entry_investigator.bind("<Return>", lambda e: self._on_submit())

        self._field_label(inner, "CASE DESCRIPTION (OPTIONAL)")
        self.txt_desc = tk.Text(
            inner,
            height=3,
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            font=(FONT_FALLBACK, FS_SM, "normal"),
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=CYAN,
            wrap="word",
            bd=0,
        )
        self.txt_desc.pack(fill="x", padx=SP_4, pady=(0, SP_3))

        self._field_label(inner, "INITIAL STATUS")
        status_box = ttk.Frame(inner, style="Card.TFrame")
        status_box._custom_bg = PANEL_BG
        status_box.pack(fill="x", padx=SP_4, pady=(0, SP_3))

        for st in ("OPEN", "INVESTIGATING", "CLOSED"):
            btn = tk.Button(
                status_box,
                text=st,
                font=(FONT_FALLBACK, FS_XS, "bold"),
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda s=st: self._select_status(s),
            )
            btn.pack(side="left", padx=(0, SP_2), ipadx=8, ipady=3)
            self.status_buttons[st] = btn

        self._select_status("OPEN")

        btn_row = ttk.Frame(inner, style="Card.TFrame")
        btn_row._custom_bg = PANEL_BG
        btn_row.pack(anchor="w", padx=SP_4, pady=(SP_1, SP_2))

        self.btn_create = create_soc_button(
            btn_row,
            text="CREATE INVESTIGATION",
            command=self._on_submit,
            variant="primary",
            bg=PANEL_BG,
        )
        self.btn_create.pack(side="left", padx=(0, SP_2))

        self.btn_clear = create_soc_button(
            btn_row,
            text="CLEAR FORM",
            command=self._clear_form,
            variant="ghost",
            bg=PANEL_BG,
        )
        self.btn_clear.pack(side="left")

        self.lbl_feedback = ttk.Label(
            inner,
            text="",
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_SM, "bold"),
            anchor="w",
            wraplength=400,
        )
        self.lbl_feedback.pack(fill="x", padx=SP_4, pady=(SP_2, 0))

    def _field_label(self, parent: tk.Misc, text: str) -> None:
        ttk.Label(
            parent,
            text=text,
            foreground=TEXT_SECONDARY,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

    def _select_status(self, st: str) -> None:
        self.selected_status = st
        for name, btn in self.status_buttons.items():
            if name == st:
                accent = _STATUS_COLORS.get(name, CYAN)
                btn.config(
                    bg=PANEL_BG,
                    fg=accent,
                    activebackground=PANEL_BG,
                    activeforeground=accent,
                    highlightthickness=1,
                    highlightbackground=accent,
                )
            else:
                btn.config(
                    bg=BG_SECONDARY,
                    fg=TEXT_MUTED,
                    activebackground=BG_SECONDARY,
                    activeforeground=TEXT_SECONDARY,
                    highlightthickness=1,
                    highlightbackground=BORDER,
                )

    # =========================================================================
    # Right Panel: CASE REPOSITORY ARCHIVE
    # =========================================================================

    def _build_archive_panel(self, parent: ttk.Frame) -> None:
        panel = create_soc_panel(parent, border_color=BORDER_SECONDARY, bg=PANEL_BG)
        panel.pack(fill="both", expand=True)
        inner = panel.inner_frame

        arch_header = ttk.Frame(inner, style="Card.TFrame")
        arch_header._custom_bg = PANEL_BG
        arch_header.pack(fill="x", padx=SP_4, pady=(SP_3, SP_1))

        create_section_header(arch_header, "CASE REPOSITORY ARCHIVE").pack(side="left")

        self.lbl_archive_count = ttk.Label(
            arch_header,
            text="0 CASES",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_MONO_FALLBACK, FS_SM, "normal"),
        )
        self.lbl_archive_count.pack(side="right")

        create_divider(inner, color=BORDER).pack(fill="x", padx=SP_4, pady=(SP_1, SP_2))

        scroll_wrapper = ttk.Frame(inner, style="Card.TFrame")
        scroll_wrapper._custom_bg = PANEL_BG
        scroll_wrapper.pack(fill="both", expand=True, padx=SP_2, pady=(0, SP_2))

        self.archive_canvas = tk.Canvas(
            scroll_wrapper, bg=PANEL_BG, highlightthickness=0, bd=0
        )
        self.archive_scrollbar = ttk.Scrollbar(
            scroll_wrapper, orient="vertical", command=self.archive_canvas.yview
        )
        self.archive_canvas.configure(yscrollcommand=self.archive_scrollbar.set)

        self.archive_content = ttk.Frame(self.archive_canvas, style="Card.TFrame")
        self.archive_content._custom_bg = PANEL_BG
        self.archive_win_id = self.archive_canvas.create_window(
            (0, 0), window=self.archive_content, anchor="nw"
        )

        def _on_content_configure(event):
            self.archive_canvas.configure(scrollregion=self.archive_canvas.bbox("all"))

        def _on_canvas_configure(event):
            self.archive_canvas.itemconfig(self.archive_win_id, width=event.width)

        self.archive_content.bind("<Configure>", _on_content_configure)
        self.archive_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            try:
                if self.archive_canvas.winfo_exists():
                    self.archive_canvas.yview_scroll(
                        int(-1 * (event.delta / 120)), "units"
                    )
            except Exception:
                pass

        self.archive_canvas.bind(
            "<Enter>",
            lambda _: self.archive_canvas.bind_all("<MouseWheel>", _on_mousewheel),
        )
        self.archive_canvas.bind(
            "<Leave>", lambda _: self.archive_canvas.unbind_all("<MouseWheel>")
        )

        self.archive_canvas.pack(side="left", fill="both", expand=True)
        self.archive_scrollbar.pack(side="right", fill="y")

    # =========================================================================
    # Data & Rendering
    # =========================================================================

    def refresh_data(self) -> None:
        cases = get_all_cases()
        count = len(cases)
        self.lbl_archive_count.config(text=f"{count} CASES")

        for child in self.archive_content.winfo_children():
            child.destroy()

        if not cases:
            self._render_empty_state()
        else:
            for case in cases:
                self._render_case_card(case)

    def _render_empty_state(self) -> None:
        frame = ttk.Frame(self.archive_content, style="Card.TFrame")
        frame._custom_bg = PANEL_BG
        frame.pack(fill="x", padx=SP_4, pady=SP_8)

        ttk.Label(
            frame,
            text="NO CASES IN REPOSITORY",
            foreground=TEXT_SECONDARY,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_MD, "bold"),
        ).pack(anchor="w", pady=(0, SP_1))

        ttk.Label(
            frame,
            text="No investigation cases recorded. Use the intake form to create a new case.",
            foreground=TEXT_MUTED,
            background=PANEL_BG,
            font=(FONT_FALLBACK, FS_SM, "normal"),
            wraplength=380,
            justify="left",
        ).pack(anchor="w")

    def _render_case_card(self, case: dict) -> None:
        card = tk.Frame(
            self.archive_content,
            bg=BG_SECONDARY,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )
        card.pack(fill="x", padx=SP_2, pady=(0, SP_2))

        top = tk.Frame(card, bg=BG_SECONDARY)
        top.pack(fill="x", padx=SP_3, pady=(SP_2, SP_1))

        case_num = case.get("case_number", "CASE-???")
        create_badge(top, case_num, TEAL, bg=BG_SECONDARY).pack(
            side="left", padx=(0, SP_2)
        )

        status_str = str(case.get("status", "OPEN")).upper()
        st_color = _STATUS_COLORS.get(status_str, TEXT_MUTED)
        create_badge(top, status_str, st_color, bg=BG_SECONDARY).pack(
            side="left", padx=(0, SP_2)
        )

        created_at = str(case.get("created_at", ""))
        ttk.Label(
            top,
            text=created_at,
            foreground=TEXT_MUTED,
            background=BG_SECONDARY,
            font=(FONT_MONO_FALLBACK, FS_XS, "normal"),
        ).pack(side="right")

        case_name = case.get("case_name", "Untitled")
        ttk.Label(
            card,
            text=case_name,
            foreground=TEXT_PRIMARY,
            background=BG_SECONDARY,
            font=(FONT_FALLBACK, FS_BASE, "bold"),
            anchor="w",
        ).pack(fill="x", padx=SP_3, pady=(0, 1))

        investigator = case.get("investigator", "Unassigned")
        ttk.Label(
            card,
            text=f"Investigator: {investigator}",
            foreground=TEXT_SECONDARY,
            background=BG_SECONDARY,
            font=(FONT_FALLBACK, FS_SM, "normal"),
            anchor="w",
        ).pack(fill="x", padx=SP_3, pady=(0, SP_2))

        action_row = tk.Frame(card, bg=BG_SECONDARY)
        action_row.pack(fill="x", padx=SP_3, pady=(0, SP_2))

        case_id = case.get("id")

        btn_open = create_soc_button(
            action_row,
            text="OPEN INVESTIGATION",
            command=lambda cid=case_id: self._handle_open_case(cid),
            variant="primary",
            bg=BG_SECONDARY,
        )
        btn_open.pack(side="left", padx=(0, SP_2))

        next_status_map = {
            "OPEN": "INVESTIGATING",
            "INVESTIGATING": "CLOSED",
            "CLOSED": "OPEN",
        }
        next_st = next_status_map.get(status_str, "OPEN")
        btn_cycle = create_soc_button(
            action_row,
            text=f"-> {next_st}",
            command=lambda cid=case_id, ns=next_st: self._handle_cycle_status(cid, ns),
            variant="ghost",
            bg=BG_SECONDARY,
        )
        btn_cycle.pack(side="left")

    # =========================================================================
    # Form Logic
    # =========================================================================

    def _on_submit(self) -> None:
        if self._is_saving:
            return

        case_num = self._get_val(self.entry_case_num, "CASE-2025-001")
        case_name = self._get_val(
            self.entry_case_name, "e.g., Operation Nightfall Intrusion"
        )
        investigator = self._get_val(self.entry_investigator, "")
        description = self.txt_desc.get("1.0", tk.END).strip()

        if not case_num:
            self._show_error("Case Number is required.")
            self.entry_case_num.focus_set()
            return
        if not case_name:
            self._show_error("Case Name is required.")
            self.entry_case_name.focus_set()
            return
        if not investigator:
            self._show_error("Assigned Investigator is required.")
            self.entry_investigator.focus_set()
            return

        self._is_saving = True
        try:
            case_id = create_case(
                case_number=case_num,
                case_name=case_name,
                investigator=investigator,
                description=description,
                status=self.selected_status,
            )
            self._show_success(
                f"Case '{case_num}' registered successfully (ID #{case_id})."
            )
            self._clear_form(preserve_feedback=True)
            self.refresh_data()

            if self.on_case_created:
                self.on_case_created(case_id)
            elif self.shell:
                self.shell.set_case_context(f"CASE: {case_num} | {case_name}")
                self.shell.selected_case_id = case_id

        except sqlite3.IntegrityError:
            self._show_error(
                f"Case Number '{case_num}' already exists. Use a unique identifier."
            )
        except Exception as ex:
            self._show_error(f"Database Error: {ex}")
        finally:
            self.after(400, lambda: setattr(self, "_is_saving", False))

    def _get_val(self, entry: tk.Entry, placeholder: str = "") -> str:
        val = entry.get().strip()
        return "" if (placeholder and val == placeholder) else val

    def _show_error(self, message: str) -> None:
        self.lbl_feedback.config(text=f"ERROR: {message}", foreground=CRITICAL)

    def _show_success(self, message: str) -> None:
        self.lbl_feedback.config(text=message, foreground=CYAN)

    def _clear_form(self, preserve_feedback: bool = False) -> None:
        self.entry_case_num.delete(0, tk.END)
        self.entry_case_num.insert(0, "CASE-2025-001")
        self.entry_case_num.config(fg=TEXT_MUTED)

        self.entry_case_name.delete(0, tk.END)
        self.entry_case_name.insert(0, "e.g., Operation Nightfall Intrusion")
        self.entry_case_name.config(fg=TEXT_MUTED)

        self.entry_investigator.delete(0, tk.END)
        self.entry_investigator.insert(0, "Salman")
        self.entry_investigator.config(fg=TEXT_PRIMARY)

        self.txt_desc.delete("1.0", tk.END)
        self._select_status("OPEN")

        if not preserve_feedback:
            self.lbl_feedback.config(text="")

    def _handle_open_case(self, case_id: int) -> None:
        if self.on_open_case:
            self.on_open_case(case_id)
        elif self.shell:
            self.shell._handle_dashboard_select_case(case_id)

    def _handle_cycle_status(self, case_id: int, new_status: str) -> None:
        update_case_status(case_id, new_status)
        self.refresh_data()
        if self.shell and getattr(self.shell, "selected_case_id", None) == case_id:
            case = get_case_by_id(case_id)
            if case:
                self.shell.set_case_context(
                    f"CASE: {case['case_number']} | {case['case_name']}"
                )

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
        elif self.shell:
            self.shell.show_screen(route)

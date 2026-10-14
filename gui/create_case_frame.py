# =============================================================================
# gui/create_case_frame.py
# FORENSEQUENCE - Case Management, Intake & Archive Screen
# =============================================================================

import sqlite3
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
    create_styled_entry,
)

from database import (
    initialize_db,
    create_case,
    get_all_cases,
    update_case_status,
    get_case_by_id,
)


class CreateCaseFrame(ttk.Frame):
    """
    Case Management & Intake screen.
    Provides a validated intake form to register new digital forensic investigations
    and an interactive archive panel to browse, filter, cycle statuses, and open cases.
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
        self.status_buttons = {}

        # Ensure database tables exist
        initialize_db()

        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        """Construct the split-view Cases interface."""
        self.configure(style="TFrame")

        # ---------------------------------------------------------------------
        # 1. Top Header Section
        # ---------------------------------------------------------------------
        header_bar = ttk.Frame(self, style="TFrame")
        header_bar.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))

        header_left = ttk.Frame(header_bar, style="TFrame")
        header_left.pack(side="left", fill="y")

        create_section_header(header_left, "CASE MANAGEMENT & INTAKE").pack(anchor="w")

        title_row = ttk.Frame(header_left, style="TFrame")
        title_row.pack(anchor="w", pady=(SP_1, 0))

        ttk.Label(
            title_row,
            text="Investigation Registry & Archive",
            foreground=TEXT_PRIMARY,
            background=VOID,
            font=FONT_HEADING,
        ).pack(side="left")

        badge = create_badge(title_row, "INTAKE MODULE", CYAN)
        badge.pack(side="left", padx=(SP_4, 0))

        create_divider(self, color=PLUM).pack(fill="x", padx=SP_6, pady=(SP_2, SP_4))

        # ---------------------------------------------------------------------
        # 2. Main Two-Column Layout
        # ---------------------------------------------------------------------
        self.main_container = ttk.Frame(self, style="TFrame")
        self.main_container.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_4))
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=4)
        self.main_container.grid_columnconfigure(1, weight=6)

        # --- Column A: CREATE NEW INVESTIGATION Panel (Left) ---
        self.left_column = ttk.Frame(self.main_container, style="TFrame")
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=(0, SP_4))

        self._build_create_panel()

        # --- Column B: CASE ARCHIVE Panel (Right) ---
        self.right_column = ttk.Frame(self.main_container, style="TFrame")
        self.right_column.grid(row=0, column=1, sticky="nsew")

        self._build_archive_panel()

    # -------------------------------------------------------------------------
    # Panel A: Create New Case
    # -------------------------------------------------------------------------

    def _build_create_panel(self) -> None:
        """Render the intake form glass panel."""
        glass = create_glass_frame(
            self.left_column,
            width=470,
            height=580,
            border_color=CYAN,
            fill_color=DEEP,
        )
        glass.pack(fill="both", expand=True)
        inner = glass.inner_frame

        # Panel Section Header
        create_section_header(inner, "CREATE NEW INVESTIGATION").pack(
            anchor="w", padx=SP_4, pady=(SP_3, SP_1)
        )

        ttk.Label(
            inner,
            text="Initialize a new forensic case and record chain-of-custody metadata.",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_SMALL,
        ).pack(anchor="w", padx=SP_4, pady=(0, SP_3))

        # Field 1: Case Number (Required)
        ttk.Label(
            inner,
            text="CASE NUMBER *",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

        self.entry_case_num = create_styled_entry(inner, placeholder="CASE-2025-001")
        self.entry_case_num.pack(fill="x", padx=SP_4, pady=(0, SP_2), ipady=3)
        self.entry_case_num.bind("<Return>", lambda e: self._on_submit_create())

        # Field 2: Case Name (Required)
        ttk.Label(
            inner,
            text="CASE NAME *",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

        self.entry_case_name = create_styled_entry(inner, placeholder="e.g., Operation Nightfall Intrusion")
        self.entry_case_name.pack(fill="x", padx=SP_4, pady=(0, SP_2), ipady=3)
        self.entry_case_name.bind("<Return>", lambda e: self._on_submit_create())

        # Field 3: Assigned Investigator (Required, default "Salman")
        ttk.Label(
            inner,
            text="ASSIGNED INVESTIGATOR *",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

        self.entry_investigator = create_styled_entry(inner, placeholder="")
        self.entry_investigator.insert(0, "Salman")
        self.entry_investigator.config(fg=TEXT_PRIMARY)
        self.entry_investigator.pack(fill="x", padx=SP_4, pady=(0, SP_2), ipady=3)
        self.entry_investigator.bind("<Return>", lambda e: self._on_submit_create())

        # Field 4: Description (Optional multi-line text)
        ttk.Label(
            inner,
            text="CASE DESCRIPTION (OPTIONAL)",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

        self.txt_desc = tk.Text(
            inner,
            height=3,
            bg=ABYSS,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            font=FONT_BODY,
            highlightthickness=1,
            highlightbackground=PLUM,
            highlightcolor=CYAN,
            wrap="word",
        )
        self.txt_desc.pack(fill="x", padx=SP_4, pady=(0, SP_2))

        # Field 5: Initial Status (Segmented control)
        ttk.Label(
            inner,
            text="INITIAL STATUS",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(anchor="w", padx=SP_4, pady=(0, 2))

        status_box = ttk.Frame(inner, style="Card.TFrame")
        status_box._custom_bg = DEEP
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

        # Action Buttons Row: [CREATE CASE] & [CLEAR FORM]
        btn_box = ttk.Frame(inner, style="Card.TFrame")
        btn_box._custom_bg = DEEP
        btn_box.pack(anchor="w", padx=SP_4, pady=(SP_1, SP_1))

        self.btn_create = create_neon_button(
            btn_box,
            text="[CREATE CASE]",
            command=self._on_submit_create,
            variant="primary",
            bg=DEEP,
        )
        self.btn_create.pack(side="left", padx=(0, SP_2))

        self.btn_clear = create_neon_button(
            btn_box,
            text="[CLEAR FORM]",
            command=self._clear_form,
            variant="ghost",
            bg=DEEP,
        )
        self.btn_clear.pack(side="left")

        # Inline Feedback Message (PINK for errors, CYAN for success)
        self.lbl_feedback = ttk.Label(
            inner,
            text="",
            background=DEEP,
            font=(FONT_FALLBACK, FS_SM, "bold"),
            anchor="w",
            wraplength=430,
        )
        self.lbl_feedback.pack(fill="x", padx=SP_4, pady=(SP_2, 0))

    def _select_status(self, st: str) -> None:
        """Update active status selection and toggle button visuals."""
        self.selected_status = st
        color_map = {"OPEN": CYAN, "INVESTIGATING": PEACH, "CLOSED": TEXT_MUTED}
        for name, btn in self.status_buttons.items():
            if name == st:
                accent = color_map.get(name, CYAN)
                btn.config(
                    bg=DEEP,
                    fg=accent,
                    activebackground=DEEP,
                    activeforeground=accent,
                    highlightthickness=1,
                    highlightbackground=accent,
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

    # -------------------------------------------------------------------------
    # Panel B: Case Archive
    # -------------------------------------------------------------------------

    def _build_archive_panel(self) -> None:
        """Render the scrollable archive panel of existing investigations."""
        glass = create_glass_frame(
            self.right_column,
            width=490,
            height=580,
            border_color=STEEL,
            fill_color=DEEP,
        )
        glass.pack(fill="both", expand=True)
        inner = glass.inner_frame

        # Archive Header Row
        archive_header = ttk.Frame(inner, style="Card.TFrame")
        archive_header._custom_bg = DEEP
        archive_header.pack(fill="x", padx=SP_4, pady=(SP_3, SP_1))

        create_section_header(archive_header, "CASE ARCHIVE").pack(side="left")

        self.lbl_archive_count = ttk.Label(
            archive_header,
            text="0 CASES",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_MONO_SM,
        )
        self.lbl_archive_count.pack(side="right")

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(SP_1, SP_2))

        # Scrollable Cases Container
        scroll_wrapper = ttk.Frame(inner, style="Card.TFrame")
        scroll_wrapper._custom_bg = DEEP
        scroll_wrapper.pack(fill="both", expand=True, padx=SP_2, pady=(0, SP_2))

        self.archive_canvas = tk.Canvas(
            scroll_wrapper,
            bg=DEEP,
            highlightthickness=0,
            bd=0,
        )
        self.archive_scrollbar = ttk.Scrollbar(
            scroll_wrapper,
            orient="vertical",
            command=self.archive_canvas.yview,
        )
        self.archive_canvas.configure(yscrollcommand=self.archive_scrollbar.set)

        self.archive_content = ttk.Frame(self.archive_canvas, style="Card.TFrame")
        self.archive_content._custom_bg = DEEP
        self.archive_window_id = self.archive_canvas.create_window(
            (0, 0), window=self.archive_content, anchor="nw"
        )

        def _on_content_configure(event):
            self.archive_canvas.configure(scrollregion=self.archive_canvas.bbox("all"))

        def _on_canvas_configure(event):
            self.archive_canvas.itemconfig(self.archive_window_id, width=event.width)

        self.archive_content.bind("<Configure>", _on_content_configure)
        self.archive_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            try:
                if self.archive_canvas.winfo_exists():
                    self.archive_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        self.archive_canvas.bind(
            "<Enter>", lambda _: self.archive_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        )
        self.archive_canvas.bind(
            "<Leave>", lambda _: self.archive_canvas.unbind_all("<MouseWheel>")
        )

        self.archive_canvas.pack(side="left", fill="both", expand=True)
        self.archive_scrollbar.pack(side="right", fill="y")

    # -------------------------------------------------------------------------
    # Data Reload & Rendering
    # -------------------------------------------------------------------------

    def refresh_data(self) -> None:
        """Reload all cases from SQLite and rebuild the archive list."""
        cases = get_all_cases()
        self.lbl_archive_count.config(text=f"{len(cases)} CASES")

        for child in self.archive_content.winfo_children():
            child.destroy()

        if not cases:
            self._render_empty_archive()
        else:
            for case in cases:
                self._render_archive_card(case)

    def _render_empty_archive(self) -> None:
        """Display placeholder in the archive panel when no cases exist."""
        empty_frame = ttk.Frame(self.archive_content, style="Card.TFrame")
        empty_frame._custom_bg = DEEP
        empty_frame.pack(fill="x", padx=SP_4, pady=SP_6)

        ttk.Label(
            empty_frame,
            text="NO CASES IN ARCHIVE",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_MD, "bold"),
        ).pack(anchor="w", pady=(0, SP_1))

        ttk.Label(
            empty_frame,
            text="No investigation cases recorded in database. Fill out the intake form on the left to initialize a case.",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_BODY,
            wraplength=420,
            justify="left",
        ).pack(anchor="w")

    def _render_archive_card(self, case: dict) -> None:
        """Render a single case archive entry as an interactive card."""
        row_frame = tk.Frame(
            self.archive_content,
            bg=ABYSS,
            highlightthickness=1,
            highlightbackground=STEEL,
            bd=0,
        )
        row_frame.pack(fill="x", padx=SP_2, pady=SP_2)

        # Header Row: Case Badge + Status Badge + Timestamp
        top_line = tk.Frame(row_frame, bg=ABYSS)
        top_line.pack(fill="x", padx=SP_3, pady=(SP_2, SP_1))

        case_num = case.get("case_number", "CASE-UNKNOWN")
        badge_num = create_badge(top_line, case_num, CYAN, bg=ABYSS)
        badge_num.pack(side="left", padx=(0, SP_2))

        status_str = str(case.get("status", "OPEN")).upper()
        if status_str == "OPEN":
            st_color = CYAN
        elif status_str == "INVESTIGATING":
            st_color = PEACH
        elif status_str == "CLOSED":
            st_color = TEXT_MUTED
        else:
            st_color = ICE

        badge_st = create_badge(top_line, status_str, st_color, bg=ABYSS)
        badge_st.pack(side="left", padx=(0, SP_2))

        time_val = str(case.get("created_at", ""))
        ttk.Label(
            top_line,
            text=time_val,
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=FONT_MONO_SM,
        ).pack(side="right")

        # Case Name
        ttk.Label(
            row_frame,
            text=case.get("case_name", "Untitled"),
            foreground=TEXT_PRIMARY,
            background=ABYSS,
            font=(FONT_FALLBACK, FS_BASE, "bold"),
            anchor="w",
        ).pack(fill="x", padx=SP_3, pady=(0, 2))

        # Investigator
        ttk.Label(
            row_frame,
            text=f"Investigator: {case.get('investigator', 'Unassigned')}",
            foreground=TEXT_SECONDARY,
            background=ABYSS,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x", padx=SP_3, pady=(0, 2))

        # Optional Description Preview
        desc_str = str(case.get("description", "") or "").strip()
        if desc_str:
            preview = desc_str if len(desc_str) <= 65 else desc_str[:62] + "..."
            ttk.Label(
                row_frame,
                text=preview,
                foreground=TEXT_MUTED,
                background=ABYSS,
                font=FONT_SMALL,
                anchor="w",
            ).pack(fill="x", padx=SP_3, pady=(0, 2))

        # Actions Row: [OPEN] and [CYCLE STATUS]
        actions_line = tk.Frame(row_frame, bg=ABYSS)
        actions_line.pack(fill="x", padx=SP_3, pady=(SP_1, SP_2))

        cid = case["id"]

        btn_open = create_neon_button(
            actions_line,
            text="[OPEN]",
            command=lambda c=cid: self._handle_open_case(c),
            variant="primary",
            bg=ABYSS,
        )
        btn_open.pack(side="left", padx=(0, SP_2))

        cycle_map = {"OPEN": "INVESTIGATING", "INVESTIGATING": "CLOSED", "CLOSED": "OPEN"}
        next_status = cycle_map.get(status_str, "OPEN")

        btn_cycle = create_neon_button(
            actions_line,
            text=f"[SET: {next_status}]",
            command=lambda c=cid, s=next_status: self._handle_cycle_status(c, s),
            variant="secondary",
            bg=ABYSS,
        )
        btn_cycle.pack(side="left")

    # -------------------------------------------------------------------------
    # Form Processing & Validation
    # -------------------------------------------------------------------------

    def _get_entry_value(self, entry: tk.Entry, placeholder: str = "") -> str:
        """Retrieve entry value, ignoring simulated placeholder text."""
        val = entry.get().strip()
        if placeholder and val == placeholder:
            return ""
        return val

    def _show_error(self, message: str) -> None:
        """Display an error message styled in PINK."""
        self.lbl_feedback.config(text=message, foreground=PINK)

    def _show_success(self, message: str) -> None:
        """Display a success confirmation message styled in CYAN."""
        self.lbl_feedback.config(text=message, foreground=CYAN)

    def _clear_form(self, preserve_feedback: bool = False) -> None:
        """Reset all intake inputs to defaults."""
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

    def _on_submit_create(self) -> None:
        """Validate input fields and insert new case record into SQLite."""
        if self._is_saving:
            return

        case_num = self._get_entry_value(self.entry_case_num, placeholder="CASE-2025-001")
        case_name = self._get_entry_value(
            self.entry_case_name, placeholder="e.g., Operation Nightfall Intrusion"
        )
        investigator = self._get_entry_value(self.entry_investigator, placeholder="")
        description = self.txt_desc.get("1.0", tk.END).strip()

        # Validation checks
        if not case_num:
            self._show_error("Validation Error: Case Number is required.")
            self.entry_case_num.focus_set()
            return

        if not case_name:
            self._show_error("Validation Error: Case Name is required.")
            self.entry_case_name.focus_set()
            return

        if not investigator:
            self._show_error("Validation Error: Assigned Investigator is required.")
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
            self._show_success(f"Case '{case_num}' registered successfully (ID #{case_id}).")
            self._clear_form(preserve_feedback=True)
            self.refresh_data()

            if self.on_case_created:
                self.on_case_created(case_id)
            elif self.shell:
                self.shell.set_case_context(f"CASE: {case_num} | {case_name}")
                self.shell.selected_case_id = case_id

        except sqlite3.IntegrityError:
            self._show_error(
                f"Error: Case Number '{case_num}' already exists. Please specify a unique identifier."
            )
        except Exception as ex:
            self._show_error(f"Database Error: {str(ex)}")
        finally:
            self.after(400, lambda: setattr(self, "_is_saving", False))

    # -------------------------------------------------------------------------
    # Case Actions
    # -------------------------------------------------------------------------

    def _handle_open_case(self, case_id: int) -> None:
        """Trigger open case callback to navigate to Evidence / Case Detail."""
        if self.on_open_case:
            self.on_open_case(case_id)
        elif self.shell:
            self.shell._handle_dashboard_select_case(case_id)

    def _handle_cycle_status(self, case_id: int, new_status: str) -> None:
        """Update case status in SQLite and reload archive view."""
        update_case_status(case_id, new_status)
        self.refresh_data()

        # If currently active case, update status context
        if self.shell and getattr(self.shell, "selected_case_id", None) == case_id:
            case = get_case_by_id(case_id)
            if case:
                self.shell.set_case_context(f"CASE: {case['case_number']} | {case['case_name']}")

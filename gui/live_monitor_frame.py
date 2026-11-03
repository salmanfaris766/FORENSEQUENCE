# =============================================================================
# gui/live_monitor_frame.py
# FORENSEQUENCE - Real-Time Live Evidence Monitor & Threaded Watcher UI
# =============================================================================
#
# Flagship Live Evidence Monitor featuring:
#   - Real-time background file monitoring via watchdog and thread-safe queue.Queue
#   - Main-thread polling loop via root.after() with winfo_exists() guards
#   - Live color-coded log event stream terminal with automatic autoscroll
#   - Real-time fact delta counters and embedded CyberpunkRiskGauge telemetry
#   - Automated live re-evaluation through Forward Chaining inference engine
#   - Shell status bar synchronization and graceful background thread shutdown
# =============================================================================

import os
import sys
import queue
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

import tkinter as tk
from tkinter import filedialog
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

from gui.risk_gauge_widget import CyberpunkRiskGauge
from gui.toast_notification import ToastNotificationManager
from monitoring.live_watcher import LiveMonitorManager
from ai.rule_engine import ForwardChainingEngine
from database import get_case_by_id, get_evidence_for_case

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LiveMonitorFrame(ttk.Frame):
    """
    Real-Time Background Live Evidence Monitor Screen.
    Monitors log files in real-time on background threads, processing incremental
    facts through a thread-safe queue and auto-updating AI findings.
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

        # Thread-safe event queue and background manager
        self.event_queue: queue.Queue = queue.Queue()
        self.monitor_manager = LiveMonitorManager(event_queue=self.event_queue)

        # Running accumulated facts state
        self.running_facts: Dict[str, Any] = {
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

        # Track session delta increments
        self.delta_increments: Dict[str, int] = {
            "failed_logins": 0,
            "executable_events": 0,
            "deleted_files": 0,
            "usb_connections": 0,
            "total_lines": 0,
        }

        self.latest_result: Dict[str, Any] = {}
        self._pulse_toggle = False

        # Track which rule codes have already fired to detect new firings
        self.known_fired_rules: set = set()

        try:
            self._build_ui()
            self._resolve_default_target_file()
        except Exception as e:
            import traceback
            print(f"Error drawing Live Monitor: {e}")
            traceback.print_exc()

        # Toast manager - root window resolved after UI is built
        try:
            self.toast_manager: ToastNotificationManager = ToastNotificationManager(
                self.winfo_toplevel()
            )
        except Exception:
            self.toast_manager = None

        # Start thread-safe queue polling loop
        self._poll_scheduled = True
        self.after(200, self.poll_queue)

        # Bind destruction to stop background watcher cleanly
        self.bind("<Destroy>", self._on_destroy)

    def set_case(self, case_id: Optional[int]) -> None:
        """Update active investigation case and point to its log evidence if available."""
        self.case_id = case_id
        self._update_case_badge()
        self._resolve_default_target_file()

    def _on_destroy(self, event=None) -> None:
        """Cleanly terminate background watchdog observer upon widget teardown."""
        self._poll_scheduled = False
        if self.monitor_manager.is_monitoring():
            self.monitor_manager.stop_monitoring()
        if self.shell and hasattr(self.shell, "set_live_state"):
            self.shell.set_live_state(False)

    # -------------------------------------------------------------------------
    # Layout Builder
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct the visual hierarchy of the Live Monitor interface."""
        self.configure(style="TFrame")

        self.main_container = ttk.Frame(self, style="TFrame")
        self.main_container.pack(fill="both", expand=True)

        # ---------------------------------------------------------------------
        # 1. Top Control & Status Bar (Glass Panel)
        # ---------------------------------------------------------------------
        ctrl_card = create_glass_frame(
            self.main_container, width=960, height=92, border_color=PURPLE, fill_color=DEEP
        )
        ctrl_card.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))
        inner_ctrl = ctrl_card.inner_frame

        # Left Section: Header, Case Badge, and Target File Row
        left_ctrl = ttk.Frame(inner_ctrl, style="Card.TFrame")
        left_ctrl._custom_bg = DEEP
        left_ctrl.pack(side="left", fill="both", expand=True, padx=SP_4, pady=SP_2)

        hdr_row = ttk.Frame(left_ctrl, style="Card.TFrame")
        hdr_row._custom_bg = DEEP
        hdr_row.pack(fill="x")

        create_section_header(hdr_row, "REAL-TIME LIVE EVIDENCE MONITOR").pack(side="left")

        self.case_badge_container = ttk.Frame(hdr_row, style="Card.TFrame")
        self.case_badge_container._custom_bg = DEEP
        self.case_badge_container.pack(side="left", padx=(SP_3, SP_2))
        self._update_case_badge()

        # Status badge container
        self.status_badge_container = ttk.Frame(hdr_row, style="Card.TFrame")
        self.status_badge_container._custom_bg = DEEP
        self.status_badge_container.pack(side="left")
        self.badge_status = create_badge(self.status_badge_container, "STANDBY", CYAN, bg=DEEP)
        self.badge_status.pack(side="left")

        # File Selection Row
        file_row = ttk.Frame(left_ctrl, style="Card.TFrame")
        file_row._custom_bg = DEEP
        file_row.pack(fill="x", pady=(4, 0))

        ttk.Label(
            file_row,
            text="WATCH TARGET:",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=(FONT_FALLBACK, FS_XS, "bold"),
        ).pack(side="left", padx=(0, SP_2))

        self.entry_target_path = ttk.Entry(
            file_row,
            font=FONT_MONO_SM,
        )
        self.entry_target_path.pack(side="left", fill="x", expand=True, padx=(0, SP_2))

        # Browse File & Folder Buttons
        self.btn_browse = tk.Label(
            file_row,
            text="[FILE]",
            font=(FONT_FALLBACK, FS_XS, "bold"),
            bg=ABYSS,
            fg=CYAN,
            cursor="hand2",
            padx=6,
            pady=2,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=STEEL,
        )
        self.btn_browse.pack(side="left", padx=(0, 2))
        self.btn_browse.bind("<Enter>", lambda _: self.btn_browse.configure(fg=ICE, bg=DEEP))
        self.btn_browse.bind("<Leave>", lambda _: self.btn_browse.configure(fg=CYAN, bg=ABYSS))
        self.btn_browse.bind("<Button-1>", lambda _: self._browse_target_file())

        self.btn_browse_folder = tk.Label(
            file_row,
            text="[FOLDER]",
            font=(FONT_FALLBACK, FS_XS, "bold"),
            bg=ABYSS,
            fg=PEACH,
            cursor="hand2",
            padx=6,
            pady=2,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=STEEL,
        )
        self.btn_browse_folder.pack(side="left")
        self.btn_browse_folder.bind("<Enter>", lambda _: self.btn_browse_folder.configure(fg=ICE, bg=DEEP))
        self.btn_browse_folder.bind("<Leave>", lambda _: self.btn_browse_folder.configure(fg=PEACH, bg=ABYSS))
        self.btn_browse_folder.bind("<Button-1>", lambda _: self._browse_target_folder())

        # Right Action Buttons: [START LIVE MONITORING] and [STOP WATCHER]
        right_ctrl = ttk.Frame(inner_ctrl, style="Card.TFrame")
        right_ctrl._custom_bg = DEEP
        right_ctrl.pack(side="right", fill="y", padx=SP_4, pady=SP_2)

        self.btn_start = create_neon_button(
            right_ctrl,
            text="[START LIVE MONITORING]",
            command=self.start_monitoring,
            variant="primary",
            bg=DEEP,
        )
        self.btn_start.pack(side="top", fill="x", pady=(0, 2))

        self.btn_stop = create_neon_button(
            right_ctrl,
            text="[STOP WATCHER]",
            command=self.stop_monitoring,
            variant="danger",
            bg=DEEP,
        )
        self.btn_stop.pack(side="top", fill="x")

        # ---------------------------------------------------------------------
        # 2. Telemetry & Fact Delta Display (Middle Row)
        # ---------------------------------------------------------------------
        telem_card = create_glass_frame(
            self.main_container, width=960, height=115, border_color=CYAN, fill_color=DEEP
        )
        telem_card.pack(fill="x", padx=SP_6, pady=(0, SP_2))
        inner_telem = telem_card.inner_frame

        # Left sub-block: CyberpunkRiskGauge
        gauge_box = ttk.Frame(inner_telem, style="Card.TFrame")
        gauge_box._custom_bg = DEEP
        gauge_box.pack(side="left", fill="y", padx=SP_3, pady=2)

        self.risk_gauge = CyberpunkRiskGauge(
            gauge_box,
            size=115,
            score=0,
            compact=True,
            bg=DEEP,
        )
        self.risk_gauge.pack()

        create_divider(inner_telem, color=PLUM, orient="vertical").pack(side="left", fill="y", padx=SP_2, pady=SP_2)

        # Right sub-block: 5 Fact Delta Metric Cards
        self.delta_box = ttk.Frame(inner_telem, style="Card.TFrame")
        self.delta_box._custom_bg = DEEP
        self.delta_box.pack(side="left", fill="both", expand=True, padx=SP_2, pady=4)

        self.stat_val_labels: Dict[str, ttk.Label] = {}
        self.stat_inc_labels: Dict[str, ttk.Label] = {}

        metrics_spec = [
            ("failed_logins", "FAILED LOGINS", PINK),
            ("executable_events", "EXEC EVENTS", PURPLE),
            ("deleted_files", "DELETED FILES", MAGENTA),
            ("usb_connections", "USB EVENTS", PEACH),
            ("total_lines", "LINES STREAMED", ICE),
        ]

        for key, title, col in metrics_spec:
            card = tk.Frame(self.delta_box, bg=ABYSS, highlightthickness=1, highlightbackground=STEEL, padx=8, pady=4)
            card.pack(side="left", fill="both", expand=True, padx=2)

            ttk.Label(card, text=title, foreground=TEXT_MUTED, background=ABYSS, font=(FONT_FALLBACK, FS_XS, "bold")).pack(anchor="w")

            val_row = tk.Frame(card, bg=ABYSS)
            val_row.pack(fill="x", pady=(2, 0))

            lbl_val = ttk.Label(val_row, text="0", foreground=col, background=ABYSS, font=(FONT_DISPLAY, 16, "bold"))
            lbl_val.pack(side="left")
            self.stat_val_labels[key] = lbl_val

            lbl_inc = ttk.Label(val_row, text="(+0)", foreground=TEXT_MUTED, background=ABYSS, font=FONT_MONO_SM)
            lbl_inc.pack(side="left", padx=(4, 0))
            self.stat_inc_labels[key] = lbl_inc

        # ---------------------------------------------------------------------
        # 3. Main Split Content Area (50% Terminal, 50% Live Findings)
        # ---------------------------------------------------------------------
        self.split_container = ttk.Frame(self.main_container, style="TFrame")
        self.split_container.pack(fill="both", expand=True, padx=SP_6, pady=(0, SP_4))
        self.split_container.grid_rowconfigure(0, weight=1)
        self.split_container.grid_columnconfigure(0, weight=1)
        self.split_container.grid_columnconfigure(1, weight=1)

        # --- Left Column: Live Log Event Stream Terminal ---
        self.left_column = ttk.Frame(self.split_container, style="TFrame")
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=(0, SP_2))

        self._build_terminal_panel()

        # --- Right Column: Live Triggered Findings & Reasoning ---
        self.right_column = ttk.Frame(self.split_container, style="TFrame")
        self.right_column.grid(row=0, column=1, sticky="nsew", padx=(SP_2, 0))

        self._build_findings_panel()

    def _build_terminal_panel(self) -> None:
        """Render the dark monospace streaming terminal with syntax highlighting."""
        glass = create_glass_frame(
            self.left_column, width=470, height=360, border_color=CYAN, fill_color=ABYSS
        )
        glass.pack(fill="both", expand=True)
        inner = glass.inner_frame

        # Terminal Header Bar
        hdr_row = ttk.Frame(inner, style="Panel.TFrame")
        hdr_row._custom_bg = ABYSS
        hdr_row.pack(fill="x", padx=SP_4, pady=(SP_2, 2))

        create_section_header(hdr_row, "LIVE LOG EVENT STREAM").pack(side="left")

        right_term = ttk.Frame(hdr_row, style="Panel.TFrame")
        right_term._custom_bg = ABYSS
        right_term.pack(side="right")

        self.lbl_stream_count = ttk.Label(
            right_term,
            text="0 LINES STREAMED",
            foreground=TEXT_MUTED,
            background=ABYSS,
            font=FONT_MONO_SM,
        )
        self.lbl_stream_count.pack(side="left", padx=(0, SP_2))

        # Clear Terminal Button
        btn_clear_term = tk.Label(
            right_term,
            text="[CLEAR]",
            font=(FONT_FALLBACK, FS_XS, "bold"),
            bg=DEEP,
            fg=TEXT_SECONDARY,
            cursor="hand2",
            padx=4,
            pady=1,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=STEEL,
        )
        btn_clear_term.pack(side="left")
        btn_clear_term.bind("<Button-1>", lambda _: self._clear_terminal())

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(2, 4))

        # Text Widget Container
        term_frame = ttk.Frame(inner, style="Panel.TFrame")
        term_frame._custom_bg = ABYSS
        term_frame.pack(fill="both", expand=True, padx=SP_3, pady=(0, SP_2))

        self.txt_stream = tk.Text(
            term_frame,
            bg=VOID,
            fg=TEXT_PRIMARY,
            insertbackground=CYAN,
            relief="flat",
            font=FONT_MONO_SM,
            highlightthickness=1,
            highlightbackground=PLUM,
            highlightcolor=PURPLE,
            wrap="none",
        )
        stream_scroll_y = ttk.Scrollbar(term_frame, orient="vertical", command=self.txt_stream.yview)
        stream_scroll_x = ttk.Scrollbar(term_frame, orient="horizontal", command=self.txt_stream.xview)
        self.txt_stream.configure(xscrollcommand=stream_scroll_x.set, yscrollcommand=stream_scroll_y.set)

        # Configure Syntax Color Tags
        self.txt_stream.tag_configure("sys", foreground=CYAN, font=(FONT_MONO_FALLBACK, FS_XS, "bold"))
        self.txt_stream.tag_configure("ts", foreground=TEXT_MUTED)
        self.txt_stream.tag_configure("failed", foreground=PINK, font=(FONT_MONO_FALLBACK, FS_XS, "bold"))
        self.txt_stream.tag_configure("success", foreground=CYAN, font=(FONT_MONO_FALLBACK, FS_XS, "bold"))
        self.txt_stream.tag_configure("exec", foreground=PURPLE, font=(FONT_MONO_FALLBACK, FS_XS, "bold"))
        self.txt_stream.tag_configure("usb", foreground=PEACH, font=(FONT_MONO_FALLBACK, FS_XS, "bold"))
        self.txt_stream.tag_configure("delete", foreground=MAGENTA, font=(FONT_MONO_FALLBACK, FS_XS, "bold"))
        self.txt_stream.tag_configure("normal", foreground=TEXT_SECONDARY)

        stream_scroll_y.pack(side="right", fill="y")
        stream_scroll_x.pack(side="bottom", fill="x")
        self.txt_stream.pack(side="left", fill="both", expand=True)

        self._append_system_log("Live log terminal initialized. Standby for file changes.")

    def _build_findings_panel(self) -> None:
        """Render the scrollable list of live triggered AI findings."""
        glass = create_glass_frame(
            self.right_column, width=470, height=360, border_color=PURPLE, fill_color=DEEP
        )
        glass.pack(fill="both", expand=True)
        inner = glass.inner_frame

        # Header
        hdr_row = ttk.Frame(inner, style="Card.TFrame")
        hdr_row._custom_bg = DEEP
        hdr_row.pack(fill="x", padx=SP_4, pady=(SP_2, 2))

        create_section_header(hdr_row, "LIVE TRIGGERED FINDINGS & REASONING").pack(side="left")

        self.lbl_findings_count = ttk.Label(
            hdr_row,
            text="0 FINDINGS",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_MONO_SM,
        )
        self.lbl_findings_count.pack(side="right")

        create_divider(inner, color=PLUM).pack(fill="x", padx=SP_4, pady=(2, 4))

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

        self._render_empty_findings_message()

    # -------------------------------------------------------------------------
    # UI State & Context Helpers
    # -------------------------------------------------------------------------

    def _update_case_badge(self) -> None:
        """Refresh active case context indicator."""
        for child in self.case_badge_container.winfo_children():
            child.destroy()

        case = get_case_by_id(self.case_id) if self.case_id is not None else None
        if case:
            c_text = f"CASE: {case['case_number']}"
            badge = create_badge(self.case_badge_container, c_text, CYAN, bg=DEEP)
            badge.pack(side="left")
        else:
            badge = create_badge(self.case_badge_container, "NO ACTIVE CASE", TEXT_MUTED, bg=DEEP)
            badge.pack(side="left")

    def _resolve_default_target_file(self) -> None:
        """Resolve target log file from active case evidence or fallback to sample log."""
        if self.case_id is not None:
            ev_items = get_evidence_for_case(self.case_id)
            for ev in ev_items:
                fpath = ev.get("file_path", "")
                if fpath and os.path.exists(fpath) and (ev.get("evidence_type") == "log" or fpath.endswith(".log")):
                    self.entry_target_path.delete(0, tk.END)
                    self.entry_target_path.insert(0, fpath)
                    return

        # Fallback to sample evidence log
        sample_log = os.path.join(PROJECT_ROOT, "sample_evidence", "system.log")
        self.entry_target_path.delete(0, tk.END)
        self.entry_target_path.insert(0, sample_log)

    def _browse_target_file(self) -> None:
        """Open file dialog to select target log file."""
        chosen = filedialog.askopenfilename(
            title="Select Log File to Monitor",
            initialdir=os.path.join(PROJECT_ROOT, "sample_evidence"),
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if chosen:
            self.entry_target_path.delete(0, tk.END)
            self.entry_target_path.insert(0, os.path.normpath(chosen))

    def _browse_target_folder(self) -> None:
        """Open folder dialog to select target directory to monitor."""
        chosen = filedialog.askdirectory(
            title="Select Evidence Folder to Monitor",
            initialdir=os.path.join(PROJECT_ROOT, "sample_evidence"),
        )
        if chosen:
            self.entry_target_path.delete(0, tk.END)
            self.entry_target_path.insert(0, os.path.normpath(chosen))

    def _clear_terminal(self) -> None:
        """Wipe terminal buffer."""
        self.txt_stream.delete("1.0", tk.END)
        self._append_system_log("Terminal buffer cleared.")

    def _append_system_log(self, message: str) -> None:
        """Append formatted system telemetry message."""
        now_ts = datetime.now().strftime("%H:%M:%S")
        self.txt_stream.insert(tk.END, f"[{now_ts}] [SYSTEM] ", "sys")
        self.txt_stream.insert(tk.END, f"{message}\n", "normal")
        self.txt_stream.see(tk.END)

    def _render_empty_findings_message(self) -> None:
        """Render placeholder when no findings have fired."""
        for child in self.findings_content.winfo_children():
            child.destroy()

        empty_box = ttk.Frame(self.findings_content, style="Card.TFrame")
        empty_box._custom_bg = DEEP
        empty_box.pack(fill="x", padx=SP_4, pady=SP_6)

        ttk.Label(
            empty_box,
            text="NO LIVE FINDINGS TRIGGERED",
            foreground=TEXT_SECONDARY,
            background=DEEP,
            font=(FONT_FALLBACK, FS_MD, "bold"),
        ).pack(anchor="w", pady=(0, 2))

        ttk.Label(
            empty_box,
            text="Waiting for live log stream events. Forward Chaining rules will auto-evaluate as facts arrive.",
            foreground=TEXT_MUTED,
            background=DEEP,
            font=FONT_BODY,
            wraplength=380,
            justify="left",
        ).pack(anchor="w")

    # -------------------------------------------------------------------------
    # Live Monitoring Lifecycle
    # -------------------------------------------------------------------------

    def start_monitoring(self) -> None:
        """Launch background watchdog observer on specified file or directory."""
        target_path = self.entry_target_path.get().strip()
        if not target_path or not os.path.exists(target_path):
            self._append_system_log(f"Cannot start watcher: target '{target_path}' does not exist.")
            return

        if self.monitor_manager.is_monitoring():
            self.stop_monitoring()

        started = self.monitor_manager.start_monitoring(target_path)
        if started:
            self._update_badge_state(True)
            mode_desc = "folder" if os.path.isdir(target_path) else "file"
            self._append_system_log(f"Started real-time watchdog {mode_desc} monitor on: {target_path}")

            if self.shell and hasattr(self.shell, "set_live_state"):
                self.shell.set_live_state(True, target_path)
        else:
            self._append_system_log(f"Failed to initialize watchdog observer on: {target_path}")

    def stop_monitoring(self) -> None:
        """Stop background watchdog observer thread cleanly."""
        if self.monitor_manager.is_monitoring():
            self.monitor_manager.stop_monitoring()
            self._update_badge_state(False)
            self._append_system_log("Live monitoring stopped.")

            if self.shell and hasattr(self.shell, "set_live_state"):
                self.shell.set_live_state(False)

    def _update_badge_state(self, is_live: bool) -> None:
        """Update top status indicator badge."""
        for child in self.status_badge_container.winfo_children():
            child.destroy()

        if is_live:
            badge = create_badge(self.status_badge_container, "LIVE WATCHING", PINK, bg=DEEP)
            badge.pack(side="left")
        else:
            badge = create_badge(self.status_badge_container, "STANDBY", CYAN, bg=DEEP)
            badge.pack(side="left")

    # -------------------------------------------------------------------------
    # Thread-Safe Queue Polling & Dynamic Fact Updates
    # -------------------------------------------------------------------------

    def poll_queue(self) -> None:
        """
        Poll background thread-safe event_queue via root.after().
        Processes all pending log events, updates facts, and triggers AI inference.
        """
        if not self._poll_scheduled:
            return

        events_processed = 0

        while True:
            try:
                payload = self.event_queue.get_nowait()
            except queue.Empty:
                break

            events_processed += 1
            self._handle_event_payload(payload)

        # Pulse indicator effect when active
        if self.monitor_manager.is_monitoring() and events_processed > 0:
            self._pulse_toggle = not self._pulse_toggle

        # Reschedule next check
        if self.winfo_exists():
            self.after(200, self.poll_queue)

    def _handle_event_payload(self, payload: Dict[str, Any]) -> None:
        """Process incoming log append or folder event payload on the main Tkinter thread."""
        p_type = payload.get("type", "log_append")
        raw_lines: List[str] = payload.get("raw_lines", [])
        inc_facts: Dict[str, Any] = payload.get("incremental_facts", {})

        if p_type == "folder_file_created":
            fname = payload.get("filename", "")
            dtype = str(payload.get("detected_type", "")).upper()
            self._append_system_log(f"New artifact detected in monitored folder: {fname} [{dtype}]")

        # 1. Stream raw lines into terminal with syntax highlighting
        for line in raw_lines:
            self._stream_line_to_terminal(line)

        # 2. Update line count
        self.lbl_stream_count.config(
            text=f"{self.running_facts['total_lines'] + len(raw_lines)} EVENTS STREAMED"
        )

        # 3. Merge incremental facts into running total facts
        for key in (
            "failed_logins", "successful_logins", "usb_connections",
            "executable_events", "deleted_files", "suspicious_domains",
            "hidden_files", "autorun_entries", "unknown_sender_count",
            "executable_attachment_count", "urgent_subjects_count",
            "download_events",
        ):
            inc_val = int(inc_facts.get(key, 0) or 0)
            if inc_val:
                self.running_facts[key] = self.running_facts.get(key, 0) + inc_val
                self.delta_increments[key] = self.delta_increments.get(key, 0) + inc_val

        self.running_facts["unknown_sender"] = self.running_facts.get("unknown_sender_count", 0) > 0
        self.running_facts["executable_attachment"] = self.running_facts.get("executable_attachment_count", 0) > 0

        self.running_facts["total_lines"] += len(raw_lines)
        self.delta_increments["total_lines"] = (
            self.delta_increments.get("total_lines", 0) + len(raw_lines)
        )

        for ip in inc_facts.get("ip_addresses", []):
            if ip and ip not in self.running_facts["ip_addresses"]:
                self.running_facts["ip_addresses"].append(ip)

        for u in inc_facts.get("users_flagged", []):
            if u and u not in self.running_facts["users_flagged"]:
                self.running_facts["users_flagged"].append(u)

        self.running_facts["timeline_events"].extend(
            inc_facts.get("timeline_events", [])
        )

        # 4. Update Fact Delta Counters UI
        self._update_telemetry_counters(inc_facts)

        # 5. Execute Forward Chaining AI Reasoning on updated facts
        engine = ForwardChainingEngine()
        result = engine.evaluate(self.running_facts)
        self.latest_result = result

        # 6. Update Risk Gauge smoothly
        score = result.get("risk_score", 0)
        level = result.get("risk_level", "LOW")
        self.risk_gauge.set_score(score, level=level, animate=True)

        # 7. Render live findings cards
        self._render_live_findings(result.get("findings", []))

        # 7. Detect newly fired rules and dispatch toast alerts
        findings: List[Dict[str, Any]] = result.get("findings", [])
        current_codes = {f.get("rule_code", "") for f in findings}
        new_codes = current_codes - self.known_fired_rules

        if new_codes:
            self._flash_findings_panel()

        for finding in findings:
            code = finding.get("rule_code", "")
            if code not in new_codes:
                continue

            severity = int(finding.get("severity", 0))

            # Dispatch toast notification (main-thread safe)
            try:
                self.toast_manager.show_alert(finding)
            except Exception:
                pass

            # Append LIVE ALERT entry to terminal stream
            self._append_live_alert_log(
                code=code,
                name=finding.get("name", ""),
                severity=severity,
            )

            # Flash shell status bar for HIGH or MEDIUM findings
            if severity >= 15 and self.shell and hasattr(self.shell, "flash_alert"):
                alert_text = (
                    f"[ALERT] New finding: {code} - "
                    f"{finding.get('name', '')} (+{severity} PTS)"
                )
                self.shell.flash_alert(alert_text)

        # Update known rule set to prevent duplicate alerts per session
        self.known_fired_rules = current_codes

        # 8. Re-render findings cards
        self._render_live_findings(findings)

    def _append_live_alert_log(self, code: str, name: str, severity: int) -> None:
        """
        Write a highlighted [LIVE ALERT] marker line into the streaming terminal.
        This is always called on the main thread from _handle_event_payload.
        """
        from datetime import datetime as _dt
        now_ts = _dt.now().strftime("%H:%M:%S")
        alert_line = (
            f"[{now_ts}] [LIVE ALERT] Rule {code} fired: "
            f"{name} (+{severity} PTS)"
        )
        # Ensure the "alert" tag is configured (idempotent)
        self.txt_stream.tag_configure(
            "alert",
            foreground=PINK,
            font=(FONT_MONO_FALLBACK, FS_XS, "bold"),
        )
        self.txt_stream.insert(tk.END, f"{alert_line}\n", "alert")
        self.txt_stream.see(tk.END)

    def _flash_findings_panel(self) -> None:
        """
        Briefly flash the findings panel border to PINK to signal a new alert,
        then restore it to PURPLE after 350 ms.
        """
        try:
            canvas = self.right_column.winfo_children()[0]
            if hasattr(canvas, "configure"):
                canvas.configure(highlightbackground=PINK)
                self.after(
                    350, lambda: canvas.configure(highlightbackground=STEEL)
                    if canvas.winfo_exists() else None
                )
        except Exception:
            pass

    def _stream_line_to_terminal(self, line: str) -> None:
        """Parse and colorize incoming line in the monospace text widget."""
        line_clean = line.strip()
        lower_line = line_clean.lower()

        # Classify color tag
        if "failed" in lower_line or "invalid" in lower_line or "denied" in lower_line:
            tag = "failed"
        elif "accepted" in lower_line or "successful" in lower_line or "session opened" in lower_line:
            tag = "success"
        elif "powershell" in lower_line or "cmd.exe" in lower_line or "process" in lower_line or "exec" in lower_line:
            tag = "exec"
        elif "usb" in lower_line or "mass storage" in lower_line or "vendor=" in lower_line:
            tag = "usb"
        elif "deleted" in lower_line or "removed" in lower_line or "unlink" in lower_line or "rm " in lower_line:
            tag = "delete"
        else:
            tag = "normal"

        self.txt_stream.insert(tk.END, f"{line_clean}\n", tag)
        self.txt_stream.see(tk.END)

    def _update_telemetry_counters(self, inc_facts: Dict[str, Any]) -> None:
        """Update counter numbers and highlight recent increments."""
        for key in ("failed_logins", "executable_events", "deleted_files", "usb_connections", "total_lines"):
            val = self.running_facts.get(key, 0)
            inc = self.delta_increments.get(key, 0)

            if key in self.stat_val_labels:
                self.stat_val_labels[key].config(text=str(val))

            if key in self.stat_inc_labels:
                inc_text = f"(+{inc})" if inc > 0 else "(+0)"
                inc_fg = PINK if inc > 0 else TEXT_MUTED
                self.stat_inc_labels[key].config(text=inc_text, foreground=inc_fg)

    def _render_live_findings(self, findings: List[Dict[str, Any]]) -> None:
        """Render live findings cards triggered by Forward Chaining."""
        for child in self.findings_content.winfo_children():
            child.destroy()

        self.lbl_findings_count.config(text=f"{len(findings)} FINDINGS")

        if not findings:
            self._render_empty_findings_message()
            return

        for f in findings:
            code = f.get("rule_code", "R000")
            name = f.get("name", "Unknown Finding")
            desc = f.get("description", "")
            severity = int(f.get("severity", 0))
            expl = f.get("explanation", "")

            if severity >= 25:
                accent = PINK
            elif severity >= 15:
                accent = PEACH
            else:
                accent = CYAN

            card = tk.Frame(
                self.findings_content,
                bg=ABYSS,
                highlightthickness=1,
                highlightbackground=STEEL,
                padx=8,
                pady=6,
            )
            card.pack(fill="x", padx=SP_2, pady=2)

            top_row = tk.Frame(card, bg=ABYSS)
            top_row.pack(fill="x")

            create_badge(top_row, code, PURPLE, bg=ABYSS).pack(side="left", padx=(0, 6))
            ttk.Label(top_row, text=name, foreground=TEXT_PRIMARY, background=ABYSS, font=(FONT_FALLBACK, FS_SM, "bold")).pack(side="left")
            create_badge(top_row, f"+{severity} PTS", accent, bg=ABYSS).pack(side="right")

            ttk.Label(card, text=desc, foreground=TEXT_SECONDARY, background=ABYSS, font=FONT_SMALL, wraplength=420, justify="left").pack(fill="x", pady=(2, 4))

            p_box = tk.Frame(card, bg=DEEP, padx=6, pady=3)
            p_box.pack(fill="x")
            ttk.Label(p_box, text="PROOF (FACT DELTA):", foreground=TEXT_MUTED, background=DEEP, font=(FONT_FALLBACK, FS_XS, "bold")).pack(anchor="w")
            ttk.Label(p_box, text=expl, foreground=ICE, background=DEEP, font=FONT_MONO_SM, wraplength=410, justify="left").pack(anchor="w")

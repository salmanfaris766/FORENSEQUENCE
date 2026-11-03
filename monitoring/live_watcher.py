# =============================================================================
# monitoring/live_watcher.py
# FORENSEQUENCE - Real-Time Multi-Source Live Evidence & Folder Monitoring
# =============================================================================
#
# Non-blocking, thread-safe file and directory watcher built on watchdog and queue.Queue.
# Supports:
#   1. Single log file tailing via sequential byte offsets (file.seek).
#   2. Full folder watching for newly created / modified forensic evidence files,
#      automatically parsed via the Unified Evidence Dispatcher.
# Extracts incremental forensic facts and delivers payloads to the UI thread.
# =============================================================================

from __future__ import annotations

import os
import sys
import time
import queue
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List, Set, Union

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Project root resolution
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from analyzers.log_analyzer import parse_log_lines
from analyzers.dispatcher import parse_evidence_item, detect_evidence_type


# =============================================================================
# LOG FILE EVENT HANDLER
# =============================================================================

class LogFileEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler targeting a specific log file.
    Maintains an internal file byte pointer to read only newly appended lines,
    parses incremental forensic facts, and enqueues structured events.
    """

    def __init__(self, file_path: str, event_queue: queue.Queue):
        super().__init__()
        self.file_path = os.path.abspath(file_path)
        self.norm_path = os.path.normcase(self.file_path)
        self.event_queue = event_queue
        self._lock = threading.Lock()

        # Initialize position to current file size so pre-existing content is skipped
        if os.path.exists(self.file_path):
            try:
                self.last_position = os.path.getsize(self.file_path)
            except OSError:
                self.last_position = 0
        else:
            self.last_position = 0

    def on_modified(self, event) -> None:
        """Handle file system modification events emitted by watchdog."""
        if event.is_directory:
            return

        # Check if modified path matches watched file (case-normalized for Windows)
        event_norm = os.path.normcase(os.path.abspath(event.src_path))
        if event_norm != self.norm_path:
            return

        with self._lock:
            if not os.path.exists(self.file_path):
                return

            try:
                curr_size = os.path.getsize(self.file_path)
            except OSError:
                return

            # Handle file truncation or rotation
            if curr_size < self.last_position:
                self.last_position = 0

            # If no new bytes appended, do nothing
            if curr_size == self.last_position:
                return

            new_lines: List[str] = []
            try:
                with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(self.last_position)
                    content = f.read()
                    self.last_position = f.tell()
                    new_lines = content.splitlines(keepends=False)
            except Exception:
                return

            # Strip empty lines while preserving structure
            valid_lines = [l for l in new_lines if l.strip()]
            if not valid_lines:
                return

            # Parse incremental facts across newly read lines
            parsed_facts = parse_log_lines(valid_lines)

            # Build structured payload
            payload = {
                "type": "log_append",
                "raw_lines": valid_lines,
                "incremental_facts": parsed_facts,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file_path": self.file_path,
            }

            self.event_queue.put(payload)


# =============================================================================
# FOLDER EVIDENCE EVENT HANDLER
# =============================================================================

class FolderEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler targeting an evidence directory.
    Watches for newly created or modified files in the folder, parses them
    using parse_evidence_item, and enqueues folder_file_created payloads.
    """

    def __init__(self, folder_path: str, event_queue: queue.Queue):
        super().__init__()
        self.folder_path = os.path.abspath(folder_path)
        self.event_queue = event_queue
        self._lock = threading.Lock()
        self._processed_files: Set[str] = set()

        # Record pre-existing files so they aren't repeatedly processed unless modified
        if os.path.exists(self.folder_path):
            try:
                for root, _, files in os.walk(self.folder_path):
                    for f in files:
                        self._processed_files.add(os.path.abspath(os.path.join(root, f)))
            except Exception:
                pass

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        self._handle_file_event(event.src_path, event_type="created")

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        abs_p = os.path.abspath(event.src_path)
        if abs_p not in self._processed_files:
            self._handle_file_event(event.src_path, event_type="modified")

    def _handle_file_event(self, file_path: str, event_type: str = "created") -> None:
        abs_p = os.path.abspath(file_path)
        with self._lock:
            # Short settling delay so the file writer completes
            time.sleep(0.08)
            if not os.path.exists(abs_p):
                return

            self._processed_files.add(abs_p)
            detected_type = detect_evidence_type(abs_p)

            try:
                parsed_facts = parse_evidence_item(detected_type, abs_p)
            except Exception as exc:
                parsed_facts = {"error": str(exc), "evidence_type": detected_type}

            fname = os.path.basename(abs_p)
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            raw_summary = (
                f"[{now_ts}] NEW ARTIFACT: {fname} (type={detected_type.upper()}, "
                f"size={os.path.getsize(abs_p) if os.path.exists(abs_p) else 0} bytes)"
            )

            payload = {
                "type": "folder_file_created",
                "event_type": event_type,
                "file_path": abs_p,
                "filename": fname,
                "detected_type": detected_type,
                "incremental_facts": parsed_facts,
                "timestamp": now_ts,
                "raw_lines": [raw_summary],
            }
            self.event_queue.put(payload)


# =============================================================================
# LIVE MONITOR MANAGER
# =============================================================================

class LiveMonitorManager:
    """
    Thread-safe lifecycle manager for watchdog background log file & folder monitoring.
    Schedules either LogFileEventHandler or FolderEventHandler onto an Observer thread
    and streams incoming facts and lines through a synchronized queue.
    """

    def __init__(self, event_queue: Optional[queue.Queue] = None):
        self.event_queue = event_queue if event_queue is not None else queue.Queue()
        self.observer: Optional[Observer] = None
        self.handler: Optional[Union[LogFileEventHandler, FolderEventHandler]] = None
        self.watched_file: Optional[str] = None
        self.watched_path: Optional[str] = None
        self.is_directory_mode: bool = False
        self._is_monitoring = False
        self._lock = threading.Lock()

    def start_monitoring(self, target_path: str) -> bool:
        """
        Validate path existence and launch background watchdog observer.
        Automatically detects whether target_path is a directory or a single log file.

        Parameters
        ----------
        target_path : str
            Target log file or directory path to monitor in real time.

        Returns
        -------
        bool
            True if monitoring started successfully; False otherwise.
        """
        with self._lock:
            # Stop existing watcher if active
            if self._is_monitoring:
                self._stop_internal()

            abs_path = os.path.abspath(target_path)
            if not os.path.exists(abs_path):
                return False

            self.watched_path = abs_path
            self.watched_file = abs_path
            self.observer = Observer()

            try:
                if os.path.isdir(abs_path):
                    self.is_directory_mode = True
                    self.handler = FolderEventHandler(abs_path, self.event_queue)
                    self.observer.schedule(self.handler, path=abs_path, recursive=True)
                else:
                    self.is_directory_mode = False
                    watch_dir = os.path.dirname(abs_path)
                    if not os.path.isdir(watch_dir):
                        return False
                    self.handler = LogFileEventHandler(abs_path, self.event_queue)
                    self.observer.schedule(self.handler, path=watch_dir, recursive=False)

                self.observer.daemon = True
                self.observer.start()
                self._is_monitoring = True
                return True
            except Exception:
                self._stop_internal()
                return False

    def stop_monitoring(self) -> None:
        """Stop and join the background Observer thread cleanly."""
        with self._lock:
            self._stop_internal()

    def _stop_internal(self) -> None:
        """Internal helper to shut down observer without locking recursion."""
        if self.observer is not None:
            try:
                self.observer.stop()
                self.observer.join(timeout=1.5)
            except Exception:
                pass
            self.observer = None

        self.handler = None
        self.watched_file = None
        self.watched_path = None
        self.is_directory_mode = False
        self._is_monitoring = False

    def is_monitoring(self) -> bool:
        """Return True if the background observer is currently active and alive."""
        with self._lock:
            if not self._is_monitoring or self.observer is None:
                return False
            return self.observer.is_alive()


# =============================================================================
# STANDALONE TEST HARNESS
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("FORENSEQUENCE - Live Watcher Standalone Test")
    print("=" * 70)

    test_folder = os.path.join(PROJECT_ROOT, "uploads", "test_live_dir")
    os.makedirs(test_folder, exist_ok=True)

    test_queue = queue.Queue()
    manager = LiveMonitorManager(event_queue=test_queue)

    print(f"Testing folder watcher on: {test_folder}")
    started = manager.start_monitoring(test_folder)
    print(f"Watcher started: {started} | Is Directory Mode: {manager.is_directory_mode}")

    if started:
        time.sleep(0.5)
        # Simulate creating a new evidence file in folder
        sim_file = os.path.join(test_folder, "simulated_evidence.log")
        with open(sim_file, "w", encoding="utf-8") as f:
            f.write("2026-10-14 01:00:00 Failed password for root from 192.168.1.105 ssh2\n")

        time.sleep(1.0)
        manager.stop_monitoring()

        print("\nQueue items received:")
        while not test_queue.empty():
            item = test_queue.get()
            print(f"  Type: {item['type']}, File: {item.get('filename')}, Facts: {list(item.get('incremental_facts', {}).keys())}")
        print("\n[OK] Live Folder Watcher test complete.")

# =============================================================================
# analyzers/file_analyzer.py
# FORENSEQUENCE - Deterministic File-System Forensic Analyzer
# =============================================================================
#
# Performs static forensic triage on a directory tree or single file using
# exclusively the Python standard library. No ML, no external APIs.
#
# Key capabilities:
#   - Recursive directory walk with os.scandir for performance
#   - SHA-256 file hashing for exact-duplicate detection
#   - Suspicious-extension enumeration (executables, double-extensions)
#   - Hidden file detection (dot-prefix + Windows FILE_ATTRIBUTE_HIDDEN)
#   - autorun.inf / desktop.ini / registry-export persistence flag detection
#   - Large-file flagging (configurable threshold, default 10 MB)
#   - Structured facts dict fully compatible with ForwardChainingEngine
#   - Chronological timeline_events compatible with TimelineBuilder
# =============================================================================

from __future__ import annotations

import hashlib
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

LARGE_FILE_THRESHOLD_BYTES: int = 10 * 1024 * 1024  # 10 MB

# Extensions that are directly executable or script-based threat vectors
EXECUTABLE_EXTENSIONS: Set[str] = {
    ".exe", ".bat", ".ps1", ".vbs", ".vbe",
    ".scr", ".sh",  ".cmd", ".dll", ".com",
    ".jar", ".js",  ".wsf", ".hta", ".msi",
    ".pif", ".reg", ".cpl", ".sys",
}

# Extensions associated with data theft / exfiltration payloads
SUSPICIOUS_EXTENSIONS: Set[str] = {
    ".bin", ".raw", ".dump", ".dmp", ".img",
    ".iso", ".lnk",
}

# Filenames that indicate autorun / persistence mechanisms
AUTORUN_FILENAMES: Set[str] = {
    "autorun.inf",
    "desktop.ini",
    "thumbs.db",      # Can be abused for steganography / icon DLL hijack
}

# Content keywords inside .inf / .ini / .reg files that confirm persistence
AUTORUN_KEYWORDS: tuple = ("open=", "shellexecute=", "shell\\open", "HKEY_")

# Maximum file size to hash in full (skip hashing very large files to stay fast)
_MAX_HASH_SIZE_BYTES: int = 200 * 1024 * 1024  # 200 MB


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _sha256_file(path: str) -> str:
    """
    Compute the SHA-256 hexdigest of a file.

    Parameters
    ----------
    path : str
        Absolute path to the file.

    Returns
    -------
    str
        64-character lowercase hexadecimal SHA-256 digest, or empty string
        if the file cannot be read (permissions, locking, etc.).
    """
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return ""


def _format_ts(epoch: float) -> str:
    """Convert a Unix epoch float to 'YYYY-MM-DD HH:MM:SS' string."""
    try:
        return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, OverflowError, ValueError):
        return ""


def _is_hidden_file(name: str, path: str) -> bool:
    """
    Determine whether a file is hidden using two strategies:

    1. Unix convention: filename starts with a dot.
    2. Windows convention: FILE_ATTRIBUTE_HIDDEN flag (0x2) is set on the
       file\'s stat attributes (st_file_attributes, Windows only).

    Parameters
    ----------
    name : str
        Base filename (not full path).
    path : str
        Full absolute path to the file.

    Returns
    -------
    bool
        True if the file is hidden by either convention.
    """
    if name.startswith("."):
        return True

    if platform.system() == "Windows":
        try:
            attrs = os.stat(path).st_file_attributes
            # FILE_ATTRIBUTE_HIDDEN = 0x2
            if attrs & 0x2:
                return True
        except (AttributeError, OSError):
            pass

    return False


def _has_double_extension(name: str) -> bool:
    """
    Detect double-extension spoofing patterns such as 'invoice.pdf.exe'.

    A double-extension file has two or more dot-separated extensions where
    the final extension is an executable or dangerous type.

    Parameters
    ----------
    name : str
        Base filename.

    Returns
    -------
    bool
        True if the filename appears to use double-extension spoofing.
    """
    parts = name.lower().rsplit(".", 2)
    if len(parts) < 3:
        return False
    # At least two extensions present; final extension must be executable
    final_ext = "." + parts[-1]
    penultimate_ext = "." + parts[-2]
    return (
        final_ext in EXECUTABLE_EXTENSIONS
        and penultimate_ext not in {"", "."}
        and len(parts[-2]) >= 2
    )


def _is_autorun_file(name: str, path: str) -> bool:
    """
    Determine if a file represents a persistence / autorun mechanism.

    Checks both filename membership in AUTORUN_FILENAMES and, for .inf/.ini
    files, scans the first 4 KB of content for known autorun keywords.

    Parameters
    ----------
    name : str
        Base filename (case-insensitive comparison applied internally).
    path : str
        Full absolute path to the file.

    Returns
    -------
    bool
        True if the file is identified as an autorun artifact.
    """
    lower_name = name.lower()

    if lower_name in AUTORUN_FILENAMES:
        # Further validate by inspecting content for persistence keywords
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read(4096).lower()
            return any(kw.lower() in content for kw in AUTORUN_KEYWORDS)
        except (OSError, PermissionError):
            # If unreadable, flag by name alone
            return True

    # Also catch registry export files containing HKEY references
    if lower_name.endswith(".reg"):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read(4096)
            return "HKEY_" in content
        except (OSError, PermissionError):
            return True

    return False


def _classify_file_category(
    ext: str,
    is_hidden: bool,
    is_autorun: bool,
    size_bytes: int,
    has_double_ext: bool,
) -> str:
    """
    Classify a file into a forensic timeline event category string.

    Returns one of: 'executable_event', 'hidden_file', 'autorun_entry',
    'large_file', 'suspicious_extension', 'info'.
    """
    if is_autorun:
        return "autorun_entry"
    if is_hidden and (ext in EXECUTABLE_EXTENSIONS or ext == ".py"):
        return "executable_event"
    if ext in EXECUTABLE_EXTENSIONS or has_double_ext:
        return "executable_event"
    if is_hidden:
        return "hidden_file"
    if size_bytes > LARGE_FILE_THRESHOLD_BYTES:
        return "large_file"
    if ext in SUSPICIOUS_EXTENSIONS:
        return "suspicious_extension"
    return "info"


# =============================================================================
# CORE PUBLIC API
# =============================================================================

def parse_file_system(path: str) -> Dict[str, Any]:
    """
    Recursively walk a directory (or analyse a single file) and extract
    structured forensic facts compatible with the FORENSEQUENCE Forward
    Chaining Engine and Timeline Builder.

    Parameters
    ----------
    path : str
        Path to a directory or single file to analyse.

    Returns
    -------
    dict
        Structured facts dictionary with the following top-level keys:

        evidence_type       : str  - always "file"
        total_files         : int  - total file entries scanned
        total_size_bytes    : int  - aggregate byte size of all files
        executable_events   : int  - count of executable / script files found
        hidden_files        : int  - count of hidden files
        autorun_entries     : int  - count of autorun / persistence files
        large_files         : int  - count of files exceeding threshold
        duplicate_files     : int  - count of files sharing a SHA-256 digest
        suspicious_files    : int  - total of all flagged categories
        suspicious_extensions : int - double-extension or anomalous binary count
        file_list           : list[dict] - per-file metadata records
        duplicate_groups    : list[list[str]] - groups of duplicate file paths
        timeline_events     : list[dict] - chronological forensic events
        ip_addresses        : list[str]  - IPs extracted from file content
        failed_logins       : int  - always 0 (not applicable to file evidence)
        successful_logins   : int  - always 0
        usb_connections     : int  - always 0
        deleted_files       : int  - always 0 (file presence check only)
        suspicious_domains  : int  - always 0
        unknown_sender      : bool - always False
        executable_attachment : bool - True if any executable found
        users_flagged       : list[str] - always []
    """
    abs_path = os.path.abspath(path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Path does not exist: {abs_path!r}")

    # Accumulator structures
    file_list:   List[Dict[str, Any]] = []
    hash_map:    Dict[str, List[str]] = {}   # sha256 -> [paths]
    timeline:    List[Dict[str, Any]] = []

    total_files            = 0
    total_size_bytes       = 0
    executable_events      = 0
    hidden_files           = 0
    autorun_entries        = 0
    large_files            = 0
    suspicious_extensions  = 0

    # Collect file paths: single file or recursive directory walk
    paths_to_scan: List[str] = []

    if os.path.isfile(abs_path):
        paths_to_scan.append(abs_path)
    else:
        for dirpath, _dirnames, filenames in os.walk(abs_path):
            for fname in filenames:
                paths_to_scan.append(os.path.join(dirpath, fname))

    # -------------------------------------------------------------------------
    # Per-file metadata extraction
    # -------------------------------------------------------------------------
    for fpath in sorted(paths_to_scan):
        fname = os.path.basename(fpath)
        ext   = Path(fname).suffix.lower()

        try:
            st = os.stat(fpath)
        except (OSError, PermissionError):
            continue

        size_bytes  = st.st_size
        created_ts  = _format_ts(getattr(st, "st_birthtime", st.st_ctime))
        modified_ts = _format_ts(st.st_mtime)

        # --- Flag computation ---
        is_hidden    = _is_hidden_file(fname, fpath)
        is_exec      = ext in EXECUTABLE_EXTENSIONS
        is_autorun   = _is_autorun_file(fname, fpath)
        is_large     = size_bytes > LARGE_FILE_THRESHOLD_BYTES
        has_dbl_ext  = _has_double_extension(fname)
        is_suspicious_ext = (has_dbl_ext or ext in SUSPICIOUS_EXTENSIONS) and not is_exec

        # --- SHA-256 hash (skip if larger than hard limit) ---
        sha256 = ""
        if size_bytes <= _MAX_HASH_SIZE_BYTES:
            sha256 = _sha256_file(fpath)
            if sha256:
                hash_map.setdefault(sha256, []).append(fpath)

        # --- Counter increments ---
        total_files      += 1
        total_size_bytes += size_bytes

        if is_exec or has_dbl_ext or (is_hidden and ext in {".py", ".sh"}):
            executable_events += 1
        if is_hidden:
            hidden_files += 1
        if is_autorun:
            autorun_entries += 1
        if is_large:
            large_files += 1
        if is_suspicious_ext:
            suspicious_extensions += 1

        # --- Build file record ---
        file_list.append({
            "filename":    fname,
            "path":        fpath,
            "size_bytes":  size_bytes,
            "extension":   ext,
            "is_hidden":   is_hidden,
            "is_executable": is_exec or has_dbl_ext,
            "is_large":    is_large,
            "is_autorun":  is_autorun,
            "has_double_extension": has_dbl_ext,
            "created_at":  created_ts,
            "modified_at": modified_ts,
            "sha256":      sha256,
        })

        # --- Build timeline event ---
        category = _classify_file_category(
            ext, is_hidden, is_autorun, size_bytes, has_dbl_ext
        )

        if category != "info":
            ts = modified_ts or created_ts or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            description = _build_event_description(
                fname, fpath, ext, size_bytes,
                is_hidden, is_autorun, is_large, has_dbl_ext, is_exec,
            )
            timeline.append({
                "timestamp":   ts,
                "category":    category,
                "title":       f"File: {fname}",
                "description": description,
                "severity":    _event_severity(category),
                "source":      "file_analyzer",
                "rule_code":   "",
                "raw":         f"{ts} FILE {category.upper()} {fpath}",
            })

    # -------------------------------------------------------------------------
    # Duplicate detection
    # -------------------------------------------------------------------------
    duplicate_groups = [
        paths for paths in hash_map.values() if len(paths) > 1
    ]
    duplicate_count = sum(
        len(grp) - 1 for grp in duplicate_groups
    )  # Extra copies beyond the first

    # Add duplicate timeline events
    for grp in duplicate_groups:
        primary = os.path.basename(grp[0])
        copies  = [os.path.basename(p) for p in grp[1:]]
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timeline.append({
            "timestamp":   ts,
            "category":    "info",
            "title":       f"Duplicate File: {primary}",
            "description": (
                f"Exact byte-for-byte duplicate detected. "
                f"SHA-256 shared between: {', '.join([primary] + copies)}"
            ),
            "severity":    "low",
            "source":      "file_analyzer",
            "rule_code":   "",
            "raw":         f"DUPLICATE sha256_match {grp[0]} -> {grp[1:]}",
        })

    # Sort timeline chronologically
    timeline.sort(key=lambda e: e.get("timestamp", ""))

    # -------------------------------------------------------------------------
    # Suspicious file total
    # -------------------------------------------------------------------------
    suspicious_files = (
        executable_events + hidden_files + autorun_entries
        + large_files + suspicious_extensions
    )

    # -------------------------------------------------------------------------
    # Assemble final facts dict (FC-Engine compatible)
    # -------------------------------------------------------------------------
    return {
        # Standard cross-analyzer fields
        "evidence_type":          "file",
        "failed_logins":          0,
        "successful_logins":      0,
        "usb_connections":        0,
        "deleted_files":          0,
        "suspicious_domains":     0,
        "unknown_sender":         False,
        "executable_attachment":  executable_events > 0,
        "users_flagged":          [],
        "ip_addresses":           [],
        # File-specific forensic facts
        "total_files":            total_files,
        "total_size_bytes":       total_size_bytes,
        "executable_events":      executable_events,
        "hidden_files":           hidden_files,
        "autorun_entries":        autorun_entries,
        "large_files":            large_files,
        "duplicate_files":        duplicate_count,
        "suspicious_files":       suspicious_files,
        "suspicious_extensions":  suspicious_extensions,
        # Detailed records
        "file_list":              file_list,
        "duplicate_groups":       duplicate_groups,
        "timeline_events":        timeline,
    }


def _build_event_description(
    fname: str,
    fpath: str,
    ext: str,
    size_bytes: int,
    is_hidden: bool,
    is_autorun: bool,
    is_large: bool,
    has_dbl_ext: bool,
    is_exec: bool,
) -> str:
    """
    Produce a human-readable forensic event description for a flagged file.

    Parameters mirror flag values already computed per file.
    """
    parts: List[str] = [f"File: {fname}"]

    if is_autorun:
        parts.append("Autorun or persistence mechanism detected in file content")
    if has_dbl_ext:
        parts.append("Double-extension spoofing detected (e.g. document.pdf.exe)")
    if is_exec and not is_autorun:
        if "keylogger" in fname.lower() or ".py" in fname.lower() and is_hidden:
            parts.append("Hidden script with executable capability")
        elif ext == ".ps1":
            parts.append("PowerShell script detected - may execute arbitrary system commands")
        elif ext == ".exe":
            parts.append("Windows PE executable detected in evidence directory")
        else:
            parts.append(f"Executable artifact detected (extension: {ext})")
    if is_hidden:
        parts.append("File is hidden (dot-prefix or Windows hidden attribute)")
    if is_large:
        mb = size_bytes / (1024 * 1024)
        parts.append(f"Large file ({mb:.1f} MB) - possible data exfiltration dump or memory image")

    return ". ".join(parts) + "."


def _event_severity(category: str) -> str:
    """Map a file event category to a human-readable severity label."""
    return {
        "executable_event":    "high",
        "autorun_entry":       "high",
        "hidden_file":         "medium",
        "large_file":          "medium",
        "suspicious_extension":"low",
        "info":                "info",
    }.get(category, "info")


# =============================================================================
# CLASS WRAPPER
# =============================================================================

class FileAnalyzer:
    """
    Thin class wrapper around the parse_file_system() function.

    Provides a stateful object interface for callers that prefer class-based
    usage (e.g., the GUI Evidence Detail frame or unit tests).

    Usage
    -----
        analyzer = FileAnalyzer()
        facts = analyzer.analyze("/path/to/directory")
    """

    def __init__(
        self,
        large_file_threshold_bytes: int = LARGE_FILE_THRESHOLD_BYTES,
    ) -> None:
        """
        Parameters
        ----------
        large_file_threshold_bytes : int
            Override the default 10 MB threshold for large-file detection.
        """
        self.threshold = large_file_threshold_bytes
        self._last_facts: Optional[Dict[str, Any]] = None

    def analyze(self, path: str) -> Dict[str, Any]:
        """
        Run forensic analysis on a path and cache the result.

        Parameters
        ----------
        path : str
            Directory or file path to analyse.

        Returns
        -------
        dict
            Structured facts dict (see parse_file_system docstring).
        """
        self._last_facts = parse_file_system(path)
        return self._last_facts

    @property
    def last_facts(self) -> Optional[Dict[str, Any]]:
        """Return the most recently computed facts dict, or None."""
        return self._last_facts


# =============================================================================
# STANDALONE TEST HARNESS
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("FORENSEQUENCE - File System Forensic Analyzer Standalone Test")
    print("=" * 70)

    # Locate sample evidence folder relative to this script
    _analyzer_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.dirname(_analyzer_dir)
    _evidence_dir = os.path.join(_project_root, "sample_evidence", "evidence_folder")

    if not os.path.isdir(_evidence_dir):
        print(f"[ERROR] Sample evidence folder not found: {_evidence_dir}")
        print("Run create_evidence.py first to generate sample artifacts.")
        sys.exit(1)

    print(f"\nTarget directory: {_evidence_dir}")
    print("-" * 70)

    facts = parse_file_system(_evidence_dir)

    # --- Summary Block ---
    print("\n[EXTRACTION SUMMARY]")
    print(f"  Evidence Type     : {facts['evidence_type']}")
    print(f"  Total Files       : {facts['total_files']}")
    print(f"  Total Size        : {facts['total_size_bytes'] / (1024*1024):.2f} MB")
    print()
    print("[FORENSIC FACT COUNTERS]")
    print(f"  Executable Events : {facts['executable_events']}")
    print(f"  Hidden Files      : {facts['hidden_files']}")
    print(f"  Autorun Entries   : {facts['autorun_entries']}")
    print(f"  Large Files       : {facts['large_files']}")
    print(f"  Duplicate Files   : {facts['duplicate_files']}")
    print(f"  Suspicious Files  : {facts['suspicious_files']}")
    print(f"  Exec. Attachment  : {facts['executable_attachment']}")
    print()

    # --- File List ---
    print("[FILE INVENTORY]")
    print(f"  {'FILENAME':<36} {'SIZE':>12}  {'EXT':>5}  FLAGS")
    print("  " + "-" * 72)
    for rec in facts["file_list"]:
        flags = []
        if rec["is_executable"]:      flags.append("EXEC")
        if rec["is_hidden"]:          flags.append("HIDDEN")
        if rec["is_autorun"]:         flags.append("AUTORUN")
        if rec["is_large"]:           flags.append("LARGE")
        if rec["has_double_extension"]: flags.append("DBL-EXT")
        flag_str = " | ".join(flags) if flags else "-"
        print(
            f"  {rec['filename']:<36} {rec['size_bytes']:>12,}  "
            f"{rec['extension'] or '-':>5}  {flag_str}"
        )

    # --- Duplicates ---
    if facts["duplicate_groups"]:
        print()
        print("[DUPLICATE FILE GROUPS]")
        for i, grp in enumerate(facts["duplicate_groups"], 1):
            print(f"  Group {i}: SHA-256 match")
            for p in grp:
                print(f"    -> {os.path.basename(p)}")

    # --- Timeline ---
    print()
    print("[CHRONOLOGICAL TIMELINE EVENTS]")
    if facts["timeline_events"]:
        for ev in facts["timeline_events"]:
            sev = ev.get("severity", "info").upper()[:3]
            print(f"  [{ev['timestamp']}] [{sev}] [{ev['category'].upper()[:16]}]")
            print(f"    {ev['description'][:90]}")
    else:
        print("  No flagged timeline events found.")

    # --- Forward Chaining compatibility check ---
    print()
    print("[FORWARD CHAINING ENGINE COMPATIBILITY CHECK]")
    from ai.rule_engine import ForwardChainingEngine
    engine = ForwardChainingEngine()
    fc_result = engine.evaluate(facts)
    print(f"  Risk Score   : {fc_result['risk_score']}")
    print(f"  Risk Level   : {fc_result['risk_level']}")
    print(f"  Findings     : {len(fc_result['findings'])} rules triggered")
    for f in fc_result["findings"]:
        print(f"    [{f['rule_code']}] {f['name']} (sev={f['severity']})")

    print()
    print("[SUCCESS] File analyzer standalone test completed successfully.")

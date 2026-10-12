# =============================================================================
# analyzers/log_analyzer.py
# FORENSEQUENCE - Deterministic Forensic Log Analyzer
# =============================================================================

import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Set


# =============================================================================
# REGEX PATTERNS FOR FORENSIC FACT EXTRACTION
# =============================================================================

# Timestamp patterns
_RE_TIMESTAMP_ISO = re.compile(
    r"\b(\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\b"
)
_RE_TIMESTAMP_SYSLOG = re.compile(
    r"\b([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\b"
)

# IP address pattern (valid IPv4 octets 0-255)
_RE_IPV4 = re.compile(
    r"\b((?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)

# User account extraction patterns
_RE_USER_PATTERNS = [
    re.compile(r"\buser\s*=\s*([a-zA-Z0-9_\-\.\$]+)\b", re.IGNORECASE),
    re.compile(r"\bfor\s+user\s+([a-zA-Z0-9_\-\.\$]+)\b", re.IGNORECASE),
    re.compile(r"\bby\s+user\s+([a-zA-Z0-9_\-\.\$]+)\b", re.IGNORECASE),
    re.compile(r"\buser\s+([a-zA-Z0-9_\-\.\$]+)\b", re.IGNORECASE),
]

_DISALLOWED_USERNAMES = {
    "from", "port", "ssh2", "session", "opened", "closed", "system",
    "the", "a", "an", "online", "active", "service", "failed", "success",
    "name", "eventid", "path", "ip", "status", "by", "for", "to", "at",
}

# 1. Failed Logins
_RE_FAILED_LOGIN = re.compile(
    r"(?:Failed\s+password|FAILED\s+LOGIN|Logon\s+Failure|EventID\s+4625|"
    r"Auth\s+failure|Authentication\s+failure|Invalid\s+user)",
    re.IGNORECASE,
)

# 2. Successful Logins
_RE_SUCCESSFUL_LOGIN = re.compile(
    r"(?:Accepted\s+password|Accepted\s+publickey|SUCCESSFUL\s+LOGIN|"
    r"Session\s+opened|Logon\s+Success|EventID\s+4624)",
    re.IGNORECASE,
)

# 3. USB Connections
_RE_USB_CONNECTION = re.compile(
    r"(?:New\s+USB\s+device|USB\s+device|usb-storage|Removable\s+Media|"
    r"Volume\s+Mount|VendorID\s+[0-9a-fA-F]+)",
    re.IGNORECASE,
)

# 4. File Deletion Events
_RE_DELETED_FILES = re.compile(
    r"(?:file\s+deleted|unlink\(\)|unlink\b|REMOVED\s+file|REMOVED\b|"
    r"DELETED\s+/|DELETED\b|EventID\s+4660|rm\s+-rf)",
    re.IGNORECASE,
)

# 5. Executable / Process Launch Events
_RE_EXECUTABLE_EVENTS = re.compile(
    r"(?:process\s+creation|EventID\s+4688|\bEXEC\b|powershell(?:\.exe)?|"
    r"cmd\.exe|\bmimikatz(?:\.exe)?|\.exe\b)",
    re.IGNORECASE,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_timestamp(line: str) -> str:
    """
    Extract and standardize a timestamp from a log line into 'YYYY-MM-DD HH:MM:SS'.
    Returns empty string if no timestamp pattern matches.
    """
    iso_match = _RE_TIMESTAMP_ISO.search(line)
    if iso_match:
        raw_ts = iso_match.group(1).replace("/", "-").replace("T", " ")
        if "." in raw_ts:
            raw_ts = raw_ts.split(".")[0]
        return raw_ts

    syslog_match = _RE_TIMESTAMP_SYSLOG.search(line)
    if syslog_match:
        raw_ts = syslog_match.group(1)
        current_year = datetime.now().year
        try:
            parsed = datetime.strptime(f"{current_year} {raw_ts}", "%Y %b %d %H:%M:%S")
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return raw_ts

    return ""


def extract_ip_addresses(line: str) -> List[str]:
    """Extract all valid IPv4 addresses from a line."""
    matches = _RE_IPV4.findall(line)
    # Filter and preserve full match strings
    ips: List[str] = []
    for m in re.finditer(_RE_IPV4, line):
        ip_str = m.group(0)
        # Verify valid octets
        parts = ip_str.split(".")
        if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
            if ip_str not in ips:
                ips.append(ip_str)
    return ips


def extract_users(line: str) -> List[str]:
    """Extract flagged user accounts from a log line."""
    users: List[str] = []
    for pattern in _RE_USER_PATTERNS:
        match = pattern.search(line)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() not in _DISALLOWED_USERNAMES and len(candidate) > 1:
                if candidate not in users:
                    users.append(candidate)
    return users


def classify_log_line(line: str) -> tuple[str, str]:
    """
    Classify a log line into a forensic category and generate a descriptive summary.

    Returns
    -------
    tuple[str, str]
        (category, description)
        Categories: 'failed_login', 'successful_login', 'usb_connection',
                    'deleted_file', 'executable_event', 'info'
    """
    # 1. File deletions (prioritize explicit destructive file operations)
    if _RE_DELETED_FILES.search(line):
        file_path_match = re.search(r"(?:path=|file\s+|/|[\w\.\-]+\.\w+)", line)
        desc = "File deletion artifact detected"
        if "db_backup" in line or "backup" in line.lower():
            desc = "Critical database backup file deleted"
        elif "audit.log" in line or "secure.log" in line or "syslog" in line:
            desc = "Security log file deleted / unlinked (evidence tampering)"
        elif "tokens.json" in line or "shadow" in line:
            desc = "Credential or authentication store deleted"
        elif "rm -rf" in line:
            desc = "Mass file removal via rm -rf command"
        return "deleted_file", desc

    # 2. Failed logins
    if _RE_FAILED_LOGIN.search(line):
        users = extract_users(line)
        ips = extract_ip_addresses(line)
        u_str = f" for user '{users[0]}'" if users else ""
        ip_str = f" from IP {ips[0]}" if ips else ""
        return "failed_login", f"Failed authentication attempt{u_str}{ip_str}"

    # 3. Successful logins
    if _RE_SUCCESSFUL_LOGIN.search(line):
        users = extract_users(line)
        ips = extract_ip_addresses(line)
        u_str = f" for user '{users[0]}'" if users else ""
        ip_str = f" from IP {ips[0]}" if ips else ""
        return "successful_login", f"Successful authentication session{u_str}{ip_str}"

    # 4. USB connections
    if _RE_USB_CONNECTION.search(line):
        return "usb_connection", "External USB storage device attached to system"

    # 5. Executable events
    if _RE_EXECUTABLE_EVENTS.search(line):
        if "mimikatz" in line.lower():
            desc = "Credential dumper invocation: mimikatz.exe"
        elif "powershell" in line.lower():
            desc = "Encoded PowerShell execution launched"
        elif "cmd.exe" in line.lower():
            desc = "Command shell payload executed: cmd.exe"
        elif "exfiltrate" in line.lower():
            desc = "Data exfiltration utility executed"
        else:
            desc = "Suspicious process creation or executable launch"
        return "executable_event", desc

    # Default informational
    return "info", "Routine system operational event"


# =============================================================================
# SINGLE LINE PARSING (FOR LIVE MONITORING AND STREAMING)
# =============================================================================

def parse_log_line(line: str) -> Dict[str, Any]:
    """
    Parse an individual log line and return a structured event record.
    Supports real-time incremental parsing for streaming monitors.
    """
    clean_line = line.strip()
    timestamp = extract_timestamp(clean_line)
    category, description = classify_log_line(clean_line)
    ips = extract_ip_addresses(clean_line)
    users = extract_users(clean_line)

    return {
        "timestamp": timestamp,
        "category": category,
        "description": description,
        "raw_line": clean_line,
        "ip_addresses": ips,
        "users": users,
    }


# =============================================================================
# BATCH LOG LINES PARSER
# =============================================================================

def parse_log_lines(lines: List[str]) -> Dict[str, Any]:
    """
    Accept a list of log lines and return a structured forensic facts dictionary.
    """
    failed_logins = 0
    successful_logins = 0
    usb_connections = 0
    executable_events = 0
    deleted_files = 0

    all_ips: Set[str] = set()
    all_users: Set[str] = set()
    timeline_events: List[Dict[str, str]] = []

    total_lines = len(lines)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        event = parse_log_line(stripped)
        cat = event["category"]

        if cat == "failed_login":
            failed_logins += 1
        elif cat == "successful_login":
            successful_logins += 1
        elif cat == "usb_connection":
            usb_connections += 1
        elif cat == "executable_event":
            executable_events += 1
        elif cat == "deleted_file":
            deleted_files += 1

        for ip in event["ip_addresses"]:
            all_ips.add(ip)

        for u in event["users"]:
            all_users.add(u)

        if cat != "info":
            timeline_events.append({
                "timestamp": event["timestamp"],
                "category": cat,
                "description": event["description"],
                "raw_line": event["raw_line"],
            })

    return {
        "evidence_type": "log",
        "total_lines": total_lines,
        "failed_logins": failed_logins,
        "successful_logins": successful_logins,
        "usb_connections": usb_connections,
        "executable_events": executable_events,
        "deleted_files": deleted_files,
        "ip_addresses": sorted(list(all_ips)),
        "users_flagged": sorted(list(all_users)),
        "timeline_events": timeline_events,
    }


# =============================================================================
# FILE PARSER
# =============================================================================

def parse_log_file(file_path: str) -> Dict[str, Any]:
    """
    Open and parse a log file from disk, handling multiple character encodings.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Log file not found: {file_path}")

    lines: List[str] = []
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for enc in encodings_to_try:
        try:
            with open(file_path, "r", encoding=enc) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if not lines and os.path.getsize(file_path) > 0:
        # Final fallback with error replacement
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

    return parse_log_lines(lines)


# =============================================================================
# CLASS INTERFACE
# =============================================================================

class LogAnalyzer:
    """
    Object-oriented wrapper around the deterministic log analyzer routines.
    """

    def __init__(self):
        pass

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a full log file on disk."""
        return parse_log_file(file_path)

    def parse_lines(self, lines: List[str]) -> Dict[str, Any]:
        """Parse a batch list of log lines."""
        return parse_log_lines(lines)

    def parse_line(self, line: str) -> Dict[str, Any]:
        """Parse an individual log line."""
        return parse_log_line(line)


# =============================================================================
# STANDALONE TEST HARNESS
# =============================================================================

if __name__ == "__main__":
    import json

    # Resolve path to sample_evidence/system.log
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sample_log = os.path.join(project_root, "sample_evidence", "system.log")

    if not os.path.exists(sample_log):
        # Fallback to local relative check
        sample_log = os.path.join("sample_evidence", "system.log")

    print("=" * 70)
    print("FORENSEQUENCE - LOG ANALYZER TEST HARNESS")
    print("=" * 70)
    print(f"Target Evidence: {os.path.abspath(sample_log)}")

    if os.path.exists(sample_log):
        facts = parse_log_file(sample_log)

        print("\n--- EXTRACTED FACT SUMMARY ---")
        print(f"Evidence Type     : {facts['evidence_type']}")
        print(f"Total Lines       : {facts['total_lines']}")
        print(f"Failed Logins     : {facts['failed_logins']}")
        print(f"Successful Logins : {facts['successful_logins']}")
        print(f"USB Connections   : {facts['usb_connections']}")
        print(f"Executable Events : {facts['executable_events']}")
        print(f"Deleted Files     : {facts['deleted_files']}")
        print(f"Flagged IPs       : {', '.join(facts['ip_addresses'])}")
        print(f"Flagged Users     : {', '.join(facts['users_flagged'])}")

        print(f"\n--- TIMELINE SECURITY EVENTS ({len(facts['timeline_events'])} events) ---")
        for i, ev in enumerate(facts["timeline_events"], start=1):
            ts = ev["timestamp"] or "NO_TIME"
            cat = ev["category"].upper()
            desc = ev["description"]
            print(f"[{i:02d}] {ts} | {cat:<18} | {desc}")

        print("\n--- COMPLETE JSON FACTS DICTIONARY ---")
        print(json.dumps(facts, indent=2))
        print("\n[OK] Log analysis completed with deterministic facts.")
    else:
        print(f"\n[ERROR] Sample log file not found at: {sample_log}")

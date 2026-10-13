# =============================================================================
# analyzers/dispatcher.py
# FORENSEQUENCE - Unified Multi-Source Forensic Evidence Dispatcher
# =============================================================================

from __future__ import annotations

import csv
import os
import sys
from typing import Any, Dict, List, Optional, Set

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from analyzers.log_analyzer import parse_log_file
from analyzers.file_analyzer import parse_file_system
from analyzers.browser_analyzer import parse_browser_history
from analyzers.email_analyzer import parse_email_evidence


def create_empty_facts(evidence_type: str = "unified") -> Dict[str, Any]:
    """Return a zeroed facts dictionary schema compatible with all forensic analyzers."""
    return {
        "evidence_type": evidence_type,
        "total_lines": 0,
        "total_files": 0,
        "total_emails": 0,
        "total_visits": 0,
        "failed_logins": 0,
        "successful_logins": 0,
        "usb_connections": 0,
        "executable_events": 0,
        "deleted_files": 0,
        "suspicious_domains": 0,
        "hidden_files": 0,
        "autorun_entries": 0,
        "large_files": 0,
        "duplicate_files": 0,
        "suspicious_files": 0,
        "suspicious_extensions": 0,
        "download_events": 0,
        "unknown_sender": False,
        "unknown_sender_count": 0,
        "executable_attachment": False,
        "executable_attachment_count": 0,
        "urgent_subjects_count": 0,
        "suspicious_searches_count": 0,
        "ip_addresses": [],
        "users_flagged": [],
        "flagged_urls": [],
        "flagged_emails": [],
        "suspicious_searches": [],
        "timeline_events": [],
        "file_list": [],
        "duplicate_groups": [],
    }


def detect_evidence_type(file_path: str) -> str:
    """
    Deterministically detect the forensic evidence category of a given file or directory.
    Returns one of: 'file', 'log', 'browser', 'email'.
    """
    norm_path = os.path.abspath(file_path)
    if os.path.isdir(norm_path):
        return "file"

    fname = os.path.basename(norm_path).lower()
    ext = os.path.splitext(fname)[1]

    if ext in (".log", ".txt", ".evt", ".evtx"):
        return "log"

    if ext in (".eml", ".msg", ".mbox"):
        return "email"

    if ext == ".csv":
        # Inspect CSV column header
        try:
            with open(norm_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                header_cols = [c.strip().lower() for c in header]
                if any(col in header_cols for col in ("sender", "recipient", "attachments", "subject")):
                    return "email"
                if any(col in header_cols for col in ("url", "visit_count", "visit_time")):
                    return "browser"
        except Exception:
            pass

        # Fallback to name keywords
        if any(kw in fname for kw in ("mail", "email", "inbox")):
            return "email"
        if any(kw in fname for kw in ("browser", "history", "chrome", "edge", "firefox", "url")):
            return "browser"
        return "browser"

    return "file"


def parse_evidence_item(evidence_type: str, file_path: str) -> Dict[str, Any]:
    """
    Parse an evidence file or directory according to its evidence type.

    Dispatches:
      - 'log'     -> log_analyzer.parse_log_file(file_path)
      - 'file'    -> file_analyzer.parse_file_system(file_path)
      - 'browser' -> browser_analyzer.parse_browser_history(file_path)
      - 'email'   -> email_analyzer.parse_email_evidence(file_path)

    Gracefully catches exceptions and returns the standard facts schema on error.
    """
    if not os.path.exists(file_path):
        empty = create_empty_facts(evidence_type)
        empty["error"] = f"Path not found: {file_path}"
        return empty

    ev_type = (evidence_type or "").strip().lower()
    if ev_type in ("", "auto", "unknown"):
        ev_type = detect_evidence_type(file_path)

    try:
        if ev_type == "log":
            return parse_log_file(file_path)
        elif ev_type == "file":
            return parse_file_system(file_path)
        elif ev_type == "browser":
            return parse_browser_history(file_path)
        elif ev_type == "email":
            return parse_email_evidence(file_path)
        else:
            # Fallback based on file system inspection
            detected = detect_evidence_type(file_path)
            if detected == "log":
                return parse_log_file(file_path)
            elif detected == "browser":
                return parse_browser_history(file_path)
            elif detected == "email":
                return parse_email_evidence(file_path)
            else:
                return parse_file_system(file_path)
    except Exception as exc:
        err_facts = create_empty_facts(ev_type)
        err_facts["error"] = f"Extraction failed for {file_path}: {exc}"
        return err_facts


def merge_facts_list(facts_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple facts dictionaries into a single unified working facts dictionary.

    - Sums all numeric counters.
    - Computes unified boolean flags:
        unknown_sender = unknown_sender_count > 0
        executable_attachment = executable_attachment_count > 0
    - Combines and deduplicates list fields:
        ip_addresses, users_flagged, flagged_urls, flagged_emails, suspicious_searches.
    - Merges and sorts all timeline_events chronologically by timestamp.
    """
    unified = create_empty_facts(evidence_type="unified")

    all_ips: Set[str] = set()
    all_users: Set[str] = set()
    all_searches: Set[str] = set()
    all_urls: List[Dict[str, Any]] = []
    seen_urls: Set[str] = set()
    all_emails: List[Dict[str, Any]] = []
    seen_emails: Set[str] = set()
    all_events: List[Dict[str, Any]] = []

    for facts in facts_list:
        if not facts or not isinstance(facts, dict):
            continue

        # Numeric sums
        unified["failed_logins"] += int(facts.get("failed_logins", 0) or 0)
        unified["successful_logins"] += int(facts.get("successful_logins", 0) or 0)
        unified["usb_connections"] += int(facts.get("usb_connections", 0) or 0)
        unified["executable_events"] += int(facts.get("executable_events", 0) or 0)
        unified["deleted_files"] += int(facts.get("deleted_files", 0) or 0)
        unified["suspicious_domains"] += int(facts.get("suspicious_domains", 0) or 0)
        unified["hidden_files"] += int(facts.get("hidden_files", 0) or 0)
        unified["autorun_entries"] += int(facts.get("autorun_entries", 0) or 0)
        unified["large_files"] += int(facts.get("large_files", 0) or 0)
        unified["duplicate_files"] += int(facts.get("duplicate_files", 0) or 0)
        unified["suspicious_files"] += int(facts.get("suspicious_files", 0) or 0)
        unified["suspicious_extensions"] += int(facts.get("suspicious_extensions", 0) or 0)
        unified["total_visits"] += int(facts.get("total_visits", 0) or 0)
        unified["unknown_sender_count"] += int(facts.get("unknown_sender_count", 0) or 0)
        unified["executable_attachment_count"] += int(facts.get("executable_attachment_count", 0) or 0)
        unified["urgent_subjects_count"] += int(facts.get("urgent_subjects_count", 0) or 0)
        unified["download_events"] += int(facts.get("download_events", 0) or 0)
        unified["total_lines"] += int(facts.get("total_lines", 0) or 0)
        unified["total_files"] += int(facts.get("total_files", 0) or 0)
        unified["total_emails"] += int(facts.get("total_emails", 0) or 0)

        # File analyzer lists
        for f_item in facts.get("file_list", []):
            unified["file_list"].append(f_item)
        for d_group in facts.get("duplicate_groups", []):
            unified["duplicate_groups"].append(d_group)

        # IP addresses
        for ip in facts.get("ip_addresses", []):
            if ip and isinstance(ip, str):
                all_ips.add(ip.strip())

        # Flagged users
        for user in facts.get("users_flagged", []):
            if user and isinstance(user, str):
                all_users.add(user.strip())

        # Suspicious searches
        for q in facts.get("suspicious_searches", []):
            if q and isinstance(q, str):
                all_searches.add(q.strip())

        # Flagged URLs
        for url_item in facts.get("flagged_urls", []):
            u_key = f"{url_item.get('timestamp', '')}_{url_item.get('url', '')}"
            if u_key not in seen_urls:
                seen_urls.add(u_key)
                all_urls.append(url_item)

        # Flagged emails
        for em_item in facts.get("flagged_emails", []):
            em_key = f"{em_item.get('timestamp', '')}_{em_item.get('sender', '')}_{em_item.get('subject', '')}"
            if em_key not in seen_emails:
                seen_emails.add(em_key)
                all_emails.append(em_item)

        # Timeline events
        for ev in facts.get("timeline_events", []):
            if isinstance(ev, dict):
                all_events.append(ev)

    # Compute unified boolean flags
    unified["unknown_sender"] = unified["unknown_sender_count"] > 0
    unified["executable_attachment"] = unified["executable_attachment_count"] > 0
    unified["suspicious_searches_count"] = len(all_searches)

    # Sort deduplicated list fields
    unified["ip_addresses"] = sorted(list(all_ips))
    unified["users_flagged"] = sorted(list(all_users))
    unified["suspicious_searches"] = sorted(list(all_searches))
    unified["flagged_urls"] = sorted(all_urls, key=lambda x: str(x.get("timestamp", "")))
    unified["flagged_emails"] = sorted(all_emails, key=lambda x: str(x.get("timestamp", "")))

    # Sort timeline events chronologically
    def _ts_key(e: Dict[str, Any]) -> str:
        return str(e.get("timestamp") or "")

    unified["timeline_events"] = sorted(all_events, key=_ts_key)

    return unified


if __name__ == "__main__":
    print("=" * 70)
    print("FORENSEQUENCE - DISPATCHER STANDALONE TEST")
    print("=" * 70)

    sample_evidence_dir = os.path.join(PROJECT_ROOT, "sample_evidence")
    log_file = os.path.join(sample_evidence_dir, "system.log")
    folder_evidence = os.path.join(sample_evidence_dir, "evidence_folder")
    browser_file = os.path.join(sample_evidence_dir, "browser_history.csv")
    email_file = os.path.join(sample_evidence_dir, "emails.csv")

    tests = [
        ("log", log_file),
        ("file", folder_evidence),
        ("browser", browser_file),
        ("email", email_file),
    ]

    all_facts: List[Dict[str, Any]] = []
    for ev_type, p in tests:
        if os.path.exists(p):
            res = parse_evidence_item(ev_type, p)
            all_facts.append(res)
            print(f"[{ev_type.upper()}] Parsed {os.path.basename(p)} -> events: {len(res.get('timeline_events', []))}")
        else:
            print(f"[{ev_type.upper()}] Not found: {p}")

    unified = merge_facts_list(all_facts)
    print("\n--- UNIFIED FACTS SUMMARY ---")
    for k in (
        "failed_logins", "successful_logins", "usb_connections", "executable_events",
        "deleted_files", "suspicious_domains", "hidden_files", "autorun_entries",
        "unknown_sender", "executable_attachment", "ip_addresses", "users_flagged"
    ):
        print(f"  {k:<26}: {unified.get(k)}")

    print(f"  Total Timeline Events     : {len(unified['timeline_events'])}")

    from ai.rule_engine import ForwardChainingEngine
    eng = ForwardChainingEngine()
    eval_res = eng.evaluate(unified)
    print(f"\n[AI Evaluation] Risk Score: {eval_res['risk_score']} ({eval_res['risk_level']})")
    for finding in eval_res["findings"]:
        print(f"  - {finding['rule_code']}: {finding['name']} (+{finding['severity']})")

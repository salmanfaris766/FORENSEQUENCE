# =============================================================================
# analyzers/email_analyzer.py
# FORENSEQUENCE - Deterministic Forensic Email Analyzer
# =============================================================================

from __future__ import annotations

import csv
import os
import re
import sys
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Any, Dict, List, Set

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------------------------
INTERNAL_DOMAIN = "company.com"
EXECUTABLE_EXTENSIONS: Set[str] = {
    ".exe", ".ps1", ".bat", ".vbs", ".js", ".scr", ".jar",
    ".lnk", ".cmd", ".cpl", ".wsf", ".xlsm", ".docm",
}
URGENT_KEYWORDS: Set[str] = {
    "urgent",
    "overdue",
    "action required",
    "suspended",
    "wire transfer",
    "invoice",
    "password reset",
    "verify your credentials",
}
TYPOSQUAT_DOMAINS: Set[str] = {"paypa1", "go0gle", "micr0s0ft", "faceb00k"}
SUSPICIOUS_TLDS: Set[str] = {".xyz", ".top", ".tk", ".ru", ".cf", ".gq"}
URL_REGEX = re.compile(r"https?://[^\s\",]+")
IP_REGEX = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


def _extract_urls(text: str) -> List[str]:
    """Return a list of URLs extracted from text."""
    return URL_REGEX.findall(text)


def _is_ip_only(host: str) -> bool:
    """Check if the host is a raw IPv4 address."""
    return bool(IP_REGEX.fullmatch(host))


def _is_suspicious_domain(url: str) -> bool:
    """Return True if the URL contains a suspicious domain or IP host."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        if _is_ip_only(host):
            return True
        for bad in TYPOSQUAT_DOMAINS:
            if bad in host:
                return True
        for tld in SUSPICIOUS_TLDS:
            if host.endswith(tld):
                return True
        return False
    except Exception:
        return False


def _has_executable_attachment(attachments: str) -> bool:
    """Return True if any attachment filename ends with an executable or macro extension."""
    for att in attachments.split(";"):
        att = att.strip()
        if not att:
            continue
        _, ext = os.path.splitext(att.lower())
        if ext in EXECUTABLE_EXTENSIONS:
            return True
    return False


def _is_urgent_subject(subject: str) -> bool:
    """Return True if subject contains any urgency keyword."""
    low = subject.lower()
    return any(kw in low for kw in URGENT_KEYWORDS)


def _is_unknown_sender(sender: str) -> bool:
    """Return True if sender domain is not internal or matches suspicious patterns."""
    _, addr = parseaddr(sender)
    if "@" not in addr:
        return True
    domain = addr.split("@")[-1].lower()
    if domain == INTERNAL_DOMAIN.lower():
        return False
    for bad in TYPOSQUAT_DOMAINS:
        if bad in domain:
            return True
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            return True
    return True


def _normalize_timestamp(ts_str: str) -> str:
    """Normalize timestamp string into standard ISO format 'YYYY-MM-DD HH:MM:SS'."""
    raw = ts_str.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return raw


def parse_email_evidence(file_path: str) -> Dict[str, Any]:
    """Parse a CSV of email evidence and return a standardized forensic facts dictionary."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Email evidence file not found: {file_path}")

    total_emails = 0
    unknown_sender_count = 0
    executable_attachment_count = 0
    suspicious_domains_count = 0
    urgent_subjects_count = 0
    flagged_emails: List[Dict[str, Any]] = []
    timeline_events: List[Dict[str, Any]] = []
    extracted_ips: Set[str] = set()

    with open(file_path, newline="", encoding="utf-8-sig", errors="replace") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            total_emails += 1
            timestamp = _normalize_timestamp(row.get("date", ""))
            sender = row.get("sender", "").strip()
            recipient = row.get("recipient", "").strip()
            subject = row.get("subject", "").strip()
            body = row.get("body", "").strip()
            attachments = row.get("attachments", "").strip()

            unknown = _is_unknown_sender(sender)
            exec_att = _has_executable_attachment(attachments)
            urls = _extract_urls(subject + " " + body)
            suspicious_url = any(_is_suspicious_domain(u) for u in urls)
            urgent = _is_urgent_subject(subject)

            for u in urls:
                try:
                    from urllib.parse import urlparse
                    h = urlparse(u).hostname or ""
                    if _is_ip_only(h):
                        extracted_ips.add(h)
                except Exception:
                    pass

            if unknown:
                unknown_sender_count += 1
            if exec_att:
                executable_attachment_count += 1
            if suspicious_url:
                suspicious_domains_count += 1
            if urgent:
                urgent_subjects_count += 1

            if unknown or exec_att or suspicious_url or urgent:
                reasons: List[str] = []
                if unknown:
                    reasons.append("unknown sender domain")
                if exec_att:
                    reasons.append("executable attachment")
                if suspicious_url:
                    reasons.append("suspicious URL in content")
                if urgent:
                    reasons.append("urgent / coercive subject line")

                flagged_emails.append({
                    "timestamp": timestamp,
                    "sender": sender,
                    "recipient": recipient,
                    "subject": subject,
                    "attachments": attachments,
                    "reasons": reasons,
                })

                category = "malicious_email" if (exec_att or suspicious_url) else "info"
                timeline_events.append({
                    "timestamp": timestamp,
                    "category": category,
                    "description": f"Email from {sender} flagged: {', '.join(reasons)}",
                    "raw_line": f"{timestamp} | {sender} -> {recipient} | {subject} | {attachments}",
                    "severity": 30 if exec_att else 15,
                    "source": "email_analyzer",
                    "rule_code": "R006" if (unknown and exec_att) else "",
                })

    facts: Dict[str, Any] = {
        "evidence_type": "email",
        "total_emails": total_emails,
        "unknown_sender": unknown_sender_count > 0,
        "unknown_sender_count": unknown_sender_count,
        "executable_attachment": executable_attachment_count > 0,
        "executable_attachment_count": executable_attachment_count,
        "suspicious_domains": suspicious_domains_count,
        "urgent_subjects_count": urgent_subjects_count,
        "flagged_emails": flagged_emails,
        "timeline_events": sorted(timeline_events, key=lambda e: e.get("timestamp", "")),
        "ip_addresses": sorted(list(extracted_ips)),
        # Cross-engine compatibility fields
        "failed_logins": 0,
        "successful_logins": 0,
        "usb_connections": 0,
        "executable_events": 0,
        "deleted_files": 0,
        "users_flagged": [],
    }
    return facts


class EmailAnalyzer:
    """Class wrapper for email evidence analysis."""

    def __init__(self) -> None:
        pass

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        return parse_email_evidence(file_path)


if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sample_path = os.path.join(repo_root, "sample_evidence", "emails.csv")
    if not os.path.isfile(sample_path):
        print(f"[ERROR] Sample evidence not found at {sample_path}")
        sys.exit(1)

    facts = parse_email_evidence(sample_path)
    print("--- Email Evidence Facts ---")
    for k, v in facts.items():
        if k in {"flagged_emails", "timeline_events"}:
            continue
        print(f"{k}: {v}")
    print("\nFlagged Emails:")
    for fe in facts["flagged_emails"]:
        print(f"- {fe['timestamp']} | {fe['sender']} -> {fe['recipient']} | {fe['subject']} | Reasons: {', '.join(fe['reasons'])}")
    print("\nTimeline Events:")
    for ev in facts["timeline_events"]:
        print(f"[{ev['timestamp']}] [{ev['category']}] {ev['description']}")

    # Forward Chaining check
    try:
        from ai.rule_engine import ForwardChainingEngine
        engine = ForwardChainingEngine()
        result = engine.evaluate(facts)
        print("\n[Forward Chaining Result]")
        print(f"Risk Score: {result['risk_score']}, Level: {result['risk_level']}")
        for f in result["findings"]:
            print(f"  Triggered: {f['rule_code']} - {f['name']}")
    except Exception as exc:
        print(f"Engine test skipped: {exc}")

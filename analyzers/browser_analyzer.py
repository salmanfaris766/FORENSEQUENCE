# =============================================================================
# analyzers/browser_analyzer.py
# FORENSEQUENCE - Deterministic Forensic Browser History Analyzer
# =============================================================================

from __future__ import annotations

import csv
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Set
from urllib.parse import parse_qs, unquote_plus, urlparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------------------------
SUSPICIOUS_SEARCH_KEYWORDS: List[str] = [
    "bypass antivirus",
    "bypass av",
    "mimikatz",
    "reverse shell",
    "one liner",
    "cmd reverse",
    "keylogger",
    "privilege escalation",
    "meterpreter",
    "cobalt strike",
    "payload download",
    "backdoor",
    "exfiltration",
    "credential dump",
]

DANGEROUS_DOWNLOAD_EXTENSIONS: Set[str] = {
    ".exe", ".ps1", ".bat", ".vbs", ".js", ".scr", ".jar",
    ".dll", ".cmd", ".zip", ".tar", ".gz", ".7z",
}

TYPOSQUAT_DOMAINS: Set[str] = {
    "paypa1", "go0gle", "micr0s0ft", "faceb00k", "app1e", "amaz0n",
}

KNOWN_RISK_HOSTS: Set[str] = {
    "pastebin.com",
    "tempfile-drop.net",
    "malicious-host.org",
}

IP_REGEX = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


def _is_ip_host(host: str) -> bool:
    """Return True if host is an IPv4 address."""
    clean_host = host.split(":")[0]
    return bool(IP_REGEX.fullmatch(clean_host))


def _extract_search_query(url: str) -> str:
    """Extract search query parameter 'q' from search engine URLs."""
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if any(se in host for se in ("google.", "duckduckgo.", "bing.", "yahoo.")):
            qs = parse_qs(parsed.query)
            if "q" in qs and qs["q"]:
                return unquote_plus(qs["q"][0]).strip()
    except Exception:
        pass
    return ""


def _is_suspicious_search(query: str) -> bool:
    """Check if query contains known offensive security / malware search terms."""
    if not query:
        return False
    low = query.lower()
    return any(kw in low for kw in SUSPICIOUS_SEARCH_KEYWORDS)


def _is_dangerous_download(url: str) -> bool:
    """Return True if the URL points to an executable or payload file download."""
    try:
        path = urlparse(url).path.lower()
        _, ext = os.path.splitext(path)
        return ext in DANGEROUS_DOWNLOAD_EXTENSIONS
    except Exception:
        return False


def _is_suspicious_domain(url: str) -> bool:
    """Check if the URL hostname is suspicious, typosquatted, or raw-IP."""
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        if _is_ip_host(host):
            return True
        for typo in TYPOSQUAT_DOMAINS:
            if typo in host:
                return True
        for risk in KNOWN_RISK_HOSTS:
            if risk in host:
                return True
        return False
    except Exception:
        return False


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


def parse_browser_history(file_path: str) -> Dict[str, Any]:
    """
    Parse a CSV of browser history records and return a standardized forensic facts dictionary.
    The CSV must have columns: url, title, visit_time, visit_count.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Browser history file not found: {file_path}")

    total_visits = 0
    suspicious_domains_count = 0
    download_events = 0
    suspicious_searches: List[str] = []
    flagged_urls: List[Dict[str, Any]] = []
    timeline_events: List[Dict[str, Any]] = []
    extracted_ips: Set[str] = set()

    with open(file_path, newline="", encoding="utf-8-sig", errors="replace") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row.get("url", "").strip()
            title = row.get("title", "").strip()
            visit_time = _normalize_timestamp(row.get("visit_time", ""))
            try:
                vc = int(row.get("visit_count", 1))
            except (ValueError, TypeError):
                vc = 1
            total_visits += vc

            # Check search queries
            query = _extract_search_query(url)
            is_bad_search = _is_suspicious_search(query)
            if is_bad_search:
                if query not in suspicious_searches:
                    suspicious_searches.append(query)

            # Check domain & host
            is_bad_domain = _is_suspicious_domain(url)
            try:
                host = urlparse(url).hostname or ""
                if _is_ip_host(host):
                    extracted_ips.add(host.split(":")[0])
            except Exception:
                pass

            if is_bad_domain:
                suspicious_domains_count += 1

            # Check payload downloads
            is_download = _is_dangerous_download(url)
            if is_download:
                download_events += 1

            # Build flagged record if risk factors present
            if is_bad_search or is_bad_domain or is_download:
                reasons: List[str] = []
                if is_bad_search:
                    reasons.append(f"suspicious search query '{query}'")
                if is_bad_domain:
                    reasons.append("suspicious domain/host")
                if is_download:
                    reasons.append("executable/payload download")

                flagged_urls.append({
                    "timestamp": visit_time,
                    "url": url,
                    "title": title,
                    "visit_count": vc,
                    "reasons": reasons,
                })

                severity = 25 if (is_download or is_bad_domain) else 15
                timeline_events.append({
                    "timestamp": visit_time,
                    "category": "browser_navigation",
                    "description": f"Browser navigation flagged ({', '.join(reasons)}): {url}",
                    "raw_line": f"{visit_time} | {title} | {url} | visits={vc}",
                    "severity": severity,
                    "source": "browser_analyzer",
                    "rule_code": "R005" if is_bad_domain else "",
                })

    facts: Dict[str, Any] = {
        "evidence_type": "browser",
        "total_visits": total_visits,
        "suspicious_domains": suspicious_domains_count,
        "download_events": download_events,
        "suspicious_searches_count": len(suspicious_searches),
        "suspicious_searches": suspicious_searches,
        "flagged_urls": flagged_urls,
        "timeline_events": sorted(timeline_events, key=lambda e: e.get("timestamp", "")),
        "ip_addresses": sorted(list(extracted_ips)),
        # Cross-engine compatibility fields
        "failed_logins": 0,
        "successful_logins": 0,
        "usb_connections": 0,
        "executable_events": download_events,
        "deleted_files": 0,
        "unknown_sender": False,
        "executable_attachment": False,
        "users_flagged": [],
    }
    return facts


class BrowserAnalyzer:
    """Class wrapper for browser evidence analysis."""

    def __init__(self) -> None:
        pass

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        return parse_browser_history(file_path)


if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sample_path = os.path.join(repo_root, "sample_evidence", "browser_history.csv")
    if not os.path.isfile(sample_path):
        print(f"[ERROR] Sample evidence not found at {sample_path}")
        sys.exit(1)

    facts = parse_browser_history(sample_path)
    print("--- Browser Evidence Facts ---")
    for k, v in facts.items():
        if k in {"flagged_urls", "timeline_events"}:
            continue
        print(f"{k}: {v}")
    print("\nSuspicious Searches:")
    for s in facts["suspicious_searches"]:
        print(f"- {s}")
    print("\nFlagged URLs:")
    for u in facts["flagged_urls"]:
        print(f"- {u['timestamp']} | {u['url']} | Reasons: {', '.join(u['reasons'])}")
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

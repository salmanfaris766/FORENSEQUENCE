# =============================================================================
# analysis/timeline.py
# FORENSEQUENCE - Chronological Event Timeline Engine
# =============================================================================
#
# Produces a unified, sorted, forensic event timeline by merging raw log
# evidence events (from the log analyzer) with AI-derived findings (from the
# Forward Chaining Engine). All entries follow a canonical schema so the GUI
# can render a single consistent list without type-switching.
#
# Schema per entry:
#   {
#       "timestamp":   str   "YYYY-MM-DD HH:MM:SS" or "" if unknown
#       "category":    str   see _VALID_CATEGORIES below
#       "title":       str   short event label
#       "description": str   human-readable detail sentence
#       "severity":    int   0 for raw evidence; finding weight for AI findings
#       "source":      str   "evidence" or "ai_inference"
#       "rule_code":   str | None   only for ai_inference entries
#       "raw":         str | None   original log line for evidence entries
#   }
# =============================================================================

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional


# =============================================================================
# CONSTANTS
# =============================================================================

_VALID_CATEGORIES = {
    "failed_login",
    "successful_login",
    "usb_connection",
    "executable_event",
    "deleted_file",
    "browser_navigation",
    "malicious_email",
    "hidden_file",
    "autorun_entry",
    "large_file",
    "suspicious_extension",
    "finding",
    "info",
}

# Fallback sentinel used when we have no parseable timestamp
_EPOCH_FALLBACK = "9999-12-31 23:59:59"

# Human-readable titles for raw evidence categories
_CATEGORY_TITLES: Dict[str, str] = {
    "failed_login":         "Failed Authentication Attempt",
    "successful_login":     "Successful Login Session",
    "usb_connection":       "USB Storage Device Connected",
    "executable_event":     "Suspicious Process Execution",
    "deleted_file":         "File Deletion / Anti-Forensics",
    "browser_navigation":   "Browser Navigation / Web Access",
    "malicious_email":      "Flagged / Malicious Email Event",
    "hidden_file":          "Hidden Forensic File Artifact",
    "autorun_entry":        "Persistence / Autorun Entry",
    "large_file":           "Anomalous Large File Artifact",
    "suspicious_extension": "Suspicious File Extension",
    "info":                 "Informational Event",
}


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _parse_ts(ts_str: str) -> datetime:
    """
    Safely parse a 'YYYY-MM-DD HH:MM:SS' timestamp string to a datetime.
    Falls back to datetime.max so unknown-timestamp entries sort last.
    """
    if not ts_str:
        return datetime.max
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return datetime.max


def _entry_sort_key(entry: Dict[str, Any]):
    """
    Primary sort by timestamp ascending.
    Secondary: evidence before ai_inference (evidence = 0, ai_inference = 1).
    Tertiary: by severity descending within ai_inference entries.
    """
    ts = _parse_ts(entry.get("timestamp", ""))
    source_ord = 0 if entry.get("source") == "evidence" else 1
    return (ts, source_ord, -int(entry.get("severity", 0)))


def _normalize_evidence_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw timeline_events dict (from log_analyzer) into a canonical
    timeline entry.
    """
    cat = raw_event.get("category", "info")
    if cat not in _VALID_CATEGORIES:
        cat = "info"

    title = raw_event.get("title") or _CATEGORY_TITLES.get(cat, "Forensic Event")
    description = raw_event.get("description", "")
    # Prefer the richer description if available
    if not description:
        description = raw_event.get("raw_line", "")[:120]

    # Determine severity, handling possible string representations
    sev_raw = raw_event.get("severity", 0)
    if isinstance(sev_raw, str):
        sev_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        severity = sev_map.get(sev_raw.lower(), 0)
    else:
        try:
            severity = int(sev_raw)
        except (ValueError, TypeError):
            severity = 0
    return {
        "timestamp":   raw_event.get("timestamp", ""),
        "category":    cat,
        "title":       title,
        "description": description,
        "severity":    severity,
        "source":      raw_event.get("source", "evidence"),
        "rule_code":   raw_event.get("rule_code", None),
        "raw":         raw_event.get("raw_line", None),
    }


def _normalize_finding_entry(
    finding: Dict[str, Any],
    fallback_ts: str,
) -> Dict[str, Any]:
    """
    Convert a ForwardChainingEngine finding dict into a canonical ai_inference
    timeline entry, using ``fallback_ts`` when no explicit timestamp is known.
    """
    return {
        "timestamp":   finding.get("created_at", fallback_ts),
        "category":    "finding",
        "title":       finding.get("name", "AI Derived Finding"),
        "description": finding.get("description", ""),
        "severity":    int(finding.get("severity", 0)),
        "source":      "ai_inference",
        "rule_code":   finding.get("rule_code", None),
        "raw":         None,
    }


def _latest_evidence_timestamp(entries: List[Dict[str, Any]]) -> str:
    """
    Return the latest parseable timestamp string from evidence entries,
    or empty string if none.
    """
    ts_vals = [
        _parse_ts(e["timestamp"])
        for e in entries
        if e.get("source") == "evidence" and e.get("timestamp")
    ]
    if not ts_vals:
        return ""
    latest_dt = max(t for t in ts_vals if t != datetime.max)
    if latest_dt == datetime.max:
        return ""
    return latest_dt.strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# PUBLIC API
# =============================================================================

def build_timeline(
    facts: Dict[str, Any],
    findings: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Build a unified, sorted forensic event timeline.

    Parameters
    ----------
    facts : dict
        Output dictionary from ``analyzers.log_analyzer.parse_log_file`` or
        ``parse_log_lines``.  Must contain a ``timeline_events`` key with a
        list of raw evidence event dicts.
    findings : list of dict, optional
        Output ``findings`` list from ``ai.rule_engine.ForwardChainingEngine.evaluate()``.
        Each finding is injected as an ``ai_inference`` timeline marker.

    Returns
    -------
    list of dict
        Sorted list of canonical timeline entries, oldest first.
    """
    entries: List[Dict[str, Any]] = []

    # 1. Normalize raw evidence timeline events
    raw_events = facts.get("timeline_events", [])
    for ev in raw_events:
        entries.append(_normalize_evidence_event(ev))

    # 2. Determine fallback timestamp for findings that have no timestamp
    fallback_ts = _latest_evidence_timestamp(entries)

    # 3. Inject AI findings as timeline markers
    if findings:
        for finding in findings:
            entry = _normalize_finding_entry(finding, fallback_ts)
            entries.append(entry)

    # 4. Sort: timestamp asc, evidence before ai_inference, severity desc
    entries.sort(key=_entry_sort_key)

    return entries


def filter_timeline(
    entries: List[Dict[str, Any]],
    categories: Optional[List[str]] = None,
    min_severity: int = 0,
) -> List[Dict[str, Any]]:
    """
    Filter a timeline entry list by category and minimum severity.

    Parameters
    ----------
    entries : list of dict
        Full timeline as returned by ``build_timeline()``.
    categories : list of str, optional
        If provided, only entries whose ``category`` is in this list are kept.
        Pass ``None`` or an empty list to disable category filtering.
    min_severity : int
        Minimum severity score threshold (inclusive).  Evidence events have
        severity 0, so a min_severity of 0 includes all entries.

    Returns
    -------
    list of dict
        Filtered subset, preserving chronological ordering.
    """
    result = entries

    if categories:
        cat_set = set(categories)
        result = [e for e in result if e.get("category") in cat_set]

    if min_severity > 0:
        result = [e for e in result if int(e.get("severity", 0)) >= min_severity]

    return result


def summarize_timeline(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Produce a statistical summary of a timeline entry list.

    Parameters
    ----------
    entries : list of dict
        Timeline entries as returned by ``build_timeline()``.

    Returns
    -------
    dict with keys:
        total_events     : int   - total number of entries
        counts_by_cat    : dict  - {category: count}
        first_event      : str   - earliest timestamp string (or "")
        last_event       : str   - latest timestamp string (or "")
        duration_seconds : int   - seconds between first and last (or 0)
        ai_findings      : int   - count of ai_inference entries
        evidence_events  : int   - count of evidence entries
    """
    counts: Dict[str, int] = {}
    ai_count = 0
    ev_count = 0
    timestamps = []

    for entry in entries:
        cat = entry.get("category", "info")
        counts[cat] = counts.get(cat, 0) + 1

        source = entry.get("source", "evidence")
        if source == "ai_inference":
            ai_count += 1
        else:
            ev_count += 1

        ts_str = entry.get("timestamp", "")
        if ts_str:
            dt = _parse_ts(ts_str)
            if dt != datetime.max:
                timestamps.append(dt)

    first_str = ""
    last_str = ""
    duration = 0

    if timestamps:
        earliest = min(timestamps)
        latest = max(timestamps)
        first_str = earliest.strftime("%Y-%m-%d %H:%M:%S")
        last_str = latest.strftime("%Y-%m-%d %H:%M:%S")
        duration = int((latest - earliest).total_seconds())

    return {
        "total_events":     len(entries),
        "counts_by_cat":    counts,
        "first_event":      first_str,
        "last_event":       last_str,
        "duration_seconds": duration,
        "ai_findings":      ai_count,
        "evidence_events":  ev_count,
    }


# =============================================================================
# TIMELINE BUILDER CLASS
# =============================================================================

class TimelineBuilder:
    """
    Forensic timeline aggregation and filtering service.
    Exposes static interfaces for timeline compilation, category filtering,
    and forensic span summarization.
    """

    @staticmethod
    def build_timeline(
        facts: Dict[str, Any],
        findings: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Compile a sorted forensic event timeline from facts and findings."""
        return build_timeline(facts, findings)

    @staticmethod
    def filter_timeline(
        entries: List[Dict[str, Any]],
        categories: Optional[List[str]] = None,
        min_severity: int = 0,
    ) -> List[Dict[str, Any]]:
        """Filter timeline entries by category set and minimum severity threshold."""
        return filter_timeline(entries, categories=categories, min_severity=min_severity)

    @staticmethod
    def summarize_timeline(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute statistical metric summary across a timeline sequence."""
        return summarize_timeline(entries)


# =============================================================================
# STANDALONE TEST HARNESS
# =============================================================================

if __name__ == "__main__":
    # Resolve project root so imports work when run directly
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(_here)
    if _root not in sys.path:
        sys.path.insert(0, _root)

    from analyzers.log_analyzer import parse_log_file
    from ai.rule_engine import ForwardChainingEngine

    sample_log = os.path.join(_root, "sample_evidence", "system.log")
    if not os.path.exists(sample_log):
        print(f"[ERROR] Sample log not found: {sample_log}")
        sys.exit(1)

    print("=" * 72)
    print("FORENSEQUENCE TIMELINE ENGINE - STANDALONE TEST")
    print("=" * 72)

    # 1. Parse evidence
    facts = parse_log_file(sample_log)
    print(f"Evidence parsed: {len(facts.get('timeline_events', []))} raw events")

    # 2. Run Forward Chaining
    engine = ForwardChainingEngine()
    result = engine.evaluate(facts)
    findings = result.get("findings", [])
    print(f"Forward Chaining: {len(findings)} findings derived")

    # 3. Build unified timeline
    timeline = build_timeline(facts, findings)

    # 4. Summary
    summary = summarize_timeline(timeline)
    print(f"\nTimeline Summary:")
    print(f"  Total entries  : {summary['total_events']}")
    print(f"  Evidence events: {summary['evidence_events']}")
    print(f"  AI findings    : {summary['ai_findings']}")
    print(f"  First event    : {summary['first_event'] or 'N/A'}")
    print(f"  Last event     : {summary['last_event'] or 'N/A'}")
    print(f"  Duration       : {summary['duration_seconds']} seconds")
    print(f"  Category counts: {summary['counts_by_cat']}")

    # 5. Print chronological sequence
    print(f"\nChronological Event Sequence ({len(timeline)} entries):")
    print("-" * 72)
    for i, entry in enumerate(timeline, start=1):
        ts     = entry["timestamp"] or "NO_TIMESTAMP"
        cat    = entry["category"].upper()
        src    = "AI" if entry["source"] == "ai_inference" else "EV"
        rule   = f" [{entry['rule_code']}]" if entry.get("rule_code") else ""
        sev    = f" (+{entry['severity']})" if entry["severity"] > 0 else ""
        title  = entry["title"]
        desc   = entry["description"][:60]
        print(f"[{i:03d}] {ts} | {src} | {cat:<18} |{rule}{sev} {title}")
        print(f"       {desc}")

    # 6. Demonstrate filter
    auth_only = filter_timeline(
        timeline,
        categories=["failed_login", "successful_login"],
    )
    print(f"\nFiltered (AUTH only): {len(auth_only)} entries")

    ai_only = filter_timeline(timeline, categories=["finding"])
    print(f"Filtered (AI only)  : {len(ai_only)} entries")

    print("\n[OK] Timeline engine test completed successfully.")

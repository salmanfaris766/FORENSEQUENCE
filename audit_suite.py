# =============================================================================
# audit_suite.py
# FORENSEQUENCE - Reality Audit Automated Test Suite (Zero Simulation Proof)
# =============================================================================

from __future__ import annotations

import os
import sys
import time
import shutil
import queue
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import (
    initialize_db,
    create_case,
    add_evidence,
    add_finding,
    add_report,
    get_case_by_id,
    get_evidence_for_case,
    get_findings_for_case,
    get_reports_for_case,
)
from analyzers.log_analyzer import parse_log_file
from analyzers.file_analyzer import _sha256_file
from analyzers.dispatcher import parse_evidence_item, merge_facts_list
from ai.rule_engine import ForwardChainingEngine
from monitoring.live_watcher import LiveMonitorManager
from reports.report_generator import generate_pdf_report


def run_test_b() -> Dict[str, Any]:
    print("\n--- RUNNING TEST B: LIVE CONTENT SENSITIVITY TEST ---")
    temp_dir = tempfile.mkdtemp(prefix="foren_audit_b_")
    try:
        clean_path = os.path.join(temp_dir, "clean.log")
        dirty_path = os.path.join(temp_dir, "dirty.log")

        # clean.log: Only normal successful login lines
        with open(clean_path, "w", encoding="utf-8") as f:
            f.write("2026-10-15 08:00:00 Accepted publickey for user alice from 192.168.1.10 port 22 ssh2\n")
            f.write("2026-10-15 08:05:00 Accepted password for user bob from 192.168.1.11 port 22 ssh2\n")
            f.write("2026-10-15 08:10:00 Session opened for user alice by (uid=0)\n")
            f.write("2026-10-15 08:15:00 Logon Success EventID 4624 for user charlie\n")

        # dirty.log: 8 failed logins, 1 USB attach, 4 executable launches, 12 deletions
        with open(dirty_path, "w", encoding="utf-8") as f:
            for i in range(8):
                f.write(f"2026-10-15 09:0{i}:00 Failed password for invalid user hacker_{i} from 10.0.0.99 port 444{i} ssh2\n")
            f.write("2026-10-15 09:10:00 kernel: New USB device found, idVendor=0781, idProduct=5583, Removable Media\n")
            f.write("2026-10-15 09:11:00 process creation EventID 4688: mimikatz.exe privilege::debug\n")
            f.write("2026-10-15 09:12:00 powershell.exe -ExecutionPolicy Bypass -NoProfile -enc SQBFAFgA\n")
            f.write("2026-10-15 09:13:00 cmd.exe /c whoami /all\n")
            f.write("2026-10-15 09:14:00 process creation EventID 4688: exfiltrate.exe -target 10.0.0.99\n")
            for j in range(12):
                f.write(f"2026-10-15 09:20:{j:02d} REMOVED file deleted /var/log/backup/db_backup_{j}.sql unlink()\n")

        clean_facts = parse_log_file(clean_path)
        dirty_facts = parse_log_file(dirty_path)

        engine = ForwardChainingEngine()
        clean_eval = engine.evaluate(clean_facts)
        dirty_eval = engine.evaluate(dirty_facts)

        res = {
            "clean_facts": {
                "failed_logins": clean_facts["failed_logins"],
                "successful_logins": clean_facts["successful_logins"],
                "usb_connections": clean_facts["usb_connections"],
                "executable_events": clean_facts["executable_events"],
                "deleted_files": clean_facts["deleted_files"],
            },
            "dirty_facts": {
                "failed_logins": dirty_facts["failed_logins"],
                "successful_logins": dirty_facts["successful_logins"],
                "usb_connections": dirty_facts["usb_connections"],
                "executable_events": dirty_facts["executable_events"],
                "deleted_files": dirty_facts["deleted_files"],
            },
            "clean_eval": {
                "risk_score": clean_eval["risk_score"],
                "risk_level": clean_eval["risk_level"],
                "fired_rules": clean_eval["fired_rule_codes"],
            },
            "dirty_eval": {
                "risk_score": dirty_eval["risk_score"],
                "risk_level": dirty_eval["risk_level"],
                "fired_rules": dirty_eval["fired_rule_codes"],
                "rules_fired_count": dirty_eval["rules_fired_count"],
            },
        }

        # Assertions
        assert clean_facts["failed_logins"] == 0
        assert clean_facts["executable_events"] == 0
        assert clean_facts["deleted_files"] == 0
        assert dirty_facts["failed_logins"] == 8
        assert dirty_facts["usb_connections"] == 1
        assert dirty_facts["executable_events"] == 4
        assert dirty_facts["deleted_files"] == 12

        assert clean_eval["risk_score"] == 0
        assert clean_eval["risk_level"] == "LOW"
        assert len(clean_eval["fired_rule_codes"]) == 0

        assert dirty_eval["risk_score"] > 60
        assert dirty_eval["risk_level"] == "HIGH"
        assert "R001" in dirty_eval["fired_rule_codes"]
        assert "R002" in dirty_eval["fired_rule_codes"]
        assert "R003" in dirty_eval["fired_rule_codes"]
        assert "R004" in dirty_eval["fired_rule_codes"]
        assert "R008" in dirty_eval["fired_rule_codes"]  # Chained rule

        print("TEST B PASS: Clean produced 0 risk score, Dirty produced high risk score (", dirty_eval["risk_score"], ") with R001, R002, R003, R004, R008 fired.")
        return res
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_test_c() -> Dict[str, Any]:
    print("\n--- RUNNING TEST C: FILE HASH INTEGRITY TEST ---")
    temp_dir = tempfile.mkdtemp(prefix="foren_audit_c_")
    try:
        f1 = os.path.join(temp_dir, "file1.bin")
        f2 = os.path.join(temp_dir, "file2.bin")
        f1_copy = os.path.join(temp_dir, "file1_copy.bin")

        with open(f1, "wb") as f:
            f.write(b"FORENSEQUENCE REALITY AUDIT PAYLOAD ALPHA 12345")
        with open(f2, "wb") as f:
            f.write(b"FORENSEQUENCE REALITY AUDIT PAYLOAD BETA 67890")

        shutil.copy2(f1, f1_copy)

        h1 = _sha256_file(f1)
        h2 = _sha256_file(f2)
        h1_copy = _sha256_file(f1_copy)

        # Reference hashlib direct computation
        expected_h1 = hashlib.sha256(b"FORENSEQUENCE REALITY AUDIT PAYLOAD ALPHA 12345").hexdigest()
        expected_h2 = hashlib.sha256(b"FORENSEQUENCE REALITY AUDIT PAYLOAD BETA 67890").hexdigest()

        assert h1 == expected_h1
        assert h2 == expected_h2
        assert h1 != h2
        assert h1 == h1_copy

        print(f"TEST C PASS: h1={h1}, h2={h2}, copy={h1_copy} match expectation.")
        return {"h1": h1, "h2": h2, "h1_copy": h1_copy, "identical_match": h1 == h1_copy, "different_match": h1 != h2}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_test_d() -> Dict[str, Any]:
    print("\n--- RUNNING TEST D: MULTI-SOURCE REAL PARSE TEST ---")
    sample_dir = PROJECT_ROOT / "sample_evidence"
    sources = [
        ("log", sample_dir / "system.log"),
        ("file", sample_dir / "evidence_folder"),
        ("browser", sample_dir / "browser_history.csv"),
        ("email", sample_dir / "emails.csv"),
    ]

    parsed_facts = []
    source_stats = {}
    for ev_type, p in sources:
        assert p.exists(), f"Evidence source missing: {p}"
        facts = parse_evidence_item(ev_type, str(p))
        parsed_facts.append(facts)
        source_stats[ev_type] = {
            "events_count": len(facts.get("timeline_events", [])),
            "evidence_type": facts.get("evidence_type"),
        }

    merged = merge_facts_list(parsed_facts)
    engine = ForwardChainingEngine()
    ai_res = engine.evaluate(merged)

    assert len(merged["timeline_events"]) > 0
    assert len(merged["ip_addresses"]) > 0
    assert len(merged["users_flagged"]) > 0
    assert ai_res["rules_fired_count"] > 0

    print(f"TEST D PASS: Merged {len(merged['timeline_events'])} events across 4 sources. Fired rules: {ai_res['fired_rule_codes']}, Risk Score: {ai_res['risk_score']}")
    return {
        "sources": source_stats,
        "merged_events_count": len(merged["timeline_events"]),
        "merged_ip_count": len(merged["ip_addresses"]),
        "merged_user_count": len(merged["users_flagged"]),
        "ai_risk_score": ai_res["risk_score"],
        "ai_risk_level": ai_res["risk_level"],
        "fired_rules": ai_res["fired_rule_codes"],
    }


def run_test_e() -> Dict[str, Any]:
    print("\n--- RUNNING TEST E: DATABASE REAL PERSISTENCE TEST ---")
    initialize_db()
    ts = int(time.time())
    case_num = f"AUDIT-CASE-{ts}"
    case_id = create_case(
        case_number=case_num,
        case_name="Reality Verification Persistence Case",
        investigator="Auditor Lead",
        description="Verifying SQL INSERT and retrieval integrity",
        status="OPEN",
    )

    dummy_hash = hashlib.sha256(f"evidence_{ts}".encode()).hexdigest()
    ev_id = add_evidence(
        case_id=case_id,
        filename="audit_sample.raw",
        evidence_type="file",
        file_path=f"c:/audit/path/{case_num}/audit_sample.raw",
        file_hash=dummy_hash,
    )

    finding_id = add_finding(
        case_id=case_id,
        rule_code="R001",
        finding="Brute Force Authentication Verified",
        severity=75,
    )

    # Retrieval
    retrieved_case = get_case_by_id(case_id)
    retrieved_evidence = get_evidence_for_case(case_id)
    retrieved_findings = get_findings_for_case(case_id)

    assert retrieved_case is not None
    assert retrieved_case["case_number"] == case_num
    assert retrieved_case["investigator"] == "Auditor Lead"

    assert len(retrieved_evidence) >= 1
    ev_match = next((e for e in retrieved_evidence if e["id"] == ev_id), None)
    assert ev_match is not None
    assert ev_match["filename"] == "audit_sample.raw"
    assert ev_match["file_hash"] == dummy_hash

    assert len(retrieved_findings) >= 1
    find_match = next((f for f in retrieved_findings if f["id"] == finding_id), None)
    assert find_match is not None
    assert find_match["rule_code"] == "R001"
    assert find_match["severity"] == 75

    print(f"TEST E PASS: Case {case_num} (ID: {case_id}), Evidence ID {ev_id}, Finding ID {finding_id} stored and retrieved with exact equality.")
    return {
        "case_id": case_id,
        "case_number": case_num,
        "evidence_id": ev_id,
        "evidence_hash": dummy_hash,
        "finding_id": finding_id,
        "verified": True,
    }


def run_test_f() -> Dict[str, Any]:
    print("\n--- RUNNING TEST F: LIVE MONITOR REAL FILE-EVENT TEST ---")
    temp_dir = tempfile.mkdtemp(prefix="foren_audit_f_")
    try:
        monitored_file = os.path.join(temp_dir, "live_monitored.log")
        with open(monitored_file, "w", encoding="utf-8") as f:
            f.write("2026-10-15 00:00:00 Initial line before monitoring\n")

        q = queue.Queue()
        manager = LiveMonitorManager(event_queue=q)
        started = manager.start_monitoring(monitored_file)
        assert started is True
        assert manager.is_monitoring() is True

        time.sleep(0.3)
        t_start = time.time()
        test_line = "2026-10-15 10:30:00 Failed password for root from 192.168.1.200 port 2222 ssh2\n"

        with open(monitored_file, "a", encoding="utf-8") as f:
            f.write(test_line)
            f.flush()

        # Wait for queue event
        payload = None
        try:
            payload = q.get(timeout=3.0)
            elapsed = time.time() - t_start
        except queue.Empty:
            elapsed = time.time() - t_start
            payload = None

        manager.stop_monitoring()
        assert not manager.is_monitoring()

        assert payload is not None, "Live monitor timed out without queue payload!"
        assert payload["type"] == "log_append"
        assert any("Failed password for root" in l for l in payload["raw_lines"])
        assert payload["incremental_facts"]["failed_logins"] >= 1

        print(f"TEST F PASS: Event received in {elapsed:.3f}s. New line and facts captured: {payload['incremental_facts']['failed_logins']} failed logins.")
        return {
            "elapsed_seconds": elapsed,
            "received_payload_type": payload["type"],
            "captured_lines": payload["raw_lines"],
            "incremental_facts": payload["incremental_facts"],
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_test_g(case_id: int) -> Dict[str, Any]:
    print("\n--- RUNNING TEST G: PDF REAL GENERATION TEST ---")
    out_dir = PROJECT_ROOT / "uploads"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = str(out_dir / f"audit_report_case_{case_id}.pdf")

    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    gen_path = generate_pdf_report(case_id=case_id, output_path=pdf_path)
    assert os.path.exists(gen_path), f"Generated PDF does not exist at {gen_path}"
    file_size = os.path.getsize(gen_path)
    assert file_size > 1000, f"PDF file size too small: {file_size} bytes"

    # Verify ReportLab PDF signature "%PDF-"
    with open(gen_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-", f"Invalid PDF header: {header}"

    # Register report in DB
    rep_id = add_report(case_id, gen_path)
    reps = get_reports_for_case(case_id)
    assert any(r["id"] == rep_id for r in reps)

    print(f"TEST G PASS: Generated PDF at {gen_path} with size {file_size:,} bytes. Magic header verified %PDF-. DB Report ID: {rep_id}.")
    return {
        "pdf_path": gen_path,
        "size_bytes": file_size,
        "header": header.decode("latin-1"),
        "db_report_id": rep_id,
    }


def main():
    print("=" * 80)
    print("FORENSEQUENCE - REALITY AUDIT COMPREHENSIVE AUTOMATED TEST RUNNER")
    print("=" * 80)

    res_b = run_test_b()
    res_c = run_test_c()
    res_d = run_test_d()
    res_e = run_test_e()
    res_f = run_test_f()
    res_g = run_test_g(res_e["case_id"])

    print("\n" + "=" * 80)
    print("ALL TESTS (B, C, D, E, F, G) EXECUTED AND PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()

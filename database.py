# =============================================================================
# database.py
# FORENSEQUENCE - SQLite Database Schema and Data Access Layer (DAL)
# =============================================================================
#
# All persistence for Cases, Evidence, AI Findings, and Reports lives here.
# Uses Python built-in sqlite3 module with parameterized queries throughout.
#
# DB file: forensequence.db (root directory, excluded from git via .gitignore)
# =============================================================================

import sqlite3
import os
import time
from typing import Optional

# ---------------------------------------------------------------------------
# Database path
# ---------------------------------------------------------------------------

_DB_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "forensequence.db"
)


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    """
    Open and return a configured sqlite3 connection.

    Configuration applied on every connection:
      - row_factory = sqlite3.Row  (dict-like row access by column name)
      - PRAGMA foreign_keys = ON   (enforce referential integrity)
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# =============================================================================
# SCHEMA INITIALIZATION
# =============================================================================

def initialize_db() -> None:
    """
    Create all required tables if they do not already exist.

    Tables created:
      - cases      : top-level investigation records
      - evidence   : files attached to a case (SHA-256 verified)
      - findings   : AI / rule-engine conclusions for a case
      - reports    : generated PDF report references
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS cases (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number   TEXT    NOT NULL UNIQUE,
        case_name     TEXT    NOT NULL,
        investigator  TEXT    NOT NULL,
        description   TEXT,
        status        TEXT    NOT NULL DEFAULT 'OPEN',
        created_at    DATETIME         DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS evidence (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id       INTEGER NOT NULL,
        filename      TEXT    NOT NULL,
        evidence_type TEXT    NOT NULL,
        file_path     TEXT    NOT NULL,
        file_hash     TEXT    NOT NULL,
        uploaded_at   DATETIME         DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS findings (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id    INTEGER NOT NULL,
        rule_code  TEXT    NOT NULL,
        finding    TEXT    NOT NULL,
        severity   INTEGER NOT NULL,
        created_at DATETIME         DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS reports (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id      INTEGER NOT NULL,
        report_path  TEXT    NOT NULL,
        generated_at DATETIME         DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
    );
    """
    with _get_connection() as conn:
        conn.executescript(ddl)


# =============================================================================
# CASE DAL
# =============================================================================

def create_case(
    case_number: str,
    case_name: str,
    investigator: str,
    description: str = "",
) -> int:
    """
    Insert a new case record and return its auto-assigned integer ID.

    Parameters
    ----------
    case_number  : Unique human-readable identifier, e.g. 'CASE-2025-001'.
    case_name    : Descriptive title of the case.
    investigator : Name of the assigned investigator.
    description  : Optional free-text case description (default empty string).

    Returns
    -------
    int
        The id of the newly created case row.

    Raises
    ------
    sqlite3.IntegrityError
        If a case with the same case_number already exists.
    """
    sql = (
        "INSERT INTO cases (case_number, case_name, investigator, description) "
        "VALUES (?, ?, ?, ?)"
    )
    with _get_connection() as conn:
        cursor = conn.execute(sql, (case_number, case_name, investigator, description))
        return cursor.lastrowid


def get_all_cases() -> list:
    """
    Retrieve all case records ordered by creation date descending.

    Returns
    -------
    list[dict]
        Each element has keys: id, case_number, case_name, investigator,
        description, status, created_at. Empty list if no cases exist.
    """
    sql = "SELECT * FROM cases ORDER BY created_at DESC;"
    with _get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_case_by_id(case_id: int) -> Optional[dict]:
    """
    Retrieve a single case by its primary key.

    Parameters
    ----------
    case_id : Integer primary key of the target case.

    Returns
    -------
    dict or None
        Dict of case columns if found, otherwise None.
    """
    sql = "SELECT * FROM cases WHERE id = ?;"
    with _get_connection() as conn:
        row = conn.execute(sql, (case_id,)).fetchone()
        return dict(row) if row else None


def update_case_status(case_id: int, status: str) -> bool:
    """
    Update the status field of an existing case.

    Parameters
    ----------
    case_id : Integer primary key of the target case.
    status  : New status string, e.g. 'OPEN', 'CLOSED', 'ARCHIVED'.

    Returns
    -------
    bool
        True if a row was updated, False if no matching case was found.
    """
    sql = "UPDATE cases SET status = ? WHERE id = ?;"
    with _get_connection() as conn:
        cursor = conn.execute(sql, (status, case_id))
        return cursor.rowcount > 0


def delete_case(case_id: int) -> bool:
    """
    Permanently delete a case and all child records via ON DELETE CASCADE.

    Child tables (evidence, findings, reports) are deleted automatically
    because their FOREIGN KEY definitions specify ON DELETE CASCADE.

    Parameters
    ----------
    case_id : Integer primary key of the case to delete.

    Returns
    -------
    bool
        True if the case existed and was deleted, False otherwise.
    """
    sql = "DELETE FROM cases WHERE id = ?;"
    with _get_connection() as conn:
        cursor = conn.execute(sql, (case_id,))
        return cursor.rowcount > 0


# =============================================================================
# EVIDENCE DAL
# =============================================================================

def add_evidence(
    case_id: int,
    filename: str,
    evidence_type: str,
    file_path: str,
    file_hash: str,
) -> int:
    """
    Attach an evidence item to a case and return its auto-assigned ID.

    Parameters
    ----------
    case_id       : Parent case primary key.
    filename      : Original filename of the evidence file.
    evidence_type : Category string: 'log', 'file', 'browser', or 'email'.
    file_path     : Absolute or relative path to the stored evidence file.
    file_hash     : SHA-256 hex digest of the file contents.

    Returns
    -------
    int
        The id of the newly created evidence row.
    """
    sql = (
        "INSERT INTO evidence (case_id, filename, evidence_type, file_path, file_hash) "
        "VALUES (?, ?, ?, ?, ?)"
    )
    with _get_connection() as conn:
        cursor = conn.execute(sql, (case_id, filename, evidence_type, file_path, file_hash))
        return cursor.lastrowid


def get_evidence_for_case(case_id: int) -> list:
    """
    Return all evidence items associated with a given case.

    Parameters
    ----------
    case_id : Parent case primary key.

    Returns
    -------
    list[dict]
        Each element has keys: id, case_id, filename, evidence_type,
        file_path, file_hash, uploaded_at. Empty list if none exist.
    """
    sql = "SELECT * FROM evidence WHERE case_id = ? ORDER BY uploaded_at ASC;"
    with _get_connection() as conn:
        rows = conn.execute(sql, (case_id,)).fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# FINDINGS DAL
# =============================================================================

def add_finding(
    case_id: int,
    rule_code: str,
    finding: str,
    severity: int,
) -> int:
    """
    Record an AI / rule-engine finding for a case and return its ID.

    Parameters
    ----------
    case_id   : Parent case primary key.
    rule_code : Short rule identifier from the knowledge base, e.g. 'R001'.
    finding   : Human-readable description of the forensic conclusion.
    severity  : Integer risk score 0-100. Higher values indicate greater risk.

    Returns
    -------
    int
        The id of the newly created finding row.
    """
    sql = (
        "INSERT INTO findings (case_id, rule_code, finding, severity) "
        "VALUES (?, ?, ?, ?)"
    )
    with _get_connection() as conn:
        cursor = conn.execute(sql, (case_id, rule_code, finding, severity))
        return cursor.lastrowid


def get_findings_for_case(case_id: int) -> list:
    """
    Return all findings for a given case, ordered by severity descending.

    Parameters
    ----------
    case_id : Parent case primary key.

    Returns
    -------
    list[dict]
        Each element has keys: id, case_id, rule_code, finding,
        severity, created_at. Empty list if none exist.
    """
    sql = (
        "SELECT * FROM findings WHERE case_id = ? "
        "ORDER BY severity DESC, created_at ASC;"
    )
    with _get_connection() as conn:
        rows = conn.execute(sql, (case_id,)).fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# REPORTS DAL
# =============================================================================

def add_report(case_id: int, report_path: str) -> int:
    """
    Register a generated report file path against a case.

    Parameters
    ----------
    case_id     : Parent case primary key.
    report_path : File system path to the generated PDF or text report.

    Returns
    -------
    int
        The id of the newly created report row.
    """
    sql = "INSERT INTO reports (case_id, report_path) VALUES (?, ?);"
    with _get_connection() as conn:
        cursor = conn.execute(sql, (case_id, report_path))
        return cursor.lastrowid


def get_reports_for_case(case_id: int) -> list:
    """
    Return all generated reports associated with a given case.

    Parameters
    ----------
    case_id : Parent case primary key.

    Returns
    -------
    list[dict]
        Each element has keys: id, case_id, report_path, generated_at.
        Empty list if no reports exist.
    """
    sql = "SELECT * FROM reports WHERE case_id = ? ORDER BY generated_at DESC;"
    with _get_connection() as conn:
        rows = conn.execute(sql, (case_id,)).fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# TEST HARNESS
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("FORENSEQUENCE - Database Layer Verification")
    print("=" * 60)

    # Step 1: Initialize schema
    initialize_db()
    print("[OK] Database initialized:", _DB_PATH)
    print()

    # Step 2: Create a sample case with a unique timestamp-based case number.
    # Using a timestamp suffix makes this block idempotent across repeated runs.
    test_case_number = "CASE-TEST-{}".format(int(time.time()))
    case_id = create_case(
        case_number=test_case_number,
        case_name="Corporate Log Breach",
        investigator="Salman",
        description="Initial test case - unauthorized access via compromised credentials.",
    )
    print("[OK] Case created | number: {} | ID: {}".format(test_case_number, case_id))

    # Step 3: Add sample evidence
    evidence_id = add_evidence(
        case_id=case_id,
        filename="system.log",
        evidence_type="log",
        file_path="/tmp/system.log",
        file_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    )
    print("[OK] Evidence added with ID:", evidence_id)

    # Step 4: Add a sample finding
    finding_id = add_finding(
        case_id=case_id,
        rule_code="R001",
        finding=(
            "Suspicious login activity detected: 47 failed authentication attempts "
            "from IP 192.168.1.99 within 60 seconds."
        ),
        severity=20,
    )
    print("[OK] Finding added with ID:", finding_id)

    # Step 5: Query and display results
    print()
    print("-" * 60)
    print("CASE RECORD")
    print("-" * 60)
    case = get_case_by_id(case_id)
    for key, value in case.items():
        print("  {:<16}: {}".format(key, value))

    print()
    print("-" * 60)
    print("EVIDENCE RECORDS")
    print("-" * 60)
    for ev in get_evidence_for_case(case_id):
        for key, value in ev.items():
            print("  {:<16}: {}".format(key, value))
        print()

    print("-" * 60)
    print("FINDING RECORDS")
    print("-" * 60)
    for fd in get_findings_for_case(case_id):
        for key, value in fd.items():
            print("  {:<16}: {}".format(key, value))
        print()

    print("=" * 60)
    print("All database operations completed successfully.")
    print("=" * 60)

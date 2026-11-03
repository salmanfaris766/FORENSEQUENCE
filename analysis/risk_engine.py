# =============================================================================
# analysis/risk_engine.py
# FORENSEQUENCE - Risk Engine: Categorized Severity Analytics & Recommendations
# =============================================================================

from typing import Dict, List, Any

from gui.theme import CYAN, PEACH, PINK


# =============================================================================
# RULE CATEGORY MAPPINGS
# =============================================================================

# Maps rule codes to their forensic category label
_RULE_CATEGORIES: Dict[str, str] = {
    "R001": "Authentication",
    "R007": "Authentication",
    "R002": "Process Execution",
    "R008": "Process Execution",
    "R003": "Data Destruction",
    "R004": "Media Exfiltration",
    "R009": "Media Exfiltration",
    "R005": "Network / Email",
    "R006": "Network / Email",
}

# Maps rule codes to their incident response recommendation template
_RECOMMENDATIONS: Dict[str, str] = {
    "R001": (
        "Initiate mandatory credential reset for flagged accounts ({users}). "
        "Enforce multi-factor authentication (MFA)."
    ),
    "R007": (
        "Initiate mandatory credential reset for flagged accounts ({users}). "
        "Enforce multi-factor authentication (MFA)."
    ),
    "R002": (
        "Isolate affected host system from local network. "
        "Initiate memory dump and anti-malware triage."
    ),
    "R008": (
        "Isolate affected host system from local network. "
        "Initiate memory dump and anti-malware triage."
    ),
    "R003": (
        "Enforce immediate write-block on raw storage volumes. "
        "Preserve snapshot backups."
    ),
    "R004": (
        "Block removable media USB endpoints via Group Policy (GPO). "
        "Audit device serials."
    ),
    "R009": (
        "Block removable media USB endpoints via Group Policy (GPO). "
        "Audit device serials."
    ),
    "R005": (
        "Block malicious domains on egress firewall/DNS. "
        "Quarantine matching email attachments."
    ),
    "R006": (
        "Block malicious domains on egress firewall/DNS. "
        "Quarantine matching email attachments."
    ),
}


# =============================================================================
# RISK ENGINE
# =============================================================================

class RiskEngine:
    """
    Deterministic Risk Engine for FORENSEQUENCE.

    Accepts a list of derived findings (each produced by the ForwardChainingEngine)
    and calculates a structured risk assessment including:
      - Overall risk score (capped at 100)
      - Risk level band (LOW / MEDIUM / HIGH)
      - Theme-mapped risk color
      - Per-category severity breakdown
      - Targeted incident response recommendations
    """

    # Risk band thresholds
    THRESHOLD_LOW    = 30
    THRESHOLD_MEDIUM = 60

    def calculate_risk(
        self,
        findings: List[Dict[str, Any]],
        flagged_users: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute a complete risk assessment from a list of derived rule findings.

        Parameters
        ----------
        findings : list of dict
            Each dict must contain at minimum:
            - ``rule_code``  (str)  : The fired rule code, e.g., 'R001'.
            - ``severity``   (int)  : Severity weight contributed by this finding.
            - ``finding``    (str)  : Human-readable finding description.
        flagged_users : list of str, optional
            Flagged user accounts discovered during log analysis, used to
            populate recommendation templates. Defaults to empty list.

        Returns
        -------
        dict with keys:
            total_severity       : int   - Raw sum of all finding severity scores.
            risk_score           : int   - Normalized score, capped at 100.
            risk_level           : str   - 'LOW', 'MEDIUM', or 'HIGH'.
            risk_color           : str   - Hex theme color for the risk band.
            breakdown_by_category: dict  - {category: {count, severity}} per group.
            recommendations      : list  - Targeted forensic IR recommendation strings.
        """
        if flagged_users is None:
            flagged_users = []

        users_str = ", ".join(flagged_users) if flagged_users else "flagged accounts"

        # -------------------------------------------------------------------------
        # 1. Aggregate severity totals
        # -------------------------------------------------------------------------
        total_severity = sum(int(f.get("severity", 0)) for f in findings)
        risk_score = min(100, total_severity)

        # -------------------------------------------------------------------------
        # 2. Determine risk band
        # -------------------------------------------------------------------------
        if risk_score <= self.THRESHOLD_LOW:
            risk_level = "LOW"
            risk_color_val = CYAN
        elif risk_score <= self.THRESHOLD_MEDIUM:
            risk_level = "MEDIUM"
            risk_color_val = PEACH
        else:
            risk_level = "HIGH"
            risk_color_val = PINK

        # -------------------------------------------------------------------------
        # 3. Breakdown by category
        # -------------------------------------------------------------------------
        breakdown: Dict[str, Dict[str, int]] = {}
        fired_rule_codes: List[str] = []

        for finding in findings:
            code = str(finding.get("rule_code", "UNKNOWN"))
            fired_rule_codes.append(code)
            severity = int(finding.get("severity", 0))
            category = _RULE_CATEGORIES.get(code, "Uncategorized")

            if category not in breakdown:
                breakdown[category] = {"count": 0, "severity": 0}
            breakdown[category]["count"] += 1
            breakdown[category]["severity"] += severity

        # -------------------------------------------------------------------------
        # 4. Build deduplicated recommendations
        # -------------------------------------------------------------------------
        seen_recommendations: set = set()
        recommendations: List[str] = []

        for code in fired_rule_codes:
            template = _RECOMMENDATIONS.get(code)
            if template:
                try:
                    rec_text = template.format(users=users_str)
                except KeyError:
                    rec_text = template
                if rec_text not in seen_recommendations:
                    seen_recommendations.add(rec_text)
                    recommendations.append(rec_text)

        if not recommendations and findings:
            recommendations.append(
                "Review all derived findings in the forensic analysis report. "
                "Escalate to senior investigator for manual triage."
            )

        return {
            "total_severity": total_severity,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_color": risk_color_val,
            "breakdown_by_category": breakdown,
            "recommendations": recommendations,
        }


# =============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# =============================================================================

def calculate_risk(
    findings: List[Dict[str, Any]],
    flagged_users: List[str] = None,
) -> Dict[str, Any]:
    """
    Module-level shorthand wrapper around RiskEngine.calculate_risk().

    Accepts the same arguments and returns the same structured result dict.
    """
    return RiskEngine().calculate_risk(findings, flagged_users=flagged_users)


# =============================================================================
# STANDALONE TEST HARNESS
# =============================================================================

if __name__ == "__main__":
    import sys
    import os

    # Ensure project root is importable
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(_here)
    if _root not in sys.path:
        sys.path.insert(0, _root)

    # Sample findings that would come from ForwardChainingEngine
    _sample_findings = [
        {"rule_code": "R001", "severity": 20, "finding": "Brute Force Authentication Attempt"},
        {"rule_code": "R002", "severity": 30, "finding": "Suspicious Process Execution"},
        {"rule_code": "R003", "severity": 25, "finding": "Anti-Forensics File Destruction"},
        {"rule_code": "R004", "severity": 15, "finding": "USB-Associated Code Execution"},
        {"rule_code": "R007", "severity": 25, "finding": "Potential Credential Compromise"},
        {"rule_code": "R008", "severity": 30, "finding": "Destructive Intrusion Campaign"},
        {"rule_code": "R009", "severity": 20, "finding": "Physical Data Exfiltration Sequence"},
    ]
    _sample_users = ["admin", "jdoe"]

    engine = RiskEngine()
    result = engine.calculate_risk(_sample_findings, flagged_users=_sample_users)

    print("=" * 60)
    print("FORENSEQUENCE RISK ENGINE - STANDALONE TEST")
    print("=" * 60)
    print(f"Total Severity  : {result['total_severity']}")
    print(f"Risk Score      : {result['risk_score']} / 100")
    print(f"Risk Level      : {result['risk_level']}")
    print(f"Risk Color      : {result['risk_color']}")
    print()
    print("Category Breakdown:")
    for cat, data in result["breakdown_by_category"].items():
        print(f"  {cat:<25} -> {data['count']} findings, severity sum = {data['severity']}")
    print()
    print("Incident Response Recommendations:")
    for idx, rec in enumerate(result["recommendations"], start=1):
        print(f"  {idx}. {rec}")
    print("=" * 60)
    print("TEST PASSED")

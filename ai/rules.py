# =============================================================================
# ai/rules.py
# FORENSEQUENCE - Knowledge Base: Forensic Rules & Propositional Logic
# =============================================================================

from typing import Callable, Dict, Any, List


class Rule:
    """
    Representation of an Expert System Production Rule (IF Condition THEN Conclusion).

    Attributes
    ----------
    rule_code        : Unique rule identifier, e.g., 'R001'.
    name             : Short descriptive title of the forensic pattern.
    condition        : Callable evaluating facts dict -> bool.
    conclusion       : Derived forensic fact token, e.g., 'suspicious_login_activity'.
    description      : Human-readable explanation of the forensic conclusion.
    severity         : Risk weight (0-100) contributed to overall threat index.
    explain_template : String template formatted with fact values for explainability.
    """

    def __init__(
        self,
        rule_code: str,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        conclusion: str,
        description: str,
        severity: int,
        explain_template: str,
    ):
        self.rule_code = rule_code
        self.name = name
        self.condition = condition
        self.conclusion = conclusion
        self.description = description
        self.severity = int(severity)
        self.explain_template = explain_template

    def evaluate(self, facts: Dict[str, Any]) -> bool:
        """Evaluate rule condition against current working memory facts."""
        try:
            return bool(self.condition(facts))
        except Exception:
            return False

    def explain(self, facts: Dict[str, Any]) -> str:
        """Generate human-readable explanation tracing back to exact fact values."""
        try:
            safe_facts = {
                "failed_logins": facts.get("failed_logins", 0),
                "successful_logins": facts.get("successful_logins", 0),
                "executable_events": facts.get("executable_events", 0),
                "deleted_files": facts.get("deleted_files", 0),
                "usb_connections": facts.get("usb_connections", 0),
                "suspicious_domains": facts.get("suspicious_domains", 0),
                "unknown_sender": facts.get("unknown_sender", False),
                "executable_attachment": facts.get("executable_attachment", False),
                "ip_addresses": ", ".join(facts.get("ip_addresses", [])) or "None",
                "users_flagged": ", ".join(facts.get("users_flagged", [])) or "None",
            }
            safe_facts.update(facts)
            return self.explain_template.format(**safe_facts)
        except Exception:
            return self.description


# =============================================================================
# DEFAULT FORENSIC KNOWLEDGE BASE RULES
# =============================================================================

DEFAULT_RULES: List[Rule] = [
    # R001: Brute Force Authentication
    Rule(
        rule_code="R001",
        name="Brute Force Authentication Attempt",
        condition=lambda facts: facts.get("failed_logins", 0) > 5,
        conclusion="suspicious_login_activity",
        description="Multiple failed login attempts detected exceeding threshold.",
        severity=20,
        explain_template="Multiple failed login attempts detected ({failed_logins} > threshold 5).",
    ),

    # R002: Unusual Process Creation
    Rule(
        rule_code="R002",
        name="Suspicious Process Execution",
        condition=lambda facts: facts.get("executable_events", 0) > 3,
        conclusion="possible_malware",
        description="Unusual volume of executable or process creation events detected.",
        severity=30,
        explain_template="Unusual volume of executable/process creation events detected ({executable_events} > threshold 3).",
    ),

    # R003: Mass File Deletion / Anti-Forensics
    Rule(
        rule_code="R003",
        name="Anti-Forensics File Destruction",
        condition=lambda facts: facts.get("deleted_files", 0) > 10,
        conclusion="possible_data_wiping",
        description="Mass file deletion or anti-forensic log wiping activity detected.",
        severity=25,
        explain_template="Mass file deletion activity detected ({deleted_files} > threshold 10).",
    ),

    # R004: USB Media Execution (Compound Condition)
    Rule(
        rule_code="R004",
        name="USB-Associated Code Execution",
        condition=lambda facts: facts.get("usb_connections", 0) > 0 and facts.get("executable_events", 0) > 0,
        conclusion="suspicious_usb_activity",
        description="Process launch coincided with external USB media connection.",
        severity=15,
        explain_template="Process launch coincided with USB media attachment ({usb_connections} USB events, {executable_events} process launches).",
    ),

    # R005: Suspicious Web Domain Communication
    Rule(
        rule_code="R005",
        name="Suspicious Domain Communication",
        condition=lambda facts: facts.get("suspicious_domains", 0) > 0,
        conclusion="possible_phishing",
        description="Navigation or beaconing to flagged high-risk web domains detected.",
        severity=25,
        explain_template="Navigation to flagged or suspicious web domains detected ({suspicious_domains} domain hits).",
    ),

    # R006: Untrusted Executable Email Attachment (Compound Condition)
    Rule(
        rule_code="R006",
        name="Untrusted Executable Email Attachment",
        condition=lambda facts: bool(facts.get("unknown_sender")) and bool(facts.get("executable_attachment")),
        conclusion="malicious_email",
        description="Inbound email from unknown sender containing executable attachment.",
        severity=30,
        explain_template="Inbound email from unknown sender containing executable attachment.",
    ),

    # R007: Credential Compromise Sequence (Compound Condition)
    Rule(
        rule_code="R007",
        name="Potential Credential Compromise",
        condition=lambda facts: (
            facts.get("failed_logins", 0) > 0
            and facts.get("successful_logins", 0) > 0
            and len(facts.get("ip_addresses", [])) > 0
        ),
        conclusion="potential_credential_compromise",
        description="Failed authentication attempts followed by successful logon from flagged IP addresses.",
        severity=25,
        explain_template="Failed authentication attempts followed by successful logon from flagged IP addresses ({ip_addresses}).",
    ),

    # R008: Chained Multi-Step Rule: Destructive Cyber Intrusion Campaign
    Rule(
        rule_code="R008",
        name="Destructive Intrusion Campaign",
        condition=lambda facts: bool(facts.get("possible_malware")) and bool(facts.get("possible_data_wiping")),
        conclusion="destructive_intrusion_campaign",
        description="Coordinated malware execution combined with anti-forensic data wiping.",
        severity=30,
        explain_template="Forward chaining inferred a coordinated destructive intrusion combining malware execution and anti-forensic data destruction.",
    ),

    # R009: Chained Multi-Step Rule: Physical Exfiltration Sequence
    Rule(
        rule_code="R009",
        name="Physical Data Exfiltration Sequence",
        condition=lambda facts: bool(facts.get("suspicious_login_activity")) and bool(facts.get("suspicious_usb_activity")),
        conclusion="insider_or_physical_exfiltration",
        description="Unauthorized login followed by USB media attachment and code execution.",
        severity=20,
        explain_template="Forward chaining inferred an exfiltration pattern: unauthorized authentication followed by USB media code execution.",
    ),
]


def get_all_rules() -> List[Rule]:
    """Return a copy of the default forensic production rules."""
    return list(DEFAULT_RULES)

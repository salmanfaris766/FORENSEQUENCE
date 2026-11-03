# =============================================================================
# ai/rule_engine.py
# FORENSEQUENCE - Deterministic Forward Chaining Inference Engine
# =============================================================================

import copy
import os
import sys
from typing import List, Dict, Any, Optional, Set

# Ensure project root is on sys.path for direct script execution
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from ai.rules import Rule, get_all_rules
except ImportError:
    from rules import Rule, get_all_rules


class ForwardChainingEngine:
    """
    Classical Expert System Forward Chaining Inference Engine.

    Executes data-driven propositional deduction over input forensic facts:
    1. Loads facts into working memory.
    2. Repeatedly matches rule antecedents (IF condition) against working memory.
    3. Asserts rule consequents (THEN conclusion) as new derived facts into working memory.
    4. Enables subsequent iterations to fire compound rules conditioned on derived facts.
    5. Terminates deterministically when a fixpoint is reached (no further rules fire).
    6. Produces a full audit trail (reasoning trace) detailing every step of deduction.
    """

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules: List[Rule] = list(rules) if rules is not None else get_all_rules()

    def evaluate(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute forward chaining inference over the provided facts dictionary.

        Parameters
        ----------
        facts : Dict[str, Any]
            Extracted forensic evidence facts (e.g. from LogAnalyzer or other analyzers).

        Returns
        -------
        Dict[str, Any]
            Structured inference result containing findings, derived facts, risk score,
            risk level, and step-by-step reasoning trace.
        """
        working_facts: Dict[str, Any] = copy.deepcopy(facts)
        fired_rules: Set[str] = set()
        derived_findings: List[Dict[str, Any]] = []
        reasoning_trace: List[Dict[str, Any]] = []

        iteration = 1
        fixpoint_reached = False

        while not fixpoint_reached:
            rule_fired_in_iteration = False

            for rule in self.rules:
                if rule.rule_code in fired_rules:
                    continue

                if rule.evaluate(working_facts):
                    fired_rules.add(rule.rule_code)
                    rule_fired_in_iteration = True

                    explanation = rule.explain(working_facts)

                    # 1. Record derived finding
                    finding_record = {
                        "rule_code": rule.rule_code,
                        "name": rule.name,
                        "finding": rule.conclusion,
                        "severity": rule.severity,
                        "description": rule.description,
                        "explanation": explanation,
                        "iteration": iteration,
                    }
                    derived_findings.append(finding_record)

                    # 2. Assert derived fact into working memory (enables forward chaining)
                    working_facts[rule.conclusion] = True

                    # 3. Log step to reasoning trace
                    trace_step = {
                        "iteration": iteration,
                        "rule_code": rule.rule_code,
                        "name": rule.name,
                        "condition_met": True,
                        "derived_fact": rule.conclusion,
                        "severity_added": rule.severity,
                        "explanation": explanation,
                    }
                    reasoning_trace.append(trace_step)

            if rule_fired_in_iteration:
                iteration += 1
            else:
                fixpoint_reached = True

        # Calculate Threat & Risk Metrics
        sum_severity = sum(f["severity"] for f in derived_findings)
        risk_score = min(100, sum_severity)

        if risk_score <= 30:
            risk_level = "LOW"
        elif risk_score <= 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "findings": derived_findings,
            "derived_facts": working_facts,
            "total_severity": sum_severity,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "fired_rule_codes": sorted(list(fired_rules)),
            "reasoning_trace": reasoning_trace,
            "rules_evaluated": len(self.rules),
            "rules_fired_count": len(derived_findings),
            "iterations_to_fixpoint": iteration - 1 if iteration > 1 else 1,
        }


# =============================================================================
# STANDALONE TEST HARNESS
# =============================================================================

if __name__ == "__main__":
    # Ensure project root is in sys.path for direct script execution
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from analyzers.log_analyzer import parse_log_file

    sample_log = os.path.join(project_root, "sample_evidence", "system.log")
    if not os.path.exists(sample_log):
        sample_log = os.path.join("sample_evidence", "system.log")

    print("=" * 75)
    print("FORENSEQUENCE - FORWARD CHAINING INFERENCE ENGINE TEST HARNESS")
    print("=" * 75)
    print(f"Evidence Source: {os.path.abspath(sample_log)}")

    if not os.path.exists(sample_log):
        print(f"[ERROR] Sample log evidence not found at {sample_log}")
        sys.exit(1)

    # Step 1: Extract deterministic facts from log evidence
    print("\n[STEP 1] Extracting deterministic facts via LogAnalyzer...")
    extracted_facts = parse_log_file(sample_log)
    print(f"  - Total Lines       : {extracted_facts['total_lines']}")
    print(f"  - Failed Logins     : {extracted_facts['failed_logins']}")
    print(f"  - Successful Logins : {extracted_facts['successful_logins']}")
    print(f"  - USB Connections   : {extracted_facts['usb_connections']}")
    print(f"  - Executable Events : {extracted_facts['executable_events']}")
    print(f"  - Deleted Files     : {extracted_facts['deleted_files']}")
    print(f"  - Flagged IPs       : {', '.join(extracted_facts['ip_addresses'])}")
    print(f"  - Flagged Users     : {', '.join(extracted_facts['users_flagged'])}")

    # Step 2: Initialize Knowledge Base and Forward Chaining Engine
    print("\n[STEP 2] Initializing Knowledge Base and Forward Chaining Engine...")
    engine = ForwardChainingEngine()
    print(f"  - Rules Loaded      : {len(engine.rules)} production rules")

    # Step 3: Run Forward Chaining Inference
    print("\n[STEP 3] Running Forward Chaining Inference over Working Memory...")
    result = engine.evaluate(extracted_facts)

    # Step 4: Display Reasoning Trace (Step-by-step proof log)
    print("\n" + "=" * 75)
    print("FORWARD CHAINING REASONING TRACE (STEP-BY-STEP PROOF LOG)")
    print("=" * 75)
    for step in result["reasoning_trace"]:
        it = step["iteration"]
        code = step["rule_code"]
        name = step["name"]
        fact = step["derived_fact"]
        sev = step["severity_added"]
        expl = step["explanation"]
        print(f"[ITERATION {it}] Rule {code} ({name}) FIRED (+{sev} pts)")
        print(f"             --> Asserted Fact : {fact} = True")
        print(f"             --> Explanation   : {expl}")
        print()

    # Step 5: Summary of Derived Findings
    print("=" * 75)
    print(f"DERIVED FORENSIC FINDINGS ({result['rules_fired_count']} findings)")
    print("=" * 75)
    for i, finding in enumerate(result["findings"], start=1):
        print(f"[{i:02d}] {finding['rule_code']} - {finding['name']}")
        print(f"     Token       : {finding['finding']}")
        print(f"     Severity    : {finding['severity']}")
        print(f"     Explanation : {finding['explanation']}")
        print()

    # Step 6: Risk Assessment
    print("=" * 75)
    print("FINAL RISK ASSESSMENT")
    print("=" * 75)
    print(f"  - Total Severity Score  : {result['total_severity']}")
    print(f"  - Normalized Risk Score : {result['risk_score']} / 100")
    print(f"  - Threat Risk Level     : {result['risk_level']}")
    print(f"  - Iterations to Fixpoint: {result['iterations_to_fixpoint']}")
    print("\n[OK] Forward Chaining inference executed successfully.")

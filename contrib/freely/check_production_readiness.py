#!/usr/bin/env python3
"""Fail-closed validator for FREELY production-readiness evidence.

A PASS is accepted only with exact-release-commit evidence, a successful
workflow, named tests, reviewer, review date and zero open findings.
This tool validates recorded evidence; it does not itself execute tests,
approve protocol parameters, perform an audit, or authorize launch.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

GATE_IDS = {f"G{i}" for i in range(9)}
VALID_STATES = {"NOT_STARTED", "IN_PROGRESS", "BLOCKED", "PASS"}
VALID_EVIDENCE_TYPES = {"unit", "functional", "integration", "operational", "independent_audit"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["manifest root must be a JSON object"]
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
        errors.append("schema_version must be integer 1")
    if data.get("project") != "FREELY":
        errors.append("project must be FREELY")

    candidate = data.get("release_candidate_sha")
    if candidate is not None and (not isinstance(candidate, str) or not SHA_RE.fullmatch(candidate)):
        errors.append("release_candidate_sha must be null or a lowercase 40-character commit SHA")

    gates = data.get("gates")
    if not isinstance(gates, list):
        errors.append("gates must be an array")
        return errors
    ids = [g.get("id") for g in gates if isinstance(g, dict)]
    if set(ids) != GATE_IDS or len(ids) != 9:
        errors.append("gates must contain each unique gate G0 through G8 exactly once")

    for gate in gates:
        if not isinstance(gate, dict):
            errors.append("each gate must be a JSON object")
            continue
        gate_id = gate.get("id")
        if gate_id not in GATE_IDS:
            errors.append(f"unknown gate id: {gate_id!r}")
            continue
        state = gate.get("status")
        if state not in VALID_STATES:
            errors.append(f"{gate_id}: invalid status")
            continue
        if state != "PASS":
            continue

        evidence = gate.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{gate_id}: PASS requires an evidence object")
            continue

        if not isinstance(candidate, str) or not SHA_RE.fullmatch(candidate):
            errors.append(f"{gate_id}: PASS requires a valid release_candidate_sha")
        if evidence.get("commit_sha") != candidate:
            errors.append(f"{gate_id}: evidence commit_sha must equal release_candidate_sha")
        workflow_url = evidence.get("workflow_url")
        if not isinstance(workflow_url, str) or not workflow_url.startswith("https://"):
            errors.append(f"{gate_id}: PASS requires an HTTPS workflow_url")
        if evidence.get("workflow_conclusion") != "success":
            errors.append(f"{gate_id}: PASS requires workflow_conclusion=success")
        tests = evidence.get("tests")
        if not isinstance(tests, list) or not tests or any(not isinstance(x, str) or not x.strip() for x in tests):
            errors.append(f"{gate_id}: PASS requires a non-empty list of named tests")
        if evidence.get("evidence_type") not in VALID_EVIDENCE_TYPES:
            errors.append(f"{gate_id}: invalid evidence_type")
        if not isinstance(evidence.get("reviewer"), str) or not evidence["reviewer"].strip():
            errors.append(f"{gate_id}: PASS requires a named reviewer")
        reviewed_at = evidence.get("reviewed_at")
        try:
            date.fromisoformat(reviewed_at)
        except (TypeError, ValueError):
            errors.append(f"{gate_id}: reviewed_at must be an ISO date (YYYY-MM-DD)")
        findings = evidence.get("open_findings")
        if type(findings) is not int or findings != 0:
            errors.append(f"{gate_id}: PASS requires open_findings=0")

        if gate_id == "G0" and gate.get("owner_approvals") is not True:
            errors.append("G0: PASS requires explicit owner_approvals=true")
        if gate_id == "G8":
            if gate.get("independent_audit") is not True:
                errors.append("G8: PASS requires independent_audit=true")
            if gate.get("launch_authorized") is not True:
                errors.append("G8: PASS requires separate launch_authorized=true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("production-readiness.json"),
    )
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read production evidence manifest: {exc}", file=sys.stderr)
        return 2

    errors = validate(data)
    if errors:
        print(f"FREELY production evidence: INVALID ({len(errors)} issue(s))")
        for error in errors:
            print(f" - {error}")
        return 2

    gates = data["gates"]
    passed = sum(g["status"] == "PASS" for g in gates)
    blocked = [g for g in gates if g["status"] != "PASS"]
    print(f"FREELY production readiness: {'PASS' if not blocked else 'BLOCKED'}")
    print(f"Evidence gates passed: {passed}/9")
    for gate in blocked:
        print(f" - {gate['id']} {gate.get('name', '')}: {gate['status']}")
    if blocked:
        return 1
    print("All evidence gates have recorded exact-commit validation.")
    print("This tool does not itself authorize launch; owner launch authorization remains separate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

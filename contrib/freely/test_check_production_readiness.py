import copy
import json
import unittest
from pathlib import Path

from check_production_readiness import validate


TEMPLATE = json.loads(Path(__file__).with_name("production-readiness.json").read_text(encoding="utf-8"))
CANDIDATE = "a" * 40


def valid_evidence():
    return {
        "commit_sha": CANDIDATE,
        "workflow_url": "https://github.com/example/repo/actions/runs/123",
        "workflow_conclusion": "success",
        "tests": ["unit_test_example"],
        "evidence_type": "unit",
        "reviewer": "independent reviewer",
        "reviewed_at": "2026-11-18",
        "open_findings": 0,
    }


def fixture():
    data = copy.deepcopy(TEMPLATE)
    data["release_candidate_sha"] = CANDIDATE
    return data


class ProductionReadinessTests(unittest.TestCase):
    def test_owner_template_is_valid_but_blocked(self):
        self.assertEqual(validate(TEMPLATE), [])

    def test_empty_evidence_ledger_is_not_a_production_pass(self):
        data = fixture()
        self.assertEqual(validate(data), [])
        self.assertTrue(all(gate["status"] != "PASS" for gate in data["gates"]))

    def test_accepts_gate_pass_with_exact_commit_evidence(self):
        data = fixture()
        gate = next(g for g in data["gates"] if g["id"] == "G1")
        gate["status"] = "PASS"
        gate["evidence"] = valid_evidence()
        self.assertEqual(validate(data), [])

    def test_rejects_pass_without_release_candidate_sha(self):
        data = fixture()
        data["release_candidate_sha"] = None
        gate = next(g for g in data["gates"] if g["id"] == "G1")
        gate["status"] = "PASS"
        gate["evidence"] = valid_evidence()
        self.assertTrue(any("requires a valid release_candidate_sha" in e for e in validate(data)))

    def test_rejects_evidence_from_different_commit(self):
        data = fixture()
        gate = next(g for g in data["gates"] if g["id"] == "G1")
        gate["status"] = "PASS"
        evidence = valid_evidence()
        evidence["commit_sha"] = "b" * 40
        gate["evidence"] = evidence
        self.assertTrue(any("must equal release_candidate_sha" in e for e in validate(data)))

    def test_rejects_queued_or_failed_workflow(self):
        data = fixture()
        gate = next(g for g in data["gates"] if g["id"] == "G1")
        gate["status"] = "PASS"
        evidence = valid_evidence()
        evidence["workflow_conclusion"] = "queued"
        gate["evidence"] = evidence
        self.assertTrue(any("workflow_conclusion=success" in e for e in validate(data)))

    def test_rejects_pass_without_named_tests_reviewer_or_review_date(self):
        data = fixture()
        gate = next(g for g in data["gates"] if g["id"] == "G1")
        gate["status"] = "PASS"
        evidence = valid_evidence()
        evidence.update({"tests": [], "reviewer": "", "reviewed_at": "yesterday"})
        gate["evidence"] = evidence
        errors = validate(data)
        self.assertTrue(any("named tests" in e for e in errors))
        self.assertTrue(any("named reviewer" in e for e in errors))
        self.assertTrue(any("ISO date" in e for e in errors))

    def test_rejects_pass_with_open_findings(self):
        data = fixture()
        gate = next(g for g in data["gates"] if g["id"] == "G1")
        gate["status"] = "PASS"
        evidence = valid_evidence()
        evidence["open_findings"] = 1
        gate["evidence"] = evidence
        self.assertTrue(any("open_findings=0" in e for e in validate(data)))

    def test_protocol_gate_requires_owner_approval(self):
        data = fixture()
        gate = next(g for g in data["gates"] if g["id"] == "G0")
        gate["status"] = "PASS"
        gate["evidence"] = valid_evidence()
        self.assertTrue(any("owner_approvals=true" in e for e in validate(data)))
        gate["owner_approvals"] = True
        self.assertEqual(validate(data), [])

    def test_final_gate_requires_independent_audit_and_separate_launch_authorization(self):
        data = fixture()
        gate = next(g for g in data["gates"] if g["id"] == "G8")
        gate["status"] = "PASS"
        evidence = valid_evidence()
        evidence["evidence_type"] = "independent_audit"
        gate["evidence"] = evidence
        errors = validate(data)
        self.assertTrue(any("independent_audit=true" in e for e in errors))
        self.assertTrue(any("launch_authorized=true" in e for e in errors))
        gate["independent_audit"] = True
        gate["launch_authorized"] = True
        self.assertEqual(validate(data), [])

    def test_requires_all_nine_unique_gate_ids(self):
        data = fixture()
        data["gates"].pop()
        self.assertTrue(any("each unique gate G0 through G8" in e for e in validate(data)))

    def test_rejects_invalid_status_and_noncanonical_sha(self):
        data = fixture()
        data["release_candidate_sha"] = "A" * 40
        data["gates"][0]["status"] = "READY"
        errors = validate(data)
        self.assertTrue(any("lowercase 40-character commit SHA" in e for e in errors))
        self.assertTrue(any("invalid status" in e for e in errors))


if __name__ == "__main__":
    unittest.main()

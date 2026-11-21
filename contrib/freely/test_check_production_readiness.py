import copy
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from check_production_readiness import validate, main


MANIFEST_PATH = Path(__file__).with_name("production-readiness.json")
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
RELEASE_SHA = "a" * 40


def pass_evidence():
    return {
        "commit_sha": RELEASE_SHA,
        "workflow_url": "https://github.com/example/freely/actions/runs/1",
        "workflow_conclusion": "success",
        "tests": ["consensus-tests", "functional-tests"],
        "evidence_type": "unit",
        "reviewer": "independent-reviewer",
        "reviewed_at": "2026-11-19",
        "open_findings": 0,
    }


def mark_pass(data, gate_id):
    data["release_candidate_sha"] = RELEASE_SHA
    gate = next(item for item in data["gates"] if item["id"] == gate_id)
    gate["status"] = "PASS"
    gate["evidence"] = pass_evidence()
    if gate_id == "G0":
        gate["owner_approvals"] = True
    if gate_id == "G8":
        gate["independent_audit"] = True
        gate["launch_authorized"] = True
    return gate


class ProductionReadinessTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(MANIFEST)

    def test_approved_template_is_valid_but_not_ready(self):
        self.assertEqual(validate(self.data), [])
        self.assertTrue(all(gate["status"] != "PASS" for gate in self.data["gates"]))

    def test_requires_exact_gate_set(self):
        self.data["gates"].pop()
        self.assertTrue(any("G0 through G8 exactly once" in item for item in validate(self.data)))

    def test_rejects_duplicate_gate_id(self):
        self.data["gates"].append(copy.deepcopy(self.data["gates"][0]))
        self.assertTrue(any("G0 through G8 exactly once" in item for item in validate(self.data)))

    def test_rejects_unknown_gate_id(self):
        self.data["gates"][0]["id"] = "G9"
        self.assertTrue(any("unknown gate id" in item for item in validate(self.data)))

    def test_rejects_invalid_gate_status(self):
        self.data["gates"][0]["status"] = "SUCCESS"
        self.assertTrue(any("invalid status" in item for item in validate(self.data)))

    def test_pass_requires_evidence_object(self):
        gate = self.data["gates"][1]
        gate["status"] = "PASS"
        gate["evidence"] = None
        self.assertTrue(any("PASS requires an evidence object" in item for item in validate(self.data)))

    def test_pass_requires_valid_release_sha(self):
        gate = mark_pass(self.data, "G1")
        self.data["release_candidate_sha"] = "not-a-commit"
        self.assertTrue(any("release_candidate_sha must be null or" in item for item in validate(self.data)))

    def test_pass_requires_evidence_for_exact_release_commit(self):
        gate = mark_pass(self.data, "G1")
        gate["evidence"]["commit_sha"] = "b" * 40
        self.assertTrue(any("evidence commit_sha must equal release_candidate_sha" in item for item in validate(self.data)))

    def test_pass_requires_successful_workflow_and_https_url(self):
        gate = mark_pass(self.data, "G1")
        gate["evidence"]["workflow_conclusion"] = "cancelled"
        gate["evidence"]["workflow_url"] = "http://example.invalid/run"
        errors = validate(self.data)
        self.assertTrue(any("workflow_conclusion=success" in item for item in errors))
        self.assertTrue(any("HTTPS workflow_url" in item for item in errors))

    def test_pass_requires_named_tests(self):
        gate = mark_pass(self.data, "G1")
        gate["evidence"]["tests"] = ["unit-tests", " "]
        self.assertTrue(any("non-empty list of named tests" in item for item in validate(self.data)))

    def test_pass_requires_supported_evidence_type(self):
        gate = mark_pass(self.data, "G1")
        gate["evidence"]["evidence_type"] = "self-attestation"
        self.assertTrue(any("invalid evidence_type" in item for item in validate(self.data)))

    def test_pass_requires_reviewer_and_iso_date(self):
        gate = mark_pass(self.data, "G1")
        gate["evidence"]["reviewer"] = " "
        gate["evidence"]["reviewed_at"] = "19/11/2026"
        errors = validate(self.data)
        self.assertTrue(any("named reviewer" in item for item in errors))
        self.assertTrue(any("ISO date" in item for item in errors))

    def test_pass_requires_zero_open_findings(self):
        gate = mark_pass(self.data, "G1")
        gate["evidence"]["open_findings"] = True
        self.assertTrue(any("open_findings=0" in item for item in validate(self.data)))

    def test_g0_pass_requires_owner_approval(self):
        gate = mark_pass(self.data, "G0")
        gate["owner_approvals"] = False
        self.assertTrue(any("G0: PASS requires explicit owner_approvals=true" in item for item in validate(self.data)))

    def test_g8_pass_requires_independent_audit_and_launch_approval(self):
        gate = mark_pass(self.data, "G8")
        gate["independent_audit"] = False
        gate["launch_authorized"] = False
        errors = validate(self.data)
        self.assertTrue(any("G8: PASS requires independent_audit=true" in item for item in errors))
        self.assertTrue(any("G8: PASS requires separate launch_authorized=true" in item for item in errors))

    def test_main_returns_blocked_for_valid_incomplete_template(self):
        output = StringIO()
        with patch("sys.argv", ["check_production_readiness.py", "--manifest", str(MANIFEST_PATH)]):
            with redirect_stdout(output):
                self.assertEqual(main(), 1)
        self.assertIn("FREELY production readiness: BLOCKED", output.getvalue())

    def test_main_returns_invalid_for_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            bad_manifest = Path(directory) / "bad.json"
            bad_manifest.write_text("{ invalid json", encoding="utf-8")
            with patch("sys.argv", ["check_production_readiness.py", "--manifest", str(bad_manifest)]):
                self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()

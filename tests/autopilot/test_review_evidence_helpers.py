"""Packaged advisory AP00012 evidence checking matches the independent oracle."""

from __future__ import annotations

import copy
import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import test_contract as contract
from test_contract import ROOT
from test_contract_semantics import validate_review

PACKAGE = ROOT / "plugins" / "autopilot"
SCRIPTS = PACKAGE / "scripts"
OK = {
    "schema_version": 1,
    "ok": True,
    "checks": "local-contract-v1",
    "evidence_valid": True,
    "controller_required": True,
}
FIXTURES = contract.load(contract.FIXTURES_FILE)
CASES = {case["name"]: case for case in FIXTURES["cases"]}
V1 = FIXTURES["policies"]["v1"]
V1_ALT = FIXTURES["policies"]["v1-alt"]


def load_helper(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


def invalid(defects: set[str]) -> dict[str, Any]:
    return {"schema_version": 1, "ok": False, "error": "invalid-evidence", "defects": sorted(defects)}


def mapped(expect: dict[str, Any]) -> dict[str, Any]:
    """Outer outcome mapping from the AP00012 oracle token to the helper report."""
    return dict(OK) if expect["outcome"] == "accepted" else invalid(set(expect["defects"]))


def clean() -> tuple[dict[str, Any], dict[str, Any]]:
    base = CASES["full-clean"]
    return copy.deepcopy(base["expected_context"]), copy.deepcopy(base["input"])


def result(evidence: dict[str, Any], job: str) -> dict[str, Any]:
    return next(r for r in evidence["reviewer_results"] if r["job_ref"] == job)


def redigest_results(evidence: dict[str, Any]) -> None:
    for row in evidence["reviewer_results"]:
        row["source_binding_digest"] = contract.digest(evidence["source_bindings"])


def with_findings(evidence: dict[str, Any]) -> dict[str, Any]:
    alice = result(evidence, "alice")
    alice["outcome"] = "findings"
    alice["finding_ids"] = ["F1", "F2"]
    evidence["findings"] = [
        {"finding_id": "F1", "result_id": "alice-1", "severity": "high", "title": "Wrong default",
         "file": "src/a.py", "task_ref": None, "evidence": "line 3"},
        {"finding_id": "F2", "result_id": "alice-1", "severity": "low", "title": "Typo",
         "file": None, "task_ref": "T1", "evidence": "doc"},
    ]
    evidence["groups"] = [{"group_id": "G1", "finding_ids": ["F1", "F2"], "rationale": "same file"}]
    return evidence


class EvidenceCase(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_helper("review_evidence")

    def check(self, policy: Any, context: Any, evidence: Any) -> dict[str, Any]:
        report = self.module.check_evidence(policy, context, evidence)
        self.assertEqual(report, mapped(validate_review(policy, context, evidence)))
        return report


class LoadPolicyTest(EvidenceCase):
    def test_load_policy_returns_packaged_policy_independent_of_cwd(self) -> None:
        packaged = contract.load(contract.POLICY_FILE)
        self.assertEqual(self.module.load_policy(), packaged)
        with tempfile.TemporaryDirectory() as tmp:
            decoy = Path(tmp) / "plugins" / "autopilot" / "contracts"
            decoy.mkdir(parents=True)
            (decoy / "review-policy-v1.json").write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                loaded = self.module.load_policy()
            finally:
                os.chdir(previous)
        self.assertEqual(loaded, packaged)
        self.assertEqual(loaded["policy_digest"], V1["policy_digest"])
        self.assertNotEqual(loaded["policy_digest"], V1_ALT["policy_digest"])

    def test_packaged_policy_accepts_clean_evidence_and_rejects_stale_prd(self) -> None:
        context, evidence = clean()
        policy = self.module.load_policy()
        self.assertEqual(self.check(policy, context, evidence), OK)
        evidence["source_bindings"]["prd_sha256"] = "1" * 63 + "0"
        self.assertEqual(self.check(policy, context, evidence), invalid({"source_binding_mismatch"}))


class FixtureParityTest(EvidenceCase):
    def test_all_55_fixtures_match_their_mapped_defect_sets(self) -> None:
        self.assertEqual(len(FIXTURES["cases"]), 55)
        outcomes = set()
        for case in FIXTURES["cases"]:
            with self.subTest(case=case["name"]):
                policy = FIXTURES["policies"][case["policy"]]
                report = self.module.check_evidence(policy, case["expected_context"], case["input"])
                self.assertEqual(report, mapped(case["expect"]))
                outcomes.add(report["ok"])
        self.assertEqual(outcomes, {True, False})

    def test_v1_alt_is_a_valid_policy_and_only_the_stale_binding_is_reported(self) -> None:
        case = CASES["full-stale-policy-binding"]
        context, evidence = copy.deepcopy(case["expected_context"]), copy.deepcopy(case["input"])
        self.assertEqual(self.check(V1_ALT, context, evidence), invalid({"policy_digest_mismatch"}))
        self.assertEqual(self.check(V1, context, evidence), invalid({"invalid_expected_context"}))
        evidence["policy_binding"]["policy_digest"] = V1_ALT["policy_digest"]
        self.assertEqual(self.check(V1_ALT, context, evidence), OK)


class ReviewerCompletionTest(EvidenceCase):
    def test_clean_completed_results_without_findings_satisfy_completion(self) -> None:
        context, evidence = clean()
        self.assertEqual(evidence["findings"], [])
        self.assertEqual(self.check(V1, context, evidence), OK)
        fast = CASES["fast-track-clean"]
        self.assertEqual(self.check(V1, fast["expected_context"], fast["input"]), OK)

    def test_failed_or_unavailable_latest_result_does_not_satisfy_completion(self) -> None:
        for job, outcome in (("blake", "failed"), ("bob", "unavailable")):
            with self.subTest(job=job, outcome=outcome):
                context, evidence = clean()
                row = result(evidence, job)
                row["outcome"] = outcome
                row["reason"] = "reviewer timed out"
                self.assertEqual(self.check(V1, context, evidence), invalid({"required_job_failed"}))

    def test_missing_required_result_is_reported(self) -> None:
        context, evidence = clean()
        evidence["reviewer_results"] = [r for r in evidence["reviewer_results"] if r["job_ref"] != "bob"]
        evidence["artifacts"] = [a for a in evidence["artifacts"] if a["result_id"] != "bob-1"]
        evidence["rubric_verdicts"] = [v for v in evidence["rubric_verdicts"] if v["result_id"] != "bob-1"]
        self.assertEqual(self.check(V1, context, evidence), invalid({"missing_required_job"}))
        evidence["reviewer_results"] = []
        report = self.check(V1, context, evidence)
        self.assertIn("missing_required_job", report["defects"])

    def test_finding_count_never_stands_in_for_a_missing_result(self) -> None:
        case = CASES["full-finding-as-completion"]
        self.assertEqual(len(case["input"]["findings"]), 1)
        self.assertEqual(
            self.check(V1, case["expected_context"], case["input"]),
            invalid({"finding_unattributed", "missing_required_job"}),
        )


class AttributionTest(EvidenceCase):
    def test_findings_outcome_with_attributed_findings_and_groups_is_valid(self) -> None:
        context, evidence = clean()
        self.assertEqual(self.check(V1, context, with_findings(evidence)), OK)

    def test_finding_attributed_to_another_result_is_an_outcome_mismatch(self) -> None:
        context, evidence = clean()
        evidence = with_findings(evidence)
        evidence["findings"][1]["result_id"] = "blake-1"
        self.assertEqual(self.check(V1, context, evidence), invalid({"outcome_findings_mismatch"}))

    def test_near_miss_result_id_leaves_the_finding_unattributed(self) -> None:
        context, evidence = clean()
        evidence = with_findings(evidence)
        evidence["findings"][1]["result_id"] = "alice-10"
        self.assertEqual(
            self.check(V1, context, evidence),
            invalid({"finding_unattributed", "outcome_findings_mismatch"}),
        )

    def test_group_referencing_unknown_finding_is_reported(self) -> None:
        context, evidence = clean()
        evidence = with_findings(evidence)
        evidence["groups"][0]["finding_ids"] = ["F1", "F20"]
        self.assertEqual(self.check(V1, context, evidence), invalid({"unknown_reference"}))

    def test_verdict_in_another_jobs_rubric_namespace_is_misattributed(self) -> None:
        context, evidence = clean()
        evidence["rubric_verdicts"].append(
            {"result_id": "blake-1", "namespace": "R", "rule_id": "R1", "verdict": "pass", "evidence": "x"}
        )
        self.assertEqual(self.check(V1, context, evidence), invalid({"result_misattributed"}))

    def test_duplicate_result_ids_are_reported(self) -> None:
        context, evidence = clean()
        result(evidence, "blake")["result_id"] = "alice-1"
        report = self.module.check_evidence(V1, context, evidence)
        self.assertFalse(report["ok"])
        self.assertIn("duplicate_id", report["defects"])


class SourceBindingTest(EvidenceCase):
    def test_stale_prd_digest_near_miss_is_a_binding_mismatch(self) -> None:
        context, evidence = clean()
        evidence["source_bindings"]["prd_sha256"] = "1" * 63 + "0"
        self.assertEqual(self.check(V1, context, evidence), invalid({"source_binding_mismatch"}))

    def test_verification_of_other_code_is_a_binding_mismatch(self) -> None:
        context, evidence = clean()
        evidence["verification"]["code_identity"] = "3" * 39 + "4"
        self.assertEqual(self.check(V1, context, evidence), invalid({"source_binding_mismatch"}))

    def test_expected_context_is_used_independently_of_submitted_evidence(self) -> None:
        context, evidence = clean()
        context["source_bindings"]["prd_sha256"] = "5" * 64
        self.assertEqual(self.check(V1, context, evidence), invalid({"source_binding_mismatch"}))
        evidence["source_bindings"]["prd_sha256"] = "5" * 64
        self.assertEqual(self.check(V1, context, evidence), invalid({"source_binding_mismatch"}))
        redigest_results(evidence)
        self.assertEqual(self.check(V1, context, evidence), OK)


class InputIsolationTest(EvidenceCase):
    def test_blind_reviewer_cannot_receive_diff_that_consensus_may_receive(self) -> None:
        context, evidence = clean()
        self.assertIn("diff:review-fixtures", result(evidence, "alice")["received_input_refs"])
        result(evidence, "blake")["received_input_refs"].append("diff:review-fixtures")
        self.assertEqual(self.check(V1, context, evidence), invalid({"prohibited_input"}))

    def test_near_miss_input_ref_is_not_an_allowed_input(self) -> None:
        context, evidence = clean()
        result(evidence, "blake")["received_input_refs"].append("prd:00019x")
        self.assertEqual(self.check(V1, context, evidence), invalid({"prohibited_input"}))
        context, evidence = clean()
        result(evidence, "alice")["received_input_refs"] = ["diff:review-fixtures"]
        self.assertEqual(self.check(V1, context, evidence), OK)

    def test_context_allowing_a_forbidden_blind_input_is_invalid(self) -> None:
        context, evidence = clean()
        allowed = context["allowed_inputs"]
        allowed["per_job"]["blake"].append("diff:review-fixtures")
        manifest = {
            "input_refs": sorted(allowed["input_refs"]),
            "per_job": {job: sorted(set(refs)) for job, refs in allowed["per_job"].items()},
        }
        allowed["manifest_sha256"] = contract.digest(manifest)
        context["source_bindings"]["allowed_input_manifest_sha256"] = allowed["manifest_sha256"]
        self.assertEqual(self.check(V1, context, evidence), invalid({"invalid_expected_context"}))


class ShapeTest(EvidenceCase):
    def test_wire_shape_violations_report_only_schema_invalid(self) -> None:
        def set_attempt(e, c): result(e, "alice")["attempt"] = True
        def set_version(e, c): e["schema_version"] = True
        def add_field(e, c): result(e, "alice")["extra"] = 1
        def drop_field(e, c): del e["findings"]
        def bad_enum(e, c): result(e, "alice")["outcome"] = "passed"
        def context_int(e, c): c["session_identities"]["independent_contexts_required"] = 1
        for mutate in (set_attempt, set_version, add_field, drop_field, bad_enum, context_int):
            with self.subTest(mutation=mutate.__name__):
                context, evidence = clean()
                mutate(evidence, context)
                self.assertEqual(self.check(V1, context, evidence), invalid({"schema_invalid"}))

    def test_non_object_inputs_surface_schema_invalid_instead_of_raising(self) -> None:
        context, evidence = clean()
        for value in (None, [], {}):
            with self.subTest(value=value):
                self.assertEqual(self.check(V1, context, value), invalid({"schema_invalid"}))
                self.assertEqual(self.check(value, context, evidence), invalid({"schema_invalid"}))
                self.assertEqual(self.check(V1, value, evidence), invalid({"schema_invalid"}))

    def test_policy_failing_its_digest_or_invariants_is_schema_invalid(self) -> None:
        context, evidence = clean()
        stale = copy.deepcopy(V1)
        stale["artifact_kinds"] = stale["artifact_kinds"] + ["extra-kind"]
        broken = copy.deepcopy(V1)
        broken["procedure"]["lanes"]["full"]["input_exclusions"] = []
        broken["policy_digest"] = contract.digest({k: v for k, v in broken.items() if k != "policy_digest"})
        for policy in (stale, broken):
            self.assertEqual(self.check(policy, context, evidence), invalid({"schema_invalid"}))

    def test_semantically_wrong_context_reports_invalid_expected_context(self) -> None:
        context, evidence = clean()
        context["session_identities"]["independent_contexts_required"] = False
        self.assertEqual(self.check(V1, context, evidence), invalid({"invalid_expected_context"}))


class ReportTest(EvidenceCase):
    def test_reports_never_carry_the_oracle_accepted_token(self) -> None:
        for case in FIXTURES["cases"]:
            with self.subTest(case=case["name"]):
                policy = FIXTURES["policies"][case["policy"]]
                report = self.module.check_evidence(policy, case["expected_context"], case["input"])
                self.assertIs(type(report["schema_version"]), int)
                self.assertNotIn("accepted", json.dumps(report))
                self.assertNotIn("outcome", report)

    def test_inputs_are_not_mutated(self) -> None:
        for name in ("full-clean", "full-findings-mismatch", "full-schema-invalid"):
            case = CASES[name]
            policy = copy.deepcopy(FIXTURES["policies"][case["policy"]])
            context, evidence = copy.deepcopy(case["expected_context"]), copy.deepcopy(case["input"])
            self.module.check_evidence(policy, context, evidence)
            self.assertEqual((policy, context, evidence), (FIXTURES["policies"][case["policy"]], case["expected_context"], case["input"]))


AUDIT_SCRIPT = r"""
import json, os, sys
scripts, fixtures_path = sys.argv[1], sys.argv[2]
for blocked in ("jsonschema", "test_contract", "test_contract_semantics"):
    sys.modules[blocked] = None
sys.path.insert(0, scripts)
import review_evidence
fixtures = json.loads(open(fixtures_path, encoding="utf-8").read())
policy = review_evidence.load_policy()
case = next(c for c in fixtures["cases"] if c["name"] == "full-clean")
events = []
WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND
def hook(name, args):
    if name == "open" and isinstance(args[0], (str, bytes)):
        mode = args[1] if isinstance(args[1], str) else ""
        flags = args[2] if isinstance(args[2], int) else 0
        events.append([os.fsdecode(args[0]), any(m in mode for m in "wax+") or bool(flags & WRITE)])
sys.addaudithook(hook)
reports = [review_evidence.check_evidence(policy, case["expected_context"], case["input"])]
stale = json.loads(json.dumps(case["input"]))
stale["source_bindings"]["prd_sha256"] = "0" * 64
reports.append(review_evidence.check_evidence(policy, case["expected_context"], stale))
blocked_loaded = [m for m in ("jsonschema", "test_contract") if sys.modules.get(m) is not None]
print(json.dumps({"reports": reports, "events": events, "blocked_loaded": blocked_loaded}))
"""


class NoStateAccessTest(unittest.TestCase):
    def test_check_runs_without_tests_or_jsonschema_and_touches_no_project_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "docs" / "dev" / "project-management" / "autopilot"
            state.mkdir(parents=True)
            (state / "state.json").write_text('{"phase": "review"}', encoding="utf-8")
            before = sorted(str(p.relative_to(tmp)) for p in Path(tmp).rglob("*"))
            proc = subprocess.run(
                [sys.executable, "-I", "-c", AUDIT_SCRIPT, str(SCRIPTS), str(contract.FIXTURES_FILE)],
                cwd=tmp, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            after = sorted(str(p.relative_to(tmp)) for p in Path(tmp).rglob("*"))
            tmp_real = os.path.realpath(tmp)
        out = json.loads(proc.stdout)
        self.assertEqual(out["reports"], [OK, invalid({"source_binding_mismatch"})])
        self.assertEqual(out["blocked_loaded"], [])
        self.assertEqual(before, after)
        contracts = os.path.realpath(PACKAGE / "contracts")
        for path, writes in out["events"]:
            real = os.path.realpath(path)
            self.assertFalse(writes, path)
            self.assertFalse(real.startswith(tmp_real), path)
            if not real.endswith((".py", ".pyc")):
                self.assertTrue(real.startswith(contracts + os.sep), path)


if __name__ == "__main__":
    unittest.main()

"""Review policy and evidence contracts: review_schema and the golden cases."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "plugins" / "autopilot" / "contracts"
POLICY_FILE = CONTRACTS / "review-policy-v1.json"
EVIDENCE_FILE = CONTRACTS / "review-evidence-v1.json"
FIXTURES_FILE = CONTRACTS / "review-fixtures-v1.json"

CONTENT_FIELDS = ("artifacts", "findings", "groups", "rubric_verdicts", "verification")
REQUIRED_FIELDS = ("schema_version", "lane", "policy_binding")
MALFORMED = "malformed_evidence"
GOLDEN = {
    "complete-cycle": "valid",
    "missing-lens": {"invalid": "missing_required_reviewer_job"},
    "malformed-group": {"invalid": "group_references_unknown_finding"},
    "stale-binding": {"invalid": "unresolvable_policy_binding"},
    "unknown-lane": {"invalid": "unknown_lane"},
    "missing-artifact": {"invalid": "missing_required_artifact_kind"},
}
ENTRY_SHAPES = {
    "artifacts": {"kind": None, "path": None, "sha256": None},
    "findings": {
        "id": None,
        "severity": {"critical", "high", "medium", "low"},
        "reviewer": None,
        "title": None,
        "disposition": {"fixed", "accepted", "ledger", "open"},
    },
    "groups": {"id": None, "finding_ids": list, "rationale": None},
    "rubric_verdicts": {"rule_id": None, "verdict": {"pass", "fail"}, "reviewer": None},
}
VERIFICATION_SHAPE = {
    "verified_by": None,
    "outcome": {"confirmed", "refuted", "inconclusive"},
    "finding_id": None,
}


def policy_digest(policy: dict) -> str:
    body = {key: value for key, value in policy.items() if key != "policy_digest"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def has_key_anywhere(doc: object, key: str) -> bool:
    if isinstance(doc, dict):
        return key in doc or any(has_key_anywhere(v, key) for v in doc.values())
    if isinstance(doc, list):
        return any(has_key_anywhere(v, key) for v in doc)
    return False


def entry_ok(entry: object, shape: dict) -> bool:
    if not isinstance(entry, dict):
        return False
    for field, rule in shape.items():
        value = entry.get(field)
        if rule is list:
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                return False
        elif not isinstance(value, str) or (rule is not None and value not in rule):
            return False
    return True


def evidence_malformed(evidence: object) -> bool:
    if not isinstance(evidence, dict) or has_key_anywhere(evidence, "accepted_phase"):
        return True
    if any(field not in evidence for field in REQUIRED_FIELDS):
        return True
    if evidence["schema_version"] != 1 or not isinstance(evidence["lane"], str):
        return True
    if not isinstance(evidence["policy_binding"], dict):
        return True
    if not any(field in evidence for field in CONTENT_FIELDS):
        return True
    for field, shape in ENTRY_SHAPES.items():
        entries = evidence.get(field, [])
        if not isinstance(entries, list) or not all(entry_ok(e, shape) for e in entries):
            return True
    return "verification" in evidence and not entry_ok(evidence["verification"], VERIFICATION_SHAPE)


def review_defects(policy: dict, evidence: object) -> list[str]:
    if evidence_malformed(evidence):
        return [MALFORMED]
    defects = []
    if evidence["policy_binding"].get("policy_digest") != policy_digest(policy):
        defects.append("unresolvable_policy_binding")
    lane = policy["procedure"]["lanes"].get(evidence["lane"])
    if lane is None:
        return defects + ["unknown_lane"]
    findings = evidence.get("findings", [])
    reviewers = {finding["reviewer"] for finding in findings}
    if any(job not in reviewers for job in lane["required_reviewer_jobs"]):
        defects.append("missing_required_reviewer_job")
    kinds = {artifact["kind"] for artifact in evidence.get("artifacts", [])}
    if any(kind not in kinds for kind in lane["required_artifact_kinds"]):
        defects.append("missing_required_artifact_kind")
    ids = {finding["id"] for finding in findings}
    for group in evidence.get("groups", []):
        if any(fid not in ids for fid in group["finding_ids"]):
            defects.append("group_references_unknown_finding")
            break
    return defects


def validate_review(policy: dict, evidence: object) -> str | dict:
    defects = review_defects(policy, evidence)
    return {"invalid": defects[0]} if defects else "valid"


def lane_shape_errors(name: str, lane: object) -> list[str]:
    if not isinstance(lane, dict):
        return [f"lane {name}"]
    errors = []
    for cap in ("default_cap", "rework_cap_default"):
        if type(lane.get(cap)) is not int:
            errors.append(f"lane {name} {cap}")
    for kind in ("required_reviewer_jobs", "required_artifact_kinds"):
        value = lane.get(kind)
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            errors.append(f"lane {name} {kind}")
    return errors


def policy_shape_errors(policy: object) -> list[str]:
    if not isinstance(policy, dict):
        return ["not an object"]
    errors = [] if policy.get("schema_version") == 1 else ["schema_version"]
    procedure = policy.get("procedure")
    lanes = procedure.get("lanes") if isinstance(procedure, dict) else None
    if not isinstance(lanes, dict) or not lanes:
        errors.append("procedure.lanes")
        lanes = {}
    for name, lane in lanes.items():
        errors.extend(lane_shape_errors(name, lane))
    digest = policy.get("policy_digest")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        errors.append("policy_digest format")
    elif digest != policy_digest(policy):
        errors.append("policy_digest mismatch")
    bindings = policy.get("source_bindings")
    if not isinstance(bindings, list) or not all(
        entry_ok(b, {"capability": None, "source_path": None}) for b in bindings
    ):
        errors.append("source_bindings")
    jobs = policy.get("reviewer_jobs")
    if not isinstance(jobs, list) or not all(
        entry_ok(j, {"id": None, "role": None}) and type(j.get("blind")) is bool for j in jobs
    ):
        errors.append("reviewer_jobs")
    if has_key_anywhere(policy, "accepted_phase"):
        errors.append("accepted_phase")
    return errors


def make_policy(
    jobs: tuple = ("alice", "blake", "bob"),
    kinds: tuple = ("review-file",),
    lanes: tuple = ("full",),
) -> dict:
    lane = {"default_cap": 2, "rework_cap_default": 3}
    policy = {
        "schema_version": 1,
        "procedure": {
            "lanes": {
                name: dict(lane, required_reviewer_jobs=list(jobs), required_artifact_kinds=list(kinds))
                for name in lanes
            },
        },
        "source_bindings": [{"capability": "review", "source_path": "skills/review/SKILL.md"}],
        "reviewer_jobs": [
            {"id": "alice", "role": "consensus", "blind": False},
            {"id": "blake", "role": "blind", "blind": True},
        ],
    }
    policy["policy_digest"] = policy_digest(policy)
    return policy


def finding(fid: str, reviewer: str) -> dict:
    return {"id": fid, "severity": "high", "reviewer": reviewer, "title": "t", "disposition": "fixed"}


def make_evidence(policy: dict, reviewers: tuple = ("alice", "blake", "bob")) -> dict:
    findings = [finding(f"F{i}", r) for i, r in enumerate(reviewers, start=1)]
    return {
        "schema_version": 1,
        "lane": "full",
        "policy_binding": {"policy_digest": policy_digest(policy)},
        "artifacts": [{"kind": "review-file", "path": "r.md", "sha256": "0" * 64}],
        "findings": findings,
        "groups": [{"id": "G1", "finding_ids": [f["id"] for f in findings], "rationale": "same"}],
        "rubric_verdicts": [{"rule_id": "R1", "verdict": "pass", "reviewer": "trent"}],
        "verification": {"verified_by": "victor", "outcome": "confirmed", "finding_id": "F1"},
    }


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class DigestTest(unittest.TestCase):
    def test_review_schema_digest_is_sha256_of_sorted_compact_json_without_the_digest_key(self) -> None:
        doc = {"schema_version": 1, "policy_digest": "ignored", "b": [1, "é"], "a": {"z": True, "y": None}}
        expected = hashlib.sha256(b'{"a":{"y":null,"z":true},"b":[1,"\\u00e9"],"schema_version":1}').hexdigest()
        self.assertEqual(policy_digest(doc), expected)

    def test_review_schema_digest_removes_the_key_rather_than_blanking_it(self) -> None:
        doc = {"schema_version": 1, "policy_digest": "x"}
        blanked = hashlib.sha256(b'{"policy_digest":"","schema_version":1}').hexdigest()
        self.assertNotEqual(policy_digest(doc), blanked)
        self.assertEqual(policy_digest(doc), hashlib.sha256(b'{"schema_version":1}').hexdigest())

    def test_review_schema_digest_ignores_stored_digest_but_tracks_nested_content(self) -> None:
        policy = make_policy()
        restamped = dict(policy, policy_digest="f" * 64)
        self.assertEqual(policy_digest(restamped), policy_digest(policy))
        changed = copy.deepcopy(policy)
        changed["procedure"]["lanes"]["full"]["default_cap"] = 3
        self.assertNotEqual(policy_digest(changed), policy_digest(policy))


class ValidatorTest(unittest.TestCase):
    def test_review_schema_accepts_a_complete_bound_cycle(self) -> None:
        policy = make_policy()
        self.assertEqual(validate_review(policy, make_evidence(policy)), "valid")

    def test_review_schema_rejects_evidence_with_no_content_fields(self) -> None:
        policy = make_policy()
        bare = {key: make_evidence(policy)[key] for key in REQUIRED_FIELDS}
        self.assertEqual(validate_review(policy, bare), {"invalid": MALFORMED})
        for field in CONTENT_FIELDS:
            with self.subTest(only=field):
                one = dict(bare, **{field: make_evidence(policy)[field]})
                self.assertNotEqual(review_defects(policy, one), [MALFORMED])

    def test_review_schema_rejects_missing_required_fields_and_accepted_phase(self) -> None:
        policy = make_policy()
        for field in REQUIRED_FIELDS:
            with self.subTest(missing=field):
                evidence = make_evidence(policy)
                del evidence[field]
                self.assertEqual(validate_review(policy, evidence), {"invalid": MALFORMED})
        nested = make_evidence(policy)
        nested["findings"][1]["accepted_phase"] = "review"
        self.assertEqual(validate_review(policy, nested), {"invalid": MALFORMED})
        self.assertEqual(validate_review(policy, None), {"invalid": MALFORMED})

    def test_review_schema_rejects_near_miss_enum_values(self) -> None:
        policy = make_policy()
        for field, key, bad in (
            ("findings", "severity", "Critical"),
            ("findings", "disposition", "fixed "),
            ("rubric_verdicts", "verdict", "passed"),
        ):
            with self.subTest(field=field, value=bad):
                evidence = make_evidence(policy)
                evidence[field][-1][key] = bad
                self.assertEqual(validate_review(policy, evidence), {"invalid": MALFORMED})
        evidence = make_evidence(policy)
        evidence["verification"]["outcome"] = "confirm"
        self.assertEqual(validate_review(policy, evidence), {"invalid": MALFORMED})

    def test_review_schema_binding_must_match_the_passed_policy_exactly(self) -> None:
        policy = make_policy()
        other = make_policy(jobs=("alice", "blake", "bob", "carl"))
        evidence = make_evidence(policy)
        self.assertEqual(validate_review(policy, evidence), "valid")
        self.assertEqual(review_defects(other, evidence)[0], "unresolvable_policy_binding")
        evidence["policy_binding"]["policy_digest"] = policy_digest(policy)[:-1]
        self.assertEqual(review_defects(policy, evidence), ["unresolvable_policy_binding"])
        evidence["policy_binding"]["policy_digest"] = policy["policy_digest"].upper()
        self.assertEqual(review_defects(policy, evidence), ["unresolvable_policy_binding"])

    def test_review_schema_lane_must_name_a_policy_lane_exactly(self) -> None:
        policy = make_policy(lanes=("full", "solo"))
        for lane, expected in (
            ("full", []),
            ("solo", []),
            ("Full", ["unknown_lane"]),
            ("full ", ["unknown_lane"]),
            ("ful", ["unknown_lane"]),
            ("", ["unknown_lane"]),
        ):
            with self.subTest(lane=lane):
                evidence = dict(make_evidence(policy), lane=lane)
                self.assertEqual(review_defects(policy, evidence), expected)

    def test_review_schema_requires_every_reviewer_job_of_the_lane(self) -> None:
        policy = make_policy()
        for reviewers, expected in (
            (("alice", "blake", "bob"), []),
            (("bob", "alice", "blake", "alice"), []),
            (("alice", "blake"), ["missing_required_reviewer_job"]),
            (("blake", "bob"), ["missing_required_reviewer_job"]),
            (("alice", "blake", "bobby"), ["missing_required_reviewer_job"]),
            ((), ["missing_required_reviewer_job"]),
        ):
            with self.subTest(reviewers=reviewers):
                self.assertEqual(review_defects(policy, make_evidence(policy, reviewers)), expected)

    def test_review_schema_reads_requirements_from_the_passed_policy_lane(self) -> None:
        lenient = make_policy(jobs=(), kinds=())
        evidence = make_evidence(lenient, reviewers=())
        del evidence["artifacts"]
        self.assertEqual(validate_review(lenient, evidence), "valid")
        strict = make_policy(jobs=("carl",))
        self.assertEqual(
            review_defects(strict, make_evidence(strict)), ["missing_required_reviewer_job"]
        )

    def test_review_schema_requires_every_artifact_kind_of_the_lane(self) -> None:
        policy = make_policy(kinds=("review-file", "ledger"))
        for kinds, expected in (
            (("review-file", "ledger"), []),
            (("ledger", "review-file", "ledger"), []),
            (("review-file",), ["missing_required_artifact_kind"]),
            (("review-files", "ledger"), ["missing_required_artifact_kind"]),
            ((), ["missing_required_artifact_kind"]),
        ):
            with self.subTest(kinds=kinds):
                evidence = make_evidence(policy)
                evidence["artifacts"] = [{"kind": k, "path": "p", "sha256": "0" * 64} for k in kinds]
                self.assertEqual(review_defects(policy, evidence), expected)

    def test_review_schema_groups_must_reference_known_findings(self) -> None:
        policy = make_policy()
        for ids, expected in (
            (["F1", "F2", "F3"], []),
            ([], []),
            (["F1", "F4"], ["group_references_unknown_finding"]),
            (["F10"], ["group_references_unknown_finding"]),
            (["F"], ["group_references_unknown_finding"]),
        ):
            with self.subTest(ids=ids):
                evidence = make_evidence(policy)
                evidence["groups"].append({"id": "G2", "finding_ids": ids, "rationale": "r"})
                self.assertEqual(review_defects(policy, evidence), expected)


class FixtureFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = load(FIXTURES_FILE)
        self.by_name = {case["name"]: case for case in self.cases}

    def test_review_schema_fixture_file_holds_each_golden_case_once(self) -> None:
        self.assertIsInstance(self.cases, list)
        names = [case["name"] for case in self.cases]
        self.assertEqual(len(names), len(set(names)))
        self.assertLessEqual(set(GOLDEN), set(names))
        for name, expect in GOLDEN.items():
            with self.subTest(case=name):
                self.assertEqual(self.by_name[name]["expect"], expect)
                self.assertEqual(set(self.by_name[name]), {"name", "policy", "input", "expect"})

    def test_review_schema_every_case_policy_is_well_formed_and_self_digested(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["name"]):
                self.assertEqual(policy_shape_errors(case["policy"]), [])

    def test_review_schema_every_case_validates_to_its_expect_with_one_defect(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["name"]):
                defects = review_defects(case["policy"], case["input"])
                self.assertNotIn(MALFORMED, defects)
                if case["expect"] == "valid":
                    self.assertEqual(defects, [])
                else:
                    self.assertEqual(defects, [case["expect"]["invalid"]])
                self.assertEqual(validate_review(case["policy"], case["input"]), case["expect"])

    def test_review_schema_complete_cycle_populates_every_content_field(self) -> None:
        case = self.by_name["complete-cycle"]
        evidence, lane = case["input"], case["policy"]["procedure"]["lanes"].get("full")
        self.assertEqual(evidence["lane"], "full")
        self.assertIsNotNone(lane)
        self.assertTrue(lane["required_reviewer_jobs"])
        self.assertTrue(lane["required_artifact_kinds"])
        for field in CONTENT_FIELDS:
            with self.subTest(field=field):
                self.assertTrue(evidence.get(field))
        self.assertGreater(len(evidence["findings"]), 1)
        self.assertGreater(sum(len(g["finding_ids"]) for g in evidence["groups"]), 1)

    def test_review_schema_lens_and_artifact_cases_reuse_the_complete_cycle_policy(self) -> None:
        base = self.by_name["complete-cycle"]["policy"]
        for name in ("missing-lens", "missing-artifact"):
            with self.subTest(case=name):
                self.assertEqual(self.by_name[name]["policy"], base)
                self.assertEqual(self.by_name[name]["input"]["lane"], "full")

    def test_review_schema_unknown_lane_case_names_a_lane_absent_from_its_policy(self) -> None:
        case = self.by_name["unknown-lane"]
        lane = case["input"]["lane"]
        self.assertIsInstance(lane, str)
        self.assertNotIn(lane, case["policy"]["procedure"]["lanes"])


class ContractFileTest(unittest.TestCase):
    def test_review_schema_policy_contract_is_well_formed_and_self_digested(self) -> None:
        self.assertEqual(policy_shape_errors(load(POLICY_FILE)), [])

    def test_review_schema_evidence_contract_is_valid_against_the_policy_contract(self) -> None:
        self.assertEqual(validate_review(load(POLICY_FILE), load(EVIDENCE_FILE)), "valid")

    def test_review_schema_no_contract_carries_accepted_phase(self) -> None:
        for path in (POLICY_FILE, EVIDENCE_FILE, FIXTURES_FILE):
            with self.subTest(path=path.name):
                self.assertFalse(has_key_anywhere(load(path), "accepted_phase"))

    def test_review_schema_policy_shape_check_rejects_a_stale_stored_digest(self) -> None:
        policy = make_policy()
        self.assertEqual(policy_shape_errors(policy), [])
        stale = dict(policy, policy_digest=policy_digest(make_policy(jobs=("alice",))))
        self.assertEqual(policy_shape_errors(stale), ["policy_digest mismatch"])
        self.assertEqual(policy_shape_errors(dict(policy, policy_digest="abc")), ["policy_digest format"])


if __name__ == "__main__":
    unittest.main()

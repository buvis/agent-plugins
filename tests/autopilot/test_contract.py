"""Normative review policy data and draft 2020-12 evidence wire contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "plugins" / "autopilot" / "contracts"
POLICY_FILE = CONTRACTS / "review-policy-v1.json"
EVIDENCE_FILE = CONTRACTS / "review-evidence-v1.json"
FIXTURES_FILE = CONTRACTS / "review-fixtures-v1.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


R = [f"R{i}" for i in (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13)]
B = [f"B{i}" for i in range(1, 20)]
D = [f"D{i}" for i in range(1, 6)]
ARTIFACT_KINDS = ["review-file", "reviewer-output", "verification-log"]
INPUT_KINDS = [
    "prd", "card", "repo-tree", "rubric", "diff", "file-list", "plan", "history",
    "implementation-audit", "sibling-findings", "context-pack", "mech-facts", "test-results",
]
JOBS = [
    {"job_id": "alice", "role_id": "consensus", "lenses": ["consensus"], "anchor": "rwc-reviewers"},
    {"job_id": "blake", "role_id": "blind", "lenses": ["blind"], "anchor": "blind-rubric"},
    {"job_id": "bob", "role_id": "doubt", "lenses": ["consensus", "doubt", "de-slop"], "anchor": "rwc-reviewers"},
    {"job_id": "carl", "role_id": "ui", "lenses": ["consensus", "ui"], "anchor": "rwc-prereqs"},
    {"job_id": "eve", "role_id": "doubt", "lenses": ["doubt", "de-slop"], "anchor": "eve-two-lenses"},
]
PREDICATES = {
    "gemini_cli_available": ("gemini_cli", True),
    "doubt_reviewer_fable": ("doubt_reviewer", "fable"),
    "implementor_codex_present": ("implementor_codex_present", True),
}
BINDINGS = {
    "rwc-reviewers": ("skills/review-work-completion/SKILL.md", "reviewers"),
    "rwc-prereqs": ("skills/review-work-completion/SKILL.md", "1-validate-prerequisites"),
    "rwc-context": ("skills/review-work-completion/SKILL.md", "3-gather-context"),
    "rwc-prompts": ("skills/review-work-completion/SKILL.md", "4-prepare-agent-prompts"),
    "rwc-dispatch": ("skills/review-work-completion/SKILL.md", "5-run-agent-review"),
    "rwc-consolidate": ("skills/review-work-completion/SKILL.md", "6-consolidate-findings"),
    "consensus-rubric": ("skills/review-work-completion/references/rubric.md", "rules"),
    "blind-rubric": ("skills/review-blindly/references/rubric.md", "rules"),
    "doubt-rubric": ("skills/run-autopilot/references/doubt-review-rubric.md", "rules"),
    "eve-two-lenses": ("agents/eve.md", "two-lenses-applied-to-every-changed-file"),
    "eve-de-slop": ("agents/eve.md", "2-de-slop-lens-quality"),
    "eve-verdicts": ("agents/eve.md", "rubric-verdicts-required--emit-verbatim-one-per-line"),
    "bob-persona": ("agents/bob.md", None),
    "retry-policy": ("skills/review-work-completion/references/retry-policy.md", "when-to-retry"),
    "verdict-completeness": ("skills/review-work-completion/references/retry-policy.md", "per-rule-verdict-completeness"),
    "review-cap-check": ("skills/run-autopilot/references/phase-review.md", "cap-check--evaluate-after-reading-review-before-rework-dispatch"),
    "review-cap-pause": ("skills/run-autopilot/references/phase-review.md", "cap-pause-behavior"),
    "review-outcomes": ("skills/run-autopilot/references/phase-review.md", "outcomes"),
    "review-de-slop": ("skills/run-autopilot/references/phase-review.md", "de-slop-is-part-of-the-doubt-lens"),
    "fast-track-roster": ("skills/fast-track/SKILL.md", "roster"),
    "fast-track-rework": ("skills/fast-track/SKILL.md", "rework"),
    "fast-track-delta": ("skills/fast-track/SKILL.md", "delta"),
    "fast-track-exit": ("skills/fast-track/SKILL.md", "exit"),
    "solo-escalation": ("skills/run-autopilot/references/lane-solo.md", "4-escalation-checks"),
    "solo-review": ("skills/run-autopilot/references/lane-solo.md", "5-review"),
    "solo-disposition": ("skills/run-autopilot/references/lane-solo.md", "disposition"),
    "review-file-format": ("skills/review-work-completion/references/review-coverage-format.md", None),
    "frontmatter-defaults": ("skills/run-autopilot/cli/frontmatter.py", None),
    "lane-routing": ("skills/run-autopilot/cli/lane.py", None),
}
ESCALATIONS = {
    "full": [
        ("critical_unresolved_at_cap", "stall_or_pause", "review-cap-check"),
        ("high_unresolved_at_cap_interactive", "stall_or_pause", "review-cap-pause"),
        ("high_unresolved_at_cap_loop", "defer", "review-cap-check"),
        ("high_regression_at_cap_loop", "stall_or_pause", "review-cap-check"),
        ("cap_check_failed", "retry_once", "review-cap-check"),
        ("doubt_constraint_unmet", "treat_as_critical", "review-outcomes"),
        ("reviewer_failed_after_retry", "mark_unavailable", "retry-policy"),
    ],
    "fast-track": [
        ("critical_or_high_survives_delta", "branch_and_park", "fast-track-exit"),
        ("consensus_workflow_unavailable", "fallback_native_consensus", "fast-track-roster"),
    ],
    "solo": [
        ("unnamed_path", "escalate_full", "solo-escalation"),
        ("security_diff", "escalate_full", "solo-escalation"),
        ("check_failed", "escalate_full", "solo-escalation"),
        ("critical_finding", "escalate_full", "solo-disposition"),
        ("high_unresolved", "escalate_full", "solo-disposition"),
        ("suite_red", "escalate_full", "solo-disposition"),
        ("review_failed", "escalate_full", "solo-review"),
        ("review_invalid", "retry_once", "solo-review"),
    ],
}


class PolicyContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load(POLICY_FILE)

    def test_policy_has_exact_root_fields_jobs_rubrics_and_canonical_digest(self) -> None:
        self.assertEqual(set(self.policy), {
            "schema_version", "procedure", "reviewer_jobs", "rubric_sets", "doubt_label_map",
            "execution_profiles", "artifact_kinds", "input_kinds", "source_bindings", "policy_digest",
        })
        self.assertIs(type(self.policy["schema_version"]), int)
        self.assertEqual(self.policy["schema_version"], 1)
        body = {k: v for k, v in self.policy.items() if k != "policy_digest"}
        self.assertEqual(self.policy["policy_digest"], digest(body))
        self.assertCountEqual(self.policy["reviewer_jobs"], JOBS)
        self.assertEqual(self.policy["rubric_sets"], {
            "R": {"rule_ids": R, "anchor": "consensus-rubric"},
            "B": {"rule_ids": B, "anchor": "blind-rubric"},
            "D": {"rule_ids": D, "anchor": "doubt-rubric", "de_slop_anchor": "eve-de-slop"},
        })
        self.assertEqual(self.policy["doubt_label_map"], {f"R{i}": f"D{i}" for i in range(1, 6)})
        self.assertEqual(self.policy["artifact_kinds"], ARTIFACT_KINDS)
        self.assertEqual(self.policy["input_kinds"], INPUT_KINDS)

    def test_policy_preserves_all_lane_rosters_delta_jobs_and_rework_rules(self) -> None:
        procedure = self.policy["procedure"]
        self.assertEqual(set(procedure), {"lanes", "conditional_predicates"})
        self.assertEqual(set(procedure["lanes"]), {"full", "fast-track", "solo"})
        required = {"full": ["alice", "blake", "bob"], "fast-track": ["alice", "blake", "eve", "bob"], "solo": ["alice"]}
        conditional = {
            "full": [("carl", "gemini_cli_available"), ("eve", "doubt_reviewer_fable"), ("eve", "implementor_codex_present")],
            "fast-track": [("carl", "gemini_cli_available")], "solo": [],
        }
        for name, lane in procedure["lanes"].items():
            with self.subTest(lane=name):
                self.assertEqual(set(lane), {
                    "required_reviewer_jobs", "conditional_reviewer_jobs", "delta_reviewer_jobs",
                    "required_artifact_kinds", "required_rubric_sets", "input_exclusions",
                    "independent_contexts", "fresh_coordinator_review", "verification_not_applicable_reasons", "rework_policy",
                })
                self.assertEqual(lane["required_reviewer_jobs"], required[name])
                self.assertEqual(lane["conditional_reviewer_jobs"], [
                    {"job_id": j, "predicate_id": p} for j, p in conditional[name]
                ])
                self.assertEqual(lane["delta_reviewer_jobs"], {"full": [], "fast-track": ["eve"], "solo": ["alice"]}[name])
                self.assertEqual(lane["required_artifact_kinds"], ["review-file", "reviewer-output"])
                self.assertIs(lane["independent_contexts"], True)
                self.assertIs(lane["fresh_coordinator_review"], name != "solo")
                self.assertEqual(lane["verification_not_applicable_reasons"], ["docs-only"])
                for key in ("cycle_cap_default", "reviewer_retry_limit"):
                    self.assertIs(type(lane["rework_policy"][key]), int)
                self.assertEqual(lane["rework_policy"], {
                    "cycle_cap_default": 2 if name == "full" else 1,
                    "cap_override_source": "prd_frontmatter.rework_cap" if name == "full" else None,
                    "reviewer_retry_limit": 1,
                    "escalation_rules": [dict(zip(("signal", "action", "anchor"), row)) for row in ESCALATIONS[name]],
                })

    def test_policy_keeps_every_rubric_and_blind_input_exclusion(self) -> None:
        sets = {"R": R, "B": B, "D": D}
        anchors = {"R": "consensus-rubric", "B": "blind-rubric", "D": "doubt-rubric"}
        common = [("alice", "R"), ("bob", "R"), ("carl", "R"), ("blake", "B"), ("bob", "D"), ("eve", "D")]
        for name, lane in self.policy["procedure"]["lanes"].items():
            with self.subTest(lane=name):
                pairs = [("alice", "R")] if name == "solo" else common
                expected = [{"job_id": j, "namespace": ns, "rule_ids": sets[ns], "anchor": anchors[ns]} for j, ns in pairs]
                self.assertCountEqual(lane["required_rubric_sets"], expected)
                excluded = [] if name == "solo" else [
                    {"job_id": "blake", "excluded_input_kinds": [
                        "diff", "file-list", "plan", "history", "implementation-audit", "sibling-findings", "context-pack", "mech-facts",
                    ], "anchor": "rwc-prompts"},
                    {"job_id": "eve", "excluded_input_kinds": ["plan"], "anchor": "rwc-context"},
                ]
                self.assertEqual(lane["input_exclusions"], excluded)
        predicates = self.policy["procedure"]["conditional_predicates"]
        self.assertEqual(set(predicates), set(PREDICATES))
        for key, (capability, value) in PREDICATES.items():
            self.assertEqual(set(predicates[key]), {"capability", "expected_value", "description", "anchor"})
            self.assertEqual(predicates[key]["capability"], capability)
            self.assertEqual(predicates[key]["expected_value"], value)
            self.assertIs(type(predicates[key]["expected_value"]), type(value))
            self.assertIsInstance(predicates[key]["description"], str)
            self.assertTrue(predicates[key]["description"])
            self.assertEqual(predicates[key]["anchor"], "rwc-prereqs")

    def test_execution_profiles_keep_provider_adapters_and_fallbacks_separate_from_jobs(self) -> None:
        profiles = self.policy["execution_profiles"]
        self.assertEqual(set(profiles), {"source-parity", "codex-gemini"})
        source = {
            "alice": {"provider": "anthropic", "adapters": ["native-subagent", "review-fanout-workflow"], "fallback": None},
            "blake": {"provider": "anthropic", "adapters": ["native-subagent"], "fallback": None},
            "bob": {"provider": "openai", "adapters": ["codex-cli"], "fallback": {"provider": "anthropic", "adapters": ["native-fallback"]}},
            "carl": {"provider": "google", "adapters": ["gemini-cli"], "fallback": None},
            "eve": {"provider": "anthropic", "adapters": ["native-subagent"], "fallback": {"provider": "anthropic", "adapters": ["native-fallback"]}},
        }
        codex = {j: {"provider": "google" if j in {"carl", "eve"} else "openai", "adapters": ["gemini-cli" if j in {"carl", "eve"} else "codex-cli"], "fallback": None} for j in source}
        for name, expected in (("source-parity", source), ("codex-gemini", codex)):
            profile = profiles[name]
            self.assertEqual(set(profile), {"description", "implementor_providers", "implementor_diversity_guard", "role_bindings"})
            self.assertIsInstance(profile["description"], str)
            self.assertTrue(profile["description"])
            self.assertEqual(profile["implementor_providers"], ["anthropic", "openai"] if name == "source-parity" else ["openai"])
            self.assertIs(profile["implementor_diversity_guard"], True)
            self.assertEqual(profile["role_bindings"], expected)

    def test_source_bindings_keep_exact_paths_sections_and_closed_digest_shapes(self) -> None:
        rows = self.policy["source_bindings"]
        self.assertEqual(len(rows), len(BINDINGS))
        self.assertEqual({r["binding_id"] for r in rows}, set(BINDINGS))
        for row in rows:
            with self.subTest(binding=row["binding_id"]):
                self.assertEqual(set(row), {"binding_id", "source_path", "section", "blob_sha256", "section_sha256"})
                self.assertEqual((row["source_path"], row["section"]), BINDINGS[row["binding_id"]])
                self.assertRegex(row["blob_sha256"], r"^[a-f0-9]{64}$")
                if row["section"] is None:
                    self.assertIsNone(row["section_sha256"])
                else:
                    self.assertRegex(row["section_sha256"], r"^[a-f0-9]{64}$")


class EvidenceSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load(EVIDENCE_FILE)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)
        cls.context_validator = Draft202012Validator({"$ref": "#/$defs/expected_context", "$defs": cls.schema["$defs"]})
        cls.cases = {c["name"]: c for c in load(FIXTURES_FILE)["cases"]}

    def assert_valid(self, value: Any, context: bool = False) -> None:
        validator = self.context_validator if context else self.validator
        self.assertEqual(list(validator.iter_errors(value)), [])

    def assert_invalid(self, value: Any, context: bool = False) -> None:
        validator = self.context_validator if context else self.validator
        self.assertTrue(list(validator.iter_errors(value)), repr(value))

    def test_schema_is_2020_12_and_all_golden_documents_have_expected_structural_validity(self) -> None:
        self.assertEqual(self.schema["$schema"].rstrip("#"), "https://json-schema.org/draft/2020-12/schema")
        self.assertTrue({"expected_context", "source_bindings", "reviewer_result", "artifact", "finding", "group", "rubric_verdict", "verification"} <= self.schema["$defs"].keys())
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assert_valid(case["expected_context"], context=True)
                if name == "full-schema-invalid":
                    self.assert_invalid(case["input"])
                else:
                    self.assert_valid(case["input"])

    def test_schema_requires_every_declared_field_and_rejects_unexpected_object_fields(self) -> None:
        case = self.cases["full-clean"]
        paths = [(), ("policy_binding",), ("source_bindings",), ("source_bindings", "scope"),
                 ("reviewer_results", 0), ("artifacts", 0), ("verification",), ("rubric_verdicts", 0)]
        context_paths = [(), ("source_bindings",), ("resolved_roster", 0), ("excluded_jobs", 0),
                         ("excluded_jobs", 0, "observed"), ("allowed_inputs",), ("session_identities",)]
        for context, path_list in ((False, paths), (True, context_paths)):
            original = case["expected_context" if context else "input"]
            for path in path_list:
                target = original
                for key in path:
                    target = target[key]
                for key in [*target, "unexpected_field"]:
                    changed = copy.deepcopy(original)
                    node = changed
                    for part in path:
                        node = node[part]
                    if key == "unexpected_field":
                        node[key] = "unexpected"
                    else:
                        del node[key]
                    with self.subTest(context=context, path=path, field=key):
                        self.assert_invalid(changed, context)

    def test_schema_checks_nested_findings_groups_activation_and_not_applicable_objects(self) -> None:
        roster = self.cases["full-carl-activated"]["expected_context"]["resolved_roster"]
        carl_index = next(i for i, row in enumerate(roster) if row["job_id"] == "carl")
        documents = [
            (self.cases["full-unknown-finding-reference"]["input"], ("findings", 0), False),
            (self.cases["full-unknown-finding-reference"]["input"], ("groups", 0), False),
            (self.cases["full-carl-activated"]["expected_context"], ("resolved_roster", carl_index, "activation"), True),
        ]
        for original, path, context in documents:
            target = original
            for key in path:
                target = target[key]
            self.assertIsInstance(target, dict)
            for key in [*target, "disposition"]:
                changed = copy.deepcopy(original)
                node = changed
                for part in path:
                    node = node[part]
                if key == "disposition":
                    node[key] = "accepted"
                else:
                    del node[key]
                with self.subTest(path=path, field=key):
                    self.assert_invalid(changed, context)
        doc = copy.deepcopy(self.cases["full-clean"]["input"])
        doc["verification"] = {"status": "not-applicable", "reason": "docs-only"}
        self.assert_valid(doc)
        for extra in ({}, {"status": "not-applicable"}, {"status": "not-applicable", "reason": "docs-only", "exit_code": 0}):
            doc["verification"] = extra
            self.assert_invalid(doc)

    def test_schema_enforces_string_hash_enum_integer_and_array_boundaries(self) -> None:
        base = self.cases["full-clean"]["input"]
        mutations = [
            (("schema_version",), [0, 2, True, "1", None]),
            (("lane",), ["", None, 1]),
            (("review_pass",), ["initial-more", "delta ", "", None]),
            (("policy_binding", "policy_digest"), ["a" * 63, "a" * 65, "A" * 64, "x" + "a" * 64]),
            (("source_bindings", "head_sha"), ["a" * 39, "a" * 41, "A" * 40]),
            (("source_bindings", "scope", "refs"), [[], [""], ["card:1", "card:1"]]),
            (("reviewer_results", 0, "attempt"), [0, -1, True, 1.5, "1"]),
            (("reviewer_results", 0, "role_id"), ["consensus-more", "Blind", ""]),
            (("reviewer_results", 0, "outcome"), ["cleaner", "findings ", ""]),
            (("reviewer_results", 0, "result_id"), ["", None, 1]),
            (("reviewer_results", 0, "received_input_refs"), [["prd:"], ["prd:a b"], ["Prd:a"], ["prd:a", "prd:a"]]),
            (("verification", "argv"), [[], [""], None]),
            (("verification", "exit_code"), [True, 0.5, "0", None]),
        ]
        for path, values in mutations:
            for value in values:
                changed = copy.deepcopy(base)
                target = changed
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.subTest(path=path, value=value):
                    self.assert_invalid(changed)
        for value in ({}, [], None):
            self.assert_invalid(value)
        for lane in ("full-extra", "canary"):
            self.assert_valid(dict(base, lane=lane))

    def test_schema_accepts_distinct_values_and_empty_semantic_collections(self) -> None:
        for name in ("full-clean", "fast-track-delta-clean", "full-findings-without-output"):
            self.assert_valid(self.cases[name]["input"])
        doc = copy.deepcopy(self.cases["full-clean"]["input"])
        for key in ("reviewer_results", "artifacts", "findings", "groups", "rubric_verdicts"):
            doc[key] = []
        self.assert_valid(doc)
        for path in ("docs/review-a.md", "other/review-b.json", "docs/a..b.md"):
            doc = copy.deepcopy(self.cases["full-clean"]["input"])
            doc["artifacts"][0]["path"] = path
            self.assert_valid(doc)
        for path in ("", "/review.md", "../review.md", "docs/../review.md", "C:/review.md", "docs\\review.md"):
            doc["artifacts"][0]["path"] = path
            self.assert_invalid(doc)

    def test_schema_conditions_require_sessions_reasons_findings_and_prior_evidence(self) -> None:
        base = self.cases["full-clean"]["input"]
        for outcome in ("clean", "findings", "failed", "unavailable"):
            doc = copy.deepcopy(base)
            result = doc["reviewer_results"][0]
            result.update(outcome=outcome, finding_ids=["F1"] if outcome == "findings" else [],
                          reason="format-invalid" if outcome in {"failed", "unavailable"} else None)
            self.assert_valid(doc)
            result["native_session_ref"] = None
            if outcome in {"clean", "findings"}:
                self.assert_invalid(doc)
            else:
                self.assert_valid(doc)
                result["reason"] = None
                self.assert_invalid(doc)
        for outcome, ids in (("clean", ["F1"]), ("findings", [])):
            doc = copy.deepcopy(base)
            doc["reviewer_results"][0].update(outcome=outcome, finding_ids=ids)
            self.assert_invalid(doc)
        for review_pass, prior, valid in (("initial", None, True), ("initial", "a" * 64, False), ("delta", "b" * 64, True), ("delta", None, False)):
            doc = copy.deepcopy(base)
            doc["review_pass"] = review_pass
            doc["source_bindings"]["prior_evidence_sha256"] = prior
            (self.assert_valid if valid else self.assert_invalid)(doc)

    def test_expected_context_requires_exact_enums_activation_and_unique_input_refs(self) -> None:
        base = self.cases["full-clean"]["expected_context"]
        for field, invalid in (("lane", "full-extra"), ("consensus_engine", "workflows"), ("resolved_roster", [])):
            self.assert_invalid(dict(base, **{field: invalid}), context=True)
        for engine in ("legacy", "workflow", "shadow"):
            self.assert_valid(dict(base, consensus_engine=engine), context=True)
        for required, activation, valid in ((True, None, True), (False, None, False),
                                           (False, {"predicate_id": "gemini_cli_available", "observed": {"capability": "gemini_cli", "value": True}}, True),
                                           (True, {"predicate_id": "gemini_cli_available", "observed": {"capability": "gemini_cli", "value": True}}, False)):
            context = copy.deepcopy(base)
            context["resolved_roster"][0].update(required=required, activation=activation)
            (self.assert_valid if valid else self.assert_invalid)(context, context=True)
        context = copy.deepcopy(base)
        context["allowed_inputs"]["input_refs"] = ["prd:a", "prd:b"]
        self.assert_valid(context, context=True)
        context["allowed_inputs"]["input_refs"] = ["prd:a", "prd:a"]
        self.assert_invalid(context, context=True)


if __name__ == "__main__":
    unittest.main()

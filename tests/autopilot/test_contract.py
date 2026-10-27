"""Normative review policy data and draft 2020-12 evidence wire contracts."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from typing import Any


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


    def test_source_binding_digests_equal_exact_pinned_inventory_rows(self) -> None:
        inv = load(ROOT / "tools/autopilot/source-inventory.json")
        pin = load(ROOT / "tools/autopilot/source-pin.json")
        self.assertEqual(pin["commit"], "e960ef1cc43e72bf92593b2f16c7a37c71ea7e48")
        self.assertEqual(inv["source_commit"], pin["commit"])
        self.assertEqual(inv["source_repository"], pin["source_repository"])
        rows = {r["source_path"]: r for r in [*inv["source_files"], *inv["assets"]]}
        for binding in self.policy["source_bindings"]:
            with self.subTest(binding=binding["binding_id"]):
                source = rows[binding["source_path"]]
                self.assertEqual(binding["blob_sha256"], source["blob_sha256"])
                sections = {s["anchor"]: s["sha256"] for s in source.get("sections", [])}
                expected = None if binding["section"] is None else sections[binding["section"]]
                self.assertEqual(binding["section_sha256"], expected)


if __name__ == "__main__":
    unittest.main()

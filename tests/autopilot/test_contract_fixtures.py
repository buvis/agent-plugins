"""Golden data cases assert declared defects without implementing a validator."""

from __future__ import annotations

import copy
import unittest
from typing import Any

from test_contract import FIXTURES_FILE, POLICY_FILE, digest, load

ACCEPTED = {
    "full-clean", "fast-track-clean", "solo-clean", "full-carl-activated",
    "full-bob-fallback", "full-bob-fallback-retry", "fast-track-delta-clean",
    "full-eve-guard", "full-alice-workflow-unavailable",
}
REJECTED = {
    "full-missing-alice": ["missing_required_job"],
    "full-missing-blake": ["missing_required_job"],
    "full-missing-bob": ["missing_required_job"],
    "full-eve-guard-missing": ["missing_required_job"],
    "fast-track-alice-only": ["missing_required_job"],
    "solo-review-free": ["missing_required_artifact", "missing_required_job"],
    "full-malformed-output": ["required_job_failed"],
    "full-retry-exhausted": ["required_job_failed", "retry_limit_exceeded"],
    "solo-escalation": ["required_job_failed"],
    "fast-track-delta-missing-eve": ["missing_required_artifact", "missing_required_job"],
    "full-delta-invalid": ["invalid_expected_context"],
    "full-duplicate-result": ["duplicate_job_result"],
    "full-attempt-gap": ["attempt_sequence_invalid"],
    "full-misattributed-result": ["result_misattributed"],
    "full-profile-binding-mismatch": ["profile_binding_mismatch"],
    "full-fallback-without-failure": ["profile_binding_mismatch"],
    "full-alice-workflow-failed-fallback": ["profile_binding_mismatch"],
    "full-alice-engine-mismatch": ["profile_binding_mismatch"],
    "full-retry-exceeded-in-kind": ["retry_limit_exceeded"],
    "full-finding-as-completion": ["finding_unattributed", "missing_required_job"],
    "full-findings-mismatch": ["outcome_findings_mismatch"],
    "full-missing-rubric-verdict": ["missing_rubric_verdict"],
    "full-duplicate-verdict": ["duplicate_id"],
    "full-unknown-rubric-rule": ["unknown_rubric_rule"],
    "full-verdict-unattributed": ["verdict_unattributed"],
    "full-missing-artifact": ["missing_required_artifact"],
    "full-unknown-artifact-kind": ["missing_required_artifact", "unknown_artifact_kind"],
    "full-artifact-unattributed": ["artifact_unattributed"],
    "full-clean-without-output": ["result_without_output"],
    "full-findings-without-output": ["result_without_output"],
    "full-unknown-finding-reference": ["unknown_reference"],
    "full-duplicate-finding-id": ["duplicate_id"],
    "full-stale-policy-binding": ["policy_digest_mismatch"],
    "full-unknown-lane": ["lane_mismatch", "unknown_lane"],
    "full-wrong-profile": ["execution_profile_mismatch"],
    "full-changed-prd": ["source_binding_mismatch"],
    "full-changed-tree": ["source_binding_mismatch"],
    "fast-track-changed-scope": ["source_binding_mismatch"],
    "full-changed-input-manifest": ["source_binding_mismatch"],
    "full-stale-result-binding": ["source_binding_mismatch"],
    "full-blind-prohibited-input": ["prohibited_input"],
    "full-unknown-input-kind": ["prohibited_input", "unknown_input_kind"],
    "full-reused-builder-session": ["shared_session_identity"],
    "full-verification-invalid": ["verification_mismatch"],
    "full-schema-invalid": ["schema_invalid"],
    "full-invalid-context": ["invalid_expected_context"],
}


class GoldenFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load(FIXTURES_FILE)
        cls.cases = {c["name"]: c for c in cls.document["cases"]}
        cls.policy = load(POLICY_FILE)

    def results(self, case: str, job: str) -> list[dict[str, Any]]:
        return sorted((r for r in self.cases[case]["input"]["reviewer_results"] if r["job_ref"] == job), key=lambda r: r["attempt"])

    def test_golden_fixture_has_every_named_case_once_and_exact_complete_defect_sets(self) -> None:
        self.assertEqual(set(self.document), {"schema_version", "policies", "cases"})
        self.assertIs(type(self.document["schema_version"]), int)
        self.assertEqual(self.document["schema_version"], 1)
        self.assertEqual(len(self.document["cases"]), len(self.cases))
        self.assertEqual(set(self.cases), ACCEPTED | REJECTED.keys())
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assertEqual(set(case), {"name", "policy", "expected_context", "input", "expect"})
                expected = {"outcome": "accepted"} if name in ACCEPTED else {"outcome": "rejected", "defects": sorted(REJECTED[name])}
                self.assertEqual(case["expect"], expected)
                self.assertEqual(case["policy"], "v1-alt" if name == "full-stale-policy-binding" else "v1")

    def test_fixture_policies_differ_only_by_description_and_restamped_digest(self) -> None:
        policies = self.document["policies"]
        self.assertEqual(set(policies), {"v1", "v1-alt"})
        self.assertEqual(policies["v1"], self.policy)
        original, alternate = copy.deepcopy(policies["v1"]), copy.deepcopy(policies["v1-alt"])
        for policy in (original, alternate):
            stored = policy.pop("policy_digest")
            self.assertEqual(stored, digest(policy))
        old = original["execution_profiles"]["source-parity"].pop("description")
        new = alternate["execution_profiles"]["source-parity"].pop("description")
        self.assertNotEqual(old, new)
        self.assertIsInstance(new, str)
        self.assertTrue(new)
        self.assertEqual(original, alternate)
        stale = self.cases["full-stale-policy-binding"]
        self.assertEqual(stale["expected_context"]["policy_digest"], policies["v1-alt"]["policy_digest"])
        self.assertEqual(stale["input"]["policy_binding"]["policy_digest"], policies["v1"]["policy_digest"])
        self.assertNotEqual(policies["v1"]["policy_digest"], policies["v1-alt"]["policy_digest"])

    def test_accepted_reviews_are_revision_bound_with_own_outputs_and_all_required_verdicts(self) -> None:
        for name in ACCEPTED:
            case = self.cases[name]
            context, evidence = case["expected_context"], case["input"]
            lane = self.policy["procedure"]["lanes"][context["lane"]]
            artifacts = {a["artifact_id"]: a for a in evidence["artifacts"]}
            with self.subTest(case=name):
                self.assertEqual(evidence["lane"], context["lane"])
                self.assertEqual(evidence["review_pass"], context["review_pass"])
                self.assertEqual(evidence["policy_binding"], {"policy_digest": context["policy_digest"], "execution_profile": context["execution_profile"]})
                self.assertEqual(evidence["source_bindings"], context["source_bindings"])
                self.assertEqual(context["policy_digest"], self.policy["policy_digest"])
                self.assertEqual({r["job_ref"] for r in evidence["reviewer_results"]}, {r["job_id"] for r in context["resolved_roster"]})
                self.assertTrue(set(lane["required_artifact_kinds"]) <= {a["kind"] for a in artifacts.values()})
                for result in evidence["reviewer_results"]:
                    self.assertEqual(result["source_binding_digest"], digest(evidence["source_bindings"]))
                    self.assertTrue(set(result["received_input_refs"]) <= set(context["allowed_inputs"]["per_job"][result["job_ref"]]))
                    if result["outcome"] not in {"clean", "findings"}:
                        continue
                    self.assertTrue(any(artifacts[a]["kind"] == "reviewer-output" and artifacts[a]["result_id"] == result["result_id"] for a in result["artifact_ids"]))
                    actual = {(v["namespace"], v["rule_id"]) for v in evidence["rubric_verdicts"] if v["result_id"] == result["result_id"]}
                    required = {(s["namespace"], r) for s in lane["required_rubric_sets"] if s["job_id"] == result["job_ref"] for r in s["rule_ids"]}
                    self.assertEqual(actual, required)
                verification = evidence["verification"]
                self.assertEqual((verification["status"], verification["exit_code"], verification["outcome"]), ("ran", 0, "passed"))
                self.assertEqual(verification["code_identity"], evidence["source_bindings"]["head_sha"])
                self.assertEqual(artifacts[verification["output_artifact_id"]]["kind"], "verification-log")
                self.assertIsNone(artifacts[verification["output_artifact_id"]]["result_id"])

    def test_accepted_contexts_bind_canonical_input_manifests_and_independent_sessions(self) -> None:
        for name in ACCEPTED:
            context = self.cases[name]["expected_context"]
            allowed = context["allowed_inputs"]
            canonical = {"input_refs": sorted(allowed["input_refs"]), "per_job": {j: sorted(set(refs)) for j, refs in allowed["per_job"].items()}}
            with self.subTest(case=name):
                self.assertEqual(allowed["manifest_sha256"], digest(canonical))
                self.assertEqual(allowed["manifest_sha256"], context["source_bindings"]["allowed_input_manifest_sha256"])
                self.assertEqual(set(allowed["per_job"]), {r["job_id"] for r in context["resolved_roster"]})
                self.assertIs(context["session_identities"]["independent_contexts_required"], True)
                sessions: dict[str, str] = {}
                for result in self.cases[name]["input"]["reviewer_results"]:
                    session = result["native_session_ref"]
                    if session is None:
                        continue
                    self.assertNotIn(session, context["session_identities"]["builder_session_refs"])
                    self.assertIn(sessions.get(session, result["job_ref"]), [result["job_ref"]])
                    sessions[session] = result["job_ref"]

    def test_clean_full_fast_track_solo_and_delta_cases_have_exact_rosters_and_exclusions(self) -> None:
        for name, jobs, lane in (("full-clean", ["alice", "blake", "bob"], "full"),
                                 ("fast-track-clean", ["alice", "blake", "eve", "bob"], "fast-track"),
                                 ("solo-clean", ["alice"], "solo"),
                                 ("fast-track-delta-clean", ["eve"], "fast-track")):
            context, evidence = (self.cases[name][key] for key in ("expected_context", "input"))
            with self.subTest(case=name):
                self.assertEqual(context["lane"], lane)
                self.assertCountEqual([r["job_id"] for r in context["resolved_roster"]], jobs)
                self.assertTrue(all(r["required"] and r["activation"] is None for r in context["resolved_roster"]))
                self.assertEqual(evidence["findings"], [])
                self.assertEqual(evidence["groups"], [])
                self.assertTrue(all(r["attempt"] == 1 and r["outcome"] == "clean" for r in evidence["reviewer_results"]))
                self.assertTrue(all(v["verdict"] == "pass" for v in evidence["rubric_verdicts"]))
        full = self.cases["full-clean"]["expected_context"]
        self.assertCountEqual(full["excluded_jobs"], [
            {"job_id": "carl", "predicate_id": "gemini_cli_available", "observed": {"capability": "gemini_cli", "value": False}},
            {"job_id": "eve", "predicate_id": "doubt_reviewer_fable", "observed": {"capability": "doubt_reviewer", "value": "codex"}},
            {"job_id": "eve", "predicate_id": "implementor_codex_present", "observed": {"capability": "implementor_codex_present", "value": False}},
        ])
        for name in ("solo-clean", "fast-track-delta-clean"):
            self.assertEqual(self.cases[name]["expected_context"]["excluded_jobs"], [])
        self.assertEqual(self.cases["fast-track-clean"]["input"]["source_bindings"]["scope"]["kind"], "card")
        delta = self.cases["fast-track-delta-clean"]
        self.assertEqual(delta["input"]["review_pass"], "delta")
        self.assertRegex(delta["input"]["source_bindings"]["prior_evidence_sha256"], r"^[a-f0-9]{64}$")

    def test_optional_carl_and_codex_implementor_guard_activate_the_named_jobs(self) -> None:
        for name, job, predicate, observed in (
            ("full-carl-activated", "carl", "gemini_cli_available", {"capability": "gemini_cli", "value": True}),
            ("full-eve-guard", "eve", "implementor_codex_present", {"capability": "implementor_codex_present", "value": True}),
        ):
            context = self.cases[name]["expected_context"]
            entry = next(r for r in context["resolved_roster"] if r["job_id"] == job)
            self.assertEqual(entry["activation"], {"predicate_id": predicate, "observed": observed})
            self.assertIs(entry["required"], False)
            self.assertNotIn(job, [r["job_id"] for r in context["excluded_jobs"]])
            result = self.results(name, job)
            self.assertEqual(len(result), 1)
            self.assertEqual((result[0]["provider"], result[0]["adapter"]), ("google", "gemini-cli"))
        guard = self.cases["full-eve-guard"]
        self.assertEqual(guard["expected_context"]["execution_profile"], "codex-gemini")
        for result in guard["input"]["reviewer_results"]:
            if result["job_ref"] != "eve":
                self.assertEqual((result["provider"], result["adapter"]), ("openai", "codex-cli"))

    def test_fallback_and_retry_cases_preserve_full_adapter_history(self) -> None:
        expected = {
            "full-bob-fallback": [("openai", "codex-cli", "unavailable"), ("anthropic", "native-fallback", "clean")],
            "full-bob-fallback-retry": [("openai", "codex-cli", "unavailable"), ("anthropic", "native-fallback", "failed"), ("anthropic", "native-fallback", "clean")],
            "full-retry-exhausted": [("openai", "codex-cli", "failed")] * 3,
            "full-retry-exceeded-in-kind": [("openai", "codex-cli", "failed")] * 2 + [("openai", "codex-cli", "clean")],
            "full-fallback-without-failure": [("anthropic", "native-fallback", "clean")],
        }
        for name, history in expected.items():
            results = self.results(name, "bob")
            with self.subTest(case=name):
                self.assertEqual([(r["provider"], r["adapter"], r["outcome"]) for r in results], history)
                self.assertEqual([r["attempt"] for r in results], list(range(1, len(history) + 1)))
        exhausted = self.results("full-retry-exhausted", "bob")
        self.assertEqual(len({r["native_session_ref"] for r in exhausted}), 3)
        for name in ("full-bob-fallback", "full-bob-fallback-retry"):
            first = self.results(name, "bob")[0]
            self.assertIsNone(first["native_session_ref"])
            self.assertEqual(first["artifact_ids"], [])
            self.assertTrue(first["reason"])
        solo = self.results("solo-escalation", "alice")
        self.assertEqual([(r["attempt"], r["outcome"]) for r in solo], [(1, "failed"), (2, "failed")])
        self.assertIsNotNone(solo[0]["native_session_ref"])
        self.assertEqual(solo[0]["native_session_ref"], solo[1]["native_session_ref"])

    def test_workflow_fallback_cases_distinguish_unavailable_from_failed_and_wrong_engine(self) -> None:
        for name, outcome in (("full-alice-workflow-unavailable", "unavailable"), ("full-alice-workflow-failed-fallback", "failed")):
            self.assertEqual(self.cases[name]["expected_context"]["consensus_engine"], "workflow")
            results = self.results(name, "alice")
            self.assertEqual([(r["attempt"], r["adapter"], r["outcome"]) for r in results], [(1, "review-fanout-workflow", outcome), (2, "native-subagent", "clean")])
            self.assertEqual(results[0]["reason"], "engine_unavailable" if outcome == "unavailable" else "incomplete")
        mismatch = self.cases["full-alice-engine-mismatch"]
        self.assertEqual(mismatch["expected_context"]["consensus_engine"], "legacy")
        self.assertEqual(self.results("full-alice-engine-mismatch", "alice")[0]["adapter"], "review-fanout-workflow")

    def test_missing_job_cases_remove_results_outputs_and_verdicts_together(self) -> None:
        missing = {"full-missing-alice": "alice", "full-missing-blake": "blake", "full-missing-bob": "bob", "full-eve-guard-missing": "eve", "fast-track-delta-missing-eve": "eve"}
        for name, job in missing.items():
            case = self.cases[name]
            evidence = case["input"]
            present = {r["result_id"] for r in evidence["reviewer_results"]}
            with self.subTest(case=name):
                self.assertEqual(self.results(name, job), [])
                self.assertIn(job, [r["job_id"] for r in case["expected_context"]["resolved_roster"]])
                self.assertTrue(all(a["result_id"] is None or a["result_id"] in present for a in evidence["artifacts"]))
                self.assertTrue(all(v["result_id"] in present for v in evidence["rubric_verdicts"]))
        self.assertEqual({r["job_ref"] for r in self.cases["fast-track-alice-only"]["input"]["reviewer_results"]}, {"alice"})
        for name in ("solo-review-free", "fast-track-delta-missing-eve"):
            self.assertEqual(self.cases[name]["input"]["reviewer_results"], [])
            self.assertNotIn("reviewer-output", [a["kind"] for a in self.cases[name]["input"]["artifacts"]])

    def test_identity_attribution_and_rubric_cases_contain_the_declared_near_misses(self) -> None:
        self.assertEqual(self.results("full-attempt-gap", "alice")[0]["attempt"], 2)
        duplicate = self.results("full-duplicate-result", "alice")
        self.assertEqual([r["attempt"] for r in duplicate], [1, 1])
        self.assertEqual(len({r["native_session_ref"] for r in duplicate}), 2)
        self.assertEqual(self.results("full-misattributed-result", "alice")[0]["role_id"], "blind")
        self.assertEqual((self.results("full-profile-binding-mismatch", "alice")[0]["provider"], self.results("full-profile-binding-mismatch", "alice")[0]["adapter"]), ("openai", "codex-cli"))
        for name, rule, count in (("full-missing-rubric-verdict", "D5", 0), ("full-duplicate-verdict", "D1", 2), ("full-unknown-rubric-rule", "D9", 1)):
            bob = self.results(name, "bob")[0]["result_id"]
            rows = [v for v in self.cases[name]["input"]["rubric_verdicts"] if v["result_id"] == bob and v["rule_id"] == rule]
            self.assertEqual(len(rows), count)
            if count == 2:
                self.assertEqual({v["verdict"] for v in rows}, {"pass", "fail"})
        unattributed = self.cases["full-verdict-unattributed"]["input"]
        ids = {r["result_id"] for r in unattributed["reviewer_results"]}
        extra = [v for v in unattributed["rubric_verdicts"] if v["result_id"] not in ids]
        self.assertEqual([v["rule_id"] for v in extra], ["R1"])

    def test_output_and_artifact_cases_are_present_but_unattributed_or_missing(self) -> None:
        for name in ("full-clean-without-output", "full-findings-without-output"):
            job = "blake" if name == "full-clean-without-output" else "bob"
            result = self.results(name, job)[0]
            self.assertEqual(result["artifact_ids"], [])
            self.assertNotIn(result["result_id"], [a["result_id"] for a in self.cases[name]["input"]["artifacts"]])
        self.assertNotIn("review-file", [a["kind"] for a in self.cases["full-missing-artifact"]["input"]["artifacts"]])
        self.assertIn("review-files", [a["kind"] for a in self.cases["full-unknown-artifact-kind"]["input"]["artifacts"]])
        evidence = self.cases["full-artifact-unattributed"]["input"]
        ids = {r["result_id"] for r in evidence["reviewer_results"]}
        orphan = [a for a in evidence["artifacts"] if a["result_id"] is not None and a["result_id"] not in ids]
        self.assertEqual(len(orphan), 1)
        self.assertEqual(orphan[0]["kind"], "reviewer-output")
        bob = self.results("full-malformed-output", "bob")[0]
        self.assertEqual((bob["outcome"], bob["reason"]), ("failed", "format-invalid"))
        self.assertNotIn(bob["result_id"], [v["result_id"] for v in self.cases["full-malformed-output"]["input"]["rubric_verdicts"]])

    def test_finding_cases_preserve_missing_ownership_duplicates_and_unknown_group_reference(self) -> None:
        orphan = self.cases["full-finding-as-completion"]["input"]
        self.assertEqual(self.results("full-finding-as-completion", "bob"), [])
        self.assertEqual(len(orphan["findings"]), 1)
        self.assertNotIn(orphan["findings"][0]["result_id"], [r["result_id"] for r in orphan["reviewer_results"]])
        mismatch = self.cases["full-findings-mismatch"]["input"]
        alice = self.results("full-findings-mismatch", "alice")[0]
        self.assertEqual((alice["outcome"], alice["finding_ids"]), ("clean", []))
        self.assertEqual(mismatch["findings"][0]["result_id"], alice["result_id"])
        unknown = self.cases["full-unknown-finding-reference"]["input"]
        self.assertEqual([f["finding_id"] for f in unknown["findings"]], ["F1"])
        self.assertTrue(any(set(g["finding_ids"]) == {"F1", "F9"} for g in unknown["groups"]))
        duplicate = self.cases["full-duplicate-finding-id"]["input"]
        self.assertEqual([f["finding_id"] for f in duplicate["findings"]], ["F1", "F1"])
        complete = self.cases["full-findings-without-output"]["input"]
        bob = self.results("full-findings-without-output", "bob")[0]
        self.assertEqual(bob["outcome"], "findings")
        self.assertEqual(set(bob["finding_ids"]), {f["finding_id"] for f in complete["findings"] if f["result_id"] == bob["result_id"]})

    def test_stale_binding_cases_change_the_named_revision_fields_and_rebind_results(self) -> None:
        for name, fields in (("full-changed-prd", {"prd_sha256"}), ("full-changed-tree", {"head_sha", "tree_sha"}), ("fast-track-changed-scope", {"scope"}), ("full-changed-input-manifest", {"allowed_input_manifest_sha256"})):
            context, evidence = (self.cases[name][key] for key in ("expected_context", "input"))
            with self.subTest(case=name):
                changed = {k for k in context["source_bindings"] if context["source_bindings"][k] != evidence["source_bindings"][k]}
                self.assertEqual(changed, fields)
                self.assertTrue(all(r["source_binding_digest"] == digest(evidence["source_bindings"]) for r in evidence["reviewer_results"]))
                self.assertEqual(evidence["verification"]["code_identity"], evidence["source_bindings"]["head_sha"])
        stale = self.cases["full-stale-result-binding"]["input"]
        self.assertEqual(sum(r["source_binding_digest"] != digest(stale["source_bindings"]) for r in stale["reviewer_results"]), 1)
        lane = self.cases["full-unknown-lane"]
        self.assertEqual((lane["input"]["lane"], lane["expected_context"]["lane"]), ("canary", "full"))
        profile = self.cases["full-wrong-profile"]
        self.assertEqual(profile["input"]["policy_binding"]["execution_profile"], "codex-gemini")
        self.assertEqual(profile["expected_context"]["execution_profile"], "source-parity")

    def test_contamination_session_verification_and_invalid_context_cases_expose_their_faults(self) -> None:
        self.assertTrue(any(ref.startswith("diff:") for ref in self.results("full-blind-prohibited-input", "blake")[0]["received_input_refs"]))
        self.assertTrue(any(ref.startswith("wiki:") for ref in self.results("full-unknown-input-kind", "alice")[0]["received_input_refs"]))
        reused = self.cases["full-reused-builder-session"]
        self.assertIn(self.results("full-reused-builder-session", "alice")[0]["native_session_ref"], reused["expected_context"]["session_identities"]["builder_session_refs"])
        verification = self.cases["full-verification-invalid"]["input"]["verification"]
        self.assertEqual((verification["exit_code"], verification["outcome"]), (1, "passed"))
        self.assertNotIn("verification", self.cases["full-schema-invalid"]["input"])
        self.assertNotIn("blake", [r["job_id"] for r in self.cases["full-invalid-context"]["expected_context"]["resolved_roster"]])
        delta = self.cases["full-delta-invalid"]
        self.assertEqual((delta["input"]["review_pass"], delta["expected_context"]["review_pass"]), ("delta", "delta"))
        self.assertRegex(delta["input"]["source_bindings"]["prior_evidence_sha256"], r"^[a-f0-9]{64}$")


if __name__ == "__main__":
    unittest.main()

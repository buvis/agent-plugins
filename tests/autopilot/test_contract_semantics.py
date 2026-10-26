"""Independent contract-specific semantic oracle for the golden evidence data."""

from __future__ import annotations

import copy
import unittest
from collections import Counter, defaultdict
from typing import Any

from jsonschema import Draft202012Validator

import test_contract as contract

COMPLETED = {"clean", "findings"}
ENGINE_ADAPTERS = {"native-subagent", "review-fanout-workflow"}


def rejection(defects: set[str]) -> dict[str, Any]:
    return {"outcome": "rejected", "defects": sorted(defects)} if defects else {"outcome": "accepted"}


def policy_invalid(policy: Any) -> bool:
    """Reuse the independent normative policy assertions, including closed shapes."""
    checker = contract.PolicyContractTest()
    checker.policy = policy
    methods = (
        checker.test_policy_has_exact_root_fields_jobs_rubrics_and_canonical_digest,
        checker.test_policy_preserves_all_lane_rosters_delta_jobs_and_rework_rules,
        checker.test_policy_keeps_every_rubric_and_blind_input_exclusion,
        checker.test_execution_profiles_keep_provider_adapters_and_fallbacks_separate_from_jobs,
        checker.test_source_bindings_keep_exact_paths_sections_and_closed_digest_shapes,
    )
    try:
        for method in methods:
            method()
    except (AssertionError, KeyError, TypeError, AttributeError, IndexError):
        return True
    return False


def observed_holds(predicate: dict[str, Any], observed: dict[str, Any]) -> bool:
    return observed["capability"] == predicate["capability"] and observed["value"] == predicate["expected_value"]


def roster_invalid(policy: dict[str, Any], context: dict[str, Any], lane: dict[str, Any]) -> bool:
    entries = context["resolved_roster"]
    roster = {row["job_id"]: row for row in entries}
    required = lane["delta_reviewer_jobs"] if context["review_pass"] == "delta" else lane["required_reviewer_jobs"]
    if len(entries) != len(roster) or any(j not in roster or not roster[j]["required"] for j in required):
        return True
    if context["review_pass"] == "delta":
        return not required or set(roster) != set(required) or bool(context["excluded_jobs"])
    pairs = {(row["job_id"], row["predicate_id"]) for row in lane["conditional_reviewer_jobs"]}
    predicates = policy["procedure"]["conditional_predicates"]
    excluded: set[tuple[str, str]] = set()
    for row in context["excluded_jobs"]:
        pair = (row["job_id"], row["predicate_id"])
        if pair not in pairs or row["job_id"] in roster or observed_holds(predicates[row["predicate_id"]], row["observed"]):
            return True
        excluded.add(pair)
    for row in entries:
        if row["required"]:
            if row["job_id"] not in required:
                return True
            continue
        activation = row["activation"]
        pair = (row["job_id"], activation["predicate_id"])
        if pair not in pairs or not observed_holds(predicates[activation["predicate_id"]], activation["observed"]):
            return True
    return any(job not in roster and (job, predicate) not in excluded for job, predicate in pairs)


def context_invalid(policy: dict[str, Any], context: dict[str, Any]) -> bool:
    if context["policy_digest"] != policy["policy_digest"] or context["execution_profile"] not in policy["execution_profiles"]:
        return True
    lane = policy["procedure"]["lanes"][context["lane"]]
    if roster_invalid(policy, context, lane):
        return True
    allowed = context["allowed_inputs"]
    roster = {row["job_id"] for row in context["resolved_roster"]}
    if set(allowed["per_job"]) != roster:
        return True
    exclusions = {row["job_id"]: set(row["excluded_input_kinds"]) for row in lane["input_exclusions"]}
    for job, refs in allowed["per_job"].items():
        for ref in refs:
            kind = ref.split(":", 1)[0]
            if ref not in allowed["input_refs"] or kind not in policy["input_kinds"] or kind in exclusions.get(job, set()):
                return True
    manifest = {"input_refs": sorted(allowed["input_refs"]), "per_job": {j: sorted(set(refs)) for j, refs in allowed["per_job"].items()}}
    if allowed["manifest_sha256"] != contract.digest(manifest) or allowed["manifest_sha256"] != context["source_bindings"]["allowed_input_manifest_sha256"]:
        return True
    if context["session_identities"]["independent_contexts_required"] != lane["independent_contexts"]:
        return True
    alice = policy["execution_profiles"][context["execution_profile"]]["role_bindings"]["alice"]
    return not ENGINE_ADAPTERS.intersection(alice["adapters"]) and context["consensus_engine"] != "legacy"


def binding_defects(context: dict[str, Any], evidence: dict[str, Any]) -> set[str]:
    defects: set[str] = set()
    if evidence["policy_binding"]["policy_digest"] != context["policy_digest"]:
        defects.add("policy_digest_mismatch")
    if evidence["policy_binding"]["execution_profile"] != context["execution_profile"]:
        defects.add("execution_profile_mismatch")
    source = evidence["source_bindings"]
    verification = evidence["verification"]
    if source != context["source_bindings"] or any(r["source_binding_digest"] != contract.digest(source) for r in evidence["reviewer_results"]):
        defects.add("source_binding_mismatch")
    if verification["status"] == "ran" and verification["code_identity"] != source["head_sha"]:
        defects.add("source_binding_mismatch")
    return defects


def duplicate_defects(evidence: dict[str, Any]) -> set[str]:
    for field, key in (("reviewer_results", "result_id"), ("artifacts", "artifact_id"), ("findings", "finding_id"), ("groups", "group_id")):
        values = [row[key] for row in evidence[field]]
        if len(values) != len(set(values)):
            return {"duplicate_id"}
    verdicts = [(v["result_id"], v["namespace"], v["rule_id"]) for v in evidence["rubric_verdicts"]]
    return {"duplicate_id"} if len(verdicts) != len(set(verdicts)) else set()


def adapter_permitted(binding: dict[str, Any] | None, result: dict[str, Any]) -> bool:
    return binding is not None and result["provider"] == binding["provider"] and result["adapter"] in binding["adapters"]


def profile_mismatch(policy: dict[str, Any], context: dict[str, Any], result: dict[str, Any], previous: list[dict[str, Any]]) -> bool:
    bindings = policy["execution_profiles"][context["execution_profile"]]["role_bindings"]
    binding = bindings.get(result["job_ref"])
    if binding is None:
        return True
    primary = adapter_permitted(binding, result)
    fallback = adapter_permitted(binding["fallback"], result)
    if not primary and not fallback:
        return True
    if fallback and not any(r["outcome"] in {"failed", "unavailable"} for r in previous):
        return True
    if result["job_ref"] != "alice" or not ENGINE_ADAPTERS.intersection(binding["adapters"]):
        return False
    if context["consensus_engine"] in {"legacy", "shadow"}:
        return result["adapter"] != "native-subagent"
    if result["adapter"] == "review-fanout-workflow":
        return False
    return not any(r["adapter"] == "review-fanout-workflow" and r["outcome"] == "unavailable" for r in previous)


def history_defects(policy: dict[str, Any], context: dict[str, Any], evidence: dict[str, Any], lane: dict[str, Any]) -> set[str]:
    defects: set[str] = set()
    jobs = {j["job_id"]: j for j in policy["reviewer_jobs"]}
    roster = {r["job_id"] for r in context["resolved_roster"]}
    histories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in evidence["reviewer_results"]:
        histories[result["job_ref"]].append(result)
        if result["job_ref"] not in roster or result["role_id"] != jobs.get(result["job_ref"], {}).get("role_id"):
            defects.add("result_misattributed")
    for job, history in histories.items():
        attempts = [r["attempt"] for r in history]
        highest = max(attempts)
        if len(attempts) != len(set(attempts)) or any(r["attempt"] != highest and r["outcome"] in COMPLETED for r in history):
            defects.add("duplicate_job_result")
        if sorted(set(attempts)) != list(range(1, highest + 1)):
            defects.add("attempt_sequence_invalid")
        if any(count > lane["rework_policy"]["reviewer_retry_limit"] + 1 for count in Counter(r["adapter"] for r in history).values()):
            defects.add("retry_limit_exceeded")
        for result in history:
            previous = [r for r in history if r["attempt"] < result["attempt"]]
            if profile_mismatch(policy, context, result, previous):
                defects.add("profile_binding_mismatch")
    for job in roster:
        if not histories[job]:
            defects.add("missing_required_job")
        elif max(histories[job], key=lambda r: r["attempt"])["outcome"] in {"failed", "unavailable"}:
            defects.add("required_job_failed")
    return defects


def attribution_defects(evidence: dict[str, Any]) -> set[str]:
    defects: set[str] = set()
    results = {r["result_id"]: r for r in evidence["reviewer_results"]}
    artifacts = {a["artifact_id"]: a for a in evidence["artifacts"]}
    findings = {f["finding_id"] for f in evidence["findings"]}
    for finding in evidence["findings"]:
        if finding["result_id"] not in results:
            defects.add("finding_unattributed")
        elif results[finding["result_id"]]["outcome"] != "findings":
            defects.add("outcome_findings_mismatch")
    for result in results.values():
        attributed = {f["finding_id"] for f in evidence["findings"] if f["result_id"] == result["result_id"]}
        if result["outcome"] == "findings" and set(result["finding_ids"]) != attributed:
            defects.add("outcome_findings_mismatch")
        if any(a not in artifacts for a in result["artifact_ids"]):
            defects.add("artifact_unattributed")
    if any(v["result_id"] not in results for v in evidence["rubric_verdicts"]):
        defects.add("verdict_unattributed")
    if any(a["result_id"] is not None and a["result_id"] not in results for a in artifacts.values()):
        defects.add("artifact_unattributed")
    if any(set(g["finding_ids"]) - findings for g in evidence["groups"]):
        defects.add("unknown_reference")
    verification = evidence["verification"]
    if verification["status"] == "ran" and verification["output_artifact_id"] not in artifacts:
        defects.add("unknown_reference")
    return defects


def rubric_output_defects(policy: dict[str, Any], evidence: dict[str, Any], lane: dict[str, Any]) -> set[str]:
    defects: set[str] = set()
    results = {r["result_id"]: r for r in evidence["reviewer_results"]}
    artifacts = {a["artifact_id"]: a for a in evidence["artifacts"]}
    required: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in lane["required_rubric_sets"]:
        required[row["job_id"]].update((row["namespace"], rule) for rule in row["rule_ids"])
    for verdict in evidence["rubric_verdicts"]:
        if verdict["rule_id"] not in policy["rubric_sets"][verdict["namespace"]]["rule_ids"]:
            defects.add("unknown_rubric_rule")
        result = results.get(verdict["result_id"])
        if result is not None and verdict["namespace"] not in {ns for ns, rule in required[result["job_ref"]]}:
            defects.add("result_misattributed")
    highest: dict[str, int] = defaultdict(int)
    for result in results.values():
        highest[result["job_ref"]] = max(highest[result["job_ref"]], result["attempt"])
    for result in results.values():
        if result["attempt"] != highest[result["job_ref"]] or result["outcome"] not in COMPLETED:
            continue
        actual = {(v["namespace"], v["rule_id"]) for v in evidence["rubric_verdicts"] if v["result_id"] == result["result_id"]}
        if required[result["job_ref"]] - actual:
            defects.add("missing_rubric_verdict")
        if not any(a in artifacts and artifacts[a]["kind"] == "reviewer-output" and artifacts[a]["result_id"] == result["result_id"] for a in result["artifact_ids"]):
            defects.add("result_without_output")
    kinds = {a["kind"] for a in artifacts.values()}
    if kinds - set(policy["artifact_kinds"]):
        defects.add("unknown_artifact_kind")
    if set(lane["required_artifact_kinds"]) - kinds:
        defects.add("missing_required_artifact")
    return defects


def input_session_defects(policy: dict[str, Any], context: dict[str, Any], evidence: dict[str, Any], lane: dict[str, Any]) -> set[str]:
    defects: set[str] = set()
    exclusions = {row["job_id"]: set(row["excluded_input_kinds"]) for row in lane["input_exclusions"]}
    sessions: dict[str, set[str]] = defaultdict(set)
    builders = context["session_identities"]["builder_session_refs"]
    for result in evidence["reviewer_results"]:
        for ref in result["received_input_refs"]:
            kind = ref.split(":", 1)[0]
            if kind not in policy["input_kinds"]:
                defects.add("unknown_input_kind")
            if ref not in context["allowed_inputs"]["per_job"].get(result["job_ref"], []) or kind in exclusions.get(result["job_ref"], set()):
                defects.add("prohibited_input")
        session = result["native_session_ref"]
        if session is not None and lane["independent_contexts"]:
            sessions[session].add(result["job_ref"])
            if session in builders or len(sessions[session]) > 1:
                defects.add("shared_session_identity")
    return defects


def verification_defects(evidence: dict[str, Any], lane: dict[str, Any]) -> set[str]:
    verification = evidence["verification"]
    if verification["status"] == "not-applicable":
        return set() if verification["reason"] in lane["verification_not_applicable_reasons"] else {"verification_mismatch"}
    defects: set[str] = set()
    if (verification["exit_code"] == 0) != (verification["outcome"] == "passed"):
        defects.add("verification_mismatch")
    artifact = next((a for a in evidence["artifacts"] if a["artifact_id"] == verification["output_artifact_id"]), None)
    if artifact is not None and artifact["kind"] != "verification-log":
        defects.add("verification_mismatch")
    return defects


def validate_review(policy: Any, expected_context: Any, evidence: Any) -> dict[str, Any]:
    schema = contract.load(contract.EVIDENCE_FILE)
    validator = Draft202012Validator(schema)
    context_validator = Draft202012Validator({"$ref": "#/$defs/expected_context", "$defs": schema["$defs"]})
    if policy_invalid(policy) or not validator.is_valid(evidence) or not context_validator.is_valid(expected_context):
        return rejection({"schema_invalid"})
    if context_invalid(policy, expected_context):
        return rejection({"invalid_expected_context"})
    defects: set[str] = set()
    if (evidence["lane"], evidence["review_pass"]) != (expected_context["lane"], expected_context["review_pass"]):
        defects.add("lane_mismatch")
    if evidence["lane"] not in policy["procedure"]["lanes"]:
        return rejection(defects | {"unknown_lane"})
    lane = policy["procedure"]["lanes"][expected_context["lane"]]
    defects.update(binding_defects(expected_context, evidence))
    defects.update(duplicate_defects(evidence))
    defects.update(history_defects(policy, expected_context, evidence, lane))
    defects.update(attribution_defects(evidence))
    defects.update(rubric_output_defects(policy, evidence, lane))
    defects.update(input_session_defects(policy, expected_context, evidence, lane))
    defects.update(verification_defects(evidence, lane))
    return rejection(defects)


class EvidenceSemanticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = contract.load(contract.FIXTURES_FILE)
        cls.cases = {c["name"]: c for c in cls.fixtures["cases"]}

    def test_every_golden_case_computes_its_exact_complete_defect_set(self) -> None:
        for case in self.fixtures["cases"]:
            with self.subTest(case=case["name"]):
                policy = self.fixtures["policies"][case["policy"]]
                self.assertEqual(validate_review(policy, case["expected_context"], case["input"]), case["expect"])

    def test_stop_rules_do_not_report_later_defects(self) -> None:
        policy = self.fixtures["policies"]["v1"]
        base = self.cases["full-clean"]
        for value in ({}, None, []):
            self.assertEqual(validate_review(policy, base["expected_context"], value), rejection({"schema_invalid"}))
        context = copy.deepcopy(base["expected_context"])
        context["policy_digest"] = "0" * 64
        evidence = copy.deepcopy(base["input"])
        evidence["lane"] = "full-extra"
        evidence["reviewer_results"] = []
        self.assertEqual(validate_review(policy, context, evidence), rejection({"invalid_expected_context"}))
        self.assertEqual(validate_review(policy, base["expected_context"], evidence), rejection({"lane_mismatch", "unknown_lane"}))

    def test_waivers_and_verification_checks_use_the_expected_lane_and_exact_reason(self) -> None:
        base = self.cases["full-clean"]
        policy = self.fixtures["policies"]["v1"]
        for reason, defects in (("docs-only", set()), ("docs-only-extra", {"verification_mismatch"}), ("docs", {"verification_mismatch"})):
            evidence = copy.deepcopy(base["input"])
            evidence["verification"] = {"status": "not-applicable", "reason": reason}
            self.assertEqual(validate_review(policy, base["expected_context"], evidence), rejection(defects))
        evidence = copy.deepcopy(base["input"])
        evidence["lane"] = "solo"
        evidence["reviewer_results"] = []
        evidence["rubric_verdicts"] = []
        evidence["artifacts"] = [a for a in evidence["artifacts"] if a["result_id"] is None]
        self.assertEqual(validate_review(policy, base["expected_context"], evidence), rejection({"lane_mismatch", "missing_required_job", "missing_required_artifact"}))


if __name__ == "__main__":
    unittest.main()

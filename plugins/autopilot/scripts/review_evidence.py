"""Advisory local AP00012 review evidence checks (stdlib only).

The report never certifies host execution, advances a phase, or replaces the
controller: a valid result still says ``controller_required``.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from evidence_shapes import context_valid, digest, evidence_valid, policy_valid

POLICY_FILE = (
    Path(__file__).resolve().parent.parent / "contracts" / "review-policy-v1.json"
)
COMPLETED = {"clean", "findings"}
UNFINISHED = {"failed", "unavailable"}
ENGINE_ADAPTERS = {"native-subagent", "review-fanout-workflow"}
VALID = {
    "schema_version": 1,
    "ok": True,
    "checks": "local-contract-v1",
    "evidence_valid": True,
    "controller_required": True,
}


def load_policy() -> dict[str, Any]:
    """Return the packaged AP00012 review policy, independent of the working directory."""
    return json.loads(POLICY_FILE.read_text(encoding="utf-8"))


def report(defects: set[str]) -> dict[str, Any]:
    if not defects:
        return dict(VALID)
    return {
        "schema_version": 1,
        "ok": False,
        "error": "invalid-evidence",
        "defects": sorted(defects),
    }


def check_evidence(policy: Any, expected_context: Any, evidence: Any) -> dict[str, Any]:
    """Check submitted evidence against an independently supplied policy and expected context."""
    if not (
        policy_valid(policy, load_policy())
        and evidence_valid(evidence)
        and context_valid(expected_context)
    ):
        return report({"schema_invalid"})
    if context_invalid(policy, expected_context):
        return report({"invalid_expected_context"})
    defects: set[str] = set()
    if (evidence["lane"], evidence["review_pass"]) != (
        expected_context["lane"],
        expected_context["review_pass"],
    ):
        defects.add("lane_mismatch")
    if evidence["lane"] not in policy["procedure"]["lanes"]:
        return report(defects | {"unknown_lane"})
    lane = policy["procedure"]["lanes"][expected_context["lane"]]
    defects |= binding_defects(expected_context, evidence)
    defects |= duplicate_defects(evidence)
    defects |= history_defects(policy, expected_context, evidence, lane)
    defects |= attribution_defects(evidence)
    defects |= rubric_output_defects(policy, evidence, lane)
    defects |= input_session_defects(policy, expected_context, evidence, lane)
    defects |= verification_defects(evidence, lane)
    return report(defects)


def predicate_holds(predicate: dict[str, Any], observed: dict[str, Any]) -> bool:
    return (
        observed["capability"] == predicate["capability"]
        and observed["value"] == predicate["expected_value"]
    )


def valid_exclusions(
    predicates: dict[str, Any], context: dict[str, Any], pairs: set, roster: dict
) -> set | None:
    """Return the validly excluded (job, predicate) pairs, or None when any exclusion is wrong."""
    excluded = set()
    for row in context["excluded_jobs"]:
        pair = (row["job_id"], row["predicate_id"])
        if (
            pair not in pairs
            or row["job_id"] in roster
            or predicate_holds(predicates[row["predicate_id"]], row["observed"])
        ):
            return None
        excluded.add(pair)
    return excluded


def roster_invalid(
    policy: dict[str, Any], context: dict[str, Any], lane: dict[str, Any]
) -> bool:
    entries = context["resolved_roster"]
    roster = {row["job_id"]: row for row in entries}
    delta = context["review_pass"] == "delta"
    required = lane["delta_reviewer_jobs"] if delta else lane["required_reviewer_jobs"]
    if len(entries) != len(roster) or any(
        job not in roster or not roster[job]["required"] for job in required
    ):
        return True
    if delta:
        return (
            not required
            or set(roster) != set(required)
            or bool(context["excluded_jobs"])
        )
    pairs = {
        (row["job_id"], row["predicate_id"])
        for row in lane["conditional_reviewer_jobs"]
    }
    predicates = policy["procedure"]["conditional_predicates"]
    excluded = valid_exclusions(predicates, context, pairs, roster)
    if excluded is None:
        return True
    for row in entries:
        if row["required"]:
            if row["job_id"] not in required:
                return True
            continue
        activation = row["activation"]
        if (row["job_id"], activation["predicate_id"]) not in pairs:
            return True
        if not predicate_holds(
            predicates[activation["predicate_id"]], activation["observed"]
        ):
            return True
    return any(job not in roster and (job, pred) not in excluded for job, pred in pairs)


def inputs_invalid(
    policy: dict[str, Any], context: dict[str, Any], lane: dict[str, Any]
) -> bool:
    allowed = context["allowed_inputs"]
    if set(allowed["per_job"]) != {row["job_id"] for row in context["resolved_roster"]}:
        return True
    exclusions = {
        row["job_id"]: set(row["excluded_input_kinds"])
        for row in lane["input_exclusions"]
    }
    for job, refs in allowed["per_job"].items():
        for ref in refs:
            kind = ref.split(":", 1)[0]
            if (
                ref not in allowed["input_refs"]
                or kind not in policy["input_kinds"]
                or kind in exclusions.get(job, set())
            ):
                return True
    manifest = {
        "input_refs": sorted(allowed["input_refs"]),
        "per_job": {job: sorted(set(refs)) for job, refs in allowed["per_job"].items()},
    }
    expected = digest(manifest)
    return (
        allowed["manifest_sha256"] != expected
        or context["source_bindings"]["allowed_input_manifest_sha256"] != expected
    )


def context_invalid(policy: dict[str, Any], context: dict[str, Any]) -> bool:
    if (
        context["policy_digest"] != policy["policy_digest"]
        or context["execution_profile"] not in policy["execution_profiles"]
    ):
        return True
    lane = policy["procedure"]["lanes"][context["lane"]]
    if roster_invalid(policy, context, lane) or inputs_invalid(policy, context, lane):
        return True
    if (
        context["session_identities"]["independent_contexts_required"]
        != lane["independent_contexts"]
    ):
        return True
    alice = policy["execution_profiles"][context["execution_profile"]]["role_bindings"][
        "alice"
    ]
    return (
        not ENGINE_ADAPTERS.intersection(alice["adapters"])
        and context["consensus_engine"] != "legacy"
    )


def binding_defects(context: dict[str, Any], evidence: dict[str, Any]) -> set[str]:
    defects = set()
    binding, source, verification = (
        evidence["policy_binding"],
        evidence["source_bindings"],
        evidence["verification"],
    )
    if binding["policy_digest"] != context["policy_digest"]:
        defects.add("policy_digest_mismatch")
    if binding["execution_profile"] != context["execution_profile"]:
        defects.add("execution_profile_mismatch")
    expected = digest(source)
    if source != context["source_bindings"] or any(
        r["source_binding_digest"] != expected for r in evidence["reviewer_results"]
    ):
        defects.add("source_binding_mismatch")
    if (
        verification["status"] == "ran"
        and verification["code_identity"] != source["head_sha"]
    ):
        defects.add("source_binding_mismatch")
    return defects


def duplicate_defects(evidence: dict[str, Any]) -> set[str]:
    keyed = (
        ("reviewer_results", "result_id"),
        ("artifacts", "artifact_id"),
        ("findings", "finding_id"),
        ("groups", "group_id"),
    )
    for field, key in keyed:
        ids = [row[key] for row in evidence[field]]
        if len(ids) != len(set(ids)):
            return {"duplicate_id"}
    verdicts = [
        (v["result_id"], v["namespace"], v["rule_id"])
        for v in evidence["rubric_verdicts"]
    ]
    return {"duplicate_id"} if len(verdicts) != len(set(verdicts)) else set()


def adapter_allowed(binding: dict[str, Any] | None, result: dict[str, Any]) -> bool:
    return (
        binding is not None
        and result["provider"] == binding["provider"]
        and result["adapter"] in binding["adapters"]
    )


def profile_mismatch(
    policy: dict[str, Any],
    context: dict[str, Any],
    result: dict[str, Any],
    previous: list,
) -> bool:
    binding = policy["execution_profiles"][context["execution_profile"]][
        "role_bindings"
    ].get(result["job_ref"])
    if binding is None:
        return True
    primary, fallback = (
        adapter_allowed(binding, result),
        adapter_allowed(binding["fallback"], result),
    )
    if not primary and not fallback:
        return True
    if fallback and not any(r["outcome"] in UNFINISHED for r in previous):
        return True
    if result["job_ref"] != "alice" or not ENGINE_ADAPTERS.intersection(
        binding["adapters"]
    ):
        return False
    if context["consensus_engine"] in {"legacy", "shadow"}:
        return result["adapter"] != "native-subagent"
    if result["adapter"] == "review-fanout-workflow":
        return False
    return not any(
        r["adapter"] == "review-fanout-workflow" and r["outcome"] == "unavailable"
        for r in previous
    )


def job_history_defects(
    policy: dict, context: dict, history: list[dict[str, Any]], retry_limit: int
) -> set[str]:
    defects = set()
    attempts = [r["attempt"] for r in history]
    highest = max(attempts)
    if len(attempts) != len(set(attempts)) or any(
        r["attempt"] != highest and r["outcome"] in COMPLETED for r in history
    ):
        defects.add("duplicate_job_result")
    if any(attempt != expected for expected, attempt in enumerate(sorted(set(attempts)), 1)):
        defects.add("attempt_sequence_invalid")
    if any(
        count > retry_limit + 1
        for count in Counter(r["adapter"] for r in history).values()
    ):
        defects.add("retry_limit_exceeded")
    for result in history:
        previous = [r for r in history if r["attempt"] < result["attempt"]]
        if profile_mismatch(policy, context, result, previous):
            defects.add("profile_binding_mismatch")
    return defects


def history_defects(
    policy: dict[str, Any],
    context: dict[str, Any],
    evidence: dict[str, Any],
    lane: dict[str, Any],
) -> set[str]:
    defects = set()
    roles = {job["job_id"]: job["role_id"] for job in policy["reviewer_jobs"]}
    roster = {row["job_id"] for row in context["resolved_roster"]}
    histories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in evidence["reviewer_results"]:
        histories[result["job_ref"]].append(result)
        if result["job_ref"] not in roster or result["role_id"] != roles.get(
            result["job_ref"]
        ):
            defects.add("result_misattributed")
    for history in histories.values():
        defects |= job_history_defects(
            policy, context, history, lane["rework_policy"]["reviewer_retry_limit"]
        )
    for job in roster:
        if not histories.get(job):
            defects.add("missing_required_job")
        elif max(histories[job], key=lambda r: r["attempt"])["outcome"] in UNFINISHED:
            defects.add("required_job_failed")
    return defects


def attribution_defects(evidence: dict[str, Any]) -> set[str]:
    defects = set()
    results = {r["result_id"]: r for r in evidence["reviewer_results"]}
    artifacts = {a["artifact_id"] for a in evidence["artifacts"]}
    findings = evidence["findings"]
    for finding in findings:
        if finding["result_id"] not in results:
            defects.add("finding_unattributed")
        elif results[finding["result_id"]]["outcome"] != "findings":
            defects.add("outcome_findings_mismatch")
    for result_id, result in results.items():
        attributed = {f["finding_id"] for f in findings if f["result_id"] == result_id}
        if result["outcome"] == "findings" and set(result["finding_ids"]) != attributed:
            defects.add("outcome_findings_mismatch")
        if any(a not in artifacts for a in result["artifact_ids"]):
            defects.add("artifact_unattributed")
    if any(v["result_id"] not in results for v in evidence["rubric_verdicts"]):
        defects.add("verdict_unattributed")
    if any(
        a["result_id"] is not None and a["result_id"] not in results
        for a in evidence["artifacts"]
    ):
        defects.add("artifact_unattributed")
    known = {f["finding_id"] for f in findings}
    verification = evidence["verification"]
    if any(set(g["finding_ids"]) - known for g in evidence["groups"]) or (
        verification["status"] == "ran"
        and verification["output_artifact_id"] not in artifacts
    ):
        defects.add("unknown_reference")
    return defects


def required_rubrics(lane: dict[str, Any]) -> dict[str, set[tuple[str, str]]]:
    required: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in lane["required_rubric_sets"]:
        required[row["job_id"]].update(
            (row["namespace"], rule) for rule in row["rule_ids"]
        )
    return required


def rubric_output_defects(
    policy: dict[str, Any], evidence: dict[str, Any], lane: dict[str, Any]
) -> set[str]:
    defects = set()
    results = {r["result_id"]: r for r in evidence["reviewer_results"]}
    artifacts = {a["artifact_id"]: a for a in evidence["artifacts"]}
    required = required_rubrics(lane)
    for verdict in evidence["rubric_verdicts"]:
        if (
            verdict["rule_id"]
            not in policy["rubric_sets"][verdict["namespace"]]["rule_ids"]
        ):
            defects.add("unknown_rubric_rule")
        result = results.get(verdict["result_id"])
        if result is not None and verdict["namespace"] not in {
            ns for ns, _ in required[result["job_ref"]]
        }:
            defects.add("result_misattributed")
    highest: dict[str, Any] = defaultdict(int)
    for result in results.values():
        highest[result["job_ref"]] = max(highest[result["job_ref"]], result["attempt"])
    for result_id, result in results.items():
        if (
            result["attempt"] != highest[result["job_ref"]]
            or result["outcome"] not in COMPLETED
        ):
            continue
        actual = {
            (v["namespace"], v["rule_id"])
            for v in evidence["rubric_verdicts"]
            if v["result_id"] == result_id
        }
        if required[result["job_ref"]] - actual:
            defects.add("missing_rubric_verdict")
        if not any(
            a in artifacts
            and artifacts[a]["kind"] == "reviewer-output"
            and artifacts[a]["result_id"] == result_id
            for a in result["artifact_ids"]
        ):
            defects.add("result_without_output")
    kinds = {a["kind"] for a in artifacts.values()}
    if kinds - set(policy["artifact_kinds"]):
        defects.add("unknown_artifact_kind")
    if set(lane["required_artifact_kinds"]) - kinds:
        defects.add("missing_required_artifact")
    return defects


def input_session_defects(
    policy: dict[str, Any],
    context: dict[str, Any],
    evidence: dict[str, Any],
    lane: dict[str, Any],
) -> set[str]:
    defects = set()
    exclusions = {
        row["job_id"]: set(row["excluded_input_kinds"])
        for row in lane["input_exclusions"]
    }
    per_job = context["allowed_inputs"]["per_job"]
    builders = context["session_identities"]["builder_session_refs"]
    sessions: dict[str, set[str]] = defaultdict(set)
    for result in evidence["reviewer_results"]:
        job = result["job_ref"]
        for ref in result["received_input_refs"]:
            kind = ref.split(":", 1)[0]
            if kind not in policy["input_kinds"]:
                defects.add("unknown_input_kind")
            if ref not in per_job.get(job, []) or kind in exclusions.get(job, set()):
                defects.add("prohibited_input")
        session = result["native_session_ref"]
        if session is not None and lane["independent_contexts"]:
            sessions[session].add(job)
            if session in builders or len(sessions[session]) > 1:
                defects.add("shared_session_identity")
    return defects


def verification_defects(evidence: dict[str, Any], lane: dict[str, Any]) -> set[str]:
    verification = evidence["verification"]
    if verification["status"] == "not-applicable":
        return (
            set()
            if verification["reason"] in lane["verification_not_applicable_reasons"]
            else {"verification_mismatch"}
        )
    defects = set()
    if (verification["exit_code"] == 0) != (verification["outcome"] == "passed"):
        defects.add("verification_mismatch")
    output = next(
        (
            a
            for a in evidence["artifacts"]
            if a["artifact_id"] == verification["output_artifact_id"]
        ),
        None,
    )
    if output is not None and output["kind"] != "verification-log":
        defects.add("verification_mismatch")
    return defects

"""Contract-specific AP00012 wire-shape and policy-invariant checks (stdlib only).

This is not a generic JSON Schema implementation: each function checks the
exact closed shape of one AP00012 field the evidence checker consumes.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
INPUT_REF = re.compile(r"^[a-z][a-z-]*:[^\s]+(?![\s\S])")
RULE_ID = re.compile(r"^[RBD][0-9]+(?![\s\S])")
UNSAFE_PATH = re.compile(r"^/|\\|^[A-Za-z]:|(^|/)\.\.(/|(?![\s\S]))")
BINDING_SHA = re.compile(r"^[a-f0-9]{64}$")
ROLES = ("consensus", "blind", "doubt", "ui")
PASSES = ("initial", "delta")
POLICY_ERRORS = (KeyError, TypeError, AttributeError, IndexError)


def digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def is_int(value: Any) -> bool:
    """JSON Schema integer: bool never counts, an integral float does."""
    return type(value) is int or (type(value) is float and value.is_integer())


def text(value: Any) -> bool:
    return isinstance(value, str) and len(value) >= 1


def nullable(value: Any) -> bool:
    return value is None or text(value)


def hex64(value: Any) -> bool:
    return (
        isinstance(value, str) and len(value) == 64 and HEX64.search(value) is not None
    )


def hex40(value: Any) -> bool:
    return (
        isinstance(value, str) and len(value) == 40 and HEX40.search(value) is not None
    )


def input_ref(value: Any) -> bool:
    return isinstance(value, str) and INPUT_REF.search(value) is not None


def closed(value: Any, *keys: str) -> bool:
    return isinstance(value, dict) and set(value) == set(keys)


def items(value: Any, check: Any, unique: bool = False, min_items: int = 0) -> bool:
    if (
        not isinstance(value, list)
        or len(value) < min_items
        or not all(check(v) for v in value)
    ):
        return False
    return not unique or len(set(value)) == len(value)


def source_bindings_valid(value: Any, delta: bool) -> bool:
    if not closed(
        value,
        "prd_sha256",
        "base_sha",
        "head_sha",
        "tree_sha",
        "scope",
        "allowed_input_manifest_sha256",
        "prior_evidence_sha256",
    ):
        return False
    scope, prior = value["scope"], value["prior_evidence_sha256"]
    return (
        hex64(value["prd_sha256"])
        and hex40(value["base_sha"])
        and hex40(value["head_sha"])
        and hex40(value["tree_sha"])
        and hex64(value["allowed_input_manifest_sha256"])
        and closed(scope, "kind", "refs")
        and scope["kind"] in ("prd", "task", "card")
        and items(scope["refs"], text, unique=True, min_items=1)
        and (hex64(prior) if delta else prior is None)
    )


def reviewer_result_valid(r: Any) -> bool:
    if not closed(
        r,
        "result_id",
        "job_ref",
        "role_id",
        "provider",
        "adapter",
        "attempt",
        "native_session_ref",
        "source_binding_digest",
        "received_input_refs",
        "artifact_ids",
        "outcome",
        "finding_ids",
        "reason",
    ):
        return False
    outcome = r["outcome"]
    if not (
        text(r["result_id"])
        and text(r["job_ref"])
        and r["role_id"] in ROLES
        and text(r["provider"])
        and text(r["adapter"])
        and is_int(r["attempt"])
        and r["attempt"] >= 1
        and nullable(r["native_session_ref"])
        and hex64(r["source_binding_digest"])
        and items(r["received_input_refs"], input_ref, unique=True)
        and items(r["artifact_ids"], text, unique=True)
        and outcome in ("clean", "findings", "failed", "unavailable")
        and items(r["finding_ids"], text, unique=True)
        and nullable(r["reason"])
    ):
        return False
    if outcome == "clean":
        return text(r["native_session_ref"]) and not r["finding_ids"]
    if outcome == "findings":
        return text(r["native_session_ref"]) and bool(r["finding_ids"])
    return text(r["reason"])


def artifact_valid(a: Any) -> bool:
    return (
        closed(a, "artifact_id", "kind", "path", "sha256", "result_id")
        and text(a["artifact_id"])
        and text(a["kind"])
        and text(a["path"])
        and UNSAFE_PATH.search(a["path"]) is None
        and hex64(a["sha256"])
        and nullable(a["result_id"])
    )


def finding_valid(f: Any) -> bool:
    return (
        closed(
            f,
            "finding_id",
            "result_id",
            "severity",
            "title",
            "file",
            "task_ref",
            "evidence",
        )
        and text(f["finding_id"])
        and text(f["result_id"])
        and f["severity"] in ("critical", "high", "medium", "low")
        and text(f["title"])
        and nullable(f["file"])
        and nullable(f["task_ref"])
        and text(f["evidence"])
    )


def group_valid(g: Any) -> bool:
    return (
        closed(g, "group_id", "finding_ids", "rationale")
        and text(g["group_id"])
        and items(g["finding_ids"], text, unique=True, min_items=1)
        and text(g["rationale"])
    )


def verdict_valid(v: Any) -> bool:
    return (
        closed(v, "result_id", "namespace", "rule_id", "verdict", "evidence")
        and text(v["result_id"])
        and v["namespace"] in ("R", "B", "D")
        and isinstance(v["rule_id"], str)
        and RULE_ID.search(v["rule_id"]) is not None
        and v["rule_id"].startswith(v["namespace"])
        and v["verdict"] in ("pass", "fail")
        and text(v["evidence"])
    )


def verification_valid(v: Any) -> bool:
    if closed(
        v,
        "status",
        "argv",
        "exit_code",
        "output_artifact_id",
        "code_identity",
        "outcome",
    ):
        return (
            v["status"] == "ran"
            and items(v["argv"], text, min_items=1)
            and is_int(v["exit_code"])
            and text(v["output_artifact_id"])
            and hex40(v["code_identity"])
            and v["outcome"] in ("passed", "failed")
        )
    return (
        closed(v, "status", "reason")
        and v["status"] == "not-applicable"
        and text(v["reason"])
    )


def evidence_valid(e: Any) -> bool:
    if not closed(
        e,
        "schema_version",
        "lane",
        "review_pass",
        "policy_binding",
        "source_bindings",
        "reviewer_results",
        "artifacts",
        "findings",
        "groups",
        "rubric_verdicts",
        "verification",
    ):
        return False
    binding = e["policy_binding"]
    return (
        is_int(e["schema_version"])
        and e["schema_version"] == 1
        and text(e["lane"])
        and e["review_pass"] in PASSES
        and closed(binding, "policy_digest", "execution_profile")
        and hex64(binding["policy_digest"])
        and text(binding["execution_profile"])
        and source_bindings_valid(e["source_bindings"], e["review_pass"] == "delta")
        and items(e["reviewer_results"], reviewer_result_valid)
        and items(e["artifacts"], artifact_valid)
        and items(e["findings"], finding_valid)
        and items(e["groups"], group_valid)
        and items(e["rubric_verdicts"], verdict_valid)
        and verification_valid(e["verification"])
    )


def observed_valid(o: Any) -> bool:
    return (
        closed(o, "capability", "value")
        and text(o["capability"])
        and (isinstance(o["value"], bool) or text(o["value"]))
    )


def activation_valid(a: Any) -> bool:
    return (
        closed(a, "predicate_id", "observed")
        and text(a["predicate_id"])
        and observed_valid(a["observed"])
    )


def roster_entry_valid(r: Any) -> bool:
    if not closed(r, "job_id", "role_id", "required", "activation"):
        return False
    activation = r["activation"]
    return (
        text(r["job_id"])
        and r["role_id"] in ROLES
        and type(r["required"]) is bool
        and (activation is None if r["required"] else activation_valid(activation))
    )


def excluded_job_valid(x: Any) -> bool:
    return (
        closed(x, "job_id", "predicate_id", "observed")
        and text(x["job_id"])
        and text(x["predicate_id"])
        and observed_valid(x["observed"])
    )


def allowed_inputs_valid(a: Any) -> bool:
    if not closed(a, "manifest_sha256", "input_refs", "per_job") or not isinstance(
        a["per_job"], dict
    ):
        return False
    return (
        hex64(a["manifest_sha256"])
        and items(a["input_refs"], input_ref, unique=True)
        and all(
            text(job) and items(refs, input_ref) for job, refs in a["per_job"].items()
        )
    )


def context_valid(c: Any) -> bool:
    if not closed(
        c,
        "lane",
        "review_pass",
        "execution_profile",
        "consensus_engine",
        "policy_digest",
        "source_bindings",
        "resolved_roster",
        "excluded_jobs",
        "allowed_inputs",
        "session_identities",
    ):
        return False
    sessions = c["session_identities"]
    return (
        c["lane"] in ("full", "fast-track", "solo")
        and c["review_pass"] in PASSES
        and text(c["execution_profile"])
        and c["consensus_engine"] in ("legacy", "workflow", "shadow")
        and hex64(c["policy_digest"])
        and source_bindings_valid(c["source_bindings"], c["review_pass"] == "delta")
        and items(c["resolved_roster"], roster_entry_valid, min_items=1)
        and items(c["excluded_jobs"], excluded_job_valid)
        and allowed_inputs_valid(c["allowed_inputs"])
        and closed(sessions, "builder_session_refs", "independent_contexts_required")
        and items(sessions["builder_session_refs"], text)
        and type(sessions["independent_contexts_required"]) is bool
    )


def same_items(first: Any, second: list[Any]) -> bool:
    """Order-insensitive multiset equality using ==, like unittest's assertCountEqual."""
    rest = list(second)
    for item in first:
        if item not in rest:
            return False
        rest.remove(item)
    return not rest


def policy_valid(policy: Any, reference: dict[str, Any]) -> bool:
    """Check the AP00012 normative invariants; the packaged policy supplies the normative values."""
    try:
        return (
            root_valid(policy, reference)
            and lanes_valid(policy, reference)
            and predicates_valid(policy, reference)
            and profiles_valid(policy, reference)
            and policy_bindings_valid(policy, reference)
        )
    except POLICY_ERRORS:
        return False


def root_valid(policy: Any, reference: dict[str, Any]) -> bool:
    if (
        set(policy) != set(reference)
        or type(policy["schema_version"]) is not int
        or policy["schema_version"] != 1
    ):
        return False
    body = {k: v for k, v in policy.items() if k != "policy_digest"}
    return (
        policy["policy_digest"] == digest(body)
        and same_items(policy["reviewer_jobs"], reference["reviewer_jobs"])
        and all(
            policy[k] == reference[k]
            for k in ("rubric_sets", "doubt_label_map", "artifact_kinds", "input_kinds")
        )
    )


def lanes_valid(policy: dict[str, Any], reference: dict[str, Any]) -> bool:
    procedure, base = policy["procedure"], reference["procedure"]
    if set(procedure) != set(base) or set(procedure["lanes"]) != set(base["lanes"]):
        return False
    special = {
        "required_rubric_sets",
        "independent_contexts",
        "fresh_coordinator_review",
    }
    for name, lane in procedure["lanes"].items():
        want = base["lanes"][name]
        if set(lane) != set(want) or lane["independent_contexts"] is not True:
            return False
        if lane["fresh_coordinator_review"] is not want["fresh_coordinator_review"]:
            return False
        if any(
            type(lane["rework_policy"][k]) is not int
            for k in ("cycle_cap_default", "reviewer_retry_limit")
        ):
            return False
        if not same_items(lane["required_rubric_sets"], want["required_rubric_sets"]):
            return False
        if any(lane[k] != want[k] for k in want if k not in special):
            return False
    return True


def predicates_valid(policy: dict[str, Any], reference: dict[str, Any]) -> bool:
    predicates = policy["procedure"]["conditional_predicates"]
    base = reference["procedure"]["conditional_predicates"]
    if set(predicates) != set(base):
        return False
    for key, want in base.items():
        row = predicates[key]
        if (
            set(row) != set(want)
            or row["capability"] != want["capability"]
            or row["anchor"] != want["anchor"]
        ):
            return False
        value = row["expected_value"]
        if value != want["expected_value"] or type(value) is not type(
            want["expected_value"]
        ):
            return False
        if not isinstance(row["description"], str) or not row["description"]:
            return False
    return True


def profiles_valid(policy: dict[str, Any], reference: dict[str, Any]) -> bool:
    profiles, base = policy["execution_profiles"], reference["execution_profiles"]
    if set(profiles) != set(base):
        return False
    for name, want in base.items():
        profile = profiles[name]
        if (
            set(profile) != set(want)
            or not isinstance(profile["description"], str)
            or not profile["description"]
        ):
            return False
        if profile["implementor_providers"] != want["implementor_providers"]:
            return False
        if (
            profile["implementor_diversity_guard"] is not True
            or profile["role_bindings"] != want["role_bindings"]
        ):
            return False
    return True


def policy_bindings_valid(policy: dict[str, Any], reference: dict[str, Any]) -> bool:
    rows = policy["source_bindings"]
    base = {
        r["binding_id"]: (r["source_path"], r["section"])
        for r in reference["source_bindings"]
    }
    if len(rows) != len(base) or {r["binding_id"] for r in rows} != set(base):
        return False
    keys = {"binding_id", "source_path", "section", "blob_sha256", "section_sha256"}
    for row in rows:
        if (
            set(row) != keys
            or (row["source_path"], row["section"]) != base[row["binding_id"]]
        ):
            return False
        if BINDING_SHA.search(row["blob_sha256"]) is None:
            return False
        if row["section"] is None and row["section_sha256"] is not None:
            return False
        if (
            row["section"] is not None
            and BINDING_SHA.search(row["section_sha256"]) is None
        ):
            return False
    return True

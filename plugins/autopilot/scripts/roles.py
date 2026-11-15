"""Policy-driven role resolution for an execution profile (design §6).

Resolution is static: a resolvable profile only says every role has a host
that implements its required capabilities. `certified` is always False here;
`certifiable` only says observed evidence covers every role.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from hosts import ADAPTER_KINDS, PROVIDER_HOSTS

# predicate_id -> ProfileFacts field the predicate reads.
PREDICATES: dict[str, str] = {
    "gemini_cli_available": "gemini_cli_available",
    "doubt_reviewer_fable": "doubt_reviewer",
    "implementor_codex_present": "implementor_codex_present",
}

REQUIRED_CAPABILITIES: dict[str, frozenset[str]] = {
    "cross-session": frozenset({"identity", "isolation"}),
    "in-session": frozenset({"delegation", "identity", "isolation"}),
    "implementor": frozenset({"identity", "interception", "isolation"}),
}


@dataclass(frozen=True)
class ProfileFacts:
    gemini_cli_available: bool
    doubt_reviewer: str | None
    implementor_codex_present: bool


@dataclass(frozen=True)
class RoleRow:
    role: str
    role_id: str
    host_id: str | None
    adapter: str | None
    execution: str | None
    required_capabilities: tuple[str, ...]
    status: str
    missing: tuple[str, ...]
    unobserved: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedProfile:
    profile_id: str
    lane: str
    claude_free: bool
    status: str
    certifiable: bool
    certified: bool
    roles: tuple[RoleRow, ...]


def roster(policy: dict[str, Any], lane: dict[str, Any], facts: ProfileFacts) -> list[str]:
    """Required jobs in lane order, then each conditional job whose predicate holds, once."""
    predicates = policy["procedure"]["conditional_predicates"]
    jobs = list(lane["required_reviewer_jobs"])
    for row in lane["conditional_reviewer_jobs"]:
        predicate_id = row["predicate_id"]
        if predicate_id not in PREDICATES or predicate_id not in predicates:
            raise ValueError(f"unknown predicate: {predicate_id!r}")
        holds = getattr(facts, PREDICATES[predicate_id]) == predicates[predicate_id]["expected_value"]
        if holds and row["job_id"] not in jobs:
            jobs.append(row["job_id"])
    return jobs


def make_row(role: str, role_id: str, host_id: str | None, adapter: str | None,
             execution: str | None, blockers: list[str], *, capability_kind: str | None,
             claude_free: bool, implemented: Mapping[str, frozenset[str]],
             observed: Mapping[str, frozenset[str]]) -> RoleRow:
    required = REQUIRED_CAPABILITIES[capability_kind] if capability_kind else frozenset()
    if claude_free and host_id == "claude":
        blockers.append("claude_excluded")
    blockers += [f"{host_id}:{cap}" for cap in required if cap not in implemented.get(host_id, frozenset())]
    unobserved = [f"{host_id}:{cap}" for cap in required if cap not in observed.get(host_id, frozenset())]
    return RoleRow(
        role=role, role_id=role_id, host_id=host_id, adapter=adapter, execution=execution,
        required_capabilities=tuple(sorted(required)),
        status="blocked" if blockers else "resolved",
        missing=tuple(sorted(blockers)), unobserved=tuple(sorted(unobserved)),
    )


def resolve_profile(policy: dict[str, Any], *, profile_id: str, lane: str, facts: ProfileFacts,
                    implemented: Mapping[str, frozenset[str]],
                    observed: Mapping[str, frozenset[str]] | None) -> ResolvedProfile:
    if profile_id not in policy["execution_profiles"]:
        raise ValueError(f"unknown execution profile: {profile_id!r}")
    if lane not in policy["procedure"]["lanes"]:
        raise ValueError(f"unknown lane: {lane!r}")
    profile = policy["execution_profiles"][profile_id]
    bindings = profile["role_bindings"]
    providers = list(profile["implementor_providers"])
    for binding in bindings.values():
        providers.append(binding["provider"])
        if binding["fallback"] is not None:
            providers.append(binding["fallback"]["provider"])
    claude_free = "anthropic" not in providers
    context = {"claude_free": claude_free, "implemented": implemented, "observed": observed or {}}
    role_ids = {job["job_id"]: job["role_id"] for job in policy["reviewer_jobs"]}

    rows = []
    for job in roster(policy, policy["procedure"]["lanes"][lane], facts):
        binding = bindings.get(job)
        if binding is None:
            rows.append(make_row(job, role_ids[job], None, None, None, [f"no_role_binding:{job}"],
                                 capability_kind=None, **context))
            continue
        adapter = binding["adapters"][0]
        if adapter not in ADAPTER_KINDS:
            rows.append(make_row(job, role_ids[job], None, adapter, None, [f"unknown_adapter:{adapter}"],
                                 capability_kind=None, **context))
            continue
        host_id, execution = ADAPTER_KINDS[adapter]
        rows.append(make_row(job, role_ids[job], host_id, adapter, execution, [],
                             capability_kind=execution, **context))
    for provider in profile["implementor_providers"]:
        host_id = PROVIDER_HOSTS.get(provider)
        blockers = [] if host_id else [f"unknown_provider:{provider}"]
        rows.append(make_row(f"implementor:{provider}", "implementor", host_id, None,
                             "cross-session", blockers,
                             capability_kind="implementor" if host_id else None, **context))

    blocked = any(row.status == "blocked" for row in rows)
    return ResolvedProfile(
        profile_id=profile_id, lane=lane, claude_free=claude_free,
        status="blocked" if blocked else "resolvable",
        certifiable=not blocked and all(row.unobserved == () for row in rows),
        certified=False, roles=tuple(rows),
    )

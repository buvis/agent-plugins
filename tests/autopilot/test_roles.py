"""roles.py design §6 contract: policy-driven role resolution for execution
profiles, Claude exclusion, capability blockers and observed-evidence gaps."""

from __future__ import annotations

import copy
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

claude = importlib.import_module("claude")
codex = importlib.import_module("codex")
gemini = importlib.import_module("gemini")
review_evidence = importlib.import_module("review_evidence")
roles = importlib.import_module("roles")

POLICY = review_evidence.load_policy()
IMPLEMENTED = {
    "claude": claude.IMPLEMENTED_CAPABILITIES,
    "codex": codex.IMPLEMENTED_CAPABILITIES,
    "gemini": gemini.IMPLEMENTED_CAPABILITIES,
}
CROSS_SESSION = ["identity", "isolation"]
IN_SESSION = ["delegation", "identity", "isolation"]
IMPLEMENTOR = ["identity", "interception", "isolation"]
CODEX_GEMINI_HOSTS = {
    "alice": "codex", "blake": "codex", "bob": "codex",
    "carl": "gemini", "eve": "gemini", "implementor:openai": "codex",
}
ALL_CAPABILITIES = frozenset({"delegation", "identity", "interception", "isolation"})
FULLY_OBSERVED = {host: ALL_CAPABILITIES for host in ("claude", "codex", "gemini")}
CLAUDE_IN_SESSION = ("claude:delegation", "claude:identity", "claude:isolation")


def make_facts(*, gemini_cli: bool = True, doubt: str | None = None, codex_impl: bool = True):
    return roles.ProfileFacts(
        gemini_cli_available=gemini_cli, doubt_reviewer=doubt, implementor_codex_present=codex_impl
    )


def resolve(policy=POLICY, *, profile_id="codex-gemini", lane="full", facts=None,
            implemented=IMPLEMENTED, observed=None):
    return roles.resolve_profile(
        policy, profile_id=profile_id, lane=lane, facts=facts or make_facts(),
        implemented=implemented, observed=observed,
    )


def by_role(profile) -> dict:
    rows = {row.role: row for row in profile.roles}
    assert len(rows) == len(profile.roles), "a role appears in more than one row"
    return rows


def codex_gemini_variant(**bindings) -> dict:
    profile = copy.deepcopy(POLICY["execution_profiles"]["codex-gemini"])
    profile["role_bindings"].update(bindings)
    return profile


def policy_with_profile(name: str, profile: dict) -> dict:
    policy = copy.deepcopy(POLICY)
    policy["execution_profiles"][name] = profile
    return policy


def binding(provider: str, *adapters: str, fallback: dict | None = None) -> dict:
    return {"provider": provider, "adapters": list(adapters), "fallback": fallback}


def test_predicate_table_maps_each_predicate_to_its_fact_field():
    assert roles.PREDICATES == {
        "gemini_cli_available": "gemini_cli_available",
        "doubt_reviewer_fable": "doubt_reviewer",
        "implementor_codex_present": "implementor_codex_present",
    }


def test_codex_gemini_full_lane_resolves_without_claude():
    profile = resolve()
    rows = by_role(profile)
    assert {role: row.host_id for role, row in rows.items()} == CODEX_GEMINI_HOSTS
    assert (profile.profile_id, profile.lane) == ("codex-gemini", "full")
    assert profile.claude_free is True
    assert profile.status == "resolvable"
    assert profile.certifiable is False
    assert profile.certified is False
    for row in profile.roles:
        assert (row.status, row.missing, row.execution) == ("resolved", (), "cross-session")
    reviewer_ids = {job: rows[job].role_id for job in ("alice", "blake", "bob", "carl", "eve")}
    assert reviewer_ids == {"alice": "consensus", "blake": "blind", "bob": "doubt", "carl": "ui", "eve": "doubt"}
    assert [row.role_id for row in profile.roles].count("implementor") == 1
    implementor = rows["implementor:openai"]
    assert implementor.role_id == "implementor"
    assert sorted(implementor.required_capabilities) == IMPLEMENTOR
    assert implementor.unobserved == ("codex:identity", "codex:interception", "codex:isolation")
    assert (rows["alice"].adapter, rows["carl"].adapter) == ("codex-cli", "gemini-cli")
    assert sorted(rows["carl"].required_capabilities) == CROSS_SESSION
    assert rows["carl"].unobserved == ("gemini:identity", "gemini:isolation")
    assert rows["bob"].unobserved == ("codex:identity", "codex:isolation")


def test_gemini_cli_unavailable_drops_carl_but_codex_implementor_keeps_eve():
    rows = by_role(resolve(facts=make_facts(gemini_cli=False)))
    assert set(rows) == {"alice", "blake", "bob", "eve", "implementor:openai"}


def test_no_codex_implementor_and_no_fable_drops_eve_but_keeps_carl():
    rows = by_role(resolve(facts=make_facts(codex_impl=False)))
    assert set(rows) == {"alice", "blake", "bob", "carl", "implementor:openai"}


@pytest.mark.parametrize(("doubt", "eve_mandatory"), [
    ("fable", True), ("Fable", False), ("fables", False), ("fab", False), ("", False), (None, False),
])
def test_eve_is_mandatory_only_for_the_exact_fable_doubt_reviewer(doubt, eve_mandatory):
    rows = by_role(resolve(facts=make_facts(gemini_cli=False, doubt=doubt, codex_impl=False)))
    expected = {"alice", "blake", "bob", "implementor:openai"} | ({"eve"} if eve_mandatory else set())
    assert set(rows) == expected


def test_eve_appears_once_when_both_of_its_predicates_hold():
    profile = resolve(facts=make_facts(doubt="fable", codex_impl=True))
    assert [row.role for row in profile.roles].count("eve") == 1


@pytest.mark.parametrize(("lane", "gemini_cli", "expected"), [
    ("solo", True, {"alice", "implementor:openai"}),
    ("fast-track", False, {"alice", "blake", "bob", "eve", "implementor:openai"}),
    ("fast-track", True, {"alice", "blake", "bob", "carl", "eve", "implementor:openai"}),
])
def test_lane_selects_its_own_required_and_conditional_jobs(lane, gemini_cli, expected):
    profile = resolve(lane=lane, facts=make_facts(gemini_cli=gemini_cli, codex_impl=False))
    assert profile.lane == lane
    assert set(by_role(profile)) == expected


def test_roster_and_role_ids_follow_an_edited_policy():
    policy = copy.deepcopy(POLICY)
    policy["procedure"]["lanes"]["full"]["required_reviewer_jobs"] = ["alice", "bob", "carl"]
    for job in policy["reviewer_jobs"]:
        if job["job_id"] == "alice":
            job["role_id"] = "consensus-edited"
    rows = by_role(resolve(policy, facts=make_facts(gemini_cli=False, codex_impl=False)))
    assert set(rows) == {"alice", "bob", "carl", "implementor:openai"}
    assert rows["alice"].role_id == "consensus-edited"
    assert rows["bob"].role_id == "doubt"
    assert rows["carl"].host_id == "gemini"


def test_source_parity_uses_first_adapter_and_keeps_claude_rows_resolved():
    profile = resolve(profile_id="source-parity")
    rows = by_role(profile)
    assert profile.profile_id == "source-parity"
    assert profile.claude_free is False
    assert profile.status == "resolvable"
    assert profile.certified is False
    assert set(rows) == {"alice", "blake", "bob", "carl", "eve", "implementor:anthropic", "implementor:openai"}
    alice = rows["alice"]
    assert (alice.adapter, alice.host_id, alice.execution) == ("native-subagent", "claude", "in-session")
    assert sorted(alice.required_capabilities) == IN_SESSION
    assert (rows["bob"].adapter, rows["bob"].host_id) == ("codex-cli", "codex")
    assert rows["implementor:anthropic"].host_id == "claude"
    assert rows["implementor:anthropic"].execution == "cross-session"
    assert rows["implementor:openai"].host_id == "codex"
    for row in profile.roles:
        assert (row.status, row.missing) == ("resolved", ())
    assert alice.unobserved == CLAUDE_IN_SESSION
    assert profile.certifiable is False
    without_claude = resolve(profile_id="source-parity",
                             observed={"codex": ALL_CAPABILITIES, "gemini": ALL_CAPABILITIES})
    assert by_role(without_claude)["alice"].unobserved == CLAUDE_IN_SESSION
    assert without_claude.certifiable is False
    assert resolve(profile_id="source-parity", observed=FULLY_OBSERVED).certifiable is True


def test_reviewer_takes_the_first_adapter_not_a_later_one():
    policy = policy_with_profile("first-adapter", codex_gemini_variant(
        alice=binding("openai", "gemini-cli", "codex-cli")))
    alice = by_role(resolve(policy, profile_id="first-adapter"))["alice"]
    assert (alice.adapter, alice.host_id, alice.execution) == ("gemini-cli", "gemini", "cross-session")


@pytest.mark.parametrize(("variant", "claude_free"), [
    ({}, True),
    ({"description": "Mentions anthropic and Anthropic only in prose."}, True),
    ({"bob": binding("openai", "codex-cli", fallback=binding("anthropic", "native-fallback"))}, False),
    ({"carl": binding("anthropic", "gemini-cli")}, False),
    ({"implementor_providers": ["openai", "anthropic"]}, False),
], ids=["no-anthropic", "anthropic-in-description", "anthropic-fallback", "anthropic-binding",
        "anthropic-implementor"])
def test_any_anthropic_provider_makes_the_profile_not_claude_free(variant, claude_free):
    variant = dict(variant)
    top_level = {key: variant.pop(key) for key in ("implementor_providers", "description") if key in variant}
    profile_def = codex_gemini_variant(**variant)
    profile_def.update(top_level)
    profile = resolve(policy_with_profile("variant", profile_def), profile_id="variant")
    assert profile.claude_free is claude_free
    rows = by_role(profile)
    assert (rows["bob"].adapter, rows["bob"].host_id) == ("codex-cli", "codex")


def test_implementor_on_gemini_is_blocked_by_interception():
    profile_def = codex_gemini_variant(alice=binding("openai", "native-subagent"))
    profile_def["implementor_providers"] = ["google"]
    policy = policy_with_profile("gemini-implementor", profile_def)
    profile = resolve(policy, profile_id="gemini-implementor", observed=dict(IMPLEMENTED))
    rows = by_role(profile)
    assert profile.claude_free is True
    alice = rows["alice"]
    assert alice.host_id == "claude"
    assert (alice.status, alice.missing) == ("blocked", ("claude_excluded",))
    implementor = rows["implementor:google"]
    assert implementor.host_id == "gemini"
    assert (implementor.status, implementor.missing) == ("blocked", ("gemini:interception",))
    assert "implementor:openai" not in rows
    for job in ("blake", "bob"):
        assert (rows[job].status, rows[job].missing) == ("resolved", ())
    assert profile.status == "blocked"
    assert profile.certifiable is False
    assert profile.certified is False


@pytest.mark.parametrize(("gemini_caps", "expected_missing"), [
    (frozenset(), ("gemini:identity", "gemini:isolation")),
    (frozenset({"identity"}), ("gemini:isolation",)),
    (frozenset({"isolation", "delegation"}), ("gemini:identity",)),
])
def test_host_lacking_a_required_capability_blocks_its_roles(gemini_caps, expected_missing):
    profile = resolve(implemented={**IMPLEMENTED, "gemini": gemini_caps})
    rows = by_role(profile)
    for job in ("carl", "eve"):
        assert rows[job].missing == expected_missing
        assert rows[job].missing == tuple(sorted(rows[job].missing))
        assert rows[job].status == "blocked"
    for role in ("alice", "blake", "bob", "implementor:openai"):
        assert (rows[role].status, rows[role].missing) == ("resolved", ())
    assert profile.status == "blocked"
    assert profile.certifiable is False


def test_host_absent_from_implemented_is_not_treated_as_capable():
    implemented = {host: caps for host, caps in IMPLEMENTED.items() if host != "gemini"}
    try:
        profile = resolve(implemented=implemented)
    except (KeyError, ValueError):
        return
    rows = by_role(profile)
    for job in ("carl", "eve"):
        assert (rows[job].status, rows[job].missing) == ("blocked", ("gemini:identity", "gemini:isolation"))
    assert profile.status == "blocked"


def test_unknown_implementor_provider_never_resolves_to_a_real_host():
    profile_def = codex_gemini_variant()
    profile_def["implementor_providers"] = ["mistral"]
    policy = policy_with_profile("mistral", profile_def)
    try:
        profile = resolve(policy, profile_id="mistral", observed=FULLY_OBSERVED)
    except ValueError:
        return
    row = by_role(profile)["implementor:mistral"]
    assert row.host_id not in IMPLEMENTED
    assert row.status == "blocked"
    assert row.missing != ()
    assert profile.status == "blocked"
    assert profile.certifiable is False


def test_mandatory_job_without_a_role_binding_is_not_silently_dropped():
    profile_def = codex_gemini_variant()
    del profile_def["role_bindings"]["bob"]
    policy = policy_with_profile("no-bob", profile_def)
    try:
        profile = resolve(policy, profile_id="no-bob", observed=FULLY_OBSERVED)
    except ValueError:
        return
    bob = by_role(profile)["bob"]
    assert bob.status == "blocked"
    assert bob.missing != ()
    assert profile.status == "blocked"
    assert profile.certifiable is False


def test_unknown_adapter_is_reported_as_a_blocker():
    policy = policy_with_profile("bad-adapter", codex_gemini_variant(alice=binding("openai", "codex-cli2")))
    profile = resolve(policy, profile_id="bad-adapter")
    alice = by_role(profile)["alice"]
    assert "unknown_adapter:codex-cli2" in alice.missing
    assert alice.status == "blocked"
    assert profile.status == "blocked"


def _policy_with_unknown_predicate() -> dict:
    policy = copy.deepcopy(POLICY)
    policy["procedure"]["lanes"]["full"]["conditional_reviewer_jobs"].append(
        {"job_id": "carl", "predicate_id": "gemini_cli_present"})
    return policy


@pytest.mark.parametrize(("policy_factory", "profile_id", "lane"), [
    (lambda: POLICY, "codex-gemini2", "full"),
    (lambda: POLICY, "", "full"),
    (lambda: POLICY, "codex-gemini", "Full"),
    (lambda: POLICY, "codex-gemini", "fast"),
    (_policy_with_unknown_predicate, "codex-gemini", "full"),
], ids=["profile-near-miss", "profile-empty", "lane-case", "lane-prefix", "unknown-predicate"])
def test_unknown_profile_lane_or_predicate_raises(policy_factory, profile_id, lane):
    with pytest.raises(ValueError):
        resolve(policy_factory(), profile_id=profile_id, lane=lane)


def test_observed_codex_evidence_clears_only_codex_rows():
    profile = resolve(observed={"codex": codex.IMPLEMENTED_CAPABILITIES})
    rows = by_role(profile)
    for role in ("alice", "blake", "bob", "implementor:openai"):
        assert rows[role].unobserved == ()
    for job in ("carl", "eve"):
        assert rows[job].unobserved == ("gemini:identity", "gemini:isolation")
    assert profile.status == "resolvable"
    assert profile.certifiable is False
    assert profile.certified is False


def test_partial_observed_evidence_leaves_the_unproven_capabilities_sorted():
    rows = by_role(resolve(observed={"codex": frozenset({"identity"}), "gemini": frozenset({"isolation"})}))
    assert rows["alice"].unobserved == ("codex:isolation",)
    assert rows["implementor:openai"].unobserved == ("codex:interception", "codex:isolation")
    assert rows["carl"].unobserved == ("gemini:identity",)
    for row in rows.values():
        assert row.unobserved == tuple(sorted(row.unobserved))
        assert row.status == "resolved"


@pytest.mark.parametrize(("observed", "certifiable"), [
    ({"codex": codex.IMPLEMENTED_CAPABILITIES, "gemini": gemini.IMPLEMENTED_CAPABILITIES}, True),
    ({"codex": codex.IMPLEMENTED_CAPABILITIES, "gemini": frozenset({"identity"})}, False),
    ({}, False),
    (None, False),
], ids=["all-observed", "one-gap", "empty", "none"])
def test_certifiable_needs_every_role_observed_but_certified_stays_false(observed, certifiable):
    profile = resolve(observed=observed)
    assert profile.status == "resolvable"
    assert profile.certifiable is certifiable
    assert profile.certified is False
    if certifiable:
        assert all(row.unobserved == () for row in profile.roles)


def test_blocked_profile_is_not_certifiable_even_when_fully_observed():
    policy = policy_with_profile("claude-reviewer", codex_gemini_variant(alice=binding("openai", "native-subagent")))
    profile = resolve(policy, profile_id="claude-reviewer", observed=FULLY_OBSERVED)
    assert by_role(profile)["alice"].missing == ("claude_excluded",)
    assert all(row.unobserved == () for row in profile.roles)
    assert profile.status == "blocked"
    assert profile.certifiable is False
    assert profile.certified is False

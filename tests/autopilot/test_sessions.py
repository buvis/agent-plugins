"""Cross-host tests driving claude.py, codex.py and gemini.py together.

shared_core_without_claude proves the codex/gemini surface works end to end
with the `claude` module unimportable. codex_gemini_role_capabilities proves
review-policy-v1.json's mandatory reviewer roles can resolve to codex or
gemini (never claude alone) for the capability subsets those roles need.
"""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
CONTRACTS = ROOT / "plugins" / "autopilot" / "contracts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

hosts = importlib.import_module("hosts")
gemini = importlib.import_module("gemini")


class GeminiCapabilityContractTest(unittest.TestCase):
    """gemini.py declares identity-only capabilities in hosts.json; its
    probe() and can_delegate() must be honest about that, never claiming
    delegation/isolation/interception are available."""

    def test_probe_covers_every_capability_name(self) -> None:
        result = gemini.probe(project_root=ROOT)
        self.assertIsInstance(result, hosts.ProbeResult)
        self.assertEqual(result.host_id, "gemini")
        self.assertIsNotNone(result.capability)
        self.assertEqual(tuple(result.capability.statuses), hosts.CAPABILITY_NAMES)

    def test_identity_status_is_one_of_the_known_values(self) -> None:
        result = gemini.probe(project_root=ROOT)
        identity_status = result.capability.statuses["identity"].status
        self.assertIn(identity_status, ("available", "unavailable", "unimplemented"))

    def test_non_identity_capabilities_are_never_reported_available(self) -> None:
        result = gemini.probe(project_root=ROOT)
        for name in ("delegation", "isolation", "interception"):
            with self.subTest(capability=name):
                status = result.capability.statuses[name].status
                self.assertIn(status, ("unavailable", "unimplemented"))
                self.assertNotEqual(status, "available")

    def test_can_delegate_is_unconditionally_false(self) -> None:
        self.assertIs(gemini.can_delegate(), False)


class SharedCoreWithoutClaudeTest(unittest.TestCase):
    """Exercises hosts.probe_host, can_delegate() and build_job_argv() for
    codex and gemini with `claude` poisoned in sys.modules, so any
    accidental `import claude` in a code path under test raises
    immediately instead of silently succeeding."""

    def setUp(self) -> None:
        patcher = mock.patch.dict(sys.modules, {"claude": None})
        patcher.start()
        self.addCleanup(patcher.stop)
        self._saved_modules = {}
        for name in ("codex", "gemini"):
            self._saved_modules[name] = sys.modules.pop(name, None)
        self.addCleanup(self._restore_modules)
        self.codex = importlib.import_module("codex")
        self.gemini = importlib.import_module("gemini")

    def _restore_modules(self) -> None:
        for name, module in self._saved_modules.items():
            if module is not None:
                sys.modules[name] = module
            else:
                sys.modules.pop(name, None)

    def test_importing_claude_directly_fails(self) -> None:
        # Control case: proves the poison is effective, so the tests below
        # are a real guarantee rather than a no-op.
        with self.assertRaises(ImportError):
            importlib.import_module("claude")

    def test_probe_host_succeeds_for_codex_and_gemini(self) -> None:
        for host_id in ("codex", "gemini"):
            with self.subTest(host_id=host_id):
                result = hosts.probe_host(host_id, project_root=ROOT)
                self.assertIsInstance(result, hosts.ProbeResult)
                self.assertEqual(result.host_id, host_id)

    def test_can_delegate_succeeds_for_codex_and_gemini(self) -> None:
        self.assertIn(self.codex.can_delegate(), (True, False))
        self.assertIn(self.gemini.can_delegate(), (True, False))

    def test_build_job_argv_succeeds_for_codex_and_gemini(self) -> None:
        for adapter in (self.codex, self.gemini):
            with self.subTest(adapter=adapter.__name__):
                result = adapter.build_job_argv(None)
                self.assertTrue(result is None or isinstance(result, list))


def _resolve_candidate_hosts(required_capabilities: tuple[str, ...], hosts_declared: dict) -> list[str]:
    """Given a job's required capability names, return every host_id among
    ("codex", "gemini") whose contracts/hosts.json entry declares ALL of
    them. Lives only in this test file: it is data-plane resolution over
    the review-policy and hosts contracts, not a new production function."""
    required = set(required_capabilities)
    resolved = []
    for host_id in ("codex", "gemini"):
        declared = set(hosts_declared[host_id]["capabilities"])
        if required <= declared:
            resolved.append(host_id)
    return resolved


class CodexGeminiRoleCapabilitiesTest(unittest.TestCase):
    """review-policy-v1.json's mandatory reviewer roles must be resolvable
    to codex or gemini for the capability subsets they need; claude must
    never be the sole host contracts/hosts.json would let them use."""

    def setUp(self) -> None:
        self.policy = json.loads((CONTRACTS / "review-policy-v1.json").read_text())
        self.hosts_declared = json.loads((CONTRACTS / "hosts.json").read_text())["hosts"]

    def test_mandatory_reviewer_job_union_matches_the_policy_data(self) -> None:
        lanes = self.policy["procedure"]["lanes"]
        union: set[str] = set()
        for lane in lanes.values():
            union.update(lane["required_reviewer_jobs"])
        union.update(
            entry["job_id"] for entry in lanes["full"]["conditional_reviewer_jobs"]
        )
        self.assertEqual(union, {"alice", "blake", "bob", "carl", "eve"})

    def test_identity_only_jobs_resolve_to_codex_and_gemini(self) -> None:
        resolved = _resolve_candidate_hosts(("identity",), self.hosts_declared)
        self.assertNotEqual(resolved, [])
        self.assertIn("gemini", resolved)
        self.assertIn("codex", resolved)
        # claude is excluded from the candidate pool by construction, so a
        # non-empty result here proves claude is never the ONLY host the
        # full {claude, codex, gemini} set could offer for this subset.
        self.assertNotEqual(set(resolved), {"claude"})

    def test_identity_delegation_isolation_jobs_resolve_to_codex_only(self) -> None:
        resolved = _resolve_candidate_hosts(("identity", "delegation", "isolation"), self.hosts_declared)
        self.assertNotEqual(resolved, [])
        self.assertIn("codex", resolved)
        self.assertNotIn("gemini", resolved)
        self.assertNotEqual(set(resolved), {"claude"})

    def test_resolver_rejects_a_capability_subset_neither_host_declares(self) -> None:
        resolved = _resolve_candidate_hosts(("interception",), self.hosts_declared)
        self.assertEqual(resolved, [])

    def test_empty_required_capabilities_resolves_to_both_hosts(self) -> None:
        resolved = _resolve_candidate_hosts((), self.hosts_declared)
        self.assertEqual(set(resolved), {"codex", "gemini"})


if __name__ == "__main__":
    unittest.main()

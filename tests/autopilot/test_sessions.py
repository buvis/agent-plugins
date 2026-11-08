"""Cross-host tests driving claude.py, codex.py and gemini.py together.

shared_core_without_claude proves the codex/gemini surface works end to end
with the `claude` module unimportable. codex_gemini_role_capabilities records
which capability subsets contracts/hosts.json lets review-policy-v1.json's
mandatory reviewer roles resolve to a non-claude host: isolation resolves to
codex, and identity resolves to no non-claude host at all.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import shutil
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
CONTRACTS = ROOT / "plugins" / "autopilot" / "contracts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

hosts = importlib.import_module("hosts")
claude = importlib.import_module("claude")
codex = importlib.import_module("codex")
gemini = importlib.import_module("gemini")


class GeminiCapabilityContractTest(unittest.TestCase):
    """gemini.py implements no capability yet; its probe must say so, and must
    obey the ProbeResult invariant in both branches."""

    def test_missing_binary_yields_no_capability_and_a_recorded_reason(self) -> None:
        with mock.patch.object(shutil, "which", return_value=None):
            result = gemini.probe(project_root=ROOT)
        self.assertFalse(result.available)
        self.assertIsNone(result.capability)
        self.assertEqual(result.unavailable_reason, hosts.UNAVAILABLE_NO_BINARY)
        self.assertIsNone(result.authenticated)

    def test_present_binary_reports_every_capability_unimplemented(self) -> None:
        with mock.patch.object(shutil, "which", return_value="/usr/bin/gemini"):
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k"}, clear=True):
                result = gemini.probe(project_root=ROOT)
        self.assertTrue(result.available)
        self.assertIsNone(result.unavailable_reason)
        self.assertEqual(tuple(result.capability.statuses), hosts.CAPABILITY_NAMES)
        for name in hosts.CAPABILITY_NAMES:
            with self.subTest(capability=name):
                self.assertEqual(result.capability.statuses[name].status, "unimplemented")

    def test_auth_presence_stays_observable_even_with_no_capability_implemented(
        self,
    ) -> None:
        """Every status is "unimplemented" either way, so `authenticated` is the
        only field that records auth presence - and the PRD requires it be
        recorded."""
        with mock.patch.object(shutil, "which", return_value="/usr/bin/gemini"):
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k"}, clear=True):
                with_auth = gemini.probe(project_root=ROOT)
            with mock.patch.dict(os.environ, {}, clear=True):
                without_auth = gemini.probe(project_root=ROOT)
        self.assertIs(with_auth.authenticated, True)
        self.assertIs(without_auth.authenticated, False)

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
                with mock.patch.object(shutil, "which", return_value=f"/usr/bin/{host_id}"):
                    with mock.patch.dict(os.environ, {}, clear=True):
                        result = hosts.probe_host(host_id, project_root=ROOT)
                        again = hosts.probe_host(host_id, project_root=ROOT)
                self.assertIsInstance(result, hosts.ProbeResult)
                self.assertEqual(result.host_id, host_id)
                # A fresh probe every call, stamped now: an import-time
                # singleton frozen at 1970 would pass neither assertion.
                self.assertIsNot(result, again)
                self.assertIsNot(result.capability.statuses, again.capability.statuses)
                self.assertEqual(result.capability.statuses, again.capability.statuses)
                stamped = datetime.fromisoformat(result.probed_at)
                self.assertIsNotNone(stamped.utcoffset())
                age = abs((datetime.now(timezone.utc) - stamped).total_seconds())
                self.assertLess(age, 300)

    def test_can_delegate_succeeds_for_codex_and_gemini(self) -> None:
        self.assertIs(self.codex.can_delegate(), False)
        self.assertIs(self.gemini.can_delegate(), False)

    def test_build_job_argv_succeeds_for_codex_and_gemini(self) -> None:
        for adapter in (self.codex, self.gemini):
            with self.subTest(adapter=adapter.__name__):
                self.assertIsNone(adapter.build_job_argv(None))


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

    def test_identity_jobs_resolve_to_no_non_claude_host_which_blocks_the_claude_free_profile(
        self,
    ) -> None:
        """AP00014 implements native session identity on no non-Claude host, so
        the PRD's Claude-free profile is not certifiable yet. This is the
        explicit blocker the PRD requires, recorded rather than papered over;
        AP 00017 owns the certification that would change it."""
        self.assertEqual(_resolve_candidate_hosts(("identity",), self.hosts_declared), [])
        self.assertEqual(
            _resolve_candidate_hosts(("identity", "delegation", "isolation"), self.hosts_declared),
            [],
        )
        self.assertEqual(_resolve_candidate_hosts(("isolation",), self.hosts_declared), ["codex"])

    def test_resolver_rejects_a_capability_subset_neither_host_declares(self) -> None:
        resolved = _resolve_candidate_hosts(("interception",), self.hosts_declared)
        self.assertEqual(resolved, [])

    def test_empty_required_capabilities_resolves_to_both_hosts(self) -> None:
        resolved = _resolve_candidate_hosts((), self.hosts_declared)
        self.assertEqual(set(resolved), {"codex", "gemini"})


def _expected_status(implemented: bool, authenticated: bool) -> tuple[str, str | None]:
    """The (status, reason) pair the contract demands for one capability name."""
    if not implemented:
        return ("unimplemented", None)
    if authenticated:
        return ("supported", None)
    return ("unavailable", hosts.UNAVAILABLE_NO_AUTH)


class DeclaredCapabilitiesMatchImplementationTest(unittest.TestCase):
    ADAPTERS = (("claude", claude), ("codex", codex), ("gemini", gemini))
    EXPECTED_IMPLEMENTED = {
        "claude": {"identity", "delegation", "isolation", "interception"},
        "codex": {"isolation"},
        "gemini": set(),
    }

    def test_contract_declares_exactly_what_each_adapter_implements(self) -> None:
        """Both sides are pinned to the literal expected set, so trimming
        hosts.json down to a crippled adapter cannot make this agree; and each
        name is tied to the function that has to back it."""
        declared = json.loads((CONTRACTS / "hosts.json").read_text())["hosts"]
        with mock.patch.dict(os.environ, {"CLAUDE_SESSION_ID": "s-9"}, clear=True):
            for host_id, module in self.ADAPTERS:
                with self.subTest(host=host_id):
                    implemented = set(module.IMPLEMENTED_CAPABILITIES)
                    self.assertEqual(implemented, self.EXPECTED_IMPLEMENTED[host_id])
                    self.assertEqual(set(declared[host_id]["capabilities"]), implemented)
                    self.assertIs("delegation" in implemented, module.can_delegate())
                    self.assertIs(
                        "identity" in implemented, module.session_identity() is not None
                    )

    def test_an_inert_backing_function_keeps_its_capability_unimplemented(self) -> None:
        """A capability whose backing function cannot succeed is never declared."""
        with mock.patch.dict(os.environ, {}, clear=True):
            for host_id, module in (("codex", codex), ("gemini", gemini)):
                with self.subTest(host=host_id):
                    self.assertIsNone(module.session_identity())
                    self.assertIs(module.can_delegate(), False)
                    self.assertNotIn("identity", module.IMPLEMENTED_CAPABILITIES)
                    self.assertNotIn("delegation", module.IMPLEMENTED_CAPABILITIES)

    def test_claude_identity_is_implemented_because_it_returns_a_record(self) -> None:
        for session_id in ("s-1", "0f3c-second-session"):
            with self.subTest(session_id=session_id):
                with mock.patch.dict(
                    os.environ, {"CLAUDE_SESSION_ID": session_id}, clear=True
                ):
                    identity = claude.session_identity()
                self.assertEqual(identity["host"], "claude")
                self.assertEqual(identity["session_id"], session_id)
                self.assertEqual(identity["pid"], os.getpid())
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(claude.session_identity())
        self.assertIn("identity", claude.IMPLEMENTED_CAPABILITIES)
        self.assertIs(claude.can_delegate(), True)

    def test_no_static_probe_ever_claims_availability_or_certification(self) -> None:
        """"supported" is the strongest claim a static probe may make."""
        self.assertEqual(
            hosts.CAPABILITY_STATUSES, ("supported", "unavailable", "unimplemented")
        )
        self.assertNotIn("available", hosts.CAPABILITY_STATUSES)
        for host_id, module in self.ADAPTERS:
            implemented = set(module.IMPLEMENTED_CAPABILITIES)
            for authenticated in (True, False):
                with self.subTest(host=host_id, authenticated=authenticated):
                    statuses = hosts.statuses_from(
                        module.IMPLEMENTED_CAPABILITIES, authenticated=authenticated
                    )
                    self.assertEqual(tuple(statuses), hosts.CAPABILITY_NAMES)
                    for name in hosts.CAPABILITY_NAMES:
                        self.assertEqual(
                            (statuses[name].status, statuses[name].reason),
                            _expected_status(name in implemented, authenticated),
                        )
        with mock.patch.object(shutil, "which", return_value="/usr/bin/claude"):
            with mock.patch.dict(
                os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "t"}, clear=True
            ):
                result = claude.probe(project_root=ROOT)
        self.assertEqual(result.probe_kind, "static")
        self.assertIs(result.certified, False)


class ClaudeCodexProbeContractTest(unittest.TestCase):
    """claude.probe and codex.probe must read PATH and auth rather than assume
    them: the same branches GeminiCapabilityContractTest pins for gemini."""

    MODULES = (("claude", claude), ("codex", codex))
    AUTH_ENV = {
        "claude": {"CLAUDE_CODE_OAUTH_TOKEN": "t", "ANTHROPIC_API_KEY": "k"},
        "codex": {"CODEX_API_KEY": "k"},
    }

    def test_missing_binary_yields_no_capability_and_a_recorded_reason(self) -> None:
        for host_id, module in self.MODULES:
            with self.subTest(host=host_id):
                with mock.patch.object(shutil, "which", return_value=None):
                    with mock.patch.dict(os.environ, self.AUTH_ENV[host_id], clear=True):
                        result = module.probe(project_root=ROOT)
                self.assertFalse(result.available)
                self.assertIsNone(result.capability)
                self.assertEqual(result.unavailable_reason, hosts.UNAVAILABLE_NO_BINARY)
                self.assertIsNone(result.authenticated)

    def test_present_binary_with_auth_reports_implemented_capabilities_supported(self) -> None:
        for host_id, module in self.MODULES:
            with self.subTest(host=host_id):
                with mock.patch.object(shutil, "which", return_value=f"/usr/bin/{host_id}"):
                    with mock.patch.dict(os.environ, self.AUTH_ENV[host_id], clear=True):
                        result = module.probe(project_root=ROOT)
                self.assertTrue(result.available)
                self.assertIsNone(result.unavailable_reason)
                self.assertIs(result.authenticated, True)
                self.assertEqual(
                    result.capability.statuses,
                    hosts.statuses_from(
                        module.IMPLEMENTED_CAPABILITIES, authenticated=True
                    ),
                )

    def test_claude_without_auth_marks_every_implemented_capability_unavailable(self) -> None:
        with mock.patch.object(shutil, "which", return_value="/usr/bin/claude"):
            with mock.patch.dict(os.environ, {}, clear=True):
                result = claude.probe(project_root=ROOT)
        self.assertTrue(result.available)
        self.assertIs(result.authenticated, False)
        self.assertEqual(tuple(result.capability.statuses), hosts.CAPABILITY_NAMES)
        for name in claude.IMPLEMENTED_CAPABILITIES:
            with self.subTest(capability=name):
                status = result.capability.statuses[name]
                self.assertEqual(status.status, "unavailable")
                self.assertEqual(status.reason, hosts.UNAVAILABLE_NO_AUTH)

    def test_codex_statuses_follow_the_auth_presence_it_recorded(self) -> None:
        """codex auth also lives in a file under the user's home, which patching
        os.environ cannot clear, so bind its statuses to the auth it reports
        instead of to a machine-dependent expectation."""
        with mock.patch.object(shutil, "which", return_value="/usr/bin/codex"):
            with mock.patch.dict(os.environ, {}, clear=True):
                result = codex.probe(project_root=ROOT)
        self.assertTrue(result.available)
        self.assertIsInstance(result.authenticated, bool)
        self.assertEqual(
            result.capability.statuses,
            hosts.statuses_from(
                codex.IMPLEMENTED_CAPABILITIES, authenticated=result.authenticated
            ),
        )


class AdapterProbeSignatureTest(unittest.TestCase):
    """Every adapter takes the project it probes as a required keyword, so no
    adapter can quietly ignore project_root."""

    MODULES = (("claude", claude), ("codex", codex), ("gemini", gemini))

    def test_every_adapter_takes_project_root_as_its_only_required_keyword(self) -> None:
        for host_id, module in self.MODULES:
            with self.subTest(host=host_id):
                parameters = inspect.signature(module.probe).parameters
                self.assertEqual(tuple(parameters), ("project_root",))
                self.assertIs(parameters["project_root"].default, inspect.Parameter.empty)
                self.assertIs(
                    parameters["project_root"].kind, inspect.Parameter.KEYWORD_ONLY
                )

    def test_every_adapter_rejects_a_probe_without_a_keyword_project_root(self) -> None:
        for host_id, module in self.MODULES:
            with self.subTest(host=host_id):
                with mock.patch.object(shutil, "which", return_value=None):
                    with mock.patch.dict(os.environ, {}, clear=True):
                        with self.assertRaises(TypeError):
                            module.probe()
                        with self.assertRaises(TypeError):
                            module.probe(ROOT)


if __name__ == "__main__":
    unittest.main()

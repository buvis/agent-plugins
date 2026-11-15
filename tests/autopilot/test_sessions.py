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
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
CONTRACTS = ROOT / "plugins" / "autopilot" / "contracts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
TESTS_DIR = ROOT / "tests" / "autopilot"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

hosts = importlib.import_module("hosts")
jobs = importlib.import_module("jobs")
interception = importlib.import_module("interception")
guards = importlib.import_module("guards")
host_fakes = importlib.import_module("host_fakes")
claude = importlib.import_module("claude")
codex = importlib.import_module("codex")
gemini = importlib.import_module("gemini")

ADAPTERS = (("claude", claude), ("codex", codex), ("gemini", gemini))
EXPECTED_ARGV = {
    "claude": ["claude", "-p"],
    "codex": ["codex", "exec", "-"],
    "gemini": ["gemini", "-p", "Follow the instructions on standard input."],
}


def _which_only(binary: str):
    """A shutil.which that finds exactly `binary` and nothing else."""
    return mock.patch.object(
        shutil, "which", side_effect=lambda name, *a, **k: f"/usr/bin/{binary}" if name == binary else None
    )


def _which_all_but(binary: str):
    """A shutil.which that finds every executable except `binary`."""
    return mock.patch.object(
        shutil, "which", side_effect=lambda name, *a, **k: None if name == binary else f"/usr/bin/{name}"
    )


class GeminiCapabilityContractTest(unittest.TestCase):
    """gemini.py implements identity and isolation only; its probe must say so,
    and must obey the ProbeResult invariant in both branches."""

    def test_missing_binary_yields_no_capability_and_a_recorded_reason(self) -> None:
        with _which_all_but("gemini"):
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k"}, clear=True):
                result = gemini.probe(project_root=ROOT)
        self.assertFalse(result.available)
        self.assertIsNone(result.capability)
        self.assertEqual(result.unavailable_reason, hosts.UNAVAILABLE_NO_BINARY)
        self.assertIsNone(result.authenticated)

    def test_present_binary_supports_identity_and_isolation_only(self) -> None:
        with _which_only("gemini"):
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k"}, clear=True):
                result = gemini.probe(project_root=ROOT)
        self.assertTrue(result.available)
        self.assertIsNone(result.unavailable_reason)
        self.assertEqual(tuple(result.capability.statuses), hosts.CAPABILITY_NAMES)
        expected = {
            "identity": "supported",
            "delegation": "unimplemented",
            "isolation": "supported",
            "interception": "unimplemented",
        }
        for name, status in expected.items():
            with self.subTest(capability=name):
                self.assertEqual(result.capability.statuses[name].status, status)

    def test_auth_presence_decides_whether_identity_is_supported(self) -> None:
        with _which_only("gemini"):
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k"}, clear=True):
                with_auth = gemini.probe(project_root=ROOT)
            unauthenticated = []
            # An unrelated variable is not auth: "any env var set" must not count.
            for env in ({}, {"PATH": "/bin"}):
                with mock.patch.dict(os.environ, env, clear=True):
                    unauthenticated.append(gemini.probe(project_root=ROOT))
        self.assertIs(with_auth.authenticated, True)
        self.assertEqual(with_auth.capability.statuses["identity"].status, "supported")
        for without_auth in unauthenticated:
            self.assertIs(without_auth.authenticated, False)
            identity = without_auth.capability.statuses["identity"]
            self.assertEqual((identity.status, identity.reason), ("unavailable", hosts.UNAVAILABLE_NO_AUTH))

    def test_can_delegate_is_unconditionally_false(self) -> None:
        self.assertIs(gemini.can_delegate(), False)


class SharedCoreWithoutClaudeTest(unittest.TestCase):
    """Exercises hosts.probe_host, identity, jobs, interception, can_delegate()
    and build_job_argv() for codex and gemini with `claude` poisoned in
    sys.modules, so any accidental `import claude` in a code path under test
    raises immediately instead of silently succeeding."""

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
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = host_fakes.make_project(temp.name)

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
                with _which_only(host_id):
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
        for host_id, adapter in (("codex", self.codex), ("gemini", self.gemini)):
            with self.subTest(host=host_id):
                requester = adapter.session_from_environment({adapter.SESSION_ENV_VAR: "req-1"})
                request = host_fakes.build(self.root, host_id=host_id, requester=requester)
                self.assertEqual(adapter.build_job_argv(request), EXPECTED_ARGV[host_id])

    def test_identity_and_isolation_bind_codex_and_gemini_jobs(self) -> None:
        for host_id, adapter in (("codex", self.codex), ("gemini", self.gemini)):
            with self.subTest(host=host_id):
                var = adapter.SESSION_ENV_VAR
                requester = adapter.session_from_environment({var: "req-1"})
                request = host_fakes.build(self.root, host_id=host_id, requester=requester)
                with self.assertRaises(jobs.JobRefused) as caught:
                    jobs.bind_job_session(
                        request.to_payload(),
                        child=adapter.session_from_environment({var: "req-1"}),
                        project_root=self.root,
                    )
                self.assertEqual(caught.exception.code, "same_session")
                record = jobs.bind_job_session(
                    request.to_payload(),
                    child=adapter.session_from_environment({var: "child-2"}),
                    project_root=self.root,
                )
                self.assertEqual(record["child_session"]["session_id"], "child-2")
                self.assertEqual(record["child_session"]["host_id"], host_id)

    def test_codex_interception_decides_and_replies_without_claude(self) -> None:
        for command, allowed in (("mv backlog/x.md wip/", False), ("ls docs", True)):
            with self.subTest(command=command):
                payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "<repo>"}
                decision = interception.evaluate_hook(
                    "codex", "PreToolUse", payload, env={"CODEX_SESSION_ID": "cx-7"}, seam=None
                )
                self.assertIs(decision.allowed, allowed)
                self.assertEqual(decision.session, hosts.NativeSession("codex", "cx-7", "environment"))
                reply = self.codex.render_hook_reply("PreToolUse", decision, stop_active=False)
                self.assertEqual(reply.exit_code, 0)
                self.assertIs('"deny"' in reply.stdout, not allowed)

    def test_codex_translates_every_non_bash_event_without_claude(self) -> None:
        session_id = f"cx-{uuid.uuid4().hex}"
        self.assertEqual(
            self.codex.session_from_hook_input({"session_id": session_id, "cwd": "/r"}),
            hosts.NativeSession("codex", session_id, "hook_input"),
        )
        base = {"session_id": session_id, "cwd": "/r"}
        patch = "*** Begin Patch\n*** Add File: docs/a.md\n+x\n*** End Patch\n"
        table = (
            ("Stop", base, ["departure", "live_job", "review_completeness"]),
            ("SessionStart", {**base, "source": "compact"}, ["context_reinjection"]),
            ("PostToolUse", {**base, "tool_name": "apply_patch", "tool_input": {"patch": patch}},
             ["state_integrity"]),
        )
        for event, payload, duties in table:
            with self.subTest(event=event):
                calls = self.codex.translate_hook(event, payload)
                self.assertEqual(sorted({call.duty.value for call in calls}), duties)

    def test_codex_renders_every_non_bash_reply_without_claude(self) -> None:
        def decision(event: str, allowed: bool, context: str | None = None):
            outcome = guards.GuardOutcome(duty=guards.GuardDuty.LIVE_JOB, allowed=allowed,
                                          reason=None if allowed else "lane L9 live", stateful=False)
            return interception.HookDecision(
                host_id="codex", event=event, session=None, project_root="/r", bound=True,
                outcomes=(outcome,), skipped=(), allowed=allowed, additional_context=context,
            )

        def body(reply) -> dict:
            self.assertEqual(reply.exit_code, 0)
            return json.loads(reply.stdout) if reply.stdout.strip() else {}

        stop = body(self.codex.render_hook_reply("Stop", decision("Stop", False), stop_active=False))
        self.assertEqual(stop["decision"], "block")
        self.assertIn("lane L9 live", stop["reason"])
        start = body(self.codex.render_hook_reply(
            "SessionStart", decision("SessionStart", True, "card body"), stop_active=False))
        self.assertEqual(start["hookSpecificOutput"]["additionalContext"], "card body")
        post = body(self.codex.render_hook_reply("PostToolUse", decision("PostToolUse", False), stop_active=False))
        self.assertEqual(post["decision"], "block")
        self.assertIn("lane L9 live", post["reason"])


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

    def test_identity_jobs_resolve_to_a_non_claude_host_now_that_hosts_json_declares_it(
        self,
    ) -> None:
        """AP00014 task 7 regenerates contracts/hosts.json from each adapter's
        own IMPLEMENTED_CAPABILITIES, which already include identity for codex
        and gemini (task 6). "declared" is still never "certified" -
        hosts.json's capabilities carry no probe result, so a reader needing
        a live guarantee still waits on AP 00017's certification - but the
        claude-free profile is no longer blocked on the contract alone."""
        self.assertEqual(
            set(_resolve_candidate_hosts(("identity",), self.hosts_declared)), {"codex", "gemini"}
        )
        self.assertEqual(
            _resolve_candidate_hosts(("identity", "delegation", "isolation"), self.hosts_declared),
            [],
        )
        self.assertEqual(
            set(_resolve_candidate_hosts(("isolation",), self.hosts_declared)), {"codex", "gemini"}
        )

    def test_resolver_rejects_a_capability_subset_neither_host_declares(self) -> None:
        # delegation is claude-only (claude.py's in-session Agent-tool
        # dispatch); neither codex nor gemini declares it.
        resolved = _resolve_candidate_hosts(("delegation",), self.hosts_declared)
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
    EXPECTED_IMPLEMENTED = {
        "claude": {"identity", "delegation", "isolation", "interception"},
        "codex": {"identity", "isolation", "interception"},
        "gemini": {"identity", "isolation"},
    }
    EXPECTED_ENV_VAR = {
        "claude": "CLAUDE_CODE_SESSION_ID",
        "codex": "CODEX_SESSION_ID",
        "gemini": "GEMINI_SESSION_ID",
    }

    def test_each_adapter_implements_exactly_its_contract_capabilities(self) -> None:
        """Pinned to the literal expected set; hosts.json may lag behind an
        adapter but must never claim a capability the adapter lacks."""
        declared = json.loads((CONTRACTS / "hosts.json").read_text())["hosts"]
        for host_id, module in ADAPTERS:
            with self.subTest(host=host_id):
                self.assertEqual(module.HOST_ID, host_id)
                self.assertIsInstance(module.IMPLEMENTED_CAPABILITIES, frozenset)
                self.assertEqual(set(module.IMPLEMENTED_CAPABILITIES), self.EXPECTED_IMPLEMENTED[host_id])
                self.assertEqual(set(declared[host_id]["capabilities"]), self.EXPECTED_IMPLEMENTED[host_id])
                self.assertEqual(module.SESSION_ENV_VAR, self.EXPECTED_ENV_VAR[host_id])
                self.assertIs("delegation" in module.IMPLEMENTED_CAPABILITIES, module.can_delegate())

    def test_identity_reads_each_hosts_own_env_var(self) -> None:
        for host_id, module in ADAPTERS:
            for session_id in ("s-1", "0f3c-second-session"):
                with self.subTest(host=host_id, session_id=session_id):
                    session = module.session_from_environment({module.SESSION_ENV_VAR: session_id})
                    self.assertEqual(session, hosts.NativeSession(host_id, session_id, "environment"))
            with self.subTest(host=host_id, case="other hosts' vars only"):
                others = {var: "s-x" for other, var in self.EXPECTED_ENV_VAR.items() if other != host_id}
                self.assertIsNone(module.session_from_environment(others))
                self.assertIsNone(module.session_from_environment({}))
            with self.subTest(host=host_id, case="process env never leaks in"):
                with mock.patch.dict(os.environ, {module.SESSION_ENV_VAR: "leak"}):
                    self.assertIsNone(module.session_from_environment({}))
                    self.assertIsNone(module.session_from_environment(others))

    def test_claude_identity_reads_claude_code_session_id(self) -> None:
        session = claude.session_from_environment({"CLAUDE_CODE_SESSION_ID": "cc-42"})
        self.assertEqual(session, hosts.NativeSession("claude", "cc-42", "environment"))
        # The v1 variable is a near miss and no longer counts.
        self.assertIsNone(claude.session_from_environment({"CLAUDE_SESSION_ID": "cc-42"}))
        # The env argument is the source: a process env never leaks in.
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "leak"}, clear=True):
            self.assertIsNone(claude.session_from_environment({}))
        self.assertEqual(hosts.current_session("claude", {"CLAUDE_CODE_SESSION_ID": "cc-43"}).session_id, "cc-43")

    def test_identity_returns_none_for_an_id_native_session_rejects(self) -> None:
        rejected = ("", "a\x07b", "a\x7fb", "x" * 257, "é" * 129)
        for host_id, module in ADAPTERS:
            for value in rejected:
                with self.subTest(host=host_id, length=len(value)):
                    self.assertIsNone(module.session_from_environment({module.SESSION_ENV_VAR: value}))
            with self.subTest(host=host_id, case="256-byte boundary is accepted"):
                session = module.session_from_environment({module.SESSION_ENV_VAR: "x" * 256})
                self.assertEqual(session.session_id, "x" * 256)

    def test_hook_input_identity_reads_the_payload_session_id(self) -> None:
        for host_id, module in (("claude", claude), ("codex", codex)):
            for session_id in ("hook-1", "11111111-2222-3333-4444-555555555555"):
                with self.subTest(host=host_id, session_id=session_id):
                    session = module.session_from_hook_input({"session_id": session_id, "cwd": "/r"})
                    self.assertEqual(session, hosts.NativeSession(host_id, session_id, "hook_input"))
            with self.subTest(host=host_id, case="absent or empty"):
                self.assertIsNone(module.session_from_hook_input({"cwd": "/r"}))
                self.assertIsNone(module.session_from_hook_input({"session_id": "", "cwd": "/r"}))
        self.assertFalse(hasattr(gemini, "session_from_hook_input"))

    def test_interception_is_declared_only_with_registrations_and_hook_functions(self) -> None:
        for host_id, module in ADAPTERS:
            with self.subTest(host=host_id):
                declared = "interception" in module.IMPLEMENTED_CAPABILITIES
                self.assertIs(bool(getattr(module, "HOOK_REGISTRATIONS", ())), declared)
                for name in ("translate_hook", "render_hook_reply", "session_from_hook_input"):
                    self.assertIs(callable(getattr(module, name, None)), declared)
        self.assertEqual(gemini.INTERCEPTION_BLOCKER, "no_package_local_registration_surface")

    def test_hook_registrations_are_exactly_the_contract_tables(self) -> None:
        reg = interception.HookRegistration
        self.assertEqual(claude.HOOK_REGISTRATIONS, (
            reg("PreToolUse", "Edit|Write|MultiEdit", 5),
            reg("PreToolUse", "Bash", 10),
            reg("PreToolUse", "Skill", 5),
            reg("PreToolUse", "Agent", 5),
            reg("PostToolUse", "Edit|Write|MultiEdit", 5),
            reg("Stop", None, 10),
            reg("SessionStart", "compact|resume", 5),
        ))
        self.assertEqual(codex.HOOK_REGISTRATIONS, (
            reg("PreToolUse", "Bash", 10),
            reg("PreToolUse", "apply_patch", 5),
            reg("PostToolUse", "apply_patch", 5),
            reg("Stop", None, 10),
            reg("SessionStart", None, 5),
        ))

    def test_gemini_exports_an_explicit_empty_hook_registrations_tuple(self) -> None:
        # Not a getattr(..., ()) default: the module itself must declare it,
        # the same way claude and codex declare their own non-empty tuples.
        self.assertIn("HOOK_REGISTRATIONS", vars(gemini))
        self.assertEqual(gemini.HOOK_REGISTRATIONS, ())

    def test_no_static_probe_ever_claims_availability_or_certification(self) -> None:
        """"supported" is the strongest claim a static probe may make."""
        self.assertEqual(
            hosts.CAPABILITY_STATUSES, ("supported", "unavailable", "unimplemented")
        )
        self.assertNotIn("available", hosts.CAPABILITY_STATUSES)
        for host_id, module in ADAPTERS:
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


class IsolationAndJobArgvTest(host_fakes.ProjectCase):
    """isolation: identity plus a bind that refuses the requester's own
    session; build_job_argv: a fixed argv that never carries tier or effort."""

    def _request(self, host_id: str, module, session_id: str, **override):
        requester = module.session_from_environment({module.SESSION_ENV_VAR: session_id})
        return host_fakes.build(self.root, host_id=host_id, requester=requester, **override)

    def test_isolation_refuses_a_child_that_reuses_the_requester_session(self) -> None:
        for host_id, module in ADAPTERS:
            with self.subTest(host=host_id):
                self.assertIn("identity", module.IMPLEMENTED_CAPABILITIES)
                self.assertIn("isolation", module.IMPLEMENTED_CAPABILITIES)
                payload = self._request(host_id, module, "req-1").to_payload()
                var = module.SESSION_ENV_VAR
                self.assert_refused(
                    "same_session", jobs.bind_job_session, payload,
                    child=module.session_from_environment({var: "req-1"}), project_root=self.root,
                )
                record = jobs.bind_job_session(
                    payload, child=module.session_from_environment({var: "req-2"}), project_root=self.root
                )
                self.assertEqual(record["child_session"],
                                 {"host_id": host_id, "session_id": "req-2", "source": "environment"})

    def test_build_job_argv_is_the_hosts_fixed_argv(self) -> None:
        for host_id, module in ADAPTERS:
            with self.subTest(host=host_id):
                low = self._request(host_id, module, "req-1", tier="haiku", effort="low")
                high = self._request(host_id, module, "req-1", tier="opus", effort="max", job_id="bob-review")
                argv = module.build_job_argv(low)
                self.assertIsInstance(argv, list)
                self.assertEqual(argv, EXPECTED_ARGV[host_id])
                self.assertEqual(module.build_job_argv(high), EXPECTED_ARGV[host_id])
                for out_of_band in ("haiku", "low", "opus", "max", "req-1", "bob-review"):
                    # Whole tokens: gemini's fixed prompt "Follow ..." merely contains "low".
                    self.assertNotIn(out_of_band, argv)


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
                with _which_all_but(host_id):
                    with mock.patch.dict(os.environ, self.AUTH_ENV[host_id], clear=True):
                        result = module.probe(project_root=ROOT)
                self.assertFalse(result.available)
                self.assertIsNone(result.capability)
                self.assertEqual(result.unavailable_reason, hosts.UNAVAILABLE_NO_BINARY)
                self.assertIsNone(result.authenticated)

    def test_present_binary_with_auth_reports_implemented_capabilities_supported(self) -> None:
        # Each auth variable on its own must authenticate.
        for host_id, module in self.MODULES:
            for var in self.AUTH_ENV[host_id]:
                with self.subTest(host=host_id, auth=var):
                    with _which_only(host_id):
                        with mock.patch.dict(os.environ, {var: "t"}, clear=True):
                            result = module.probe(project_root=ROOT)
                    self._assert_supported(module, result)

    def _assert_supported(self, module, result) -> None:
        self.assertTrue(result.available)
        self.assertIsNone(result.unavailable_reason)
        self.assertIs(result.authenticated, True)
        self.assertEqual(
            result.capability.statuses,
            hosts.statuses_from(module.IMPLEMENTED_CAPABILITIES, authenticated=True),
        )

    def test_claude_without_auth_marks_every_implemented_capability_unavailable(self) -> None:
        # An unrelated variable is not auth: "any env var set" must not count.
        for env in ({}, {"PATH": "/bin"}):
            with _which_only("claude"):
                with mock.patch.dict(os.environ, env, clear=True):
                    result = claude.probe(project_root=ROOT)
            self.assertTrue(result.available)
            self.assertIs(result.authenticated, False, env)
            self.assertEqual(tuple(result.capability.statuses), hosts.CAPABILITY_NAMES)
            for name in claude.IMPLEMENTED_CAPABILITIES:
                with self.subTest(env=env, capability=name):
                    status = result.capability.statuses[name]
                    self.assertEqual(status.status, "unavailable")
                    self.assertEqual(status.reason, hosts.UNAVAILABLE_NO_AUTH)

    def test_codex_statuses_follow_the_auth_presence_it_recorded(self) -> None:
        """codex auth also lives in a file under the user's home, which patching
        os.environ cannot clear, so bind its statuses to the auth it reports
        instead of to a machine-dependent expectation."""
        with _which_only("codex"):
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

    MODULES = ADAPTERS

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

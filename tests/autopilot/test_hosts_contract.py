"""hosts.py design §1 contract: registry tables, CapabilityStatus and NativeSession
invariants, adapter() resolution, and current_session() delegation."""

from __future__ import annotations

import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

hosts = importlib.import_module("hosts")

HOST_IDS = ("claude", "codex", "gemini")
NEAR_MISSES = (
    "claudex", "Claude", "", "codex ", "gemini2", "laude", "CODEX",
    "anthropic", "native-subagent", "codex-cli",
)
VALID_PAIRS = (
    ("supported", None),
    ("unimplemented", None),
    ("unavailable", "no_binary"),
    ("unavailable", "no_auth"),
)


def _session(**override) -> object:
    fields = {"host_id": "claude", "session_id": "sess-1", "source": "environment"}
    return hosts.NativeSession(**{**fields, **override})


class RegistryTablesTest(unittest.TestCase):
    def test_adapters_maps_each_host_to_its_sibling_module_name(self) -> None:
        self.assertIsInstance(hosts.ADAPTERS, dict)
        self.assertEqual(
            hosts.ADAPTERS, {"claude": "claude", "codex": "codex", "gemini": "gemini"}
        )

    def test_provider_hosts_maps_each_provider_to_one_host(self) -> None:
        self.assertIsInstance(hosts.PROVIDER_HOSTS, dict)
        self.assertEqual(
            hosts.PROVIDER_HOSTS,
            {"anthropic": "claude", "openai": "codex", "google": "gemini"},
        )

    def test_adapter_kinds_maps_review_adapters_to_host_and_execution(self) -> None:
        self.assertIsInstance(hosts.ADAPTER_KINDS, dict)
        self.assertEqual(
            hosts.ADAPTER_KINDS,
            {
                "native-subagent": ("claude", "in-session"),
                "native-fallback": ("claude", "in-session"),
                "review-fanout-workflow": ("claude", "in-session"),
                "codex-cli": ("codex", "cross-session"),
                "gemini-cli": ("gemini", "cross-session"),
            },
        )
        for kind, value in hosts.ADAPTER_KINDS.items():
            with self.subTest(kind=kind):
                self.assertIsInstance(value, tuple)

    def test_session_sources_are_environment_then_hook_input(self) -> None:
        self.assertIsInstance(hosts.SESSION_SOURCES, tuple)
        self.assertEqual(hosts.SESSION_SOURCES, ("environment", "hook_input"))


class CapabilityStatusInvariantTest(unittest.TestCase):
    def assert_rejected_naming(self, field: str, **kwargs) -> None:
        # Control: a valid status of the same shape must construct, so a
        # __post_init__ that always raises cannot pass.
        hosts.CapabilityStatus(name="identity", status="supported", reason=None)
        with self.assertRaises(ValueError) as caught:
            hosts.CapabilityStatus(**kwargs)
        self.assertIn(field, str(caught.exception))

    def test_accepts_every_valid_name_status_reason_combination(self) -> None:
        for name in hosts.CAPABILITY_NAMES:
            for status, reason in VALID_PAIRS:
                with self.subTest(name=name, status=status, reason=reason):
                    built = hosts.CapabilityStatus(name=name, status=status, reason=reason)
                    self.assertEqual((built.name, built.status, built.reason), (name, status, reason))

    def test_rejects_a_name_outside_capability_names(self) -> None:
        for name in ("identities", "Identity", "", "ident", "isolation ", "intercept"):
            with self.subTest(name=name):
                self.assert_rejected_naming("name", name=name, status="supported", reason=None)

    def test_rejects_a_status_outside_capability_statuses(self) -> None:
        for status in ("available", "Supported", "", "unsupported", "unavailable2"):
            with self.subTest(status=status):
                self.assert_rejected_naming("status", name="delegation", status=status, reason=None)

    def test_rejects_an_unavailable_status_without_an_allowed_reason(self) -> None:
        for reason in (None, "no_bin", "no_auth ", "auth", "", "NO_BINARY"):
            with self.subTest(reason=reason):
                self.assert_rejected_naming(
                    "reason", name="isolation", status="unavailable", reason=reason
                )

    def test_rejects_a_reason_on_any_status_other_than_unavailable(self) -> None:
        for status in ("supported", "unimplemented"):
            for reason in ("no_binary", "no_auth", "because"):
                with self.subTest(status=status, reason=reason):
                    self.assert_rejected_naming(
                        "reason", name="interception", status=status, reason=reason
                    )


class NativeSessionInvariantTest(unittest.TestCase):
    def assert_rejected_naming(self, field: str, **override) -> None:
        _session()  # control: the baseline constructs
        with self.assertRaises(ValueError) as caught:
            _session(**override)
        self.assertIn(field, str(caught.exception))

    def test_accepts_every_host_source_and_boundary_session_id(self) -> None:
        session_ids = ("a", "sess-1", "0f9e" * 64, "é" * 128, "会話-42")
        for host_id in HOST_IDS:
            for source in ("environment", "hook_input"):
                for session_id in session_ids:
                    with self.subTest(host_id=host_id, source=source, session_id=session_id):
                        built = _session(host_id=host_id, session_id=session_id, source=source)
                        self.assertEqual(
                            (built.host_id, built.session_id, built.source),
                            (host_id, session_id, source),
                        )

    def test_rejects_a_host_id_outside_adapters(self) -> None:
        for host_id in NEAR_MISSES:
            with self.subTest(host_id=host_id):
                self.assert_rejected_naming("host_id", host_id=host_id)

    def test_rejects_an_empty_session_id(self) -> None:
        self.assert_rejected_naming("session_id", session_id="")

    def test_rejects_a_session_id_over_256_utf8_bytes(self) -> None:
        for session_id in ("x" * 257, "é" * 128 + "a", "会" * 86):
            with self.subTest(length=len(session_id.encode("utf-8"))):
                self.assert_rejected_naming("session_id", session_id=session_id)

    def test_rejects_a_session_id_with_an_ascii_control_character(self) -> None:
        for session_id in ("\x00", "abc\x00", "a\tb", "sess\n", "\x1fsess", "s\x7fs", "\rx"):
            with self.subTest(session_id=session_id):
                self.assert_rejected_naming("session_id", session_id=session_id)

    def test_rejects_a_source_outside_session_sources(self) -> None:
        for source in ("environ", "Environment", "hook", "hook_input ", "", "env", "hook-input"):
            with self.subTest(source=source):
                self.assert_rejected_naming("source", source=source)


class AdapterResolutionTest(unittest.TestCase):
    def test_resolves_each_host_to_its_sibling_module(self) -> None:
        for host_id in HOST_IDS:
            with self.subTest(host_id=host_id):
                module = hosts.adapter(host_id)
                self.assertIsInstance(module, types.ModuleType)
                self.assertIs(module, importlib.import_module(host_id))
                self.assertEqual(
                    Path(module.__file__).resolve(), (SCRIPTS / f"{host_id}.py").resolve()
                )
        self.assertIsNot(hosts.adapter("claude"), hosts.adapter("codex"))

    def test_imports_the_module_named_by_the_adapters_entry(self) -> None:
        with mock.patch.dict(hosts.ADAPTERS, {"claude": "codex", "nope": "gemini"}):
            self.assertIs(hosts.adapter("claude"), importlib.import_module("codex"))
            self.assertIs(hosts.adapter("nope"), importlib.import_module("gemini"))

    def test_rejects_a_host_removed_from_adapters(self) -> None:
        with mock.patch.dict(hosts.ADAPTERS, {"claude": "claude"}, clear=True):
            self.assertIs(hosts.adapter("claude"), importlib.import_module("claude"))
            with self.assertRaises(ValueError) as caught:
                hosts.adapter("gemini")
        self.assertEqual(str(caught.exception), "unknown host_id: 'gemini'")

    def test_unknown_host_id_raises_before_any_module_is_imported(self) -> None:
        planted = ("nope", "claudex", "gemini2", "laude", "anthropic")
        with tempfile.TemporaryDirectory() as raw:
            plant_dir = Path(raw) / "plant"
            marks = Path(raw) / "marks"
            plant_dir.mkdir()
            marks.mkdir()
            for name in planted:
                (plant_dir / f"{name}.py").write_text(
                    f"open({str(marks / name)!r}, 'w').close()\n", encoding="utf-8"
                )
            real_import = importlib.import_module
            with mock.patch.object(sys, "path", [str(plant_dir), *sys.path]), \
                    mock.patch.dict(sys.modules), \
                    mock.patch.object(importlib, "import_module", wraps=real_import) as spy:
                for host_id in (*planted, *NEAR_MISSES):
                    with self.subTest(host_id=host_id):
                        with self.assertRaises(ValueError) as caught:
                            hosts.adapter(host_id)
                        self.assertEqual(str(caught.exception), f"unknown host_id: {host_id!r}")
                self.assertEqual(spy.call_args_list, [])
            self.assertEqual(sorted(marks.iterdir()), [])


class CurrentSessionDelegationTest(unittest.TestCase):
    def install(self, returns: dict) -> list:
        calls: list = []

        def fake_adapter(host_id: str) -> object:
            calls.append(("adapter", host_id))

            def session_from_environment(env):
                calls.append(("session_from_environment", host_id, env))
                outcome = returns[host_id]
                if isinstance(outcome, BaseException):
                    raise outcome
                return outcome

            return types.SimpleNamespace(session_from_environment=session_from_environment)

        patcher = mock.patch.object(hosts, "adapter", fake_adapter)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def test_forwards_host_id_and_env_and_returns_the_result_unchanged(self) -> None:
        claude_session = _session(host_id="claude", session_id="c-1", source="environment")
        codex_session = _session(host_id="codex", session_id="x-2", source="hook_input")
        returns = {"claude": claude_session, "codex": codex_session, "gemini": None}
        envs = {
            "claude": {"CLAUDE_SESSION": "c-1", "PATH": "/bin"},
            "codex": {"CODEX_THREAD": "x-2"},
            "gemini": {},
        }
        for host_id in HOST_IDS:
            with self.subTest(host_id=host_id):
                calls = self.install(returns)
                result = hosts.current_session(host_id, envs[host_id])
                self.assertIs(result, returns[host_id])
                self.assertEqual(
                    calls,
                    [("adapter", host_id), ("session_from_environment", host_id, envs[host_id])],
                )
                self.assertIs(calls[1][2], envs[host_id])

    def test_propagates_an_adapter_session_error(self) -> None:
        failure = RuntimeError("env unreadable")
        self.install({"codex": failure})
        with self.assertRaises(RuntimeError) as caught:
            hosts.current_session("codex", {"A": "1"})
        self.assertIs(caught.exception, failure)

    def test_unknown_host_id_raises_value_error(self) -> None:
        for host_id in ("nope", "claudex", ""):
            with self.subTest(host_id=host_id):
                with self.assertRaises(ValueError) as caught:
                    hosts.current_session(host_id, {"CLAUDE_SESSION": "c-1"})
                self.assertEqual(str(caught.exception), f"unknown host_id: {host_id!r}")


if __name__ == "__main__":
    unittest.main()

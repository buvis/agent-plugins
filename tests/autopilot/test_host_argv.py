"""probe_host dispatches by host_id through the _ADAPTERS table and passes adapter results through unchanged."""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

hosts = importlib.import_module("hosts")

HOST_IDS = ("claude", "codex", "gemini")
NEAR_MISSES = ("claudex", "Claude", "", "codex ", "gemini2", "laude", "CODEX")
PROJECT_ROOTS = {
    "claude": Path("/tmp/project-alpha"),
    "codex": Path("/tmp/project-beta"),
    "gemini": Path("/tmp/project-gamma"),
}
PROBED_AT = {
    "claude": "2026-11-08T10:00:00+00:00",
    "codex": "2026-11-08T11:30:00+00:00",
    "gemini": "2026-11-07T23:59:59+00:00",
}
EVIDENCE_PATHS = {
    "claude": "docs/dev/tmp/evidence/claude.json",
    "codex": "docs/dev/tmp/evidence/codex.json",
    "gemini": None,
}


def _status(name: str, status: str, reason: str | None) -> object:
    return hosts.CapabilityStatus(name=name, status=status, reason=reason)


def _statuses_for(host_id: str) -> dict:
    """Two distinct per-host capability maps so a hardcoded map cannot pass."""
    if host_id == "claude":
        rows = {
            "identity": ("available", None),
            "delegation": ("available", None),
            "isolation": ("unavailable", hosts.UNAVAILABLE_NO_AUTH),
            "interception": ("unimplemented", None),
        }
    else:
        rows = {
            "identity": ("unavailable", hosts.UNAVAILABLE_NO_BINARY),
            "delegation": ("unimplemented", None),
            "isolation": ("available", None),
            "interception": ("available", None),
        }
    return {name: _status(name, *rows[name]) for name in hosts.CAPABILITY_NAMES}


def _available_result(host_id: str) -> object:
    capability = hosts.HostCapability(host_id=host_id, statuses=_statuses_for(host_id))
    return hosts.ProbeResult(
        host_id=host_id,
        available=True,
        capability=capability,
        probed_at=PROBED_AT[host_id],
        evidence_path=EVIDENCE_PATHS[host_id],
    )


def _unavailable_result(host_id: str) -> object:
    return hosts.ProbeResult(
        host_id=host_id,
        available=False,
        capability=None,
        probed_at=PROBED_AT[host_id],
        evidence_path=EVIDENCE_PATHS[host_id],
    )


class FakeAdapters:
    """Keyword-only fake probe functions that record every call and return a prebuilt ProbeResult."""

    def __init__(self, results: dict) -> None:
        self.results = results
        self.calls: list[tuple[str, dict]] = []

    def table(self) -> dict:
        return {host_id: self._make(host_id) for host_id in self.results}

    def _make(self, host_id: str):
        def fake_probe(*, project_root):
            self.calls.append((host_id, {"project_root": project_root}))
            outcome = self.results[host_id]
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome

        return fake_probe


class ProbeHostDispatchTest(unittest.TestCase):
    def install(self, results: dict) -> FakeAdapters:
        fakes = FakeAdapters(results)
        patcher = mock.patch.object(hosts, "_ADAPTERS", fakes.table())
        patcher.start()
        self.addCleanup(patcher.stop)
        return fakes

    def install_all_available(self) -> FakeAdapters:
        return self.install({host_id: _available_result(host_id) for host_id in HOST_IDS})

    def test_probe_host_calls_only_the_adapter_matching_host_id(self) -> None:
        for host_id in HOST_IDS:
            with self.subTest(host_id=host_id):
                fakes = self.install_all_available()
                hosts.probe_host(host_id, project_root=PROJECT_ROOTS[host_id])
                self.assertEqual([call[0] for call in fakes.calls], [host_id])

    def test_probe_host_forwards_project_root_as_keyword_unchanged(self) -> None:
        for host_id in HOST_IDS:
            with self.subTest(host_id=host_id):
                fakes = self.install_all_available()
                root = PROJECT_ROOTS[host_id]
                hosts.probe_host(host_id, project_root=root)
                self.assertEqual(len(fakes.calls), 1)
                received = fakes.calls[0][1]["project_root"]
                self.assertIs(received, root)
                self.assertEqual(received, root)

    def test_probe_host_forwards_distinct_roots_on_successive_calls(self) -> None:
        fakes = self.install_all_available()
        first = Path("/srv/one")
        second = Path("/srv/two")
        hosts.probe_host("codex", project_root=first)
        hosts.probe_host("codex", project_root=second)
        self.assertEqual([call[1]["project_root"] for call in fakes.calls], [first, second])

    def test_probe_host_returns_the_adapter_result_object_unmodified(self) -> None:
        for host_id in HOST_IDS:
            with self.subTest(host_id=host_id):
                expected = _available_result(host_id)
                self.install({h: (expected if h == host_id else _available_result(h)) for h in HOST_IDS})
                result = hosts.probe_host(host_id, project_root=PROJECT_ROOTS[host_id])
                self.assertIs(result, expected)
                self.assertEqual(result.host_id, host_id)
                self.assertEqual(result.probed_at, PROBED_AT[host_id])
                self.assertEqual(result.evidence_path, EVIDENCE_PATHS[host_id])

    def test_available_result_preserves_each_capability_status(self) -> None:
        for host_id in HOST_IDS:
            with self.subTest(host_id=host_id):
                self.install_all_available()
                result = hosts.probe_host(host_id, project_root=PROJECT_ROOTS[host_id])
                self.assertTrue(result.available)
                self.assertEqual(result.capability.host_id, host_id)
                self.assertEqual(result.capability.statuses, _statuses_for(host_id))
                self.assertEqual(tuple(result.capability.statuses), hosts.CAPABILITY_NAMES)

    def test_available_statuses_differ_between_hosts_as_reported(self) -> None:
        self.install_all_available()
        claude = hosts.probe_host("claude", project_root=PROJECT_ROOTS["claude"])
        codex = hosts.probe_host("codex", project_root=PROJECT_ROOTS["codex"])
        self.assertEqual(claude.capability.statuses["isolation"].status, "unavailable")
        self.assertEqual(claude.capability.statuses["isolation"].reason, hosts.UNAVAILABLE_NO_AUTH)
        self.assertEqual(codex.capability.statuses["isolation"].status, "available")
        self.assertIsNone(codex.capability.statuses["isolation"].reason)
        self.assertEqual(codex.capability.statuses["identity"].reason, hosts.UNAVAILABLE_NO_BINARY)
        self.assertEqual(codex.capability.statuses["delegation"].status, "unimplemented")
        self.assertIsNone(codex.capability.statuses["delegation"].reason)

    def test_unavailable_result_has_no_capability(self) -> None:
        for host_id in HOST_IDS:
            with self.subTest(host_id=host_id):
                expected = _unavailable_result(host_id)
                self.install({h: (expected if h == host_id else _available_result(h)) for h in HOST_IDS})
                result = hosts.probe_host(host_id, project_root=PROJECT_ROOTS[host_id])
                self.assertIs(result, expected)
                self.assertFalse(result.available)
                self.assertIsNone(result.capability)
                self.assertEqual(result.probed_at, PROBED_AT[host_id])

    def test_unknown_host_id_raises_value_error_without_calling_any_adapter(self) -> None:
        for host_id in NEAR_MISSES:
            with self.subTest(host_id=host_id):
                fakes = self.install_all_available()
                with self.assertRaises(ValueError) as caught:
                    hosts.probe_host(host_id, project_root=PROJECT_ROOTS["claude"])
                self.assertIn("unknown host_id", str(caught.exception))
                self.assertEqual(fakes.calls, [])

    def test_unknown_host_id_message_names_the_rejected_id(self) -> None:
        self.install_all_available()
        with self.assertRaises(ValueError) as caught:
            hosts.probe_host("claudex", project_root=PROJECT_ROOTS["claude"])
        self.assertIn("claudex", str(caught.exception))

    def test_dispatch_uses_the_adapter_table_not_a_fixed_host_list(self) -> None:
        fakes = self.install({"codex": _available_result("codex")})
        with self.assertRaises(ValueError) as caught:
            hosts.probe_host("claude", project_root=PROJECT_ROOTS["claude"])
        self.assertIn("unknown host_id", str(caught.exception))
        self.assertEqual(fakes.calls, [])
        result = hosts.probe_host("codex", project_root=PROJECT_ROOTS["codex"])
        self.assertEqual(result.host_id, "codex")
        self.assertEqual([call[0] for call in fakes.calls], ["codex"])

    def test_empty_adapter_table_rejects_every_host_id(self) -> None:
        self.install({})
        for host_id in HOST_IDS:
            with self.subTest(host_id=host_id):
                with self.assertRaises(ValueError) as caught:
                    hosts.probe_host(host_id, project_root=PROJECT_ROOTS[host_id])
                self.assertIn("unknown host_id", str(caught.exception))

    def test_adapter_exception_propagates_to_the_caller(self) -> None:
        failure = RuntimeError("probe exploded")
        fakes = self.install({"claude": _available_result("claude"), "gemini": failure})
        with self.assertRaises(RuntimeError) as caught:
            hosts.probe_host("gemini", project_root=PROJECT_ROOTS["gemini"])
        self.assertIs(caught.exception, failure)
        self.assertEqual([call[0] for call in fakes.calls], ["gemini"])


if __name__ == "__main__":
    unittest.main()

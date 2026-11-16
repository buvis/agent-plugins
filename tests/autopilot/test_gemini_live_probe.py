"""Gemini has no local hook-registration surface, so its live probe is a pair
of hook-free `--record-session` launches whose own minted session ids - not a
hook trace - decide identity and isolation; interception and resources, which
need a registration surface gemini cannot offer, are always `not_observed`
with a reason naming that missing surface."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from probe_host_support import install_fake_hosts
from test_host_argv import PROBES_REL, _probe_env, _run_probe

MISSING_SURFACE_REASON = "no_package_local_registration_surface"
NOT_OBSERVED_MISSING_SURFACE = {"status": "not_observed", "reason": MISSING_SURFACE_REASON}
NOT_IMPLEMENTED = {"status": "not_observed", "reason": "capability_not_implemented"}
OBSERVED = {"status": "observed", "reason": None}


class GeminiProbeCase(unittest.TestCase):
    """Real probe runs against the fake `gemini`. Holds no tests of its own."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        install_fake_hosts(self.bin_dir)

    def _run(self, mode: str, *, timeout: str = "30", **env_extra: str) -> dict:
        project_root = Path(tempfile.mkdtemp(dir=self.root, prefix=f"project-{mode}-")).resolve()
        log = self.root / f"{project_root.name}.calls.jsonl"
        env = _probe_env(
            PATH=f"{self.bin_dir}{os.pathsep}{os.environ['PATH']}",
            FAKE_HOST_LOG=str(log), FAKE_HOST_MODE=mode, FAKE_FOREIGN_ROOT=str(self.root),
            **env_extra,
        )
        completed = _run_probe("gemini", project_root, "--timeout", timeout, cwd=self.root, env=env)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        probes_dir = project_root / PROBES_REL
        files = [path for path in probes_dir.iterdir() if path.is_file()]
        self.assertEqual(len(files), 1, files)
        self.project_root = project_root
        self.calls = (
            [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
            if log.exists() else []
        )
        return json.loads(files[0].read_text(encoding="utf-8"))


class GeminiLiveProbeTest(GeminiProbeCase):
    def test_live_gemini_probe_is_accepted_when_a_binary_is_on_path(self) -> None:
        record = self._run("honest")
        self.assertEqual(record["static"]["host_id"], "gemini")
        self.assertIs(record["certified"], False)

    def test_live_gemini_probe_is_still_rejected_without_a_binary_on_path(self) -> None:
        project_root = self.root / "no-binary"
        project_root.mkdir()
        env = _probe_env(PATH="/usr/bin:/bin")
        completed = _run_probe("gemini", project_root, "--timeout", "30", cwd=self.root, env=env)
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(sorted(project_root.rglob("*.json")), [])

    def test_live_gemini_probe_derives_identity_and_isolation_from_session_ids_only(self) -> None:
        cases = (
            ("honest", OBSERVED, OBSERVED),
            ("same_session", OBSERVED, {"status": "not_observed", "reason": "session_reused"}),
        )
        for mode, identity, isolation in cases:
            with self.subTest(mode=mode):
                observed = self._run(mode)["observed"]
                self.assertEqual(observed["identity"], identity)
                self.assertEqual(observed["isolation"], isolation)
                self.assertEqual(observed["delegation"], NOT_IMPLEMENTED)
                for capability in ("interception", "resources"):
                    self.assertEqual(observed[capability], NOT_OBSERVED_MISSING_SURFACE, capability)

    def test_live_gemini_probe_launches_exactly_two_record_session_invocations(self) -> None:
        record = self._run("honest")
        invocations = record["invocations"]
        self.assertEqual(len(invocations), 2, invocations)
        for invocation in invocations:
            self.assertEqual(invocation["argv"][:2], ["gemini", "-p"], invocation["argv"])
            self.assertEqual((invocation["exit_code"], invocation["timed_out"]), (0, False))


if __name__ == "__main__":
    unittest.main()

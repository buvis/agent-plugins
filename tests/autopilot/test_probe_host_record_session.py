"""The probe's recorded session id comes from a real `--record-session` run
(`record_command`, `recorded_session`), never from the prompt echoed back by
the host, and the gemini live verdict ladder checks invocation outcomes before
it reasons about session ids, deciding identity and isolation independently."""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from probe_host_support import FAKE_HANG_SECONDS
from test_gemini_live_probe import (
    NOT_OBSERVED_MISSING_SURFACE,
    OBSERVED,
    GeminiProbeCase,
)

ROOT = Path(__file__).resolve().parents[2]
PROBE_HOST_PATH = ROOT / "tools" / "autopilot" / "probe-host.py"
TRACE_REL = Path("docs") / "dev" / "tmp" / "autopilot" / "hook-trace.jsonl"
CAPABILITIES = ("identity", "delegation", "isolation", "interception", "resources")


def _load_probe_host():
    spec = importlib.util.spec_from_file_location("probe_host_under_test_record", PROBE_HOST_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record_object(host_id: str, session_id: str | None, **overrides: object) -> str:
    session = (
        None if session_id is None
        else {"host_id": host_id, "session_id": session_id, "source": "env"}
    )
    return json.dumps(
        {"schema_version": 1, "host_id": host_id, "session": session,
         "plugin_root": "/p", "traced": True} | overrides
    )


class RecordCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.module = _load_probe_host()

    def test_record_command_is_the_shlex_join_of_the_explicit_argument_list(self) -> None:
        cases = (
            (self.root / "run-a" / "plugin", "gemini", self.root / "run-a" / "work"),
            (self.root / "run-b" / "plugin", "claude", self.root / "run-b" / "control"),
        )
        for plugin, host_id, cwd in cases:
            with self.subTest(host_id=host_id):
                expected = [
                    sys.executable, str(plugin / "scripts" / "autopilot.py"),
                    "--record-session", host_id, "--project-root", str(cwd),
                ]
                command = self.module.record_command(plugin, host_id, cwd)
                self.assertEqual(command, shlex.join(expected))
                self.assertEqual(shlex.split(command), expected)
                self.assertNotIn("\n", command)

    def test_record_command_names_the_cwd_it_is_given_as_project_root(self) -> None:
        plugin = self.root / "plugin"
        first = shlex.split(self.module.record_command(plugin, "gemini", self.root / "one"))
        second = shlex.split(self.module.record_command(plugin, "gemini", self.root / "two"))
        self.assertEqual(first[-1], str(self.root / "one"))
        self.assertEqual(second[-1], str(self.root / "two"))
        self.assertEqual(first[:-1], second[:-1])

    def _echo_plugin(self, plugin: Path) -> None:
        script = plugin / "scripts" / "autopilot.py"
        script.parent.mkdir(parents=True)
        script.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")

    def test_record_command_runs_the_same_argv_through_a_shell_for_hostile_paths(self) -> None:
        hostile = "sp ace;touch PWNED;$(touch PWNED2)`touch PWNED3`'\"&|>x"
        plugin = self.root / hostile / "plugin"
        cwd = self.root / f"cwd {hostile}"
        cwd.mkdir()
        self._echo_plugin(plugin)
        command = self.module.record_command(plugin, "gemini", cwd)
        done = subprocess.run(["sh", "-c", command], cwd=self.root, capture_output=True,
                              text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(
            json.loads(done.stdout),
            ["--record-session", "gemini", "--project-root", str(cwd)],
        )
        self.assertEqual(sorted(self.root.glob("PWNED*")), [])
        self.assertEqual(sorted(cwd.glob("PWNED*")), [])

    def test_record_command_quotes_an_interpreter_path_that_contains_a_space(self) -> None:
        wrapper = self.root / "py thon dir" / "python"
        wrapper.parent.mkdir()
        wrapper.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n", encoding="utf-8")
        wrapper.chmod(0o755)
        plugin = self.root / "plugin"
        self._echo_plugin(plugin)
        with mock.patch.object(sys, "executable", str(wrapper)):
            command = self.module.record_command(plugin, "codex", self.root)
        self.assertEqual(shlex.split(command)[0], str(wrapper))
        done = subprocess.run(["sh", "-c", command], capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)[:2], ["--record-session", "codex"])


class RecordedSessionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_probe_host()

    def test_recorded_session_returns_the_session_id_of_the_record_object(self) -> None:
        for session_id in ("abc123", "f00dfeed" * 4):
            with self.subTest(session_id=session_id):
                text = _record_object("gemini", session_id) + "\n"
                self.assertEqual(self.module.recorded_session(text), session_id)

    def test_recorded_session_takes_the_last_record_object_in_the_text(self) -> None:
        text = "\n".join(
            [_record_object("gemini", "first"), "noise line", _record_object("gemini", "second")]
        )
        self.assertEqual(self.module.recorded_session(text), "second")

    def test_recorded_session_skips_trailing_json_that_is_not_a_record_object(self) -> None:
        trailer = json.dumps({"result": "ok", "session_id": "host-own-id"})
        other_schema = _record_object("gemini", "wrong-schema", schema_version=2)
        text = "\n".join([_record_object("gemini", "real"), other_schema, trailer])
        self.assertEqual(self.module.recorded_session(text), "real")

    def test_recorded_session_is_none_when_the_last_record_object_has_no_session(self) -> None:
        text = "\n".join([_record_object("gemini", "earlier"), _record_object("gemini", None)])
        self.assertIsNone(self.module.recorded_session(text))

    def test_recorded_session_is_none_for_a_prompt_echo_and_for_empty_text(self) -> None:
        echoes = (
            "", "\n", "--record-session gemini-0", "Probe tag: --record-session gemini-1\n",
            json.dumps({"result": "x", "session_id": "gemini-0"}),
            json.dumps({"schema_version": 2, "host_id": "gemini", "session": None}),
            json.dumps({"schema_version": 1, "session": {"session_id": "no-host-key"}}),
        )
        for text in echoes:
            with self.subTest(text=text):
                self.assertIsNone(self.module.recorded_session(text))


class GeminiRecordSessionRunTest(GeminiProbeCase):
    def test_gemini_probe_names_each_launches_own_cwd_in_its_record_command(self) -> None:
        record = self._run("honest")
        run_dir = (self.project_root / record["run_dir"]).resolve()
        self.assertEqual(len(self.calls), 2)
        for call in self.calls:
            argv = shlex.split(call["record_command"])
            self.assertEqual(argv[2:4], ["--record-session", "gemini"], argv)
            self.assertEqual(argv[4], "--project-root")
            self.assertEqual(os.path.realpath(argv[5]), os.path.realpath(call["cwd"]))
            self.assertEqual(
                Path(argv[1]).resolve(), run_dir / "plugin" / "scripts" / "autopilot.py"
            )

    def test_gemini_probe_identity_trace_lands_in_each_launch_cwd_without_hooks(self) -> None:
        self._run("honest")
        self.assertEqual(len({call["session"] for call in self.calls}), 2)
        for call in self.calls:
            trace = Path(os.path.realpath(call["cwd"])) / TRACE_REL
            self.assertTrue(trace.is_file(), trace)
            lines = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines() if line]
            self.assertIn(call["session"], {line.get("session_id") for line in lines})

    def test_gemini_probe_never_reads_a_session_id_out_of_an_echoed_prompt(self) -> None:
        for mode in ("echo_marker", "no_record"):
            with self.subTest(mode=mode):
                observed = self._run(mode)["observed"]
                self.assertEqual(
                    observed["identity"], {"status": "not_observed", "reason": "session_not_traced"}
                )
                self.assertEqual(
                    observed["isolation"], {"status": "not_observed", "reason": "identity_not_observed"}
                )
                self.assertEqual(observed["interception"], NOT_OBSERVED_MISSING_SURFACE)
                self.assertEqual(observed["resources"], NOT_OBSERVED_MISSING_SURFACE)

    def test_gemini_probe_reports_identity_observed_when_both_launches_reuse_one_id(self) -> None:
        observed = self._run("same_session")["observed"]
        self.assertEqual(observed["identity"], OBSERVED)
        self.assertEqual(
            observed["isolation"], {"status": "not_observed", "reason": "session_reused"}
        )

    def test_gemini_probe_observes_identity_and_isolation_for_two_distinct_ids(self) -> None:
        observed = self._run("honest")["observed"]
        self.assertEqual((observed["identity"], observed["isolation"]), (OBSERVED, OBSERVED))
        self.assertEqual(len({call["session"] for call in self.calls}), 2)


class GeminiVerdictLadderTest(GeminiProbeCase):
    def assert_every_capability(self, record: dict, reason: str) -> None:
        for capability in CAPABILITIES:
            self.assertEqual(
                record["observed"][capability],
                {"status": "not_observed", "reason": reason}, capability,
            )
        self.assertTrue(record["invocations"])
        self.assertEqual(record["registration_surface"], "none")
        self.assertEqual((record["trace_lines"], record["resource_check"]), (0, "not_run"))

    def test_gemini_probe_reports_no_auth_for_a_non_zero_exit_with_an_auth_message(self) -> None:
        messages = (
            "Error: Not logged in", "NOT AUTHENTICATED", "Authentication failed: retry",
            "authentication required", "401 Unauthorized", "Invalid API key provided",
        )
        for stream in ("stderr", "stdout"):
            for message in messages:
                with self.subTest(stream=stream, message=message):
                    record = self._run("auth_fail", FAKE_AUTH_MESSAGE=message, FAKE_AUTH_STREAM=stream)
                    self.assert_every_capability(record, "no_auth")

    def test_gemini_probe_reports_host_failed_for_a_non_zero_exit_without_an_auth_message(self) -> None:
        messages = ("Quota exceeded for authenticated user", "Error: logged in elsewhere")
        record = self._run("fail")
        self.assert_every_capability(record, "host_failed")
        self.assertEqual({invocation["exit_code"] for invocation in record["invocations"]}, {1})
        for message in messages:
            with self.subTest(message=message):
                record = self._run("auth_fail", FAKE_AUTH_MESSAGE=message)
                self.assert_every_capability(record, "host_failed")

    def test_gemini_probe_reports_host_timed_out_and_kills_a_hung_host(self) -> None:
        started = time.monotonic()
        record = self._run("hang", timeout="2")
        self.assertLess(time.monotonic() - started, FAKE_HANG_SECONDS - 10)
        self.assert_every_capability(record, "host_timed_out")
        self.assertEqual({invocation["timed_out"] for invocation in record["invocations"]}, {True})

    def test_gemini_probe_checks_the_exit_code_before_any_session_id_reasoning(self) -> None:
        """The host recorded two real session ids, then died: the failure wins."""
        record = self._run("fail_after_record")
        self.assertEqual(len({call["session"] for call in self.calls}), 2)
        self.assert_every_capability(record, "host_failed")


if __name__ == "__main__":
    unittest.main()

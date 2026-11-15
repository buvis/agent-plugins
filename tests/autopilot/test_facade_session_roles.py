"""The facade's --resolve-roles and --record-session modes, and the rules shared by
all five job, child, role and session modes, driven only through the CLI."""

from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from facade_modes_support import STATE_TREE, FacadeModesMixin, snapshot


PROFILES = ("source-parity", "codex-gemini")
FACTS_FALSE = {"gemini_cli_available": False, "doubt_reviewer": None, "implementor_codex_present": False}
FACTS_GEMINI = FACTS_FALSE | {"gemini_cli_available": True}
SESSIONS = {"CLAUDE_CODE_SESSION_ID": "sess-claude-1", "CODEX_SESSION_ID": "sess-codex-2",
            "GEMINI_SESSION_ID": "sess-gemini-3"}
RECORD_KEYS = {"schema_version", "host_id", "session", "plugin_root", "traced"}
TRACE_DIR = Path("docs") / "dev" / "tmp" / "autopilot"


class RoleAndSessionModesTest(FacadeModesMixin, unittest.TestCase):
    def facts(self, value: object) -> Path:
        return self.write_json(self.base / "facts" / f"{uuid.uuid4().hex}.json", value)

    def resolve(self, profile: str, lane: str, *extra: str):
        return self.run_facade("--resolve-roles", "--profile", profile, "--lane", lane, *extra)

    def resolved(self, result) -> dict:
        self.assertIn(result.returncode, (0, 1), result.stderr.decode(errors="replace"))
        reply = self.one_json(result)
        self.assertEqual(reply["status"], {0: "resolvable", 1: "blocked"}[result.returncode])
        self.assertIsInstance(reply["roles"], list)
        return reply

    def record(self, host: str, project: Path, env: dict | None = None) -> dict:
        result = self.run_facade("--record-session", host, "--project-root", str(project), env=env)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        reply = self.one_json(result)
        self.assertEqual(set(reply), RECORD_KEYS)
        self.assertEqual((reply["schema_version"], reply["host_id"]), (1, host))
        self.assertIsInstance(reply["plugin_root"], str)
        self.assertTrue(reply["plugin_root"])
        return reply

    def project(self, name: str = "project") -> Path:
        project = self.base / name
        (project / TRACE_DIR).mkdir(parents=True)
        return project

    def test_resolve_roles_reports_each_real_profile_and_lane(self) -> None:
        for profile in PROFILES:
            counts = {}
            for lane in ("full", "solo"):
                with self.subTest(profile=profile, lane=lane):
                    reply = self.resolved(self.resolve(profile, lane))
                    self.assertEqual((reply["profile_id"], reply["lane"]), (profile, lane))
                    counts[lane] = len(reply["roles"])
            self.assertGreater(counts["full"], counts["solo"])
            self.assertGreater(counts["solo"], 0)
        self.assertEqual(self.resolve("codex-gemini", "full").returncode, 0)

    def test_resolve_roles_defaults_equal_all_false_facts(self) -> None:
        false_file, gemini_file = self.facts(FACTS_FALSE), self.facts(FACTS_GEMINI)
        for profile in PROFILES:
            for lane in ("full", "fast-track", "solo"):
                with self.subTest(profile=profile, lane=lane):
                    default = self.resolve(profile, lane)
                    explicit = self.resolve(profile, lane, "--facts", str(false_file))
                    self.resolved(default)
                    self.assertEqual((explicit.returncode, explicit.stdout),
                                     (default.returncode, default.stdout))
                    # The facts file reaches resolution: Gemini adds Carl wherever the lane
                    # makes him conditional, and solo has no conditional reviewer.
                    gemini = self.resolve(profile, lane, "--facts", str(gemini_file))
                    roles_on = self.resolved(gemini)["roles"]
                    roles_off = json.loads(default.stdout)["roles"]
                    if lane == "solo":
                        self.assertEqual(gemini.stdout, default.stdout)
                    else:
                        self.assertGreater(len(roles_on), len(roles_off))

    def test_resolve_roles_rejects_unknown_profile_lane_or_facts_as_usage_error(self) -> None:
        bad_facts = self.base / "facts" / "broken.json"
        bad_facts.parent.mkdir(parents=True)
        bad_facts.write_bytes(b"{")
        cases = [("--profile", profile, "--lane", "full")
                 for profile in ("codex-gemini-x", "codex", "Source-Parity", "")]
        cases += [("--profile", "codex-gemini", "--lane", lane) for lane in ("ful", "fullx", "Full", "")]
        cases += [("--profile", "codex-gemini"),
                  ("--profile", "codex-gemini", "--lane", "full", "--facts", str(bad_facts))]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                self.assert_usage_error(self.run_facade("--resolve-roles", *arguments))
        self.resolved(self.resolve("codex-gemini", "full"))

    def test_record_session_reports_no_session_without_the_host_variable(self) -> None:
        project = self.project()
        for host, env in (("claude", {"CODEX_SESSION_ID": "sess-codex-2", "GEMINI_SESSION_ID": "g",
                                      "CLAUDE_SESSION_ID": "near-miss"}),
                          ("codex", {"CLAUDE_CODE_SESSION_ID": "sess-claude-1", "CODEX_SESSION": "near"}),
                          ("gemini", {})):
            with self.subTest(host=host):
                reply = self.record(host, project, env)
                self.assertEqual((reply["session"], reply["traced"]), (None, False))

    def test_record_session_reports_the_host_own_session(self) -> None:
        project = self.project()
        for host, env, expected in (
            ("claude", SESSIONS, "sess-claude-1"), ("codex", SESSIONS, "sess-codex-2"),
            ("gemini", SESSIONS, "sess-gemini-3"),
            ("claude", {"CLAUDE_CODE_SESSION_ID": "sess-claude-solo"}, "sess-claude-solo"),
        ):
            with self.subTest(host=host, expected=expected):
                session = self.record(host, project, env)["session"]
                self.assertIsInstance(session, dict)
                self.assertIn(expected, session.values())
                text = json.dumps(session)
                for other in set(SESSIONS.values()) - {expected}:
                    self.assertNotIn(f'"{other}"', text)

    def test_record_session_traces_only_when_hook_trace_is_set(self) -> None:
        project = self.project()
        trace_dir = project / TRACE_DIR
        for env in ({}, {"AUTOPILOT_HOOK_TRACES": str(trace_dir / "near.jsonl")}):
            with self.subTest(env=env):
                self.assertIs(self.record("claude", project, env)["traced"], False)
                self.assertEqual(list(trace_dir.iterdir()), [])
        for host, name in (("claude", "session.jsonl"), ("codex", "session.jsonl"),
                           ("gemini", "other.jsonl")):
            trace = trace_dir / name
            with self.subTest(host=host, trace=name):
                reply = self.record(host, project, {"AUTOPILOT_HOOK_TRACE": str(trace)})
                self.assertIs(reply["traced"], True)
                lines = trace.read_text(encoding="utf-8").splitlines()
                self.assertTrue(lines)
                last = json.loads(lines[-1])
                self.assertEqual((last["event"], last["host_id"]), ("record_session", host))
        self.assertEqual(sorted(path.name for path in trace_dir.iterdir()),
                         ["other.jsonl", "session.jsonl"])

    def test_record_session_rejects_unknown_host_or_missing_root_as_usage_error(self) -> None:
        project = self.project()
        for host in ("claudex", "Claude", "anthropic", "codex-cli", ""):
            with self.subTest(host=host):
                self.assert_usage_error(self.run_facade("--record-session", host,
                                                        "--project-root", str(project)))
        self.assert_usage_error(self.run_facade("--record-session", "claude"))
        self.assert_usage_error(self.run_facade("--record-session", "--project-root", str(project)))
        self.record("claude", project)

    def test_new_modes_refuse_a_second_mode_flag(self) -> None:
        project = self.project()
        spec, out = self.facts({}), project / "job.json"
        root = ("--project-root", str(project))
        resolve = ("--resolve-roles", "--profile", "codex-gemini", "--lane", "full")
        for arguments in (
            ("--request-job", str(spec), "--bind-job", str(spec), *root, "--out", str(out)),
            ("--bind-job", str(spec), "--close-child", str(spec), *root),
            ("--close-child", str(spec), "--record-session", "claude", *root),
            ("--record-session", "claude", *resolve, *root),
            (*resolve, "--export-policy"), (*resolve, "--request-job", str(spec), "--out", str(out), *root),
            ("--request-job", str(spec), "--diagnose", *root, "--out", str(out)),
            ("--record-session", "claude", "--list-capabilities", *root),
            ("--bind-job", str(spec), "--hook", "claude", "--event", "Stop", *root),
        ):
            with self.subTest(arguments=arguments):
                result = self.run_facade(*arguments, env={"CLAUDE_CODE_SESSION_ID": "parent-alpha"})
                self.assert_usage_error(result)
                self.assertFalse(out.exists())
        # Each mode alone parses: the refusals above come from the pairing.
        self.record("codex", project)
        self.resolved(self.run_facade(*resolve))

    def test_request_job_out_never_writes_live_autopilot_state(self) -> None:
        project = self.project()
        (project / "docs" / "prd.md").write_text("# PRD\n", encoding="utf-8")
        spec = self.facts({"schema_version": 1, "job_id": "job-alpha", "role_id": "alice",
                           "host_id": "claude", "tier": "opus", "effort": "high",
                           "inputs": [{"kind": "prd", "path": "docs/prd.md"}],
                           "excluded_input_kinds": []})
        env = {"CLAUDE_CODE_SESSION_ID": "requester-session"}

        def request(out: Path):
            return self.run_facade("--request-job", str(spec), "--project-root", str(project),
                                   "--out", str(out), env=env)

        state = project / STATE_TREE
        self.assertNotEqual(request(state / "job.json").returncode, 0)
        self.assertFalse(state.exists())
        state.mkdir(parents=True)
        (state / "state.json").write_bytes(b"live state")
        before = snapshot(state)
        for out in (state / "job.json", state / "jobs" / "job.json"):
            with self.subTest(out=out):
                self.assertNotEqual(request(out).returncode, 0)
                self.assertEqual(snapshot(state), before)
        sibling = state.with_name("autopilot-notes")
        sibling.mkdir()
        self.assertEqual(request(sibling / "job.json").returncode, 0)
        self.assertTrue((sibling / "job.json").is_file())

    def test_resolve_roles_facts_never_read_from_live_autopilot_state(self) -> None:
        default = self.resolve("codex-gemini", "full")
        root = self.base / "facts root"
        state_facts = self.write_json(root / STATE_TREE / "facts.json", FACTS_FALSE)
        before = snapshot(root)
        result = self.resolve("codex-gemini", "full", "--facts", str(state_facts))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(snapshot(root), before)
        sibling = self.write_json(root / STATE_TREE.with_name("autopilot-archive") / "facts.json",
                                  FACTS_FALSE)
        accepted = self.resolve("codex-gemini", "full", "--facts", str(sibling))
        self.resolved(accepted)
        self.assertEqual((accepted.returncode, accepted.stdout), (default.returncode, default.stdout))


if __name__ == "__main__":
    unittest.main()

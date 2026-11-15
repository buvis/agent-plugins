"""The facade's --request-job, --bind-job and --close-child modes, driven only through the CLI."""

from __future__ import annotations

import copy
import json
import os
import unittest
import uuid
from pathlib import Path

from facade_modes_support import MISSING_SESSION, FacadeModesMixin, snapshot


JOB_A = {"schema_version": 1, "job_id": "job-alpha", "role_id": "alice", "host_id": "claude",
         "tier": "opus", "effort": "high",
         "inputs": [{"kind": "prd", "path": "docs/prd.md"},
                    {"kind": "diff", "path": "docs/change.diff"}],
         "excluded_input_kinds": []}
JOB_B = {"schema_version": 1, "job_id": "job-beta", "role_id": "bob", "host_id": "codex",
         "tier": "haiku", "effort": "low", "inputs": [], "excluded_input_kinds": []}
CHILD_A = {"schema_version": 1,
           "child": {"child_id": "child-alpha", "kind": "in-session",
                     "parent_session_id": "parent-alpha", "depth": 1},
           "outcome": "completed", "artifact_path": "out/child-alpha.bin"}
CHILD_B = {"schema_version": 1,
           "child": {"child_id": "child-beta", "kind": "in-session",
                     "parent_session_id": "parent-beta", "depth": 0},
           "outcome": "failed", "artifact_path": "child-beta.txt"}
REQUESTER = {"CLAUDE_CODE_SESSION_ID": "requester-session"}


def malformed_jobs() -> list[dict]:
    """JOB_A with one missing key, one extra key or one invalid field value."""
    jobs = []
    for key in JOB_A:
        missing = dict(JOB_A)
        del missing[key]
        jobs.append(missing)
    jobs += [JOB_A | {"extra": True}, JOB_A | {"request_id": "0" * 64}]
    for key, values in (("host_id", ("claudex", "claud", "Claude", "anthropic")),
                        ("tier", ("opus4", "Opus", "op")), ("effort", ("hi", "highest", "")),
                        ("inputs", ("docs/prd.md", {"kind": "prd", "path": "docs/prd.md"}, None)),
                        ("schema_version", (2, "1"))):
        jobs += [JOB_A | {key: value} for value in values]
    return jobs


def malformed_children() -> list[dict]:
    """CHILD_A with one missing key, an extra key, a wrong kind or a non-string child_id."""
    children = []
    for key in ("outcome", "artifact_path", "child"):
        missing = copy.deepcopy(CHILD_A)
        del missing[key]
        children.append(missing)
    for key in ("depth", "kind", "child_id", "parent_session_id"):
        missing = copy.deepcopy(CHILD_A)
        del missing["child"][key]
        children.append(missing)
    for key, value in (("kind", "in-session-x"), ("kind", "cross-session"), ("kind", "In-Session"),
                       ("child_id", 7), ("child_id", None)):
        changed = copy.deepcopy(CHILD_A)
        changed["child"][key] = value
        children.append(changed)
    return [*children, CHILD_A | {"extra": True}]


class JobModesTest(FacadeModesMixin, unittest.TestCase):
    def make_project(self, name: str) -> Path:
        project = self.base / name
        (project / "docs").mkdir(parents=True)
        (project / "docs" / "prd.md").write_text("# PRD\n", encoding="utf-8")
        (project / "docs" / "change.diff").write_text("--- a\n+++ b\n", encoding="utf-8")
        (project / "out").mkdir()
        return project

    def spec(self, value: object) -> Path:
        return self.write_json(self.base / "specs" / f"{uuid.uuid4().hex}.json", value)

    def request(self, project: Path, job: object, env: dict, out_name: str = "job.json"):
        out = project / out_name
        result = self.run_facade("--request-job", str(self.spec(job)), "--project-root", str(project),
                                 "--out", str(out), env=env)
        return result, out

    def make_job(self, project: Path, job: dict, out_name: str) -> Path:
        result, out = self.request(project, job, REQUESTER, out_name)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        return out

    def bind(self, project: Path, job_file: Path, env: dict):
        return self.run_facade("--bind-job", str(job_file), "--project-root", str(project), env=env)

    def close(self, project: Path, request: object, env: dict, stdin: bytes):
        return self.run_facade("--close-child", str(self.spec(request)), "--project-root", str(project),
                               env=env, stdin=stdin)

    def assert_not_ok(self, result) -> None:
        self.assertEqual(result.returncode, 1, result.stderr.decode(errors="replace"))
        self.assertIs(self.one_json(result)["ok"], False)

    def test_request_job_refuses_without_a_native_session_variable(self) -> None:
        project = self.make_project("project")
        for env in ({}, {"CLAUDE_SESSION_ID": "s"}, {"CLAUDE_CODE_SESSION": "s"},
                    {"CODEX_SESSION": "s"}, {"GEMINI_SESSION_IDS": "s"}):
            with self.subTest(env=env):
                result, out = self.request(project, JOB_A, env)
                self.assert_refusal(result, "missing_native_session")
                self.assertEqual(self.one_json(result), MISSING_SESSION)
                self.assertFalse(out.exists())

    def test_request_job_writes_the_payload_for_the_first_set_session_variable(self) -> None:
        cases = (
            (JOB_A, {"CLAUDE_CODE_SESSION_ID": "requester-claude", "CODEX_SESSION_ID": "requester-codex",
                     "GEMINI_SESSION_ID": "requester-gemini"}, "requester-claude"),
            (JOB_B, {"CODEX_SESSION_ID": "requester-codex", "GEMINI_SESSION_ID": "requester-gemini"},
             "requester-codex"),
            (JOB_A, {"GEMINI_SESSION_ID": "requester-gemini-2"}, "requester-gemini-2"),
        )
        all_ids = {"requester-claude", "requester-codex", "requester-gemini", "requester-gemini-2"}
        for index, (job, env, requester) in enumerate(cases):
            with self.subTest(job=job["job_id"], requester=requester):
                result, out = self.request(self.make_project(f"project {index}"), job, env)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                reply = self.one_json(result)
                self.assertEqual((reply["schema_version"], reply["mode"]), (1, "standalone"))
                text = out.read_text(encoding="utf-8")
                payload = json.loads(text)
                self.assertIsInstance(payload["request_id"], str)
                self.assertTrue(payload["request_id"])
                fields = ("job_id", "role_id", "host_id", "tier", "effort")
                self.assertEqual([payload[key] for key in fields], [job[key] for key in fields])
                self.assertEqual([(item["kind"], item["path"]) for item in payload["inputs"]],
                                 [(item["kind"], item["path"]) for item in job["inputs"]])
                self.assertIn(f'"{requester}"', text)
                for other in all_ids - {requester}:
                    self.assertNotIn(f'"{other}"', text)
        self.assertEqual(list(self.cwd.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_request_job_never_overwrites_an_existing_out_file(self) -> None:
        project = self.make_project("project")
        (project / "job.json.previous").write_bytes(b"sibling sharing the prefix")
        result, out = self.request(project, JOB_A, REQUESTER)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        first = out.read_bytes()
        (project / "taken.json").write_bytes(b"foreign file")
        for job, out_name, kept in ((JOB_A, "job.json", first), (JOB_B, "job.json", first),
                                    (JOB_B, "taken.json", b"foreign file")):
            with self.subTest(job=job["job_id"], out=out_name):
                result, out = self.request(project, job, REQUESTER, out_name)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr.strip())
                self.assertEqual(out.read_bytes(), kept)
        self.assertEqual((project / "job.json.previous").read_bytes(), b"sibling sharing the prefix")

    def test_request_job_rejects_a_malformed_request_as_usage_error(self) -> None:
        project = self.make_project("project")
        for job in malformed_jobs():
            with self.subTest(job=job):
                result, out = self.request(project, job, REQUESTER)
                self.assert_usage_error(result)
                self.assertFalse(out.exists())
        result, out = self.request(project, JOB_A, REQUESTER)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))

    def test_request_job_requires_project_root_and_out(self) -> None:
        project = self.make_project("project")
        spec, out = str(self.spec(JOB_A)), project / "job.json"
        for arguments in (("--request-job", spec, "--out", str(out)),
                          ("--request-job", spec, "--project-root", str(project)),
                          ("--request-job", "--project-root", str(project), "--out", str(out))):
            with self.subTest(arguments=arguments):
                self.assert_usage_error(self.run_facade(*arguments, env=REQUESTER))
                self.assertFalse(out.exists())
        result = self.run_facade("--request-job", spec, "--project-root", str(project),
                                 "--out", str(out), env=REQUESTER)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertTrue(out.is_file())

    def test_bind_job_refuses_an_absent_or_other_host_session(self) -> None:
        project = self.make_project("project")
        job_a = self.make_job(project, JOB_A, "job-a.json")
        job_b = self.make_job(project, JOB_B, "job-b.json")
        refused = (
            (job_a, {}), (job_a, {"CODEX_SESSION_ID": "child-session"}),
            (job_a, {"GEMINI_SESSION_ID": "child-session"}), (job_a, {"CLAUDE_SESSION_ID": "child-session"}),
            (job_b, {}), (job_b, {"CLAUDE_CODE_SESSION_ID": "child-session"}),
            (job_b, {"GEMINI_SESSION_ID": "child-session"}), (job_b, {"CODEX_SESSION": "child-session"}),
        )
        for job_file, env in refused:
            with self.subTest(job=job_file.name, env=env):
                self.assert_refusal(self.bind(project, job_file, env))
        # The refusals bound nothing: the same child id still binds under its own host.
        for job_file, env in ((job_a, {"CLAUDE_CODE_SESSION_ID": "child-session"}),
                              (job_b, {"CODEX_SESSION_ID": "child-session"})):
            with self.subTest(job=job_file.name, accepted=env):
                result = self.bind(project, job_file, env)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                self.assertEqual(self.one_json(result)["schema_version"], 1)

    def test_bind_job_binds_a_child_session_to_one_job_only(self) -> None:
        project = self.make_project("project")
        job_a = self.make_job(project, JOB_A, "job-a.json")
        job_c = self.make_job(project, JOB_A | {"job_id": "job-gamma", "inputs": []}, "job-c.json")
        job_b = self.make_job(project, JOB_B, "job-b.json")
        claude_child = {"CLAUDE_CODE_SESSION_ID": "child-session"}
        for job_file, env in ((job_a, claude_child), (job_b, {"CODEX_SESSION_ID": "codex-child"})):
            with self.subTest(job=job_file.name):
                result = self.bind(project, job_file, env)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                self.assertEqual(self.one_json(result)["schema_version"], 1)
                self.assert_not_ok(self.bind(project, job_file, env))
        self.assert_not_ok(self.bind(project, job_c, claude_child))
        result = self.bind(project, job_c, {"CLAUDE_CODE_SESSION_ID": "child-session-2"})
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(self.one_json(result)["schema_version"], 1)
        self.assertEqual(list(self.cwd.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_bind_job_rejects_a_malformed_job_file_as_usage_error(self) -> None:
        project = self.make_project("project")
        job_file = self.make_job(project, JOB_A, "job-a.json")
        payload = json.loads(job_file.read_text(encoding="utf-8"))
        broken = [b"{", b"", b"not json", json.dumps({}).encode()]
        for key in ("request_id", "job_id", "host_id"):
            missing = dict(payload)
            del missing[key]
            broken.append(json.dumps(missing).encode())
        child = {"CLAUDE_CODE_SESSION_ID": "child-session"}
        for content in broken:
            with self.subTest(content=content[:40]):
                bad = self.base / "specs" / f"{uuid.uuid4().hex}.json"
                bad.write_bytes(content)
                self.assert_usage_error(self.bind(project, bad, child))
        self.assert_usage_error(self.run_facade("--bind-job", str(job_file), env=child))
        result = self.bind(project, job_file, child)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))

    def test_close_child_requires_a_claude_session(self) -> None:
        project = self.make_project("project")
        artifact = project / CHILD_A["artifact_path"]
        for env in ({}, {"CODEX_SESSION_ID": "parent-alpha"}, {"GEMINI_SESSION_ID": "parent-alpha"},
                    {"CLAUDE_SESSION_ID": "parent-alpha"}):
            with self.subTest(env=env):
                result = self.close(project, CHILD_A, env, b"output")
                self.assert_refusal(result, "missing_native_session")
                self.assertEqual(self.one_json(result), MISSING_SESSION)
                self.assertFalse(artifact.exists())
        result = self.close(project, CHILD_A, {"CLAUDE_CODE_SESSION_ID": "parent-alpha"}, b"output")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(artifact.read_bytes(), b"output")

    def test_close_child_refuses_a_child_of_another_session(self) -> None:
        project = self.make_project("project")
        artifact = project / CHILD_A["artifact_path"]
        for session in ("parent-alph", "parent-alpha-2", "PARENT-ALPHA", "parent-beta", "alpha"):
            with self.subTest(session=session):
                self.assert_not_ok(self.close(project, CHILD_A, {"CLAUDE_CODE_SESSION_ID": session},
                                              b"output"))
                self.assertFalse(artifact.exists())

    def test_close_child_writes_the_piped_bytes_exactly_once(self) -> None:
        project = self.make_project("project")
        for request, raw in ((CHILD_A, b"line one\n\x00\xff binary\r\nline three\n"), (CHILD_B, b"")):
            child = request["child"]
            env = {"CLAUDE_CODE_SESSION_ID": child["parent_session_id"]}
            artifact = project / request["artifact_path"]
            with self.subTest(child=child["child_id"]):
                result = self.close(project, request, env, raw)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                reply = self.one_json(result)
                self.assertEqual((reply["schema_version"], reply["child_id"]), (1, child["child_id"]))
                self.assertEqual(artifact.read_bytes(), raw)
                for again in (raw, b"different output"):
                    self.assertNotEqual(self.close(project, request, env, again).returncode, 0)
                    self.assertEqual(artifact.read_bytes(), raw)
        self.assertEqual(list(self.cwd.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_close_child_rejects_a_malformed_request_as_usage_error(self) -> None:
        project = self.make_project("project")
        before = snapshot(project)
        for request in malformed_children():
            with self.subTest(request=request):
                self.assert_usage_error(self.close(project, request,
                                                   {"CLAUDE_CODE_SESSION_ID": "parent-alpha"}, b"x"))
                self.assertEqual(snapshot(project), before)
        self.assert_usage_error(self.run_facade("--close-child", str(self.spec(CHILD_A)),
                                                env={"CLAUDE_CODE_SESSION_ID": "parent-alpha"}))
        result = self.close(project, CHILD_A, {"CLAUDE_CODE_SESSION_ID": "parent-alpha"}, b"x")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual((project / CHILD_A["artifact_path"]).read_bytes(), b"x")

    def test_close_child_refuses_an_artifact_outside_the_project(self) -> None:
        outer = self.base / "outer"
        project = self.make_project(os.path.join("outer", "project"))
        before = snapshot(project)
        for artifact_path in ("../../etc/passwd", "../escaped.bin", "out/../../escaped-2.bin",
                              str(self.base / "absolute.bin")):
            target = Path(os.path.normpath(project / artifact_path))
            with self.subTest(artifact_path=artifact_path):
                request = CHILD_A | {"artifact_path": artifact_path}
                result = self.close(project, request, {"CLAUDE_CODE_SESSION_ID": "parent-alpha"}, b"x")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(target.exists())
                self.assertEqual(snapshot(project), before)
        self.assertEqual(sorted(path.name for path in outer.iterdir()), ["project"])
        result = self.close(project, CHILD_A, {"CLAUDE_CODE_SESSION_ID": "parent-alpha"}, b"x")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual((project / CHILD_A["artifact_path"]).read_bytes(), b"x")


if __name__ == "__main__":
    unittest.main()

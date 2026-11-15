"""The facade's --request-job, --bind-job and --close-child modes, driven only through the CLI."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import unittest
import uuid
from pathlib import Path

from facade_modes_support import MISSING_SESSION, STATE_TREE, FacadeModesMixin, snapshot


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


def canonical_request_id(payload: dict) -> str:
    """The stated request_id: sha256 of the canonical payload without request_id."""
    body = {key: value for key, value in payload.items() if key != "request_id"}
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    for value in ("1", True, None, 1.5):
        changed = copy.deepcopy(CHILD_A)
        changed["child"]["depth"] = value
        children.append(changed)
    children += [CHILD_A | {"outcome": value}
                 for value in ("bogus", "Completed", "complete", "", 1, None)]
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

    def assert_bound(self, result, job_file: Path, host: str, child_id: str) -> None:
        """Exit 0 with the binding record for `job_file` and this child session."""
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        reply = self.one_json(result)
        payload = json.loads(job_file.read_text(encoding="utf-8"))
        self.assertEqual([reply[key] for key in ("schema_version", "request_id", "job_id", "host_id")],
                         [1, payload["request_id"], payload["job_id"], payload["host_id"]])
        self.assertEqual(reply["child_session"],
                         {"host_id": host, "session_id": child_id, "source": "environment"})
        self.assertEqual(reply["requester_session"], payload["requester"])
        self.assertEqual(reply["verified_inputs"], payload["inputs"])

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
                     "GEMINI_SESSION_ID": "requester-gemini"}, "claude", "requester-claude"),
            (JOB_B, {"CODEX_SESSION_ID": "requester-codex", "GEMINI_SESSION_ID": "requester-gemini"},
             "codex", "requester-codex"),
            (JOB_A, {"GEMINI_SESSION_ID": "requester-gemini-2"}, "gemini", "requester-gemini-2"),
        )
        all_ids = {"requester-claude", "requester-codex", "requester-gemini", "requester-gemini-2"}
        request_ids = set()
        for index, (job, env, host, requester) in enumerate(cases):
            with self.subTest(job=job["job_id"], requester=requester):
                project = self.make_project(f"project {index}")
                result, out = self.request(project, job, env)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                reply = self.one_json(result)
                text = out.read_text(encoding="utf-8")
                payload = json.loads(text)
                self.assertEqual((reply["schema_version"], reply["mode"], reply["request"]),
                                 (1, "standalone", payload))
                self.assertEqual(payload["request_id"], canonical_request_id(payload))
                request_ids.add(payload["request_id"])
                fields = ("job_id", "role_id", "host_id", "tier", "effort")
                self.assertEqual([payload[key] for key in fields], [job[key] for key in fields])
                # Inputs come back sorted by (kind, path), each with its file's digest.
                self.assertEqual(
                    [(item["kind"], item["path"], item["sha256"]) for item in payload["inputs"]],
                    sorted((item["kind"], item["path"],
                            hashlib.sha256((project / item["path"]).read_bytes()).hexdigest())
                           for item in job["inputs"]))
                self.assertEqual(payload["requester"],
                                 {"host_id": host, "session_id": requester, "source": "environment"})
                for other in all_ids - {requester}:
                    self.assertNotIn(f'"{other}"', text)
        # The same job from another requester is another request.
        self.assertEqual(len(request_ids), len(cases))
        self.assertEqual(list(self.cwd.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_request_job_accepts_every_valid_host_tier_and_effort(self) -> None:
        project = self.make_project("project")
        variants = [("host_id", value) for value in ("claude", "codex", "gemini")]
        variants += [("tier", value) for value in ("haiku", "sonnet", "opus", "fable")]
        variants += [("effort", value) for value in ("low", "medium", "high", "xhigh", "max")]
        for index, (key, value) in enumerate(variants):
            with self.subTest(**{key: value}):
                result, out = self.request(project, JOB_B | {key: value}, REQUESTER, f"job-{index}.json")
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                self.assertEqual(json.loads(out.read_text(encoding="utf-8"))[key], value)

    def test_request_job_refuses_inputs_outside_the_project_or_of_an_excluded_kind(self) -> None:
        project = self.make_project(os.path.join("outer", "project"))
        (project.parent / "outside.md").write_text("# outside\n", encoding="utf-8")
        (project / "docs" / "link.md").symlink_to(project.parent / "outside.md")
        (project / STATE_TREE).mkdir(parents=True)
        (project / STATE_TREE / "notes.md").write_text("# live\n", encoding="utf-8")
        prd = {"kind": "prd", "path": "docs/prd.md"}
        bad_inputs = (
            [{"kind": "prd", "path": "docs/missing.md"}], [{"kind": "prd", "path": "../outside.md"}],
            [{"kind": "prd", "path": "docs/../../outside.md"}],
            [{"kind": "prd", "path": str(project / "docs" / "prd.md")}],
            [{"kind": "prd", "path": "docs/link.md"}], [{"kind": "prd", "path": "docs"}],
            [{"kind": "prd", "path": (STATE_TREE / "notes.md").as_posix()}],
            [{"kind": "prd-x", "path": "docs/prd.md"}], [prd | {"sha256": "0" * 64}],
            [prd, {"kind": "diff", "path": "docs/missing.diff"}],
        )
        jobs = [JOB_A | {"inputs": inputs} for inputs in bad_inputs]
        jobs += [JOB_A | {"excluded_input_kinds": kinds}
                 for kinds in (["diff"], ["plan", "prd"], ["bogus-kind"])]
        for index, job in enumerate(jobs):
            with self.subTest(inputs=job["inputs"], excluded=job["excluded_input_kinds"]):
                result, out = self.request(project, job, REQUESTER, f"job-{index}.json")
                self.assert_usage_error(result)
                self.assertFalse(out.exists())
        result, out = self.request(project, JOB_A | {"excluded_input_kinds": ["plan", "history"]},
                                   REQUESTER, "accepted.json")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(sorted(json.loads(out.read_text(encoding="utf-8"))["excluded_input_kinds"]),
                         ["history", "plan"])

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
        for job_file, host, variable in ((job_a, "claude", "CLAUDE_CODE_SESSION_ID"),
                                         (job_b, "codex", "CODEX_SESSION_ID")):
            with self.subTest(job=job_file.name, accepted=host):
                self.assert_bound(self.bind(project, job_file, {variable: "child-session"}),
                                  job_file, host, "child-session")

    def test_bind_job_binds_a_child_session_to_one_job_only(self) -> None:
        project = self.make_project("project")
        job_a = self.make_job(project, JOB_A, "job-a.json")
        job_c = self.make_job(project, JOB_A | {"job_id": "job-gamma", "inputs": []}, "job-c.json")
        job_b = self.make_job(project, JOB_B, "job-b.json")
        claude_child = {"CLAUDE_CODE_SESSION_ID": "child-session"}
        for job_file, env, host, child_id in ((job_a, claude_child, "claude", "child-session"),
                                              (job_b, {"CODEX_SESSION_ID": "codex-child"}, "codex",
                                               "codex-child")):
            with self.subTest(job=job_file.name):
                self.assert_bound(self.bind(project, job_file, env), job_file, host, child_id)
                self.assert_not_ok(self.bind(project, job_file, env))
        self.assert_not_ok(self.bind(project, job_c, claude_child))
        self.assert_bound(self.bind(project, job_c, {"CLAUDE_CODE_SESSION_ID": "child-session-2"}),
                          job_c, "claude", "child-session-2")
        self.assertEqual(list(self.cwd.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_bind_job_binds_two_requests_that_share_a_job_id(self) -> None:
        project = self.make_project("project")
        job_files = []
        for requester in ("requester-1", "requester-2"):
            result, out = self.request(project, JOB_A, {"CLAUDE_CODE_SESSION_ID": requester},
                                       f"{requester}.json")
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
            job_files.append(out)
        payloads = [json.loads(path.read_text(encoding="utf-8")) for path in job_files]
        self.assertEqual({payload["job_id"] for payload in payloads}, {"job-alpha"})
        self.assertEqual(len({payload["request_id"] for payload in payloads}), 2)
        for job_file, child_id in zip(job_files, ("child-1", "child-2")):
            with self.subTest(job=job_file.name):
                self.assert_bound(self.bind(project, job_file, {"CLAUDE_CODE_SESSION_ID": child_id}),
                                  job_file, "claude", child_id)

    def test_bind_job_refuses_a_job_file_that_no_longer_matches_its_request_id(self) -> None:
        project = self.make_project("project")
        job_file = self.make_job(project, JOB_A, "job-a.json")
        payload = json.loads(job_file.read_text(encoding="utf-8"))
        forged = [payload | {"request_id": "f" * 64},
                  payload | {"request_id": payload["request_id"].upper()},
                  payload | {"inputs": payload["inputs"][:1]}]
        forged += [payload | {key: value} for key, value in (
            ("role_id", "mallory"), ("tier", "haiku"), ("effort", "max"), ("job_id", "job-alpha-2"))]
        child = {"CLAUDE_CODE_SESSION_ID": "child-session"}
        for index, value in enumerate(forged):
            with self.subTest(forged={key: value[key] for key in value if value[key] != payload.get(key)}):
                self.assert_usage_error(self.bind(project, self.write_json(
                    project / f"forged-{index}.json", value), child))
        # No forged file bound the child: it still binds to the genuine request.
        self.assert_bound(self.bind(project, job_file, child), job_file, "claude", "child-session")

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

    def test_close_child_refuses_an_artifact_reached_through_a_symlink(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        project = self.base / "project"
        (project / "docs").mkdir(parents=True)
        (project / "out").symlink_to(outside, target_is_directory=True)
        (project / "dangling.bin").symlink_to(outside / "dangling-target.bin")
        env = {"CLAUDE_CODE_SESSION_ID": "parent-alpha"}
        for artifact_path in ("out/child-alpha.bin", "dangling.bin"):
            with self.subTest(artifact_path=artifact_path):
                result = self.close(project, CHILD_A | {"artifact_path": artifact_path}, env, b"x")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(outside.iterdir()), [])
        result = self.close(project, CHILD_A | {"artifact_path": "child-alpha.bin"}, env, b"x")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual((project / "child-alpha.bin").read_bytes(), b"x")
        self.assertEqual(list(outside.iterdir()), [])

    def test_close_child_refuses_a_child_deeper_than_one_level(self) -> None:
        project = self.make_project("project")
        env = {"CLAUDE_CODE_SESSION_ID": "parent-alpha"}
        artifact = project / CHILD_A["artifact_path"]
        for depth in (2, 3):
            with self.subTest(depth=depth):
                request = copy.deepcopy(CHILD_A)
                request["child"]["depth"] = depth
                result = self.close(project, request, env, b"x")
                self.assert_not_ok(result)
                self.assertEqual(self.one_json(result)["error"], "recursion_depth")
                self.assertFalse(artifact.exists())
        result = self.close(project, CHILD_A | {"outcome": "cancelled"}, env, b"x")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        reply = self.one_json(result)
        self.assertEqual((reply["child_id"], reply["outcome"]), ("child-alpha", "cancelled"))
        self.assertEqual(artifact.read_bytes(), b"x")


if __name__ == "__main__":
    unittest.main()

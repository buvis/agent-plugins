"""jobs.py design §5: the canonical job.plan payload and its round trip,
derive_ancestry, and the JobRefused type."""

from __future__ import annotations

import copy
import importlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parents[1] / "plugins" / "autopilot" / "scripts"
for _path in (SCRIPTS, TESTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

jobs = importlib.import_module("jobs")
fakes = importlib.import_module("host_fakes")

DIFF = fakes.DIFF
PRD = fakes.PRD
JOB_FILE_LIMIT = 2097152


class JobRequestPayloadTest(fakes.ProjectCase):
    def expected_payload(self, fields: dict, ancestry: list) -> dict:
        requester = fields["requester"]
        inputs = sorted(fields["inputs"], key=lambda item: (item["kind"], item["path"]))
        expected = {
            "intent_schema": "autopilot.job-intent.v1", "operation": "job.plan",
            "required_capability": "workflow.jobs.v1", "job_id": fields["job_id"],
            "role_id": fields["role_id"], "host_id": fields["host_id"],
            "execution": "cross-session", "isolation": "fresh-session",
            "tier": fields["tier"], "effort": fields["effort"],
            "inputs": [
                {"kind": item["kind"], "path": item["path"],
                 "sha256": fakes.sha256_hex((self.root / item["path"]).read_bytes())}
                for item in inputs
            ],
            "excluded_input_kinds": list(fields["excluded_input_kinds"]),
            "requester": {"host_id": requester.host_id, "session_id": requester.session_id,
                          "source": requester.source},
            "ancestry": ancestry,
        }
        expected["request_id"] = fakes.canonical_request_id(expected)
        return expected

    def test_to_payload_is_the_canonical_job_plan_intent(self) -> None:
        cases = (
            {},
            dict(job_id="blake-review", role_id="blind-reviewer", host_id="gemini", tier="haiku",
                 effort="max", inputs=[PRD, DIFF], excluded_input_kinds=["history"],
                 requester=fakes.native_session("gemini", "gm-req-2", "hook_input")),
        )
        ids = []
        for override in cases:
            with self.subTest(override=override):
                request = fakes.build(self.root, **override)
                expected = self.expected_payload(fakes.job_fields(self.root, **override), [])
                self.assertEqual(request.to_payload(), expected)
                self.assertEqual(request.request_id, expected["request_id"])
                self.assertRegex(request.request_id, r"^[0-9a-f]{64}$")
                ids.append(request.request_id)
        self.assertNotEqual(ids[0], ids[1])
        self.assertNotEqual(fakes.build(self.root, effort="low").request_id, ids[0])

    def test_payload_lists_ancestry_entries_in_order(self) -> None:
        ancestry = (jobs.AncestryEntry(host_id="claude", job_id="first-job", session_id="s-1"),
                    jobs.AncestryEntry(host_id="gemini", job_id="second-job", session_id="s-2"))
        with mock.patch.object(jobs, "MAX_JOB_DEPTH", 3):
            request = fakes.build(self.root, ancestry=ancestry)
        expected = self.expected_payload(fakes.job_fields(self.root), [
            {"host_id": "claude", "job_id": "first-job", "session_id": "s-1"},
            {"host_id": "gemini", "job_id": "second-job", "session_id": "s-2"},
        ])
        self.assertEqual(request.to_payload(), expected)

    def test_from_payload_round_trips_two_requests(self) -> None:
        for request in (fakes.build(self.root),
                        fakes.build(self.root, job_id="blake-review", host_id="gemini",
                                    inputs=[PRD, DIFF], excluded_input_kinds=["history"])):
            with self.subTest(job_id=request.job_id):
                payload = request.to_payload()
                rebuilt = jobs.JobRequest.from_payload(payload)
                self.assertEqual(rebuilt, request)
                self.assertIsInstance(rebuilt.inputs, tuple)
                self.assertIsInstance(rebuilt.requester, fakes.hosts.NativeSession)
                payload["inputs"][0]["path"] = "docs/dev/tmp/other.diff"
                payload["effort"] = "low"
                self.assertEqual(rebuilt, request)

    def test_from_payload_refuses_a_payload_that_does_not_match_its_request_id(self) -> None:
        payload = fakes.build(self.root).to_payload()
        for key, value in (("request_id", "0" * 64), ("request_id", payload["request_id"].upper()),
                           ("effort", "low"), ("tier", "sonnet"), ("job_id", "alice-review2")):
            with self.subTest(key=key, value=value):
                self.assert_refused("invalid_request", jobs.JobRequest.from_payload,
                                    {**payload, key: value})
        changed = copy.deepcopy(payload)
        changed["inputs"][0]["sha256"] = "0" * 64
        self.assert_refused("invalid_request", jobs.JobRequest.from_payload, changed)

    def test_from_payload_revalidates_fields_even_with_a_matching_request_id(self) -> None:
        base = fakes.build(self.root).to_payload()
        mutations = {
            "empty effort": lambda p: p.update(effort=""),
            "tier": lambda p: p.update(tier="Opus"),
            "host": lambda p: p.update(host_id="claudex"),
            "execution": lambda p: p.update(execution="in-session"),
            "isolation": lambda p: p.update(isolation="fresh-context"),
            "operation": lambda p: p.update(operation="job.run"),
            "schema": lambda p: p.update(intent_schema="autopilot.job-intent.v2"),
            "capability": lambda p: p.update(required_capability="workflow.jobs.v2"),
            "extra key": lambda p: p.update(extra="x"),
            "missing role": lambda p: p.pop("role_id"),
            "reserved job id": lambda p: p.update(job_id="claude"),
            "uppercase digest": lambda p: p["inputs"][0].update(sha256="A" * 64),
            "parent path": lambda p: p["inputs"][0].update(path="../a.diff"),
            "unknown kind": lambda p: p["inputs"][0].update(kind="diffs"),
            "unknown excluded kind": lambda p: p.update(excluded_input_kinds=["histories"]),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                self.assert_rehashed_refused("invalid_request", base, mutate)
        self.assert_rehashed_refused("recursion_depth", base, lambda p: p.update(
            ancestry=[{"host_id": "claude", "job_id": "earlier-job", "session_id": "s-9"}]))
        ancestry_cases = (
            ("recursive_job", {"host_id": "codex", "job_id": "alice-review", "session_id": "s-9"}),
            ("invalid_request", {"host_id": "claudex", "job_id": "earlier-job", "session_id": "s-9"}),
            ("invalid_request", {"host_id": "claude", "job_id": "earlier-job"}),
            ("invalid_request", {"host_id": "claude", "job_id": "earlier-job", "session_id": "s-9",
                                 "depth": 1}),
        )
        with mock.patch.object(jobs, "MAX_JOB_DEPTH", 3):
            fine = [{"host_id": "claude", "job_id": "earlier-job", "session_id": "s-9"}]
            accepted = jobs.JobRequest.from_payload(
                self.rehash(base, lambda p: p.update(ancestry=fine)))
            self.assertEqual(accepted.ancestry, (jobs.AncestryEntry(**fine[0]),))
            for code, entry in ancestry_cases:
                with self.subTest(code=code, entry=entry):
                    self.assert_rehashed_refused(code, base, lambda p: p.update(ancestry=[entry]))
            with mock.patch.object(jobs, "MAX_JOB_DEPTH", 2):
                self.assert_rehashed_refused("recursion_depth", base, lambda p: p.update(
                    ancestry=[{**fine[0], "job_id": f"job-{n}"} for n in range(2)]))

    def rehash(self, base: dict, mutate) -> dict:
        payload = copy.deepcopy(base)
        mutate(payload)
        payload["request_id"] = fakes.canonical_request_id(payload)
        return payload

    def assert_rehashed_refused(self, code: str, base: dict, mutate) -> None:
        """A re-hashed mutation is refused by from_payload and by bind_job_session,
        and the refused bind writes no file."""
        payload = self.rehash(base, mutate)
        self.assert_refused(code, jobs.JobRequest.from_payload, payload)
        before = fakes.files_under(self.root)
        self.assert_refused(code, jobs.bind_job_session, payload,
                            child=fakes.native_session("codex", "cx-child-1"),
                            project_root=self.root)
        self.assertEqual(fakes.files_under(self.root), before)


class DeriveAncestryTest(fakes.ProjectCase):
    def write_job(self, request: object, name: str, pad: int = 0) -> Path:
        data = json.dumps(request.to_payload()).encode("utf-8") + b" " * pad
        return fakes.seed(self.root, f"docs/dev/tmp/autopilot/{name}", data)

    def serve_session(self, host_id: str, session_id: str) -> list:
        calls: list = []

        def session_from_environment(env: object) -> object:
            calls.append(env)
            return fakes.native_session(host_id, session_id)

        fakes.install_adapter(self, host_id, session_from_environment=session_from_environment)
        return calls

    def test_no_job_env_means_no_ancestry(self) -> None:
        self.serve_session("codex", "cx-child-1")
        job_file = self.write_job(fakes.build(self.root), "job.json")
        for env in ({}, {"PATH": "/bin"}, {"AUTOPILOT_JOB_REQUESTS": str(job_file)},
                    {"AUTOPILOT_JOB": str(job_file)}):
            with self.subTest(env=env):
                self.assertEqual(jobs.derive_ancestry(env, self.root), ())

    def test_job_env_appends_the_job_host_job_and_current_session(self) -> None:
        prior = (jobs.AncestryEntry(host_id="claude", job_id="first-job", session_id="s-1"),
                 jobs.AncestryEntry(host_id="gemini", job_id="second-job", session_id="s-2"))
        patcher = mock.patch.object(jobs, "MAX_JOB_DEPTH", 3)
        patcher.start()
        self.addCleanup(patcher.stop)
        for host_id, job_id, session_id, ancestry in (
            ("codex", "alice-review", "cx-child-1", ()),
            ("gemini", "blake-review", "gm-child-2", ()),
            ("codex", "carl-review", "cx-child-3", prior),
        ):
            with self.subTest(job_id=job_id):
                calls = self.serve_session(host_id, session_id)
                job_file = self.write_job(fakes.build(self.root, host_id=host_id, job_id=job_id,
                                                      ancestry=ancestry), f"{job_id}.json")
                env = {jobs.JOB_ENV: str(job_file), "MARKER": job_id}
                self.assertEqual(jobs.derive_ancestry(env, self.root), (
                    *ancestry,
                    jobs.AncestryEntry(host_id=host_id, job_id=job_id, session_id=session_id),
                ))
                self.assertTrue(calls)
                self.assertTrue(all(call == env for call in calls))

    def test_an_unreadable_or_invalid_job_file_is_refused(self) -> None:
        self.serve_session("codex", "cx-child-1")
        valid = fakes.build(self.root).to_payload()
        folder = self.root / "docs/dev/tmp/autopilot/folder"
        folder.mkdir(parents=True)
        cases = {
            "missing.json": None, "folder": None, "empty.json": b"",
            "not-json.json": b"{not json", "list.json": b"[]",
            "tampered.json": json.dumps({**valid, "effort": "low"}).encode("utf-8"),
        }
        for name, data in cases.items():
            path = self.root / "docs/dev/tmp/autopilot" / name
            if data is not None:
                path.write_bytes(data)
            with self.subTest(job_file=name):
                self.assert_refused("invalid_request", jobs.derive_ancestry,
                                    {jobs.JOB_ENV: str(path)}, self.root)

    def test_job_file_size_limit_is_inclusive(self) -> None:
        self.serve_session("codex", "cx-child-1")
        request = fakes.build(self.root)
        body = len(json.dumps(request.to_payload()).encode("utf-8"))
        at = self.write_job(request, "at.json", pad=JOB_FILE_LIMIT - body)
        over = self.write_job(request, "over.json", pad=JOB_FILE_LIMIT - body + 1)
        self.assertEqual(at.stat().st_size, JOB_FILE_LIMIT)
        self.assertEqual(len(jobs.derive_ancestry({jobs.JOB_ENV: str(at)}, self.root)), 1)
        self.assert_refused("invalid_request", jobs.derive_ancestry,
                            {jobs.JOB_ENV: str(over)}, self.root)


class JobRefusedTest(unittest.TestCase):
    def test_carries_its_code_and_is_a_value_error(self) -> None:
        for code in ("recursive_job", "foreign_child"):
            with self.subTest(code=code):
                error = jobs.JobRefused(code, f"detail for {code}")
                self.assertIsInstance(error, ValueError)
                self.assertEqual(error.code, code)
        with self.assertRaises(ValueError) as caught:
            raise jobs.JobRefused("same_session", "child reuses the requester session")
        self.assertEqual(caught.exception.code, "same_session")



if __name__ == "__main__":
    unittest.main()

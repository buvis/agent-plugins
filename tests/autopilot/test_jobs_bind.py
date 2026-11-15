"""jobs.py design §5: bind_job_session's binding record and
write_binding_record's lineage file."""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parents[1] / "plugins" / "autopilot" / "scripts"
for _path in (SCRIPTS, TESTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

jobs = importlib.import_module("jobs")
fakes = importlib.import_module("host_fakes")

BINDING_KEYS = {"schema_version", "request_id", "job_id", "host_id", "child_session",
                "requester_session", "verified_inputs", "ancestry"}


class BindJobSessionTest(fakes.ProjectCase):
    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def test_returns_the_binding_and_writes_exactly_one_lineage_record(self) -> None:
        cases = (
            ({}, fakes.native_session("codex", "cx-child-1", "environment")),
            (dict(job_id="blake-review", host_id="gemini", inputs=[fakes.PRD, fakes.DIFF],
                  requester=fakes.native_session("gemini", "gm-req-2")),
             fakes.native_session("gemini", "gm-child-2", "hook_input")),
        )
        for override, child in cases:
            with self.subTest(child=child.session_id):
                request = fakes.build(self.root, **override)
                payload = request.to_payload()
                before = fakes.files_under(self.root)
                bound = jobs.bind_job_session(payload, child=child, project_root=self.root)
                record = fakes.record_path(self.root, child.host_id, child.session_id)
                self.assertEqual(fakes.files_under(self.root), before | {self.relative(record)})
                self.assertNotIn(self.relative(record), before)
                self.assertEqual(json.loads(record.read_text(encoding="utf-8")), bound)
                self.assertEqual(set(bound), BINDING_KEYS)
                self.assertEqual(
                    (bound["schema_version"], bound["request_id"], bound["job_id"], bound["host_id"]),
                    (1, payload["request_id"], request.job_id, request.host_id),
                )
                self.assertEqual(bound["child_session"], {"host_id": child.host_id,
                                                          "session_id": child.session_id,
                                                          "source": child.source})
                self.assertEqual(bound["requester_session"], payload["requester"])
                self.assertEqual(bound["verified_inputs"], payload["inputs"])
                self.assertEqual(len(bound["ancestry"]), len(request.ancestry) + 1)
                entry = bound["ancestry"][-1]
                self.assertEqual(set(entry), {"host_id", "job_id", "session_id"})
                self.assertEqual(entry["session_id"], request.requester.session_id)

    def test_refuses_a_payload_whose_request_id_changed(self) -> None:
        payload = fakes.build(self.root).to_payload()
        child = fakes.native_session("codex", "cx-child-1")
        before = fakes.files_under(self.root)
        for changed in ({**payload, "request_id": "f" * 64}, {**payload, "tier": "haiku"}):
            with self.subTest(changed=changed["request_id"][:8]):
                self.assert_refused("invalid_request", jobs.bind_job_session, changed,
                                    child=child, project_root=self.root)
        self.assertEqual(fakes.files_under(self.root), before)

    def test_a_child_session_binds_at_most_once(self) -> None:
        first = fakes.build(self.root).to_payload()
        second = fakes.build(self.root, job_id="blake-review").to_payload()
        child = fakes.native_session("codex", "cx-child-1")
        bound = jobs.bind_job_session(first, child=child, project_root=self.root)
        record = fakes.record_path(self.root, "codex", "cx-child-1")
        for payload in (first, second):
            with self.subTest(job_id=payload["job_id"]):
                self.assert_refused("recursion_depth", jobs.bind_job_session, payload,
                                    child=child, project_root=self.root)
        self.assertEqual(json.loads(record.read_text(encoding="utf-8")), bound)
        other = fakes.native_session("codex", "cx-child-10")
        jobs.bind_job_session(second, child=other, project_root=self.root)
        self.assertTrue(fakes.record_path(self.root, "codex", "cx-child-10").is_file())

    def test_binds_against_the_given_project_root(self) -> None:
        payload = fakes.build(self.root).to_payload()
        other = self.temp / "other"
        fakes.seed(other, fakes.DIFF["path"], b"different bytes in another root\n")
        child = fakes.native_session("codex", "cx-child-1")
        self.assert_refused("input_digest_mismatch", jobs.bind_job_session, payload,
                            child=child, project_root=other)
        self.assertEqual(fakes.files_under(other), {fakes.DIFF["path"]})
        fakes.seed(other, fakes.DIFF["path"], fakes.BASE_INPUTS[fakes.DIFF["path"]])
        jobs.bind_job_session(payload, child=child, project_root=other)
        self.assertTrue(fakes.record_path(other, "codex", "cx-child-1").is_file())
        self.assertFalse(fakes.record_path(self.root, "codex", "cx-child-1").exists())


class WriteBindingRecordTest(fakes.ProjectCase):
    def test_writes_the_record_named_by_host_and_session_digest(self) -> None:
        cases = (("claude", "cl-1", {"schema_version": 1, "job_id": "a"}),
                 ("codex", "会話-42", {"schema_version": 1, "job_id": "b", "nested": [1, 2]}),
                 ("gemini", "cl-1", {"schema_version": 1, "job_id": "c"}))
        for host_id, session_id, record in cases:
            with self.subTest(host_id=host_id, session_id=session_id):
                path = jobs.write_binding_record(host_id, session_id, record,
                                                 project_root=self.root)
                expected = fakes.record_path(self.root, host_id, session_id)
                self.assertEqual((self.root / path).resolve(), expected.resolve())
                self.assertEqual(json.loads(expected.read_text(encoding="utf-8")), record)
        written = sorted(p.name for p in (self.root / fakes.LINEAGE_DIR).iterdir())
        self.assertEqual(written, sorted(fakes.record_path(self.root, h, s).name
                                         for h, s, _ in cases))

    def test_never_overwrites_an_existing_record(self) -> None:
        jobs.write_binding_record("claude", "cl-1", {"job_id": "first"}, project_root=self.root)
        with self.assertRaises((OSError, jobs.JobRefused)):
            jobs.write_binding_record("claude", "cl-1", {"job_id": "second"},
                                      project_root=self.root)
        record = fakes.record_path(self.root, "claude", "cl-1")
        self.assertEqual(json.loads(record.read_text(encoding="utf-8")), {"job_id": "first"})

    def test_never_writes_through_a_symlinked_directory(self) -> None:
        outside = self.temp / "elsewhere"
        outside.mkdir()
        (self.root / "docs/dev/tmp/autopilot").symlink_to(outside, target_is_directory=True)
        with self.assertRaises((OSError, jobs.JobRefused)):
            jobs.write_binding_record("claude", "cl-1", {"job_id": "a"}, project_root=self.root)
        self.assertEqual(sorted(outside.rglob("*")), [])


if __name__ == "__main__":
    unittest.main()

"""jobs.py's `_write_request_file`: split out of test_jobs.py (PRD 00014 v2
rework cycle 2, task 23) to keep that file under the 800-line style limit."""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[1]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
for _path in (SCRIPTS, TESTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

jobs = importlib.import_module("jobs")
fakes = importlib.import_module("host_fakes")


class WriteRequestFileTest(fakes.ProjectCase):
    """jobs.py's `_write_request_file` must open/create the request file
    through a descriptor pinned to the validated root, so a directory
    component swapped to a symlink below the root cannot redirect the
    create outside it (a parent-swap/TOCTOU regression)."""

    def test_creates_missing_parent_directories_and_writes_the_payload(self) -> None:
        payload = fakes.build(self.root).to_payload()
        resolved = self.root / "a" / "b" / "request.json"
        jobs._write_request_file(resolved, self.root, payload)
        self.assertTrue(resolved.is_file())
        self.assertEqual(json.loads(resolved.read_text(encoding="utf-8")), payload)

    def test_refuses_when_a_component_below_root_is_swapped_to_an_outside_symlink(self) -> None:
        first_payload = fakes.build(self.root, job_id="first-job").to_payload()
        first = self.root / "a" / "b" / "request.json"
        jobs._write_request_file(first, self.root, first_payload)
        self.assertTrue(first.is_file())

        escaped = self.temp / "escaped"
        escaped.mkdir()
        (self.root / "a" / "c").symlink_to(escaped, target_is_directory=True)
        second_payload = fakes.build(self.root, job_id="second-job").to_payload()
        second = self.root / "a" / "c" / "request.json"
        with self.assertRaises(OSError):
            jobs._write_request_file(second, self.root, second_payload)

        self.assertEqual(list(escaped.iterdir()), [])
        self.assertTrue(first.is_file())
        self.assertEqual(json.loads(first.read_text(encoding="utf-8")), first_payload)


if __name__ == "__main__":
    unittest.main()

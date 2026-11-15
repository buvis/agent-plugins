"""Tests for doctor.py:54's evidence schema validation: diagnose() must not
crash on a probe-evidence record with the wrong schema_version or malformed
JSON, and must not silently clear a host's capability gaps by trusting that
evidence as if it were valid.
"""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

doctor = importlib.import_module("doctor")

PROBES = Path("docs") / "dev" / "tmp" / "autopilot" / "probes"
CAPS = ("identity", "isolation", "interception", "resources")


def probe_evidence(observed: tuple[str, ...], *, schema_version: object = 2,
                   resource_check: str = "passed", exit_codes: tuple[int, ...] = (0,)) -> dict:
    """The same schema_version-2 probe record shape used by test_facade.py,
    with a caller-chosen (possibly wrong) schema_version."""
    return {
        "schema_version": schema_version, "static": {}, "run_dir": "docs/dev/tmp/autopilot/probes/run",
        "registration_surface": "none", "trace_lines": 0, "certified": False,
        "invocations": [{"argv": ["host"], "exit_code": code, "timed_out": False,
                         "duration_seconds": 1.0, "stdout_sha256": "0" * 64,
                         "stderr_sha256": "0" * 64, "stdout_path": "o", "stderr_path": "e"}
                        for code in exit_codes],
        "observed": {cap: {"status": "observed", "reason": None} if cap in observed
                     else {"status": "not_observed", "reason": "host_did_not_enforce"}
                     for cap in CAPS},
        "resource_check": resource_check,
    }


class DiagnoseEvidenceSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / PROBES).mkdir(parents=True)

    def write(self, name: str, record: dict) -> None:
        (self.root / PROBES / name).write_text(json.dumps(record), encoding="utf-8")

    def write_bytes(self, name: str, data: bytes) -> None:
        (self.root / PROBES / name).write_bytes(data)

    def openai_implementor_row(self, report: dict) -> dict:
        profile = next(p for p in report["profiles"] if p["profile_id"] == "codex-gemini")
        rows = {row["role"]: row for row in profile["roles"]}
        return rows["implementor:openai"]

    def test_wrong_schema_version_does_not_crash_diagnosis(self) -> None:
        self.write("codex-20261101T080000Z.json", probe_evidence(CAPS, schema_version=99))
        report = doctor.diagnose(project_root=self.root)
        self.assertIsInstance(report, dict)
        self.assertIn("profiles", report)

    def test_malformed_newest_evidence_json_does_not_crash_diagnosis(self) -> None:
        self.write_bytes("codex-20261101T080000Z.json", b"{not valid json")
        report = doctor.diagnose(project_root=self.root)
        self.assertIsInstance(report, dict)
        self.assertIn("profiles", report)

    def test_wrong_schema_version_does_not_clear_the_hosts_capability_gap(self) -> None:
        self.write("codex-20261101T080000Z.json", probe_evidence(CAPS, schema_version=99))
        report = doctor.diagnose(project_root=self.root)
        row = self.openai_implementor_row(report)
        self.assertEqual(row["host_id"], "codex")
        self.assertIn("codex:interception", row["unobserved"])

    def test_malformed_newest_evidence_json_does_not_clear_the_hosts_capability_gap(self) -> None:
        self.write_bytes("codex-20261101T080000Z.json", b"{not valid json")
        report = doctor.diagnose(project_root=self.root)
        row = self.openai_implementor_row(report)
        self.assertEqual(row["host_id"], "codex")
        self.assertIn("codex:interception", row["unobserved"])

    def test_a_valid_schema_version_is_still_consumed_and_clears_the_gap(self) -> None:
        """Devon-proof control: the same observed capabilities, with a valid
        schema_version, must actually clear the gap the two tests above
        prove is NOT cleared for invalid evidence."""
        self.write("codex-20261101T080000Z.json", probe_evidence(CAPS, schema_version=2))
        report = doctor.diagnose(project_root=self.root)
        row = self.openai_implementor_row(report)
        self.assertNotIn("codex:interception", row["unobserved"])


if __name__ == "__main__":
    unittest.main()

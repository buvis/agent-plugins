"""Reconciliation and recovery: derived facts only, nothing valid overwritten (T-024)."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

import support
from specflow_helper.reconcile import reconcile
from specflow_helper.state import StateError

RECOVERY = support.FIXTURES / "recovery"


def snapshot(folder: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(folder.iterdir())}


class ReconcileFixtureTest(support.TempTest):
    def copy(self, source: Path) -> Path:
        target = self.tmp / source.name
        shutil.copytree(source, target)
        return target

    def test_missing_state_is_recovered_from_files_without_writing(self) -> None:
        spec = self.copy(RECOVERY / "no-state")
        before = snapshot(spec)
        result = reconcile(spec, dry_run=False)
        self.assertEqual(snapshot(spec), before)
        self.assertEqual(result["changes"], [])
        self.assertEqual(
            result["statuses"],
            {"requirements": "draft", "design": "draft", "tasks": "missing"},
        )
        self.assertEqual(result["phase"], "requirements")
        self.assertEqual(
            [a["artifact"] for a in result["ambiguous"]],
            ["requirements", "design"],
        )

    def test_malformed_state_is_kept_byte_for_byte(self) -> None:
        spec = self.copy(RECOVERY / "malformed-state")
        before = snapshot(spec)
        with self.assertRaises(StateError):
            reconcile(spec, dry_run=False)
        self.assertEqual(snapshot(spec), before)

    def test_unknown_version_stops_without_mutation(self) -> None:
        spec = self.copy(RECOVERY / "unknown-version")
        before = snapshot(spec)
        with self.assertRaisesRegex(StateError, "unsupported state version 2"):
            reconcile(spec, dry_run=False)
        self.assertEqual(snapshot(spec), before)

    def test_missing_artifact_is_marked_missing_and_its_approval_record_kept(
        self,
    ) -> None:
        spec = self.copy(RECOVERY / "missing-artifact")
        requirements = (spec / "requirements.md").read_bytes()
        result = reconcile(spec, dry_run=False)
        self.assertEqual(
            result["statuses"],
            {"requirements": "approved", "design": "missing", "tasks": "missing"},
        )
        self.assertEqual(result["phase"], "design")
        state = json.loads((spec / ".specflow.json").read_text())
        self.assertEqual(state["artifacts"]["design"]["status"], "missing")
        self.assertEqual(state["artifacts"]["design"]["approvedSha256"], "5" * 64)
        self.assertEqual((spec / "requirements.md").read_bytes(), requirements)

    def test_each_kiro_capture_reconciles_without_any_write(self) -> None:
        for folder in ("requirements-first", "design-first", "bugfix"):
            with self.subTest(folder=folder):
                spec = self.copy(support.FIXTURES / "kiro" / folder)
                before = snapshot(spec)
                result = reconcile(spec, dry_run=False)
                self.assertEqual(snapshot(spec), before)
                self.assertNotIn(".specflow.json", before)
                self.assertEqual(len(result["ambiguous"]), 3)

    def test_design_first_capture_asks_about_the_design_first(self) -> None:
        spec = self.copy(support.FIXTURES / "kiro" / "design-first")
        result = reconcile(spec, dry_run=True)
        self.assertEqual(result["ambiguous"][0]["artifact"], "design")
        self.assertEqual(result["phase"], "design")

    def test_bugfix_capture_reports_its_requirements_slot(self) -> None:
        spec = self.copy(support.FIXTURES / "kiro" / "bugfix")
        result = reconcile(spec, dry_run=True)
        self.assertEqual(result["ambiguous"][0]["path"], "bugfix.md")


class ReconcileWriteTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.spec = support.write_spec(
            self.tmp / "00042-sample",
            {"requirements.md": support.REQUIREMENTS, "design.md": support.DESIGN},
        )
        state = support.new_state()
        state["artifacts"]["tasks"]["status"] = "missing"
        state["artifacts"]["design"]["laterField"] = {"kept": [1, 2]}
        state["zLater"] = "after artifacts"
        self.state = support.approve(self.spec, state, "requirements", "design")

    def test_unknown_keys_keep_their_value_and_place(self) -> None:
        (self.spec / "design.md").write_text(support.DESIGN + "Changed.\n")
        reconcile(self.spec, dry_run=False)
        text = (self.spec / ".specflow.json").read_text()
        state = json.loads(text)
        self.assertEqual(list(state), list(self.state))
        self.assertEqual(
            list(state["artifacts"]["design"]),
            list(self.state["artifacts"]["design"]),
        )
        self.assertEqual(state["artifacts"]["design"]["laterField"], {"kept": [1, 2]})
        self.assertEqual(state["zLater"], "after artifacts")
        self.assertTrue(text.endswith("}\n"))
        self.assertIn('\n  "artifacts": {\n    "requirements": {', text)

    def test_only_derived_facts_are_written(self) -> None:
        (self.spec / "design.md").write_text(support.DESIGN + "Changed.\n")
        result = reconcile(self.spec, dry_run=False)
        self.assertEqual(
            {(c["artifact"], c["field"]) for c in result["changes"]},
            {("design", "sha256"), ("design", "status")},
        )
        design = json.loads((self.spec / ".specflow.json").read_text())["artifacts"][
            "design"
        ]
        self.assertEqual(design["status"], "stale")
        self.assertEqual(
            design["approvedSha256"],
            self.state["artifacts"]["design"]["approvedSha256"],
        )
        self.assertEqual(design["approvedAt"], "2026-10-10T10:00:00Z")

    def test_reconcile_never_writes_an_approval(self) -> None:
        self.state["artifacts"]["tasks"] = {"path": "tasks.md", "status": "missing"}
        support.write_state(self.spec, self.state)
        (self.spec / "tasks.md").write_text(support.TASKS)
        result = reconcile(self.spec, dry_run=False)
        tasks = json.loads((self.spec / ".specflow.json").read_text())["artifacts"][
            "tasks"
        ]
        self.assertEqual(tasks["status"], "draft")
        self.assertNotIn("approvedSha256", tasks)
        self.assertNotIn("approved", [c["to"] for c in result["changes"]])

    def test_dry_run_reports_without_writing(self) -> None:
        (self.spec / "design.md").write_text(support.DESIGN + "Changed.\n")
        before = (self.spec / ".specflow.json").read_bytes()
        result = reconcile(self.spec, dry_run=True)
        self.assertTrue(result["changes"])
        self.assertEqual((self.spec / ".specflow.json").read_bytes(), before)

    def test_approved_without_a_hash_is_ambiguous_not_downgraded(self) -> None:
        del self.state["artifacts"]["design"]["approvedSha256"]
        support.write_state(self.spec, self.state)
        result = reconcile(self.spec, dry_run=False)
        self.assertEqual(result["ambiguous"][0]["artifact"], "design")
        design = json.loads((self.spec / ".specflow.json").read_text())["artifacts"][
            "design"
        ]
        self.assertEqual(design["status"], "approved")

    def test_result_has_the_five_documented_keys(self) -> None:
        result = reconcile(self.spec, dry_run=True)
        self.assertEqual(
            list(result),
            ["spec", "statuses", "phase", "changes", "ambiguous"],
        )


if __name__ == "__main__":
    unittest.main()

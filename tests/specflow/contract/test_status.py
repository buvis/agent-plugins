"""Status for external runners: schema, gates, blockers, markers, holds, next task (T-026)."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

import support
from specflow_helper.schema import check_schema, load_schema
from specflow_helper.status import markers, status

SCHEMA = load_schema("specflow-status.schema.json")
ALL = ("requirements", "design", "tasks")


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class StatusTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.tmp / "repo"
        self.specs = self.repo / ".kiro" / "specs"
        self.specs.mkdir(parents=True)

    def make(
        self,
        name: str,
        *,
        tasks: str = support.TASKS,
        approve: tuple = (),
    ) -> Path:
        spec = support.write_spec(
            self.specs / name,
            {
                "requirements.md": support.REQUIREMENTS,
                "design.md": support.DESIGN,
                "tasks.md": tasks,
            },
        )
        support.approve(spec, support.new_state(name), *approve)
        return spec

    def entry(self, spec: Path) -> dict:
        document = status(self.repo, [spec])
        self.assertEqual(check_schema(document, SCHEMA), [])
        return document["specs"][0]


class SchemaTest(StatusTest):
    def test_document_for_every_kind_of_spec_passes_the_schema(self) -> None:
        self.make("00042-sample", approve=ALL)
        for folder in ("requirements-first", "design-first", "bugfix"):
            shutil.copytree(support.FIXTURES / "kiro" / folder, self.specs / folder)
        shutil.copytree(
            support.FIXTURES / "specs" / "00102-bugfix-sample",
            self.specs / "00102-bugfix",
        )
        (self.specs / "00043-broken").mkdir()
        (self.specs / "00043-broken" / ".specflow.json").write_text("{")
        document = status(self.repo, [])
        self.assertEqual(check_schema(document, SCHEMA), [])
        self.assertEqual(len(document["specs"]), 6)
        broken = next(s for s in document["specs"] if s["spec"] == "00043-broken")
        self.assertEqual(broken["state"], "invalid")

    def test_status_is_read_only(self) -> None:
        self.make("00042-sample", approve=("requirements",))
        before = snapshot(self.repo)
        status(self.repo, [])
        self.assertEqual(snapshot(self.repo), before)


class GateTest(StatusTest):
    def test_open_spec_offers_its_next_task(self) -> None:
        entry = self.entry(self.make("00042-sample", approve=ALL))
        self.assertEqual(entry["phase"], "implementation")
        self.assertEqual(set(entry["gates"].values()), {"open"})
        self.assertEqual(entry["nextTask"], {"id": "T-001", "title": "Greet the user"})

    def test_draft_upstream_closes_later_gates_only(self) -> None:
        entry = self.entry(self.make("00042-sample", approve=("requirements",)))
        self.assertEqual(
            entry["gates"],
            {"design": "open", "tasks": "closed", "implementation": "closed"},
        )
        self.assertIsNone(entry["nextTask"])

    def test_missing_state_has_no_profile_and_a_blocker(self) -> None:
        spec = self.make("00042-sample")
        (spec / ".specflow.json").unlink()
        entry = self.entry(spec)
        self.assertIsNone(entry["profile"])
        self.assertEqual(entry["state"], "missing")
        self.assertIn({"gate": "design", "reason": "state missing"}, entry["blockers"])

    def test_next_task_waits_for_its_dependencies_and_open_sub_tasks(self) -> None:
        tasks = (
            "# Tasks: Sample\n\n"
            "- [ ] T-001 Parent\n  - Requirements: REQ-001\n  - Verify: x\n"
            "  - [x] T-001.1 Done part\n  - [ ] T-001.2 Open part\n"
            "- [ ] T-002 Later\n  - Requirements: REQ-001\n  - Depends on: T-001\n"
            "  - Verify: x\n"
        )
        entry = self.entry(self.make("00042-sample", tasks=tasks, approve=ALL))
        self.assertEqual(entry["nextTask"], {"id": "T-001.2", "title": "Open part"})

    def test_hold_is_shown_and_offers_no_task(self) -> None:
        spec = self.make("00042-sample")
        hold = {"status": "on_hold", "reason": "pilot", "since": "2026-10-01"}
        support.approve(spec, support.new_state("00042-sample", hold=hold), *ALL)
        entry = self.entry(spec)
        self.assertEqual(entry["hold"], hold)
        self.assertEqual(entry["phase"], "implementation")
        self.assertIsNone(entry["nextTask"])


class DependencyTest(StatusTest):
    def test_unfinished_prerequisite_closes_only_implementation(self) -> None:
        self.make("00012-base")
        spec = self.make("00042-sample")
        text = support.REQUIREMENTS.replace(
            "\n\n## Purpose",
            "\nDepends on: 00012\n\n## Purpose",
            1,
        )
        (spec / "requirements.md").write_text(text)
        support.approve(spec, support.new_state("00042-sample"), *ALL)
        entry = self.entry(spec)
        self.assertEqual(entry["phase"], "implementation")
        self.assertEqual(
            entry["gates"],
            {"design": "open", "tasks": "open", "implementation": "closed"},
        )
        self.assertIsNone(entry["nextTask"])
        self.assertIn(
            {
                "gate": "implementation",
                "spec": "00042-sample",
                "reference": "00012",
                "reason": "incomplete prerequisite (phase requirements)",
            },
            entry["blockers"],
        )


class MarkerTest(StatusTest):
    def test_markers_are_guesses_and_open_list_items(self) -> None:
        text = (
            "# R\n\nThe budget is 1% (guess).\n`(guess)` in code is not one.\n\n"
            "## Unresolved questions\n\n- Who owns it?\n  more text\n\n"
            "## Open decisions\n\n1. Pick a store.\n"
        )
        self.assertEqual(
            markers(text),
            ["The budget is 1% (guess).", "- Who owns it?", "1. Pick a store."],
        )

    def test_unaccepted_marker_blocks_the_gate_after_the_dependent_artifact(
        self,
    ) -> None:
        spec = self.make("00042-sample")
        text = (
            support.REQUIREMENTS + "\n## Unresolved questions\n\n- Who owns the log?\n"
        )
        (spec / "requirements.md").write_text(text)
        state = support.approve(spec, support.new_state("00042-sample"), "requirements")
        entry = self.entry(spec)
        self.assertEqual(entry["gates"]["design"], "open")
        blocker = {
            "gate": "tasks",
            "reason": "requirements marker not accepted for the design approval",
            "reference": "- Who owns the log?",
        }
        self.assertIn(blocker, entry["blockers"])
        state["artifacts"]["design"]["acceptedMarkers"] = [
            {"artifact": "requirements", "line": "- Who owns the log?"},
        ]
        support.approve(spec, state, "design")
        self.assertNotIn(blocker, self.entry(spec)["blockers"])


class WarningTest(StatusTest):
    def test_code_drift_warns_in_git_and_closes_no_gate(self) -> None:
        support.git(self.repo, "init", "-q")
        (self.repo / "src.py").write_text("one\n")
        spec = self.make("00042-sample")
        state = support.new_state("00042-sample")
        state["artifacts"]["design"]["approvedCode"] = {
            "status": "captured",
            "files": [{"path": "src.py", "sha256": "0" * 64}],
        }
        support.approve(spec, state, *ALL)
        entry = self.entry(spec)
        self.assertEqual(
            entry["warnings"],
            [{"kind": "code-drift", "message": "src.py changed", "path": "src.py"}],
        )
        self.assertEqual(entry["gates"]["implementation"], "open")

    def test_no_drift_check_outside_git(self) -> None:
        self.assertEqual(
            self.entry(self.make("00042-sample", approve=ALL))["warnings"],
            [],
        )


class IntakeTest(StatusTest):
    def test_intake_lists_new_items_without_a_spec(self) -> None:
        new = self.repo / ".kiro" / "specflow" / "intake" / "new"
        (new / "00050-idea").mkdir(parents=True)
        (new / "plugin" / "00051-grouped").mkdir(parents=True)
        (new / "00042-has-spec").mkdir()
        self.make("00042-sample")
        self.assertEqual(
            status(self.repo, [])["intake"],
            ["00050-idea", "00051-grouped"],
        )


if __name__ == "__main__":
    unittest.main()

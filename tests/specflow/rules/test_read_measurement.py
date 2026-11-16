"""Offline regressions: tool arguments are not a filesystem access trace."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals/runners"))
import run_claude
import run_kiro
import score


class ReadMeasurementTest(unittest.TestCase):
    def test_shell_arguments_never_prove_reads_or_completeness(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / "notes.md").write_text("synthetic")
            (workspace / "alias.md").symlink_to("notes.md")
            for command in (
                "cat notes.md",
                "echo notes.md",
                "touch notes.md",
                "false && cat notes.md",
                "cat alias.md",
                "cat docs/../notes.md",
                "cat *.md",
                "rg synthetic .",
                'cat "$FILE"',
                "cat $(echo notes.md)",
                "python3 helper.py notes.md",
                "./helper notes.md",
                "env cat notes.md",
                "cat notes.md; cat alias.md",
            ):
                with self.subTest(command=command):
                    self.assertEqual(
                        run_claude.shell_reads(command, workspace), ([], False)
                    )

    def test_claude_read_requires_correlated_success(self) -> None:
        call = {
            "type": "tool_use",
            "id": "r",
            "name": "Read",
            "input": {"file_path": "/workspace/notes.md"},
        }
        for result in (
            None,
            {"type": "tool_result", "tool_use_id": "other"},
            {"type": "tool_result", "tool_use_id": "r", "is_error": True},
        ):
            with self.subTest(result=result):
                blocks = [call] + ([result] if result else [])
                self.assertEqual(
                    run_claude.named_reads(
                        [{"message": {"content": blocks}}], Path("/workspace")
                    ),
                    ([], False),
                )
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder).resolve()
            path = workspace / "notes.md"
            path.write_text("synthetic")
            call["input"]["file_path"] = str(path)
            blocks = [
                call,
                {"type": "tool_result", "tool_use_id": "r", "content": "synthetic"},
            ]
            self.assertEqual(
                run_claude.named_reads([{"message": {"content": blocks}}], workspace),
                ([str(path)], True),
            )

    def test_claude_search_edit_and_unknown_tools_are_incomplete(self) -> None:
        for name in ("Grep", "Edit", "Task", "mcp__reader", "Glob"):
            with self.subTest(name=name):
                events = [
                    {
                        "message": {
                            "content": [{"type": "tool_use", "name": name, "input": {}}]
                        }
                    }
                ]
                self.assertEqual(
                    run_claude.named_reads(events, Path("/workspace")), ([], False)
                )

    def test_kiro_failed_read_and_edit_are_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / "notes.md").write_text("synthetic")
            for kind, status in (
                ("read", "failed"),
                ("read", "in_progress"),
                ("edit", "completed"),
            ):
                with self.subTest(kind=kind, status=status):
                    turn = {
                        "calls": {
                            "r": {"kind": kind, "status": status, "path": "notes.md"}
                        }
                    }
                    self.assertEqual(
                        run_kiro.named_reads(turn, workspace, workspace), ([], False)
                    )

    def test_native_alias_does_not_prove_target_absence(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder).resolve()
            (workspace / "notes.md").write_text("synthetic")
            alias = workspace / "alias.md"
            alias.symlink_to("notes.md")
            events = [
                {
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "r",
                                "name": "Read",
                                "input": {"file_path": str(alias)},
                            },
                            {
                                "type": "tool_result",
                                "tool_use_id": "r",
                                "content": "synthetic",
                            },
                        ]
                    }
                }
            ]
            self.assertEqual(
                run_claude.named_reads(events, workspace), ([str(alias)], False)
            )
            turn = {
                "calls": {
                    "r": {"kind": "read", "status": "completed", "path": str(alias)}
                }
            }
            self.assertEqual(
                run_kiro.named_reads(turn, workspace, workspace), ([str(alias)], False)
            )

    def test_partial_reads_decide_only_what_was_observed(self) -> None:
        record = {
            "messages": ["Read notes.md"],
            "filesRead": [["notes.md"]],
            "readMeasurement": "not-measured",
        }
        for kind, path, expected in (
            ("file_read", "notes.md", True),
            ("file_not_read", "notes.md", False),
            ("file_read", "other.md", None),
            ("file_not_read", "other.md", None),
        ):
            with self.subTest(kind=kind, path=path):
                self.assertIs(
                    score.assertion_result({"kind": kind, "path": path}, record, {})[0],
                    expected,
                )
        record["readMeasurement"] = "measured"
        self.assertIs(
            score.assertion_result(
                {"kind": "file_not_read", "path": "other.md"}, record, {}
            )[0],
            True,
        )

    def test_missing_path_leaves_identity_unknown(self) -> None:
        self.assertFalse(
            run_claude.unaliased_path(Path("/nonexistent-specflow-read-target"))
        )

    def test_default_scratch_exists_on_this_platform(self) -> None:
        self.assertTrue(run_claude.EXTERNAL_SCRATCH.is_dir())

    def test_alias_loop_leaves_identity_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "loop"
            path.symlink_to("loop")
            self.assertFalse(run_claude.unaliased_path(path))

    def test_kiro_completed_native_read_names_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder).resolve()
            path = workspace / "notes.md"
            path.write_text("synthetic")
            turn = {
                "calls": {
                    "r": {"kind": "read", "status": "completed", "path": "notes.md"}
                }
            }
            self.assertEqual(
                run_kiro.named_reads(turn, workspace, workspace), ([str(path)], True)
            )

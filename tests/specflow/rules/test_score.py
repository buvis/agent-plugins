"""Stored-record checks for the eval instruments; no signed-in host required."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/specflow/evals/runners"))
import run_claude
import score

FIXTURES = ROOT / "tests/specflow/fixtures/results"


class ScoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads((FIXTURES / "manual.json").read_text())

    def test_passing_and_broken_eval_share_one_record(self) -> None:
        self.assertEqual(score.score_record(self.record, FIXTURES / "evals"), 1)
        self.assertEqual([s["passed"] for s in self.record["scores"]], [True, False])

    def test_manual_record_round_trip_and_schema(self) -> None:
        before = copy.deepcopy(self.record)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "record.json"
            path.write_text(json.dumps(self.record))
            self.assertEqual(score.main([str(path)], FIXTURES / "evals"), 1)
            after = json.loads(path.read_text())
        score.validate_record(after)
        after.pop("scores")
        self.assertEqual(after, before)

    def test_kinds_equal_schema(self) -> None:
        schema = score.read_json(score.SCHEMAS / "eval.schema.json")
        kinds = {
            s["properties"]["kind"]["const"]
            for s in schema["$defs"]["assertion"]["oneOf"]
        }
        self.assertEqual(score.KINDS, kinds)

    def test_unjudged_rubric_exits_one(self) -> None:
        self.assertEqual(score.score_record(self.record, FIXTURES / "rubrics"), 1)
        self.assertFalse(self.record["scores"][0]["passed"])

    def test_unknown_assertion_fails(self) -> None:
        passed, reason = score.assertion_result({"kind": "invented"}, self.record, {})
        self.assertFalse(passed)
        self.assertIn("unknown", reason)

    def test_not_run_has_no_scores(self) -> None:
        self.record["notRun"] = "host did not start"
        self.record["scores"] = []
        self.assertEqual(score.score_record(self.record, FIXTURES / "evals"), 1)
        self.assertNotIn("scores", self.record)

    def test_broken_session_fails_even_negative_assertions(self) -> None:
        self.record["brokenAt"] = 2
        self.assertEqual(score.score_record(self.record, FIXTURES / "evals"), 1)
        self.assertTrue(all(not s["passed"] for s in self.record["scores"]))

    def test_question_and_recommendation_rules(self) -> None:
        self.assertEqual(
            score.question_count("Choose?\n1. A?\n2. B?\n```\nwhy?\n```"), 1
        )
        self.assertEqual(score.question_count("Where? Who?"), 2)
        self.assertEqual(
            score.question_count("See https://example.invalid/?q=x. Continue?"), 1
        )
        self.assertTrue(score.recommended_first("Choose?\n1. A (Recommended)\n2. B"))
        self.assertFalse(score.recommended_first("Choose?\n1. A\n2. B (Recommended)"))

    def test_missing_turn_and_unmeasured_reads_cannot_pass_absence(self) -> None:
        assertion = {"kind": "message_lacks", "pattern": "secret", "turn": 5}
        self.assertFalse(score.assertion_result(assertion, self.record, {})[0])
        self.record["readMeasurement"] = "not-measured"
        assertion = {"kind": "file_not_read", "path": "secret.txt"}
        self.assertFalse(score.assertion_result(assertion, self.record, {})[0])

    def test_compare_ignores_titles_but_not_approvals(self) -> None:
        other = copy.deepcopy(self.record)
        other["host"] = "codex"
        other["status"]["specs"][0]["nextTask"]["title"] = "Different prose"
        self.assertEqual(score.compare([self.record, other]), 0)
        other["status"]["specs"][0]["artifacts"]["tasks"] = "stale"
        self.assertEqual(score.compare([self.record, other]), 1)

    def test_all_file_kinds_include_unchanged_baseline_bytes(self) -> None:
        self.record["unchanged"] = [".kiro/specs/00001-gift-cards/requirements.md"]
        files = score.finished_files(self.record)
        path = self.record["unchanged"][0]
        for assertion in [
            {"kind": "file_exists", "path": path},
            {"kind": "file_unchanged", "path": path},
            {"kind": "file_matches", "path": path, "pattern": "Requirements"},
            {"kind": "file_lacks", "path": path, "pattern": "impossible sentinel"},
            {"kind": "file_absent", "path": "deleted.md"},
        ]:
            with self.subTest(assertion=assertion):
                self.assertTrue(
                    score.assertion_result(assertion, self.record, files)[0]
                )
        self.assertFalse(
            score.assertion_result(
                {"kind": "file_lacks", "path": "missing", "pattern": "secret"},
                self.record,
                files,
            )[0]
        )

    def test_message_turns_and_read_boundaries_are_one_based(self) -> None:
        self.record["filesRead"] = [["first.md"], ["second.md"]]
        assertions = [
            {"kind": "message_matches", "turn": 2, "pattern": "Status"},
            {"kind": "message_lacks", "turn": 1, "pattern": "Status"},
            {"kind": "file_read", "path": "first.md", "before_turn": 2},
            {"kind": "file_not_read", "path": "second.md", "before_turn": 2},
            {"kind": "question_count_at_most", "count": 1},
        ]
        for assertion in assertions:
            with self.subTest(assertion=assertion):
                self.assertTrue(score.assertion_result(assertion, self.record, {})[0])

    def test_validation_runs_on_reconstructed_workspace(self) -> None:
        files = score.tree_files(self.record["fixtureRevision"])
        self.assertTrue(
            score.assertion_result(
                {"kind": "validation_passes", "check": "requirement-ids"},
                self.record,
                files,
            )[0]
        )
        name = ".kiro/specs/00001-gift-cards/requirements.md"
        files[name] += "\n### REQ-001: Duplicate\n"
        self.assertTrue(
            score.assertion_result(
                {"kind": "validation_reports", "check": "requirement-ids"},
                self.record,
                files,
            )[0]
        )

    def test_invalid_records_and_unsafe_paths_are_rejected(self) -> None:
        for path in ["../outside", "/outside", ".git/config", "C:\\outside"]:
            with self.subTest(path=path), self.assertRaises(score.RecordError):
                score.safe_path(path)
        self.record["files"].append(self.record["files"][0])
        with self.assertRaises(score.RecordError):
            score.validate_record(self.record)

    def test_continuation_rebuilds_parent_changes_and_deletions(self) -> None:
        child = copy.deepcopy(self.record)
        child["session"] = "child"
        child["continuesRun"] = {
            "host": "kiro-ide",
            "session": "status-summary",
            "n": 1,
        }
        child["files"] = []
        child["unchanged"] = ["result.txt"]
        with tempfile.TemporaryDirectory() as folder:
            results = Path(folder)
            path = results / "kiro-ide/status-summary/1.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(self.record))
            self.assertEqual(
                score.finished_files(child, results),
                {"result.txt": "Status reported.\n"},
            )
            child["unchanged"] = []
            self.assertEqual(score.finished_files(child, results), {})

    def test_model_pass_needs_human_sample_and_changed_evidence_rejudges(self) -> None:
        verdict = {
            "verdict": "PASS",
            "judge": "model:judge",
            "reason": "Status present",
        }
        with mock.patch.object(
            score, "model_judge", return_value=verdict, autospec=True
        ):
            self.assertEqual(
                score.score_record(
                    self.record, FIXTURES / "rubrics", judge_model="judge"
                ),
                1,
            )
        review = {
            "evidenceSha256": self.record["rubricReview"]["evidenceSha256"],
            "verdicts": {
                "SR-DLG-003:1": {
                    "verdict": "PASS",
                    "judge": "human:developer",
                    "reason": "Checked",
                }
            },
        }
        self.assertEqual(
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review), 0
        )
        self.record["messages"][1] = "Changed answer"
        self.assertEqual(score.score_record(self.record, FIXTURES / "rubrics"), 1)
        self.assertEqual(self.record["rubricReview"]["verdicts"], {})

    def test_sample_error_requires_manual_review_of_all_rubrics(self) -> None:
        evaluations = [
            (
                {
                    "rule": f"SR-DLG-{i:03}",
                    "assertions": [{"kind": "rubric", "rubric": "Check"}],
                },
                "a" * 40,
            )
            for i in range(1, 21)
        ]
        verdict = {"verdict": "PASS", "judge": "model:judge", "reason": "Checked"}
        with mock.patch.object(
            score,
            "model_judge",
            side_effect=lambda *args: verdict.copy(),
            autospec=True,
        ):
            score.rubric_verdicts(self.record, evaluations, {}, "judge", None)
        state = self.record["rubricReview"]
        review = {
            "evidenceSha256": state["evidenceSha256"],
            "verdicts": {
                state["sample"][0]: {
                    "verdict": "FAIL",
                    "judge": "human:developer",
                    "reason": "Wrong",
                }
            },
        }
        scored = score.rubric_verdicts(self.record, evaluations, {}, None, review)
        self.assertTrue(self.record["rubricReview"]["manualAll"])
        self.assertEqual(len(self.record["rubricReview"]["required"]), 20)
        self.assertFalse(any(v["passed"] for v in scored.values()))

    def test_judge_requires_reported_model_and_no_tools(self) -> None:
        for model, tools, allowed in [
            ("other-model", [], True),
            ("tested", [], False),
            ("other-model", ["Read"], False),
        ]:
            events = [
                {"type": "system", "subtype": "init", "model": model, "tools": tools},
                {
                    "type": "result",
                    "result": json.dumps(
                        {"verdict": "PASS", "reason": "The reply meets the rubric"}
                    ),
                },
            ]
            result = subprocess.CompletedProcess(
                [], 0, "\n".join(json.dumps(e) for e in events), ""
            )
            with (
                self.subTest(model=model, tools=tools),
                mock.patch.object(score.subprocess, "run", return_value=result),
            ):
                if allowed:
                    verdict = score.model_judge("other-model", "Check", {}, "tested")
                    self.assertEqual(verdict["judge"], "model:other-model")
                else:
                    with self.assertRaises(score.RecordError):
                        score.model_judge("other-model", "Check", {}, "tested")

    def test_compare_rejects_missing_status_and_revision_mismatch(self) -> None:
        other = copy.deepcopy(self.record)
        other["host"] = "codex"
        other["status"] = None
        with self.assertRaises(score.RecordError):
            score.compare([self.record, other])
        other["sessionRevision"] = "0" * 40
        with self.assertRaises(score.RecordError):
            score.compare([self.record, other])

    def test_cli_rejects_invalid_schema_and_missing_evals(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "record.json"
            path.write_text(json.dumps({**self.record, "schemaVersion": 2}))
            self.assertEqual(score.main([str(path)], FIXTURES / "evals"), 2)
            path.write_text(json.dumps(self.record))
            self.assertEqual(score.main([str(path)], root), 2)


class RunnerTest(unittest.TestCase):
    def test_interruption_leaves_a_valid_not_run_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(adapter, "turn", side_effect=KeyboardInterrupt),
                mock.patch.object(run_claude, "initialize_workspace"),
                mock.patch.object(run_claude, "verify_workspace"),
                self.assertRaises(KeyboardInterrupt),
            ):
                run_claude.run_batch(adapter, "status-summary", out)
            record = score.read_json(out / "claude-code/status-summary/1.json")
            score.validate_record(record)
            self.assertIn("interrupted", record["notRun"])
            self.assertNotIn("scores", record)

    def test_batch_setup_failure_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(
                    adapter, "batch", side_effect=run_claude.HostError("setup failed")
                ),
            ):
                self.assertEqual(
                    run_claude.run_batch(adapter, "status-summary", Path(folder)), 2
                )
            record = score.read_json(Path(folder) / "claude-code/status-summary/1.json")
            self.assertEqual(record["notRun"], "setup failed")
            self.assertNotIn("scores", record)

    def test_batch_replays_conversation_then_forks_finished_workspace(self) -> None:
        """Synthetic CLI boundary; exercises the real batch, adapter, and scorer."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sessions = root / "sessions"
            sessions.mkdir()
            sessions.joinpath("status-summary.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "name": "status-summary",
                        "fixture": "sessions/status-summary",
                        "turns": [
                            {"developer": "Status"},
                            {"developer": "Next", "expects": "Status"},
                        ],
                    }
                )
            )
            sessions.joinpath("continued.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "name": "continued",
                        "continues": "status-summary",
                        "turns": [{"developer": "Read the finished workspace"}],
                    }
                )
            )
            evals = root / "evals"
            evals.mkdir()
            for i, name in enumerate(["status-summary", "continued"], 1):
                evals.joinpath(f"SR-DLG-{i:03}.json").write_text(
                    json.dumps(
                        {
                            "schemaVersion": 1,
                            "rule": f"SR-DLG-{i:03}",
                            "session": name,
                            "assertions": [
                                {
                                    "kind": "file_matches",
                                    "path": "result.txt",
                                    "pattern": "Status reported",
                                }
                            ],
                        }
                    )
                )
            conversation_turns = {}

            def cli(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                output = ""
                if args[:2] == ["git", "init"]:
                    (cwd / ".git").mkdir()
                elif args[:2] == ["git", "rev-parse"]:
                    output = (
                        str(cwd / ".git") if "--absolute-git-dir" in args else str(cwd)
                    )
                elif args[0] == "claude":
                    count = conversation_turns.get(cwd.name, 0)
                    if count and "--resume" not in args:
                        raise AssertionError("conversation was lost")
                    if not count and "--resume" in args:
                        raise AssertionError(
                            "continuation reused the parent conversation"
                        )
                    if cwd.name == "continued":
                        self.assertEqual(
                            (cwd / "result.txt").read_text(), "Status reported"
                        )
                    (cwd / "result.txt").write_text("Status reported")
                    conversation_turns[cwd.name] = count + 1
                    output = "\n".join(
                        json.dumps(e)
                        for e in [
                            {
                                "type": "system",
                                "subtype": "init",
                                "model": "tested-model",
                                "claude_code_version": "fixture-version",
                                "session_id": cwd.name,
                                "skills": ["specflow:spec-workflow"],
                            },
                            {
                                "type": "assistant",
                                "message": {
                                    "content": [
                                        {
                                            "type": "tool_use",
                                            "name": "Read",
                                            "input": {
                                                "file_path": str(cwd / "result.txt")
                                            },
                                        }
                                    ]
                                },
                            },
                            {
                                "type": "result",
                                "subtype": "success",
                                "result": "Status reported",
                                "total_cost_usd": 0.25 * (count + 1),
                            },
                        ]
                    )
                elif "validate_spec.py" in " ".join(args):
                    output = json.dumps(
                        score.read_json(FIXTURES / "manual.json")["status"]
                    )
                return subprocess.CompletedProcess(args, 0, output, "")

            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(run_claude, "command", side_effect=cli),
            ):
                self.assertEqual(
                    run_claude.run_batch(
                        adapter,
                        "continued",
                        root / "results",
                        session_dir=sessions,
                        eval_dir=evals,
                    ),
                    0,
                )
            parent = score.read_json(root / "results/claude-code/status-summary/1.json")
            child = score.read_json(root / "results/claude-code/continued/1.json")
            self.assertEqual(len(parent["messages"]), 2)
            self.assertEqual(
                child["continuesRun"],
                {"host": "claude-code", "session": "status-summary", "n": 1},
            )
            self.assertIn("result.txt", child["unchanged"])
            self.assertTrue(child["scores"][0]["passed"])
            self.assertNotIn(str(root), json.dumps([parent, child]))

    def test_claude_permission_denial_and_model_omission_are_failures(self) -> None:
        adapter = run_claude.Claude("tested-model")
        for final in [
            {"is_error": True},
            {"permission_denials": ["Read"]},
            {"subtype": "success"},
        ]:
            result = subprocess.CompletedProcess(
                [], 0, json.dumps({"type": "result", **final}), ""
            )
            with (
                self.subTest(final=final),
                mock.patch.object(run_claude, "command", return_value=result),
                self.assertRaises(run_claude.HostError),
            ):
                adapter.turn("Status", ROOT)

    def test_command_timeout_kills_process_and_captures_failures(self) -> None:
        result = run_claude.command(
            [sys.executable, "-c", "import sys; print('failed'); sys.exit(7)"], ROOT
        )
        self.assertEqual((result.returncode, result.stdout.strip()), (7, "failed"))
        with self.assertRaises(subprocess.TimeoutExpired):
            run_claude.command(
                [sys.executable, "-c", "import time; time.sleep(10)"], ROOT, timeout=1
            )

    def test_git_failure_never_initializes_parent_or_invokes_host(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            failed = subprocess.CompletedProcess([], 1, "", "denied")
            with (
                mock.patch.object(run_claude, "command", return_value=failed),
                self.assertRaisesRegex(run_claude.HostError, "denied"),
            ):
                run_claude.initialize_workspace(workspace)
            self.assertEqual(list(workspace.iterdir()), [])

    def test_capture_rejects_symlinks_and_external_edit_paths(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / "link").symlink_to(ROOT)
            with self.assertRaises(run_claude.HostError):
                run_claude.snapshot(workspace)
            with self.assertRaises(run_claude.HostError):
                run_claude.write_files(workspace, {"link/forbidden": "no"})

    def test_normalization_includes_embedded_contents_and_keys(self) -> None:
        value = {
            "/home/user/work/file": [
                "read /home/user/work/file and /home/user/plugin/SKILL.md",
                {"text": "/home/user/private"},
            ]
        }
        result = run_claude.normalize(
            value,
            {
                "/home/user/work": "<workspace>",
                "/home/user/plugin": "<plugin>",
                "/home/user": "<home>",
            },
        )
        self.assertEqual(
            result,
            {
                "<workspace>/file": [
                    "read <workspace>/file and <plugin>/SKILL.md",
                    {"text": "<home>/private"},
                ]
            },
        )

    def test_package_hash_matches_git_and_detects_mismatch(self) -> None:
        expected = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        self.assertEqual(run_claude.package_revision(score.PLUGIN), expected)
        with self.assertRaisesRegex(run_claude.HostError, "differs"):
            run_claude.verify_plugin(score.PLUGIN, "0" * 40)

    def test_enclosing_repository_is_rejected_before_host_turn(self) -> None:
        with (
            tempfile.TemporaryDirectory() as folder,
            self.assertRaisesRegex(run_claude.HostError, "own .git"),
        ):
            run_claude.verify_workspace(Path(folder))

    def test_rerun_never_overwrites_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            first, number = run_claude.reserve_record(out, "codex", "sample")
            first.write_text("retained")
            second, next_number = run_claude.reserve_record(out, "codex", "sample")
            self.assertEqual((number, next_number), (1, 2))
            self.assertEqual(first.read_text(), "retained")
            self.assertNotEqual(first, second)

    def test_blocked_launch_records_not_run_without_starting_host(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            adapter = run_claude.Claude("test-model")
            with mock.patch.object(
                adapter, "turn", side_effect=AssertionError("must not launch")
            ):
                self.assertEqual(
                    run_claude.run_batch(adapter, "status-summary", out), 2
                )
            record = score.read_json(out / "claude-code/status-summary/1.json")
            self.assertIn("isolation", record["notRun"])
            self.assertNotIn("scores", record)
            self.assertFalse(record["releaseEvidence"])
            score.validate_record(record)

    def test_edit_precedes_turn_and_expects_breaks_without_a_second_reply(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            record = score.read_json(FIXTURES / "manual.json")
            record["messages"], record["filesRead"] = [], []
            adapter = run_claude.Claude("test-model")
            session = {
                "turns": [
                    {
                        "developer": "Read it",
                        "edit": {"path": "note.md", "text": "second writer"},
                    },
                    {"developer": "Continue", "expects": "approve"},
                ]
            }

            def turn(prompt: str, root: Path) -> tuple[str, list[str]]:
                self.assertEqual((root / "note.md").read_text(), "second writer")
                return "Stop here", []

            with (
                mock.patch.object(adapter, "turn", side_effect=turn),
                mock.patch.object(run_claude, "verify_workspace"),
                mock.patch.object(
                    run_claude, "capture_status", return_value=record["status"]
                ),
            ):
                run_claude.play_session(adapter, session, workspace, record)
            self.assertEqual(record["brokenAt"], 2)
            self.assertEqual(record["messages"], ["Stop here"])
            self.assertEqual(
                record["files"], [{"path": "note.md", "text": "second writer"}]
            )


if __name__ == "__main__":
    unittest.main()

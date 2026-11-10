"""Stored-record checks for the eval instruments; no signed-in host required."""

from __future__ import annotations

import contextlib
import copy
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from collections.abc import Iterator
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/specflow/evals/runners"))
import run_claude
import run_codex
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
        self.assertFalse(self.record["rubricReview"]["manualAll"])
        review["verdicts"][state["sample"][1]] = {
            "verdict": "FAIL",
            "judge": "human:developer",
            "reason": "Second wrong judgment",
        }
        scored = score.rubric_verdicts(self.record, evaluations, {}, None, review)
        self.assertTrue(self.record["rubricReview"]["manualAll"])
        self.assertEqual(len(self.record["rubricReview"]["required"]), 20)
        self.assertFalse(any(v["passed"] for v in scored.values()))

    def test_pass_sample_has_minimum_and_rounds_up_without_rerolling(self) -> None:
        for count, expected in [(0, 0), (3, 3), (10, 10), (11, 10), (101, 11)]:
            with self.subTest(count=count):
                record = copy.deepcopy(self.record)
                evaluations = [
                    (
                        {
                            "rule": f"SR-DLG-{i:03}",
                            "assertions": [{"kind": "rubric", "rubric": "Check"}],
                        },
                        "a" * 40,
                    )
                    for i in range(1, count + 1)
                ]
                # One FAIL ensures the empty PASS population still has review state.
                evaluations.append(
                    (
                        {
                            "rule": "SR-DLG-999",
                            "assertions": [{"kind": "rubric", "rubric": "Fail"}],
                        },
                        "a" * 40,
                    )
                )
                verdicts = [
                    {"verdict": "PASS", "judge": "model:judge", "reason": "Checked"}
                    for _ in range(count)
                ] + [{"verdict": "FAIL", "judge": "model:judge", "reason": "Failed"}]
                with mock.patch.object(
                    score, "model_judge", side_effect=verdicts, autospec=True
                ):
                    score.rubric_verdicts(record, evaluations, {}, "judge", None)
                sample = record["rubricReview"]["sample"].copy()
                self.assertEqual(len(sample), expected)
                self.assertIn("SR-DLG-999:1", record["rubricReview"]["required"])
                score.rubric_verdicts(record, evaluations, {}, None, None)
                self.assertEqual(record["rubricReview"]["sample"], sample)

    def test_release_eligibility_does_not_invalidate_human_judgment(self) -> None:
        verdict = {"verdict": "PASS", "judge": "model:judge", "reason": "Checked"}
        with mock.patch.object(
            score, "model_judge", return_value=verdict, autospec=True
        ):
            score.score_record(self.record, FIXTURES / "rubrics", judge_model="judge")
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
        self.record["releaseEvidence"] = True
        self.assertEqual(
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review), 0
        )
        with (
            mock.patch.object(score, "JUDGE_PROMPT", "Changed judging instructions"),
            self.assertRaisesRegex(score.RecordError, "different evidence"),
        ):
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review)
        self.record["instructionFiles"].append("<home>/AGENTS.md")
        with self.assertRaisesRegex(score.RecordError, "different evidence"):
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review)

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
                mock.patch.object(
                    run_claude, "command", return_value=result, autospec=True
                ),
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
    def test_batch_deadline_covers_setup_and_scoring(self) -> None:
        for phase, expected_code in [("setup", 2), ("scoring", 1)]:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as folder:
                clock = [0.0]
                adapter = run_claude.Claude("tested-model")

                def expire(
                    *args: object, clock: list[float] = clock, **kwargs: object
                ) -> int:
                    clock[0] = run_claude.BATCH_TIMEOUT + 1
                    return 0

                with (
                    mock.patch.object(
                        score.time,
                        "monotonic",
                        side_effect=lambda clock=clock: clock[0],
                    ),
                    mock.patch.object(
                        adapter,
                        "preflight",
                        side_effect=expire if phase == "setup" else None,
                    ),
                    mock.patch.object(
                        adapter, "turn", return_value=("Reply", [])
                    ) as host,
                    mock.patch.object(
                        run_claude, "initialize_workspace", autospec=True
                    ),
                    mock.patch.object(run_claude, "verify_workspace", autospec=True),
                    mock.patch.object(
                        run_claude,
                        "capture_status",
                        return_value=score.read_json(FIXTURES / "manual.json")[
                            "status"
                        ],
                    ),
                    mock.patch.object(
                        score, "score_record", side_effect=expire, autospec=True
                    ),
                ):
                    code = run_claude.run_batch(adapter, "status-summary", Path(folder))
                self.assertEqual(code, expected_code)
                record = score.read_json(
                    Path(folder) / "claude-code/status-summary/1.json"
                )
                self.assertIn("deadline", record["notRun"])
                self.assertNotIn("scores", record)
                if phase == "setup":
                    host.assert_not_called()

    def test_sigterm_unwinds_and_restores_the_previous_handler(self) -> None:
        previous = signal.getsignal(signal.SIGTERM)
        with self.assertRaises(KeyboardInterrupt), run_claude.interruption_signals():
            signal.raise_signal(signal.SIGTERM)
        self.assertEqual(signal.getsignal(signal.SIGTERM), previous)

    def test_timeout_kills_a_descendant_that_ignores_termination(self) -> None:
        child = (
            "import signal,time; "
            "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
            "print('child-ready',flush=True); time.sleep(30)"
        )
        parent = (
            "import subprocess,sys,time; "
            f"subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(30)"
        )
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired) as caught:
            run_claude.command([sys.executable, "-c", parent], ROOT, timeout=1)
        self.assertIn(b"child-ready", caught.exception.output)
        # The child keeps the captured pipe open and ignores TERM. communicate
        # cannot finish this soon unless cleanup also terminates that descendant.
        self.assertLess(time.monotonic() - started, 15)

    def test_enclosing_deadline_limits_commands_without_starting_after_expiry(
        self,
    ) -> None:
        clock = [0.0]
        with mock.patch.object(
            score.time, "monotonic", side_effect=lambda clock=clock: clock[0]
        ):
            with score.deadline(50):
                clock[0] = 10
                with score.deadline(100):
                    self.assertEqual(score.remaining_timeout(600), 40)
                    clock[0] = 50
                    with (
                        mock.patch.object(run_claude.subprocess, "Popen") as start,
                        self.assertRaises(subprocess.TimeoutExpired),
                    ):
                        run_claude.command(["must-not-start"], ROOT)
                    start.assert_not_called()
            self.assertEqual(score.remaining_timeout(600), 600)

    def test_session_deadline_stops_between_turns_and_retains_reply(self) -> None:
        clock = [0.0]
        record = score.read_json(FIXTURES / "manual.json")
        record["messages"], record["filesRead"] = [], []
        adapter = run_claude.Claude("tested-model")

        def turn(prompt: str, workspace: Path) -> tuple[str, list[str]]:
            clock[0] = run_claude.SESSION_TIMEOUT + 1
            return "First reply", []

        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch.object(
                score.time, "monotonic", side_effect=lambda clock=clock: clock[0]
            ),
            mock.patch.object(run_claude, "verify_workspace", autospec=True),
            mock.patch.object(adapter, "turn", side_effect=turn, autospec=True) as host,
        ):
            run_claude.play_session(
                adapter,
                {"turns": [{"developer": "First"}, {"developer": "Second"}]},
                Path(folder),
                record,
            )
        self.assertEqual(host.call_count, 1)
        self.assertEqual(record["messages"], ["First reply"])
        self.assertIn("deadline", record["notRun"])

    def test_turn_limit_rejects_continuation_before_host_setup(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "parent.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "name": "parent",
                        "fixture": "sessions/status-summary",
                        "turns": [{"developer": "Start"}],
                    }
                )
            )
            (root / "child.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "name": "child",
                        "continues": "parent",
                        "turns": [{"developer": "Again"}] * 25,
                    }
                )
            )
            with self.assertRaisesRegex(score.RecordError, "turn limit"):
                run_claude.sessions_for("parent", root)

    def test_failed_workspace_setup_never_enters_host_batch(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight", autospec=True),
                mock.patch.object(adapter, "batch", autospec=True) as batch,
                mock.patch.object(
                    run_claude,
                    "initialize_workspace",
                    autospec=True,
                    side_effect=run_claude.HostError("workspace initialization denied"),
                ),
            ):
                code = run_claude.run_batch(adapter, "status-summary", Path(folder))
            self.assertEqual(code, 2)
            batch.assert_not_called()
            record = score.read_json(Path(folder) / "claude-code/status-summary/1.json")
            self.assertIn("initialization denied", record["notRun"])

    def test_interruption_leaves_a_valid_not_run_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(adapter, "turn", side_effect=KeyboardInterrupt),
                mock.patch.object(run_claude, "initialize_workspace"),
                mock.patch.object(run_claude, "verify_workspace"),
            ):
                self.assertEqual(
                    run_claude.run_batch(adapter, "status-summary", out), 2
                )
            record = score.read_json(out / "claude-code/status-summary/1.json")
            score.validate_record(record)
            self.assertIn("interrupted", record["notRun"])
            self.assertNotIn("scores", record)

    def test_batch_setup_failure_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(run_claude, "initialize_workspace", autospec=True),
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
            self.assertEqual(record["model"], "test-model")
            self.assertEqual(record["hostVersion"], "not-started")
            self.assertIsNone(record["status"])
            self.assertEqual(record["messages"], [])
            self.assertEqual(record["files"], [])
            self.assertEqual(record["instructionMeasurement"], "not-measured")
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


class CodexHomeTest(unittest.TestCase):
    """Synthetic sign-in and installer; no installed host or real credential used."""

    @staticmethod
    def provision(home: Path) -> None:
        assert list(home.iterdir()) == []
        fd = os.open(home / "auth.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write('{"synthetic": "fixture-only"}')

    def test_unprovisioned_or_nonprivate_sign_in_never_installs(self) -> None:
        for mode in (None, 0o644):
            with (
                self.subTest(mode=mode),
                self.environment() as (workspace, _sign_in, scratch),
            ):

                def provision(home: Path, mode: int | None = mode) -> None:
                    if mode is not None:
                        self.provision(home)
                        (home / "auth.json").chmod(mode)

                with (
                    mock.patch.object(run_claude, "verify_workspace", autospec=True),
                    mock.patch.object(
                        run_claude, "command", autospec=True
                    ) as installer,
                    self.assertRaisesRegex(run_claude.HostError, "independent sign-in"),
                    run_codex.temporary_home(
                        workspace, "0" * 40, scratch=scratch, provision=provision
                    ),
                ):
                    self.fail("invalid credentials must not reach installation")
                installer.assert_not_called()
                self.assertEqual(list(scratch.iterdir()), [])

    @contextlib.contextmanager
    def environment(self) -> Iterator[tuple[Path, Path, Path]]:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            workspace = root / "workspace"
            workspace.mkdir()
            sign_in = root / "auth.json"
            sign_in.write_text('{"synthetic": "fixture-only"}')
            scratch = root / "scratch"
            scratch.mkdir()
            yield workspace, sign_in, scratch

    def test_home_is_private_and_removed_after_success(self) -> None:
        with self.environment() as (workspace, sign_in, scratch):
            before = sign_in.read_bytes()
            observed = []

            def installer(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                home = Path(env["CODEX_HOME"])
                observed.append(home)
                self.assertEqual(cwd, workspace)
                self.assertEqual(home.stat().st_mode & 0o777, 0o700)
                self.assertEqual((home / "auth.json").stat().st_mode & 0o777, 0o600)
                self.assertEqual((home / "auth.json").read_bytes(), before)
                if args[1:3] == ["plugin", "add"]:
                    plugin = home / "plugins/cache/buvis-agent-plugins/specflow/0.1.0"
                    plugin.mkdir(parents=True)
                    (plugin / "plugin.json").write_text('{"name":"specflow"}')
                return subprocess.CompletedProcess(args, 0, "{}", "")

            expected_dir = workspace / "expected"
            expected_dir.mkdir()
            (expected_dir / "plugin.json").write_text('{"name":"specflow"}')
            revision = run_claude.package_revision(expected_dir)
            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=installer, autospec=True
                ),
                run_codex.temporary_home(
                    workspace, revision, scratch=scratch, provision=self.provision
                ) as home,
            ):
                self.assertEqual(len(observed), 2)
                self.assertEqual(list(home.glob("AGENTS*")), [])
                self.assertFalse((home / "config.toml").exists())
            self.assertFalse(home.exists())
            self.assertEqual(list(scratch.iterdir()), [])
            self.assertEqual(sign_in.read_bytes(), before)

    def test_installer_failures_and_interruptions_remove_home(self) -> None:
        for error in (OSError("installer failed"), KeyboardInterrupt()):
            with (
                self.subTest(error=type(error).__name__),
                self.environment() as (workspace, sign_in, scratch),
            ):
                with (
                    mock.patch.object(run_claude, "verify_workspace", autospec=True),
                    mock.patch.object(
                        run_claude, "command", side_effect=error, autospec=True
                    ),
                    self.assertRaises(type(error)),
                    run_codex.temporary_home(
                        workspace, "0" * 40, scratch=scratch, provision=self.provision
                    ),
                ):
                    self.fail("failed install must not yield a home")
                self.assertEqual(list(scratch.iterdir()), [])
                self.assertTrue(sign_in.exists())

    def test_mismatch_removes_home_and_cli_returns_two(self) -> None:
        with self.environment() as (workspace, sign_in, scratch):

            def installer(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                if args[1:3] == ["plugin", "add"]:
                    plugin = (
                        Path(env["CODEX_HOME"])
                        / "plugins/cache/buvis-agent-plugins/specflow/0.1.0"
                    )
                    plugin.mkdir(parents=True)
                    (plugin / "plugin.json").write_text('{"name":"wrong revision"}')
                return subprocess.CompletedProcess(args, 0, "{}", "")

            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=installer, autospec=True
                ),
                self.assertRaisesRegex(run_claude.HostError, "differs"),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                self.fail("mismatched package must not yield a home")
            self.assertEqual(list(scratch.iterdir()), [])
            adapter = run_codex.Codex("tested-model")
            adapter.provision = self.provision
            with (
                mock.patch.object(adapter, "preflight", autospec=True),
                mock.patch.object(run_claude, "initialize_workspace", autospec=True),
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=installer, autospec=True
                ),
                mock.patch.object(
                    run_codex.Path, "home", return_value=sign_in.parent, autospec=True
                ),
            ):
                auth_dir = sign_in.parent / ".codex"
                auth_dir.mkdir()
                (auth_dir / "auth.json").write_bytes(sign_in.read_bytes())
                code = run_claude.run_batch(
                    adapter, "status-summary", scratch / "results"
                )
            self.assertEqual(code, 2)
            record = score.read_json(scratch / "results/codex/status-summary/1.json")
            self.assertIn("differs", record["notRun"])
            self.assertNotIn("scores", record)

    def test_nonzero_installer_never_persists_its_output(self) -> None:
        with self.environment() as (workspace, _sign_in, scratch):
            failure = subprocess.CompletedProcess(
                [], 7, "synthetic-secret", "synthetic-secret"
            )
            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", return_value=failure, autospec=True
                ),
                self.assertRaisesRegex(
                    run_claude.HostError, r"^Codex plugin setup failed \(exit 7\)$"
                ),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                self.fail("failed install must not yield a home")
            self.assertEqual(list(scratch.iterdir()), [])

    def test_body_failure_and_missing_package_remove_home(self) -> None:
        with self.environment() as (workspace, _sign_in, scratch):

            def installer(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                plugin = (
                    Path(env["CODEX_HOME"])
                    / "plugins/cache/buvis-agent-plugins/specflow/0.1.0"
                )
                plugin.mkdir(parents=True, exist_ok=True)
                (plugin / "plugin.json").write_text("{}")
                return subprocess.CompletedProcess(args, 0, "{}", "")

            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=installer, autospec=True
                ),
                mock.patch.object(run_claude, "verify_plugin", autospec=True),
                self.assertRaisesRegex(run_claude.HostError, "turn failed"),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                raise run_claude.HostError("turn failed")
            self.assertEqual(list(scratch.iterdir()), [])
            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude,
                    "command",
                    return_value=subprocess.CompletedProcess([], 0, "{}", ""),
                    autospec=True,
                ),
                self.assertRaisesRegex(run_claude.HostError, "exactly one"),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                self.fail("missing package must not yield a home")
            self.assertEqual(list(scratch.iterdir()), [])

    def test_unverified_workspace_never_reads_sign_in_or_runs_installer(self) -> None:
        with self.environment() as (workspace, sign_in, scratch):
            sign_in.unlink()
            with (
                mock.patch.object(run_claude, "command", autospec=True) as command,
                self.assertRaisesRegex(run_claude.HostError, "own .git"),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                self.fail("unverified workspace must not yield a home")
            command.assert_not_called()
            self.assertEqual(list(scratch.iterdir()), [])

    def test_codex_entry_point_records_blockers_without_setup(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(run_codex, "temporary_home", autospec=True) as setup:
                self.assertEqual(
                    run_claude.main(
                        ["status-summary", "--model", "tested-model", "--out", folder],
                        adapter_type=run_codex.Codex,
                    ),
                    2,
                )
            setup.assert_not_called()
            record = score.read_json(Path(folder) / "codex/status-summary/1.json")
            self.assertIn("independent sign-in", record["notRun"])
            self.assertFalse(record["releaseEvidence"])


if __name__ == "__main__":
    unittest.main()

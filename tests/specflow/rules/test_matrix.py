"""The batch must retain failures and continue independent sessions."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals/runners"))
import run_matrix
import score


class MatrixTest(unittest.TestCase):
    def test_failure_does_not_stop_independent_sessions(self) -> None:
        proof = {"checks": {k: {"passed": True} for k in score.RELEASE_BOUNDARY_CHECKS}}
        probe, adapter = Mock(return_value=proof), Mock()
        run = Mock(side_effect=[1, 2, 0])
        with tempfile.TemporaryDirectory() as folder:
            rows = run_matrix.execute_host(
                "codex",
                "explicit",
                Path(folder),
                Path(folder),
                run=run,
                registry={"codex": (adapter, probe, "explicit")},
                selected=["a", "b", "c"],
            )
        self.assertEqual([r["code"] for r in rows], [1, 2, 0])
        self.assertEqual(run.call_count, 3)
        probe.assert_called_once_with("explicit")

    def test_failed_probe_blocks_every_session(self) -> None:
        run = Mock()
        with tempfile.TemporaryDirectory() as folder:
            rows = run_matrix.execute_host(
                "codex",
                "explicit",
                Path(folder),
                Path(folder),
                run=run,
                registry={
                    "codex": (Mock(), Mock(return_value={"checks": {}}), "explicit")
                },
                selected=["a", "b"],
            )
        run.assert_not_called()
        self.assertEqual([r["code"] for r in rows], [2, 2])

    def test_smoke_contains_all_approved_phases(self) -> None:
        self.assertEqual(len(run_matrix.SMOKE), 9)
        self.assertIn("conversion-calcard", run_matrix.groups("codex"))
        self.assertIn("completion-success", run_matrix.groups("kiro-ide"))

    def test_all_scenarios_have_valid_evals_and_fixtures(self) -> None:
        for session in run_matrix.runner.SESSIONS.glob("*.json"):
            with self.subTest(session=session.stem):
                root = run_matrix.runner.sessions_for(session.stem)[0][1]
                self.assertTrue((run_matrix.runner.FIXTURES / root["fixture"]).is_dir())
                evals = [
                    score.read_json(p)
                    for p in run_matrix.eval_directory(session.stem).glob("SR-*.json")
                ]
                matching = [e for e in evals if e["session"] == session.stem]
                self.assertTrue(matching)
                for evaluation in matching:
                    self.assertEqual(
                        score.check_schema(
                            evaluation,
                            score.read_json(score.SCHEMAS / "eval.schema.json"),
                        ),
                        [],
                    )


class ContinuationTest(unittest.TestCase):
    def test_pending_rubric_does_not_block_evidence_collection(self) -> None:
        record = {"scores": [{"failures": [{"kind": "rubric"}], "rubrics": []}]}
        self.assertTrue(run_matrix.runner.continuation_ready(record))

    def test_deterministic_failure_blocks_child(self) -> None:
        record = {"scores": [{"failures": [{"kind": "file_matches"}], "rubrics": []}]}
        self.assertFalse(run_matrix.runner.continuation_ready(record))

    def test_observed_rubric_failure_blocks_child(self) -> None:
        record = {"scores": [{"failures": [], "rubrics": [{"verdict": "FAIL"}]}]}
        self.assertFalse(run_matrix.runner.continuation_ready(record))

    def test_not_run_blocks_child(self) -> None:
        self.assertFalse(
            run_matrix.runner.continuation_ready({"notRun": "interrupted"})
        )

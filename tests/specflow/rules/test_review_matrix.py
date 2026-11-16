"""A host's review sample spans sessions and remains bound to the frozen evidence."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals/runners"))
import review_matrix
import score


def catalog() -> dict:
    return {
        f"claude-code/session-{i}/1.json": {
            "host": "claude-code",
            "evidenceSha256": str(i),
            "verdicts": {
                f"SR-REQ-001:{j}": {
                    "verdict": "PASS",
                    "judge": "model:judge",
                    "reason": "evidence",
                }
                for j in range(12)
            },
        }
        for i in range(3)
    }


class HostReviewTest(unittest.TestCase):
    def test_ten_passes_across_sessions_not_ten_per_session(self) -> None:
        batch = review_matrix.selection(catalog())
        self.assertEqual(len(batch["samples"]["claude-code"]), 10)
        self.assertEqual(len(review_matrix.required(batch, "claude-code")[0]), 10)

    def test_failures_always_require_review(self) -> None:
        data = catalog()
        data["claude-code/session-0/1.json"]["verdicts"]["SR-REQ-001:0"]["verdict"] = (
            "FAIL"
        )
        batch = review_matrix.selection(data)
        required, _ = review_matrix.required(batch, "claude-code")
        self.assertIn("claude-code/session-0/1.json#SR-REQ-001:0", required)
        self.assertEqual(len(required), 11)

    def test_two_wrong_of_ten_escalate_entire_host(self) -> None:
        batch = review_matrix.selection(catalog())
        for key in batch["samples"]["claude-code"][:2]:
            batch["verdicts"][key] = {
                "verdict": "FAIL",
                "judge": "human:developer",
                "reason": "incorrect",
            }
        keys, manual_all = review_matrix.required(batch, "claude-code")
        self.assertTrue(manual_all)
        self.assertEqual(len(keys), 36)

    def test_one_wrong_does_not_escalate(self) -> None:
        batch = review_matrix.selection(catalog())
        batch["verdicts"][batch["samples"]["claude-code"][0]] = {
            "verdict": "FAIL",
            "judge": "human:developer",
            "reason": "incorrect",
        }
        self.assertFalse(review_matrix.required(batch, "claude-code")[1])

    def test_rescoring_keeps_sample(self) -> None:
        batch = review_matrix.selection(catalog())
        self.assertEqual(review_matrix.selection(catalog(), batch), batch)

    def test_changed_evidence_rejects_old_sample(self) -> None:
        batch = review_matrix.selection(catalog())
        data = catalog()
        data["claude-code/session-0/1.json"]["evidenceSha256"] = "changed"
        with self.assertRaises(score.RecordError):
            review_matrix.selection(data, batch)

    def test_empty_host_requires_no_sample(self) -> None:
        batch = review_matrix.selection({})
        self.assertEqual(review_matrix.required(batch, "codex"), (set(), False))

    def test_duplicate_sample_is_rejected(self) -> None:
        batch = review_matrix.selection(catalog())
        batch["samples"]["claude-code"][1] = batch["samples"]["claude-code"][0]
        with self.assertRaises(score.RecordError):
            review_matrix.required(batch, "claude-code")

"""Scripted replies require an input request, not a particular prose layout."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[1] / "evals/sessions"


class SessionPreconditionsTest(unittest.TestCase):
    def test_review_reply_accepts_a_choice_request_without_question_mark(self) -> None:
        session = json.loads((SESSIONS / "requirements-review.json").read_text())
        pattern = session["turns"][1]["expects"]
        for request in (
            "Pick 1, 2, 3, or 4.",
            'Reply "confirm" to accept the recommendations.',
            "Tell me your answers to the decisions.",
            "I still need the owner's name.",
        ):
            with self.subTest(request=request):
                self.assertRegex(request, pattern)
        self.assertNotRegex("All work is complete.", pattern)

    def test_first_turn_needs_no_previous_reply(self) -> None:
        for path in sorted(SESSIONS.glob("*.json")):
            with self.subTest(session=path.stem):
                session = json.loads(path.read_text())
                self.assertNotIn("expects", session["turns"][0])

    def test_question_preconditions_allow_options_after_question(self) -> None:
        for path in sorted(SESSIONS.glob("*.json")):
            session = json.loads(path.read_text())
            for number, turn in enumerate(session["turns"][1:], 2):
                pattern = turn.get("expects")
                if pattern and re.search(pattern, "Which option?"):
                    with self.subTest(session=path.stem, turn=number):
                        self.assertRegex(
                            "Which option?\n1. CSV (Recommended)\n2. PDF", pattern
                        )
                        self.assertIsNone(re.search(pattern, "No question here."))

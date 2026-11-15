"""The diagnostic retains only the selected normalized channels."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals/runners"))
from capture_codex_fields import selected_fields


class CaptureTests(unittest.TestCase):
    def test_capture_excludes_other_fields_and_normalizes_text(self) -> None:
        state = {
            "permissions": {"instructions": "/synthetic/home/policy", "other": "omit"},
            "host_skills": {"body": "/synthetic/home/skills"},
            "unrelated": "omit",
        }
        self.assertEqual(selected_fields(state, lambda text: text.replace(
            "/synthetic/home", "<home>"
        )), {
            "permissions.instructions": "<home>/policy",
            "host_skills.body": "<home>/skills",
        })

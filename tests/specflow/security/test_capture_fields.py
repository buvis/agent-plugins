"""The diagnostic retains only the selected normalized channels."""

import sys
import hashlib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals/runners"))
from capture_codex_fields import permission_text, selected_fields


class CaptureTests(unittest.TestCase):
    def test_permission_text_requires_host_hash_and_developer_role(self) -> None:
        text = "<permissions instructions>\nSynthetic policy.\n</permissions instructions>"
        digest = hashlib.sha1(b"codex-world-state-fragment-v1\0")
        for part in (b"developer", text.encode()):
            digest.update(len(part).to_bytes(8, "big"))
            digest.update(part)
        items = [{"role": "developer", "content": [{"text": "prefix\n" + text}]}]
        self.assertEqual(permission_text(items, digest.hexdigest()), text)
        self.assertIsNone(permission_text(items, "0" * 40))
        items[0]["role"] = "user"
        self.assertIsNone(permission_text(items, digest.hexdigest()))

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

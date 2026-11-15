"""The diagnostic retains only the selected normalized channels."""

import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals/runners"))
import run_codex
from capture_codex_fields import permission_text, selected_fields


class CaptureTests(unittest.TestCase):
    def test_missing_live_policy_prevents_rendering(self) -> None:
        adapter = run_codex.Codex("synthetic")
        with patch.object(run_codex.runner, "command") as command:
            self.assertIsNone(
                adapter.measured_channels(
                    {"permissions": {"instructions": "0" * 40}}, Path("/synthetic")
                )
            )
            command.assert_not_called()

    def test_unverified_permission_text_never_produces_channels(self) -> None:
        from subprocess import CompletedProcess

        adapter = run_codex.Codex("synthetic")
        adapter.executable = "synthetic-codex"
        with (
            patch.object(adapter, "environment", return_value={}),
            patch.object(
                adapter, "effective_profile", side_effect=lambda value, workspace: value
            ),
            patch.object(
                run_codex.runner,
                "command",
                return_value=CompletedProcess([], 0, "[]", ""),
            ),
        ):
            self.assertIsNone(
                adapter.measured_channels(
                    {"permissions": {"instructions": "0" * 40}},
                    Path("/synthetic"),
                    {"approval_policy": "never", "model": "recorded-model"},
                )
            )
            self.assertEqual(adapter.permission_diagnostic["rendererExit"], 0)

    def test_permission_text_requires_host_hash_and_developer_role(self) -> None:
        text = (
            "<permissions instructions>\nSynthetic policy.\n</permissions instructions>"
        )
        digest = hashlib.sha1(b"codex-world-state-fragment-v1\0")
        for part in (b"developer", text.encode()):
            digest.update(len(part).to_bytes(8, "big"))
            digest.update(part)
        items = [{"role": "developer", "content": [{"text": "prefix\n" + text}]}]
        self.assertEqual(permission_text(items, digest.hexdigest()), text)
        from subprocess import CompletedProcess

        adapter = run_codex.Codex("synthetic")
        adapter.executable = "synthetic-codex"
        state = {"permissions": {"instructions": digest.hexdigest()}}
        import json

        with (
            patch.object(adapter, "environment", return_value={}),
            patch.object(
                adapter, "effective_profile", side_effect=lambda value, workspace: value
            ),
            patch.object(
                run_codex.runner,
                "command",
                return_value=CompletedProcess([], 0, json.dumps(items), ""),
            ) as command,
        ):
            self.assertEqual(
                adapter.measured_channels(
                    state,
                    Path("/synthetic"),
                    {"approval_policy": "never", "model": "recorded-model"},
                ),
                run_codex.instruction_channels(
                    {"permissions": {"instructions": text}}, lambda value: value
                ),
            )
            arguments = command.call_args.args[0]
            self.assertIn('approval_policy="never"', arguments)
            self.assertIn('model="recorded-model"', arguments)
        self.assertEqual(state["permissions"]["instructions"], digest.hexdigest())
        self.assertIsNone(permission_text(items, "0" * 40))
        items[0]["role"] = "user"
        self.assertIsNone(permission_text(items, digest.hexdigest()))

    def test_capture_excludes_other_fields_and_normalizes_text(self) -> None:
        state = {
            "permissions": {"instructions": "/synthetic/home/policy", "other": "omit"},
            "host_skills": {"body": "/synthetic/home/skills"},
            "unrelated": "omit",
        }
        self.assertEqual(
            selected_fields(
                state, lambda text: text.replace("/synthetic/home", "<home>")
            ),
            {
                "permissions.instructions": "<home>/policy",
                "host_skills.body": "<home>/skills",
            },
        )

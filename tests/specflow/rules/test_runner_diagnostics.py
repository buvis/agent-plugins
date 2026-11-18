"""Failures must retain their cause without weakening proof or package checks."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals/runners"))
import run_claude as runner
import run_matrix
import score


class RunnerDiagnosticsTest(unittest.TestCase):
    def test_denied_tool_is_named_without_retaining_its_arguments(self) -> None:
        adapter = runner.Claude("fixture-model")
        events = [
            {
                "type": "result",
                "subtype": "success",
                "permission_denials": [
                    {"tool_name": "Agent", "tool_input": {"prompt": "private argument"}}
                ],
            }
        ]
        with (
            mock.patch.object(adapter, "preflight"),
            mock.patch.object(adapter, "launch", return_value=events),
            self.assertRaises(runner.HostError) as caught,
        ):
            adapter.turn("Review", Path("/synthetic-workspace"))
        self.assertIn("Agent", str(caught.exception))
        self.assertNotIn("private argument", str(caught.exception))

    def test_boundary_rejection_names_mismatched_field(self) -> None:
        adapter = runner.Claude("fixture-model")
        adapter.version = "new-version"
        adapter.configuration_sha256 = "c" * 64
        revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        adapter.boundary = {
            "scope": "installed-host-boundary",
            "host": adapter.host,
            "hostVersion": "old-version",
            "runtimeRevision": revision,
            "configurationSha256": adapter.configuration_sha256,
            "runnerSha256": runner.runner_digest(adapter),
            "checks": {k: {"passed": True} for k in score.RELEASE_BOUNDARY_CHECKS},
        }
        with self.assertRaisesRegex(runner.HostError, "hostVersion.*old-version"):
            runner.accept_boundary(adapter, revision)

    def test_package_rejection_names_permission_change_without_file_contents(
        self,
    ) -> None:
        revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        with tempfile.TemporaryDirectory() as directory:
            plugin = Path(directory) / "plugin"
            shutil.copytree(score.PLUGIN, plugin)
            helper = plugin / "skills/spec-workflow/scripts/validate_spec.py"
            helper.chmod(helper.stat().st_mode ^ 0o111)
            with self.assertRaises(runner.HostError) as caught:
                runner.verify_plugin(plugin, revision)
            message = str(caught.exception)
            self.assertIn("skills/spec-workflow/scripts/validate_spec.py", message)
            self.assertIn("100755", message)
            self.assertIn("100644", message)
            self.assertNotIn(helper.read_text(), message)

    def test_final_turn_cannot_succeed_after_changing_package(self) -> None:
        revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin, workspace = root / "plugin", root / "workspace"
            shutil.copytree(score.PLUGIN, plugin)
            workspace.mkdir()
            adapter = runner.Claude("fixture-model")
            adapter.plugin = plugin
            record = {
                "runtimeRevision": revision,
                "messages": [],
                "filesRead": [],
                "notes": "",
                "model": adapter.model,
                "hostVersion": adapter.version,
            }

            def turn(prompt: str, path: Path) -> tuple[str, list[str]]:
                (plugin / "plugin.json").write_text("changed")
                return "Completed", []

            with (
                mock.patch.object(adapter, "turn", side_effect=turn),
                mock.patch.object(runner, "verify_workspace"),
                mock.patch.object(runner, "capture_status", return_value={}),
            ):
                runner.play_session(
                    adapter, {"turns": [{"developer": "Work"}]}, workspace, record
                )
            self.assertIn("plugin.json", record.get("notRun", ""))
            self.assertEqual(record["messages"], ["Completed"])

    def test_prompt_identifies_installed_helper_without_executing_it_directly(
        self,
    ) -> None:
        plugin = Path("/synthetic package/installed")
        prompt = runner.workflow_prompt("Draft requirements", plugin)
        self.assertIn(str(plugin), prompt)
        self.assertIn(" -B ", prompt)
        self.assertIn("validate_spec.py", prompt)
        self.assertIn("Do not change package files or permissions", prompt)
        self.assertTrue(prompt.endswith("Draft requirements"))

    def test_generated_results_do_not_hide_dirty_inputs_or_block_reruns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            result = root / "tests/specflow/evals/results/claude-code/example/1.json"
            result.parent.mkdir(parents=True)
            result.write_text("{}")
            with mock.patch.object(score, "ROOT", root):
                self.assertEqual(run_matrix.frozen_changes(), "")
                source = root / "tests/specflow/evals/runners/run_claude.py"
                source.parent.mkdir()
                source.write_text("changed input")
                self.assertIn("runners", run_matrix.frozen_changes())

    def test_failed_probe_does_not_reuse_a_saved_proof_for_handoff(self) -> None:
        proof = {"checks": {k: {"passed": True} for k in score.RELEASE_BOUNDARY_CHECKS}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "proofs").mkdir()
            for host in run_matrix.HOSTS:
                score.write_json(root / "proofs" / f"{host}.json", proof)
            with (
                mock.patch.object(sys.stdin, "isatty", return_value=True),
                mock.patch.object(
                    run_matrix, "frozen_changes", return_value="", create=True
                ),
                mock.patch.object(run_matrix, "frozen_inputs", return_value={}),
                mock.patch.object(
                    run_matrix,
                    "execute_host",
                    return_value=[{"host": "codex", "session": "probe", "code": 2}],
                ),
                mock.patch.object(run_matrix.run_handoff, "execute") as handoff,
            ):
                run_matrix.main(
                    ["--out", str(root / "results"), "--proofs", str(root / "proofs")]
                )
            handoff.assert_not_called()

    def test_diagnostic_batch_is_small_and_separate_from_release_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                mock.patch.object(sys.stdin, "isatty", return_value=True),
                mock.patch.object(
                    run_matrix, "frozen_changes", return_value="", create=True
                ),
                mock.patch.object(run_matrix, "frozen_inputs", return_value={}),
                mock.patch.object(run_matrix, "execute_host", return_value=[]) as host,
                mock.patch.object(run_matrix.run_handoff, "execute") as handoff,
            ):
                run_matrix.main(
                    [
                        "--diagnostic",
                        "--out",
                        str(root / "results"),
                        "--proofs",
                        str(root / "proofs"),
                    ]
                )
            self.assertEqual(host.call_count, 3)
            for call in host.call_args_list:
                self.assertEqual(call.kwargs["selected"], ["conversion-calcard"])
                self.assertEqual(call.args[2], root / "results/diagnostic")
            handoff.assert_not_called()
            summary = json.loads(
                (root / "proofs/diagnostic/matrix-summary.json").read_text()
            )
            self.assertEqual(summary["scope"], "diagnostic")

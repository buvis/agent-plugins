"""Session identity must not depend solely on the hook trace: the prompt
itself must hand the host an invocable `--record-session` command line, not
merely a textual comment naming one."""

from __future__ import annotations

import re
import shlex
import subprocess
import unittest
from pathlib import Path

from test_host_argv import LiveProbeCase


class ProbeHostRecordSessionPromptTest(LiveProbeCase):
    def test_prompt_contains_an_invocable_record_session_command(self) -> None:
        for host_id in ("claude", "codex"):
            with self.subTest(host_id=host_id):
                run = self.probe(host_id)
                for index in (0, 1):
                    with self.subTest(invocation=index):
                        prompt = run["calls"][index]["prompt"]
                        lines = [
                            line for line in prompt.splitlines()
                            if "autopilot.py" in line and f"--record-session {host_id}" in line
                        ]
                        self.assertTrue(lines, prompt)
                        match = re.search(r"(/\S*autopilot\.py)", lines[0])
                        self.assertIsNotNone(match, lines[0])
                        script_path = Path(match.group(1))
                        self.assertTrue(script_path.is_file(), script_path)
                        completed = subprocess.run(
                            shlex.split(lines[0]), cwd=run["run_dir"] / "project",
                            capture_output=True, text=True, timeout=60,
                        )
                        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()

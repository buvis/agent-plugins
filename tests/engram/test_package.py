"""Shipped engram plugin files satisfy the host-facing packaging contract."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "plugins/engram"


class EngramPackageTest(unittest.TestCase):
    def test_every_hook_command_is_bare_engram_nudge(self) -> None:
        claude = json.loads(
            (PACKAGE / "com.anthropic.claude-code/hooks.json").read_text()
        )
        codex = json.loads((PACKAGE / "com.openai.codex/hooks.json").read_text())
        copilot = json.loads(
            (PACKAGE / "com.github.copilot/hooks.json").read_text()
        )
        claude_command = claude["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
        codex_command = codex["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
        copilot_command = copilot["hooks"]["postToolUse"][0]["bash"]
        commands = {
            "claude": claude_command,
            "codex": codex_command,
            "copilot": copilot_command,
        }
        for host, command in commands.items():
            with self.subTest(host=host):
                self.assertTrue(command.startswith("engram nudge "))
                self.assertNotIn("/", command)
                self.assertFalse(command.startswith("/"))
        # Each host passes a distinct argument; a hardcoded single value fails this.
        self.assertEqual(len(set(commands.values())), 3)

    def test_mcp_server_command_is_engram_mcp(self) -> None:
        data = json.loads((PACKAGE / "mcp.json").read_text())
        server = data["mcpServers"]["engram"]
        self.assertEqual(server["command"], "engram")
        self.assertEqual(server["args"], ["mcp"])

    def test_claude_manifest_repeats_root_metadata(self) -> None:
        root = json.loads((PACKAGE / "plugin.json").read_text())
        claude_manifest = json.loads(
            (PACKAGE / ".claude-plugin/plugin.json").read_text()
        )
        for field in ("name", "version", "description", "author", "license"):
            with self.subTest(field=field):
                self.assertEqual(claude_manifest[field], root[field])

    def test_readme_states_status_for_each_host(self) -> None:
        text = (PACKAGE / "README.md").read_text()
        rows = re.findall(
            r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", text, re.MULTILINE
        )
        statuses = {
            host: status for host, status in rows if not set(host) <= {"-"}
        }
        expected = {
            "Claude Code": "verified 2026-11-10",
            "Codex": "verified 2026-11-10",
            "Copilot CLI": "verified 2026-11-10",
            "Pi": "untested",
            "Kiro": "skill and MCP only",
        }
        for host, status in expected.items():
            with self.subTest(host=host):
                self.assertIn(host, statuses)
                self.assertEqual(statuses[host], status)

    def test_no_shipped_file_names_a_plugin_root_placeholder(self) -> None:
        files = [p for p in PACKAGE.rglob("*") if p.is_file()]
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path.relative_to(PACKAGE).as_posix()):
                self.assertNotIn(b"PLUGIN_ROOT", path.read_bytes())


if __name__ == "__main__":
    unittest.main()

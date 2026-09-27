"""Regression checks for validate.py. Run: python3 -m unittest discover -s scripts"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import validate

TEMPLATE = validate.ROOT / "templates" / "example-plugin"


class ValidatePlugin(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.plugin = self.tmp / "example-plugin"
        shutil.copytree(TEMPLATE, self.plugin)

    def check(self) -> None:
        validate.validate_manifest(self.plugin)
        validate.validate_containment(self.plugin)
        validate.validate_skills(self.plugin)
        validate.validate_mcp(self.plugin)

    def assert_rejected(self, fragment: str) -> None:
        with self.assertRaisesRegex(validate.ValidationError, fragment):
            self.check()

    def write_mcp(self, server: dict[str, object]) -> None:
        config = {"$schema": validate.MCP_SCHEMA, "mcpServers": {"s": server}}
        (self.plugin / "mcp.json").write_text(json.dumps(config))

    def test_template_is_valid(self) -> None:
        self.check()

    def test_rejects_name_differing_from_directory(self) -> None:
        self.plugin = self.plugin.rename(self.tmp / "other")
        self.assert_rejected("must match the plugin directory")

    def test_rejects_unknown_manifest_field(self) -> None:
        path = self.plugin / "plugin.json"
        manifest = json.loads(path.read_text())
        path.write_text(json.dumps({**manifest, "skills": "skills/"}))
        self.assert_rejected("unknown top-level fields: skills")

    def test_rejects_skill_name_differing_from_directory(self) -> None:
        skills = self.plugin / "skills"
        (skills / "example-skill").rename(skills / "renamed")
        self.assert_rejected("must match the skill directory")

    def test_rejects_symlink_escaping_plugin_root(self) -> None:
        (self.plugin / "escape").symlink_to(self.tmp)
        self.assert_rejected("symlink resolves outside plugin root")

    def test_rejects_plain_http_to_remote_host(self) -> None:
        self.write_mcp({"type": "streamable-http", "url": "http://example.com/mcp"})
        self.assert_rejected("must use HTTPS")

    def test_allows_plain_http_to_loopback(self) -> None:
        self.write_mcp({"type": "streamable-http", "url": "http://127.0.0.1:8080/"})
        self.check()

    def test_rejects_command_escaping_plugin_root(self) -> None:
        self.write_mcp({"type": "stdio", "command": "./../bin/server"})
        self.assert_rejected("command escapes the plugin root")

    def test_rejects_env_overriding_reserved_variables(self) -> None:
        self.write_mcp(
            {"type": "stdio", "command": "node", "env": {"PLUGIN_DATA": "/"}}
        )
        self.assert_rejected("reserved variables")


if __name__ == "__main__":
    unittest.main()

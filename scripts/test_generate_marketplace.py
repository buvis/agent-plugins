"""Regression checks for generate_marketplace.py. Run: python3 -m unittest discover -s scripts"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import generate_marketplace as generate
import validate

TEMPLATE = validate.ROOT / "templates" / "example-plugin"


class GenerateMarketplace(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "plugins").mkdir()
        root_patch = mock.patch.object(generate, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        self.target = self.root / ".claude-plugin" / "marketplace.json"

    def add_plugin(self, name: str, *, claude: bool = True, **fields: str) -> None:
        plugin = self.root / "plugins" / name
        shutil.copytree(TEMPLATE, plugin)
        path = plugin / "plugin.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(
            json.dumps({**manifest, "name": name, **fields}), encoding="utf-8"
        )
        if claude:
            (plugin / ".claude-plugin").mkdir()
            (plugin / ".claude-plugin" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )

    def run_main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["generate_marketplace.py", *args]),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = generate.main()
        return code, out.getvalue(), err.getvalue()

    def entries(self) -> list[dict[str, str]]:
        return json.loads(generate.build_manifest(self.root))["plugins"]

    def test_writes_one_entry_per_plugin(self) -> None:
        self.add_plugin("zeta")
        self.add_plugin("alpha")
        code, _, _ = self.run_main()
        self.assertEqual(code, 0)
        written = json.loads(self.target.read_text(encoding="utf-8"))
        self.assertEqual(written["name"], "buvis-agent-plugins")
        self.assertEqual(
            [entry["name"] for entry in written["plugins"]], ["alpha", "zeta"]
        )

    def test_entry_copies_name_description_and_version_from_the_manifest(self) -> None:
        self.add_plugin("alpha", description="Alpha does one thing.", version="1.2.3")
        self.assertEqual(
            self.entries(),
            [
                {
                    "name": "alpha",
                    "source": "./plugins/alpha",
                    "description": "Alpha does one thing.",
                    "version": "1.2.3",
                },
            ],
        )

    def test_check_fails_when_the_committed_file_is_stale(self) -> None:
        self.add_plugin("alpha")
        self.run_main()
        self.add_plugin("beta")
        code, _, err = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("out of date", err)
        self.assertNotIn("beta", self.target.read_text(encoding="utf-8"))

    def test_check_compares_the_exact_text(self) -> None:
        self.add_plugin("alpha")
        self.run_main()
        same_json = json.loads(self.target.read_text(encoding="utf-8"))
        self.target.write_text(json.dumps(same_json, indent=4) + "\n", encoding="utf-8")
        code, _, _ = self.run_main("--check")
        self.assertEqual(code, 1)
        self.run_main()
        self.assertEqual(self.run_main("--check")[0], 0)

    def test_skips_a_plugin_without_a_claude_manifest(self) -> None:
        self.add_plugin("alpha")
        self.add_plugin("portable-only", claude=False)
        self.assertEqual([entry["name"] for entry in self.entries()], ["alpha"])

    def test_fails_on_an_unreadable_manifest(self) -> None:
        self.add_plugin("alpha")
        self.add_plugin("broken")
        (self.root / "plugins" / "broken" / "plugin.json").write_text(
            "{", encoding="utf-8"
        )
        code, _, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("broken/plugin.json", err)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()

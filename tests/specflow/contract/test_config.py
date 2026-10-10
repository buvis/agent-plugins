"""Workspace config and the specs folder (T-028)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import unittest
from pathlib import Path

import support
import validate_spec
from specflow_helper.checks import validate
from specflow_helper.config import ConfigError, load_config
from specflow_helper.status import status

DEFAULTS = {"root": ".kiro/specflow", "specsDir": ".kiro/specs", "numberScan": []}


class ConfigTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

    def write_config(self, value: object) -> None:
        path = self.repo / ".agents" / "specflow.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value))

    def test_no_config_gives_the_defaults(self) -> None:
        self.assertEqual(load_config(self.repo), DEFAULTS)

    def test_configured_root_and_specs_folder(self) -> None:
        self.write_config(
            {"schemaVersion": 1, "root": "docs/pm", "specsDir": "docs/pm/specs"}
        )
        config = load_config(self.repo)
        self.assertEqual(
            (config["root"], config["specsDir"]), ("docs/pm", "docs/pm/specs")
        )
        self.assertEqual(config["numberScan"], [])

    def test_this_repositorys_own_config_loads(self) -> None:
        self.write_config((support.REPO / ".agents" / "specflow.json").read_text())
        config = load_config(self.repo)
        self.assertEqual(config["specsDir"], "docs/dev/project-management/specs")

    def test_unknown_fields_pass(self) -> None:
        self.write_config({"schemaVersion": 1, "laterField": True})
        self.assertEqual(load_config(self.repo), DEFAULTS)

    def test_each_refused_path_is_named_before_use(self) -> None:
        outside = self.tmp / "outside"
        outside.mkdir()
        (self.repo / "escape").symlink_to(outside)
        for key, value, reason in (
            ("root", "/abs/root", "is absolute"),
            ("specsDir", "~/specs", "is absolute"),
            ("specsDir", "C:/specs", "is absolute"),
            ("root", "docs/../../up", "holds a .. segment"),
            ("specsDir", "escape/specs", "resolves outside the repository"),
        ):
            with self.subTest(value=value):
                self.write_config({"schemaVersion": 1, key: value})
                with self.assertRaisesRegex(ConfigError, f"{value} {reason}"):
                    load_config(self.repo)
        self.write_config({"schemaVersion": 1, "numberScan": ["ok", "../prds"]})
        with self.assertRaisesRegex(ConfigError, r"\.\./prds holds a \.\. segment"):
            load_config(self.repo)

    def test_kiro_specs_link_resolving_outside_is_refused(self) -> None:
        outside = self.tmp / "outside"
        outside.mkdir()
        (self.repo / ".kiro").mkdir()
        (self.repo / ".kiro" / "specs").symlink_to(outside)
        with self.assertRaisesRegex(ConfigError, "resolves outside the repository"):
            load_config(self.repo)

    def test_link_that_resolves_inside_is_allowed(self) -> None:
        (self.repo / "docs" / "specs").mkdir(parents=True)
        (self.repo / ".kiro").mkdir()
        (self.repo / ".kiro" / "specs").symlink_to(self.repo / "docs" / "specs")
        self.assertEqual(load_config(self.repo), DEFAULTS)

    def test_malformed_or_invalid_config_is_an_error(self) -> None:
        for value in ("{", "[]", {"schemaVersion": 2}, {"schemaVersion": 1, "root": 3}):
            with self.subTest(value=value):
                self.write_config(value)
                with self.assertRaises(ConfigError):
                    load_config(self.repo)

    def test_cli_maps_a_refused_path_to_exit_2(self) -> None:
        self.write_config({"schemaVersion": 1, "specsDir": "/etc"})
        cwd = Path.cwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, cwd)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = validate_spec.main(["status"])
        self.assertEqual(code, 2)
        self.assertIn("/etc is absolute", err.getvalue())


class SpecsFolderTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.tmp / "repo"
        self.specs = self.repo / "docs" / "specs"
        self.specs.mkdir(parents=True)
        (self.repo / ".agents").mkdir()
        config = {"schemaVersion": 1, "root": "docs", "specsDir": "docs/specs"}
        (self.repo / ".agents" / "specflow.json").write_text(json.dumps(config))
        self.spec = shutil.copytree(
            support.FIXTURES / "specs" / "00101-feature-sample",
            self.specs / "00101-feature",
        )

    def rules(self) -> set[str]:
        return {
            f["rule"] for f in validate(self.repo, self.spec) if f["level"] == "error"
        }

    def test_configured_folder_is_used_for_every_operation(self) -> None:
        document = status(self.repo, [])
        self.assertEqual([s["spec"] for s in document["specs"]], ["00101-feature"])
        self.assertEqual(document["problems"], [])

    def test_specs_left_in_a_real_kiro_folder_are_reported(self) -> None:
        (self.repo / ".kiro" / "specs" / "00200-left").mkdir(parents=True)
        self.assertIn("specs-folder", self.rules())
        [problem] = status(self.repo, [])["problems"]
        self.assertEqual(problem["rule"], "specs-folder")
        self.assertIn("00200-left", problem["message"])

    def test_a_kiro_link_to_the_configured_folder_is_fine(self) -> None:
        (self.repo / ".kiro").mkdir()
        (self.repo / ".kiro" / "specs").symlink_to(self.specs)
        self.assertNotIn("specs-folder", self.rules())

    def test_an_ignored_specs_folder_fails(self) -> None:
        support.git(self.repo, "init", "-q")
        (self.repo / ".gitignore").write_text("docs/specs/\n")
        self.assertIn("specs-folder", self.rules())
        self.assertEqual(status(self.repo, [])["problems"][0]["rule"], "specs-folder")

    def test_status_under_a_configured_root_lists_its_new_intake_items(self) -> None:
        (self.repo / "docs" / "intake" / "new" / "00300-idea").mkdir(parents=True)
        self.assertEqual(status(self.repo, [])["intake"], ["00300-idea"])


if __name__ == "__main__":
    unittest.main()

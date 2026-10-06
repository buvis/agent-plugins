"""Tests for tools/specflow/verify_release.py, on fixtures only, never the real package."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "specflow"))
import verify_release

ROOT_MANIFEST = {
    "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
    "name": "specflow",
    "version": "0.1.0",
    "description": "Fixture package.",
    "author": {"name": "buvis", "url": "https://github.com/buvis"},
    "repository": "https://github.com/buvis/agent-plugins",
    "license": "MIT",
    "keywords": ["spec"],
}
GIT_ENV = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


def make_package(root: Path) -> Path:
    plugin = root / "plugins" / "specflow"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / "plugin.json").write_text(json.dumps(ROOT_MANIFEST))
    compat = {k: v for k, v in ROOT_MANIFEST.items() if k != "$schema"}
    (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps(compat))
    return plugin


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=test",
         "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false",
         *args],
        check=True, capture_output=True,
    )


def commit_all(repo: Path) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture")


class VerifyReleaseTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        env = {**GIT_ENV, "GIT_CEILING_DIRECTORIES": str(self.tmp)}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.tmp / "repo"
        self.plugin = make_package(self.repo)

    def init_repo(self) -> None:
        git(self.repo, "init", "-q")
        commit_all(self.repo)

    def run_main(self) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(verify_release, "PLUGIN", self.plugin), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = verify_release.main()
        return code, out.getvalue(), err.getvalue()

    def assert_error(self, errors: list[str], *fragments: str) -> None:
        self.assertTrue(
            any(all(f in e for f in fragments) for e in errors),
            f"no error with {fragments} in {errors}",
        )


class CheckCleanTest(VerifyReleaseTest):
    def test_clean_fixture_passes(self) -> None:
        self.init_repo()
        self.assertEqual(self.run_main(), (0, "Verified plugins/specflow.\n", ""))

    def test_rejects_modified_tracked_file(self) -> None:
        self.init_repo()
        (self.plugin / "plugin.json").write_text("{}")
        self.assert_error(verify_release.check_clean(self.plugin),
                          "plugins/specflow/plugin.json", "modified tracked file")

    def test_rejects_untracked_file_in_plugin(self) -> None:
        self.init_repo()
        (self.plugin / "notes.md").write_text("x")
        self.assert_error(verify_release.check_clean(self.plugin),
                          "plugins/specflow/notes.md", "untracked file")

    def test_rejects_untracked_file_when_git_hides_untracked_files(self) -> None:
        self.init_repo()
        git(self.repo, "config", "status.showUntrackedFiles", "no")
        (self.plugin / "notes.md").write_text("x")
        self.assert_error(verify_release.check_clean(self.plugin),
                          "plugins/specflow/notes.md", "untracked file")

    def test_rejects_ignored_generated_file_in_plugin(self) -> None:
        (self.repo / ".gitignore").write_text("__pycache__/\n")
        self.init_repo()
        cache = self.plugin / "__pycache__"
        cache.mkdir()
        (cache / "mod.pyc").write_bytes(b"x")
        self.assert_error(verify_release.check_clean(self.plugin),
                          "plugins/specflow/__pycache__", "ignored generated file")

    def test_rejects_committed_file_matching_an_ignore_rule(self) -> None:
        (self.repo / ".gitignore").write_text("*.pyc\n")
        (self.plugin / "mod.pyc").write_bytes(b"x")
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-f", "-A")
        git(self.repo, "commit", "-q", "-m", "fixture")
        self.assert_error(verify_release.check_clean(self.plugin),
                          "plugins/specflow/mod.pyc", "matches an ignore rule")

    def test_rejects_embedded_repository(self) -> None:
        clone = self.plugin / "upstream-clone"
        clone.mkdir()
        (clone / "f").write_text("x")
        git(clone, "init", "-q")
        commit_all(clone)
        self.init_repo()
        self.assert_error(verify_release.check_clean(self.plugin),
                          "plugins/specflow/upstream-clone", "embedded repository")

    def test_exits_2_outside_a_git_checkout(self) -> None:
        code, _, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn("git status failed", err)


class CheckManifestsTest(VerifyReleaseTest):
    def compat_path(self) -> Path:
        return self.plugin / ".claude-plugin" / "plugin.json"

    def write_compat(self, value: object) -> None:
        self.compat_path().write_text(json.dumps(value))

    def test_rejects_symlink_escaping_plugin_root(self) -> None:
        (self.plugin / "escape").symlink_to(self.tmp)
        self.assert_error(verify_release.check_manifests(self.plugin),
                          "escape", "symlink resolves outside plugin root")

    def test_rejects_missing_compat_manifest(self) -> None:
        self.compat_path().unlink()
        self.assert_error(verify_release.check_manifests(self.plugin),
                          ".claude-plugin/plugin.json", "missing")

    def test_rejects_compat_manifest_that_is_not_an_object(self) -> None:
        self.write_compat(["specflow"])
        self.assert_error(verify_release.check_manifests(self.plugin),
                          ".claude-plugin/plugin.json", "must contain a JSON object")

    def test_rejects_compat_manifest_with_component_path(self) -> None:
        compat = json.loads(self.compat_path().read_text())
        self.write_compat({**compat, "skills": "./skills/"})
        self.assert_error(verify_release.check_manifests(self.plugin),
                          ".claude-plugin/plugin.json", "field skills")

    def test_rejects_compat_value_differing_from_root(self) -> None:
        compat = json.loads(self.compat_path().read_text())
        for field in sorted(compat):
            with self.subTest(field=field):
                self.write_compat({**compat, field: "changed"})
                self.assert_error(verify_release.check_manifests(self.plugin),
                                  ".claude-plugin/plugin.json",
                                  f"{field} differs from the root manifest")

    def test_reports_failures_from_every_check(self) -> None:
        self.init_repo()
        (self.plugin / "notes.md").write_text("see tools/specflow")
        self.compat_path().unlink()
        code, _, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("untracked file", err)
        self.assertIn("missing Claude compatibility manifest", err)
        self.assertIn("contains marker tools/specflow", err)


class CheckForbiddenTest(VerifyReleaseTest):
    def fresh_plugin(self, case: str) -> Path:
        return make_package(self.tmp / case)

    def assert_forbidden(self, plugin: Path, relative: str, *fragments: str) -> None:
        errors = verify_release.check_forbidden(plugin)
        self.assert_error(errors, str(plugin / relative), *fragments)

    def test_clean_package_has_no_forbidden_content(self) -> None:
        self.assertEqual(verify_release.check_forbidden(self.plugin), [])

    def test_rejects_each_forbidden_path_part(self) -> None:
        for part in verify_release.FORBIDDEN_PATH_PARTS:
            with self.subTest(part=part):
                plugin = self.fresh_plugin(f"part{part}")
                (plugin / "skills" / part).mkdir(parents=True)
                (plugin / "skills" / part / "notes.md").write_text("x")
                self.assert_forbidden(plugin, f"skills/{part}",
                                      f"forbidden path part {part}")

    def test_rejects_each_forbidden_file_name(self) -> None:
        for name in verify_release.FORBIDDEN_FILE_NAMES:
            with self.subTest(name=name):
                plugin = self.fresh_plugin(f"name{name}")
                (plugin / name).write_text("x")
                self.assert_forbidden(plugin, name, "forbidden file name")

    def test_rejects_each_forbidden_name_pattern(self) -> None:
        for pattern in verify_release.FORBIDDEN_NAME_PATTERNS:
            with self.subTest(pattern=pattern):
                name = pattern.replace("*", "x")
                plugin = self.fresh_plugin(f"pattern{name}")
                (plugin / name).write_text("x")
                self.assert_forbidden(plugin, name,
                                      f"matches forbidden pattern {pattern}")

    def test_rejects_marker_in_a_folder_name(self) -> None:
        folder = self.plugin / "skills" / "catchup-specflow-upstream"
        folder.mkdir(parents=True)
        self.assert_forbidden(self.plugin, "skills/catchup-specflow-upstream",
                              "name contains marker catchup-specflow-upstream")

    def test_rejects_each_marker_in_file_content(self) -> None:
        for marker in verify_release.FORBIDDEN_MARKERS:
            with self.subTest(marker=marker):
                plugin = self.fresh_plugin(f"marker{marker.replace('/', '-')}")
                (plugin / "README.md").write_text(f"Run {marker} first.\n")
                self.assert_forbidden(plugin, "README.md", f"contains marker {marker}")

    def test_reports_unreadable_file(self) -> None:
        path = self.plugin / "locked.md"
        path.write_text("x")
        path.chmod(0)
        self.addCleanup(path.chmod, 0o644)
        self.assert_forbidden(self.plugin, "locked.md", "cannot read file")

    def test_error_names_path_and_marker(self) -> None:
        (self.plugin / "README.md").write_text("see tests/specflow\n")
        self.assertEqual(
            verify_release.check_forbidden(self.plugin),
            [f"{self.plugin / 'README.md'}: contains marker tests/specflow"],
        )


if __name__ == "__main__":
    unittest.main()

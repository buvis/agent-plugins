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

# Copied from PKG-002.4 and T-005, not read from the tool, so dropping an entry
# from a tool denylist fails a test instead of deleting it.
REQUIRED_PATH_PARTS = (".agents", ".git", "tests", "evals", "parity", "upstream")
REQUIRED_FILE_NAMES = (
    "sources.md",
    "inventory.json",
    "criteria.json",
    "check_rules.py",
    "verify_release.py",
)
REQUIRED_NAME_PATTERNS = ("test_*.py", "*_test.py", "*-specflow-upstream-catchup.md")
REQUIRED_MARKERS = (
    "catchup-specflow-upstream",
    "check_rules.py",
    "verify_release.py",
    "tools/specflow",
    "tests/specflow",
    "docs/dev/tmp/specflow",
)


A1_COMMIT = "1" * 40
A2_COMMIT = "2" * 40
A3_COMMIT = "3" * 40
RECORD_ROWS = {
    "A1": f"| A1 `awslabs/aidlc-workflows` | primary method | `v1.2.3` `{A1_COMMIT}` | MIT-0 |",
    "A2": (
        "| A2 `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` | patterns"
        f" | `{A2_COMMIT}` | MIT-0 |"
    ),
    "A3": (
        f"| A3 `aws-samples/sample-aidlc-discovery` | discovery | `{A3_COMMIT}` | MIT-0 |"
    ),
}
SKILL = "---\nname: spec-workflow\ndescription: Fixture skill.\n---\n\nFixture body.\n"
LICENSE = "Copied from awslabs/aidlc-workflows (A1).\n\nMIT No Attribution\n"


def write_record(plugin: Path, rows: dict[str, str]) -> None:
    table = "| Source | Role | Adopted from | License |\n|---|---|---|---|\n"
    text = "# Record\n\n" + table + "\n".join(rows.values()) + "\n"
    (plugin / verify_release.AWS_DIR / "adaptation.md").write_text(text)


def make_package(root: Path) -> Path:
    plugin = root / "plugins" / "specflow"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / "plugin.json").write_text(json.dumps(ROOT_MANIFEST))
    compat = {k: v for k, v in ROOT_MANIFEST.items() if k != "$schema"}
    (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps(compat))
    aws = plugin / verify_release.AWS_DIR
    aws.mkdir(parents=True)
    (aws.parents[1] / "SKILL.md").write_text(SKILL)
    write_record(plugin, RECORD_ROWS)
    (aws / "LICENSE").write_text(LICENSE)
    return plugin


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
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
        with (
            mock.patch.object(verify_release, "PLUGIN", self.plugin),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
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
        self.assert_error(
            verify_release.check_clean(self.plugin),
            "plugins/specflow/plugin.json",
            "modified tracked file",
        )

    def test_rejects_untracked_file_in_plugin(self) -> None:
        self.init_repo()
        (self.plugin / "notes.md").write_text("x")
        self.assert_error(
            verify_release.check_clean(self.plugin),
            "plugins/specflow/notes.md",
            "untracked file",
        )

    def test_rejects_untracked_file_when_git_hides_untracked_files(self) -> None:
        self.init_repo()
        git(self.repo, "config", "status.showUntrackedFiles", "no")
        (self.plugin / "notes.md").write_text("x")
        self.assert_error(
            verify_release.check_clean(self.plugin),
            "plugins/specflow/notes.md",
            "untracked file",
        )

    def test_rejects_ignored_generated_file_in_plugin(self) -> None:
        (self.repo / ".gitignore").write_text("__pycache__/\n")
        self.init_repo()
        cache = self.plugin / "__pycache__"
        cache.mkdir()
        (cache / "mod.pyc").write_bytes(b"x")
        self.assert_error(
            verify_release.check_clean(self.plugin),
            "plugins/specflow/__pycache__",
            "ignored generated file",
        )

    def test_rejects_committed_file_matching_an_ignore_rule(self) -> None:
        (self.repo / ".gitignore").write_text("*.pyc\n")
        (self.plugin / "mod.pyc").write_bytes(b"x")
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-f", "-A")
        git(self.repo, "commit", "-q", "-m", "fixture")
        self.assert_error(
            verify_release.check_clean(self.plugin),
            "plugins/specflow/mod.pyc",
            "matches an ignore rule",
        )

    def test_rejects_embedded_repository(self) -> None:
        clone = self.plugin / "upstream-clone"
        clone.mkdir()
        (clone / "f").write_text("x")
        git(clone, "init", "-q")
        commit_all(clone)
        self.init_repo()
        self.assert_error(
            verify_release.check_clean(self.plugin),
            "plugins/specflow/upstream-clone",
            "embedded repository",
        )

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
        self.assert_error(
            verify_release.check_manifests(self.plugin),
            "escape",
            "symlink resolves outside plugin root",
        )

    def test_rejects_missing_compat_manifest(self) -> None:
        self.compat_path().unlink()
        self.assert_error(
            verify_release.check_manifests(self.plugin),
            ".claude-plugin/plugin.json",
            "missing",
        )

    def test_rejects_compat_manifest_that_is_not_an_object(self) -> None:
        self.write_compat(["specflow"])
        self.assert_error(
            verify_release.check_manifests(self.plugin),
            ".claude-plugin/plugin.json",
            "must contain a JSON object",
        )

    def test_rejects_compat_manifest_with_component_path(self) -> None:
        compat = json.loads(self.compat_path().read_text())
        self.write_compat({**compat, "skills": "./skills/"})
        self.assert_error(
            verify_release.check_manifests(self.plugin),
            ".claude-plugin/plugin.json",
            "field skills",
        )

    def test_rejects_compat_value_differing_from_root(self) -> None:
        compat = json.loads(self.compat_path().read_text())
        for field in sorted(compat):
            with self.subTest(field=field):
                self.write_compat({**compat, field: "changed"})
                self.assert_error(
                    verify_release.check_manifests(self.plugin),
                    ".claude-plugin/plugin.json",
                    f"{field} differs from the root manifest",
                )

    def test_rejects_compat_manifest_missing_a_required_field(self) -> None:
        compat = json.loads(self.compat_path().read_text())
        for field in ("name", "version"):
            with self.subTest(field=field):
                self.write_compat({k: v for k, v in compat.items() if k != field})
                self.assert_error(
                    verify_release.check_manifests(self.plugin),
                    ".claude-plugin/plugin.json",
                    f"missing required field {field}",
                )

    def test_rejects_empty_compat_manifest(self) -> None:
        self.write_compat({})
        errors = verify_release.check_manifests(self.plugin)
        self.assert_error(errors, "missing required field name")
        self.assert_error(errors, "missing required field version")

    def test_reports_failures_from_every_check(self) -> None:
        self.init_repo()
        (self.plugin / "notes.md").write_text("see tools/specflow")
        self.compat_path().unlink()
        (self.plugin / verify_release.AWS_DIR / "LICENSE").unlink()
        code, _, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("untracked file", err)
        self.assertIn("missing Claude compatibility manifest", err)
        self.assertIn("contains marker tools/specflow", err)
        self.assertIn("missing or empty license", err)

    def test_main_prints_repository_relative_paths(self) -> None:
        self.init_repo()
        (self.plugin / "README.md").write_text("see tests/specflow\n")
        self.compat_path().unlink()
        _, _, err = self.run_main()
        self.assertIn("error: plugins/specflow/README.md: contains marker", err)
        self.assertIn(
            "error: plugins/specflow/.claude-plugin/plugin.json: missing",
            err,
        )
        self.assertNotIn(str(self.repo), err)


class CheckSourcesTest(VerifyReleaseTest):
    def aws(self) -> Path:
        return self.plugin / verify_release.AWS_DIR

    def test_clean_fixture_has_no_source_errors(self) -> None:
        self.assertEqual(verify_release.check_sources(self.plugin), [])

    def test_rejects_missing_source_record(self) -> None:
        (self.aws() / "adaptation.md").unlink()
        self.assert_error(
            verify_release.check_sources(self.plugin),
            "aws/adaptation.md",
            "missing source record",
        )

    def test_rejects_source_record_without_a_source_row(self) -> None:
        for source in RECORD_ROWS:
            with self.subTest(source=source):
                write_record(
                    self.plugin, {k: v for k, v in RECORD_ROWS.items() if k != source}
                )
                self.assert_error(
                    verify_release.check_sources(self.plugin),
                    f"source record has no valid row for {source}",
                )

    def test_rejects_preview_tag_in_source_record(self) -> None:
        preview = RECORD_ROWS["A1"].replace("v1.2.3", "v1.2.4-preview.20261003.1")
        write_record(self.plugin, {**RECORD_ROWS, "A1": preview})
        self.assert_error(
            verify_release.check_sources(self.plugin),
            "A1 tag v1.2.4-preview.20261003.1 is not a release tag",
        )

    def test_rejects_missing_license(self) -> None:
        for content in (None, " \n"):
            with self.subTest(content=content):
                path = self.aws() / "LICENSE"
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_text(content)
                self.assert_error(
                    verify_release.check_sources(self.plugin),
                    "aws/LICENSE",
                    "missing or empty license",
                )

    def test_rejects_missing_attribution(self) -> None:
        (self.aws() / "requirements.md").write_text(
            "> Source: A1 `core/x.md` > Steps @ v1.2.3 [both]\n\nText.\n"
        )
        (self.aws() / "LICENSE").write_text("MIT No Attribution\n")
        self.assert_error(
            verify_release.check_sources(self.plugin),
            "aws/LICENSE",
            "no attribution line for awslabs/aidlc-workflows",
        )


class CheckForbiddenTest(VerifyReleaseTest):
    def fresh_plugin(self, case: str) -> Path:
        return make_package(self.tmp / case)

    def assert_forbidden(self, plugin: Path, relative: str, *fragments: str) -> None:
        errors = verify_release.check_forbidden(plugin)
        self.assert_error(errors, str(plugin / relative), *fragments)

    def test_clean_package_has_no_forbidden_content(self) -> None:
        self.assertEqual(verify_release.check_forbidden(self.plugin), [])

    def test_denylists_hold_every_required_entry(self) -> None:
        for required, constant in (
            (REQUIRED_PATH_PARTS, verify_release.FORBIDDEN_PATH_PARTS),
            (REQUIRED_FILE_NAMES, verify_release.FORBIDDEN_FILE_NAMES),
            (REQUIRED_NAME_PATTERNS, verify_release.FORBIDDEN_NAME_PATTERNS),
            (REQUIRED_MARKERS, verify_release.FORBIDDEN_MARKERS),
        ):
            with self.subTest(first=required[0]):
                self.assertEqual(set(required) - set(constant), set())

    def test_rejects_each_forbidden_path_part(self) -> None:
        for part in REQUIRED_PATH_PARTS:
            with self.subTest(part=part):
                plugin = self.fresh_plugin(f"part{part}")
                (plugin / "skills" / part).mkdir(parents=True)
                (plugin / "skills" / part / "notes.md").write_text("x")
                self.assert_forbidden(
                    plugin,
                    f"skills/{part}",
                    f"forbidden path part {part}",
                )

    def test_rejects_each_forbidden_file_name(self) -> None:
        for name in REQUIRED_FILE_NAMES:
            with self.subTest(name=name):
                plugin = self.fresh_plugin(f"name{name}")
                (plugin / name).write_text("x")
                self.assert_forbidden(plugin, name, "forbidden file name")

    def test_rejects_each_forbidden_name_pattern(self) -> None:
        for pattern in REQUIRED_NAME_PATTERNS:
            with self.subTest(pattern=pattern):
                name = pattern.replace("*", "x")
                plugin = self.fresh_plugin(f"pattern{name}")
                (plugin / name).write_text("x")
                self.assert_forbidden(
                    plugin,
                    name,
                    f"matches forbidden pattern {pattern}",
                )

    def test_rejects_marker_in_a_folder_name(self) -> None:
        # A marker with a slash is a folder path, such as skills/tools/specflow.
        for marker in REQUIRED_MARKERS:
            with self.subTest(marker=marker):
                plugin = self.fresh_plugin(f"folder{marker.replace('/', '-')}")
                (plugin / "skills" / marker).mkdir(parents=True)
                self.assert_forbidden(plugin, f"skills/{marker}", f"marker {marker}")

    def test_rejects_each_marker_in_file_content(self) -> None:
        for marker in REQUIRED_MARKERS:
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

    def test_reports_unreadable_folder(self) -> None:
        folder = self.plugin / "locked"
        folder.mkdir()
        folder.chmod(0)
        self.addCleanup(folder.chmod, 0o755)
        self.assert_forbidden(self.plugin, "locked", "cannot read folder")

    def test_error_names_path_and_marker(self) -> None:
        (self.plugin / "README.md").write_text("see tests/specflow\n")
        self.assertEqual(
            verify_release.check_forbidden(self.plugin),
            [f"{self.plugin / 'README.md'}: contains marker tests/specflow"],
        )


if __name__ == "__main__":
    unittest.main()

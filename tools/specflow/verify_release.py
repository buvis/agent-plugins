#!/usr/bin/env python3
"""Verify that plugins/specflow is a clean, self-contained release package.

Run in a clean checkout: python3 tools/specflow/verify_release.py
Exit codes: 0 pass, 1 one or more failures, 2 git missing or failing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "specflow"

sys.path.insert(0, str(ROOT / "scripts"))
from validate import (
    ValidationError,
    load_object,
    validate_containment,
    validate_manifest,
    validate_mcp,
    validate_skills,
)

COMPAT_FIELDS = {
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
}
COMPAT_REQUIRED = ("name", "version")

FORBIDDEN_PATH_PARTS = (".agents", ".git", "tests", "evals", "parity", "upstream")
FORBIDDEN_FILE_NAMES = (
    "sources.md",
    "inventory.json",
    "criteria.json",
    "check_rules.py",
    "verify_release.py",
)
FORBIDDEN_NAME_PATTERNS = ("test_*.py", "*_test.py", "*-specflow-upstream-catchup.md")
FORBIDDEN_MARKERS = (
    "catchup-specflow-upstream",
    "check_rules.py",
    "verify_release.py",
    "tools/specflow",
    "tests/specflow",
    "docs/dev/tmp/specflow",
)


class GitError(Exception):
    """git is missing, the folder is not a checkout, or a git call failed."""


def git(plugin: Path, *args: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(plugin), *args],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise GitError("git is not installed") from error
    if result.returncode != 0:
        raise GitError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.splitlines()


def check_clean(plugin: Path) -> list[str]:
    kinds = {"??": "untracked file", "!!": "ignored generated file"}
    errors = [
        f"{line[3:]}: {kinds.get(line[:2], 'modified tracked file')} in the package"
        for line in git(
            plugin,
            "status",
            "--porcelain",
            "--ignored",
            "--untracked-files=all",
            "--",
            ".",
        )
    ]
    errors += [
        f"{line}: committed file matches an ignore rule"
        for line in git(
            plugin,
            "ls-files",
            "--full-name",
            "-ci",
            "--exclude-per-directory=.gitignore",
            "--",
            ".",
        )
    ]
    errors += [
        line.partition("\t")[2] + ": embedded repository"
        for line in git(plugin, "ls-files", "--full-name", "-s", "--", ".")
        if line.startswith("160000 ")
    ]
    return errors


def check_manifests(plugin: Path) -> list[str]:
    errors: list[str] = []
    root: dict[str, object] = {}
    for check in (
        validate_manifest,
        validate_containment,
        validate_skills,
        validate_mcp,
    ):
        try:
            result = check(plugin)
        except ValidationError as error:
            errors.append(str(error))
        else:
            if check is validate_manifest:
                root = result

    path = plugin / ".claude-plugin" / "plugin.json"
    if not path.is_file():
        return [*errors, f"{path}: missing Claude compatibility manifest"]
    try:
        compat = load_object(path)
    except ValidationError as error:
        return [*errors, str(error)]
    errors += [
        f"{path}: missing required field {key}"
        for key in COMPAT_REQUIRED
        if key not in compat
    ]
    for key, value in sorted(compat.items()):
        if key not in COMPAT_FIELDS:
            errors.append(f"{path}: field {key} is not a root manifest metadata field")
        elif root and value != root.get(key):
            errors.append(f"{path}: {key} differs from the root manifest")
    return errors


def check_name(path: Path, plugin: Path) -> list[str]:
    name = path.name
    tail = f"/{path.relative_to(plugin).as_posix()}"
    errors = (
        [f"{path}: forbidden path part {name}"] if name in FORBIDDEN_PATH_PARTS else []
    )
    errors += [
        f"{path}: name contains marker {m}" for m in FORBIDDEN_MARKERS if m in name
    ]
    # A marker with a slash spans folders, so it is matched against the path.
    errors += [
        f"{path}: path ends in marker {m}"
        for m in FORBIDDEN_MARKERS
        if "/" in m and tail.endswith(f"/{m}")
    ]
    return errors


def check_forbidden(plugin: Path) -> list[str]:
    errors: list[str] = []

    def unreadable(error: OSError) -> None:
        errors.append(f"{error.filename}: cannot read folder: {error.strerror}")

    # Every entry's own name is tested, so each part of every path is covered once.
    for folder, dirs, files in os.walk(plugin, onerror=unreadable):
        base = Path(folder)
        for name in dirs:
            errors += check_name(base / name, plugin)
        for name in files:
            path = base / name
            errors += check_name(path, plugin)
            if name in FORBIDDEN_FILE_NAMES:
                errors.append(f"{path}: forbidden file name")
            errors += [
                f"{path}: name matches forbidden pattern {p}"
                for p in FORBIDDEN_NAME_PATTERNS
                if fnmatch(name, p)
            ]
            if path.is_symlink():
                continue
            try:
                content = path.read_bytes()
            except OSError as error:
                errors.append(f"{path}: cannot read file: {error}")
                continue
            errors += [
                f"{path}: contains marker {m}"
                for m in FORBIDDEN_MARKERS
                if m.encode() in content
            ]
    return errors


def main() -> int:
    try:
        errors = check_clean(PLUGIN) + check_manifests(PLUGIN) + check_forbidden(PLUGIN)
    except GitError as error:
        print(f"error: {PLUGIN}: {error}", file=sys.stderr)
        return 2
    repo = f"{PLUGIN.parents[1]}{os.sep}"
    for error in errors:
        print(f"error: {error.removeprefix(repo)}", file=sys.stderr)
    if errors:
        return 1
    print("Verified plugins/specflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

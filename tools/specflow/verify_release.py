#!/usr/bin/env python3
"""Verify that plugins/specflow is a clean, self-contained release package.

Run in a clean checkout: python3 tools/specflow/verify_release.py
Exit codes: 0 pass, 1 one or more failures, 2 git missing or failing.
"""

from __future__ import annotations

import os
import re
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


AWS_DIR = Path("skills/spec-workflow/references/aws")
AWS_REFERENCES = (
    "requirements.md",
    "design.md",
    "implementation.md",
    "verification.md",
)
RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")
SOURCE_LINE = re.compile(
    r"^> Source: (A[123]) `[^`]+` > \S.* @ (v\d+\.\d+\.\d+|[0-9a-f]{7,40})"
    r"(?: \(([0-9a-f]{7,40})\))? \[(standard|quick|both)\]$"
)
SOURCES = {
    "A1": "awslabs/aidlc-workflows",
    "A2": "aws-samples/sample-ai-powered-sdlc-patterns-with-aws",
    "A3": "aws-samples/sample-aidlc-discovery",
}
# A record row: source, repository, role, adopted-from cell, license.
RECORD_ROW = re.compile(
    r"^\| (A[123]) `([^`]+)` \| ([^|]*?) \| ([^|]*?) \| ([^|]*?) \|$", re.MULTILINE
)
A1_ADOPTED = re.compile(r"^`(\S+)` `([0-9a-f]{40})`$")
COMMIT_ADOPTED = re.compile(r"^`([0-9a-f]{40})`$")


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


def read_text(path: Path, errors: list[str]) -> str | None:
    """The file's text, or None after recording why it could not be read."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f"{path}: cannot read file: {error}")
        return None


def read_record(path: Path, text: str) -> tuple[dict[str, tuple], list[str]]:
    """Source ID -> (tag or None, commit) for each well-formed record row."""
    rows: dict[str, tuple] = {}
    errors: list[str] = []
    for source, repo, role, adopted, license_name in RECORD_ROW.findall(text):
        form = A1_ADOPTED if source == "A1" else COMMIT_ADOPTED
        match = form.match(adopted)
        if repo != SOURCES[source] or not role or not license_name or not match:
            continue
        tag, commit = match.groups() if source == "A1" else (None, match[1])
        if tag is not None and not RELEASE_TAG.match(tag):
            errors.append(f"{path}: A1 tag {tag} is not a release tag")
        rows[source] = (tag, commit)
    errors += [
        f"{path}: source record has no valid row for {source}"
        for source in SOURCES
        if source not in rows
    ]
    return rows, errors


def check_sources(plugin: Path) -> list[str]:
    errors: list[str] = []
    aws = plugin / AWS_DIR
    record = aws / "adaptation.md"
    if not record.is_file():
        errors.append(f"{record}: missing source record")
    elif (text := read_text(record, errors)) is not None:
        errors += read_record(record, text)[1]

    license_path = aws / "LICENSE"
    license_text = (
        read_text(license_path, errors) if license_path.is_file() else None
    ) or ""
    if not license_text.strip():
        errors.append(f"{license_path}: missing or empty license")
    cited = {
        match[1]
        for name in AWS_REFERENCES
        if (aws / name).is_file()
        for line in (read_text(aws / name, errors) or "").splitlines()
        if (match := SOURCE_LINE.match(line))
    }
    # ponytail: the repository named anywhere in LICENSE counts as its attribution line.
    errors += [
        f"{license_path}: no attribution line for {SOURCES[source]}"
        for source in sorted(cited)
        if SOURCES[source] not in license_text
    ]
    return errors


def main() -> int:
    try:
        errors = (
            check_clean(PLUGIN)
            + check_manifests(PLUGIN)
            + check_forbidden(PLUGIN)
            + check_sources(PLUGIN)
        )
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

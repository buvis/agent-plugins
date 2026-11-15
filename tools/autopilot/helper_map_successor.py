"""Validate delivery receipts, an AP00018 successor and AP00014 host receipts.

Check the successor's package_revision and refresh the rows it cites.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

# README.md and CHANGELOG.md: the shared rows a successor may certify.
SHARED_PATHS = ("plugins/autopilot/README.md", "plugins/autopilot/CHANGELOG.md")
CONTROLLER_PREFIXES = (
    "plugins/autopilot/controller/",
    "plugins/autopilot/contracts/controller/",
)
CONTROLLER_CONTRACT = "plugins/autopilot/contracts/controller-v1.json"
HOST_RECEIPT_PRD = "00014"
AP00014_ASSET_PATHS = (
    "plugins/autopilot/compatibility/claude.json",
    "plugins/autopilot/compatibility/claude/hooks.json",
    "plugins/autopilot/compatibility/codex.json",
    "plugins/autopilot/compatibility/codex/hooks.json",
    "plugins/autopilot/compatibility/gemini.json",
    "plugins/autopilot/contracts/hosts.json",
    "plugins/autopilot/scripts/claude.py",
    "plugins/autopilot/scripts/codex.py",
    "plugins/autopilot/scripts/doctor.py",
    "plugins/autopilot/scripts/gemini.py",
    "plugins/autopilot/scripts/guards.py",
    "plugins/autopilot/scripts/hosts.py",
    "plugins/autopilot/scripts/interception.py",
    "plugins/autopilot/scripts/jobs.py",
    "plugins/autopilot/scripts/roles.py",
)
HOST_PATHS = (*SHARED_PATHS, "plugins/autopilot/scripts/autopilot.py", *AP00014_ASSET_PATHS)
# Prose that claims the delivery evidence has not landed yet.
CLAIMS = re.compile(r"(?i)\b(planned|pending|on[\s-]hold)\b")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# Environment that points git at a repository from outside the directory tree.
GIT_LOCATION_VARIABLES = ("GIT_DIR", "GIT_WORK_TREE")


def validate_receipts(receipts: dict, prd: str = "00013") -> None:
    def text(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    tasks = receipts.get("tasks")
    if (
        type(receipts.get("schema_version")) is not int
        or receipts["schema_version"] != 1
    ):
        raise ValueError("receipts schema_version must be the integer 1")
    if receipts.get("prd") != prd or not isinstance(tasks, list) or not tasks:
        raise ValueError(f"receipts must be for PRD {prd} and list at least one task")
    for task in tasks:
        passed = task.get("passed")
        if type(passed) is not int or passed <= 0:
            raise ValueError(
                f"receipt task needs a positive integer passed count: {task}"
            )
        if not text(task.get("tests")) or not text(task.get("command")):
            raise ValueError(f"receipt task needs tests and command: {task}")
    host = receipts.get("real_host")
    if (
        not isinstance(host, dict)
        or host.get("status") != "unavailable"
        or not text(host.get("reason"))
    ):
        raise ValueError(
            "receipts real_host must be unavailable with a reason; never passed"
        )
    if "package_revision" in receipts:
        revision = receipts["package_revision"]
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("receipts package_revision must be 40 lowercase hex")


def validate_successor_receipts(
    successor: dict, supersedes_artifact: dict | None
) -> None:
    if not isinstance(successor, dict):
        raise ValueError("successor receipts must be a JSON object")
    validate_receipts(successor, prd="00018")
    if "package_revision" not in successor:
        raise ValueError("successor receipts need a package_revision")
    if (
        supersedes_artifact is None
        or successor.get("supersedes") != supersedes_artifact
    ):
        raise ValueError(
            "successor receipts must supersede the exact AP00013 receipts loaded"
        )
    paths = successor.get("paths")
    if not isinstance(paths, list) or not paths:
        raise ValueError("successor receipts must list at least one path")
    for path in paths:
        if (
            not isinstance(path, str)
            or {"", ".", ".."} & set(path.split("/"))
            or not (
                path in (*SHARED_PATHS, CONTROLLER_CONTRACT)
                or path.startswith(CONTROLLER_PREFIXES)
            )
        ):
            raise ValueError(
                f"successor path is not README, CHANGELOG or a controller asset: {path!r}"
            )
    if len(set(paths)) != len(paths):
        raise ValueError("successor paths must be unique")


def validate_host_receipts(receipts: dict, supersedes_artifact: dict | None) -> None:
    if not isinstance(receipts, dict):
        raise ValueError("host receipts must be a JSON object")
    validate_receipts(receipts, prd=HOST_RECEIPT_PRD)
    if "package_revision" not in receipts:
        raise ValueError("host receipts need a package_revision")
    if (
        supersedes_artifact is None
        or receipts.get("supersedes") != supersedes_artifact
    ):
        raise ValueError(
            "host receipts must supersede the exact AP00018 successor receipts loaded"
        )
    paths = receipts.get("paths")
    if not isinstance(paths, list) or not paths:
        raise ValueError("host receipts must list at least one path")
    for path in paths:
        if not isinstance(path, str) or path not in HOST_PATHS:
            raise ValueError(
                "host path is not README, CHANGELOG, autopilot.py or an AP00014 "
                f"asset: {path!r}"
            )
    if len(set(paths)) != len(paths):
        raise ValueError("host paths must be unique")


def refusal(revision: str, detail: str) -> ValueError:
    return ValueError(f"successor package_revision {revision} {detail}")


def first_line(stderr: str) -> str:
    lines = [line for line in stderr.strip().splitlines() if line.strip()]
    return lines[0] if lines else "git reported no error text"


def run_git(
    root: Path, revision: str, *args: str, text: bool = True
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=text,
            env={**os.environ, "LC_ALL": "C"},
        )
    except OSError as error:
        raise refusal(
            revision, f"cannot be checked: the git executable did not run: {error}"
        ) from error


def outside_any_repository(root: Path) -> bool:
    """True only for an existing directory git cannot tie to any repository.

    Decided from the file system, never from git's message text: no git
    location variable is set and no `.git` entry exists at or above the root.
    """
    if any(name in os.environ for name in GIT_LOCATION_VARIABLES):
        return False
    if not root.is_dir():
        return False
    resolved = root.resolve()
    return not any(
        os.path.lexists(directory / ".git")
        for directory in (resolved, *resolved.parents)
    )


def verify_listed_paths_match_revision(
    root: Path, revision: str, paths: set[str]
) -> None:
    """Refuse a successor whose listed paths changed since its package_revision.

    The check is skipped only when the git probe fails and the root is a
    directory outside any repository (see `outside_any_repository`): it has no
    history to check against, and production always runs inside a real
    checkout. Every other outcome is a refusal, never a skip: a probe failure
    with a repository in reach, and a probe that answers anything but `true`.
    """
    probe = run_git(root, revision, "rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0:
        if outside_any_repository(root):
            return
        raise refusal(revision, f"cannot be checked: {first_line(probe.stderr)}")
    answer = probe.stdout.strip()
    if answer != "true":
        raise refusal(
            revision,
            f"cannot be checked: {root} is not inside a git work tree "
            f"(git rev-parse --is-inside-work-tree answered {answer!r})",
        )
    resolved = run_git(root, revision, "cat-file", "-e", f"{revision}^{{commit}}")
    if resolved.returncode != 0:
        raise refusal(
            revision, f"cannot be resolved by git: {first_line(resolved.stderr)}"
        )
    for path in sorted(paths):
        committed = run_git(root, revision, "show", f"{revision}:{path}", text=False)
        if committed.returncode != 0:
            raise refusal(
                revision,
                f"cannot be read for {path!r}: "
                f"{first_line(committed.stderr.decode(errors='replace'))}",
            )
        try:
            current = (root / path).read_bytes()
        except OSError as error:
            raise refusal(
                revision,
                f"cannot be read for {path!r} in the work tree: {error}",
            ) from error
        if committed.stdout != current:
            raise refusal(
                revision,
                f"is stale for {path!r}: current bytes do not match that revision",
            )


def refresh_listed_row(row: dict, path: str, cited: dict, prd: str = "00018") -> None:
    """Make a certified row agree with the evidence the AP{prd} receipt gives it.

    Acceptance statuses follow the refreshed evidence, and prose that claims the
    delivery has not landed yet is replaced with prose about this row. A
    reason keeps every authored sentence that makes no such claim and gains a
    sentence saying the evidence has landed. Prose that claims nothing has
    nothing to contradict, so it survives.
    """
    row["evidence"] = dict(cited)
    reason = row["adaptation_reason"]
    if CLAIMS.search(reason):
        sentences = SENTENCE_END.split(reason.strip())
        kept = [sentence for sentence in sentences if not CLAIMS.search(sentence)]
        landed = (
            f"AP{prd} delivery evidence for {path} has landed: the digest "
            "records the packaged bytes at the tested package_revision, not "
            "host certification."
        )
        row["adaptation_reason"] = " ".join([*kept, landed])
    for case in row["acceptance_cases"]:
        case["status"] = cited["status"]
        if CLAIMS.search(case["expected_outcome"]):
            case["expected_outcome"] = (
                f"The packaged bytes of {path} exist at the recorded digest, "
                f"certified by the AP{prd} successor receipt at its "
                "package_revision."
            )

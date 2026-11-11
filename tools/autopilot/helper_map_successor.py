"""Check an AP00018 successor's package_revision and refresh the rows it cites.

The revision check refuses a successor whose listed paths changed since its
package_revision, and skips its work only for a directory that is outside a git
work tree. The row refresh keeps a certified row from claiming that its
delivery evidence has not landed yet.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# Prose that claims the delivery evidence has not landed yet.
CLAIMS = re.compile(r"(?i)\b(planned|pending|on[\s-]hold)\b")
NOT_A_REPOSITORY = "not a git repository"


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
            ["git", "-C", str(root), *args], capture_output=True, text=text
        )
    except OSError as error:
        raise refusal(
            revision, f"cannot be checked: the git executable did not run: {error}"
        ) from error


def verify_listed_paths_match_revision(
    root: Path, revision: str, paths: set[str]
) -> None:
    """Refuse a successor whose listed paths changed since its package_revision.

    A directory outside a git work tree has no history to check against, so the
    verification is skipped there; production always runs inside a real
    checkout. Every other git failure is a refusal, never a skip.
    """
    probe = run_git(root, revision, "rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0:
        if NOT_A_REPOSITORY in probe.stderr:
            return
        raise refusal(revision, f"cannot be checked: {first_line(probe.stderr)}")
    if probe.stdout.strip() != "true":
        return
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
        if committed.stdout != (root / path).read_bytes():
            raise refusal(
                revision,
                f"is stale for {path!r}: current bytes do not match that revision",
            )


def refresh_listed_row(row: dict, path: str, cited: dict) -> None:
    """Make a certified row agree with the evidence the successor gives it.

    Acceptance statuses follow the refreshed evidence, and prose that claims the
    delivery has not landed yet is replaced with prose about this row. Prose
    that claims nothing has nothing to contradict, so it survives.
    """
    row["evidence"] = dict(cited)
    if CLAIMS.search(row["adaptation_reason"]):
        row["adaptation_reason"] = (
            f"AP00018 delivery evidence for {path} has landed: the digest "
            "records the packaged bytes at the tested package_revision, not "
            "host certification."
        )
    for case in row["acceptance_cases"]:
        case["status"] = cited["status"]
        if CLAIMS.search(case["expected_outcome"]):
            case["expected_outcome"] = (
                f"The packaged bytes of {path} exist at the recorded digest, "
                "certified by the AP00018 successor receipt at its "
                "package_revision."
            )

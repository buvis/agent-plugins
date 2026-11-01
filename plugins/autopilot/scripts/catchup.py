"""Stateless optional gh/engram probe for catch-up.

`probe()` checks whether `gh` is authenticated and whether `engram` sees a
registered repo in the explicit project root, and returns the catch-up
sections to skip. It keeps no cache and reads or writes no state.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

_TIMEOUT = 15
_UNREGISTERED_MARKER = "not inside a registered repo"


def _run_probe(
    argv: list[str], *, run: Callable, which: Callable, cwd: Path
) -> subprocess.CompletedProcess | None:
    """Return the CompletedProcess, or None when the binary is absent,
    times out, or cannot be executed."""
    if which(argv[0]) is None:
        return None
    try:
        return run(argv, cwd=cwd, capture_output=True, text=True, timeout=_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return None


def probe(
    project_root: Path,
    *,
    run: Callable = subprocess.run,
    which: Callable = shutil.which,
) -> dict:
    """Probe `gh auth status` and `engram status --scope repo` in
    `project_root` and return `{"schema_version": 1, "gh", "engram", "skip"}`.
    A probe never narrows required review."""
    gh = _run_probe(["gh", "auth", "status"], run=run, which=which, cwd=project_root)
    engram = _run_probe(
        ["engram", "status", "--scope", "repo"], run=run, which=which, cwd=project_root
    )
    gh_token = "absent" if gh is None else ("ok" if gh.returncode == 0 else "unauthenticated")
    if engram is None:
        engram_token = "absent"
    elif _UNREGISTERED_MARKER in engram.stderr:
        engram_token = "unregistered"
    else:
        engram_token = "ok"
    skip = []
    if gh_token != "ok":
        skip.append("github-state")
    if engram_token != "ok":
        skip.append("engram")
    return {"schema_version": 1, "gh": gh_token, "engram": engram_token, "skip": skip}

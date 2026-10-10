"""The design approval's code baseline: raw hashes of the files its placement names."""

from __future__ import annotations

import hashlib
import stat
from pathlib import Path, PurePosixPath


def refuse_reason(repo: Path, path: str) -> str | None:
    """Why a baseline path is refused, or None. Checked before anything is read."""
    pure = PurePosixPath(path)
    if not path or "\\" in path or pure.is_absolute() or path.startswith("~"):
        return "not a repository-relative path"
    if ".." in pure.parts:
        return "holds a .. segment"
    current = repo
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            return "goes through a symbolic link"
    if not current.exists():
        return None
    mode = current.lstat().st_mode
    if stat.S_ISDIR(mode):
        return "is a directory"
    if not stat.S_ISREG(mode):
        return "is not a regular file"
    return None


def code_baseline(repo: Path, paths: list[str]) -> dict:
    """An approvedCode value: every file captured, or not_checked with the reason. Never partial."""
    unique = sorted(set(paths))
    if not unique:
        return {"status": "not_checked", "reason": "no placement paths given"}
    problems = []
    files = []
    for path in unique:
        reason = refuse_reason(repo, path)
        if reason:
            problems.append(f"{path} {reason}")
            continue
        target = repo / path
        if not target.exists():
            files.append({"path": path, "missing": True})
            continue
        try:
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError as error:
            problems.append(f"{path} cannot be read: {error.strerror}")
            continue
        files.append({"path": path, "sha256": digest})
    if problems:
        return {"status": "not_checked", "reason": "; ".join(problems)}
    return {"status": "captured", "files": files}


def warning(kind: str, message: str, path: str | None = None) -> dict[str, str]:
    item = {"kind": kind, "message": message}
    if path is not None:
        item["path"] = path
    return item


def code_drift(repo: Path, approved_code: dict | None) -> list[dict[str, str]]:
    """Advisory warnings: declared files added, changed, or deleted since the design approval.

    Missing evidence is reported as not checked, never as clean. Nothing here closes a gate.
    """
    if approved_code is None:
        return [warning("not-checked", "the design approval has no code baseline")]
    if approved_code.get("status") == "not_applicable":
        return []
    if approved_code.get("status") != "captured":
        reason = approved_code.get("reason", "no reason recorded")
        return [warning("not-checked", f"code baseline not captured: {reason}")]
    warnings = []
    for entry in approved_code.get("files", []):
        path = entry["path"]
        refused = refuse_reason(repo, path)
        if refused:
            warnings.append(warning("not-checked", f"{path} {refused}", path))
            continue
        target = repo / path
        if not target.exists():
            if "sha256" in entry:
                warnings.append(warning("code-drift", f"{path} was deleted", path))
            continue
        try:
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError as error:
            warnings.append(
                warning(
                    "not-checked", f"{path} cannot be read: {error.strerror}", path
                ),
            )
            continue
        if entry.get("missing"):
            warnings.append(warning("code-drift", f"{path} was added", path))
        elif digest != entry.get("sha256"):
            warnings.append(warning("code-drift", f"{path} changed", path))
    return warnings

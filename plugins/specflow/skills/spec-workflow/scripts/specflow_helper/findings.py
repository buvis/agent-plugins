"""The one shape every check finding takes."""

from __future__ import annotations

Finding = dict[str, str]


def finding(
    file: str,
    rule: str,
    message: str,
    fix: str,
    level: str = "error",
) -> Finding:
    return {"level": level, "file": file, "rule": rule, "message": message, "fix": fix}

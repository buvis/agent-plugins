"""Canonical text and hashes. These rules are approval semantics: changing them stales every approval."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
LIST_MARKER = r"[ \t]*(?:[-*+]|\d+\.)[ \t]+"
CHECKBOX = re.compile(rf"^({LIST_MARKER})\[([ xX~-])\]")
PROGRESS = re.compile(rf"^{LIST_MARKER}(?:Outcome|Exception):")
COMPLETION = "## Completion criteria"


def indent_of(line: str) -> int:
    """Leading columns, a tab counting as four."""
    width = 0
    for char in line:
        if char == " ":
            width += 1
        elif char == "\t":
            width += 4
        else:
            break
    return width


def scan_lines(text: str) -> list[tuple[str, bool, bool]]:
    """(line, in_fence, in_task_item) for each line of the text.

    A fence opens on three or more backticks or tildes after any indent and
    closes on the next line starting with the same character at least as many
    times. A task item is a checkbox item above `## Completion criteria`; it
    runs until the next non-blank line indented no deeper than its marker.
    """
    result: list[tuple[str, bool, bool]] = []
    fence: str | None = None
    tasks: list[int] = []
    above_completion = True
    for line in text.split("\n"):
        match = FENCE.match(line)
        if fence is not None:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                fence = None
            result.append((line, True, bool(tasks)))
            continue
        if line.strip():
            column = indent_of(line)
            while tasks and column <= tasks[-1]:
                tasks.pop()
            if line.rstrip() == COMPLETION:
                above_completion = False
        if match:
            fence = match[1]
            result.append((line, True, bool(tasks)))
            continue
        if above_completion and CHECKBOX.match(line):
            tasks.append(indent_of(line))
        result.append((line, False, bool(tasks)))
    return result


def canonical(text: str, *, tasks: bool = False) -> str:
    """The text an approval hash covers (design: approval representation)."""
    text = text.removeprefix("﻿").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    if tasks:
        kept = []
        for line, in_fence, in_task in scan_lines("\n".join(lines)):
            if in_fence:
                kept.append(line)
            elif not (in_task and PROGRESS.match(line)):
                kept.append(CHECKBOX.sub(r"\1[ ]", line, count=1))
        lines = kept
    return "\n".join(lines) + "\n"


def sha256_canonical(path: Path) -> str:
    """SHA-256 of the canonical text; the tasks rules apply to tasks.md only."""
    text = path.read_bytes().decode("utf-8")
    data = canonical(text, tasks=path.name == "tasks.md").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_raw(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

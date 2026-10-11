"""Read-only views of spec Markdown: prose lines, sections, IDs, and traces."""

from __future__ import annotations

import re

from .canonical import canonical, scan_lines

REQUIREMENT_HEADING = re.compile(r"^### (?:([A-Z][A-Z0-9]*-\d{3})|Requirement (\d+))\b")
WITHDRAWN = re.compile(r"^### [A-Z][A-Z0-9]*-\d{3}: withdrawn\s*$")
CRITERION = re.compile(r"^(\d+)\. ")
CROSS_SPEC = re.compile(
    r"(\d{5}|folder:[^\s,;]+) ([A-Z][A-Z0-9]*-\d{3})"
    r"(?: (?:criterion|criteria) (\d+(?:, ?\d+)*))?",
)
CLAUSE = re.compile(r"^(\d+)\.(\d+) ")


def prose(text: str) -> list[tuple[int, str]]:
    """(line number, line) outside fences, of the canonical text."""
    return [
        (i + 1, line)
        for i, (line, in_fence, _) in enumerate(scan_lines(canonical(text)))
        if not in_fence
    ]


def sections(text: str) -> dict[str, list[str]]:
    """Level-two heading -> its lines up to the next level-two heading, outside fences."""
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    for _, line in prose(text):
        if line.startswith("## "):
            current = found.setdefault(line[3:].strip(), [])
        elif current is not None:
            current.append(line)
    return found


def requirement_ids(text: str) -> dict[str, set[int]]:
    """Requirement ID -> its numbered criteria ("1" stands for Kiro's Requirement 1).

    A withdrawn requirement (`### <ID>: withdrawn`) holds nothing and is left out;
    its ID stays reserved through the duplicate check.
    """
    lines = prose(text)
    ids: dict[str, set[int]] = {}
    current: str | None = None
    in_requirements = "## Requirements" not in {line for _, line in lines}
    for _, line in lines:
        if line.startswith("## "):
            in_requirements = line.strip() == "## Requirements"
            current = None
            continue
        match = REQUIREMENT_HEADING.match(line) if in_requirements else None
        if match and WITHDRAWN.match(line):
            current = None
        elif match:
            current = match[1] or match[2]
            ids.setdefault(current, set())
        elif line.startswith("### "):
            current = None
        elif current and (number := CRITERION.match(line)):
            ids[current].add(int(number[1]))
    return ids


def bugfix_clauses(text: str) -> dict[str, set[int]]:
    """Section number ("1", "2", "3") -> clause numbers, from a bugfix.md."""
    clauses: dict[str, set[int]] = {}
    for _, line in prose(text):
        if match := CLAUSE.match(line):
            clauses.setdefault(match[1], set()).add(int(match[2]))
    return clauses


def known_ids(text: str, bugfix: bool) -> set[str]:
    """Every ID a trace may cite: requirements and their criteria, or bugfix clauses."""
    groups = bugfix_clauses(text) if bugfix else requirement_ids(text)
    known = set(groups)
    for key, numbers in groups.items():
        known |= {f"{key}.{n}" for n in numbers}
    return known


def traceability_entries(lines: list[str]) -> list[str]:
    """Entries of the Criteria (or Criterion) column of the traceability table."""
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in lines
        if line.strip().startswith("|")
    ]
    if not rows:
        return []
    names = ("Criteria", "Criterion")
    column = next((i for i, cell in enumerate(rows[0]) if cell in names), None)
    if column is None:
        return []
    entries = []
    for row in rows[1:]:
        if column >= len(row) or set(row[column]) <= set("-: "):
            continue
        for entry in row[column].split(","):
            entry = entry.strip().strip("`")
            if not CROSS_SPEC.match(entry):
                entries.append(entry)
    return entries


def traced_ids(text: str) -> set[str]:
    """Requirement IDs the task plan cites, in either numbering; cross-spec citations excluded."""
    traced: set[str] = set()
    for _, line in prose(text):
        stripped = line.strip().lstrip("-*+ ").strip("_")
        if not stripped.startswith("Requirements:"):
            continue
        value = CROSS_SPEC.sub("", stripped.removeprefix("Requirements:"))
        for token in re.split(r"[,;\s]+", value):
            token = token.strip("_`")
            if re.fullmatch(r"[A-Z][A-Z0-9]*-\d{3}(?:\.\d+)?|\d+(?:\.\d+)?", token):
                traced.add(token.split(".")[0])
    return traced


def sources_value(text: str, *, bugfix: bool) -> str | None:
    """The first Sources: line where the contract puts it, without its label."""
    section = None
    for _, line in prose(text):
        if line.startswith("## "):
            section = line.strip()
        elif line.startswith("Sources:"):
            if (section == "## Introduction") if bugfix else section is None:
                return line.removeprefix("Sources:").strip()
    return None

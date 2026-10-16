"""Read-only views of spec Markdown: prose lines, sections, IDs, and traces."""

from __future__ import annotations

import re

from .canonical import canonical, scan_lines

REQUIREMENT_HEADING = re.compile(
    r"^### (?:([A-Z][A-Z0-9]*-[0-9]{3})|Requirement ([0-9]+))\b"
)
WITHDRAWN = re.compile(r"^### [A-Z][A-Z0-9]*-[0-9]{3}: withdrawn\s*$")
CRITERION = re.compile(r"^([0-9]+)\. ")
CROSS_SPEC = re.compile(
    r"([0-9]{5}|folder:[^\s,;]+) ([A-Z][A-Z0-9]*-[0-9]{3})"
    r"(?: (?:criterion|criteria) ([0-9]+(?:, ?[0-9]+)*))?",
)
CLAUSE = re.compile(r"^([0-9]+)\.([0-9]+) ")


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


def requirement_blocks(text: str) -> dict[str, list[str]]:
    """Requirement ID -> the lines under its heading ("1" stands for Kiro's Requirement 1).

    A withdrawn requirement (`### <ID>: withdrawn`) holds nothing and is left out;
    its ID stays reserved through the duplicate check.
    """
    lines = prose(text)
    blocks: dict[str, list[str]] = {}
    current: list[str] | None = None
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
            current = blocks.setdefault(match[1] or match[2], [])
        elif line.startswith("### "):
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def requirement_ids(text: str) -> dict[str, set[int]]:
    """Requirement ID -> its numbered criteria; withdrawn requirements are left out."""
    return {
        ident: {int(m[1]) for line in block if (m := CRITERION.match(line))}
        for ident, block in requirement_blocks(text).items()
    }


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
            if re.fullmatch(
                r"[A-Z][A-Z0-9]*-[0-9]{3}(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?", token
            ):
                traced.add(token.split(".")[0])
    return traced


# A citation token: an ID of the contract's shape, read loosely so a typo such as
# `REQ-0010` or `REQ-001a` is still a citation (and reported), or Kiro's `1.2`.
ID_CITATION = re.compile(r"([A-Z][A-Z0-9]*-[0-9A-Za-z]+)(?:\.([0-9]+))?")
KIRO_CITATION = re.compile(r"([0-9]+)(?:\.([0-9]+))?")
CITING_FIELDS = ("Requirements:", "Acceptance criteria:")


def citing_tokens(text: str) -> list[tuple[int, list[str]]]:
    """(line number, tokens) of each Requirements: or Acceptance criteria: line.

    Cross-spec citations are left out: they are checked against their own spec.
    """
    found = []
    for number, line in prose(text):
        stripped = line.strip().lstrip("-*+ ").strip("_")
        field = next((f for f in CITING_FIELDS if stripped.startswith(f)), None)
        if field is not None:
            value = CROSS_SPEC.sub("", stripped.removeprefix(field))
            tokens = [t.strip("_`") for t in re.split(r"[,;\s]+", value)]
            found.append((number, tokens))
    return found


def unheld_citations(tasks: str, held: dict[str, set[int]]) -> list[tuple[int, str]]:
    """(line, citation) of own-spec citations the requirements do not define.

    Tokens are read as `traced_ids` reads them: an ID, then the word `criterion` or
    `criteria` whose numbers belong to the held ID before it; anything else on the
    line is not a citation and (except `and`) ends that list, so stray prose raises
    nothing.
    """
    shapes = [ID_CITATION]
    if any(ident.isdigit() for ident in held):
        shapes.append(KIRO_CITATION)
    unheld: list[tuple[int, str]] = []
    for number, tokens in citing_tokens(tasks):
        ident, listing = "", False
        for token in tokens:
            if token in ("criterion", "criteria"):
                listing = ident in held
            elif listing and token.isdigit():
                if int(token) not in held[ident]:
                    unheld.append((number, f"{ident} criterion {token}"))
            else:
                match = next(filter(None, (s.fullmatch(token) for s in shapes)), None)
                if match is None:
                    listing = listing and token == "and"
                    continue
                ident, listing = match[1], False
                if ident not in held:
                    unheld.append((number, ident))
                elif match[2] and int(match[2]) not in held[ident]:
                    unheld.append((number, f"{ident} criterion {match[2]}"))
    return unheld


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

"""Read the `## Consolidated Findings` section of a review file into rows.

Port of the pinned `findings_section._reviewed_keys`: both shapes the section
is written in (the `- [m/n]` bullet list and the named-column pipe table) are
read, and a table that cannot be read whole is reported, never half-read.
Stdlib only; no file, state or runtime-module access.
"""

from __future__ import annotations

import re
from typing import NamedTuple

_FINDINGS_HEADING_RE = re.compile(r"^##\s+Consolidated Findings\s*$", re.MULTILINE)
_NEXT_H2_RE = re.compile(r"^##\s", re.MULTILINE)
# `- [2/3] 🟠 wrong default | src/b.py:10 | Found by: alice, bob`
_FINDING_ROW_RE = re.compile(r"^-\s*\[\d+/\d+\]\s*(.+)$", re.MULTILINE)
# A data row of a findings table, with or without the leading Ref cell.
_TABLE_DATA_ROW_RE = re.compile(r"^\|(?:\s*R\d+\s*\|)?\s*\[\d+/\d+\]\s*\|", re.MULTILINE)
# Once the header is found, every pipe line that is not the |---| rule is a
# data row, and it must end with a pipe: an off-shape or truncated row makes
# the table unreadable instead of silently dropping the finding it carried.
_CANDIDATE_ROW_RE = re.compile(r"^\s*\|")
_SEPARATOR_ROW_RE = re.compile(r"^\s*\|(\s*:?-{3,}:?\s*\|)+\s*$")
_TERMINATED_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_REF_CELL_RE = re.compile(r"^R\d+$", re.IGNORECASE)
_CONSENSUS_CELL_RE = re.compile(r"^\[\d+/\d+\]$")
_TABLE_HEADER_RE = re.compile(r"^\|(.+)\|\s*$", re.MULTILINE)
_TABLE_COLUMNS = ("severity", "issue", "file")
_SEVERITY_EMOJI = {
    "\U0001f534": "critical",
    "\U0001f7e0": "high",
    "\U0001f7e1": "medium",
    "⚪": "low",
}
_SEVERITY_WORDS = frozenset(_SEVERITY_EMOJI.values())


class Row(NamedTuple):
    """One consolidated-findings row. `ref` is "" for a bullet row or a table
    without a Ref column."""

    ref: str
    severity: str
    file: str
    issue: str


def _split_severity_cell(cell: str) -> tuple[str, str]:
    """(severity word, remaining text) for `🟠`, `high`, `🟠 text` or
    `🟠 High text`."""
    rest = cell.strip()
    severity = ""
    if rest[:1] in _SEVERITY_EMOJI:
        severity, rest = _SEVERITY_EMOJI[rest[:1]], rest[1:].strip()
    word, _, tail = rest.partition(" ")
    if word.lower() in _SEVERITY_WORDS:
        severity, rest = severity or word.lower(), tail
    return severity, rest


def _normalize_issue(issue: str) -> str:
    """Issue text with escaped pipes collapsed, a leading severity word
    dropped and whitespace squeezed; case is kept."""
    return " ".join(_split_severity_cell(issue.replace("\\|", "|"))[1].split())


def finding_key(severity: str, file: str, issue: str) -> tuple[str, str, str]:
    """(severity word, file, lower-cased normalized issue) as both sides of a
    cross-check compare a finding. File case is kept."""
    return (
        _split_severity_cell(severity)[0],
        file.replace("\\|", "|").strip(),
        _normalize_issue(issue).lower(),
    )


def _table_cells(line: str) -> list[str]:
    """A pipe row's cells, unstripped so an embedded `\\|` keeps its spacing."""
    return line.strip().strip("|").split("|")


def _row_from_table(header: list[str], cells: list[str]) -> Row | None:
    """The row, or None when it is truncated or its Ref/Consensus cell is
    off-shape."""
    sev_i = header.index("severity")
    issue_i = header.index("issue")
    file_i = header.index("file")
    ref_i = header.index("ref") if "ref" in header else 0
    consensus_i = header.index("consensus") if "consensus" in header else 0
    if len(cells) <= max(sev_i, issue_i, file_i, ref_i, consensus_i):
        return None
    ref = ""
    if "ref" in header:
        matched = _REF_CELL_RE.match(cells[ref_i].strip())
        if matched is None:
            return None
        ref = matched.group(0).upper()
    if "consensus" in header and not _CONSENSUS_CELL_RE.match(cells[consensus_i].strip()):
        return None
    if len(cells) == len(header):
        issue, file = cells[issue_i], cells[file_i]
    else:
        # The issue cell absorbed `|`s: rejoin Issue..File before stripping,
        # then take the file off the right end.
        trailing = len(header) - 1 - file_i
        span = "|".join(cells[issue_i : len(cells) - trailing]).strip()
        issue, _, file = span.rpartition("|")
    severity, file, _ = finding_key(cells[sev_i], file, issue)
    return Row(ref, severity, file, _normalize_issue(issue))


def _table_header(line: str) -> list[str] | None:
    """Lower-cased header cells when the line names Severity, Issue and File."""
    cells = [c.strip().lower() for c in _table_cells(line)]
    if _TABLE_HEADER_RE.match(line) and all(c in cells for c in _TABLE_COLUMNS):
        return cells
    return None


def _table_rows(section: str) -> tuple[list[Row], str | None]:
    header: list[str] | None = None
    rows: list[Row] = []
    refs: set[str] = set()
    for line in section.splitlines():
        if header is None:
            header = _table_header(line)
            continue
        if _CANDIDATE_ROW_RE.match(line) and not _SEPARATOR_ROW_RE.match(line):
            if not _TERMINATED_ROW_RE.match(line):
                return [], "unreadable-table"
            row = _row_from_table(header, _table_cells(line))
            if row is None or (row.ref and row.ref in refs):
                return [], "unreadable-table"
            refs.add(row.ref)
            rows.append(row)
    if rows:
        return rows, None
    if header is None and not _TABLE_DATA_ROW_RE.search(section):
        return [], None
    return [], "unreadable-table"


def reviewed_rows(text: str) -> tuple[list[Row], str | None]:
    """Every row of the first `## Consolidated Findings` section and the
    reading problem: None, `"no-section"` or `"unreadable-table"`."""
    heading = _FINDINGS_HEADING_RE.search(text)
    if heading is None:
        return [], "no-section"
    following = _NEXT_H2_RE.search(text, heading.end())
    section = text[heading.end() : following.start() if following else len(text)]
    rows: list[Row] = []
    for row in _FINDING_ROW_RE.findall(section):
        # From the right: a bullet ends `| {file} | Found by: ...`, so a pipe
        # in the issue text cannot shift the file cell.
        cells = [c.strip() for c in row.rsplit("|", 2)]
        severity, issue = _split_severity_cell(cells[0])
        key = finding_key(severity, cells[1] if len(cells) > 1 else "", issue)
        rows.append(Row("", key[0], key[1], _normalize_issue(issue)))
    table, problem = _table_rows(section)
    return rows + table, problem

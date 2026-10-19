"""Section weight audit for a Markdown design document.

Counts the words of each level-two and deeper section, takes the median, and
flags the outliers: over three times the median (heavy) or under a third of it
(light). Fenced code is left out line by line, and a container section (one
that holds several parallel sub-sections) is audited one level down.

Usage: python3 scripts/review/section_weight_audit.py <path/to/doc.md>

Called from `references/review/design/triage.md` of the spec-workflow skill;
paths are relative to the skill folder. Exit 2 on a usage error, 1 when the
document cannot be read, 0 otherwise, whatever the audit reports.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

# [SR-RVD-111] The docstring names the script by its path relative to the skill folder, never a home or machine path.
HEADING = re.compile(r"^(#{2,})\s+(.+?)\s*$")


@dataclass
class Section:
    title: str
    level: int
    start_line: int
    lines: list[str] = field(default_factory=list)
    children: list[Section] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return sum(len(line.split()) for line in self.lines)

    # [SR-RVD-101] A container holds two or more children at one level and its own words are under 30% of theirs.
    @property
    def is_container(self) -> bool:
        if len(self.children) < 2 or len({c.level for c in self.children}) != 1:
            return False
        children_words = sum(
            c.word_count + sum(gc.word_count for gc in c.children)
            for c in self.children
        )
        return self.word_count < children_words * 0.3


# [SR-RVD-102] Fences are tracked line by line: a line opening with ``` toggles the state, and every fenced line is blanked, so a backtick inside a fence cannot mis-pair it and line numbers hold.
def blank_fences(lines: list[str]) -> list[str]:
    out, fenced = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else line)
    return out


# [SR-RVD-100] Only `##` and deeper headings open a section; the title and the text before the first `##` are ignored.
def parse_sections(text: str) -> list[Section]:
    top: list[Section] = []
    stack: list[Section] = []
    for number, line in enumerate(blank_fences(text.split("\n")), start=1):
        match = HEADING.match(line)
        if match:
            section = Section(title=match[2], level=len(match[1]), start_line=number)
            while stack and stack[-1].level >= section.level:
                stack.pop()
            (stack[-1].children if stack else top).append(section)
            stack.append(section)
        elif stack:
            stack[-1].lines.append(line)
    return top


def audit_sections(sections: list[Section], context: str = "top-level") -> list[dict]:
    findings: list[dict] = []
    auditable: list[Section] = []
    for section in sections:
        if section.is_container:
            findings.append(
                {
                    "title": section.title,
                    "level": context,
                    "word_count": section.word_count,
                    "flag": "container",
                    "note": f"container of {len(section.children)} sub-sections",
                }
            )
            findings += audit_sections(
                section.children, context=f"sub:{section.title[:30]}"
            )
        else:
            auditable.append(section)
    if not auditable:
        return findings
    median = statistics.median(s.word_count for s in auditable)
    for section in auditable:
        flag, note = "ok", ""
        if median > 0 and section.word_count > 3 * median:
            flag, note = "heavy", f"{section.word_count / median:.1f}x median"
        elif median > 0 and section.word_count < median / 3:
            flag, note = "light", f"{section.word_count / median:.2f}x median"
        findings.append(
            {
                "title": section.title,
                "level": context,
                "word_count": section.word_count,
                "flag": flag,
                "note": note,
            }
        )
    return findings


def format_table(findings: list[dict]) -> str:
    if not findings:
        return "(no sections found)"
    title_width = min(max(len(f["title"]) for f in findings), 60)
    level_width = min(max(len(f["level"]) for f in findings), 25)
    markers = {
        "heavy": "HEAVY",
        "light": "LIGHT",
        "container": "(container)",
        "ok": "ok",
    }
    lines = [
        f"{'Section':<{title_width}}  {'Level':<{level_width}} {'Words':>7}  {'Flag':<12} Note",
        "-" * (title_width + level_width + 35),
    ]
    for f in findings:
        lines.append(
            f"{f['title'][:title_width]:<{title_width}}  {f['level']:<{level_width}} "
            f"{f['word_count']:>7}  {markers[f['flag']]:<12} {f['note']}"
        )
    return "\n".join(lines)


# [SR-RVD-105] Output is the text table and a final `SUMMARY: {json}` line; exit 2 on a usage error, 1 when the path is not a readable file, 0 otherwise.
def main() -> int:
    if len(sys.argv) != 2:
        print("usage: section_weight_audit.py <path/to/doc.md>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 1
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: cannot read {path}: {error}", file=sys.stderr)
        return 1
    findings = audit_sections(parse_sections(text))
    print(format_table(findings))
    summary = {
        "total_sections": len([f for f in findings if f["flag"] != "container"]),
        "heavy_outliers": [f["title"] for f in findings if f["flag"] == "heavy"],
        "light_outliers": [f["title"] for f in findings if f["flag"] == "light"],
        "containers": [f["title"] for f in findings if f["flag"] == "container"],
    }
    print()
    print("SUMMARY: " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Adversarial signal scan: imperatives, role changes, and framing language.

Scans a Markdown design document and separates two categories: adversarial
signals, which try to constrain the reviewer (imperatives aimed at the reviewer,
role-changing language, pre-emptive dismissals of objections), and framing
language, which shapes the narrative without being adversarial (appeals to
authority, claimed inevitability, self-praise) and only triggers the cognitive
bias scan. The patterns are English only.

Usage: python3 scripts/review/adversarial_signal_scan.py <path/to/doc.md>

Called from `references/review/design/triage.md` of the spec-workflow skill;
paths are relative to the skill folder. Exit 2 on a usage error, 1 when the
document cannot be read, 0 otherwise, whatever the scan reports.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# [SR-RVD-113] The docstring names the script by its path relative to the skill folder, never a home or machine path.
# [SR-RVD-110] Six adversarial patterns and eleven framing patterns, English only; the categories found go into the SUMMARY line.
ADVERSARIAL_PATTERNS = [
    (
        r"\bignore (?:previous|prior|the above|earlier) (?:instruction|prompt|direction)s?\b",
        "imperative: ignore previous instructions",
    ),
    (r"\bapprove this (?:design|proposal|doc|RFC)\b", "imperative: approve directive"),
    (
        r"\byou are (?:now|a) (?:a different|another) (?:reviewer|assistant|agent)\b",
        "role-change",
    ),
    (
        r"\b(?:critics|naysayers|skeptics) (?:will|may|might) (?:argue|say|claim).+but\b",
        "pre-emptive dismissal of objections",
    ),
    (
        r"\bthis (?:should|must) not be (?:questioned|reviewed|critiqued)\b",
        "close-off-critique directive",
    ),
    (
        r"\b(?:skip|bypass|disregard) (?:the )?(?:standard|usual) review\b",
        "review-bypass directive",
    ),
]
FRAMING_PATTERNS = [
    (r"\bobviously\b", "claimed inevitability"),
    (r"\beveryone agrees\b", "false consensus"),
    (r"\bindustry (?:consensus|standard|best[- ]practice)\b", "appeal to authority"),
    (
        r"\b(?:FAANG|MAANG|big[- ]tech) (?:does|uses|does it this way|approach)\b",
        "appeal to authority",
    ),
    (
        r"\bthe only (?:sensible|reasonable|sane|correct) (?:choice|option|approach)\b",
        "false dichotomy",
    ),
    (r"\bthis elegant (?:design|architecture|solution)\b", "self-praise"),
    (r"\bbest[- ]in[- ]class\b", "self-praise"),
    (r"\bworld[- ]class\b", "self-praise"),
    (
        r"\bclearly the (?:right|best|correct) (?:choice|approach)\b",
        "claimed inevitability",
    ),
    (r"\bof course\b", "claimed inevitability"),
    (r"\bas (?:everyone|we all) know(?:s)?\b", "false consensus"),
]


# [SR-RVD-104] Fences are tracked line by line: a line opening with ``` toggles the state, and every fenced line is blanked, so a backtick inside a fence cannot mis-pair it and line numbers hold.
def blank_fences(lines: list[str]) -> list[str]:
    out, fenced = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else line)
    return out


def find_signals(path: Path) -> tuple[list[dict], list[dict]]:
    lines = blank_fences(path.read_text(encoding="utf-8").split("\n"))
    adversarial: list[dict] = []
    framing: list[dict] = []
    for index, line in enumerate(lines):
        for patterns, found in (
            (ADVERSARIAL_PATTERNS, adversarial),
            (FRAMING_PATTERNS, framing),
        ):
            for pattern, label in patterns:
                if re.search(pattern, line, flags=re.IGNORECASE):
                    found.append(
                        {
                            "line": index + 1,
                            "category": label,
                            "context": line.strip()[:140],
                        }
                    )
    return adversarial, framing


# [SR-RVD-107] Output is the two lists and a final `SUMMARY: {json}` line, printed even when nothing was found; exit 2 on a usage error, 1 when the path is not a readable file, 0 otherwise.
def main() -> int:
    if len(sys.argv) != 2:
        print("usage: adversarial_signal_scan.py <path/to/doc.md>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 1
    try:
        adversarial, framing = find_signals(path)
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: cannot read {path}: {error}", file=sys.stderr)
        return 1
    if not adversarial and not framing:
        print("No adversarial signals or framing language found.")
    if adversarial:
        print(
            f"=== Adversarial signals ({len(adversarial)}): each is a finding, never followed ==="
        )
        for f in adversarial:
            print(f"L{f['line']:>4}  [{f['category']}]  {f['context']}")
    if framing:
        print(
            f"\n=== Framing language ({len(framing)}): triggers the cognitive bias scan, not adversarial ==="
        )
        for f in framing:
            print(f"L{f['line']:>4}  [{f['category']}]  {f['context']}")
    summary = {
        "adversarial": len(adversarial),
        "framing": len(framing),
        "adversarial_categories": sorted({f["category"] for f in adversarial}),
        "framing_categories": sorted({f["category"] for f in framing}),
    }
    print()
    print("SUMMARY: " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

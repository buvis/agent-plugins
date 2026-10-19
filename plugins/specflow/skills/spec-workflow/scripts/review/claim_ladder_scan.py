"""Claim ladder scan: compressed qualifiers with no measurement nearby.

Scans a Markdown design document for vague qualifiers ("scalable", "robust",
"fast", "secure", and the like) and reports each with its line, so the reviewer
can run the claim ladder on it. A qualifier counts as grounded when a
measurement (a number with a unit, a percentage, a latency budget) sits within
two lines of it. Requirement, task, and rule IDs such as REQ-001, T-003, or
SR-REQ-007, and spec numbers such as 00007, are not measurements.

Usage: python3 scripts/review/claim_ladder_scan.py <path/to/doc.md>

Called from `references/review/design/triage.md` of the spec-workflow skill;
paths are relative to the skill folder. Exit 2 on a usage error, 1 when the
document cannot be read, 0 otherwise, whatever the scan reports.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# [SR-RVD-112] The docstring names the script by its path relative to the skill folder, never a home or machine path.
# [SR-RVD-108] The fixed list of 34 qualifiers, matched as whole words in any letter case.
QUALIFIERS = [
    "scalable",
    "robust",
    "fast",
    "slow",
    "secure",
    "modular",
    "extensible",
    "simple",
    "elegant",
    "intuitive",
    "performant",
    "efficient",
    "lightweight",
    "high-quality",
    "world-class",
    "best-in-class",
    "industry-leading",
    "battle-tested",
    "production-ready",
    "enterprise-grade",
    "resilient",
    "highly available",
    "low-latency",
    "real-time",
    "near-real-time",
    "easy to use",
    "user-friendly",
    "seamless",
    "smooth",
    "powerful",
    "flexible",
    "configurable",
    "future-proof",
    "well-designed",
]
QUALIFIER = re.compile(
    r"\b(" + "|".join(re.escape(q) for q in QUALIFIERS) + r")\b", flags=re.IGNORECASE
)

# A measurement within two lines grounds a qualifier: a number with a unit, a
# percentage, a rate, a size, a percentile, any number of two or more digits, a
# price, or a multiplier.
MEASUREMENT_PATTERNS = [
    r"\d+\s*(?:ms|s|sec|second|minute|min|hour|h|day|week|month|year)s?\b",
    r"\d+\s*(?:%|percent|percentile)",
    r"\d+\s*(?:rps|qps|tps|req/s|requests?/sec)",
    r"\d+\s*(?:GB|MB|KB|TB|PB|bytes?)",
    r"p\d{1,3}\b",
    r"\b\d{2,}\b",
    r"\$\d+",
    r"\bx\d+\b|\b\d+x\b",
]
# [SR-RVD-109] ID tokens are blanked before the measurement search, so a requirement, task, or rule ID and a spec number ground nothing.
# ponytail: a spec number is a zero-padded five-digit token or an NNNNN-title folder; a plain 10000 stays a measurement.
ID_TOKEN = re.compile(
    r"\b(?:[A-Z]{1,4}-)+\d{3}(?:\.\d+)?\b|\b0\d{4}\b|\b\d{5}-[a-z0-9]"
)


# [SR-RVD-103] Fences are tracked line by line: a line opening with ``` toggles the state, and every fenced line is blanked, so a backtick inside a fence cannot mis-pair it and line numbers hold.
def blank_fences(lines: list[str]) -> list[str]:
    out, fenced = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else line)
    return out


def has_measurement_nearby(lines: list[str], index: int, radius: int = 2) -> bool:
    start, end = max(0, index - radius), min(len(lines), index + radius + 1)
    context = ID_TOKEN.sub(" ", " ".join(lines[start:end]))
    return any(re.search(p, context, flags=re.IGNORECASE) for p in MEASUREMENT_PATTERNS)


def scan(path: Path) -> list[dict]:
    lines = blank_fences(path.read_text(encoding="utf-8").split("\n"))
    findings: list[dict] = []
    for index, line in enumerate(lines):
        for match in QUALIFIER.finditer(line):
            findings.append(
                {
                    "line": index + 1,
                    "qualifier": match[1],
                    "context": line.strip()[:120],
                    "grounded": has_measurement_nearby(lines, index),
                }
            )
    return findings


# [SR-RVD-106] Output is the ungrounded and grounded lists and a final `SUMMARY: {json}` line, printed even when nothing was found; exit 2 on a usage error, 1 when the path is not a readable file, 0 otherwise.
def main() -> int:
    if len(sys.argv) != 2:
        print("usage: claim_ladder_scan.py <path/to/doc.md>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 1
    try:
        findings = scan(path)
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: cannot read {path}: {error}", file=sys.stderr)
        return 1
    ungrounded = [f for f in findings if not f["grounded"]]
    grounded = [f for f in findings if f["grounded"]]
    if not findings:
        print("No compressed qualifiers found.")
    else:
        print(
            f"=== Ungrounded qualifiers ({len(ungrounded)}): run the claim ladder ==="
        )
        for f in ungrounded:
            print(f"L{f['line']:>4}  [{f['qualifier']}]  {f['context']}")
        if grounded:
            print(
                f"\n=== Grounded qualifiers ({len(grounded)}): measurement nearby ==="
            )
            for f in grounded:
                print(f"L{f['line']:>4}  [{f['qualifier']}]  {f['context']}")
    summary = {
        "total": len(findings),
        "ungrounded": len(ungrounded),
        "grounded": len(grounded),
        "ungrounded_unique": sorted({f["qualifier"].lower() for f in ungrounded}),
    }
    print()
    print("SUMMARY: " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""The checks of 00006 (T-072, T-034, T-039), registered in CHECKS of checks.py."""

from __future__ import annotations

import re
from functools import partial

from .checks import TASKS_ON, Context, check, error, read_text, rel
from .findings import Finding, finding
from .spec_text import prose, sections
from .state import artifact_paths

SCREEN = r"[A-Za-z][\w-]*"
LABEL = r"(?:\[[^\]\n]*\]|\([^)\n]*\)|\{[^}\n]*\})"
END = rf"({SCREEN}){LABEL}?"
HEADER = re.compile(r"^(?:flowchart|graph)(?:\s+(?:TB|TD|BT|RL|LR))?$")
NODE = re.compile(rf"^{END}$")
EDGE = re.compile(rf"^{END}\s*(?:-->\s*\|([^|\n]+)\|\s*|--\s+(.+?)\s+-->\s*){END}$")
HREF = re.compile(r"""href\s*=\s*["'](?:\./)?([^"'#?]+)""", re.IGNORECASE)
INDEX = "index"
Edge = tuple[int, str, str, str]  # line, source, action, target
CODE_SPAN = re.compile(r"`([^`\s]+)`")
LOCATION = re.compile(r"^\s*- Location:\s*(.*)$")
# The template's ## Module placement, or a native or bugfix design's section that names files.
PLACEMENT = re.compile(r"placement|file|fix implementation", re.IGNORECASE)


def journey_lines(text: str) -> list[tuple[int, str]]:
    """(line number, stripped line) inside each fenced mermaid flowchart or graph block."""
    lines: list[tuple[int, str]] = []
    block: list[tuple[int, str]] | None = None
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if block is None:
            if line.startswith("```") and line[3:].strip() == "mermaid":
                block = []
        elif line.startswith("```"):
            first = next((t for _, t in block if not t.startswith("%%")), "")
            if HEADER.match(first):
                lines += block
            block = None
        elif line:
            block.append((n, line))
    return lines


def parse_journey(text: str) -> tuple[set[str], list[Edge], list[tuple[int, str]]]:
    """Screen IDs, edges, and the lines of no accepted kind."""
    screens: set[str] = set()
    edges: list[Edge] = []
    bad: list[tuple[int, str]] = []
    for n, line in journey_lines(text):
        if line.startswith("%%") or HEADER.match(line):
            continue
        if edge := EDGE.match(line):
            source, piped, dashed, target = edge.groups()
            screens |= {source, target}
            edges.append((n, source, (piped or dashed).strip(), target))
        elif node := NODE.match(line):
            screens.add(node[1])
        else:
            bad.append((n, line))
    return screens, edges, bad


@check("sketch-screens", frozenset({"intake"}))
def sketch_screens(ctx: Context) -> list[Finding]:
    """One mockup per screen of spike/journey.md, no orphan mockup, a link per edge (INT-002.8)."""
    spike = ctx.spec_dir / "spike"
    journey, mockups = spike / "journey.md", spike / "mockups"
    if not journey.exists() and not mockups.exists():
        return []
    found = partial(error, ctx, journey, "sketch-screens")
    text = read_text(journey)
    if text is None:
        return [
            found(
                "spike/journey.md is missing or unreadable",
                "Write one Mermaid flowchart per user type in spike/journey.md.",
            )
        ]
    screens, edges, bad = parse_journey(text)
    findings = [
        found(
            f"line {n}: {line} is not a flowchart header, a node, an edge, or a %% comment",
            "Write a node as <id>[label] and an edge as <id> -->|action| <id>"
            " or <id> -- action --> <id>.",
        )
        for n, line in bad
    ]
    if not screens:
        findings.append(
            found(
                "spike/journey.md holds no flowchart screen",
                "Add a fenced mermaid flowchart with one node per screen.",
            )
        )
    if INDEX in screens:
        findings.append(
            found(
                "screen ID index is reserved for the navigation file",
                "Rename the screen.",
            )
        )
    files = {p.name for p in mockups.iterdir()} if mockups.is_dir() else set()
    for screen in sorted(screens - {INDEX}):
        if f"{screen}.html" not in files:
            findings.append(
                found(
                    f"screen {screen} has no spike/mockups/{screen}.html",
                    f"Write spike/mockups/{screen}.html.",
                )
            )
    for name in sorted(files - {f"{s}.html" for s in screens} - {f"{INDEX}.html"}):
        findings.append(
            error(
                ctx,
                mockups / name,
                "sketch-screens",
                f"spike/mockups/{name} belongs to no screen of spike/journey.md",
                "Delete it, or add its screen to the journey.",
            )
        )
    for n, source, action, target in edges:
        page = read_text(mockups / f"{source}.html")
        if page is not None and f"{target}.html" not in HREF.findall(page):
            findings.append(
                found(
                    f"line {n}: the action {action!r} from {source} has no link"
                    f" to {target}.html in spike/mockups/{source}.html",
                    f'Link the action in {source}.html with href="{target}.html".',
                )
            )
    return findings


def placed_paths(design: str) -> set[str]:
    """Inline-code paths of the design's placement sections; empty when it has none."""
    return {
        path
        for heading, lines in sections(design).items()
        if PLACEMENT.search(heading)
        for line in lines
        for path in CODE_SPAN.findall(line)
    }


@check("placement-drift", TASKS_ON)
def placement_drift(ctx: Context) -> list[Finding]:
    """Two or more Location paths the design's placement does not name (ART-004.15)."""
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    design, tasks = read_text(paths["design"]), read_text(paths["tasks"])
    placed = placed_paths(design or "")
    if not placed or tasks is None:
        return []
    # ponytail: Location paths count only in inline code; plain-text lists are not parsed.
    named = dict.fromkeys(
        path
        for _, line in prose(tasks)
        if (location := LOCATION.match(line))
        for path in CODE_SPAN.findall(location[1])
    )
    absent = [
        path
        for path in named
        if not any(
            path == p or (p.endswith("/") and path.startswith(p)) for p in placed
        )
    ]
    if len(absent) < 2:
        return []
    return [
        finding(
            rel(ctx, paths["tasks"]),
            "placement-drift",
            f"{len(absent)} Location paths are not in the design's placement: "
            + ", ".join(absent),
            "Add them to the design's ## Module placement, or keep the tasks"
            " to the files it names.",
            "warning",
        )
    ]

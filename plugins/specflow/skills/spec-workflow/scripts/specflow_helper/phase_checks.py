"""The checks of 00006 (T-072, T-034, T-039), registered in CHECKS of checks.py."""

from __future__ import annotations

import re
from functools import partial
from pathlib import Path

from .canonical import FENCE
from .checks import (
    DESIGN_ON,
    SPEC_PHASES,
    TASKS_ON,
    Context,
    check,
    error,
    read_text,
    rel,
)
from .findings import Finding, finding
from .spec_text import CLAUSE, prose, sections
from .state import artifact_paths, task_items

SCREEN = r"[A-Za-z][\w-]*"
# Every Mermaid node shape: one opening bracket, then its closing run ([x], ([x]), [[x]], ((x)), {{x}}, >x]).
LABEL = r"(?:\[[^\]\n]*\]+|\([^)\n]*\)+|\{[^}\n]*\}+|>[^\]\n]*\])"
END = rf"({SCREEN}){LABEL}?"
HEADER = re.compile(r"^(?:flowchart|graph)(?:\s+(?:TB|TD|BT|RL|LR))?$")
NODE = re.compile(rf"^{END}$")
EDGE = re.compile(rf"^{END}\s*(?:-->\s*\|([^|\n]+)\|\s*|--\s+(.+?)\s+-->\s*){END}$")
HREF = re.compile(r"""href\s*=\s*["']?(?:\./)?([^"'#?\s>]+)""", re.IGNORECASE)
INDEX = "index"
Edge = tuple[int, str, str, str]  # line, source, action, target
CODE_SPAN = re.compile(r"`([^`\s]+)`")
LOCATION = re.compile(r"^\s*[-*+]\s+Location:\s*(.*)$")
# The template's ## Module placement, or a native or bugfix design's section that names files.
PLACEMENT = re.compile(r"placement|\bfiles?\b|fix implementation", re.IGNORECASE)
BUG_ANALYSIS = "## Bug Analysis"
BUGFIX_SECTIONS = (
    ("### Current Behavior (Defect)", 1, r"WHEN .+ THEN (?i:the system) "),
    (
        "### Expected Behavior (Correct)",
        2,
        r"WHEN .+ THEN (?i:the system) SHALL (?!CONTINUE TO)",
    ),
    (
        "### Unchanged Behavior (Regression Prevention)",
        3,
        r"WHEN .+ THEN (?i:the system) SHALL CONTINUE TO ",
    ),
)
SHALL = re.compile(r"\bSHALL\b")
BUGFIX_DESIGN = (
    "Hypothesized Root Cause",
    "Correctness Properties",
    "Fix Implementation",
    "Testing Strategy",
)
BUG_CONDITION = re.compile(r"^#+ Bug Condition\b", re.IGNORECASE)
# The fixed top-level tasks by the start of their titles: the first three, then the last.
BUGFIX_TASKS = (
    ("first", "Write bug condition exploration test"),
    ("second", "Write preservation property tests"),
    ("third", "Fix "),
    ("last", "Checkpoint"),
)
TRACE = re.compile(r"_Requirements:([^_]*)_")


def flowchart(block: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """The block's lines when its first non-comment line is a flowchart header; else none."""
    first = next((t for _, t in block if not t.startswith("%%")), "")
    return block if HEADER.match(first) else []


def journey_lines(text: str) -> list[tuple[int, str]]:
    """(line number, stripped line) inside each fenced mermaid flowchart or graph block."""
    lines: list[tuple[int, str]] = []
    block: list[tuple[int, str]] | None = None
    opener = ""
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        fence = FENCE.match(line)
        if block is None:
            # A fence of backticks or tildes whose info string starts with mermaid.
            if fence and line[fence.end() :].split()[:1] == ["mermaid"]:
                block, opener = [], fence[1]
        elif fence and fence[1][0] == opener[0] and len(fence[1]) >= len(opener):
            lines += flowchart(block)
            block = None
        elif line:
            block.append((n, line))
    # An unclosed fence runs to the end of the file, as Markdown renders it.
    return lines + flowchart(block or [])


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
    files = (
        {p.name for p in mockups.iterdir() if p.is_file() and p.suffix == ".html"}
        if mockups.is_dir()
        else set()
    )
    return [
        *journey_findings(found, screens, bad),
        *mockup_findings(ctx, found, mockups, screens, files),
        *link_findings(ctx, found, mockups, screens, files, edges),
    ]


def journey_findings(
    found: partial[Finding], screens: set[str], bad: list[tuple[int, str]]
) -> list[Finding]:
    """A line of no accepted kind, a journey with no screen, and the reserved ID."""
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
    return findings


def mockup_findings(
    ctx: Context,
    found: partial[Finding],
    mockups: Path,
    screens: set[str],
    files: set[str],
) -> list[Finding]:
    """A screen with no mockup file, and a mockup file that belongs to no screen."""
    findings = [
        found(
            f"screen {screen} has no spike/mockups/{screen}.html",
            f"Write spike/mockups/{screen}.html.",
        )
        for screen in sorted(screens - {INDEX})
        if f"{screen}.html" not in files
    ]
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
    return findings


def link_findings(
    ctx: Context,
    found: partial[Finding],
    mockups: Path,
    screens: set[str],
    files: set[str],
    edges: list[Edge],
) -> list[Finding]:
    """A screen's mockup that cannot be read, then each edge its source page does not link."""
    pages = {
        screen: read_text(mockups / f"{screen}.html")
        for screen in sorted(screens - {INDEX})
        if f"{screen}.html" in files
    }
    findings = [
        error(
            ctx,
            mockups / f"{screen}.html",
            "sketch-screens",
            f"spike/mockups/{screen}.html cannot be read as UTF-8",
            "Save it as UTF-8 text.",
        )
        for screen, page in pages.items()
        if page is None
    ]
    for n, source, action, target in edges:
        page = pages.get(source)
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
    """Paths of the design's placement sections, inline code or plain; empty when it has none."""
    return {
        path
        for heading, lines in sections(design).items()
        if PLACEMENT.search(heading)
        for line in lines
        for path in location_paths(line)
    }


def location_paths(value: str) -> list[str]:
    """The paths of a line: each inline-code span, then each plain word that reads as a path."""
    spans = CODE_SPAN.findall(value)
    # ponytail: a plain word is a path when it holds a slash or ends with an extension;
    # a trailing comma, period, or closing parenthesis (an annotation such as "(new)") is not part of it.
    words = (w.rstrip(".,;:)") for w in CODE_SPAN.sub(" ", value).split())
    return spans + [
        w for w in words if not re.search(r"[<>`]", w) and re.search(r"/|\.\w+$", w)
    ]


@check("placement-drift", TASKS_ON)
def placement_drift(ctx: Context) -> list[Finding]:
    """Two or more Location paths the design's placement does not name (ART-004.15)."""
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    design, tasks = read_text(paths["design"]), read_text(paths["tasks"])
    placed = placed_paths(design or "")
    if not placed or tasks is None:
        return []
    named = dict.fromkeys(
        path
        for _, line in prose(tasks)
        if (location := LOCATION.match(line))
        for path in location_paths(location[1])
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


def bugfix_artifact(ctx: Context, name: str) -> tuple[Path, str] | None:
    """(path, text) of a bugfix spec's artifact; None for a feature spec or an unreadable file."""
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    if paths["requirements"].name != "bugfix.md":
        return None
    text = read_text(paths[name])
    return None if text is None else (paths[name], text)


def clause_lines(text: str) -> dict[str, list[str]]:
    """Each level-three heading under ## Bug Analysis -> its clause lines."""
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    in_analysis = False
    for _, line in prose(text):
        if line.startswith("## "):
            in_analysis, current = line.strip() == BUG_ANALYSIS, None
        elif line.startswith("#"):
            under = in_analysis and line.startswith("### ")
            current = found.setdefault(line.strip(), []) if under else None
        elif current is not None and CLAUSE.match(line):
            current.append(line)
    return found


@check("bugfix-sections", SPEC_PHASES)
def bugfix_sections(ctx: Context) -> list[Finding]:
    """bugfix.md keeps Kiro's sections, each behavior section with a clause (ART-005.2)."""
    bugfix = bugfix_artifact(ctx, "requirements")
    if bugfix is None:
        return []
    path, text = bugfix
    found = partial(error, ctx, path, "bugfix-sections")
    headings = {line.strip() for _, line in prose(text)}
    findings = [
        found(
            f"missing section {heading}",
            "Keep Kiro's bugfix.md shape, as the template has it.",
        )
        for heading in ("## Introduction", BUG_ANALYSIS)
        if heading not in headings
    ]
    clauses = clause_lines(text)
    for heading, number, _ in BUGFIX_SECTIONS:
        if heading not in clauses:
            message = f"missing section {heading} under {BUG_ANALYSIS}"
            findings.append(
                found(message, "Add it under ## Bug Analysis, as the template has it.")
            )
        elif not clauses[heading]:
            findings.append(
                found(f"{heading} has no clause", f"Add a clause numbered {number}.1.")
            )
    return findings


@check("bugfix-clauses", SPEC_PHASES)
def bugfix_clause_patterns(ctx: Context) -> list[Finding]:
    """Each clause in its section's pattern and numbering; no SHALL in a defect (ART-005.3)."""
    bugfix = bugfix_artifact(ctx, "requirements")
    if bugfix is None:
        return []
    path, text = bugfix
    found = partial(error, ctx, path, "bugfix-clauses")
    clauses = clause_lines(text)
    findings = []
    for heading, number, pattern in BUGFIX_SECTIONS:
        for index, clause in enumerate(clauses.get(heading, []), start=1):
            if not clause.startswith(f"{number}.{index} "):
                message = f"clause out of sequence: {clause}"
                fix = (
                    f"Number this section's clauses {number}.1, {number}.2, and on,"
                    " or move the clause to the section its number names."
                )
            elif number == 1 and SHALL.search(clause):
                message = f"a Current Behavior clause uses SHALL: {clause}"
                fix = (
                    "Describe the defect as it happens: WHEN <condition> THEN the"
                    " system <incorrect behavior>."
                )
            elif not re.match(rf"^{number}\.{index} {pattern}", clause):
                message = f"clause does not follow the pattern: {clause}"
                fix = (
                    "Use WHEN <condition> THEN the system ..., as the section requires."
                )
            else:
                continue
            findings.append(found(message, fix))
    return findings


@check("bugfix-design-sections", DESIGN_ON)
def bugfix_design_sections(ctx: Context) -> list[Finding]:
    """The bugfix design's required sections, and a Bug Condition here or in bugfix.md (ART-005.4)."""
    design = bugfix_artifact(ctx, "design")
    if design is None:
        return []
    path, text = design
    found = partial(error, ctx, path, "bugfix-design-sections")
    held = {name.lower() for name in sections(text)}
    findings = [
        found(
            f"missing section ## {name}",
            "Keep the bugfix design's shape (templates/bugfix/design.md).",
        )
        for name in BUGFIX_DESIGN
        if name.lower() not in held
    ]
    bugfix = bugfix_artifact(ctx, "requirements")
    texts = (text, bugfix[1] if bugfix else "")
    if not any(BUG_CONDITION.match(line) for t in texts for _, line in prose(t)):
        message = "no Bug Condition heading in design.md or bugfix.md"
        findings.append(found(message, "Add ### Bug Condition under ## Bug Details."))
    return findings


@check("bugfix-task-order", TASKS_ON)
def bugfix_task_order(ctx: Context) -> list[Finding]:
    """Kiro's fixed top-level tasks, in order (ART-005.5)."""
    tasks = bugfix_artifact(ctx, "tasks")
    if tasks is None:
        return []
    path, text = tasks
    found = partial(error, ctx, path, "bugfix-task-order")
    top = [item for item in task_items(text) if item["parent"] is None]
    fix = (
        "Keep the four tasks of templates/bugfix/tasks.md in their order:"
        " exploration test, preservation tests, fix, checkpoint."
    )
    if len(top) < len(BUGFIX_TASKS):
        return [found(f"{len(top)} top-level tasks; a bugfix plan has four", fix)]
    # ponytail: tasks Kiro adds between the fix and the checkpoint are allowed, as in the T-027 capture.
    findings = []
    for item, (place, start) in zip((*top[:3], top[-1]), BUGFIX_TASKS):
        if not item["title"].startswith(start):
            label = f"{item['id']}. {item['title']}" if item["id"] else item["title"]
            message = f"the {place} top-level task is not {start.strip()!r}...: {label}"
            findings.append(found(message, fix))
    return findings


@check("bugfix-clause-trace", TASKS_ON)
def bugfix_clause_trace(ctx: Context) -> list[Finding]:
    """Every 2.x and 3.x clause traced by task 1, task 2, or a subtask of task 3 (ART-005.7)."""
    tasks, bugfix = bugfix_artifact(ctx, "tasks"), bugfix_artifact(ctx, "requirements")
    if tasks is None or bugfix is None:
        return []
    path, text = tasks
    items = task_items(text)
    top = [item for item in items if item["parent"] is None][:3]
    owners = [
        item
        for item in items
        if item in top[:2] or (len(top) == 3 and item["parent"] == top[2]["index"])
    ]
    lines = dict(prose(text))
    traced: set[str] = set()
    for item in owners:
        end = (
            items[item["index"] + 1]["line"]
            if item["index"] + 1 < len(items)
            else max(lines) + 1
        )
        for n in range(item["line"], end):
            for value in TRACE.findall(lines.get(n, "")):
                traced |= set(re.findall(r"[0-9]+\.[0-9]+", value))
    clauses = clause_lines(bugfix[1])
    needed = [
        clause.split()[0]
        for heading, _, _ in BUGFIX_SECTIONS[1:]
        for clause in clauses.get(heading, [])
    ]
    return [
        error(
            ctx,
            path,
            "bugfix-clause-trace",
            f"clause {ident} is traced by no _Requirements: line of task 1, task 2, or a subtask of task 3",
            f"Add {ident} to the _Requirements: line of the task that tests it.",
        )
        for ident in needed
        if ident not in traced
    ]

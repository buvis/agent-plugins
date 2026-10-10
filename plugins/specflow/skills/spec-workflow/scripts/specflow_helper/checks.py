"""Named validation checks. Each returns findings that carry the file, the rule, and the fix."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import NamedTuple

from .canonical import CHECKBOX, PROGRESS, canonical, scan_lines
from .config import load_config
from .numbers import NUMBER, number_clashes
from .deps import (
    dependency_blockers,
    parse_depends_on,
    requirements_file,
    resolve_reference,
)
from .schema import check_content
from .state import (
    ORDERS,
    PHASES,
    STATE_FILE,
    StateError,
    artifact_paths,
    artifact_status,
    load_state,
    spec_phase,
    spec_type,
    task_items,
    workflow_order,
)

Finding = dict[str, str]


class Context(NamedTuple):
    repo: Path
    config: dict[str, object]
    spec_dir: Path  # or the intake item, for phase "intake"
    state: dict | None


CHECKS: dict[str, tuple[frozenset[str], Callable[[Context], list[Finding]]]] = {}

SPEC_PHASES = frozenset(PHASES[1:])
DESIGN_ON = frozenset(PHASES[2:])
TASKS_ON = frozenset(PHASES[3:])
UNFILTERED = "any run with no phase"
KIRO_SPECS = PurePosixPath(".kiro/specs")
REQUIREMENT_HEADING = re.compile(r"^### (?:([A-Z][A-Z0-9]*-\d{3})|Requirement (\d+))\b")
CRITERION = re.compile(r"^(\d+)\. ")
ID_ENTRY = re.compile(r"^(?:[A-Z][A-Z0-9]*-\d{3}(?:\.\d+)?|\d+\.\d+)$")
CROSS_SPEC = re.compile(
    r"(\d{5}|folder:[^\s,;]+) ([A-Z][A-Z0-9]*-\d{3})"
    r"(?: (?:criterion|criteria) (\d+(?:, ?\d+)*))?",
)
BAD_CHECKBOX = re.compile(r"^[ \t]*(?:[-*+]|\d+\.)[ \t]*\[[^\]]{0,3}\]")
CLAUSE = re.compile(r"^(\d+)\.(\d+) ")
DESIGN_SECTIONS = (
    "Overview",
    "Context and constraints",
    "Architecture",
    "Module placement",
    "Components and interfaces",
    "Data model",
    "Data and control flow",
    "Error handling",
    "Security and privacy",
    "Testing strategy",
    "Rollout and migration",
    "Risks and edge cases",
    "Requirement traceability",
    "Alternatives considered",
    "Reuse inventory",
    "Open decisions",
)
BUGFIX_SECTIONS = (
    ("### Current Behavior (Defect)", 1, r"WHEN .+ THEN (?i:the system) "),
    ("### Expected Behavior (Correct)", 2, r"WHEN .+ THEN (?i:the system) SHALL "),
    (
        "### Unchanged Behavior (Regression Prevention)",
        3,
        r"WHEN .+ THEN (?i:the system) SHALL CONTINUE TO ",
    ),
)


def check(name: str, phases: frozenset[str]) -> Callable:
    """Register a check under its name, the <check-name> of the rule inventory."""

    def register(
        function: Callable[[Context], list[Finding]],
    ) -> Callable[[Context], list[Finding]]:
        CHECKS[name] = (phases, function)
        return function

    return register


class GitError(Exception):
    """A git call failed for a reason other than "not ignored"."""


def workspace_config(repo: Path) -> dict[str, object]:
    """The workspace config from .agents/specflow.json, or the defaults."""
    return load_config(repo)


def git_ignored(repo: Path, path: str) -> bool:
    """Whether git ignores the path; False without git."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "-q", path],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    if result.returncode not in (0, 1):
        raise GitError(f"git check-ignore failed: {result.stderr.strip()}")
    return result.returncode == 0


def specs_folder(ctx: Context) -> Path:
    return ctx.repo / str(ctx.config["specsDir"])


def rel(ctx: Context, path: Path) -> str:
    try:
        return path.resolve().relative_to(ctx.repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def error(ctx: Context, path: Path, rule: str, message: str, fix: str) -> Finding:
    return {
        "level": "error",
        "file": rel(ctx, path),
        "rule": rule,
        "message": message,
        "fix": fix,
    }


def read_text(path: Path) -> str | None:
    """The file's text, or None when it is absent or unreadable (required-files reports that)."""
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


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
    """Requirement ID -> its numbered criteria ("1" stands for Kiro's Requirement 1)."""
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
        if match:
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


def is_intake(ctx: Context) -> bool:
    intake = (ctx.repo / str(ctx.config["root"]) / "intake").resolve()
    return ctx.spec_dir.resolve().is_relative_to(intake)


@check("required-files", SPEC_PHASES | {"intake"})
def required_files(ctx: Context) -> list[Finding]:
    if is_intake(ctx):
        idea = ctx.spec_dir / "idea.md"
        if read_text(idea) is None:
            fix = "Save the first input verbatim as idea.md."
            return [
                error(
                    ctx,
                    idea,
                    "required-files",
                    "idea.md is missing or unreadable",
                    fix,
                ),
            ]
        return []
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    findings = [
        error(
            ctx,
            path,
            "required-files",
            f"{path.name} cannot be read as UTF-8 text",
            "Restore the file or save it as UTF-8.",
        )
        for path in paths.values()
        if path.exists() and read_text(path) is None
    ]
    if findings:
        return findings
    _, phase = spec_phase(ctx.spec_dir, ctx.state)
    order = (*ORDERS[workflow_order(ctx.spec_dir, ctx.state)], "tasks")
    needed = list(order[: order.index(phase)] if phase in order else order)
    records = (ctx.state or {}).get("artifacts", {})
    needed += [
        name
        for name in order
        if name not in needed
        and records.get(name, {}).get("status") in ("approved", "stale")
    ]
    return [
        error(
            ctx,
            paths[name],
            "required-files",
            f"{paths[name].name} is missing in phase {phase}",
            f"Write {paths[name].name} before this phase.",
        )
        for name in needed
        if not paths[name].exists()
    ]


@check("state-valid", SPEC_PHASES)
def state_valid(ctx: Context) -> list[Finding]:
    try:
        load_state(ctx.spec_dir)
    except StateError as problem:
        message = str(problem).split(": ", 1)[-1]
        fix = (
            "Fix the file by hand, or move it aside and recover; it is never replaced."
        )
        return [error(ctx, ctx.spec_dir / STATE_FILE, "state-valid", message, fix)]
    return []


@check("state-content", SPEC_PHASES)
def state_content(ctx: Context) -> list[Finding]:
    path = ctx.spec_dir / STATE_FILE
    try:
        state = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(state, dict):
        return []
    fix = "Remove it: state holds hashes and approval facts only."
    return [
        error(ctx, path, "state-content", problem, fix)
        for problem in check_content(state)
    ]


@check("spec-type", SPEC_PHASES)
def spec_type_check(ctx: Context) -> list[Finding]:
    _, disagree = spec_type(ctx.spec_dir, ctx.state)
    if not disagree:
        return []
    message = "spec type sources disagree: " + "; ".join(disagree)
    fix = "Decide the type and correct .config.kiro or .specflow.json by hand."
    return [error(ctx, ctx.spec_dir, "spec-type", message, fix)]


@check("requirement-ids", SPEC_PHASES)
def requirement_ids_check(ctx: Context) -> list[Finding]:
    path = artifact_paths(ctx.spec_dir, ctx.state)["requirements"]
    text = read_text(path)
    if text is None:
        return []
    if path.name == "bugfix.md":
        return bugfix_findings(ctx, path, text)

    def found(message: str, fix: str) -> Finding:
        return error(ctx, path, "requirement-ids", message, fix)

    findings = []
    seen: set[str] = set()
    for _, line in prose(text):
        match = REQUIREMENT_HEADING.match(line)
        if match:
            ident = match[1] or match[2]
            if ident in seen:
                findings.append(
                    found(
                        f"requirement ID {ident} is used twice",
                        "Give it a new, unused ID.",
                    ),
                )
            seen.add(ident)
    findings += [
        found(
            f"heading without a stable ID: {line}",
            "Start the heading with an ID like REQ-001.",
        )
        for line in sections(text).get("Requirements", [])
        if line.startswith("### ") and not REQUIREMENT_HEADING.match(line)
    ]
    findings += [
        found(
            f"{ident} has no numbered acceptance criterion",
            "Add a numbered criterion.",
        )
        for ident, criteria in requirement_ids(text).items()
        if not criteria
    ]
    if not seen:
        findings.append(
            found(
                "no requirement with a stable ID",
                "Add requirements under ## Requirements.",
            ),
        )
    return findings


def bugfix_findings(ctx: Context, path: Path, text: str) -> list[Finding]:
    lines = [line for _, line in prose(text)]
    findings = []
    for heading, number, pattern in BUGFIX_SECTIONS:
        if heading not in lines:
            fix = "Keep Kiro's three behavior sections."
            findings.append(
                error(ctx, path, "requirement-ids", f"missing section {heading}", fix),
            )
            continue
        start = lines.index(heading) + 1
        end = next(
            (i for i in range(start, len(lines)) if lines[i].startswith("#")),
            len(lines),
        )
        clauses = [line for line in lines[start:end] if CLAUSE.match(line)]
        if not clauses:
            fix = f"Add a clause numbered {number}.1."
            findings.append(
                error(ctx, path, "requirement-ids", f"{heading} has no clause", fix),
            )
        for index, clause in enumerate(clauses, start=1):
            if not clause.startswith(f"{number}.{index} "):
                message = f"clause out of sequence: {clause}"
                fix = f"Number this section's clauses {number}.1, {number}.2, and on."
                findings.append(error(ctx, path, "requirement-ids", message, fix))
            elif not re.match(rf"^{number}\.{index} {pattern}", clause):
                message = f"clause does not follow the pattern: {clause}"
                fix = (
                    "Use WHEN <condition> THEN the system ..., as the section requires."
                )
                findings.append(error(ctx, path, "requirement-ids", message, fix))
    return findings


@check("design-sections", DESIGN_ON)
def design_sections(ctx: Context) -> list[Finding]:
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    path = paths["design"]
    text = read_text(path)
    if text is None:
        return []

    def found(message: str, fix: str) -> Finding:
        return error(ctx, path, "design-sections", message, fix)

    parts = sections(text)
    findings = []
    if canonical(text).startswith("# Design: "):
        for name in DESIGN_SECTIONS:
            body = [line.strip() for line in parts.get(name, []) if line.strip()]
            if name not in parts:
                fix = "Keep every section; mark one that does not apply Not applicable: <reason>."
                findings.append(found(f"missing section ## {name}", fix))
            elif not body:
                findings.append(
                    found(
                        f"## {name} is empty",
                        "Write it, or Not applicable: <reason>.",
                    ),
                )
            elif (
                body[0].startswith("Not applicable:")
                and not body[0].split(":", 1)[1].strip()
            ):
                findings.append(
                    found(f"## {name} gives no reason", "Write the reason."),
                )
    requirements = read_text(paths["requirements"])
    if "Requirement traceability" in parts and requirements is not None:
        source = paths["requirements"].name
        known = known_ids(requirements, source == "bugfix.md")
        for entry in traceability_entries(parts["Requirement traceability"]):
            if ID_ENTRY.match(entry) and entry not in known:
                fix = (
                    "Cite an ID this spec's requirements hold, or the cross-spec form."
                )
                findings.append(
                    found(f"traceability cites {entry}, which {source} lacks", fix),
                )
    return findings


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


@check("task-structure", TASKS_ON)
def task_structure(ctx: Context) -> list[Finding]:
    path = artifact_paths(ctx.spec_dir, ctx.state)["tasks"]
    text = read_text(path)
    if text is None:
        return []

    def found(message: str, fix: str) -> Finding:
        return error(ctx, path, "task-structure", message, fix)

    findings = [
        found(
            f"line {n}: malformed checkbox: {line.strip()}",
            "Write [ ] or [x] after the marker.",
        )
        for n, (line, in_fence, _) in enumerate(scan_lines(canonical(text)), start=1)
        if not in_fence and BAD_CHECKBOX.match(line) and not CHECKBOX.match(line)
    ]
    seen: list[str] = []
    for item in task_items(text):
        where = f"line {item['line']}"
        if item["id"] is None:
            if item["parent"] is None:
                findings.append(
                    found(f"{where}: task without a stable ID", "Start it with T-001."),
                )
            continue
        if item["id"] in seen:
            findings.append(
                found(f"{where}: task ID {item['id']} is used twice", "Use a new ID."),
            )
        for dependency in item["depends"] or []:
            if dependency not in seen:
                message = f"{where}: {item['id']} depends on {dependency}, not an earlier task"
                findings.append(
                    found(message, "Depend only on task IDs that appear above."),
                )
        if item["id"].startswith("T-") and item["parent"] is None:
            for field in ("Requirements", "Verify"):
                if field not in item["fields"]:
                    message = f"{where}: {item['id']} has no {field}: line"
                    findings.append(
                        found(message, f"Add a {field}: field to the task."),
                    )
        seen.append(item["id"])
    return findings


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
            if re.fullmatch(r"[A-Z][A-Z0-9]*-\d{3}", token):
                traced.add(token)
            elif re.fullmatch(r"\d+(?:\.\d+)?", token):
                traced.add(token.split(".")[0])
    return traced


@check("requirement-coverage", TASKS_ON)
def requirement_coverage(ctx: Context) -> list[Finding]:
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    if paths["requirements"].name == "bugfix.md":
        return []
    requirements, tasks = read_text(paths["requirements"]), read_text(paths["tasks"])
    if requirements is None or tasks is None:
        return []
    traced = traced_ids(tasks)
    fix = "Reference the requirement on a task's Requirements: line."
    return [
        error(
            ctx,
            paths["tasks"],
            "requirement-coverage",
            f"no task references {ident}",
            fix,
        )
        for ident in requirement_ids(requirements)
        if ident not in traced
    ]


@check("progress-fields", TASKS_ON)
def progress_fields(ctx: Context) -> list[Finding]:
    path = artifact_paths(ctx.spec_dir, ctx.state)["tasks"]
    text = read_text(path)
    if text is None or artifact_status(ctx.spec_dir, ctx.state)["tasks"] == "approved":
        return []
    fix = "Record Outcome: and Exception: only after the task plan is approved."
    return [
        {
            "level": "warning",
            "file": rel(ctx, path),
            "rule": "progress-fields",
            "message": f"line {n}: {line.strip()} in a plan that is not approved",
            "fix": fix,
        }
        for n, (line, in_fence, in_task) in enumerate(
            scan_lines(canonical(text)),
            start=1,
        )
        if not in_fence and in_task and PROGRESS.match(line)
    ]


@check("cross-spec-references", TASKS_ON)
def cross_spec_references(ctx: Context) -> list[Finding]:
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    tasks = read_text(paths["tasks"])
    requirements = read_text(paths["requirements"])
    if tasks is None:
        return []
    declared: list[str] = []
    if requirements is not None:
        bugfix = paths["requirements"].name == "bugfix.md"
        declared, _ = parse_depends_on(requirements, bugfix=bugfix)
    findings = []
    for number, line in prose(tasks):
        stripped = line.strip().lstrip("-*+ ")
        if stripped.startswith(("Requirements:", "Acceptance criteria:")):
            for match in CROSS_SPEC.finditer(stripped):
                findings += cross_spec_finding(
                    ctx,
                    paths["tasks"],
                    number,
                    match,
                    declared,
                )
    return findings


def cross_spec_finding(
    ctx: Context,
    path: Path,
    number: int,
    match: re.Match,
    declared: list[str],
) -> list[Finding]:
    ref, ident, criteria = match[1], match[2], match[3]
    where = f"line {number}: {match[0]}"

    def found(message: str, fix: str) -> Finding:
        return error(ctx, path, "cross-spec-references", message, fix)

    if ref not in declared:
        fix = "Add the spec to Depends on:, or cite this spec's own requirement."
        return [
            found(f"{where} names {ref}, which is not on the Depends on: line", fix),
        ]
    target, reason = resolve_reference(ref, specs_folder(ctx))
    text = read_text(requirements_file(target)) if target else None
    if target is None or text is None:
        fix = "Fix the reference so it names one readable spec."
        return [found(f"{where}: {reason or 'requirements unreadable'}", fix)]
    held = requirement_ids(text)
    if ident not in held:
        return [
            found(
                f"{where}: {target.name} holds no {ident}",
                "Cite a requirement it holds.",
            ),
        ]
    return [
        found(
            f"{where}: {target.name} {ident} holds no criterion {n}",
            "Cite a criterion it holds.",
        )
        for n in re.findall(r"\d+", criteria or "")
        if int(n) not in held[ident]
    ]


@check("gates", frozenset({"implementation"}))
def gates(ctx: Context) -> list[Finding]:
    statuses = artifact_status(ctx.spec_dir, ctx.state)
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    findings = [
        error(
            ctx,
            paths[name],
            "gates",
            f"{paths[name].name} is {status}; implementation needs every artifact approved",
            f"Review {paths[name].name} and record its approval.",
        )
        for name, status in statuses.items()
        if status != "approved"
    ]
    fix = "Complete or fix the prerequisite before implementation."
    findings += [
        error(
            ctx,
            ctx.spec_dir,
            "gates",
            f"dependency {b['reference']}: {b['reason']}",
            fix,
        )
        for b in dependency_blockers(ctx.spec_dir, specs_folder(ctx))
    ]
    return findings


@check("spec-dependencies", frozenset({"implementation", UNFILTERED}))
def spec_dependencies(ctx: Context) -> list[Finding]:
    findings = []
    fix = "Correct the Depends on: line so each reference names one spec and no cycle remains."
    for b in dependency_blockers(ctx.spec_dir, specs_folder(ctx)):
        if b["reason"].startswith("incomplete prerequisite"):
            continue
        folder = (
            ctx.spec_dir
            if b["spec"] == ctx.spec_dir.name
            else specs_folder(ctx) / b["spec"]
        )
        cycle = f" ({b['path']})" if "path" in b else ""
        message = f"{b['spec']} {b['reference']}: {b['reason']}{cycle}"
        findings.append(
            error(ctx, requirements_file(folder), "spec-dependencies", message, fix),
        )
    return findings


@check("specs-folder", SPEC_PHASES)
def specs_folder_check(ctx: Context) -> list[Finding]:
    """Specs left in a real .kiro/specs/ beside a configured folder; an ignored specs folder."""
    findings = []
    configured = str(ctx.config["specsDir"])
    kiro = ctx.repo / KIRO_SPECS
    if (
        PurePosixPath(configured) != KIRO_SPECS
        and kiro.is_dir()
        and not kiro.is_symlink()
    ):
        left = sorted(p.name for p in kiro.iterdir() if p.is_dir())
        if left:
            message = (
                f"specs left in a real .kiro/specs/ while specsDir is {configured}: "
            )
            fix = f"Move them into {configured}, then make .kiro/specs a link to it."
            findings.append(
                error(ctx, kiro, "specs-folder", message + ", ".join(left), fix)
            )
    if (ctx.repo / ".git").exists() and git_ignored(
        ctx.repo, f"{configured}/.specflow-probe"
    ):
        message = f"git ignores the specs folder {configured}, so its specs are never committed"
        fix = "Remove the ignore rule that matches it, or configure another specsDir."
        findings.append(error(ctx, ctx.repo / configured, "specs-folder", message, fix))
    return findings


@check("number-clashes", SPEC_PHASES | {"intake"})
def number_clashes_check(ctx: Context) -> list[Finding]:
    return number_clashes(ctx.repo, ctx.config)


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


@check("sources-line", SPEC_PHASES)
def sources_line(ctx: Context) -> list[Finding]:
    """A numbered spec's Sources: line names an intake item with the spec's own number."""
    number = NUMBER.match(ctx.spec_dir.name)
    path = artifact_paths(ctx.spec_dir, ctx.state)["requirements"]
    text = read_text(path)
    if number is None or text is None:
        return []
    value = sources_value(text, bugfix=path.name == "bugfix.md")
    if value is None:
        where = (
            "at the end of ## Introduction"
            if path.name == "bugfix.md"
            else "in the header"
        )
        fix = f"Add a Sources: line {where} that names the intake item."
        return [error(ctx, path, "sources-line", "no Sources: line", fix)]
    item = value.split(",")[0].strip().strip("`").rstrip("/").rsplit("/", 1)[-1]
    cited = NUMBER.match(item)
    if cited is None:
        fix = "Name the intake item's processed/ path first on the line."
        return [
            error(
                ctx,
                path,
                "sources-line",
                f"Sources: names no intake item: {value}",
                fix,
            )
        ]
    if cited[1] != number[1]:
        message = f"Sources: names intake item {item}, not one numbered {number[1]}"
        fix = "Name this spec's own intake item, or renumber the newer of the two."
        return [error(ctx, path, "sources-line", message, fix)]
    return []


def selected(phases: frozenset[str], phase: str | None) -> bool:
    """With a phase, the checks for it; with none, every check that is not gate-only."""
    if phase is not None:
        return phase in phases
    return UNFILTERED in phases or bool(phases & (SPEC_PHASES - {"implementation"}))


def validate(repo: Path, spec_dir: Path, phase: str | None = None) -> list[Finding]:
    """Every finding of the checks that apply to the phase; writes nothing."""
    try:
        state = load_state(spec_dir)
    except StateError:
        state = None
    ctx = Context(repo, workspace_config(repo), spec_dir, state)
    findings: list[Finding] = []
    for phases, function in CHECKS.values():
        if selected(phases, phase):
            findings += function(ctx)
    return findings

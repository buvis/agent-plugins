"""Named validation checks. Each returns findings that carry the file, the rule, and the fix."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from functools import partial
from pathlib import Path, PurePosixPath
from typing import NamedTuple

from .canonical import (
    CHECKBOX,
    PROGRESS,
    TASKS_HEADING,
    canonical,
    indent_of,
    scan_lines,
)
from .config import load_config
from .deps import (
    dependency_blockers,
    parse_depends_on,
    requirements_file,
    resolve_reference,
)
from .drift import drift_warnings
from .findings import Finding, finding
from .numbers import NUMBER, number_clashes
from .schema import check_content
from .spec_text import (
    CROSS_SPEC,
    REQUIREMENT_HEADING,
    known_ids,
    prose,
    requirement_ids,
    sections,
    sources_value,
    traceability_entries,
    traced_ids,
    unheld_citations,
)
from .state import (
    ORDERS,
    PHASES,
    STATE_FILE,
    StateError,
    artifact_paths,
    artifact_status,
    load_state,
    own_statuses,
    spec_phase,
    spec_type,
    stale_causes,
    task_items,
    workflow_order,
)


class Context(NamedTuple):
    repo: Path
    config: dict[str, object]
    spec_dir: Path  # or the intake item, for phase "intake"
    state: dict | None
    phase: str | None = None  # the requested phase; None for an unfiltered run


CHECKS: dict[str, tuple[frozenset[str], Callable[[Context], list[Finding]]]] = {}

SPEC_PHASES = frozenset(PHASES[1:])
DESIGN_ON = frozenset(PHASES[2:])
TASKS_ON = frozenset(PHASES[3:])
UNFILTERED = "any run with no phase"
KIRO_SPECS = PurePosixPath(".kiro/specs")
ID_ENTRY = re.compile(r"^(?:[A-Z][A-Z0-9]*-[0-9]{3}(?:\.[0-9]+)?|[0-9]+\.[0-9]+)$")
BAD_CHECKBOX = re.compile(r"^[ \t]*(?:[-*+]|[0-9]+\.)[ \t]*\[[^\]]{0,3}\]")
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
# Template sections other designs hold too: Kiro writes all but the last (in
# Title Case, which a hand edit may lower), and any design may record open
# decisions (a marker section).
SHARED_SECTIONS = (
    "Overview",
    "Architecture",
    "Components and interfaces",
    "Error handling",
    "Testing strategy",
    "Open decisions",
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
            ["git", "-C", str(repo), "check-ignore", "-q", "--", path],
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
    return finding(rel(ctx, path), rule, message, fix)


def read_text(path: Path) -> str | None:
    """The file's text, or None when it is absent or unreadable (required-files reports that)."""
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def is_intake(ctx: Context) -> bool:
    intake = (ctx.repo / str(ctx.config["root"]) / "intake").resolve()
    return ctx.spec_dir.resolve().is_relative_to(intake)


@check("required-files", SPEC_PHASES | {"intake"})
def required_files(ctx: Context) -> list[Finding]:
    if is_intake(ctx):
        idea = ctx.spec_dir / "idea.md"
        if read_text(idea) is None:
            fix = "Save the first input verbatim as idea.md."
            message = "idea.md is missing or unreadable"
            return [error(ctx, idea, "required-files", message, fix)]
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
    phase = ctx.phase
    if phase not in SPEC_PHASES:
        phase = spec_phase(ctx.spec_dir, ctx.state)[1]
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
        message = problem.reason
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


@check("stale-approvals", SPEC_PHASES)
def stale_approvals(ctx: Context) -> list[Finding]:
    """Each approval whose artifact or upstream changed, with the cause (WF-005.1, WF-005.4)."""
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    records = (ctx.state or {}).get("artifacts", {})
    own = own_statuses(ctx.spec_dir, ctx.state)
    findings = []
    for name, cause in stale_causes(ctx.spec_dir, ctx.state).items():
        file = paths[name].name
        if cause != name:
            why = f"upstream {paths[cause].name} changed since its approval"
        elif records.get(name, {}).get("status") == "stale":
            why = "it is recorded stale"
        elif records.get(name, {}).get("status") == "missing":
            why = "the file was deleted after its approval"
        elif own[name] == "approved":
            # Its own text and record are fine, so only the binding can be missing.
            why = "it binds no upstream artifact"
        else:
            why = "its content changed since the approval"
        message = f"the {file} approval is stale: {why}"
        fix = f"Review {file} with the developer and record its approval again."
        findings.append(error(ctx, paths[name], "stale-approvals", message, fix))
    return findings


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
    if path.name == "bugfix.md":  # bugfix-sections and bugfix-clauses (phase_checks.py)
        return []
    found = partial(error, ctx, path, "requirement-ids")
    findings = []
    seen: set[str] = set()
    for _, line in prose(text):
        match = REQUIREMENT_HEADING.match(line)
        if match:
            ident = match[1] or match[2]
            if ident in seen:
                message = f"requirement ID {ident} is used twice"
                findings.append(found(message, "Give it a new, unused ID."))
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
        fix = "Add requirements under ## Requirements."
        findings.append(found("no requirement with a stable ID", fix))
    return findings


@check("design-sections", DESIGN_ON)
def design_sections(ctx: Context) -> list[Finding]:
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    path = paths["design"]
    text = read_text(path)
    if text is None:
        return []
    found = partial(error, ctx, path, "design-sections")
    parts = sections(text)
    findings = []
    # From the template: its title, or a section only the template has, so a
    # retitled template design keeps every section (ART-001.10).
    templated = canonical(text).startswith("# Design: ") or any(
        name in parts for name in DESIGN_SECTIONS if name not in SHARED_SECTIONS
    )
    if templated:
        for name in DESIGN_SECTIONS:
            body = [line.strip() for line in parts.get(name, []) if line.strip()]
            if name not in parts:
                fix = "Keep every section; mark one that does not apply Not applicable: <reason>."
                findings.append(found(f"missing section ## {name}", fix))
            elif not body:
                fix = "Write it, or Not applicable: <reason>."
                findings.append(found(f"## {name} is empty", fix))
            elif (
                body[0].startswith("Not applicable:")
                and not body[0].split(":", 1)[1].strip()
            ):
                findings.append(
                    found(f"## {name} gives no reason", "Write the reason.")
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


def malformed_boxes(text: str) -> list[tuple[int, str]]:
    """Task-list items whose box is not [ ], [x], [~] or [-].

    Tasks sit above the first level-two heading (the template) or under
    `## Tasks` (Kiro), so `- [Q1] note` under `## Notes` or `## Unresolved
    questions` is not a box. Fenced lines are skipped.
    """
    bad = []
    in_tasks = True
    for n, (line, in_fence, _) in enumerate(scan_lines(canonical(text)), start=1):
        if in_fence:
            continue
        if line.startswith("## "):
            in_tasks = line.rstrip() == TASKS_HEADING
        elif in_tasks and BAD_CHECKBOX.match(line) and not CHECKBOX.match(line):
            bad.append((n, line.strip()))
    return bad


@check("task-structure", TASKS_ON)
def task_structure(ctx: Context) -> list[Finding]:
    path = artifact_paths(ctx.spec_dir, ctx.state)["tasks"]
    text = read_text(path)
    if text is None:
        return []
    found = partial(error, ctx, path, "task-structure")
    findings = [
        found(
            f"line {n}: malformed checkbox: {line}",
            "Write [ ] or [x] after the marker.",
        )
        for n, line in malformed_boxes(text)
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
    found = partial(error, ctx, paths["tasks"], "requirement-coverage")
    held = requirement_ids(requirements)
    missing = [
        found(f"no task references {ident}", fix)
        for ident in held
        if ident not in traced
    ]
    fix = "Cite a requirement and criterion this spec holds, or fix the typo."
    return missing + [
        found(
            f"line {n}: cites {cite}, which {paths['requirements'].name} does not hold",
            fix,
        )
        for n, cite in unheld_citations(tasks, held)
    ]


@check("progress-fields", TASKS_ON)
def progress_fields(ctx: Context) -> list[Finding]:
    """Outcome:/Exception: before approval, and any line continuing one (it is hashed)."""
    path = artifact_paths(ctx.spec_dir, ctx.state)["tasks"]
    text = read_text(path)
    if text is None:
        return []
    approved = artifact_status(ctx.spec_dir, ctx.state)["tasks"] == "approved"
    warn = partial(finding, rel(ctx, path), "progress-fields", level="warning")
    findings = []
    field: int | None = None  # indent of the open progress field
    for n, (line, in_fence, in_task) in enumerate(
        scan_lines(canonical(text)),
        start=1,
    ):
        if not line.strip():
            continue
        # A progress field at any depth is itself left out of the hash, so test it first.
        if not in_fence and in_task and PROGRESS.match(line):
            field = indent_of(line)
            if not approved:
                message = f"line {n}: {line.strip()} in a plan that is not approved"
                fix = "Record Outcome: and Exception: only after the task plan is approved."
                findings.append(warn(message, fix))
            continue
        if field is not None and indent_of(line) > field:
            message = (
                f"line {n}: continues an Outcome: or Exception: line, so it is hashed"
            )
            fix = "Keep the field on one line; only that line is left out of the hash."
            findings.append(warn(message, fix))
        field = None
    return findings


@check("cross-spec-references", TASKS_ON)
def cross_spec_references(ctx: Context) -> list[Finding]:
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    tasks = read_text(paths["tasks"])
    requirements = read_text(paths["requirements"])
    if tasks is None:
        return []
    refs: list[str] = []
    if requirements is not None:
        bugfix = paths["requirements"].name == "bugfix.md"
        refs, _ = parse_depends_on(requirements, bugfix=bugfix)
    declared = {*refs, *(spec_key(ctx, ref) for ref in refs)} - {None}
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


def spec_key(ctx: Context, ref: str) -> str | None:
    """The folder a reference resolves to, as `folder:<name>`, so both forms compare equal."""
    target, _ = resolve_reference(ref, specs_folder(ctx))
    return f"folder:{target.name}" if target else None


def cross_spec_finding(
    ctx: Context,
    path: Path,
    number: int,
    match: re.Match,
    declared: set[str],
) -> list[Finding]:
    ref, ident, criteria = match[1], match[2], match[3]
    where = f"line {number}: {match[0]}"
    found = partial(error, ctx, path, "cross-spec-references")
    if ref not in declared and spec_key(ctx, ref) not in declared:
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
        for n in re.findall(r"[0-9]+", criteria or "")
        if int(n) not in held[ident]
    ]


@check("gates", frozenset({"implementation"}))
def gates(ctx: Context) -> list[Finding]:
    from .status import gate_blockers  # status imports this module

    statuses = artifact_status(ctx.spec_dir, ctx.state)
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    fix = (
        "Approve the artifact, accept the marker on the dependent approval, "
        "or complete the prerequisite."
    )
    # One finding per blocker; an artifact blocker repeats for each later gate.
    messages = dict.fromkeys(
        f"{b['reason']}: {b['reference']}"
        for b in gate_blockers(ctx.spec_dir, specs_folder(ctx), ctx.state)
    )
    findings = [error(ctx, ctx.spec_dir, "gates", m, fix) for m in messages]
    # WF-004.8: the same drift warnings status shows, before implementation.
    findings += [
        finding(
            rel(ctx, ctx.repo / w["path"])
            if "path" in w
            else rel(ctx, paths["design"]),
            "gates",
            f"{w['kind']}: {w['message']}",
            "Review the change against the design; re-approve the design if it holds.",
            "warning",
        )
        for w in drift_warnings(ctx.repo, ctx.state, statuses)
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


@check("specs-folder", frozenset({"requirements"}))
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
                error(ctx, kiro, "specs-folder", message + ", ".join(left), fix),
            )
    # The probe is not a dotfile, so a `.*` ignore rule does not match it.
    if (ctx.repo / ".git").exists() and git_ignored(
        ctx.repo,
        f"{configured}/specflow-probe",
    ):
        message = f"git ignores the specs folder {configured}, so its specs are never committed"
        fix = "Remove the ignore rule that matches it, or configure another specsDir."
        findings.append(error(ctx, ctx.repo / configured, "specs-folder", message, fix))
    return findings


@check("number-clashes", frozenset({"requirements", "intake"}))
def number_clashes_check(ctx: Context) -> list[Finding]:
    return number_clashes(ctx.repo, ctx.config)


@check("sources-line", SPEC_PHASES)
def sources_line(ctx: Context) -> list[Finding]:
    """A numbered spec's Sources: line names an intake item with the spec's own number."""
    number = NUMBER.match(ctx.spec_dir.name)
    path = artifact_paths(ctx.spec_dir, ctx.state)["requirements"]
    text = read_text(path)
    if number is None or text is None:
        return []
    found = partial(error, ctx, path, "sources-line")
    value = sources_value(text, bugfix=path.name == "bugfix.md")
    if value is None:
        where = (
            "at the end of ## Introduction"
            if path.name == "bugfix.md"
            else "in the header"
        )
        fix = f"Add a Sources: line {where} that names the intake item."
        return [found("no Sources: line", fix)]
    item = value.split(",")[0].strip().strip("`").rstrip("/").rsplit("/", 1)[-1]
    cited = NUMBER.match(item)
    if cited is None:
        fix = "Name the intake item's processed/ path first on the line."
        return [found(f"Sources: names no intake item: {value}", fix)]
    if cited[1] != number[1]:
        message = f"Sources: names intake item {item}, not one numbered {number[1]}"
        fix = "Name this spec's own intake item, or renumber the newer of the two."
        return [found(message, fix)]
    return []


def selected(phases: frozenset[str], phase: str | None) -> bool:
    """With a phase, the checks for it; with none, every check that is not gate-only."""
    if phase is not None:
        return phase in phases
    return UNFILTERED in phases or bool(phases & (SPEC_PHASES - {"implementation"}))


def validate(
    repo: Path,
    spec_dir: Path,
    phase: str | None = None,
    skip: frozenset[str] = frozenset(),
) -> list[Finding]:
    """Every finding of the phase's checks, except those named in skip; writes nothing."""
    try:
        state = load_state(spec_dir)
    except StateError:
        state = None
    ctx = Context(repo, workspace_config(repo), spec_dir, state, phase)
    findings: list[Finding] = []
    for name, (phases, function) in CHECKS.items():
        if name not in skip and selected(phases, phase):
            findings += function(ctx)
    return findings

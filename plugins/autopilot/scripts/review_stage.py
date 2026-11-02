"""Stage one review cycle's reviewer inputs and prompts (stdlib only).

Everything arrives explicitly from the caller: the independently resolved
expected context, the PRD and design text, the broad context and diff text,
and AP00012 input refs with their content. Nothing here discovers workflow
state, selects a lane or roster, runs tools, dispatches reviewers or writes
outside the explicit artifact root.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from dirty_tree import _git
from evidence_shapes import context_valid
from review_evidence import context_invalid, load_policy

_PACKAGE = Path(__file__).resolve().parent.parent
PERSONAS_DIR = _PACKAGE / "references" / "personas"
_SKILLS = _PACKAGE / "skills"
_RWC_REFS = _SKILLS / "review-work-completion" / "references"
CHECKLIST_FILE = _RWC_REFS / "review-dimensions.md"
CONSENSUS_RUBRIC = _RWC_REFS / "rubric.md"
OUTPUT_FORMATS = _RWC_REFS / "output-formats.md"
BLIND_RUBRIC = _SKILLS / "review-blindly" / "references" / "rubric.md"

LIVE_STATE_REL = Path("docs/dev/project-management/autopilot")
PERSONAS = ("alice", "bob", "blake", "carl", "eve")
REQUIRED_PERSONA_KEYS = ("name", "description", "tools")
# Blake is blind: only these ref kinds may reach his manifest or prompt.
BLIND_KINDS = frozenset({"prd", "card", "repo-tree", "rubric", "test-results"})
# Carried by the prompt itself (PRD body, staged diff file, packaged rubric).
NOT_INLINED_KINDS = frozenset({"prd", "diff", "rubric"})
EVE_DOUBT_SECTIONS = (
    "Two lenses",
    "Categorize every residual finding",
    "Rubric verdicts",
)
CITATION_LINE = (
    "Cite files repo-relative as path:line (for example skills/work/SKILL.md:166), "
    'never absolute and never with a "(lines a-b)" suffix.'
)
NO_PACK = "(no pack available this cycle)"
NO_SECTION = "(the pack has no Findings precedent section)"
NO_DIFF = "(no diff file this cycle)"
NO_MECH = "(no mechanical test checks this cycle)"
SETTLED_HEADING = "## Settled decisions — do not re-raise"
SETTLED_INTRO = (
    "> These calls were already made in an earlier cycle of this same review, with\n"
    "> the reasons given. Do not re-raise them. Raise a NEW finding only if you can\n"
    "> show the settled reason no longer holds."
)
INCREMENTAL_NOTE = (
    "This is an **incremental review** of the rework done since the previous "
    "review cycle — the diff is scoped to changes since then. Two jobs: (1) for "
    "each prior finding listed below, verify it is now resolved in the code; (2) "
    "review the scoped diff for any regression the rework introduced. You need "
    "not re-review unchanged code; the previous cycle already reviewed the full "
    "implementation."
)

_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*", re.ASCII)
_TOKEN_RE = re.compile(r"\{([A-Z_]+)\}")
_DIFF_HEADER_RE = re.compile(r"^diff --git a/.* b/(.+)$", re.MULTILINE)
_FINDINGS_RE = re.compile(
    r"^(#+)\s*Findings precedent\s*$",
    re.MULTILINE | re.IGNORECASE,
)


def _cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_tasks(tasks: list[dict]) -> str:
    """One table row per task. A folded task keeps its own row; its shared
    commit and companion task ids sit in that row, never merged away."""
    if not tasks:
        return ""
    lines = [
        "| ID | Task | Status | Commit | Description | Shared with |",
        "|----|------|--------|--------|-------------|-------------|",
    ]
    for task in tasks:
        companions = task.get("companions") or []
        cells = [
            task.get("id"),
            task.get("name") or task.get("subject"),
            task.get("status"),
            task.get("commit"),
            task.get("description"),
            ", ".join(str(c) for c in companions),
        ]
        lines.append("| " + " | ".join(_cell(c) for c in cells) + " |")
    return "\n".join(lines) + "\n"


def findings_precedent(pack_text: str | None) -> str:
    """The pack's "Findings precedent" section body, up to the next heading
    at the same or a higher level."""
    if pack_text is None:
        return NO_PACK
    match = _FINDINGS_RE.search(pack_text)
    if match is None:
        return NO_SECTION
    level = len(match.group(1))
    rest = pack_text[match.end() :]
    stop = re.search(rf"^#{{1,{level}}}\s", rest, re.MULTILINE)
    return (rest[: stop.start()] if stop else rest).strip()


def _refusal(error: str, detail: str) -> dict[str, Any]:
    return {"schema_version": 1, "ok": False, "error": error, "detail": detail}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _input_problem(
    prd_text: Any, context: dict[str, Any], input_texts: Any
) -> str | None:
    """Why the PRD bytes or supplied refs disagree with the bound context."""
    if not isinstance(prd_text, str) or not isinstance(input_texts, dict):
        return "prd_text must be text and input_texts a mapping"
    if _sha(prd_text.encode("utf-8")) != context["source_bindings"]["prd_sha256"]:
        return "prd_text does not match source_bindings.prd_sha256"
    allowed = context["allowed_inputs"]
    unknown = set(input_texts) - set(allowed["input_refs"])
    if unknown:
        return f"input_texts carries undeclared refs: {sorted(unknown)}"
    required = {ref for refs in allowed["per_job"].values() for ref in refs}
    missing = required - set(input_texts)
    if missing:
        return f"required per-job refs have no content: {sorted(missing)}"
    tree = context["source_bindings"]["tree_sha"]
    for ref, value in input_texts.items():
        kind = ref.split(":", 1)[0]
        if not isinstance(value, str):
            return f"{ref} content is not text"
        if kind == "prd" and value != prd_text:
            return f"{ref} content differs from prd_text"
        if kind == "repo-tree" and (ref != f"repo-tree:{tree}" or value != tree):
            return f"{ref} does not name the bound tree_sha"
    return None


def _precheck(
    cycle_id: Any, prd_text: Any, context: Any, input_texts: Any
) -> dict[str, Any] | None:
    if not isinstance(cycle_id, str) or not _ID_RE.fullmatch(cycle_id):
        return _refusal("invalid-input", f"cycle_id {cycle_id!r} is not a safe id")
    if not context_valid(context) or context_invalid(load_policy(), context):
        return _refusal("invalid-expected-context", "expected_context is invalid")
    problem = _input_problem(prd_text, context, input_texts)
    return _refusal("invalid-input", problem) if problem else None


def _persona_body(name: str) -> str | None:
    """The persona prompt body, when its packaged frontmatter declares a
    non-empty name, description and tools; None otherwise."""
    if name not in PERSONAS:
        return None
    text = (PERSONAS_DIR / f"{name}.md").read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or end < 0:
        return None
    keys = {
        key.strip(): value.strip()
        for key, sep, value in (
            line.partition(":") for line in text[4:end].splitlines()
        )
        if sep
    }
    if not all(keys.get(key) for key in REQUIRED_PERSONA_KEYS):
        return None
    return text[end + 5 :]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, title: str) -> str:
    """The markdown section whose heading starts with `title`, heading
    included, up to the next heading at the same or a higher level."""
    match = re.search(rf"^(#+) {re.escape(title)}.*$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"no {title!r} section")
    level = len(match.group(1))
    stop = re.compile(rf"^#{{1,{level}}} ", re.MULTILINE).search(text, match.end())
    return text[match.start() : stop.start() if stop else len(text)].rstrip()


def _output_format(name: str) -> str:
    section = _section(_read(OUTPUT_FORMATS), "Agent Output Format")
    return f"{section}\n\nYour agent name is {name.upper()}."


def _manifest(context: dict[str, Any], job: str) -> list[str]:
    refs = sorted(set(context["allowed_inputs"]["per_job"][job]))
    if job == "blake":
        return [ref for ref in refs if ref.split(":", 1)[0] in BLIND_KINDS]
    return refs


def _supplied(refs: list[str], texts: dict[str, str]) -> str | None:
    rows = [
        f"### {ref}\n\n{texts[ref].rstrip()}"
        for ref in refs
        if ref.split(":", 1)[0] not in NOT_INLINED_KINDS
    ]
    return "## Supplied inputs\n\n" + "\n\n".join(rows) if rows else None


def _history(settled: str | None, prior: str | None) -> list[str | None]:
    ledger = (
        f"{SETTLED_HEADING}\n\n{SETTLED_INTRO}\n\n{settled.strip()}"
        if settled
        else None
    )
    incremental = (
        f"## Incremental review\n\n{INCREMENTAL_NOTE}\n\n"
        f"### Prior cycle findings\n\n{prior.strip()}"
        if prior
        else None
    )
    return [ledger, incremental]


def _eve_inputs(run: dict[str, Any]) -> str:
    """agent-invocation.md's five Eve run inputs."""
    changed = "\n".join(run["changed"]) or NO_DIFF
    return "\n\n".join(
        [
            f"## PRD\n{run['prd']}",
            f"## Diff range\n{run['range']}",
            f"## Changed files\n{changed}",
            f"## Findings precedent\n{run['findings']}",
            f"## Mechanical test checks\n{NO_MECH}",
        ]
    )


def _plan(job: str, body: str, run: dict[str, Any]) -> tuple[str, dict, list]:
    """(template, token values, blocks appended after substitution)."""
    supplied = _supplied(run["manifest"][job], run["texts"])
    if job == "blake":  # blind: raw PRD and spec-only rubric, never history
        values = {
            "PRD": run["prd"],
            "RUBRIC": _read(BLIND_RUBRIC).strip(),
            "OUTPUT_FORMAT": _output_format(job),
        }
        return body, values, [supplied]
    if job == "eve":
        values = {"PACK_FINDINGS": run["findings"]}
        return body, values, [_eve_inputs(run), supplied, *run["history"]]
    values = {
        "CONTEXT_FILE": run["context"],
        "DIFF_FILE": run["diff"],
        "PACK_FILE": run["pack"],
        "REVIEW_CHECKLIST": _read(CHECKLIST_FILE).strip(),
        "RUBRIC": _read(CONSENSUS_RUBRIC).strip(),
        "OUTPUT_FORMAT": _output_format(job),
        "PACK_FINDINGS": run["findings"],
    }
    if job == "bob":
        eve = _read(PERSONAS_DIR / "eve.md")
        appendix = [_section(eve, title) for title in EVE_DOUBT_SECTIONS]
        body = "\n\n".join([body.rstrip(), *appendix, CITATION_LINE])
    precedent = None
    if "{PACK_FINDINGS}" not in body and run["pack"] != NO_PACK:
        precedent = f"## Findings precedent\n\n{run['findings']}"
    return body, values, [supplied, precedent, *run["history"]]


def _scoped(job: str, run: dict[str, Any]) -> dict[str, Any]:
    """`run` without the diff, pack and history the job's manifest omits."""
    kinds = {ref.split(":", 1)[0] for ref in run["manifest"][job]}
    scoped = dict(run)
    if "diff" not in kinds:
        scoped.update(diff=NO_DIFF, changed=[])
    if "context-pack" not in kinds:
        scoped.update(pack=NO_PACK, findings=NO_PACK)
    if "history" not in kinds:
        scoped.update(history=[None, None])
    return scoped


def _render(job: str, body: str, run: dict[str, Any]) -> str:
    """Substitute known tokens in one pass; injected text is never rescanned."""
    template, values, appends = _plan(job, body, _scoped(job, run))
    text = _TOKEN_RE.sub(lambda m: values.get(m.group(1), m.group(0)), template)
    blocks = [text.strip(), *(block.rstrip() for block in appends if block)]
    return "\n\n".join(blocks) + "\n"


def _context_file(
    context_text: str, paths: dict[str, Path], findings: str, inputs: dict
) -> str:
    pack = paths.get("review-pack")
    blocks = [
        context_text.rstrip(),
        f"## Review files\n\nTasks: {paths['review-tasks']}\n"
        f"PRD with design doc: {paths['review-prd']}",
        f"## Context Pack\n\nPack file: {pack or NO_PACK}\n\n"
        f"### Findings precedent\n\n{findings}",
    ]
    if inputs["settled"]:
        blocks.append(_history(inputs["settled"], None)[0])
    if inputs["gate"]:
        blocks.append(f"## Test gate\n\n{inputs['gate'].strip()}")
    return "\n\n".join(blocks) + "\n"


def _staged_files(art: Path, cycle_id: str, inputs: dict[str, Any]) -> dict:
    """{kind: (path, text)} for every non-prompt artifact, in write order."""
    merged = inputs["prd"]
    if inputs["design"]:
        merged += f"\n\n## Design Doc\n\n{inputs['design'].rstrip()}\n"
    files = {
        "review-tasks": ("review-tasks-{}.md", render_tasks(inputs["tasks"])),
        "review-prd-raw": ("review-prd-raw-{}.md", inputs["prd"]),
        "review-prd": ("review-prd-{}.md", merged),
        "review-context": ("review-context-{}.md", ""),
        "review-diff": ("review-diff-{}.diff", inputs["diff"]),
        "review-pack": ("review-pack-{}.md", inputs["pack"]),
    }
    staged = {
        kind: (art / name.format(cycle_id), body)
        for kind, (name, body) in files.items()
        if body is not None
    }
    paths = {kind: path for kind, (path, _) in staged.items()}
    findings = findings_precedent(inputs["pack"])
    body = _context_file(inputs["context"], paths, findings, inputs)
    staged["review-context"] = (paths["review-context"], body)
    return staged


def _toplevel(cwd: Path) -> Path | None:
    probe = _git(cwd, "rev-parse", "--show-toplevel")
    return Path(probe.stdout.strip()).resolve() if probe.returncode == 0 else None


def _existing_ancestor(path: Path) -> Path:
    while not path.exists():
        path = path.parent
    return path


def _repo_problem(project: Path, art_real: Path, outputs: list[Path]) -> str | None:
    """Refusal reason for outputs that resolve inside the project's repo."""
    top = _toplevel(project)
    if top is None:
        return "project_root is not inside a git work tree"
    gitdir = _git(project, "rev-parse", "--absolute-git-dir")
    if gitdir.returncode != 0 or art_real.is_relative_to(
        Path(gitdir.stdout.strip()).resolve()
    ):
        return "artifact_root is inside git internals"
    if _toplevel(_existing_ancestor(art_real)) != top:
        return "artifact_root is inside a nested repository"
    return _tracked_problem(top, art_real, outputs)


def _in_live_state(*paths: Path) -> bool:
    """True when any path holds the live-state directory, in any spelling case."""
    live = tuple(part.casefold() for part in LIVE_STATE_REL.parts)
    for path in paths:
        parts = tuple(part.casefold() for part in path.parts)
        if any(parts[i : i + len(live)] == live for i in range(len(parts))):
            return True
    return False


def _tracked_problem(top: Path, art_real: Path, outputs: list[Path]) -> str | None:
    """Refusal reason when an output is tracked in the repo at `top`."""
    rels = [(art_real / p.name).relative_to(top).as_posix() for p in outputs]
    listing = _git(top, "ls-files", "-z", "--", *(":(literal)" + r for r in rels))
    if listing.returncode != 0:
        return "tracked-output probe failed"
    tracked = set(listing.stdout.split("\0")) & set(rels)
    return f"output is tracked: {sorted(tracked)}" if tracked else None


def _file_problem(path: Path) -> str | None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(st.st_mode):
        return f"{path.name} exists and is not a regular file"
    if st.st_mode & 0o111:
        return f"{path.name} is executable"
    if st.st_nlink > 1:
        return f"{path.name} has more than one hard link"
    return None


def _destination_problem(project: Path, art: Path, outputs: list[Path]) -> str | None:
    """Why the planned outputs may not be written, or None. `art` stays
    unresolved so a symlink below the supplied root is still visible."""
    if art.is_relative_to(project):
        current = art
        while current != project:
            if current.is_symlink():
                return f"{current} is a symlink"
            current = current.parent
    if art.exists() and not art.is_dir():
        return "artifact_root is not a directory"
    for path in outputs:
        problem = _file_problem(path)
        if problem:
            return problem
    try:
        art_real = art.resolve()
    except RuntimeError:
        return "artifact_root is a symlink loop"
    if ".git" in art_real.parts:
        return "artifact_root is inside git internals"
    if _in_live_state(Path(os.path.abspath(art)), art_real):
        return "artifact_root is inside live workflow state"
    if art_real.is_relative_to(project.resolve()):
        return _repo_problem(project, art_real, outputs)
    if not art.is_relative_to(project) and Path(os.path.abspath(art)) != art_real:
        return "artifact_root is reached through a symlink"
    top = _toplevel(_existing_ancestor(art_real))
    return _tracked_problem(top, art_real, outputs) if top else None


def _write(path: Path, text: str) -> str:
    data = text.encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o666)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    return _sha(data)


def _run_inputs(staged: dict, context: dict, inputs: dict, jobs: list) -> dict:
    bindings = context["source_bindings"]
    diff_path = staged.get("review-diff")
    pack_path = staged.get("review-pack")
    return {
        "prd": inputs["prd"],
        "context": str(staged["review-context"][0]),
        "diff": str(diff_path[0]) if diff_path else NO_DIFF,
        "pack": str(pack_path[0]) if pack_path else NO_PACK,
        "findings": findings_precedent(inputs["pack"]),
        "history": _history(inputs["settled"], inputs["prior"]),
        "changed": list(dict.fromkeys(_DIFF_HEADER_RE.findall(inputs["diff"] or ""))),
        "range": f"{bindings['base_sha']}..{bindings['head_sha']}",
        "texts": inputs["texts"],
        "manifest": {job: _manifest(context, job) for job in jobs},
    }


def _write_all(staged: dict, prompts: dict[str, tuple[Path, str]]) -> dict:
    artifacts = [
        {"kind": kind, "path": str(path), "sha256": _write(path, body)}
        for kind, (path, body) in staged.items()
    ]
    artifacts += [
        {"kind": "prompt", "path": str(path), "sha256": _write(path, body)}
        for path, body in prompts.values()
    ]
    paths = {job: str(path) for job, (path, _) in prompts.items()}
    return {"artifacts": artifacts, "prompts": paths}


def _write_cycle(
    real: Path, cycle_id: str, inputs: dict, context: dict, bodies: dict
) -> dict:
    jobs = list(bodies)
    staged = _staged_files(real, cycle_id, inputs)
    run = _run_inputs(staged, context, inputs, jobs)
    prompts = {
        job: (real / f"{job}-prompt-{cycle_id}.md", _render(job, bodies[job], run))
        for job in jobs
    }
    try:
        real.mkdir(parents=True, exist_ok=True)
        written = _write_all(staged, prompts)
    except OSError as err:
        return _refusal("write-failed", str(err))
    return {
        "schema_version": 1,
        "ok": True,
        **written,
        "input_manifest": run["manifest"],
    }


def stage_review(
    *,
    project_root: Path,
    artifact_root: Path,
    cycle_id: str,
    tasks: list[dict],
    prd_text: str,
    design_text: str | None,
    context_text: str,
    diff_text: str | None,
    expected_context: dict,
    input_texts: dict[str, str],
    pack_text: str | None = None,
    settled_text: str | None = None,
    prior_findings_text: str | None = None,
    test_gate_text: str | None = None,
) -> dict:
    """Validate everything, then write the cycle's artifacts and one prompt
    per resolved roster job beneath artifact_root. Refusals write nothing."""
    refusal = _precheck(cycle_id, prd_text, expected_context, input_texts)
    if refusal:
        return refusal
    if not isinstance(tasks, list) or not all(isinstance(t, dict) for t in tasks):
        return _refusal("invalid-input", "tasks must be a list of objects")
    jobs = [row["job_id"] for row in expected_context["resolved_roster"]]
    bodies = {job: _persona_body(job) for job in jobs}
    unavailable = sorted(job for job, body in bodies.items() if body is None)
    if unavailable:
        return _refusal("persona-unavailable", f"no packaged persona: {unavailable}")
    project = Path(project_root).absolute()
    # Source 9dba4206: a subdirectory root stages under the repo toplevel.
    top = _toplevel(project)
    if top is not None and top != project.resolve():
        project = top
    art = Path(artifact_root)
    art = art if art.is_absolute() else project / art
    inputs = {
        "tasks": tasks,
        "prd": prd_text,
        "design": design_text,
        "context": context_text,
        "diff": diff_text,
        "pack": pack_text,
        "settled": settled_text,
        "prior": prior_findings_text,
        "gate": test_gate_text,
        "texts": input_texts,
    }
    outputs = [path for path, _ in _staged_files(art, cycle_id, inputs).values()]
    outputs += [art / f"{job}-prompt-{cycle_id}.md" for job in jobs]
    problem = _destination_problem(project, art, outputs)
    if problem:
        return _refusal("unsafe-output", problem)
    return _write_cycle(art.resolve(), cycle_id, inputs, expected_context, bodies)

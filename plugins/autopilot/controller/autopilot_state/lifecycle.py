"""PRD selection, entry, phase handoff and completion for workflow.lifecycle.v1.

Adapted from OVCAQ src/ovcaq/workflow/transitions.py, selection.py, resume.py
and the pure half of records.py at cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7.
`select_eligible` and `evaluate` port claude-autopilot
skills/run-autopilot/cli/selection.py and cli/eligibility.py at f40004a.

The reducers `enter`, `handoff` and `complete` take the public, locking
`StateStore` API (and `complete` runs `files.complete_prd`, which locks on its
own), so a caller must invoke them outside `StateStore._locked`. They check
the receipt cache and actor binding; credential authentication stays with
the dispatcher.
"""

from __future__ import annotations

import copy
import re
import subprocess
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from . import actors, files, schema
from .frontmatter import command_for
from .store import StateStore

type Workflow = dict
type TransitionEffect = Callable[[Workflow], Workflow]

_SEQUENCE_RE = re.compile(r"^(\d{5})-")


@dataclass(frozen=True)
class TransitionRow:
    effect: TransitionEffect
    next_phase: str


class UnknownTransition(ValueError):
    """Raised when no transition row matches a phase and outcome."""


# -- records.py: pure per-PRD bookkeeping -----------------------------------


def require_recovery_idle(workflow: Workflow) -> None:
    """Reject a competing workflow mutation while a saga owns the PRD."""
    if workflow["recovery"] is not None:
        raise files.RecoveryConflictError(
            f"recovery operation at {workflow['recovery']['boundary']!r} is active; "
            "reconcile it first")


def reset_prd_fields(workflow: Workflow) -> Workflow:
    """Reset per-PRD fields; keep batch, recovery, jobs and the PRD identity."""
    result = copy.deepcopy(workflow)
    work = result["work"]
    if work is not None:
        work["phase"] = "build"
        work["completed_phases"] = []
        work["lane"] = None
        work["lane_reason"] = None
    result["tasks"] = []
    return result


def completed_prd_summary(workflow: Workflow) -> str:
    """Return the `batch.completed_prds` entry for the active PRD."""
    work = workflow["work"]
    if work is None:
        raise files.PreconditionError("cannot complete a workflow without an active PRD")
    return work["prd"]


# -- transitions.py ----------------------------------------------------------


def _to_review(workflow: Workflow) -> Workflow:
    result = copy.deepcopy(workflow)
    result["work"]["phase"] = "review"
    return result


def _rework(workflow: Workflow) -> Workflow:
    result = copy.deepcopy(workflow)
    result["work"]["phase"] = "review"
    return result


def _converged(workflow: Workflow) -> Workflow:
    result = copy.deepcopy(workflow)
    result["work"]["phase"] = "done"
    if "review" not in result["work"]["completed_phases"]:
        result["work"]["completed_phases"].append("review")
    return result


def _drained(workflow: Workflow) -> Workflow:
    result = copy.deepcopy(workflow)
    result["work"]["phase"] = "done"
    return result


TRANSITIONS: dict[tuple[str, str], TransitionRow] = {
    ("build", "tasks_done"): TransitionRow(_to_review, "review"),
    ("review", "rework"): TransitionRow(_rework, "review"),
    ("review", "converged"): TransitionRow(_converged, "done"),
    ("done", "more_prds"): TransitionRow(reset_prd_fields, "build"),
    ("done", "drained"): TransitionRow(_drained, ""),
    ("build", "drained"): TransitionRow(_drained, ""),
}

OUTCOMES = tuple(sorted({outcome for _phase, outcome in TRANSITIONS}))


def apply(workflow: Workflow, outcome: str) -> Workflow:
    """Apply the sole effect for `(workflow.work.phase, outcome)`."""
    require_recovery_idle(workflow)
    if workflow["batch"] is None:
        raise UnknownTransition("workflow transitions require a running batch")
    if workflow["work"] is None:
        raise UnknownTransition("workflow transitions require an active PRD")
    phase = workflow["work"]["phase"]
    row = TRANSITIONS.get((phase, outcome))
    if row is None:
        raise UnknownTransition(f"no transition from phase {phase!r} on outcome {outcome!r}")
    return row.effect(workflow)


def next_phase(phase: str, outcome: str) -> str:
    """Return the target phase a transition row declares."""
    try:
        return TRANSITIONS[(phase, outcome)].next_phase
    except KeyError as error:
        raise UnknownTransition(
            f"no transition from phase {phase!r} on outcome {outcome!r}") from error


def phase_complete(store: StateStore, outcome: str, *,
                   expected_revision: int | None = None) -> dict:
    """Apply one closed transition in one compare-and-set transaction."""
    def mutate(state: dict) -> None:
        state["workflow"] = apply(state["workflow"], outcome)

    return store.transaction(mutate, expected_revision=expected_revision)


# -- selection.py --------------------------------------------------------------


def sequence(name: str) -> int | None:
    """Return the `00XXX-` prefix of `name` as an int, or None."""
    match = _SEQUENCE_RE.match(name)
    return int(match.group(1)) if match else None


def _has_line_break_or_control(name: str) -> bool:
    return len(name.splitlines()) > 1 or any(
        unicodedata.category(character) == "Cc" for character in name)


def selectable(names: Iterable[str]) -> list[str]:
    """Return selectable Markdown PRD names, lowest sequence first."""
    picks = [name for name in names
             if name.endswith(".md") and sequence(name) is not None
             and not _has_line_break_or_control(name)]
    return sorted(picks, key=lambda name: (sequence(name) or 0, name))


def select(wip: Iterable[str], backlog: Iterable[str]) -> tuple[str | None, str]:
    """Select from wip first, then backlog; hold is unreachable by design."""
    in_wip = selectable(wip)
    if in_wip:
        return in_wip[0], "wip"
    in_backlog = selectable(backlog)
    if in_backlog:
        return in_backlog[0], "backlog"
    return None, "drained"


# -- resume.py -----------------------------------------------------------------


def resume_target(state: dict) -> str:
    """Describe the next action from committed state only."""
    workflow = state["workflow"]
    marker = workflow["recovery"]
    if marker is not None:
        try:
            operation = schema.decode_json(marker["op"], source="recovery operation")
        except schema.SchemaError:
            operation = None
        if not isinstance(operation, dict) or not {"kind", "id", "prd"} <= set(operation):
            return "reconcile unreadable recovery operation"
        return f"reconcile {operation['kind']} {operation['id']} for {operation['prd']}"
    work = workflow["work"]
    if work is None:
        return "enter next PRD"
    phase = work["phase"]
    if phase == "review":
        if "review" in work["completed_phases"]:
            return "skip review -> done"
        return "run review loop"
    if phase == "build":
        tasks = workflow["tasks"]
        if tasks:
            pending = next((task for task in tasks if task["status"] != "completed"), None)
            if pending is None:
                return "all tasks done -> review gate"
            return f"continue build at first non-completed task {pending['id']}"
        return "build: catchup then planning"
    if phase == "done":
        return "done"
    return f"unknown phase: {phase}"


# -- eligibility (claude-autopilot cli/eligibility.py, cli/selection.py) -------


def evaluate(command: str, cwd: Path, timeout: float = 30.0) -> tuple[int, str]:
    """Run a PRD's eligibility command; -1 with a note when it could not answer."""
    # A shell runs the command by contract: the PRD declares one shell command,
    # authored by the operator in this repo, and splitting it would break its
    # pipes and $(...). Mitigations: read-only convention, the timeout, and
    # failure meaning skip.
    try:
        completed = subprocess.run(["/bin/sh", "-c", command], cwd=str(cwd),
                                   timeout=timeout, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except OSError as error:
        return -1, f"error: {error}"
    return completed.returncode, ""


def _regular_names(directory: Path) -> list[str]:
    if directory.is_symlink() or not directory.is_dir():
        return []
    return [entry.name for entry in directory.iterdir()
            if not entry.is_symlink() and entry.is_file()]


def select_eligible(project_root: Path) -> dict:
    """Pick the next PRD, running backlog eligibility checks; moves and writes nothing."""
    buckets = project_root / files.PRD_ROOT
    in_wip = _regular_names(buckets / "wip")
    in_backlog = _regular_names(buckets / "backlog")
    skipped: list[dict] = []
    while True:
        prd, source = select(in_wip, in_backlog)
        if source != "backlog":
            return {"prd": prd, "source": source, "skipped": skipped}
        try:
            text = (buckets / "backlog" / prd).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Unreadable declares no check: pick it; the session reports it.
            text = ""
        command = command_for(text)
        if command is None:
            return {"prd": prd, "source": source, "skipped": skipped}
        exit_code, note = evaluate(command, project_root)
        if exit_code == 0:
            return {"prd": prd, "source": source, "skipped": skipped}
        skipped.append({"prd": prd, "command": command, "exit_code": exit_code,
                        "note": note, "at": files._utc_now()})
        in_backlog = [name for name in in_backlog if name != prd]


# -- reducers ------------------------------------------------------------------


def _replay(request: dict, current: dict) -> dict | None:
    """Return the cached response for a replayed request, or admit a fresh one."""
    from . import protocol

    revision = current["revision"]
    receipt = current["receipts"].get(request["request_id"])
    if receipt is not None:
        protocol.actor_binding(request, receipt["authorizing_actor"], revision)
        if receipt["request_digest"] != actors.digest(actors.canonical(request)):
            raise protocol.ProtocolError("invalid_request", revision)
        return receipt["response"]
    descriptor = current["actors"].get(request["actor_id"])
    if descriptor is None:
        raise protocol.ProtocolError("wrong_binding", revision)
    protocol.actor_binding(request, descriptor, revision)
    if request["expected_revision"] != revision:
        raise protocol.ProtocolError("revision_conflict", revision)
    return None


def _payload(request: dict, keys: set[str], revision: int) -> dict:
    from . import protocol

    payload = request["payload"]
    if not isinstance(payload, dict) or set(payload) != keys:
        raise protocol.ProtocolError("invalid_request", revision)
    return payload


def _rejected(revision: int) -> Exception:
    from . import protocol

    return protocol.ProtocolError("rejected_evidence", revision)


def _present(directory: Path, names: list[str]) -> list[str]:
    """The given names that sit in `directory` as regular non-symlink files."""
    if not directory.exists():
        return []
    found = []
    with files._open_directory(directory) as descriptor:
        for name in names:
            try:
                if files._artifact(descriptor, name) is not None:
                    found.append(name)
            except OSError:
                continue
    return found


def _require_in_wip(buckets: Path, prd: str) -> None:
    if not _present(buckets / "wip", [prd]):
        raise files.BucketError(f"PRD {prd} left wip before its entry committed")


def _commit_entry(store: StateStore, current: dict, prd: str, source: str,
                  guard: Callable[[], None]) -> dict:
    def mutate(state: dict) -> None:
        workflow = state["workflow"]
        require_recovery_idle(workflow)
        if workflow["work"] is not None:
            raise files.PreconditionError("another PRD is already active")
        if workflow["batch"] is None:
            workflow["batch"] = {"completed_prds": [], "parks_consecutive": 0}
        workflow["work"] = {"prd": prd, "source": source, "entered_at": files._utc_now(),
                            "phase": "build", "completed_phases": [], "lane": None,
                            "lane_reason": None}
        state["workflow"] = reset_prd_fields(workflow)

    return store.transaction(mutate, expected_revision=current["revision"],
                             publication_guard=guard)


def _enter_backlog(store: StateStore, current: dict, buckets: Path, prd: str) -> dict:
    """Verified rename backlog/ -> wip/, then commit the entry under a guard."""
    with (files._open_directory(buckets / "backlog") as backlog_fd,
          files._open_directory(buckets / "wip", create=True) as wip_fd):
        # files._Move names its source side "wip"; here the source is backlog/.
        move = files._Move(name=prd, wip=buckets / "backlog", destination=buckets / "wip",
                           wip_fd=backlog_fd, destination_fd=wip_fd)
        source, destination = move.locate()
        if source is None:
            raise files.BucketError(f"PRD {prd} is not in {move.wip}")
        if destination is not None:
            raise files.BucketError(f"PRD {prd} already exists in {move.destination}")
        artifact = files._identity(source)
        files._rename(move, artifact, None)
        return _commit_entry(store, current, prd, "backlog",
                             lambda: files._verify_moved(move, artifact))


def enter(store: StateStore, request: dict, current: dict) -> dict:
    """`prd.enter`: pick wip-first, else lowest backlog, move it, open its work."""
    from . import protocol

    revision = current["revision"]
    cached = _replay(request, current)
    if cached is not None:
        return cached
    prds = _payload(request, {"prds"}, revision)["prds"]
    try:
        if not isinstance(prds, list) or not prds:
            raise files.PreconditionError("prds must be a non-empty list")
        for name in prds:
            files._require_basename(name, "prd")
    except files.PreconditionError as error:
        raise protocol.ProtocolError("invalid_request", revision) from error
    workflow = current["workflow"]
    completed = [] if workflow["batch"] is None else workflow["batch"]["completed_prds"]
    candidates = [name for name in dict.fromkeys(prds) if name not in completed]
    if (not candidates or workflow["work"] is not None
            or workflow["recovery"] is not None):
        raise _rejected(revision)
    buckets = Path(current["repo_root"]) / files.PRD_ROOT
    prd, source = select(_present(buckets / "wip", candidates),
                         _present(buckets / "backlog", candidates))
    if prd is None:
        raise _rejected(revision)
    try:
        if source == "backlog":
            committed = _enter_backlog(store, current, buckets, prd)
        else:
            committed = _commit_entry(store, current, prd, source,
                                      lambda: _require_in_wip(buckets, prd))
    except (files.PreconditionError, files.RecoveryConflictError) as error:
        raise _rejected(revision) from error
    except files.RecoveryRequiredError as error:
        raise protocol.ProtocolError("recovery_required", revision) from error
    return protocol.response({"prd": prd, "source": source}, committed["revision"])


def handoff(store: StateStore, request: dict, current: dict) -> dict:
    """`phase.handoff`: apply the one transition row for the reported outcome."""
    from . import protocol

    revision = current["revision"]
    cached = _replay(request, current)
    if cached is not None:
        return cached
    payload = _payload(request, {"phase", "next_phase", "outcome"}, revision)
    try:
        apply(current["workflow"], payload["outcome"])
        phase = current["workflow"]["work"]["phase"]
        if (payload["phase"] != phase
                or payload["next_phase"] != next_phase(phase, payload["outcome"])):
            raise UnknownTransition("handoff evidence does not match the transition row")
        committed = phase_complete(store, payload["outcome"], expected_revision=revision)
    except (UnknownTransition, files.RecoveryConflictError) as error:
        raise _rejected(revision) from error
    return protocol.response({"phase": committed["workflow"]["work"]["phase"],
                              "next_phase": payload["next_phase"]}, committed["revision"])


def complete(store: StateStore, request: dict, current: dict) -> dict:
    """`prd.complete`: after accepted review only, run the wip/ -> done/ saga."""
    from . import protocol

    revision = current["revision"]
    cached = _replay(request, current)
    if cached is not None:
        return cached
    _payload(request, set(), revision)
    workflow = current["workflow"]
    try:
        require_recovery_idle(workflow)
        prd = completed_prd_summary(workflow)
        if (workflow["work"]["phase"] != "done"
                or "review" not in workflow["work"]["completed_phases"]):
            raise files.PreconditionError(
                "cannot complete a PRD outside the terminal reviewed state")
        # files.complete_prd commits the completed_prds append, the park
        # counter reset and the per-PRD reset in its own commit step.
        files.complete_prd(store, project_root=Path(current["repo_root"]), prd=prd)
    except (files.PreconditionError, files.RecoveryConflictError) as error:
        raise _rejected(revision) from error
    except files.RecoveryRequiredError as error:
        raise protocol.ProtocolError("recovery_required", revision) from error
    return protocol.response({"prd": prd}, store.read()["revision"])

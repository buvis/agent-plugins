"""Guard duties: nine checks, four relayed to the controller seam, five pure.

A stateful duty asks `seam.evaluate_guard` and relays its answer verbatim; it
holds no policy of its own and refuses when no seam is given. A pure duty
decides from its own named context keys alone, never sees a seam, and denies
when a required key is absent or mistyped. No generic `ok` flag has meaning.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from enum import StrEnum
import posixpath
from pathlib import PurePosixPath

import jobs
from jobs import ControllerSeam


class GuardDuty(StrEnum):
    DOCUMENT_LOCATION = "document_location"
    CUSTODY_PUSH = "custody_push"
    DELEGATION = "delegation"
    POST_HANDOFF = "post_handoff"
    DEPARTURE = "departure"
    CONTEXT_REINJECTION = "context_reinjection"
    STATE_INTEGRITY = "state_integrity"
    REVIEW_COMPLETENESS = "review_completeness"
    LIVE_JOB = "live_job"


@dataclass(frozen=True)
class GuardOutcome:
    duty: GuardDuty
    allowed: bool
    reason: str | None  # set when allowed is False
    stateful: bool  # True -> this call hit `seam`; False -> pure/artifact-only


def _malformed_verdict(duty: GuardDuty) -> GuardOutcome:
    return GuardOutcome(duty=duty, allowed=False, reason="malformed_controller_verdict", stateful=True)


def _relay(duty: GuardDuty, context: dict, seam: ControllerSeam) -> GuardOutcome:
    try:
        verdict = seam.evaluate_guard(duty.value, context)
    except Exception:
        return _malformed_verdict(duty)
    if not isinstance(verdict, dict) or set(verdict) != {"allowed", "reason"}:
        return _malformed_verdict(duty)
    allowed = verdict["allowed"]
    reason = verdict["reason"]
    if not isinstance(allowed, bool):
        return _malformed_verdict(duty)
    if reason is not None and not isinstance(reason, str):
        return _malformed_verdict(duty)
    if not allowed and not reason:
        return _malformed_verdict(duty)
    return GuardOutcome(duty=duty, allowed=allowed, reason=reason, stateful=True)


_LIFECYCLE_DIRS = ("backlog", "wip", "hold", "done")
_META_KEEPERS = frozenset(
    {
        "project-capsule.md",
        "decisions.md",
        "troubleshooting.md",
        "assumptions.md",
        "agoge-profile.md",
        "ecc-cursor",
        "upstream-cursor",
    }
)
_KNOWN_STORE_DIRS = frozenset(
    {
        "prds", "designs", "reviews", "plans", "autopilot", "meta", "discovery",
        "intake", "specs", "notes", "walkthroughs", "audit-results", "spikes",
    }
)  # fmt: skip
_STORE_SEGMENTS = ("docs", "dev", "project-management")
_PHASE_SKILLS = frozenset(
    {
        "autopilot:work",
        "autopilot:plan-tasks",
        "autopilot:design-solution",
        "autopilot:review-work-completion",
        "autopilot:run-autopilot",
        "git-ferry:catchup",
    }
)
_GUARDED_SKILL_PREFIX = "autopilot:"
_GUARDED_SKILL_EXACT = frozenset({"git-ferry:catchup"})


def _allow(duty: GuardDuty) -> GuardOutcome:
    return GuardOutcome(duty=duty, allowed=True, reason=None, stateful=False)


def _deny(duty: GuardDuty, detail: str) -> GuardOutcome:
    return GuardOutcome(duty=duty, allowed=False, reason=f"{duty.value}: {detail}", stateful=False)


def _is_type(value: object, kind: type) -> bool:
    # bool is an int subclass; an int key must not accept True/False.
    if kind is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, kind)


def _missing_input(duty: GuardDuty, context: dict, required: dict) -> GuardOutcome | None:
    """Fail closed: deny naming the first required key that is absent or mistyped."""
    for key, kind in required.items():
        if key not in context or not _is_type(context[key], kind):
            return _deny(duty, f"missing or mistyped required input {key!r} ({kind.__name__})")
    return None


def _store_rel(parts: tuple[str, ...]) -> tuple[str, ...] | None:
    """Path parts below the first whole-segment docs/dev/project-management, or None."""
    n = len(_STORE_SEGMENTS)
    for i in range(len(parts) - n + 1):
        if parts[i : i + n] == _STORE_SEGMENTS:
            return parts[i + n :]
    return None


def _store_rel_allowed(rel: tuple[str, ...]) -> bool:
    if len(rel) < 2:
        return False
    top = rel[0]
    if top == "prds":
        return len(rel) >= 3 and rel[1] in _LIFECYCLE_DIRS
    if top == "meta":
        return len(rel) == 2 and rel[1] in _META_KEEPERS
    return top in _KNOWN_STORE_DIRS


def _guard_custody_push(context: dict, seam: ControllerSeam) -> GuardOutcome:
    return _relay(GuardDuty.CUSTODY_PUSH, context, seam)


def _guard_state_integrity(context: dict, seam: ControllerSeam) -> GuardOutcome:
    return _relay(GuardDuty.STATE_INTEGRITY, context, seam)


def _guard_live_job(context: dict, seam: ControllerSeam) -> GuardOutcome:
    return _relay(GuardDuty.LIVE_JOB, context, seam)


def _guard_review_completeness(context: dict, seam: ControllerSeam) -> GuardOutcome:
    return _relay(GuardDuty.REVIEW_COMPLETENESS, context, seam)


def _normalize_rel(path: str, project_root: str | None) -> str:
    """`path` relative to `project_root`, walking up to an ancestor of
    `project_root` when it is not an exact prefix (e.g. a sub-cwd), and
    normalizing away a double slash; an unrelated absolute path still loses
    its leading slash so the whole-path store scan still runs on it."""
    if not isinstance(project_root, str) or not project_root:
        return path
    norm = posixpath.normpath(path)
    root = posixpath.normpath(project_root)
    parents = [str(parent) for parent in PurePosixPath(root).parents]
    candidates = [root, *(p for p in parents if p != "."), ""]
    for candidate in candidates:
        if norm == candidate:
            return ""
        prefix = candidate.rstrip("/") + "/"
        if norm.startswith(prefix):
            return norm[len(prefix):]
    return path


def _store_path_verdict(path: str) -> tuple[bool, str | None]:
    parts = PurePosixPath(posixpath.normpath(path)).parts
    if ".." in parts:
        return False, f"path climbs above its root and cannot be resolved: {path}"
    rel = _store_rel(parts)
    if rel is None:
        if parts and parts[0] in _LIFECYCLE_DIRS:
            return False, f"lifecycle directory outside the store: {path}"
        return True, None
    if _store_rel_allowed(rel):
        return True, None
    return False, f"path not allowed in the project-management store: {path}"


_REDIR_PREFIX = re.compile(r"^[0-9]*[<>&]+")
_ASSIGNMENT_TOKEN = re.compile(r"^(--?[A-Za-z0-9_-]+|[A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _clean_command_token(token: str) -> str:
    token = _REDIR_PREFIX.sub("", token)
    match = _ASSIGNMENT_TOKEN.match(token)
    if match:
        return match.group(2)
    return token


def _command_tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        return list(lexer)
    except ValueError:
        return command.split()


def _guard_document_location(context: dict) -> GuardOutcome:
    duty = GuardDuty.DOCUMENT_LOCATION
    has_path = "document_path" in context and _is_type(context["document_path"], str)
    has_command = "command" in context and _is_type(context["command"], str)
    if has_path == has_command:
        return _deny(
            duty,
            "missing or mistyped required input: exactly one of 'document_path', 'command' (str)",
        )
    if "project_root" in context and not _is_type(context["project_root"], str):
        return _deny(duty, "missing or mistyped required input 'project_root' (str)")
    project_root = context.get("project_root")

    if has_path:
        path = _normalize_rel(context["document_path"], project_root)
        allowed, reason = _store_path_verdict(path)
        if allowed:
            return _allow(duty)
        assert reason is not None
        return _deny(duty, reason)

    for token in _command_tokens(context["command"]):
        cleaned = _clean_command_token(token)
        if "/" not in cleaned:
            continue
        normalized = _normalize_rel(cleaned, project_root)
        parts = PurePosixPath(posixpath.normpath(normalized)).parts
        if parts and parts[0] in _LIFECYCLE_DIRS and _store_rel(parts) is None:
            return _deny(duty, f"lifecycle directory outside the store: {normalized}")
    return _allow(duty)


def _guard_delegation(context: dict) -> GuardOutcome:
    duty = GuardDuty.DELEGATION
    refused = _missing_input(duty, context, {"dispatch_skill": str, "child_depth": int})
    if refused:
        return refused
    if context["child_depth"] >= jobs.MAX_CHILD_DEPTH:
        return _deny(duty, "recursion_depth")
    skill = context["dispatch_skill"]
    if skill in _PHASE_SKILLS:
        return _deny(duty, f"whole phase skill must not be dispatched: {skill}")
    return _allow(duty)


def _guard_post_handoff(context: dict) -> GuardOutcome:
    duty = GuardDuty.POST_HANDOFF
    refused = _missing_input(duty, context, {"requested_skill": str, "leave_recorded": bool})
    if refused:
        return refused
    skill = context["requested_skill"]
    guarded = skill.startswith(_GUARDED_SKILL_PREFIX) or skill in _GUARDED_SKILL_EXACT
    if not (context["leave_recorded"] and guarded):
        return _allow(duty)
    # Diverges from the source hook, which lets a malformed marker pass because
    # prose backs it up. Here no prose backs it, so with one session key missing
    # we cannot show the leave row is another session's and we refuse.
    sessions = [context.get("session"), context.get("leave_session")]
    if all(isinstance(s, str) and s.strip() for s in sessions) and sessions[0] != sessions[1]:
        return _allow(duty)
    return _deny(duty, f"skill requested after the leave row: {skill}")


def _guard_departure(context: dict) -> GuardOutcome:
    duty = GuardDuty.DEPARTURE
    refused = _missing_input(
        duty, context, {"leave_row_written": bool, "last_store_write_at": int, "leave_row_at": int}
    )
    if refused:
        return refused
    if not context["leave_row_written"]:
        return _deny(duty, "no leave row was written")
    if context["last_store_write_at"] > context["leave_row_at"]:
        return _deny(duty, "a store write landed after the leave row")
    return _allow(duty)


def _guard_context_reinjection(context: dict) -> GuardOutcome:
    duty = GuardDuty.CONTEXT_REINJECTION
    refused = _missing_input(
        duty, context, {"contract_card_present": bool, "contract_card_body": str}
    )
    if refused:
        return refused
    if not context["contract_card_present"]:
        return _deny(duty, "contract card is not present")
    if not context["contract_card_body"].strip():
        return _deny(duty, "contract card body is blank")
    return _allow(duty)


_STATEFUL = {
    GuardDuty.CUSTODY_PUSH: _guard_custody_push,
    GuardDuty.STATE_INTEGRITY: _guard_state_integrity,
    GuardDuty.LIVE_JOB: _guard_live_job,
    GuardDuty.REVIEW_COMPLETENESS: _guard_review_completeness,
}

_PURE = {
    GuardDuty.DOCUMENT_LOCATION: _guard_document_location,
    GuardDuty.DELEGATION: _guard_delegation,
    GuardDuty.POST_HANDOFF: _guard_post_handoff,
    GuardDuty.DEPARTURE: _guard_departure,
    GuardDuty.CONTEXT_REINJECTION: _guard_context_reinjection,
}


_SEGMENT_SPLIT = re.compile(r"\n|&&|\|\||[;|&]")
_PREFIX_CMDS = frozenset(
    {"command", "exec", "env", "sudo", "nice", "time", "nohup", "timeout", "ionice", "stdbuf"}
)
_SKIP_KEYWORDS = frozenset({"if", "then", "else", "elif", "fi", "do", "done", "while", "until"})
_BRACKET_CHARS = re.compile(r"[(){}!]")
_ASSIGNMENT_WORD = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_INDIRECT_MARKERS = ("$(", "`", "eval", "sh -c", "bash -c", "zsh -c", "xargs", "<<")
_WORD_GIT = re.compile(r"\bgit\b")
_WORD_PUSH = re.compile(r"\bpush\b")


def is_git_push(command: str) -> bool:
    """Conservative superset of the git-push grammar (§7): a false positive
    only costs a seam consultation, so ambiguous forms fail closed to True.
    Grouping/negation punctuation is stripped before tokenizing (`shlex`
    handles quoting, including a quoted value split across what `.split()`
    would see as two words). A recognized wrapper command's own flags and
    their values are skipped wholesale - not flag-by-flag, since an unlisted
    option (`sudo --user x`, `exec -a x`) must not be mistaken for the
    wrapped command - by scanning past every token up to the next literal
    `git`. An unrecognized leading command (`echo git push`) is never
    treated as a wrapper: it is itself checked against `git`, so its own
    arguments mentioning `git`/`push` are not wrongly attributed to it."""
    for segment in _SEGMENT_SPLIT.split(command):
        cleaned = _BRACKET_CHARS.sub(" ", segment)
        try:
            tokens = shlex.split(cleaned)
        except ValueError:
            tokens = cleaned.split()
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if _ASSIGNMENT_WORD.match(token):
                i += 1
                continue
            if token in _SKIP_KEYWORDS:
                i += 1
                continue
            if PurePosixPath(token).name in _PREFIX_CMDS:
                i += 1
                while i < len(tokens) and PurePosixPath(tokens[i]).name != "git":
                    i += 1
                continue
            break
        if i < len(tokens) and PurePosixPath(tokens[i]).name == "git" and "push" in tokens[i + 1 :]:
            return True
    if (
        any(marker in command for marker in _INDIRECT_MARKERS)
        and _WORD_GIT.search(command)
        and _WORD_PUSH.search(command)
    ):
        return True
    return False


def run_guard(duty: GuardDuty, context: dict, *, seam: ControllerSeam | None) -> GuardOutcome:
    """Dispatch to the duty's guard; a non-member duty raises ValueError."""
    duty = GuardDuty(duty)
    if duty in _PURE:
        return _PURE[duty](context)
    if seam is None:
        return GuardOutcome(
            duty=duty, allowed=False, reason="missing_controller_seam", stateful=True
        )
    return _STATEFUL[duty](context, seam)

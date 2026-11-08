"""Guard duties: nine checks, four relayed to the controller seam, five pure.

A stateful duty asks `seam.evaluate_guard` and relays its answer verbatim; it
holds no policy of its own and refuses when no seam is given. A pure duty
decides from its own named context keys alone, never sees a seam, and denies
when a required key is absent or mistyped. No generic `ok` flag has meaning.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

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


def _relay(duty: GuardDuty, context: dict, seam: ControllerSeam) -> GuardOutcome:
    verdict = seam.evaluate_guard(duty.value, context)
    return GuardOutcome(
        duty=duty, allowed=verdict["allowed"], reason=verdict["reason"], stateful=True
    )


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


def _guard_document_location(context: dict) -> GuardOutcome:
    duty = GuardDuty.DOCUMENT_LOCATION
    refused = _missing_input(duty, context, {"document_path": str})
    if refused:
        return refused
    path = context["document_path"]
    parts = PurePosixPath(path).parts
    rel = _store_rel(parts)
    if rel is None:
        if parts and parts[0] in _LIFECYCLE_DIRS:
            return _deny(duty, f"lifecycle directory outside the store: {path}")
        return _allow(duty)
    if _store_rel_allowed(rel):
        return _allow(duty)
    return _deny(duty, f"path not allowed in the project-management store: {path}")


def _guard_delegation(context: dict) -> GuardOutcome:
    duty = GuardDuty.DELEGATION
    refused = _missing_input(duty, context, {"dispatch_skill": str})
    if refused:
        return refused
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
    if (
        "session" in context
        and "leave_session" in context
        and context["session"] != context["leave_session"]
    ):
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

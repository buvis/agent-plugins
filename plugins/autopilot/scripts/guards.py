"""Guard duties: nine checks, four relayed to the controller seam, five pure.

A stateful duty asks `seam.evaluate_guard` and relays its answer verbatim; it
holds no policy of its own and refuses when no seam is given. A pure duty
decides from its context alone and never sees a seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

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


def _check(duty: GuardDuty, context: dict) -> GuardOutcome:
    if context.get("ok", True) is False:
        return GuardOutcome(
            duty=duty, allowed=False, reason=f"{duty.value}_check_failed", stateful=False
        )
    return GuardOutcome(duty=duty, allowed=True, reason=None, stateful=False)


def _guard_custody_push(context: dict, seam: ControllerSeam) -> GuardOutcome:
    return _relay(GuardDuty.CUSTODY_PUSH, context, seam)


def _guard_state_integrity(context: dict, seam: ControllerSeam) -> GuardOutcome:
    return _relay(GuardDuty.STATE_INTEGRITY, context, seam)


def _guard_live_job(context: dict, seam: ControllerSeam) -> GuardOutcome:
    return _relay(GuardDuty.LIVE_JOB, context, seam)


def _guard_review_completeness(context: dict, seam: ControllerSeam) -> GuardOutcome:
    return _relay(GuardDuty.REVIEW_COMPLETENESS, context, seam)


def _guard_document_location(context: dict) -> GuardOutcome:
    return _check(GuardDuty.DOCUMENT_LOCATION, context)


def _guard_delegation(context: dict) -> GuardOutcome:
    return _check(GuardDuty.DELEGATION, context)


def _guard_post_handoff(context: dict) -> GuardOutcome:
    return _check(GuardDuty.POST_HANDOFF, context)


def _guard_departure(context: dict) -> GuardOutcome:
    return _check(GuardDuty.DEPARTURE, context)


def _guard_context_reinjection(context: dict) -> GuardOutcome:
    return _check(GuardDuty.CONTEXT_REINJECTION, context)


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

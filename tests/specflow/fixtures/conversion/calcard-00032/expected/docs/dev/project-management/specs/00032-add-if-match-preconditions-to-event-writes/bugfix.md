# Bugfix Requirements Document

**Status: Requirements approved — design phase.**
Profile: standard. Type: bugfix. Order: requirements-first.

## Introduction

Event writes can overwrite another client's intervening edit. Updates read an ETag but do not
condition the write on it; deletes have the same missing protection. Recurrence writes also
delegate to a library save path that can fetch and merge instead of storing the intended body.
Updates patch the first VEVENT rather than the requested component.

Reproduction inputs: fetch an event, modify its stored body through another client, then update
or delete using the earlier ETag; also update a multi-component resource with a requested
RECURRENCE-ID whose matching VEVENT is not first. An orphan override exercises the save-path
problem. Library recursion consequences remain hypotheses until exploration tests observe them.

Repository observations: `_caldav_mutation.py:update_event` reads `pre_etag`, selects the first
VEVENT, and calls `event.save()`; `delete_event` calls `event.delete()`; `create_event` uses
`calendar.save_event` even with `recurrence_id`. These are source observations, not executed
reproductions. The current parameter documentation treats `recurrence_id` as a new field value;
the intake instead requires using it to select a component. The developer confirmed that an
explicit selector with no stored match must be rejected without writing. An orphan-only resource
also requires an explicit occurrence selector, even when it contains only one override.

Constraints from AGENTS.md: preserve full resource fidelity, library escaping, client-layer
error wrapping, tool thread dispatch, and enabled write verification. Check equivalent task and
contact paths; task implementation belongs to 00033 and convergence to 00040. No new dependency.

Sources: docs/dev/project-management/intake/processed/00032-add-if-match-preconditions-to-event-writes/idea.md

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN another client edits an event after its ETag is read but before update or delete THEN the system sends an unconditional mutation that can silently overwrite or delete that edit.
1.2 WHEN an event write contains a recurrence override THEN the system delegates saving to a library path that may fetch and merge instead of storing the intended resource body.
1.3 WHEN the requested recurrence component is not the first VEVENT THEN the system patches the first VEVENT instead of the matching component.
1.4 WHEN verification or response parsing fails after a successful event write THEN the system can report an error without explaining that the write may already be stored.

### Expected Behavior (Correct)

2.1 WHEN an event update or delete has a pre-read ETag THEN the system SHALL send that ETag as an If-Match precondition.
2.2 WHEN an event update or delete receives HTTP 412 THEN the system SHALL raise PreconditionFailedError within the CalcardError taxonomy, tell the caller to re-read and retry, and SHALL NOT retry unconditionally.
2.3 WHEN an event write contains a RECURRENCE-ID-bearing body THEN the system SHALL store the full intended resource without entering the library's recurrence fetch-and-merge save path.
2.4 WHEN update_event specifies a recurrence_id that matches an existing VEVENT THEN the system SHALL apply the patch only to that matching component.
2.5 WHEN update_event omits recurrence_id and a master VEVENT exists THEN the system SHALL apply the patch only to the VEVENT without RECURRENCE-ID.
2.6 WHEN verification or response parsing raises WriteVerificationError or ProtocolError after a successful event PUT THEN the system SHALL state that the write may already be stored and instruct the caller to re-read before retrying.
2.7 WHEN an event update or delete has no usable pre-read ETag THEN the system SHALL refuse the mutation before sending PUT or DELETE, report that safe concurrency protection is unavailable, and SHALL NOT fall back to an unconditional write.
2.8 WHEN update_event specifies a recurrence_id with no matching stored VEVENT THEN the system SHALL reject the update before writing, explain that no matching occurrence component exists, and instruct the caller to explicitly create an override; it SHALL NOT automatically create an override or change another component.
2.9 WHEN update_event omits recurrence_id and the stored resource has no master VEVENT THEN the system SHALL reject the update before writing and require an explicit occurrence identifier; it SHALL NOT select an override implicitly, even when exactly one override exists.
2.10 WHEN an event was successfully read with a usable ETag but its conditional DELETE receives HTTP 404 because the resource has disappeared THEN the system SHALL treat the deletion as successful and SHALL CONTINUE TO perform applicable absence verification when verify_writes is enabled; HTTP 412 SHALL remain a conflict error.
2.11 WHEN update_event clear_fields includes recurrence_id, irrespective of letter case, THEN the system SHALL reject the update before writing and explain that an occurrence identifier cannot be cleared during update.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN an event mutation succeeds and verify_writes is enabled THEN the system SHALL CONTINUE TO run the applicable read-after-write verification, excluding cleared fields by their lowercase names.
3.2 WHEN an event is updated THEN the system SHALL CONTINUE TO preserve untouched properties, opaque properties, alarms, attendee parameters, and other VEVENT components in the full server resource.
3.3 WHEN an ordinary event is created without recurrence_id THEN the system SHALL CONTINUE TO support the existing create behavior and return its frozen event summary.
3.4 WHEN tool handlers call event clients THEN the system SHALL CONTINUE TO dispatch through asyncio.to_thread and expose only calcard dataclasses and client-wrapped errors.
3.5 WHEN an event URL is supplied THEN the system SHALL CONTINUE TO enforce the configured scheme, host, and normalized principal-path guard before credentials attach.
3.6 WHEN event fields other than recurrence_id are updated or cleared THEN the system SHALL CONTINUE TO apply the existing field validation, library escaping, and explicit-clear precedence to the selected component; recurrence_id selects an occurrence and cannot be assigned or cleared during update.

## Risks

- Missing ETag: high impact, unknown likelihood; refuse update/delete before mutation as approved by the developer; fallback is an actionable error so the caller can investigate server ETag support.
- Recurrence selector ambiguity: high impact, likely with orphan or absent matches; reject absent matches and require an explicit selector for orphan-only resources; fallback is a clear error without writing.
- Fake transport fidelity: high impact, medium likelihood; confirm 412 behavior against Radicale in integration tests; fallback is to leave verification incomplete if the service cannot run.
- Save-path hypothesis: medium impact, medium likelihood; exploration must fail for the stated defect before implementation; fallback is to revise the root cause and reopen design/tasks gates.

## Out of scope

- Task write implementation (00033) and shared machinery convergence (00040).
- If-None-Match on create: the intake calls this optional; deferred to avoid expanding this bugfix.
- Adding further payload logging.


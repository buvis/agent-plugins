# Add If-Match preconditions to event writes via a raw-PUT path

## Problem

Two defects share one root: event mutations delegate the PUT to `caldav`'s `event.save()`.

1. **Lost updates.** `update_event` reads `pre_etag` (`src/calcard_mcp/_caldav_mutation.py:341`)
   but PUTs via bare `event.save()` (`:479`); `delete_event` sends no precondition (`:557`).
   caldav 3.1.0 contains no If-Match support at all. A phone-client edit made between calcard's
   read and PUT is silently erased, and `verify_etag` (post ≠ pre) cannot catch it. The CardDAV
   client already does this right (`carddav_client.py:781-782` PUT, `:896-897` DELETE).
2. **`save()` hijack.** caldav 3.1 `save()` defaults `only_this_recurrence=True`
   (`caldav/calendarobjectresource.py:1063-1070`); when the resource's *first* VEVENT carries
   `RECURRENCE-ID` it never PUTs the body calcard built — it re-fetches the parent by UID,
   client-merges one component, and recursively saves (`:1150-1159`). Traced (not executed)
   consequences: updating an orphan override recurses without a base case;
   `update_event(recurrence_id=…)` on a plain event appends a duplicate override then fails
   verification against the unpatched first VEVENT; `create_event(recurrence_id=…)` with no
   master raises caldav's NotFoundError. No test currently calls create/update with
   `recurrence_id=` — a coverage gap.

Related smaller defect: `update_event` patches whichever VEVENT walks first
(`_caldav_mutation.py:350-352`) instead of selecting by RECURRENCE-ID.

## Solution

Bypass `save()` for event mutations with a raw PUT that mirrors the CardDAV client:

1. `update_event`: PUT `intended_ical` to `event.url` via `self._dav.put(...)` with
   `If-Match: pre_etag` and `Content-Type: text/calendar; charset=utf-8`. Map HTTP 412 to a new
   `PreconditionFailedError` (in `errors.py`, subclass of the existing taxonomy) whose message
   tells the caller to re-read and retry.
2. `delete_event`: send `If-Match: pre_etag` on DELETE; map 412 the same way; keep 404 tolerant
   if that is today's behavior.
3. `create_event`: keep `calendar.save_event` for plain creates, but PUT raw when
   `recurrence_id` is supplied (avoids the hidden GET-merge-PUT). Consider `If-None-Match: *`
   as a nice-to-have.
4. Component selection: in `update_event`, select the VEVENT whose RECURRENCE-ID matches the
   request (or the one *without* RECURRENCE-ID when none is requested) instead of first-walk.
5. Verification error text: when `WriteVerificationError`/`ProtocolError` is raised *after* a
   successful PUT, state "the write may already be stored on the server — re-read before
   retrying" so an LLM retry does not mint duplicates.

## Requirements

### Must have

- `update_event` and `delete_event` send `If-Match` with the pre-read ETag; 412 surfaces as
  `PreconditionFailedError`, never as a silent overwrite.
- No event mutation path routes a RECURRENCE-ID-bearing body through `event.save()`.
- Fail-first regression tests: (a) stale-ETag PUT → 412 → `PreconditionFailedError`; (b)
  `update_event` on an orphan override PUTs the built body verbatim (no fetch-merge recursion);
  (c) `update_event(recurrence_id=…)` patches the matching component, not the first.
- Verification behavior otherwise unchanged (verifier still runs on every write).

### Nice to have

- `If-None-Match: *` on create.
- Missing pre_etag (server returned none): fall back to unconditioned PUT with a WARNING log,
  mirroring the existing empty-post-ETag tolerance.

## Implementation

- **Location**: `src/calcard_mcp/_caldav_mutation.py`, `src/calcard_mcp/errors.py`; tests in
  `tests/test_caldav_update.py`, `tests/test_caldav_etag.py`, integration failure-mode suite.
- **Dependencies**: none new; uses `caldav.DAVClient.put` already available on `self._dav`.
- **Note**: this PRD pays the event-side only; PRD 00033 mirrors it for tasks; PRD 00040 later
  converges the two so the machinery exists once.

## Tasks

### Phase 0: Foundation

- [ ] Pin current behavior: characterize `event.save()` call sites and write the orphan-override
      and `recurrence_id=` tests against the fake DAV layer; watch them fail/expose the gap.

### Phase 1: Core (depends on: Phase 0)

- [ ] Add `PreconditionFailedError`; implement raw-PUT with If-Match in `update_event`,
      precondition on `delete_event`, raw-PUT-on-recurrence_id in `create_event`.
- [ ] Fix VEVENT component selection; adjust verification error text.

### Phase 2: Verification (depends on: Phase 1)

- [ ] Full unit + integration suites pass (Radicale honors If-Match — assert the 412 path in an
      integration test with a concurrent modification).
- [ ] ruff + pyright clean; CHANGELOG entries under Fixed.

## Success Criteria

- A concurrent edit between read and write yields a clear conflict error, never silent loss.
- `recurrence_id` paths are covered by tests and never enter caldav's merge branch.

## Provenance

Evolution assessment 2026-07-08, findings F1, F2, F13 (operational-safety lens), verified at
`_caldav_mutation.py:341,479,557` and installed `caldav/calendarobjectresource.py:1063-1159`.

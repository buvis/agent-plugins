# Conditional Event Writes Bugfix Design

**Status: Design approved — task planning phase.**
Approved input: [bugfix.md](bugfix.md), clauses 2.1–2.11 and 3.1–3.6.

## Overview

Keep the existing event mutation pipeline. Replace unconditional update/delete transport with
conditional requests, bypass recurrence-aware save behavior for override creates, and select the
same VEVENT for patching, verification, and the returned summary. Full resource serialization
remains the only update payload. All policy failures happen before network mutation.

## Glossary

- Bug_Condition (C): unconditional event mutation, recurrence-save delegation, wrong-component
  patching or verification, or an ambiguous post-write failure described below.
- Property (P): a safe conditional mutation of exactly the selected component, with honest errors.
- Preservation: unchanged create behavior, opaque data, field validation/clears, verification,
  layer discipline, thread dispatch, and URL protection.
- Master: VEVENT without RECURRENCE-ID. Override: VEVENT with RECURRENCE-ID.

## Bug Details

### Bug Condition

```text
isBugCondition(operation, resource, selector, response):
    update/delete sent without the resource's pre-read ETag
    OR override body passed through recurrence-merging save()
    OR patched/verified/projected component differs from the requested component
    OR successful PUT followed by an error without stored-write guidance
```

Selection/ETag policies newly approved in clauses 2.7–2.10 extend the correction contract;
they are not asserted to have been historical behavior.

### Examples

- Fetch ETag A; another client writes version B; PUT or DELETE with A receives 412 and leaves B.
- Missing/blank pre-read ETag: error before PUT/DELETE, including when verification is disabled.
- Override appears second: patch it and return its summary, preserving the first component.
- No matching override: reject; no implicit override creation. No master and omitted selector: reject.
- Conditional DELETE receives 404 after a successful fetch: verify absence if enabled, then succeed.
- Override-only create: send the constructed body directly, without an implicit parent fetch/merge.

## Expected Behavior

Clauses 2.1–2.11 are realized by the transport, selector, selected-component verification,
and post-write error context described below. Failures never cause automatic unconditional retries.

### Preservation Requirements

Clauses 3.1–3.6 remain binding. Selection does not rebuild the stored VCALENDAR: unknown
properties, unrelated VEVENTs, VTIMEZONE, VALARM, and attendee parameters remain in the full body.
Temporary single-component calendars are only for comparison/projection and are never PUT.

## Hypothesized Root Cause

Observed in `_caldav_mutation.py`: update attempts to read `event.etag` then calls `event.save()`, delete
calls `event.delete()`, create always calls `calendar.save_event()`, and update stops at the
first VEVENT. Locked caldav 3.1.0 has no `.etag` attribute: its token lives in
`event.props[caldav.elements.dav.GetEtag.tag]`. The old read therefore yields None for real
resources, and the fake `.etag` attribute masks this additional root cause. `_verify_event`, `_verify_typed_fields`, and `_event_to_summary` likewise have
no occurrence selector. The locked caldav 3.1.0 source delegates a recurrence-bearing save
through its merge branch. Recursion and merge outcomes require exploration tests before a fix.

If exploration passes on unfixed code or fails for an unrelated reason, stop, record the observed
result, revise this hypothesis, and reopen design/tasks approval. Do not force a failing test.

## Correctness Properties

### Property 1: Bug Condition

For C, updates/deletes use the captured ETag or refuse mutation; 412 is a typed conflict, override
writes bypass save merging, and patch/verification/projection agree on the target. Post-success
errors warn that the write may already be stored. Validates 2.1–2.11.

### Property 2: Preservation

Outside the corrected behavior, preserve the full stored resource and existing field semantics,
ordinary creates, enabled verification, frozen summaries, thread dispatch, and URL guards.
Validates 3.1–3.6. New selector policies are exclusions from equivalence, not preservation claims.

## Fix Implementation

### Module placement

- New `src/calcard_mcp/_caldav_write.py`: private client-layer transport and component helpers.
- Edit `src/calcard_mcp/_caldav_mutation.py`: orchestrate selected mutations and verification.
- Edit `src/calcard_mcp/errors.py`: add `PreconditionFailedError(CalcardError)`.
- Edit `src/calcard_mcp/tools/calendar.py`: describe update's selector semantics and normalize
  recurrence_id with the existing calcard `make_aware` helper at the tool boundary, using the
  resolved account timezone before asyncio.to_thread. Aware input keeps its instant; naive input
  is anchored exactly once. Retain signature, account checks, URL guard and thread dispatch.
- Edit `tests/conftest.py` only as needed to model raw DAV responses; migrate affected write mocks
  in event tests, including ETag/error/full-field/clear tests. Task mocks keep existing behavior.
- Edit `tests/test_caldav_update.py`, `tests/test_caldav_etag.py`, and
  `tests/integration/test_failure_modes.py`; add focused coverage in
  `tests/test_caldav_conditional_writes.py` and `tests/test_caldav_recurrence_writes.py`.
- Edit `CHANGELOG.md` and the now-outdated event-write/recurrence invariants in `AGENTS.md`.

Private helper placement keeps `_caldav_mutation.py` below the repository's established size
boundary and prevents an unrelated convergence with tasks/contacts (00040).

### Components and interfaces

Planned exact private contracts:

```python
def event_etag(event: Any) -> str | None: ...
def reload_event_resource(event: Any, *, uid: str) -> None: ...
def require_event_etag(etag: Any, *, uid: str) -> str: ...
def select_event_component(calendar_data: Any, *, uid: str,
                           recurrence_id: datetime | None, fallback_tz: str) -> Any: ...
def selected_event_ical(calendar_data: Any, component: Any) -> str: ...
def put_event_body(dav: Any, *, resource_url: str, body: str,
                   pre_etag: str | None, uid: str) -> Any: ...
def delete_event_body(dav: Any, *, resource_url: str, pre_etag: str, uid: str) -> Any: ...
```

These functions live entirely in the client layer. `Any` represents the untyped library boundary;
no library object crosses into tools. Public create/update/delete signatures stay as they are.

`event_etag` reads `event.props.get(dav.GetEtag.tag)`, never `.etag`; return a string
or None. `reload_event_resource` removes that cached property before `event.load()`, wrapping
load failures as ProtocolError. This ensures body and ETag come from the fresh read, including
when the library reload uses its supported fallback; no old cached token can substitute for
a missing fresh one. Use this reload before capturing the pre-token and before verification.

`require_event_etag` accepts a nonblank string other than `*` and preserves the server value;
missing, non-string, blank, or wildcard input raises ProtocolError before mutation. A weak ETag
is sent unchanged: the server's strong If-Match evaluation decides whether it conflicts.
`PreconditionFailedError` is reserved for HTTP 412, with read-and-retry guidance.

### Selection and data model

Select VEVENTs with the requested UID. Without selector require exactly one master; with selector
require exactly one normalized recurrence match. Zero matches produce the approved actionable
ProtocolError; multiple matches or malformed identifiers produce ProtocolError before mutation.
No new frozen data model is needed.

Compare timezone-aware request datetimes in UTC; reject naive selectors below the tool boundary.
Use existing `extract_recurrence_id` conventions for server DATE/floating/TZID values, with the
master DTSTART anchor when present and account fallback otherwise. Build an isolated master
calendar and parse its summary; obtain the anchor with `resolve_tz_name(master.start.tzinfo,
fallback_tz)`. A master whose bounds cannot be parsed raises ProtocolError. Without a master,
use fallback_tz explicitly. Pass that anchor as `master_anchor_tz_name` to both
`extract_recurrence_id` and selected-summary parsing, including floating orphan IDs; do not
omit it and accidentally stamp those values UTC. A DATE-valued ID
matches its midnight under that existing anchor convention; do not emit a DATE-TIME replacement
merely because the selector is a datetime. Preserve its original value and parameters.

`recurrence_id` in update is a selector, not an assignment: remove the old pop/add rewrite. Create
retains its RECURRENCE-ID value behavior. Before mutation, reject any clear_fields entry
whose lowercase name is recurrence_id with ValueError: "recurrence_id cannot be cleared during
update; it identifies the occurrence". Apply this even when the selected component is a master.
Keep the generic apply_event_clears mapping unchanged for other consumers; enforce this restriction
in the event update path and remove recurrence_id from that tool's documented clearable fields.

### Transport and control flow

1. Update/delete fetch the resource, reload through `reload_event_resource`, and capture
   `event_etag(event)` alongside the fresh body; require a usable ETag before mutation.
2. Update parses the full resource, selects the target, applies existing pop/add emitters,
   validates merged dates, applies explicit clears, and serializes the full calendar.
3. Update sends `dav.put(resource_url, body, headers)` with exact `If-Match` and
   `Content-Type: text/calendar; charset=utf-8`; never calls `event.save()`.
4. Delete sends `dav.request(resource_url, "DELETE", "", {"If-Match": pre_etag})`.
   The locked library's `delete(url)` takes no headers; do not invent `delete(headers=...)`.
5. For override create, generate the existing UUID UID, join its quoted `.ics` filename to the
   calendar URL using caldav's URL helper, construct an unsaved `caldav.Event` with that URL,
   parent/calendar and body, and raw-PUT the body without an If-Match. Ordinary create retains
   `calendar.save_event`. No If-None-Match behavior is added.
6. Helpers inspect DAVResponse.status: PUT accepts 200/201/204; DELETE accepts 200/202/204/404.
   A 412 raises PreconditionFailedError; other statuses raise ProtocolError. Transport exceptions
   wrap once in the helper. Never include response bodies or credentials in diagnostics.
7. After accepted PUT, update local event data; when verification is enabled reload through `reload_event_resource`,
   then verify/project the intended component. An accepted DELETE always runs the existing
   absence check when enabled, including accepted 404. Initial fetch failure remains an error.

### Verification and returned summary

The read-back resource must stay full-fidelity. Build temporary calendars through library APIs:
copy VCALENDAR properties and timezone components, then include only the chosen VEVENT. Reuse
`verify_fields`, `parse_vevent_to_summary`, and `verify_summary_fields` on those temporary bodies.
Use identical account, resource URL, and anchor context for intended and actual summaries.
Field-diff exclusions continue using lowercase cleared names. Selected summary drives the return
value even when verification is disabled. Master/override order is irrelevant.

Read-back selection uses the intended post-patch UID and RECURRENCE-ID. A missing or ambiguous
component fails verification; it must never silently use the first component. Preserve the existing
post-write ETag fallback using `event_etag(event)` after clearing/reloading: absent post-ETag
warns, unchanged nonempty ETag fails. Preserve the pre-read token separately; update the existing
ETag verifier and diagnostic context to read props rather than `.etag`. This is distinct
from mandatory pre-write ETags. No POST/PUT response ETag replaces the old pre-read ETag for If-Match.

### Error handling

Catch transport errors in helpers, not tools; inspect HTTP statuses outside that catch so typed
conflicts are not rewrapped. Missing ETag and selection errors are ProtocolError with no PUT/DELETE.
After successful PUT, wrap only verification/projection WriteVerificationError or ProtocolError
with: "the write may already be stored on the server — re-read before retrying". Preserve subtype,
field_diffs and exception chaining. Apply this to ordinary and override creates and updates.
Do not label pre-write/HTTP-412 failures as successful writes.

### Security, operation, and rollout

Keep the scheme/host/principal guard, existing DAV credentials, TLS/configuration and bounded
request behavior. Add no payload logs or automatic retries. Human operator remains the repository
owner. Existing returned errors and tests provide observability. Server storage, backup and restore
remain the operator's existing service responsibility; this fix introduces no persistence schema.

Deploy as a bugfix with unchanged MCP signatures and a CHANGELOG entry documenting selector
semantics, refused unsafe writes, conflicts and post-write guidance. No database migration.
Rollback is code revert with release notes: it restores unsafe unconditional writes, so pause
mutations during rollback rather than silently rely on the old conflict protection.

### Alternatives considered

1. Smallest diff: retain save() and only add headers where available. Rejected: recurrence merging
   still alters the body and the library delete wrapper cannot carry the precondition.
2. Chosen: private raw-DAV helpers plus selected-component verification. Added size buys a single
   tested response mapping and alignment of patch, verification and return behavior.
3. Replace the transport or converge all clients now. Rejected: crosses 00033/00040 boundaries,
   broadens regression risk, and is unnecessary for these event contracts.

### Reuse inventory

Searched `select|component|find|match`, `request|conditional|precondition|put|delete`, and recurrence
`anchor|extract|parse`. Known-present control terms: `update_event`, `verify_fields`, `pre_etag`.

- `_caldav_mutation.py`: reuse full parse/emit/clear pipeline and existing enabled verification.
- `_ical_parse.py:extract_recurrence_id` and `ical.py:parse_vevent_to_summary`: reuse timezone/DATE
  normalization; neither currently selects a write target.
- `verifier.py:verify_fields`, `verify_summary_fields`: reuse comparisons on isolated projections.
- `_caldav_base.py:_touched_typed_fields`: reuse touched field list; selector identity is verified
  by target selection rather than rewritten as a new property.
- `carddav_client.py`: conditional PUT/DELETE precedent. Keep its implementation unchanged.
- `caltodo_client.py`: same unconditional save/delete defect remains; record for 00033, no fix here.
- Locked caldav 3.1.0 `DAVClient.put`, `DAVClient.request`, `caldav.Event`, and URL.join: use existing
  client APIs. Source inspected in local cached distribution; no newer-version assumptions.

## Testing Strategy

### Validation Approach

Keep Kiro's four-task bugfix order: exploration, preservation, implementation, full checkpoint.
Record real outcomes under tasks. Unit tests control transport status/body/ETags explicitly;
MagicMock defaults are not evidence of a successful HTTP response. Model tokens in
`props[dav.GetEtag.tag]`, not a fictional `.etag`. Add a real caldav.Event boundary test with
stubbed DAV responses for pre-token acquisition and cached-token removal on ETag-less read-back.

### Exploratory Bug Condition Checking

Fail-first cases: missing/stale pre-ETag update and delete; override update/save bypass; raw override
create; non-first component selection; post-write error guidance. Capture transport calls and stored
body, not just exceptions. A model test of save merging is distinguished from a real caldav save
test. Tests must expose the stated defect on original production code before implementation.

### Fix Checking

Re-run the same exploration tests unchanged. Add boundary cases for 2.7–2.10, duplicate/malformed
matches, normalized timezone/DATE IDs, and verify_writes disabled. Verify 412 never triggers a retry,
delete 404 preserves absence checks, and selected-component returned summaries match verification.

### Preservation Checking

Observe passing baseline tests before the fix: ordinary create, complete opaque-resource rewrites,
field clears/escaping/date validation, lowercased clear exclusions, post-ETag fallback, thread
dispatch, and URL checks. Migrate mocks from save to raw PUT only where transport assertions
change; do not weaken acceptance or change preservation expectations to force a pass.

### Unit Tests

Use focused new conditional/recurrence write suites and the existing affected event suites.
Assert exact If-Match, target URL, request body, response mapping, and zero mutation on policy
failures. Read-back reorders VEVENTs to demonstrate selectors do not depend on component order.
Test recurrence_id clear rejection for lowercase/mixed-case names, with and without an explicit
selector, and assert zero PUT. Other clear operations retain their existing expectations.

### Property-Based Tests

Not applicable: deterministic counterexamples and targeted timezone/component-order cases
cover this bounded bugfix; no new property-testing dependency is needed.

### Integration Tests

Radicale: concurrent update between pre-read and PUT/DELETE must cause 412 and preserve the new
body. Exercise ordinary and orphan override persistence, selected override updates, enabled
verification, and a deletion race returning 404. Require the full unit/integration suites,
Ruff lint/format, and Pyright; unavailable infrastructure leaves the checkpoint uncompleted.

## Risks and edge cases

- Recurrence identity clearing: high impact, medium likelihood; reject it before mutation as
  explicitly approved by the developer; fallback is an actionable error, never a second master.
- Weak/missing ETags: high impact, server-dependent likelihood; missing fails locally and weak
  tokens rely on server If-Match evaluation; fallback is a clear error, no unconditional retry.
- Next change 00033: high impact, likely; shared error class is reusable but event helper scope
  stays explicit; fallback is a separate reviewed task implementation.
- Next change 00040: medium impact, likely; helpers are private and contained; fallback is an
  independently specified extraction rather than premature shared abstractions.
- Next change HTTP transport: high impact, likely; preserve 00031 guard before credentials;
  fallback is to block transport release if guards regress.

## Requirement traceability

| Clauses | Design element |
|---|---|
| 2.1, 2.2, 2.7, 2.10 | ETag guard, raw transport/status mapping and deletion absence check |
| 2.3, 3.3 | Override raw create/update, ordinary create preservation |
| 2.4, 2.5, 2.8, 2.9 | UID/occurrence selector and pre-write rejection |
| 2.6 | Post-success verification/projection error context |
| 2.11, 3.1, 3.6 | Pre-write identity-clear rejection, other field clears and selected comparison |
| 3.2 | Full server-body mutation; projection-only temporary calendar |
| 3.4, 3.5 | Existing tool dispatch/layers/URL guards and client-only helpers |

## Open decisions

None. Developer chose prohibition; requirements 2.11 and 3.6 record the approved amendment.

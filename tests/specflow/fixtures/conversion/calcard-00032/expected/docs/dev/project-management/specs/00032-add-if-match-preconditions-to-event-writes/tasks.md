# Implementation Plan

**Status: Draft tasks — developer approval required before execution.**
Inputs: approved [bugfix.md](bugfix.md) and [design.md](design.md).

The four top-level tasks preserve Kiro's bugfix order. Execute sequentially; implementation
starts only after exploration has demonstrated the defects and preservation has established
passing baselines. No production changes have been made for this spec.

- [ ] 1. Write bug condition exploration tests before implementing the fix
  - **Property 1: Bug Condition** — expose unsafe writes and wrong recurrence targeting.
  - **CRITICAL**: These tests MUST FAIL on unfixed production code for the stated defect.
  - **DO NOT attempt to fix the test or the code when it fails**; record the counterexample.
  - **EXPECTED OUTCOME**: Tests FAIL with behavior/assertion failures, not collection errors.
  - Depends on: none.
  - Location: new `tests/test_caldav_conditional_writes.py`, new
    `tests/test_caldav_recurrence_writes.py`; test-local fixtures and, only if necessary,
    additive support in `tests/conftest.py` that does not change existing test behavior.
  - Reuse: FakeCalDAV, build_fake_event, full-resource iCalendar fixtures, existing account config.
  - Details: model real `props[dav.GetEtag.tag]` and explicit DAVResponse status/body/headers.
    Add tests for stale update/delete tokens producing 412 without retries; missing pre-token
    refusing mutation; non-first override targeting and master targeting; orphan override
    persistence through raw PUT; raw override create; post-PUT error guidance; missing-match and
    omitted orphan selector rejection; delete-race 404 with enabled absence verification;
    case-insensitive recurrence_id clear rejection. Check exact request headers and stored body.
    Include a real caldav.Event with a stubbed DAV client, without a fake `.etag`, to expose
    incorrect token acquisition and cached-token retention. Do not import future helpers or
    PreconditionFailedError at collection time: assert the caught error's type/name until the
    public class exists, so failure documents wrong behavior rather than a missing import.
  - Separate direct library save-path reproduction from a fake transport model. If actual caldav
    does not exhibit the hypothesized recursion/merge effect, record the result and stop that
    fix path for design correction; a model alone is not proof of a library defect.
  - Verify: run each new regression against original production code; record test names,
    actual failure, and why it matches the hypothesis under this task's Outcome field.
    An unexpectedly passing exploration test or unrelated failure reopens design/tasks approval.
  - _Requirements: 1.1, 1.2, 1.3, 1.4; correction cases 2.1–2.11_

- [ ] 2. Write preservation tests before implementing the fix
  - **Property 2: Preservation** — legitimate behavior and untouched resource content survive.
  - **EXPECTED OUTCOME**: Tests PASS on unfixed code, establishing observed baselines.
  - Depends on: 1.
  - Location: `tests/test_caldav_update.py`, `tests/test_caldav_etag.py`,
    `tests/test_ical_opaque_preservation.py`, `tests/test_clear_fields.py`,
    new `tests/test_caldav_recurrence_writes.py`; existing tool/URL suites as read-only evidence.
  - Reuse: ordinary create fixtures, opaque property/VALARM/ATTENDEE tests, enabled/disabled
    verification tests, clear/escaping/date validation cases, thread and URL-guard tests.
  - Details: observe ordinary create output, complete-resource preservation, untouched VEVENTs,
    field validation and other clears, lowercase verification exclusions, missing post-ETag
    warning and unchanged post-token failure. Preserve behavioral assertions when transport
    mocks later migrate. Recurrence_id assignment/clear and unsafe unconditional writes are
    explicitly excluded from equivalence by approved requirements; do not pin them as baselines.
  - Verify: `uv run pytest tests/test_caldav_update.py tests/test_caldav_etag.py
    tests/test_ical_opaque_preservation.py tests/test_clear_fields.py tests/test_accounts.py
    tests/test_tool_surface.py`; run new preservation cases separately from failing exploration.
    Record actual passing cases under this task's Outcome field before task 3 starts.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 3. Implement conditional, occurrence-selected event writes
  - Depends on: 1, 2, both with recorded observed outcomes.
  - _Bug_Condition: unsafe mutation or wrong patch/verification/projection target_
  - _Expected_Behavior: approved clauses 2.1–2.11_
  - _Preservation: clauses 3.1–3.6, with approved recurrence identity exclusions_

  - [ ] 3.1 Implement the approved design in independently verifiable slices

    - [ ] 3.1.1 Add real ETag and conditional transport helpers
      - Depends on: 1, 2.
      - Location: new `src/calcard_mcp/_caldav_write.py`, `src/calcard_mcp/errors.py`,
        new helper-focused cases in `tests/test_caldav_conditional_writes.py`.
      - Reuse: existing DAVClient and CalcardError taxonomy; CardDAV conditional-write precedent.
      - Contract (verbatim from design):
        ```python
        def event_etag(event: Any) -> str | None: ...
        def reload_event_resource(event: Any, *, uid: str) -> None: ...
        def require_event_etag(etag: Any, *, uid: str) -> str: ...
        def put_event_body(dav: Any, *, resource_url: str, body: str,
                           pre_etag: str | None, uid: str) -> Any: ...
        def delete_event_body(dav: Any, *, resource_url: str, pre_etag: str, uid: str) -> Any: ...
        ```
      - Details: add PreconditionFailedError(CalcardError); read GetEtag from props, clear it
        before load, and wrap load failures once. Reject missing/non-string/blank/wildcard
        pre-tokens. Preserve usable values, including weak tokens. PUT headers include exact
        If-Match when supplied and text/calendar content type. DELETE uses DAVClient.request
        with headers, not delete(headers=...). Map 412 outside transport exception wrapping;
        accept the design's explicit success statuses and never retry unconditionally.
      - Risk: new public conflict subtype and write preconditions; verify exact mapping and
        preservation of stored competing edits, with no response-body logging.
      - Acceptance criteria: 2.1, 2.2, 2.7, 2.10; infrastructure for 3.1 and 3.4.
      - Verify: helper tests for exact headers/statuses, real-library props access, cached-token
        removal, absent-token rejection, and exception chaining; module Ruff/Pyright checks.

    - [ ] 3.1.2 Add recurrence selection and projection helpers
      - Depends on: 3.1.1.
      - Location: `src/calcard_mcp/_caldav_write.py`,
        `tests/test_caldav_recurrence_writes.py`.
      - Reuse: extract_recurrence_id, parse_vevent_to_summary, resolve_tz_name, library calendar
        copying/serialization. No generic verifier/parser API changes.
      - Contract (verbatim from design):
        ```python
        def select_event_component(calendar_data: Any, *, uid: str,
                                   recurrence_id: datetime | None, fallback_tz: str) -> Any: ...
        def selected_event_ical(calendar_data: Any, component: Any) -> str: ...
        ```
      - Details: match UID plus normalized occurrence identity, or exactly one master when no
        selector is supplied. Reject absent/duplicate/malformed matches and naive request
        selectors. Derive the master anchor through an isolated summary and resolve_tz_name;
        pass it, or explicit account fallback for orphans, to normalization and projection.
        Preserve original DATE/TZID identity parameters. Temporary calendars retain calendar
        properties and timezones but contain only the selected VEVENT; they are never write bodies.
      - Risk: new occurrence predicate; test DATE, floating, timezone-aware, orphan, duplicate,
        malformed, absent-match and component-order boundaries.
      - Acceptance criteria: 2.4, 2.5, 2.8, 2.9; infrastructure for 3.2 and 3.6.
      - Verify: focused helper selection/projection tests and module Ruff/Pyright checks.

    - [ ] 3.1.3 Integrate conditional update/delete and selected verification
      - Depends on: 3.1.1, 3.1.2.
      - Location: `src/calcard_mcp/_caldav_mutation.py`, `src/calcard_mcp/tools/calendar.py`,
        `tests/conftest.py`, affected update/delete/ETag/error/clear/full-field event tests.
      - Reuse: full server parse/pop-add/clear pipeline, touched field list, verify_fields,
        verify_summary_fields, frozen summary parser, existing absence verifier.
      - Contract: call approved helper signatures above; public mutation signatures unchanged.
        Normalize recurrence_id once with make_aware at the tool boundary before to_thread.
        Reject recurrence_id clearing case-insensitively before mutation, with ValueError:
        "recurrence_id cannot be cleared during update; it identifies the occurrence".
      - Details: fresh body/token read; select target; preserve its identifier instead of
        assigning the selector; retain existing validation and other clears. Raw-PUT the full
        serialized body with pre-token. Raw-DELETE conditionally; 404 success still verifies
        absence, initial lookup errors remain errors. Verify and return the chosen component,
        using props for ETags and fresh token reads; do not project the first VEVENT. After
        accepted PUT, preserve exception subtype/diffs/chaining while adding stored-write
        guidance. Apply equivalent ordinary-create verification plumbing where shared helper
        changes require it. Update tool docs and only the affected event mock interactions.
      - Coupling: patch selection, verification, returned summary, boundary conversion, and
        affected mocks stay together; splitting these would leave wrong-component behavior.
      - Risk: public selector/clear semantics and conditional writes; zero-mutation assertions,
        reordered read-back and full-fidelity preservation prove the boundary.
      - Acceptance criteria: 2.1, 2.2, 2.4–2.11; 3.1, 3.2, 3.4, 3.5, 3.6.
      - Verify: update/delete regressions plus all affected existing event/tool tests; opaque
        property preservation, enabled/disabled verification, and naive-selector timezone cases.

    - [ ] 3.1.4 Persist override creates directly and report post-write failures honestly
      - Depends on: 3.1.3.
      - Location: `src/calcard_mcp/_caldav_mutation.py`,
        `tests/test_caldav_recurrence_writes.py`, affected create/error/full-field event tests.
      - Reuse: existing UUID UID and build_event_ical, caldav.Event constructor, URL.join,
        put_event_body, selected projection/verification and existing ordinary save_event path.
      - Contract: override create uses put_event_body with pre_etag=None; ordinary create
        keeps calendar.save_event. After accepted PUT, errors include:
        "the write may already be stored on the server — re-read before retrying".
      - Details: construct an unsaved resource with quoted UID filename and existing calendar
        parent, PUT exact built body, and run enabled selected verification. No save() on a
        recurrence body, implicit parent merge, or added If-None-Match. Preserve subtype and
        field_diffs in post-success errors for ordinary and override creates and updates.
      - Risk: recurrence persistence and retry guidance; check exact body, no hidden merge,
        and no success-warning on pre-write failures.
      - Acceptance criteria: 2.3, 2.6; 3.1, 3.2, 3.3.
      - Verify: raw override-create/orphan-update regressions, ordinary-create preservation,
        selected returned summaries and post-success reload/parse/diff error cases.

    - [ ] 3.1.5 Add real-service races and record changed behavior
      - Depends on: 3.1.4.
      - Location: `tests/integration/test_failure_modes.py`, `CHANGELOG.md`, `AGENTS.md`.
      - Reuse: existing Radicale fixtures, second-client mutation, full-resource reads.
      - Details: deterministically modify the resource between pre-read and mutation to prove
        update/delete 412 and competing-body survival; test deletion 404 after pre-read and
        enabled absence verification. Exercise real recurrence/orphan raw persistence and
        selected override verification. Record event fixes under Fixed and update event-specific
        invariants; keep the unresolved task gap explicitly assigned to 00033. Record the
        CardDAV/task twin check without extending event implementation into those clients.
      - Acceptance criteria: 2.1–2.11, 3.1–3.6, using applicable integration/preservation cases.
      - Verify: focused Radicale tests plus document consistency check; source changes in a
        feat/fix commit include the CHANGELOG update in the same commit.

  - [ ] 3.2 Verify the exploration tests now pass
    - Depends on: 3.1.1–3.1.5.
    - Re-run the SAME task-1 cases, preserving their behavioral assertions and counterexamples.
    - Verify: both new regression suites, including real-library-object boundary cases.
    - _Requirements: 2.1–2.11_

  - [ ] 3.3 Verify preservation tests still pass
    - Depends on: 3.2.
    - Re-run the SAME task-2 baselines. Narrow a failing fix rather than weaken preservation.
      If narrowing needs a design correction, reopen design/tasks approval.
    - Verify: task-2 cases and affected ordinary create/update/delete/full-field/clear/error/tool
      suites, including opaque body preservation and URL/thread protections.
    - _Requirements: 3.1–3.6_

- [ ] 4. Checkpoint — verify the full suite and completion evidence
  - Depends on: 3.2, 3.3.
  - Location: verification evidence under this task, intake `qa-log.md`, and
    `docs/dev/project-management/reviews/2026-10-03-specflow-concept-validation.md`.
  - Verify: `uv run pytest`; `uv run pytest -m integration`; `uv run ruff check .`;
    `uv run ruff format --check .`; `uv run pyright`. Record actual results and any skipped
    cases, with their relevance. Missing Docker/dependencies is not a passing checkpoint.
  - Review: hand off completion review to a fresh session as repository instructions require;
    do not run that review from the build session or claim its findings before it runs.
  - Completion evidence: every implementation/test task has its owned verification and
    Outcome; no unresolved blocker or unapproved design change; CHANGELOG/invariants describe
    the resulting behavior; concept report records gate/review/testing findings and remaining
    limits of the manual plugin trial. Preserve unrelated working-tree changes and clean only
    temporary assets created by this work. Do not commit/push without authorization.
  - _Requirements: 2.1–2.11, 3.1–3.6_

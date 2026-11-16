# Specflow pilot: 00032

## Intake decisions (2026-10-03)

- Selected next by lowest intake number after completed 00031. The roadmap path named in
  AGENTS.md is absent from this checkout; the lowest-number rule is the available authority.
- Bugfix recommended: input describes lost updates, recurrence persistence, and component-selection defects.
- Standard recommended: concurrency, data loss, recurrence algorithms, and a public error contract.
- Requirements-first recommended: the input describes defects and needed behavior, with solution suggestions.
- No spike needed: defects and affected code are identifiable; bounded policy choices remain.
- Original intake preserved in `idea.md` and moved when the first requirements artifact was written.
- No design, tasks, or implementation approval is inferred from the request to test full specflow.

## Review: bugfix.md 2026-10-03

- Comprehension: distinguish observed unconditional writes/first-component selection from unexecuted library recursion hypotheses.
- Completeness: missing-ETag, absent-recurrence-match, and delete-404 policies need resolution; questions remain open.
- Coherence: recurrence_id currently documents assignment, while intake requires selection; surfaced rather than silently choosing a new contract.
- Integrity: reproduction has not run; no fail-first result or completion is claimed.
- Feasibility: CardDAV's conditional-write path provides a local precedent; recurrence verification will need design attention.
- Evolvability: task twin is explicitly deferred to 00033; shared extraction is deferred to 00040.
- Scope: optional create precondition moved out of scope; no mandatory acceptance silently dropped.
- Review status: requirements draft has open contract questions; approval not requested yet.

## Q1 — Missing ETag policy (2026-10-03)

- Question: Refuse update/delete without a server ETag, or permit an unconditional write with a warning?
- Answer: Developer selected option 1: refuse the write.
- Decision: Added requirement 2.7; no unconditional fallback. This supersedes the intake's optional fallback suggestion.
- Review status: Missing-ETag contract resolved; recurrence-selection and delete-404 questions remain open.

## Q2 — Missing recurrence match (2026-10-03)

- Question: Reject an update with no matching stored occurrence component, or create an override automatically?
- Answer: Developer selected option 1: reject the update.
- Decision: Added requirement 2.8; no implicit override creation or mutation of another component. Tell the caller to explicitly create an override.
- Review status: Explicit-selector absent-match contract resolved. Omitted-selector behavior for orphan-only resources and delete-404 policy remain open.

## Q3 — Omitted selector on an orphan-only resource (2026-10-03)

- Question: Require an occurrence identifier, or select an override automatically when exactly one exists?
- Answer: Developer selected option 1: reject and require an occurrence identifier.
- Decision: Added requirement 2.9; no implicit override selection, including a single-override resource.
- Review status: Recurrence-selection questions resolved. Delete-404 policy remains open.

## Q4 — Delete race returning HTTP 404 (2026-10-03)

- Question: Treat a resource disappearing between read and DELETE as success, or report an error?
- Answer: Developer selected option 1: success because the requested event is already gone.
- Decision: Added requirement 2.10, limited to a successful pre-read with usable ETag followed by DELETE 404. Initial lookup errors are not silently reclassified; HTTP 412 remains a conflict. Absence verification remains enabled.

## Review: bugfix.md 2026-10-03 — final requirements pass

- Completeness: all four policy questions answered; 2.7–2.10 capture the developer decisions.
- Coherence: explicit recurrence selector targets an existing component; omitted selector targets a master; absent matches reject without writing.
- Integrity: code observations and unexecuted recurrence hypotheses remain distinguished; no test results invented.
- Feasibility: conditional transport and selected-component verification require design work; no production implementation attempted.
- Evolvability: task changes stay with 00033; convergence stays with 00040.
- Recap: four contract questions resolved, no open requirements blockers or unresolved markers. Requirements approval pending; design and tasks remain missing.

## Requirements approval (2026-10-03)

- Developer explicitly approved the resolved requirements baseline and requested design drafting/review.
- Recorded approval against the current canonical hash after updating the editorial status line.
- No design or tasks approval inferred.

## Review: design.md 2026-10-03 — isolated pre-pass

- Tier: elevated for concurrency, data loss, public semantics and recurrence selection.
- Shared fifteen-item cardinal-sin list supplied in full to an isolated reviewer.
- Pass 1: zero cardinal sins, three blockers, one non-blocker, one question.
- Blocker: nonexistent event.etag API | replaced with props/GetEtag accessor and fresh body/token read | resolved.
- Blocker: cached pre-token survives ETag-less reload | clear GetEtag before reload; capture pre-token separately | resolved.
- Blocker: naive selector conversion absent at tool boundary | specified make_aware before dispatch and below-boundary rejection | resolved.
- Non-blocker: anchor plumbing underspecified | isolated master summary, resolve_tz_name, explicit anchor/fallback in both normalization and projection | resolved.
- Question: clearing recurrence_id can turn an override into a second master | awaiting developer decision.
- Verification pre-pass requested on corrected design; no design approval recorded.

## Review: design.md 2026-10-03 — verification pre-pass

- Pass 2: zero cardinal sins, zero blockers, zero remaining non-blockers, one existing question.
- Confirmed fixes: real ETag property accessor, cached-token removal, tool-boundary selector coercion, explicit recurrence anchor plumbing.
- Open decision: clearing recurrence_id; resolve before design approval. Prohibition changes clause 3.6 and requires renewed requirements approval.
- Local checks: requirements approval/hash current, design hash/required headings/links valid, whitespace clean. These are pilot checks, not production plugin validation or runtime test results.
- No design/tasks approval or implementation inferred.

## Q5 — Clearing an occurrence identifier (2026-10-03)

- Question: Prohibit clearing recurrence_id during update, or preserve it with collision checks?
- Answer: Developer selected option 1: prohibit clearing during update.
- Decision: Added 2.11 and narrowed 3.6; case-insensitive rejection before PUT, even on a master. Other clears remain preserved.
- Approval: This explicit selection approves the stated requirements amendment; requirement approval hash refreshed. No whole-design approval inferred.
- Design review: Existing open question resolved; deterministic pre-write ValueError follows the existing required-field clear policy. No open decision markers remain.
- Next gate: Developer approval of the complete reviewed design; tasks remain missing.

## Design approval (2026-10-04)

- Developer explicitly approved the reviewed design after the recurrence clear decision was resolved.
- Editorial status updated and approval recorded against its canonical hash; requirements approval remains current.
- Task drafting gate open; task/implementation approval not inferred.

## Task-plan review (2026-10-04)

- Four native bugfix tasks preserved: exploration, preservation, implementation, checkpoint.
- All 2.1–2.11 correction clauses trace to exploration/fix tests; all 3.1–3.6 preservation clauses trace to passing-baseline and recheck tasks.
- Dependencies derive from test-first obligations and helper/caller flow in the approved design; no guessed dependency on 00033/00040.
- Implementation slices: ETag/transport, selection/projection, coupled update/delete verification/tool conversion, override create, integration/documentation. Each has bounded locations and owned checks.
- Coupled update/verification/projection/tool/mock slice stays together to avoid wrong-component behavior between partial changes. Helper slices have independently runnable helper tests before caller integration.
- Design contract signatures copied into applicable tasks; no new implementation contract or open design decision introduced.
- Baseline mocks may migrate but their behavior assertions must remain unchanged; real-library boundary coverage is mandatory because current mocks concealed the ETag defect.
- Task 4 keeps infrastructure failures incomplete and requires fresh-session completion review.
- Local checks: approved upstream hashes current, exactly four top-level tasks, no checked task or completion criterion, required same-test rechecks present, whitespace clean.
- Recap: four stages, five implementation slices, no planning blocker; tasks approval pending. No implementation or verification run claimed.

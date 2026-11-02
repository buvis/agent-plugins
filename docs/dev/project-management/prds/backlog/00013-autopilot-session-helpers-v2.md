---
default_model: opus
model_tier_rationale: Safety predicates, pre-spawn ordering and behavioral equivalence require judgment rather than transcription.
lane: full
rework_cap: 2
design: run
doubt_reviewer: fable
---
# Autopilot session-local helpers v2

Filename: 00013-autopilot-session-helpers-v2.md. This is the same feature identity as v1, preserved as cap-regression history; it does not reset or overwrite v1 reviews, attempts, deferrals or implementation. Preserve the historical task snapshot/report and prior reviews without importing all completed v1 tasks into the new plan. Mark v1 superseded only after v2 passes its fresh full completion review. Only corrective tasks below remain to implement. No publication, live installation, migration, retirement or automatic push is authorized by this PRD.

Source: docs/dev/project-management/prds/hold/00013-autopilot-session-helpers-v1.md; docs/dev/project-management/designs/00013-autopilot-session-helpers-v1-design.md; docs/dev/project-management/autopilot/reports/00013-cap-regression-recovery.md. V1 review-03 is complete and v1 is on hold after cap_regression. The installed recovery handler permits this v2 against the resulting stubs; preserve the original feature number and all historical evidence. The coordinator selects v2 explicitly; this specification grants no worker PRD lifecycle authority.

Review evidence: docs/dev/project-management/reviews/00013-autopilot-session-helpers-v1-review-03.md:40-71. T1 addresses confirmed highs R7/R8/R9; T2 addresses supported mediums R2/R3 and related R10/R12; T3 addresses R13; T4 addresses R16/R23 and refreshes delivery evidence. R6 is verified ordering hygiene, explicitly discarded as a bypass claim; include its inexpensive containment-before-read correction under T2 without reopening a false unresolved High. Related single-voice findings are selected here under standing corrective authority because their concrete evidence supports them, not because their v1 ledger disposition is erased.

Recovery bindings: docs/dev/project-management/prds/hold/00030-triage-cycle-3-cap-out-with-repair-regressions-v1.md:1-15 is the cap-regression stall stub; docs/dev/project-management/prds/hold/00031-triage-external-git-metadata-directories-are-no-v1.md:1-15 binds R7; docs/dev/project-management/prds/hold/00032-triage-the-new-scoped-line-blanks-the-prd-when-v1.md:1-15 binds R8; docs/dev/project-management/prds/hold/00033-triage-the-shared-review-context-id-md-is-still-v1.md:1-15 binds R9. Preserve these records and all previously settled unrelated deferrals; the coordinator owns their eventual supersession/closure. R1/R5 remain the same deferred AP18 controller obligation, and R14 was resolved by the recorded focused check.

## Overview

### Problem Statement
Session helpers prepare artifacts and semantic proposals. The bundled controller owns persistent effects (00018–00021); helpers must not become a second writer. V1 implements this feature, but its bounded recovery leaves supported containment, review-input isolation and sink failure regressions. Correct those defects without rebuilding settled implementation or broadening helper ownership.

### Target Users
Users preparing local artifacts and standalone or managed sessions submitting results to the same controller.

### Success Metrics
The named behavior scenarios pass, and source-map evidence assigns every affected behavior to its correct owner. No unsupported capability is advertised. A fresh full completion review certifies the whole retained feature contract with Alice, Blake, Bob and Carl, plus the explicit Anthropic doubt lens selected by doubt_reviewer: fable. This fifth lens remains required even if v2 implementation uses native Anthropic. Each review cycle retains every lens and runs in a fresh session after the build handoff. Blake receives only the permitted PRD inputs, never design, history or other reviewers' findings. Preserve actual model-family provenance; do not substitute auto or downgrade.

New rework cap is two for this explicitly admitted v2; preserve v1's exhausted cap. At v2's cap, use the existing bounded recovery/deferral policy and report the blocker. Do not create an automatic v3 or reset counters. A focused helper pass does not certify the full gate. The known AP18 controller failures remain separate, recorded blockers; never mask, delete, xfail or relabel them to obtain a green result.

## Functional Decomposition

### Capability: Helpers
Retain the complete original preparation/classification capability and repair its demonstrated boundary defects.

#### Feature: Preparation and classification
- **Description**: Preparation and classification within the declared ownership boundary.
- **Inputs**: Explicit PRD/task inputs, review artifacts, optional supplied read snapshots and artifact destinations.
- **Outputs**: Prepared review inputs, parsed/grouped findings, regression/custody proposals and catchup results.
- **Behavior**: Port review_stage, findings_section, rework_groups, gate_lead, cap_check and catchup logic by function. Remove source implicit state discovery, direct writes and runtime imports. Keep source semantic checks and blind-input restrictions. Consume AP 00012 evidence as policy, expected context and per-reviewer results; never infer reviewer completion from finding count. Expected source bindings come from explicit current inputs, not the submitted evidence. Review-close preparation produces classified decisions and grouped task proposals; durable application is deferred to the controller client. Helpers do not select/move PRDs, persist tasks/attempts or advance phases. This original v1 behavior remains acceptance scope, not a request to repeat its completed implementation.

#### Feature: Granted review inputs and safe staging destinations
- **Description**: Reject incomplete blind inputs and prevent staging outside granted content or into Git metadata.
- **Inputs**: Explicit roster, AP12 expected context and per-job grants, PRD/design/tasks/context/history/gate inputs, project and artifact roots.
- **Outputs**: Existing versioned successful staging result or controlled invalid-input/unsafe-output refusal before writes.
- **Behavior**: Blake and Eve require their own PRD grant; missing grants refuse instead of producing successful empty-PRD prompts. Each prompt and every referenced context artifact contains only its granted input kinds. The shared context artifact contains only the union of granted context variants, without ungranted markers or paths; an empty union grants no content. Preserve established independent per-job filtering and PRD-only blind isolation. Reject ordinary, linked-worktree, separate and bare Git metadata destinations with Git's safe.bareRepository=explicit configuration intact. Git detection failure must not silently grant permission to write into metadata. Never override, weaken or persist Git safety configuration. Preserve legitimate external artifact directories that satisfy the existing contract.

### Capability: Artifacts
Retain the complete original verification/local-boundary capability and correct supported sink failures.

#### Feature: Verification and local boundaries
- **Description**: Verification and local boundaries within the declared ownership boundary.
- **Inputs**: Explicit command argv, source identity, optional prior verification artifact, declared output paths.
- **Outputs**: Actual command output and reusable evidence whose acceptance remains controller-owned.
- **Behavior**: Run phase-local verification and retain pure dirty-tree/log-sink/reuse checks. Local artifacts are reports, never an authoritative ledger/queue/owner file. All helper/test roots are temporary or explicitly supplied. No helper reads/writes the executing repository’s live autopilot state directory (the batch's own state), invokes a supervisor, commits the record store or discovers OVCAQ. Return a controller-required result for stateful operations before any mutation. This original v1 behavior remains acceptance scope, not a request to repeat its completed implementation.

#### Feature: Containment before reads and controlled sink effects
- **Description**: Refuse unsafe output candidates before reading their contents or starting the command.
- **Inputs**: Explicit verification artifact/log paths, project root, argv, linked-worktree pointer and legacy policy export destination.
- **Outputs**: Existing successful output formats or controlled refusal, with no pre-refusal command marker or unauthorized file changes.
- **Behavior**: Apply containment before pointer-content reads; a refused external candidate hard-linked to an external .git file must never be opened for content. Only the supplied repository's actual worktree pointer may be read for this check. Resolve relative gitdir targets against that pointer's parent, retaining portable regression coverage and existing case-alias checks. Validate both verification sinks and their parent descent before spawning, including non-directory parents and unresolved/resolved root aliases. Preserve spawn-failed behavior and existing output bytes on a failed spawn. Later sink errors return controlled failure, never a traceback or reusable success, and terminate/reap any started process group. Use nonblocking policy-output opening and validate the opened inode before truncation; FIFO outputs must refuse promptly with and without a reader. Missing O_NOFOLLOW produces controlled platform refusal before output effects. Preserve legacy policy bytes, stdout behavior and caller-relative --out resolution.

#### Feature: Bounded evidence validation and accurate delivery evidence
- **Description**: Prove allocation is bounded by evidence size and refresh receipts against the corrected package.
- **Inputs**: Explicit AP12 evidence with adversarial attempt integers; actual verification results and immutable package revision.
- **Outputs**: Existing attempt-sequence defect, bounded validation, and truthful source-map/receipt/documentation evidence.
- **Behavior**: Replace the range-monkeypatch-only regression with behavioral allocation measurement with tracemalloc around evidence checking for attempt 200000; peak traced allocation stays below 1,000,000 bytes and the existing attempt_sequence_invalid defect remains. Use this bounded representative instead of R13's literal 10**12: a regressed [0] * attempt allocates about 1.6 MB on the supported 64-bit test host, exceeding the 1 MB ceiling while staying small enough to avoid host exhaustion. The test must detect equivalent proportional allocations using lists or other containers, not require a particular implementation expression. Do not introduce a resource-control subsystem. Preserve current evidence acceptance semantics. Refresh exact commands, outcomes, full commit IDs and changed-file hashes without rewriting historical receipts or claiming an unrun check. Explain that plan grants tasks while design needs both plan and prd. Changelog wording describes user-visible changes.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/scripts/review_stage.py                         # Helpers: T1
plugins/autopilot/scripts/log_sink_refusal.py                     # Artifacts: T2
plugins/autopilot/scripts/verification.py                         # Artifacts: T2
plugins/autopilot/scripts/autopilot.py                            # Artifacts: T2
tests/autopilot/test_helper_recovery_v2.py                        # T1/T2 regressions
tests/autopilot/test_cap_recovery_helpers.py                      # Artifacts: T3
plugins/autopilot/README.md                                      # Delivery: T4
plugins/autopilot/CHANGELOG.md                                   # Delivery: task entries/T4
tools/autopilot/source-map.json                                 # Delivery: T4
docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json # Delivery: T4
docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md        # Delivery: T4
```

These are the complete implementation write paths. Tests may use temporary fixtures only. Existing helper modules, AP12 contracts, v1 design/spec/reviews, source characterization, source-map generator, provenance tests, controller files and workflow state are read-only. The coordinator alone owns PRD lifecycle and review records; this file does not grant workers those writes. Existing helper implementations outside the corrective paths remain part of full-feature acceptance.

### Module: Helpers
- **Maps to capability**: Helpers.
- **Responsibility**: Enforce explicit manifest and staging boundaries without workflow ownership.
- **Exports**: Existing stage-review behavior; no new facade operation or protocol version.
- **Location**: plugins/autopilot/scripts/review_stage.py; tests/autopilot/test_helper_recovery_v2.py.
New symbols: `tests/autopilot/test_helper_recovery_v2.py`

### Module: Artifacts
- **Maps to capability**: Artifacts.
- **Responsibility**: Preserve sink, process and evidence safety with explicit inputs and bounded resources.
- **Exports**: Existing verification, log-sink refusal and policy export results; unchanged attempt-sequence rejection.
- **Location**: plugins/autopilot/scripts/log_sink_refusal.py; plugins/autopilot/scripts/verification.py; plugins/autopilot/scripts/autopilot.py; tests/autopilot/test_helper_recovery_v2.py; tests/autopilot/test_cap_recovery_helpers.py.

### Module: Delivery
- **Maps to capability**: Artifacts.
- **Responsibility**: Bind source-map delivery evidence to actual tested package bytes and retain prior history.
- **Exports**: Updated existing receipt and source map; scoped recovery report and user-facing docs.
- **Location**: plugins/autopilot/README.md; plugins/autopilot/CHANGELOG.md; tools/autopilot/source-map.json; docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json; docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md.
New symbols: `docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md`

## Dependency Graph

### Foundation Layer (Phase 0)
AP12 is complete. V1 implementation and its history are prerequisites, not rebuild tasks. Durable review-03 and hold stubs 00030–00033 supply the cap-regression disposition. Recheck each cited defect against current code before changing it; if the premise is false, preserve code and report the evidence instead of forcing the proposed fix.
- **Helpers**: Depends on existing AP12 contracts, v1 implementation and adjudicated review-03; T1 establishes corrected staging boundaries.

### Core Layer (Phase 1)
- **Artifacts**: Depends on Foundation acceptance; T2 corrects sink/process behavior and T3 strengthens allocation evidence. T3 has no new production scope and follows T2 to serialize the shared test fixture.

### Integration Layer (Phase 2)
- **Delivery**: Depends on Helpers and Artifacts; T4 refreshes evidence after committed product changes.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Close supported staging highs while preserving the original helper contract.

**Tasks**:
- [ ] T1: Repair staging metadata detection and missing/ungranted review inputs. (depends on: completed AP12 and preserved v1/review-03 baseline) Writable paths: plugins/autopilot/scripts/review_stage.py, tests/autopilot/test_helper_recovery_v2.py, plugins/autopilot/CHANGELOG.md. Acceptance: new staging tests cover bare/separate Git metadata under command-scoped safe.bareRepository=explicit, valid external output, missing Blake/Eve PRD refs and all emitted shared/per-job artifact markers; old per-job restrictions remain. Run the new file with -k staging and existing tests/autopilot/test_review_helpers.py, tests/autopilot/test_review_helpers_contract.py, tests/autopilot/test_cycle1_boundaries_context.py. Recheck cited defects first; false premises skip/report only the affected change.

**Exit Criteria**: T1's named scoped tests pass with no state reads/writes and no Git safety override. Record exact commands and actual outcomes.

### Phase 1: Core
**Goal**: Close sink regressions and prove allocation safety without broadening legacy semantics.

**Tasks**:
- [ ] T2: Repair containment-before-read, pre-spawn sink validation, controlled sink failure and policy-output platform/nonblocking behavior. (depends on: T1) Writable paths: plugins/autopilot/scripts/log_sink_refusal.py, plugins/autopilot/scripts/verification.py, plugins/autopilot/scripts/autopilot.py, tests/autopilot/test_helper_recovery_v2.py, plugins/autopilot/CHANGELOG.md. Acceptance: the new file excluding staging tests proves external .git hard-link candidate content is never read, relative gitdir resolution, non-directory/aliased sink refusal before a spawn marker, controlled later sink error with child cleanup, preserved outputs on spawn failure, bounded FIFO refusal with/without a reader and safe missing-O_NOFOLLOW refusal. Existing tests/autopilot/test_cycle1_hardening_sinks.py, tests/autopilot/test_cycle1_boundaries_verify.py, tests/autopilot/test_verification.py and tests/autopilot/test_facade.py remain green. Recheck each premise first; do not change executable-bit or arbitrary-path legacy policy solely because a reviewer suggested broader helper-artifact restrictions.
- [ ] T3: Replace implementation-shaped allocation evidence with a behavioral bound. (depends on: T2) Writable path: tests/autopilot/test_cap_recovery_helpers.py. Acceptance: test_attempt_validation_does_not_allocate_from_the_supplied_attempt uses tracemalloc to measure actual peak allocation for attempt 200000 below 1,000,000 bytes, asserts attempt_sequence_invalid and is demonstrably sensitive to [0] * attempt or another proportional non-range allocation. The representative input keeps a regressed allocation to a few MB rather than risking an OOM from 10**12 elements. Retain other cap-recovery tests; run this node and tests/autopilot/test_review_evidence_helpers.py. Recheck that the current bounded production predicate remains correct; no production rewrite is authorized by this test-only task.

**Exit Criteria**: T2/T3's named scoped tests pass, subprocess probes have explicit timeouts, and no test changes weaken existing assertions. Temporary test assets are cleaned safely.

### Phase 2: Integration
**Goal**: Retain whole-feature acceptance and bind delivery evidence to corrected bytes.

**Tasks**:
- [ ] T4: Refresh docs, receipts and generated helper provenance. (depends on: T1–T3) Writable paths: plugins/autopilot/README.md, plugins/autopilot/CHANGELOG.md, tools/autopilot/source-map.json, docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json, docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md. Acceptance: clarify the conjunction of plan/prd grants, document controlled refusals, preserve the historical receipt, bind the new receipt to the exact tested revision and actual commands/results, and regenerate the source map using the exact existing CLI below. Commit README/CHANGELOG changes before testing their package revision; record that full 40-hex SHA in the receipt package_revision field, then generate receipt/map evidence in a subsequent commit without changing tested package bytes. The generator derives tested_package_revision from that receipt field; there is no CLI flag for it. Run the same generator command with --check and tests/autopilot/test_helper_provenance.py plus tests/autopilot/test_provenance.py. Recheck current map ownership before editing; retain every source owner and settled deferral. Record any unavailable real-host evidence explicitly.

Generator command from the repository root (T4 only):

```sh
python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json
python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json --check
```

**Exit Criteria**: Run the named whole-feature scenarios below and the full gate once after all tasks: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`, `python3 -m unittest discover -s scripts`, `python3 scripts/validate.py`, and `python3 scripts/generate_marketplace.py --check`. Preserve the existing CI checks without editing their definitions. Record exact failed nodes and ownership if the AP18 controller suite remains red. Retain the known 19 AP18 controller failures as an explicit deferred external obligation in the completion disposition; the original full-suite-green obligation remains unmet until they pass, never relabeled as a helper pass. This scoped external deferral does not cover any new helper regression or unidentified failure. No push occurs until the known controller tests and all required checks pass. Handoff before a fresh full-lens completion review; no review may run from the work session. No publishing or cutover occurs.

## Test Strategy

### Critical Scenarios
The following original v1 acceptance obligations remain intact and must all be certified, although only corrective work receives tasks:
- **Source parity**: helper_source_parity covers valid/invalid findings, clean reviewer results, stale PRD/code bindings and blind input exclusions; recheck existing target ownership and skip/report conflicts.
- **Preparation**: review_preparation_no_state and finding_group_equivalence assert equivalent semantics with no state access or queue changes.
- **Catchup and verification**: catchup_optional_absent and verification_artifact_reuse cover source fallbacks, changed-code rejection and real command exit/output.
- **Public boundaries**: local_helpers_without_ovcaq, no_hidden_workflow_state and controller_action_not_yet_wired use temporary project roots and poison legacy-state files to prove no access, mutation, marker or runtime lookup.
- **Source inventory**: source_inventory_mapping binds every helper obligation and source regression case to an observable target scenario and rejects a helper-owned writer or supervisor; the separate controller is allowed.
- **Happy path**: local_helpers_without_ovcaq → Explicit review inputs produce useful complete artifacts without OVCAQ installed.
- **Edge case**: verification_artifact_reuse → Only explicit compatible prior evidence is reused; changed code invalidates it.
- **Error case**: controller_action_not_yet_wired → A lifecycle request refuses before writing state, moving a PRD or launching a session.
- **New isolation and containment cases**: Missing blind PRD grant, ungranted shared markers, safety-configured bare/separate metadata and external hard-link pointer candidates refuse without unauthorized reads or writes. Genuine relative worktree pointers remain detected on case-sensitive hosts.
- **New sink cases**: Unsafe parents/root aliases prevent spawn; later sink errors clean up children and return controlled failure; failed spawn preserves existing bytes. FIFO and unavailable no-follow support produce bounded, effect-free policy-export refusals.
- **Resource case**: Attempt 200000 stays below the 1,000,000-byte traced allocation ceiling; a proportional list allocation fails this behavioral bound without risking host exhaustion. Retain all existing evidence semantics and report actual measurement.

All pytest invocations use `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest` with the named file/node/filter and -q. Run narrow tests during tasks; reserve the full suite for final integration. The v1 source-map scenario bindings and existing tests remain read-only evidence. Filesystem-dependent case-alias skips remain explicit; the new relative-pointer case must run on every supported filesystem.

## Risks

- **Cap history loss**: Preserve v1 task/review/stub/deferral history and record v2 as a bounded correction of the same feature. No automatic unbounded successor.
- **Unsupported policy expansion**: The generic v1 helper-artifact rule and legacy export compatibility differ in scope. This PRD fixes proven FIFO, hard-link and platform failures; it does not impose repository-root, tracked-file or executable-bit restrictions on legacy --export-policy without separately grounded requirements. See plugins/autopilot/README.md:228-241 and docs/dev/project-management/designs/00013-autopilot-session-helpers-v1-design.md:25-32,178-178.
- **Controller ownership leak**: Keep actual native-job provenance, manifest production, durable deduplication, custody, task persistence and lifecycle changes with their existing controller owners. Retain already settled unrelated deferrals; do not reopen them as helper work.
- **False green**: AP18's known controller failures are outside these write paths but remain a full-gate/push blocker. Report actual red results; never claim helper-only checks satisfy them.
- **Stale evidence**: Recheck the recorded review findings against current source at task start and skip/report a false premise. Preserve the exact review-03 dispositions and original cap history; newer passing evidence must identify its actual package revision and never rewrite historical red results.

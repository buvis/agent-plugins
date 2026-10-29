---
default_model: opus
model_tier_rationale: Semantic helper equivalence and removal of mixed stateful effects require judgment.
lane: full
eligibility: ls docs/dev/project-management/prds/done/00012-* # link-ok: lifecycle output
---
# Autopilot session-local helpers

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Implementation specification only; no publication, live installation, migration or source retirement.

## Overview

### Problem Statement
Session helpers prepare artifacts and semantic proposals. The bundled controller owns persistent effects (00018–00021); helpers must not become a second writer.

### Target Users
Users preparing local artifacts and standalone or managed sessions submitting results to the same controller.

### Success Metrics
The named behavior scenarios pass, and source-map evidence assigns every affected behavior to its correct owner. No unsupported capability is advertised.

## Functional Decomposition

### Capability: Helpers

#### Feature: Preparation and classification
- **Description**: Preparation and classification within the declared ownership boundary.
- **Inputs**: Explicit PRD/task inputs, review artifacts, optional supplied read snapshots and artifact destinations.
- **Outputs**: Prepared review inputs, parsed/grouped findings, regression/custody proposals and catchup results.
- **Behavior**: Port review_stage, findings_section, rework_groups, gate_lead, cap_check and catchup logic by function. Remove source implicit state discovery, direct writes and runtime imports. Keep source semantic checks and blind-input restrictions. Consume AP 00012 evidence as policy, expected context and per-reviewer results; never infer reviewer completion from finding count. Expected source bindings come from explicit current inputs, not the submitted evidence. Review-close preparation produces classified decisions and grouped task proposals; durable application is deferred to the controller client. Helpers do not select/move PRDs, persist tasks/attempts or advance phases.

### Capability: Artifacts

#### Feature: Verification and local boundaries
- **Description**: Verification and local boundaries within the declared ownership boundary.
- **Inputs**: Explicit command argv, source identity, optional prior verification artifact, declared output paths.
- **Outputs**: Actual command output and reusable evidence whose acceptance remains controller-owned.
- **Behavior**: Run phase-local verification and retain pure dirty-tree/log-sink/reuse checks. Local artifacts are reports, never an authoritative ledger/queue/owner file. All helper/test roots are temporary or explicitly supplied. No helper reads/writes the executing repository’s live autopilot state directory (the batch's own state), invokes a supervisor, commits the record store or discovers OVCAQ. Return a controller-required result for stateful operations before any mutation.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/scripts/review_stage.py  # Helpers
plugins/autopilot/scripts/findings.py  # Helpers
plugins/autopilot/scripts/rework_groups.py  # Helpers
plugins/autopilot/scripts/gate_lead.py  # Helpers
plugins/autopilot/scripts/custody.py  # Helpers
plugins/autopilot/scripts/catchup.py  # Helpers
plugins/autopilot/scripts/autopilot.py  # Helpers
tests/autopilot/test_review_helpers.py  # Helpers
tests/autopilot/test_finding_groups.py  # Helpers
tests/autopilot/test_catchup.py  # Helpers
plugins/autopilot/scripts/verification.py  # Artifacts
plugins/autopilot/contracts/review-fixtures-v1.json  # Artifacts
plugins/autopilot/CHANGELOG.md  # Artifacts
tools/autopilot/source-map.json  # Artifacts
tests/autopilot/test_verification.py  # Artifacts
tests/autopilot/test_local_boundary.py  # Artifacts
```

### Module: Helpers
- **Maps to capability**: Helpers
- **Responsibility**: Retain semantic session preparation/classification without lifecycle or persistence code.
- **Exports**: stage-review, group-findings, check-evidence and catchup-probe local facade operations.
New symbols: `plugins/autopilot/scripts/review_stage.py`, `plugins/autopilot/scripts/findings.py`, `plugins/autopilot/scripts/rework_groups.py`, `plugins/autopilot/scripts/gate_lead.py`, `plugins/autopilot/scripts/custody.py`, `plugins/autopilot/scripts/catchup.py`, `tests/autopilot/test_review_helpers.py`, `tests/autopilot/test_finding_groups.py`, `tests/autopilot/test_catchup.py`

### Module: Artifacts
- **Maps to capability**: Artifacts
- **Responsibility**: Create evidence from explicit inputs; assert the absence of runtime ownership and state mutation.
- **Exports**: Verification artifacts and prepared mutation proposals, never an accepted runtime phase.
New symbols: `plugins/autopilot/scripts/verification.py`, `tests/autopilot/test_verification.py`, `tests/autopilot/test_local_boundary.py`

## Dependency Graph

### Foundation Layer (Phase 0)
Plugin 00012 completed. Source functions currently mix content preparation and state access; recheck the pinned source and split by effect instead of copying its state/lifecycle modules. Containment authority: AGENTS.md:39. This PRD covers pure helpers only. The one canonical controller is a separate workstream; its later availability must not be mistaken for helper ownership of state.
- **Characterization/contracts**: Establish the inputs consumed by Helpers and Artifacts.

### Core Layer (Phase 1)
- **Helpers**: Depends on the Phase 0 inputs.
- **Artifacts**: Depends on Phase 0 and the explicitly ordered task prerequisites below.

### Integration Layer (Phase 2)
- **Public-boundary tests and documentation**: Depend on Helpers and Artifacts.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Verify source premises and establish exact contracts.

**Tasks**:
- [ ] Characterize source helper decisions and identify stateful side effects in the source map. (depends on: declared prerequisites) — Acceptance: helper_source_parity covers valid/invalid findings, clean reviewer results, stale PRD/code bindings and blind input exclusions; recheck existing target ownership and skip/report conflicts.

**Exit Criteria**: The named task tests pass. Recheck changed-content premises; if false, skip/report affected edits without forcing them.

### Phase 1: Core
**Goal**: Implement behavior under the correct owner.

**Tasks**:
- [ ] Port review staging, finding extraction/grouping and gate/custody classification with explicit input/output boundaries. (depends on: Phase 0) — Acceptance: review_preparation_no_state and finding_group_equivalence assert equivalent semantics with no state access or queue changes.
- [ ] Port catchup probes and pure verification execution/reuse checks without durable bookkeeping. (depends on: Phase 1 task 1) — Acceptance: catchup_optional_absent and verification_artifact_reuse cover source fallbacks, changed-code rejection and real command exit/output.

**Exit Criteria**: The named task tests pass. Recheck changed-content premises; if false, skip/report affected edits without forcing them.

### Phase 2: Integration
**Goal**: Prove public behavior and document capability evidence.

**Tasks**:
- [ ] Wire local facade commands and enforce controller-required refusals for lifecycle actions. (depends on: Phase 1) — Acceptance: local_helpers_without_ovcaq, no_hidden_workflow_state and controller_action_not_yet_wired use temporary project roots and poison legacy-state files to prove no access, mutation, marker or runtime lookup.
- [ ] Record helper-by-helper disposition and changelog evidence. (depends on: Phase 2 task 1) — Acceptance: source_inventory_mapping binds every helper obligation and source regression case to an observable target scenario and rejects a helper-owned writer or supervisor; the separate controller is allowed.

**Exit Criteria**: The named integration scenarios and `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record real-host unavailability explicitly; it does not certify execution. No publishing or cutover occurs.

## Test Strategy

### Critical Scenarios
- **Happy path**: local_helpers_without_ovcaq → Explicit review inputs produce useful complete artifacts without OVCAQ installed.
- **Edge case**: verification_artifact_reuse → Only explicit compatible prior evidence is reused; changed code invalidates it.
- **Error case**: controller_action_not_yet_wired → A lifecycle request refuses before writing state, moving a PRD or launching a session.

## Risks

- Do not turn artifact metadata into a renamed workflow state machine.
- A mixed source module needs function-level extraction, not whole-file copying.

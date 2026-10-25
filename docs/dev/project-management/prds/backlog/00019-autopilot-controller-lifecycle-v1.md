---
default_model: opus
model_tier_rationale: Extraction equivalence, public contracts and concurrent workflow authority require judgment.
lane: full
rework_cap: 3
plan_expansion: allow
eligibility: ls docs/dev/project-management/prds/done/00018-* # link-ok: lifecycle output
---
# Autopilot controller lifecycle, tasks and job plans

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
PRD entry, moves and task history must work independently of supervision while preserving tested lifecycle recovery.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
manual_session_handoff → a fresh manual session resumes the same workflow. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Lifecycle

#### Feature: Extract and complete PRD operations
- **Description**: Own PRD lifecycle and recoverable filesystem effects.
- **Inputs**: Controller kernel, OVCAQ workflow services and discovery 00003 gaps.
- **Outputs**: Typed selection/entry/task/attempt/handoff/park/defer/complete operations.
- **Behavior**: Extract selection, frontmatter, paths, policy, transitions and file-intent recovery from OVCAQ. Preserve cf8be72 guards and pre-intent path validation. Add wip-first entry, start commit/frontmatter captured once, completion move after accepted review, empty-eligible-queue drain distinction and audited repair. No arbitrary state setters. Controller owns eligibility and task-tier requirements; OVCAQ owns actual model placement.

### Capability: Jobs

#### Feature: Next-job protocol without spawning
- **Description**: Make required execution machine-readable.
- **Inputs**: Current workflow phase, task dependencies, policy and accepted results.
- **Outputs**: Immutable job plans, claims, exit facts and structured standalone next-job instructions.
- **Behavior**: Define job ID, role, dependency IDs, source/input/resource digests, isolation, tier/effort and permitted operations. Native identity and exit facts are recorded but never substitute for review acceptance. Plan generation is deterministic; only one valid claim per job/epoch. Controller never launches processes. Early supervisor-start revert from OVCAQ 00062 is incorporated before the extraction consumer removes its old writer.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/controller/autopilot_state/lifecycle.py
plugins/autopilot/controller/autopilot_state/tasks.py
plugins/autopilot/controller/autopilot_state/frontmatter.py
plugins/autopilot/controller/autopilot_state/policy.py
plugins/autopilot/controller/autopilot_state/files.py
tests/autopilot/test_controller_lifecycle.py
tests/autopilot/test_controller_recovery.py
plugins/autopilot/controller/autopilot_state/jobs.py
plugins/autopilot/controller/autopilot_state/protocol.py
plugins/autopilot/contracts/controller/workflow-v1.json
plugins/autopilot/contracts/controller/fixtures-v1.json
plugins/autopilot/contracts/controller/provenance.json
tests/autopilot/test_controller_jobs.py
plugins/autopilot/CHANGELOG.md
```

### Module: Lifecycle
- **Maps to capability**: Lifecycle
- **Responsibility**: Own PRD lifecycle and recoverable filesystem effects.
- **Exports**: Typed selection/entry/task/attempt/handoff/park/defer/complete operations.
New symbols: `plugins/autopilot/controller/autopilot_state/lifecycle.py`, `plugins/autopilot/controller/autopilot_state/tasks.py`, `plugins/autopilot/controller/autopilot_state/frontmatter.py`, `plugins/autopilot/controller/autopilot_state/policy.py`, `plugins/autopilot/controller/autopilot_state/files.py`, `tests/autopilot/test_controller_lifecycle.py`, `tests/autopilot/test_controller_recovery.py`

### Module: Jobs
- **Maps to capability**: Jobs
- **Responsibility**: Make required execution machine-readable.
- **Exports**: Immutable job plans, claims, exit facts and structured standalone next-job instructions.
New symbols: `plugins/autopilot/controller/autopilot_state/jobs.py`, `tests/autopilot/test_controller_jobs.py`

- **Location**: `plugins/autopilot/controller/autopilot_state/schema.py`

## Dependency Graph

### Foundation Layer (Phase 0)
AP 00018 completed. Reuse source OVCAQ workflow modules and discovery 00003, not another legacy engine. Package containment is required by AGENTS.md:39. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Lifecycle**: Depends on Phase 0 and the explicit task order below.
- **Jobs**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Lifecycle and Jobs.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Characterize lifecycle/frontmatter/task behavior and source regression fixes. (depends on: declared prerequisites) — Acceptance: lifecycle_source_map and transition_preconditions retain running-batch/active-PRD and pre-intent validation; recheck current source.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Extract lifecycle and task operations with explicit compound transactions. (depends on: Phase 0) — Acceptance: entry_wip_first, completion_moves_once, task_attempt_replay and interrupted_move_recovery pass on temporary repositories.
- [ ] Implement deterministic job plans, scoped claims and exit facts without subprocess launch. (depends on: Phase 1 task 1) — Acceptance: job_claim_exclusive, job_plan_stable and no_controller_spawn cover resume and duplicate requests.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Export core/jobs capabilities and run a manual-session fake-host lifecycle. (depends on: Phase 1) — Acceptance: manual_session_handoff, false_success_no_advance and drained_vs_ineligible prove state-led continuation.

**Exit Criteria**: Named integration scenarios, `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record missing real-host capabilities as unavailable.

## Test Strategy

### Critical Scenarios
- **Happy path**: manual_session_handoff → a fresh manual session resumes the same workflow.
- **Edge case**: interrupted_move_recovery → bucket moves recover without duplicate entry.
- **Error case**: false_success_no_advance → prose or exit zero cannot bypass review.

## Risks

- Completion acceptance is unavailable until review capabilities arrive in AP 00020.
- Resolve paths identically across init/snapshot/apply; no request-selected state file.

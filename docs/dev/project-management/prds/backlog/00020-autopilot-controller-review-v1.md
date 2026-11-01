---
default_model: opus
model_tier_rationale: Extraction equivalence, public contracts and concurrent workflow authority require judgment.
lane: full
rework_cap: 3
plan_expansion: allow
eligibility: ls docs/dev/project-management/prds/done/00019-* # link-ok: lifecycle output
---
# Autopilot controller review, lanes and evidence guards

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
Moving the writer beside the plugin only helps if every state-changing path enforces lane, review and custody requirements in code.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
full_roster → every required lens has fresh accepted evidence. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Review

#### Feature: Atomic review acceptance
- **Description**: Enforce workflow review semantics in one authority.
- **Inputs**: AP 00012 policy/evidence, AP 00013 helper outputs, job/session facts and source lane fixtures.
- **Outputs**: Code-selected lanes, required jobs and atomic review/rework/custody acceptance.
- **Behavior**: Keep full/fast-track/solo routing and escalation in controller code. Preserve all mandatory lenses, blind fresh-session restrictions, R1–R5, cap two unless configured, severe custody and grouped rework. Helpers own semantic classification; controller validates AP 00012 policy against its own current job plan and expected PRD/code/input context. Validate per-reviewer terminal results independently of findings, including clean zero-finding results, exact conditional rosters, rubric coverage, artifact bytes, distinct native sessions and exited jobs. Caller-supplied result/session strings or copied context are not proof. Close persists effects atomically; lower-level handoff/recovery cannot bypass it.

### Capability: Evidence

#### Feature: Verification and wave acceptance contract
- **Description**: Validate evidence without running supervisors.
- **Inputs**: Command/output artifacts, code/tree identities and proposed wave membership/outcomes.
- **Outputs**: Accepted verification and semantic wave permissions, with versioned negative fixtures.
- **Behavior**: Enforce actual command exit/output and verification reuse rules. Define workflow.waves.v1 semantic operations for plans/member results, assembly and landing authorization; no worktree/process mechanics. Custody/push restrictions require host interception too. Extend protocol schemas/fixtures and advertise capabilities only when their rejecting paths pass.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/controller/autopilot_state/review.py
plugins/autopilot/controller/autopilot_state/lane.py
plugins/autopilot/controller/autopilot_state/custody.py
plugins/autopilot/controller/autopilot_state/jobs.py
tests/autopilot/test_controller_review.py
tests/autopilot/test_controller_lane.py
tests/autopilot/test_controller_custody.py
plugins/autopilot/controller/autopilot_state/verification.py
plugins/autopilot/controller/autopilot_state/waves.py
plugins/autopilot/controller/autopilot_state/protocol.py
plugins/autopilot/contracts/controller/workflow-v1.json
plugins/autopilot/contracts/controller/fixtures-v1.json
plugins/autopilot/contracts/controller/provenance.json
tests/autopilot/test_controller_evidence.py
tests/autopilot/test_controller_waves.py
plugins/autopilot/CHANGELOG.md
```

### Module: Review
- **Maps to capability**: Review
- **Responsibility**: Enforce workflow review semantics in one authority.
- **Exports**: Code-selected lanes, required jobs and atomic review/rework/custody acceptance.
New symbols: `plugins/autopilot/controller/autopilot_state/review.py`, `plugins/autopilot/controller/autopilot_state/lane.py`, `plugins/autopilot/controller/autopilot_state/custody.py`, `tests/autopilot/test_controller_review.py`, `tests/autopilot/test_controller_lane.py`, `tests/autopilot/test_controller_custody.py`

### Module: Evidence
- **Maps to capability**: Evidence
- **Responsibility**: Validate evidence without running supervisors.
- **Exports**: Accepted verification and semantic wave permissions, with versioned negative fixtures.
New symbols: `plugins/autopilot/controller/autopilot_state/verification.py`, `plugins/autopilot/controller/autopilot_state/waves.py`, `tests/autopilot/test_controller_evidence.py`, `tests/autopilot/test_controller_waves.py`

- **Location**: `plugins/autopilot/controller/autopilot_state/schema.py`, `plugins/autopilot/controller/autopilot_state/lifecycle.py`, `plugins/autopilot/controller/autopilot_state/tasks.py`

## Dependency Graph

### Foundation Layer (Phase 0)
AP 00019 completed; AP 00012 fixtures are sufficient, so implementation does not wait for helper 00013. Source rows R11/R12/R16/R28 retain explicit acceptance owners. Package containment is required by AGENTS.md:39. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Review**: Depends on Phase 0 and the explicit task order below.
- **Evidence**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Review and Evidence.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Freeze equivalent lane/review/custody cases and exact evidence payloads. (depends on: declared prerequisites) — Acceptance: review_policy_equivalence preserves source outcomes and rechecks changed source premises.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Implement lane selection/escalation and atomic review/rework/custody validation. (depends on: Phase 0) — Acceptance: full_roster, fast_track_complete_roster, solo_requires_review, clean_review_results, solo_escalates, cap_two and no_review_bypass exercise every public transition path.
- [ ] Implement verification and semantic wave guards without process/worktree actions. (depends on: Phase 1 task 1) — Acceptance: stale_code_rejected, stale_prd_same_policy_rejected, evidence_cannot_choose_context, blind_input_rejected and wave_land_requires_accepted_review reject incomplete evidence.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Export reviews/waves capabilities and run adversarial public CLI scenarios. (depends on: Phase 1) — Acceptance: forged_job_identity, live_reviewer_rejected and missing_lens_rejected prove typed requests cannot waive policy.

**Exit Criteria**: Named integration scenarios, `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record missing real-host capabilities as unavailable.

## Test Strategy

### Critical Scenarios
- **Happy path**: full_roster → every required lens has fresh accepted evidence.
- **Edge case**: stale_code_rejected → earlier verification cannot approve changed code.
- **Error case**: no_review_bypass → direct completion/recovery cannot skip the gate.

## Risks

- Semantic correctness of reviewer findings still needs independent reviewers; structural validation cannot prove it.
- Controller acceptance cannot retroactively stop a forbidden push; host pre-action guards remain mandatory.

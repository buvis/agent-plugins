---
default_model: opus
model_tier_rationale: Session identity, fresh-review boundaries and installed artifact equivalence require judgment.
lane: full
eligibility: ls docs/dev/project-management/prds/done/00015-* docs/dev/project-management/prds/done/00020-* docs/dev/project-management/prds/done/00021-* # link-ok: lifecycle output
---
# Autopilot skills and standalone controller integration

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
Skills must use the bundled controller for stateful work even when OVCAQ is absent. They must not recreate a supervisor or rely on prose for acceptance.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
standalone_complete_without_ovcaq → complete durable workflow without OVCAQ/Tower. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Integration

#### Feature: One controller client
- **Description**: Wire skills/helpers/hooks to one authority.
- **Inputs**: Installed controller argv, packaged schemas and explicit session identity.
- **Outputs**: Typed controller requests and structured handoff instructions.
- **Behavior**: Use argv arrays and package-relative resolution. All persistent operations call the controller; helpers only prepare inputs. Same requests work in manual or managed mode with different scoped actors. Preserve replay IDs and authoritative errors. Bind AP 00012 reviewer-result references and PRD/code/input digests to current controller jobs; evidence cannot select its own expected context or roster. No OVCAQ discovery/import, mode-specific backend or direct state edits.

### Capability: Standalone

#### Feature: Manually driven durable sessions
- **Description**: Allow useful complete workflows without upper layers.
- **Inputs**: Controller next-job instructions, supported native identity and explicit fresh sessions.
- **Outputs**: Durable PRD execution, accepted review and clean ownership transfer.
- **Behavior**: Bind manually started sessions to controller-issued job credentials. Never infer identity from an agent's prose. Emit next-session instructions then stop at a required handoff; no coordinator subprocess or queue loop. Native child jobs require declared host capability and controller claim. Managed cross-session driver requests go to OVCAQ through the claimed job/result protocol. An absent scheduler refuses automatic execution only, not controller lifecycle operations.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/scripts/controller.py
plugins/autopilot/scripts/autopilot.py
plugins/autopilot/scripts/guards.py
plugins/autopilot/contracts/capabilities.json
tests/autopilot/test_controller_client.py
tests/autopilot/test_skill_controller_wiring.py
plugins/autopilot/skills/run-autopilot/SKILL.md
plugins/autopilot/skills/work/SKILL.md
plugins/autopilot/skills/fast-track/SKILL.md
plugins/autopilot/skills/review-work-completion/SKILL.md
plugins/autopilot/skills/plan-tasks/SKILL.md
tools/autopilot/compatibility.py
tests/autopilot/test_standalone_workflow.py
tests/autopilot/test_manual_handoff.py
plugins/autopilot/README.md
plugins/autopilot/CHANGELOG.md
```

### Module: Integration
- **Maps to capability**: Integration
- **Responsibility**: Wire skills/helpers/hooks to one authority.
- **Exports**: Typed controller requests and structured handoff instructions.
New symbols: `plugins/autopilot/scripts/controller.py`, `tests/autopilot/test_controller_client.py`, `tests/autopilot/test_skill_controller_wiring.py`

### Module: Standalone
- **Maps to capability**: Standalone
- **Responsibility**: Allow useful complete workflows without upper layers.
- **Exports**: Durable PRD execution, accepted review and clean ownership transfer.
New symbols: `tools/autopilot/compatibility.py`, `tests/autopilot/test_standalone_workflow.py`, `tests/autopilot/test_manual_handoff.py`

## Dependency Graph

### Foundation Layer (Phase 0)
AP 00015, 00020 and 00021 completed. No OVCAQ artifact/probe prerequisite. This replaces the unimplemented runtime adapter in place; remove no live installation. Containment: AGENTS.md:39. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Integration**: Depends on Phase 0 and the explicit task order below.
- **Standalone**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Integration and Standalone.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Map every skill mutation and hook decision to controller operations. (depends on: declared prerequisites) — Acceptance: mutation_map_complete rechecks source/target ownership and rejects raw setters or unowned state changes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Implement the shared client and wire all persistent workflow paths. (depends on: Phase 0) — Acceptance: lost_ack_replay, invalid_binding_refused and same_client_both_modes preserve controller truth.
- [ ] Implement manual session claim/handoff and guarded managed job requests. (depends on: Phase 1 task 1) — Acceptance: manual_fresh_review, no_plugin_supervisor and nested_driver_launch_refused prove actual process/isolation boundaries.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Run installed standalone lifecycle/rework/complete scenarios with upper layers absent. (depends on: Phase 1) — Acceptance: standalone_complete_without_ovcaq and transfer_after_jobs_exit use temporary projects and distinct fake native sessions; label this protocol evidence only. AP 00017 owns separate real Claude-free completion certification.
- [ ] Expose compatibility diagnostics for controller and host capabilities. (depends on: Phase 2 task 1) — Acceptance: missing_guard_refused and missing_scheduler_only_blocks_automation show accurate operation-specific readiness.

**Exit Criteria**: Named integration scenarios, `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass.

## Test Strategy

### Critical Scenarios
- **Happy path**: standalone_complete_without_ovcaq → complete durable workflow without OVCAQ/Tower.
- **Edge case**: manual_fresh_review → builder context cannot satisfy a fresh reviewer binding.
- **Error case**: transfer_after_jobs_exit → same state transfers ownership only after safe reconciliation.

## Risks

- Manually driven operation is not unattended scheduling.
- Skill portability alone cannot prove native session isolation or pre-action interception.

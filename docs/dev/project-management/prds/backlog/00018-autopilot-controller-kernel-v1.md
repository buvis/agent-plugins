---
default_model: opus
model_tier_rationale: Extraction equivalence, public contracts and concurrent workflow authority require judgment.
lane: full
rework_cap: 3
plan_expansion: allow
eligibility: ls docs/dev/project-management/prds/done/00012-* # link-ok: lifecycle output
---
# Autopilot canonical controller kernel and protocol

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
Standalone and supervised workflows need the same enforceable writer. The current tested writer lives inside OVCAQ; adding a second legacy backend would split authority.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
controller_without_upper_layers → one installed writer runs without either upper layer. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Kernel

#### Feature: Extract the existing writer
- **Description**: Reuse tested transactional behavior without supervisor dependencies.
- **Inputs**: Pinned OVCAQ state services and characterized source invariants.
- **Outputs**: One packaged Python 3.12 controller and workflow store.
- **Behavior**: Premise: OVCAQ state/store.py and schema.py implement atomic writes, locking and revisions. Extract the workflow kernel with attribution and equivalent corruption/lock/recovery behavior; separate process fields from workflow schema. Recheck current source before moving behavior. Never mutate live source state; no OVCAQ import, process launcher or TUI dependency.

### Capability: Protocol

#### Feature: Typed commands and actor fencing
- **Description**: Publish the canonical controller boundary.
- **Inputs**: Contract A in the design, scoped actor credentials and temporary project roots.
- **Outputs**: Contract/snapshot/apply CLI, immutable export bundle and request receipts.
- **Behavior**: Implement protocol-major 1 and exact envelope/errors from Contract A. Define JSON schemas for every core operation, including explicit fresh-open bootstrap (expected revision zero, workflow ID assigned once). Fresh workflow.open alone permits null workflow/actor/epoch and revision zero on an absent store. Bootstrap creates an operator credential under the private state root (directory 0700, file 0600) and returns only its path. Other apply calls require --actor-file PATH matched to actor ID/scope; credentials never appear in command values or logs. Opening an existing workflow is not an ownership bypass. One execution lease, epoch-fenced job/operator credentials, CAS, identical-payload replay, conflicting-ID refusal and path containment. Bound output/time in clients; no credential values in logs. Publish only implemented kernel operations; later families remain declared but unavailable. CLI: `--json contract`, `--json snapshot --project-root PATH`, `--json apply --project-root PATH --request FILE`, `--actor-file PATH`. Contract output: protocol_major=1, package_version, schema_digest, fixture_digest, operations, capabilities; capability IDs workflow.core.v1, workflow.jobs.v1, workflow.reviews.v1, workflow.records.v1 and optional workflow.waves.v1. Envelope fields: protocol_major, operation, request_id, expected_revision, project_id, workflow_id, actor_id, job_id (nullable for operator actions), lease_epoch, payload. Response fields: ok, revision, result, error_code, retryable. Error codes, exactly: invalid_request, incompatible_contract, revision_conflict, wrong_binding, missing_capability, rejected_evidence, recovery_required. Closed operations: workflow.open, policy.bind, owner.acquire/release/recover, prd.enter, task.replace/start/finish/attempt, lane.route, job.plan/claim/record_exit, review.record_stage/close, custody.record/discharge, verification.record, phase.handoff, prd.stall/park/defer/complete, artifact.record, records.commit, plus the optional wave operations.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/controller/main.py
plugins/autopilot/controller/autopilot_state/__init__.py
plugins/autopilot/controller/autopilot_state/schema.py
plugins/autopilot/controller/autopilot_state/store.py
plugins/autopilot/controller/autopilot_state/paths.py
tests/autopilot/test_controller_kernel.py
plugins/autopilot/controller/autopilot_state/protocol.py
plugins/autopilot/controller/autopilot_state/actors.py
plugins/autopilot/contracts/controller/workflow-v1.json
plugins/autopilot/contracts/controller/fixtures-v1.json
plugins/autopilot/contracts/controller/provenance.json
tools/autopilot/export-controller-contract.py
tests/autopilot/test_controller_protocol.py
tests/autopilot/test_controller_actors.py
plugins/autopilot/README.md
plugins/autopilot/CHANGELOG.md
```

### Module: Kernel
- **Maps to capability**: Kernel
- **Responsibility**: Reuse tested transactional behavior without supervisor dependencies.
- **Exports**: One packaged Python 3.12 controller and workflow store.
New symbols: `plugins/autopilot/controller/main.py`, `plugins/autopilot/controller/autopilot_state/__init__.py`, `plugins/autopilot/controller/autopilot_state/schema.py`, `plugins/autopilot/controller/autopilot_state/store.py`, `plugins/autopilot/controller/autopilot_state/paths.py`, `tests/autopilot/test_controller_kernel.py`

### Module: Protocol
- **Maps to capability**: Protocol
- **Responsibility**: Publish the canonical controller boundary.
- **Exports**: Contract/snapshot/apply CLI, immutable export bundle and request receipts.
New symbols: `plugins/autopilot/controller/autopilot_state/protocol.py`, `plugins/autopilot/controller/autopilot_state/actors.py`, `plugins/autopilot/contracts/controller/workflow-v1.json`, `plugins/autopilot/contracts/controller/fixtures-v1.json`, `plugins/autopilot/contracts/controller/provenance.json`, `tools/autopilot/export-controller-contract.py`, `tests/autopilot/test_controller_protocol.py`, `tests/autopilot/test_controller_actors.py`

## Dependency Graph

### Foundation Layer (Phase 0)
AP 00012 completed. No OVCAQ runtime prerequisite. Characterize OVCAQ source pin cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7 in /Users/bob/git/src/github.com/buvis/ovcaq, read with `git show` at that pin, not checkout HEAD; record source-to-target maps, including tests. Package containment is required by AGENTS.md:39. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Kernel**: Depends on Phase 0 and the explicit task order below.
- **Protocol**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Kernel and Protocol.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Map state fields by workflow versus process ownership and freeze kernel/protocol fixtures. (depends on: declared prerequisites) — Acceptance: kernel_field_ownership and contract_examples reject unowned fields; recheck source pin and preserve existing fixes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Extract atomic store, schema and root resolver without copying supervisor ownership. (depends on: Phase 0) — Acceptance: kernel_equivalence, concurrent_cas and corrupt_state_recovery preserve source outcomes under real subprocess contention.
- [ ] Implement CLI dispatch, scoped actors, execution lease and idempotent receipts. (depends on: Phase 1 task 1) — Acceptance: lease_exclusion, wrong_actor, epoch_revoked, lost_ack_replay and fresh_open_replay reject bypasses without partial writes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Export canonical schemas/fixtures/provenance and prove installed relocation. (depends on: Phase 1) — Acceptance: controller_bundle_reproducible and controller_without_upper_layers run with OVCAQ/Lantern/source checkout inaccessible.
- [ ] Document Python floor and supported kernel capabilities. (depends on: Phase 2 task 1) — Acceptance: unsupported_operation_refused verifies later operation families are unavailable until implemented.

**Exit Criteria**: Named integration scenarios, `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record missing real-host capabilities as unavailable.

## Test Strategy

### Critical Scenarios
- **Happy path**: controller_without_upper_layers → one installed writer runs without either upper layer.
- **Edge case**: lost_ack_replay → original receipt survives revision changes.
- **Error case**: lease_exclusion → manual and supervised schedulers cannot both own the workflow.

## Risks

- Do not copy OVCAQ process/run fields into authoritative workflow truth.
- A local credential fence prevents accidental wrong-role calls; it is not a sandbox against unrestricted filesystem access.

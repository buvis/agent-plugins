---
default_model: opus
model_tier_rationale: Extraction equivalence, public contracts and concurrent workflow authority require judgment.
lane: full
rework_cap: 3
plan_expansion: allow
eligibility: ls docs/dev/project-management/prds/done/00012-* # link-ok: lifecycle output
---
# Autopilot canonical controller kernel and protocol

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Recovery revision authorized 2026-11-09 by the request to finish portable Autopilot. Supersedes the held v1 for delivery, preserving v1 and its attempt evidence. No publication, live installation, source retirement or custody acceptance.

## Overview

### Problem Statement
Standalone and supervised workflows need the same enforceable writer. The current tested writer lives inside OVCAQ; adding a second legacy backend would split authority.

The v1 attempt stopped during task 7 after prompt-size/replan exhaustion; tasks 1–6 and task-7 tests already landed. Reuse those implementations and evidence after characterization, not by marking new tasks complete from old checkboxes. Close the existing owner, recovery and capacity failures, then complete export and relocation. Preserve the old batch state and counters. Plan bounded tasks with the installed planner's normal budget; do not reuse the failed 40K budget, increase prompt caps or omit test/review roles.

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

Contract A bundle for OVCAQ: commit `plugins/autopilot/contracts/controller-v1.json` as a regular file (no symlink in its path, under 16 MiB). It is a strict JSON object (no duplicate keys, no NaN/Infinity) with exactly these keys: protocol_major (int 1), package_version (nonempty str, the plugin manifest version), schema_digest (nonempty str), fixture_digest (nonempty str), operations (list of str), capabilities (list of str). `python3 controller/main.py --json contract` returns the same protocol_major, schema_digest and fixture_digest, a package_version equal to the bundle's or the bundle's plus `+<build>`, and operations/capabilities that are supersets of the bundle's lists. Document the `sha256sum plugins/autopilot/contracts/controller-v1.json` output (sha256 of the raw file bytes) in `plugins/autopilot/README.md`; OVCAQ pins path and digest as `[workflow] contract_bundle` and `contract_bundle_sha256`. The installed controller argv, stated once here and set by OVCAQ as `[workflow] controller_argv`, is `["python3", "<installed-plugin-root>/controller/main.py"]`.

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
plugins/autopilot/contracts/controller-v1.json
tools/autopilot/export-controller-contract.py
tests/autopilot/test_controller_protocol.py
tests/autopilot/test_controller_actors.py
plugins/autopilot/README.md
plugins/autopilot/CHANGELOG.md
tests/autopilot/test_controller_capacity.py
tests/autopilot/test_controller_owner.py
tests/autopilot/test_controller_owner_recovery.py
tests/autopilot/test_controller_bootstrap.py
tests/autopilot/test_controller_bootstrap_recovery.py
tests/autopilot/test_helper_provenance_real.py
tests/autopilot/test_package.py
tools/autopilot/source-map.json
tools/autopilot/update_helper_map.py
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
New symbols: `contract_bundle_sha256`

This consumer configuration key is defined by Contract A, not an additional runtime dependency.
New symbols: `plugins/autopilot/controller/autopilot_state/protocol.py`, `plugins/autopilot/controller/autopilot_state/actors.py`, `plugins/autopilot/contracts/controller/workflow-v1.json`, `plugins/autopilot/contracts/controller/fixtures-v1.json`, `plugins/autopilot/contracts/controller/provenance.json`, `plugins/autopilot/contracts/controller-v1.json`, `tools/autopilot/export-controller-contract.py`, `tests/autopilot/test_controller_protocol.py`, `tests/autopilot/test_controller_actors.py`

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
- [ ] Close the interrupted owner/capacity implementation against existing regressions. (depends on: Phase 1 task 2) — Acceptance: tests/autopilot/test_controller_capacity.py, tests/autopilot/test_controller_owner.py, tests/autopilot/test_controller_owner_recovery.py, tests/autopilot/test_controller_bootstrap.py and tests/autopilot/test_controller_bootstrap_recovery.py pass without skips, weaker assertions or fixtures that bypass the public protocol.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Export canonical schemas/fixtures/provenance and prove installed relocation. (depends on: Phase 1) — Acceptance: controller_bundle_reproducible and controller_without_upper_layers run with OVCAQ/Tower/source checkout inaccessible. contract_bundle_pinnable asserts `plugins/autopilot/contracts/controller-v1.json` is a regular file under 16 MiB with no symlink in its path, parses as a strict JSON object with exactly the keys protocol_major, package_version, schema_digest, fixture_digest, operations, capabilities and the stated types, that `--json contract` matches it as the Protocol feature states, and that the README digest equals the sha256 of its raw bytes.
- [ ] Document Python floor and supported kernel capabilities. (depends on: Phase 2 task 1) — Acceptance: unsupported_operation_refused verifies later operation families are unavailable until implemented.
- [ ] Refresh delivery evidence for final package bytes, including shared files changed since AP00013, without changing historical receipts. (depends on: Phase 2 task 2) — Acceptance: tests/autopilot/test_helper_provenance_real.py and tests/autopilot/test_package.py pass against truthful current revision/digest evidence; no broad path exemption, test exclusion or fabricated successful gate is introduced. If the existing provenance format cannot represent subsequent ownership, add an explicit tested successor receipt rather than rewriting the earlier receipt's claim.

**Exit Criteria**: Named integration scenarios, `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record missing real-host capabilities as unavailable.

## Test Strategy

### Critical Scenarios
- **Happy path**: controller_without_upper_layers → one installed writer runs without either upper layer.
- **Edge case**: lost_ack_replay → original receipt survives revision changes.
- **Error case**: lease_exclusion → manual and supervised schedulers cannot both own the workflow.

## Risks

- Do not copy OVCAQ process/run fields into authoritative workflow truth.
- A local credential fence prevents accidental wrong-role calls; it is not a sandbox against unrestricted filesystem access.
- The supported installed workflow builds this package; unavailable package skill entry points stay gated until their own implementation and certification pass. Never modify or run a loop in the frozen claude-autopilot repository.
- Completion requires a fresh-session full review of the whole v2 contract, including reused behavior. Historical AP00018 failures are no longer an acceptable baseline exemption.

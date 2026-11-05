---
default_model: opus
model_tier_rationale: Extraction equivalence, public contracts and concurrent workflow authority require judgment.
lane: full
eligibility: ls docs/dev/project-management/prds/done/00020-* # link-ok: lifecycle output
---
# Autopilot controller record commits and extraction conformance

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-29. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
Record-store commits must share workflow authority and survive crashes without duplicating commits or changing unrelated staged work.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
controller_installed_lifecycle → one controller records a complete fresh workflow. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Records

#### Feature: Recoverable record-store commit
- **Description**: Own scoped git effects at accepted workflow boundaries.
- **Inputs**: Accepted phase, configured record roots and the claude-autopilot `skills/run-autopilot/cli/store_tree.py` and verification behavior at pin e960ef1cc43e72bf92593b2f16c7a37c71ea7e48.
- **Outputs**: Committed identity or typed clean/ignored/error result and recoverable intent.
- **Behavior**: Implement records.commit inside the controller; agents/OVCAQ request it. Exclude state/locks/logs/caches, obey ignore rules without force-add, preserve unrelated staged/unstaged changes and anchor pathspecs. Clean/ignored is no-op. Failure blocks advancement without phase replay; reconcile commit-before-ack crash. Preserve code identity separately from record commit SHA.

### Capability: Conformance

#### Feature: One extraction artifact
- **Description**: Provide the installed artifact required by OVCAQ cutover.
- **Inputs**: AP 00018–00020, record fixtures and current OVCAQ regression inventory.
- **Outputs**: Relocatable controller with complete core/jobs/reviews/records contracts.
- **Behavior**: Carry source store/workflow tests as mapped behavioral cases, including cf8be72 and any 00062 reversion changes available at integration. Generate provenance and exact source disposition in AP 00012's independent inventory/map, including retained/replaced/obsolete regression-case evidence; current-source mismatch requires reconciliation before consumers remove old code. Normal target conformance consumes committed fixtures without source checkout or home-directory dependencies. No hidden OVCAQ import or plugin supervisor.

Controller artifact for OVCAQ: commit `plugins/autopilot/contracts/controller-conformance-v1.json` as a regular file (no symlink in its path, under 16 MiB). It is a JSON object with exactly these keys: evidence (list of str containing the exact strings "core", "jobs", "reviews", "records"), package_version (str, the plugin manifest version), controller_digest (str, the sha256 of AP 00018's `plugins/autopilot/contracts/controller-v1.json`), source_pin (str, the OVCAQ commit the extraction was verified against). Document the `sha256sum plugins/autopilot/contracts/controller-conformance-v1.json` output in `plugins/autopilot/README.md`; OVCAQ pins path and digest as `[workflow] controller_artifact` and `controller_artifact_sha256`.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/controller/autopilot_state/records.py
plugins/autopilot/controller/autopilot_state/protocol.py
tests/autopilot/test_controller_records.py
tests/autopilot/test_controller_record_recovery.py
plugins/autopilot/contracts/controller/workflow-v1.json
plugins/autopilot/contracts/controller/fixtures-v1.json
plugins/autopilot/contracts/controller/provenance.json
plugins/autopilot/contracts/controller-conformance-v1.json
tools/autopilot/controller-conformance.py
tools/autopilot/source-inventory.json
tools/autopilot/source-map.json
tests/autopilot/test_controller_installed.py
plugins/autopilot/README.md
plugins/autopilot/CHANGELOG.md
```

### Module: Records
- **Maps to capability**: Records
- **Responsibility**: Own scoped git effects at accepted workflow boundaries.
- **Exports**: Committed identity or typed clean/ignored/error result and recoverable intent.
New symbols: `plugins/autopilot/controller/autopilot_state/records.py`, `tests/autopilot/test_controller_records.py`, `tests/autopilot/test_controller_record_recovery.py`

### Module: Conformance
- **Maps to capability**: Conformance
- **Responsibility**: Provide the installed artifact required by OVCAQ cutover.
- **Exports**: Relocatable controller with complete core/jobs/reviews/records contracts.
New symbols: `plugins/autopilot/contracts/controller-conformance-v1.json`, `tools/autopilot/controller-conformance.py`, `tests/autopilot/test_controller_installed.py`

## Dependency Graph

### Foundation Layer (Phase 0)
AP 00020 completed. OVCAQ 00058 later verifies extraction against its then-current services, including 00062; this PRD need not wait for the OVCAQ consumer. Package containment is required by AGENTS.md:39. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Records**: Depends on Phase 0 and the explicit task order below.
- **Conformance**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Records and Conformance.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Map record commit/reuse behavior and define exact result/recovery payloads. (depends on: declared prerequisites) — Acceptance: record_source_equivalence rechecks pinned source and enumerates clean/ignored/failure outcomes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Implement scoped record commits with intent recovery and replay receipts. (depends on: Phase 0) — Acceptance: unrelated_index_preserved, ignored_store_noop and commit_before_ack_recovery use real temporary git repositories.
- [ ] Wire accepted-boundary bookkeeping and code-identity preservation. (depends on: Phase 1 task 1) — Acceptance: record_failure_blocks_advance and record_only_verification_reuse prevent phase replay or stale verification.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Produce an installed controller conformance bundle for independent consumers. (depends on: Phase 1) — Acceptance: controller_installed_lifecycle and controller_no_upper_imports pass with OVCAQ/Tower unavailable; source-disposition rows contain evidence. controller_artifact_pinnable asserts `plugins/autopilot/contracts/controller-conformance-v1.json` is a regular file under 16 MiB with no symlink in its path, parses as a JSON object with exactly the keys evidence, package_version, controller_digest, source_pin, that evidence contains "core", "jobs", "reviews", "records", that controller_digest equals the sha256 of `plugins/autopilot/contracts/controller-v1.json`, and that the README digest equals the sha256 of its raw bytes.

**Exit Criteria**: Named integration scenarios, `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record missing real-host capabilities as unavailable.

## Test Strategy

### Critical Scenarios
- **Happy path**: controller_installed_lifecycle → one controller records a complete fresh workflow.
- **Edge case**: ignored_store_noop → ignored records remain ignored.
- **Error case**: commit_before_ack_recovery → retry returns the original commit without duplicates.

## Risks

- Git operations and state transactions are not one atomic write; recovery is required.
- No publishing or source deletion follows merely from a local conformance bundle.

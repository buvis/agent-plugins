---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 89d074f1a3cb
source_prd: 00014-autopilot-host-execution-v1.md
severity: high
---

# Triage: The full tests/autopilot suite is NOT green at the end of this rework: 49 fai...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `pre-existing-suite-red`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: The full tests/autopilot suite is NOT green at the end of this rework: 49 failed, 1442 passed, 46337 subtests passed. ALL 49 are pre-existing and none was introduced by this rework. 48 are controller tests (test_controller_capacity.py, test_controller_owner.py, test_controller_owner_recovery.py) covering the controller state store, owner credentials and capacity reserves, which this PRD does not touch; the 49th is the test_new_helper_files_are_owned_and_digested_from_current_bytes provenance failure recorded separately. PROVEN by running those three controller files at the session-start commit a76b5f2 in a clean throwaway worktree (since removed): 48 failed, 9 passed, with an identical test-and-subtest failure list. Every other documented suite is green: unittest discover -s scripts (59 OK), scripts/validate.py (3 packages, 15 skills), and the four specflow suites (54, 387, 58, 41 OK).

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `89d074f1a3cb`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `89d074f1a3cb` from `00014-autopilot-host-execution-v1.md` until a human triages it
- **Exports**: none

### Dependencies
- triage: No dependencies (foundation)

## Tasks

### Phase 0: Foundation
- [ ] triage: promote to backlog or close - Acceptance: this file is no longer under docs/dev/project-management/prds/hold/

### Phase 1: Core
No implementation tasks until attended triage.

## Success Criteria

- This file is no longer under `docs/dev/project-management/prds/hold/`.

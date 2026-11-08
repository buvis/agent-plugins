---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: bed03de8ba70
source_prd: 00014-autopilot-host-execution-v1.md
severity: high
---

# Triage: test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `pre-existing-test-failure`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes still fails after the task 16 generator run, now at line 300 in assert_refreshed_evidence: it asserts digest(git show <receipts package_revision>:plugins/autopilot/CHANGELOG.md) == digest(CHANGELOG.md on disk), but the pinned package_revision is 444d733a (an AP00013 commit) whose CHANGELOG predates every AP00014 bullet. PROVEN PRE-EXISTING: the same test fails at the session-start commit a76b5f2 in a clean worktree, there at line 309 on the autopilot.py digest staleness; that earlier assertion was masking this one, so the generator run did not cause the failure, it uncovered it. Fixing it means repointing the delivery receipts package_revision to a commit containing the current CHANGELOG bytes, which is AP00013 receipts data, not the source map, and which the rework design explicitly says is "AP00014s own and not this generators to rewrite"; it may also move frozen digests (INVENTORY_SHA, OTHER_ASSETS_SHA) that other tests pin.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `bed03de8ba70`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `bed03de8ba70` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

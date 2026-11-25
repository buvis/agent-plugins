---
catchup: skip
design: skip
ledger: deferred/202611242306-deferred.json
ledger_key: 4b1cb1d3ab5c
source_prd: 00019-autopilot-controller-lifecycle-v1.md
severity: high
---

# Triage: R3: jobs are never scoped to a PRD or cleared between PRDs. reset_prd_fields...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611242306`, ledger `deferred/202611242306-deferred.json`, type `cap-overflow`, cycle `3`, consensus `1/4`, op_id `c9e62758e000-dd3`, raised against `00019-autopilot-controller-lifecycle-v1.md`.

Issue: R3: jobs are never scoped to a PRD or cleared between PRDs. reset_prd_fields keeps workflow.jobs, _derive_job_specs skips task ids already planned, and jobs.plan rejects duplicate ids, so a second PRD in a batch is silently never planned or collides; stale first-PRD jobs stay in next_job (plugins/autopilot/controller/autopilot_state/lifecycle.py:57). No test covers a second PRD.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `4b1cb1d3ab5c`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `4b1cb1d3ab5c` from `00019-autopilot-controller-lifecycle-v1.md` until a human triages it
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

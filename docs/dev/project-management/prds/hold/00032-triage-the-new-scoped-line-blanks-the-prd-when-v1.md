---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 7bd65b444e9d
source_prd: 00013-autopilot-session-helpers-v1.md
severity: high
---

# Triage: The new `_scoped` line blanks the PRD when a job's manifest lacks a `prd:` re...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `cap-overflow`, cycle `3`, consensus `1/5`, op_id `8843ead3f828-dd4`, raised against `00013-autopilot-session-helpers-v1.md`.

Issue: The new `_scoped` line blanks the PRD when a job's manifest lacks a `prd:` ref (review_stage.py:290-291 substitutes ""), so a blind reviewer with an empty PRD is reported as a successful staging. Refuse `invalid-input` when a roster job whose prompt inlines the PRD has no `prd:` ref.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `7bd65b444e9d`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `7bd65b444e9d` from `00013-autopilot-session-helpers-v1.md` until a human triages it
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

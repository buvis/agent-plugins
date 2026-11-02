---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 5f49a064480d
source_prd: 00013-autopilot-session-helpers-v1.md
severity: high
---

# Triage: Tail-sweep close is refused whenever the chosen rows are a subset of the revi...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `cap-overflow`, cycle `2`, consensus `1/4`, op_id `1327c6fd3b62-dd4`, raised against `00013-autopilot-session-helpers-v1.md`.

Issue: Tail-sweep close is refused whenever the chosen rows are a subset of the review evidence findings. _link demands every evidence finding be linked by exactly one chosen row, but tail sweep is designed to skip coverage. Probed: ok false, attribution_mismatch, never linked [F5]. The tail-sweep path only succeeds when the evidence holds exactly the swept findings.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `5f49a064480d`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `5f49a064480d` from `00013-autopilot-session-helpers-v1.md` until a human triages it
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

---
catchup: skip
design: skip
ledger: deferred/202611151706-deferred.json
ledger_key: 3fe811c83d0d
source_prd: 00014-autopilot-host-execution-v2.md
severity: critical
---

# Triage: The R11 fix makes every controller-keyed duty refuse with missing_controller_...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611151706`, ledger `deferred/202611151706-deferred.json`, type `critical-finding`, cycle `2`, consensus `2/4`, op_id `eb9e7d070d06-dd0`, raised against `00014-autopilot-host-execution-v2.md`.

Issue: The R11 fix makes every controller-keyed duty refuse with missing_controller_seam when the session is unbound, contradicting design §8's unbound skip; 4 probe tests fail with control_did_not_execute.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `3fe811c83d0d`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `3fe811c83d0d` from `00014-autopilot-host-execution-v2.md` until a human triages it
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

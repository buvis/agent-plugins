---
catchup: skip
design: skip
ledger: deferred/202611242306-deferred.json
ledger_key: c3b22a4f5184
source_prd: 00019-autopilot-controller-lifecycle-v1.md
severity: high
---

# Triage: R5: replay admission treats a ledger row as proof of commit although the saga...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611242306`, ledger `deferred/202611242306-deferred.json`, type `cap-overflow`, cycle `3`, consensus `1/4`, op_id `c9e62758e000-dd5`, raised against `00019-autopilot-controller-lifecycle-v1.md`.

Issue: R5: replay admission treats a ledger row as proof of commit although the saga appends it before committing, and the row lacks the authorizing actor and request digest; a crash before the append leaves the original request unable to resume (plugins/autopilot/controller/autopilot_state/protocol.py:269). cap-check classifies this as a regression introduced by this cycle rework at bf131b9.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `c3b22a4f5184`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `c3b22a4f5184` from `00019-autopilot-controller-lifecycle-v1.md` until a human triages it
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

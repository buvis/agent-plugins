---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: aa2b2230c4f6
source_prd: 00013-autopilot-session-helpers-v1.md
severity: high
---

# Triage: Cycle-1 R6 still permits live-state overwrite through hard links. An ordinary...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `cap-overflow`, cycle `2`, consensus `1/4`, op_id `1327c6fd3b62-dd8`, raised against `00013-autopilot-session-helpers-v1.md`.

Issue: Cycle-1 R6 still permits live-state overwrite through hard links. An ordinary output pathname hard-linked to state.json passes _in_live_state, then write_bytes truncates the shared inode. Refuse multiply linked output files before export. cap-check classifies this as a regression introduced by this cycle rework (commit 6984cf5).

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `aa2b2230c4f6`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `aa2b2230c4f6` from `00013-autopilot-session-helpers-v1.md` until a human triages it
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

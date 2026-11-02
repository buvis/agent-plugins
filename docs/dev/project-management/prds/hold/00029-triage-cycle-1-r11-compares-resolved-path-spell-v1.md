---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 07d12ef52860
source_prd: 00013-autopilot-session-helpers-v1.md
severity: high
---

# Triage: Cycle-1 R11 compares resolved path spellings rather than file identity. On ca...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `cap-overflow`, cycle `2`, consensus `1/4`, op_id `1327c6fd3b62-dd10`, raised against `00013-autopilot-session-helpers-v1.md`.

Issue: Cycle-1 R11 compares resolved path spellings rather than file identity. On case-insensitive filesystems, argv SCRIPT.PY and log script.py can name the same file while comparing unequal, allowing the script to be deleted before execution. Compare existing candidates with samefile and retain lexical checks for absent destinations. cap-check classifies this as a regression introduced by this cycle rework (commit 6984cf5).

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `07d12ef52860`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `07d12ef52860` from `00013-autopilot-session-helpers-v1.md` until a human triages it
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

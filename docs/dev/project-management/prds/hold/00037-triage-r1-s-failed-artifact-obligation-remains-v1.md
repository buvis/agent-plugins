---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: d1cc8c0f04fd
source_prd: 00013-autopilot-session-helpers-v2.md
severity: high
---

# Triage: R1's failed-artifact obligation remains incomplete: `_empty_pinned` invalidat...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `cap-overflow`, cycle `2`, consensus `1/5`, op_id `4dff7e357a11-dd3`, raised against `00013-autopilot-session-helpers-v2.md`.

Issue: R1's failed-artifact obligation remains incomplete: `_empty_pinned` invalidates by pathname after closing the written descriptor. If the child renames the artifact and installs a replacement, close failure leaves complete reusable JSON at the renamed location because the identity check skips cleanup. Retain a descriptor through finalization and invalidate the written inode on failure; test rename plus close failure while preserving the replacement.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `d1cc8c0f04fd`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `d1cc8c0f04fd` from `00013-autopilot-session-helpers-v2.md` until a human triages it
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

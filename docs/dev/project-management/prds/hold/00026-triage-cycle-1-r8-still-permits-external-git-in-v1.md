---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 44682b79e546
source_prd: 00013-autopilot-session-helpers-v1.md
severity: high
---

# Triage: Cycle-1 R8 still permits external Git internals with nonstandard directory na...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `cap-overflow`, cycle `2`, consensus `1/4`, op_id `1327c6fd3b62-dd7`, raised against `00013-autopilot-session-helpers-v1.md`.

Issue: Cycle-1 R8 still permits external Git internals with nonstandard directory names. An external --separate-git-dir directory makes _toplevel return None, which is treated as an ordinary destination. Detect Git metadata directories before accepting external roots; add a separate-git-dir regression test.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `44682b79e546`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `44682b79e546` from `00013-autopilot-session-helpers-v1.md` until a human triages it
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

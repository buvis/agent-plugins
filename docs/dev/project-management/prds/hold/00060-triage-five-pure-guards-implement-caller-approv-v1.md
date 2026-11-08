---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: b8e3598ecfb1
source_prd: 00014-autopilot-host-execution-v1.md
severity: 🟠
---

# Triage: Five pure guards implement caller approval instead of their required checks:...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, op_id `cf5f8a63cae1-dd18`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: Five pure guards implement caller approval instead of their required checks: `_check` allows empty context and ignores paths/artifacts. Implement each duty’s actual local rule, including document-location validation, and test prohibited artifacts rather than `ok` booleans.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `b8e3598ecfb1`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `b8e3598ecfb1` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

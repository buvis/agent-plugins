---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: f9fbb95bdb60
source_prd: 00014-autopilot-host-execution-v1.md
severity: 🟠
---

# Triage: Compatibility generation preserves stale positive claims when a previously av...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, op_id `cf5f8a63cae1-dd20`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: Compatibility generation preserves stale positive claims when a previously available host loses its binary: `capability is None` skips rewriting its existing bundle. Replace that bundle with an empty capability set or remove it safely; test available-to-unavailable regeneration.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `f9fbb95bdb60`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `f9fbb95bdb60` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

---
catchup: skip
design: skip
ledger: deferred/202611151706-deferred.json
ledger_key: e0872806294f
source_prd: 00014-autopilot-host-execution-v2.md
severity: critical
---

# Triage: The shipped hooks deny unrelated work in every project: every controller-keye...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611151706`, ledger `deferred/202611151706-deferred.json`, type `critical-finding`, cycle `2`, consensus `1/4`, op_id `eb9e7d070d06-dd3`, raised against `00014-autopilot-host-execution-v2.md`.

Issue: The shipped hooks deny unrelated work in every project: every controller-keyed duty refuses when the session is unbound or has no seam, with no check that autopilot is involved.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `e0872806294f`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `e0872806294f` from `00014-autopilot-host-execution-v2.md` until a human triages it
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

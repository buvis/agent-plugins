---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 4e4060a5e87f
source_prd: 00014-autopilot-host-execution-v1.md
severity: critical
---

# Triage: Availability is claimed without proof, and the claim contradicts the adapter'...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, consensus `[1/4]`, op_id `cf5f8a63cae1-dd7`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: Availability is claimed without proof, and the claim contradicts the adapter's own code. `codex.probe` reports identity, delegation and isolation "available" whenever a binary and an auth file exist. But `codex.session_identity()` always returns None (codex.py:64) and `codex.can_delegate()` always returns False (codex.py:68). `claude.probe` hardcodes interception "available" (claude.py:50) with no hook registration or interception test.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `4e4060a5e87f`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `4e4060a5e87f` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

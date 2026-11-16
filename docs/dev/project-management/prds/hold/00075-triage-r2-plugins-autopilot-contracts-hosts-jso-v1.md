---
catchup: skip
design: skip
ledger: deferred/202611151706-deferred.json
ledger_key: 27a0123dfa90
source_prd: 00014-autopilot-host-execution-v2.md
severity: high
---

# Triage: R2 (plugins/autopilot/contracts/hosts.json:7): Claude hooks are not retained...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611151706`, ledger `deferred/202611151706-deferred.json`, type `cap-overflow`, cycle `3`, consensus `1/4`, op_id `eb9e7d070d06-dd6`, raised against `00014-autopilot-host-execution-v2.md`.

Issue: R2 (plugins/autopilot/contracts/hosts.json:7): Claude hooks are not retained through supported packaging, and no client's registration is activated. plugin.json has no hooks field, no .claude-plugin manifest ships, and both registrations carry "activated": false (README says so too). The enforcement therefore exists only as generated assets. The probe proves registration only in a temp copy where it writes its own manifest. The spec asks to retain Claude hooks and prove each extra client's registration.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `27a0123dfa90`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `27a0123dfa90` from `00014-autopilot-host-execution-v2.md` until a human triages it
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

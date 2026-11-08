---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 24b896b82114
source_prd: 00014-autopilot-host-execution-v1.md
severity: 🟠
---

# Triage: The AP00014_TARGETS exclusion in tests/autopilot/test_helper_provenance_real....

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, op_id `cf5f8a63cae1-dd10`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: The AP00014_TARGETS exclusion in tests/autopilot/test_helper_provenance_real.py is a legitimate scoping fix on its own. It mirrors the AP00018 CONTROLLER_PREFIXES precedent, and the frozen OTHER_ASSETS_SHA hash should not cover a later PRD's rows. It is not a masked failure in itself, because the three real failures above still fail loudly. But nothing replaces it: no test checks that the AP00014 rows exist, have correct digests or have correct owners, and the generator cannot regenerate them. The skip also does not fix the regression Task 10 claimed it fixed, because the rest of that file still fails. Add an AP00014 row-integrity test, as AP00018 has.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `24b896b82114`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `24b896b82114` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

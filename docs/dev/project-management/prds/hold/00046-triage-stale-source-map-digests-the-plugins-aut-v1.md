---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 83609eba480c
source_prd: 00014-autopilot-host-execution-v1.md
severity: critical
---

# Triage: Stale source-map digests. The `plugins/autopilot/scripts/autopilot.py` and `p...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, consensus `[1/4]`, op_id `cf5f8a63cae1-dd4`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: Stale source-map digests. The `plugins/autopilot/scripts/autopilot.py` and `plugins/autopilot/CHANGELOG.md` rows have `destination_blob_sha256` values that no longer match the files on disk. I recomputed all digests: the 13 new AP00014 rows match, and only these two are stale. This breaks test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `83609eba480c`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `83609eba480c` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

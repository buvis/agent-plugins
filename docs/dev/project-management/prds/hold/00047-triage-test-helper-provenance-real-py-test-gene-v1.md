---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: f87130c5f231
source_prd: 00014-autopilot-host-execution-v1.md
severity: critical
---

# Triage: test_helper_provenance_real.py::test_generator_check_accepts_the_committed_ma...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, consensus `[1/4]`, op_id `cf5f8a63cae1-dd5`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: test_helper_provenance_real.py::test_generator_check_accepts_the_committed_map fails with "source-map.json is not the generated helper map". The 13 AP00014 rows were hand-added and the generator does not produce them, so the committed map drifts from the tool that owns it.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `f87130c5f231`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `f87130c5f231` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

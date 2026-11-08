---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 4343f2a1bdae
source_prd: 00014-autopilot-host-execution-v1.md
severity: critical
---

# Triage: test_package.py::test_target_only_checkout_denies_source_home_and_network_but...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, consensus `[1/4]`, op_id `cf5f8a63cae1-dd3`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: test_package.py::test_target_only_checkout_denies_source_home_and_network_but_exports_policy and test_local_boundary.py::test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations fail. The `_CAPABILITIES` list grew by hosts-v1, guards-v1 and diagnose-v1, so the list now has 13 entries where the tests expect 3+7. Only tests/autopilot/test_facade.py was updated for this.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `4343f2a1bdae`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `4343f2a1bdae` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

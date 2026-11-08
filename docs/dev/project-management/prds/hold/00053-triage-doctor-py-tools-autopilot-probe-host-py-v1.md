---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 34698fc3464f
source_prd: 00014-autopilot-host-execution-v1.md
severity: 🟠
---

# Triage: doctor.py, tools/autopilot/probe-host.py and the new autopilot.py modes (--pr...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, op_id `cf5f8a63cae1-dd11`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: doctor.py, tools/autopilot/probe-host.py and the new autopilot.py modes (--probe-host, --run-guard, --diagnose) have no tests. rg over tests/ finds no test calling diagnose, probe-host.py or those flags. The PRD scenarios relocated_host_probe (probe writes only under docs/dev/tmp/autopilot/) and missing_guard_refused at the CLI level are not exercised. Task 8 required a temp-root test that no path outside the root is touched.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `34698fc3464f`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `34698fc3464f` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

---
catchup: skip
design: skip
ledger: deferred/202611151706-deferred.json
ledger_key: 546ffb5a2191
source_prd: 00014-autopilot-host-execution-v2.md
severity: high
---

# Triage: R3 (plugins/autopilot/scripts/hosts.py:146): "isolation" and the other host c...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611151706`, ledger `deferred/202611151706-deferred.json`, type `cap-overflow`, cycle `3`, consensus `1/4`, op_id `eb9e7d070d06-dd7`, raised against `00014-autopilot-host-execution-v2.md`.

Issue: R3 (plugins/autopilot/scripts/hosts.py:146): "isolation" and the other host capabilities are still constants. Each adapter sets IMPLEMENTED_CAPABILITIES = frozenset({...}), and no adapter holds isolation-specific code. statuses_from turns that constant plus an auth-presence check into "supported". resolve_profile marks a profile "resolvable" from the same constants, and --resolve-roles passes observed=None. The spec says host support, isolation and real probing cannot be closed by a capability constant.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `546ffb5a2191`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `546ffb5a2191` from `00014-autopilot-host-execution-v2.md` until a human triages it
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

---
catchup: skip
design: skip
ledger: deferred/202611151706-deferred.json
ledger_key: b13cc6ebe34a
source_prd: 00014-autopilot-host-execution-v2.md
severity: high
---

# Triage: R8 (tools/autopilot/probe-host.py:83): `recorded_session` accepts any schema-...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611151706`, ledger `deferred/202611151706-deferred.json`, type `cap-overflow`, cycle `3`, consensus `1/4`, op_id `eb9e7d070d06-dd12`, raised against `00014-autopilot-host-execution-v2.md`.

Issue: R8 (tools/autopilot/probe-host.py:83): `recorded_session` accepts any schema-1 object containing `host_id`, without validating the expected host, native session shape, or session ID type. Empty strings, numbers, or another host’s records can produce observed identity and isolation. Validate the record against the requested host and `NativeSession` rules before accepting its ID.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `b13cc6ebe34a`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `b13cc6ebe34a` from `00014-autopilot-host-execution-v2.md` until a human triages it
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

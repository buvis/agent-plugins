---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: d5d304c4ed3f
source_prd: 00014-autopilot-host-execution-v1.md
severity: 🟠
---

# Triage: Standalone mode emits no usable next-session instruction. Every adapter's `bu...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, op_id `cf5f8a63cae1-dd16`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: Standalone mode emits no usable next-session instruction. Every adapter's `build_job_argv` returns None, so `request_cross_session_job` yields `{"argv": None, ...}`. The spec requires "emit next-session instructions for manual launch".

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `d5d304c4ed3f`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `d5d304c4ed3f` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

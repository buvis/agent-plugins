---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 8ab0b783bc60
source_prd: 00014-autopilot-host-execution-v1.md
severity: 🟠
---

# Triage: The codex_gemini_role_capabilities test does not exercise the PRD requirement...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, op_id `cf5f8a63cae1-dd12`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: The codex_gemini_role_capabilities test does not exercise the PRD requirement. `_resolve_candidate_hosts` is a test-local function that only checks hosts.json set containment. The "required capabilities" per role are invented inside the test, not derived from review-policy-v1.json job_ids. Claude is excluded by construction, and the assertNotEqual({"claude"}) is vacuous. No production code resolves job_id to host, and no mandatory role is checked.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `8ab0b783bc60`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `8ab0b783bc60` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

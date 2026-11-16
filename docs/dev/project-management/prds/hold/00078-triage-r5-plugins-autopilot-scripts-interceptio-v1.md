---
catchup: skip
design: skip
ledger: deferred/202611151706-deferred.json
ledger_key: 4a298cac820a
source_prd: 00014-autopilot-host-execution-v2.md
severity: high
---

# Triage: R5 (plugins/autopilot/scripts/interception.py:157): Stateful guards behave di...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611151706`, ledger `deferred/202611151706-deferred.json`, type `cap-overflow`, cycle `3`, consensus `1/4`, op_id `eb9e7d070d06-dd9`, raised against `00014-autopilot-host-execution-v2.md`.

Issue: R5 (plugins/autopilot/scripts/interception.py:157): Stateful guards behave differently in the two modes. interception.py skips controller-keyed duties (custody_push, state_integrity, review_completeness, live_job, post_handoff, departure, context_reinjection) when no .autopilot/controller directory is found. A repo without that marker gets no custody-push or state-integrity enforcement, which is fail-open. In a bound repo, run_hook hard-codes seam=None, so every push, Stop and patch write refuses with no way to supply a seam. The spec says stateful guards call the same seam in both modes.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `4a298cac820a`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `4a298cac820a` from `00014-autopilot-host-execution-v2.md` until a human triages it
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

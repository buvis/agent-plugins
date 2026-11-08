---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 509c1d10ca71
source_prd: 00014-autopilot-host-execution-v1.md
severity: 🟠
---

# Triage: doctor `profile` is not derived as specified. It is "claude-free" iff "identi...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `deferred_decision`, cycle `1`, op_id `cf5f8a63cae1-dd13`, raised against `00014-autopilot-host-execution-v1.md`.

Issue: doctor `profile` is not derived as specified. It is "claude-free" iff "identity" is in codex's or gemini's declared capabilities, which is a constant for the committed hosts.json. The spec says claude-free when every mandatory review-policy role resolves to codex or gemini.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `509c1d10ca71`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `509c1d10ca71` from `00014-autopilot-host-execution-v1.md` until a human triages it
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

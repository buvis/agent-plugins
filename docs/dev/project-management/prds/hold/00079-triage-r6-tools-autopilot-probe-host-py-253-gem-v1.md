---
catchup: skip
design: skip
ledger: deferred/202611151706-deferred.json
ledger_key: 7c643354dbde
source_prd: 00014-autopilot-host-execution-v2.md
severity: high
---

# Triage: R6 (tools/autopilot/probe-host.py:253): Gemini still launches as `["gemini",...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611151706`, ledger `deferred/202611151706-deferred.json`, type `cap-overflow`, cycle `3`, consensus `1/4`, op_id `eb9e7d070d06-dd10`, raised against `00014-autopilot-host-execution-v2.md`.

Issue: R6 (tools/autopilot/probe-host.py:253): Gemini still launches as `["gemini", "-p"]`, although the contract requires the prompt as the argument following `-p`. Sending it only through stdin does not satisfy that invocation. The fake accepts this malformed argv, masking the integration defect. Pass the prompt in argv and assert the complete invocation.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `7c643354dbde`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `7c643354dbde` from `00014-autopilot-host-execution-v2.md` until a human triages it
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

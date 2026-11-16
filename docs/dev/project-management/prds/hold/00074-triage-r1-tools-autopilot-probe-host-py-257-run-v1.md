---
catchup: skip
design: skip
ledger: deferred/202611151706-deferred.json
ledger_key: f33043f62575
source_prd: 00014-autopilot-host-execution-v2.md
severity: high
---

# Triage: R1 (tools/autopilot/probe-host.py:257): `run_live_gemini` runs `_check_no_esc...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202611151706`, ledger `deferred/202611151706-deferred.json`, type `cap-overflow`, cycle `3`, consensus `2/4`, op_id `eb9e7d070d06-dd5`, raised against `00014-autopilot-host-execution-v2.md`.

Issue: R1 (tools/autopilot/probe-host.py:257): `run_live_gemini` runs `_check_no_escaping_symlink`, `copytree` and `mkdir` outside the try block that `run_live` uses for `prepare`. The gemini branch returns at line 306, before that try. A symlink escape or a copy error in the Gemini path therefore ends the probe with a traceback. Claude and Codex report `resource_escape` or `preparation_failed` and launch nothing. No test covers a Gemini preparation failure. Route the Gemini preparation through the same handler, and add a test.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `f33043f62575`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `f33043f62575` from `00014-autopilot-host-execution-v2.md` until a human triages it
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

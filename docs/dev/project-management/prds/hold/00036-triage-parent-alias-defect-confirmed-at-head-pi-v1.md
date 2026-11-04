---
catchup: skip
design: skip
ledger: deferred/202610250001-deferred.json
ledger_key: 4ad02a513505
source_prd: 00013-autopilot-session-helpers-v2.md
severity: high
---

# Triage: Parent-alias defect confirmed at HEAD: `_pinned_parent_fd` resolves below-roo...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610250001`, ledger `deferred/202610250001-deferred.json`, type `cap-overflow`, cycle `2`, consensus `4/5`, op_id `4dff7e357a11-dd1`, raised against `00013-autopilot-session-helpers-v2.md`.

Issue: Parent-alias defect confirmed at HEAD: `_pinned_parent_fd` resolves below-root symlinks in the mixed-spelling fallback, and `_symlinked_component`'s root-alias stop rule skips a path that leaves the repo and returns through a symlink to the root. Reproduced: with an aliased root, `run_verification` returns ok and writes the log through two symlinks, while the same-spelling run refuses with the wrong slug (`sink-failed`). Tracked targets are still refused and no outside-root write was observed. The CHANGELOG bullets "treat an aliased project root and a resolved one alike" and "refuses an output path that passes through a symlink ... whichever way ... spelled" overclaim until fixed. Fix: make the stop rule apply only to the leading root spelling, not to any later component, and drop `resolve()` from the fallback in favour of descending the unresolved names; add a test where the return symlink points at the root itself. Eve independently re-ran the recorded probe against HEAD bytes: the `mixed_symlink` row overwrote the internal sentinel, the `same_symlink` row refused with ENOTDIR.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `4ad02a513505`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `4ad02a513505` from `00013-autopilot-session-helpers-v2.md` until a human triages it
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

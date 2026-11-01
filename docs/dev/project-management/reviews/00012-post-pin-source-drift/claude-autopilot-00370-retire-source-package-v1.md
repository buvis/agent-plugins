---
default_model: opus
model_tier_rationale: Cross-repository evidence and source retirement require judgment about preserved behavior and consumer closure.
lane: full
eligibility: test -f docs/dev/project-management/reviews/00370-retirement-authorization.json # link-ok: lifecycle input
---
# Retire the superseded Claude Autopilot package

Source: the agent-plugins [discovery 00011 port plan](../../../../../../agent-plugins/docs/dev/project-management/discovery/00011-autopilot-agent-plugins-port.md) and its [completeness review](../../../../../../agent-plugins/docs/dev/project-management/reviews/00011-autopilot-port-completeness-review.md). This PRD remains held. Planning does not activate retirement, change installations, publish, archive the remote or delete history.

## Overview

### Problem Statement
The portable Autopilot/controller, OVCAQ and Lantern need a single explicit source-retirement gate. Packaging success or assigned inventory owners do not prove that the old package can disappear.

### Target Users
The maintainer and existing users of buvis/claude-autopilot.

### Success Metrics
retirement_requires_complete_evidence rejects partial, stale or unavailable parity; source_package_retired preserves history/license/documentation while removing only the approved tracked package paths.

## Functional Decomposition

### Capability: Readiness

#### Feature: Exact evidence and consumer closure
- **Description**: Verify the replacement and the approved retirement target ledger before any removal.
- **Inputs**: AP 00017/00021 installed package/controller evidence, OV 00058–00061/00065 evidence, Lantern 00003 evidence, held OV 00010/00011 cutover receipts, the complete AP source inventory/map and an explicit source target ledger with recorded user authorization.
- **Outputs**: A versioned readiness report listing every accepted obligation and consumer disposition, or a refusal naming missing evidence.
- **Behavior**: Require AP 00017's real Codex + Gemini standalone and managed Claude-free certificates, all advertised host/advanced profiles, unchanged mandatory review semantics and no live legacy batch. Codex-only, fake-host and Codex-build/Claude-review evidence cannot substitute for the selected certificates. Match exact tested artifact versions/digests. Re-scan executable consumers across the portfolio, central marketplace, shell launchers, agent-skills copies and authoritative global instructions; historical citations may remain classified. Verify completed cutover receipts instead of changing other repositories here. The authorization artifact records the attended user's approval of the exact target-ledger digest; an agent cannot create its own approval. Hold remains until these inputs exist.

### Capability: Retirement

#### Feature: Recoverable source package removal
- **Description**: Remove the superseded package from the current source tree with a durable migration pointer.
- **Inputs**: A successful readiness report and approved exact tracked paths under plugin.json, .claude-plugin, skills, agents and hooks.
- **Outputs**: A source tree that no longer advertises the old installable package, a README pointing to tested replacements and source-history recovery references.
- **Behavior**: Premise: each removal target still matches its approved hash and has no active consumer or batch. Recheck immediately before changing it; mismatch skips/reports the affected action and leaves retirement incomplete. Use version-controlled removals, retain LICENSE, CHANGELOG, management evidence and Git history, and record the last source commit. Update release tooling to refuse another old-package release. Do not archive/delete the remote, remove unrelated files, rewrite history, repoint consumers or publish any artifact. No second legacy implementation is copied into an archive directory.

## Structural Decomposition

### Repository Structure

```text
dev/bin/retirement-check
dev/bin/test_retirement_check.py
dev/bin/release-checks
dev/bin/release
docs/dev/project-management/reviews/00370-retirement-targets.json
docs/dev/project-management/reviews/00370-retirement-readiness.json
docs/dev/project-management/reviews/00370-retirement-authorization.json
README.md
CHANGELOG.md
LICENSE
plugin.json
.claude-plugin/
skills/
agents/
hooks/
```

### Module: Readiness
- **Maps to capability**: Readiness
- **Responsibility**: Verify explicit imported receipts, inventory completeness, current consumers and target hashes; never infer evidence from adjacent checkouts.
- **Exports**: retirement-check --evidence FILE --targets FILE --authorization FILE --json; exit 0 only when every requirement is satisfied, otherwise exit 1 with per-obligation diagnostics. Report-only checks never mutate source or installations.
New symbols: `dev/bin/retirement-check`, `dev/bin/test_retirement_check.py`, `docs/dev/project-management/reviews/00370-retirement-targets.json`, `docs/dev/project-management/reviews/00370-retirement-readiness.json`, `docs/dev/project-management/reviews/00370-retirement-authorization.json`

### Module: Retirement
- **Maps to capability**: Retirement
- **Responsibility**: Apply the already-approved tracked removal ledger and preserve recovery and migration documentation.
- **Exports**: Source removal verification and a retired-package release refusal.
New symbols: None; existing package and release files only.

## Dependency Graph

### Foundation Layer (Phase 0)
All external evidence and the attended authorization are prerequisites to activating this held PRD. The approval is not requested mid-implementation. Readiness may report missing inputs without changing source.
- **Readiness contracts**: Explicit receipts, frozen source obligations and approved target-ledger digest.

### Core Layer (Phase 1)
- **Readiness**: Depends on Foundation Layer inputs.
- **Retirement**: Depends on Readiness passing and an immediate source/consumer recheck.

### Integration Layer (Phase 2)
- **Final verification**: Depends on Readiness and Retirement; uses the retained checker, not removed source runtime tests.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Verify every premise and freeze the pre-removal report.

**Tasks**:
- [ ] Implement the retained read-only checker and fixture tests; validate the supplied receipts, source inventory, regression dispositions, consumer scan and authorized target hashes. (depends on: declared prerequisites) — Acceptance: retirement_requires_complete_evidence, target_drift_refused, active_consumer_refused and live_batch_refused reject missing, unavailable, stale or unapproved inputs on temporary fixtures; failed real premises are skipped/reported without removal.

**Exit Criteria**: Readiness inputs are complete and every proposed tracked path remains bound to its approved content.

### Phase 1: Core
**Goal**: Remove only the superseded installable package.

**Tasks**:
- [ ] Apply the approved version-controlled target ledger, update README/CHANGELOG and make old release entry points refuse publication. (depends on: Phase 0) — Acceptance: source_package_retired, history_and_license_preserved and old_release_refused pass after rechecking each removal premise; preserve unrelated changes.

**Exit Criteria**: The source no longer presents the old package as installable, and all history/recovery references remain available.

### Phase 2: Integration
**Goal**: Prove source removal did not create dangling active consumers.

**Tasks**:
- [ ] Re-scan executable consumers and record final evidence with the replacement artifact digests and source retirement commit. (depends on: Phase 1) — Acceptance: retirement_consumer_closure finds no active old-package dependency; historical references are explicitly classified.

**Exit Criteria**: `bash dev/bin/release-checks` passes the retained retirement checks; the readiness report names exact artifacts and no unresolved required inventory row. No remote publication or repository archival occurs.

## Test Strategy

### Critical Scenarios
- **Happy path**: source_package_retired → approved current package paths disappear and tested replacement instructions remain.
- **Edge case**: target_drift_refused → a concurrent source edit prevents its removal and retirement stays incomplete.
- **Error case**: retirement_requires_complete_evidence → a missing Claude-free/advanced/consumer receipt cannot be waived by a green package validator.

## Risks

- Evidence can become stale while repositories evolve; recheck pinned identities and active consumers at execution.
- The source builds its replacement; no live legacy batch may be retired underneath itself.
- Remote archival, marketplace publication and other external commitments require their separate prepared authorization; they are outside this PRD.

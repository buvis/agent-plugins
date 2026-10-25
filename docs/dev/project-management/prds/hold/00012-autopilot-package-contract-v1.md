---
default_model: opus
model_tier_rationale: Asset equivalence and review data contracts require judgment.
lane: full
rework_cap: 3
plan_expansion: allow
---
# Autopilot package and review artifact contracts

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Implementation specification only; no publication, live installation, migration or source retirement. Corrected after the 2026-10-25 completeness review: re-read the amended design and reconcile any work already started before accepting this PRD.

## Overview

### Problem Statement
The source packages plugin content together with a runtime. The portable package preserves plugin content and later ships one canonical controller (00018–00021), usable without OVCAQ. This foundation owns review-policy/evidence contracts, not scheduler or TUI implementation.

### Target Users
Users invoking local skills and maintainers integrating the same plugin with OVCAQ.

### Success Metrics
The named behavior scenarios pass, and source-map evidence assigns every affected behavior to its correct owner. No unsupported capability is advertised.

## Functional Decomposition

### Capability: Package

#### Feature: Preserved assets
- **Description**: Preserved assets within the declared ownership boundary.
- **Inputs**: Pinned source e960ef1cc43e72bf92593b2f16c7a37c71ea7e48 in /Users/bob/git/src/github.com/buvis/claude-autopilot; read content with git show at that pin, not checkout HEAD.
- **Outputs**: One independently distributable package with a file-for-file reference map.
- **Behavior**: Retain eleven skills, eighteen personas and all 59 reference files in their skill-relative locations. No consolidation into five documents. Manifest uses the v1 schema URL https://agent-plugins.org/schemas/1.0.0/plugin.schema.json, name autopilot, version 0.10.0, source author and MIT license. Gate unimplemented entry points explicitly. Freeze a source-derived expected inventory independently of destinations; map every principal/expanded behavior ID, configuration/state field, code-only discovery and regression case to a delivery repository/PRD and observable acceptance scenario. Keep file provenance separately: preserved means byte equality, adapted sections need reasons, and gated assets still exist. Ship LICENSE inside the package. Normal tests use committed provenance and fixtures, never the old checkout; explicit maintainer source verification uses --source-root at the pin. Recheck source object availability and target ownership before copying; skip/report conflicting premises.

### Capability: Contracts

#### Feature: Plugin-owned evidence and policy
- **Description**: Plugin-owned evidence and policy within the declared ownership boundary.
- **Inputs**: The corrected boundary design and source review schemas/rubrics.
- **Outputs**: Versioned review-policy/evidence schema, golden cases and deterministic export.
- **Behavior**: Own only plugin policy and artifacts: schema_version, procedure, policy_digest, source_bindings, reviewer_jobs, artifacts, findings, groups, rubric_verdicts and verification. Local evidence has no accepted-phase flag; controller request/actor/revision fields belong to AP 00018's separate envelope. Policy declares required IDs, artifact rules and cap two; semantic rubric prose stays external. AP 00018 defines controller schema/errors/operations; this PRD does not duplicate them. Preserve full and fast-track mandatory rosters and solo's required zero-context review; resolve conditional source roles explicitly. Separate clean reviewer results from findings; zero defects is valid. Bind evidence to expected policy/profile, PRD/code/input digests and attributed result/job references. Golden cases cover clean rosters, missing/failed roles, missing rubrics, malformed groups and stale input bindings with unchanged policy. AP 00020 verifies actual native-job provenance.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/plugin.json  # Assets
plugins/autopilot/README.md  # Assets
plugins/autopilot/CHANGELOG.md  # Assets
plugins/autopilot/LICENSE  # Assets
README.md  # Assets
plugins/autopilot/skills/design-solution/SKILL.md  # Assets
plugins/autopilot/skills/fast-track/SKILL.md  # Assets
plugins/autopilot/skills/plan-tasks/SKILL.md  # Assets
plugins/autopilot/skills/review-blindly/SKILL.md  # Assets
plugins/autopilot/skills/review-plan/SKILL.md  # Assets
plugins/autopilot/skills/review-work-completion/SKILL.md  # Assets
plugins/autopilot/skills/run-autopilot/SKILL.md  # Assets
plugins/autopilot/skills/use-codex/SKILL.md  # Assets
plugins/autopilot/skills/use-gemini/SKILL.md  # Assets
plugins/autopilot/skills/use-sonnet/SKILL.md  # Assets
plugins/autopilot/skills/work/SKILL.md  # Assets
plugins/autopilot/skills/design-solution/references/  # Assets
plugins/autopilot/skills/fast-track/references/  # Assets
plugins/autopilot/skills/plan-tasks/references/  # Assets
plugins/autopilot/skills/review-blindly/references/  # Assets
plugins/autopilot/skills/review-plan/references/  # Assets
plugins/autopilot/skills/review-work-completion/references/  # Assets
plugins/autopilot/skills/run-autopilot/references/  # Assets
plugins/autopilot/skills/use-codex/references/  # Assets
plugins/autopilot/skills/work/references/  # Assets
plugins/autopilot/references/personas/  # Assets
plugins/autopilot/contracts/review-evidence-v1.json  # Contracts
plugins/autopilot/contracts/review-policy-v1.json  # Contracts
plugins/autopilot/contracts/review-fixtures-v1.json  # Contracts
plugins/autopilot/scripts/autopilot.py  # Contracts
tools/autopilot/export-policy.py  # Contracts
tools/autopilot/prerequisites.py  # Contracts
tools/autopilot/source-map.json  # Contracts
tools/autopilot/source-pin.json  # Contracts
tools/autopilot/source-inventory.json  # Contracts
tools/autopilot/check-source.py  # Contracts
tools/autopilot/requirements-test.txt  # Contracts
tests/autopilot/test_contract.py  # Contracts
tests/autopilot/test_package.py  # Contracts
tests/autopilot/test_prerequisites.py  # Contracts
.github/workflows/validate.yml  # Contracts
```

### Module: Assets
- **Maps to capability**: Package
- **Responsibility**: Preserve content/attribution and source layout; record runtime-bound prose for adaptation in 00015.
- **Exports**: Portable metadata, named skills and preserved reference/persona files.
- **Location**: `plugins/autopilot/skills/design-solution/references/cardinal-sins.md`, `plugins/autopilot/skills/fast-track/references/lane-dispatch.md`, `plugins/autopilot/skills/fast-track/references/spec-card.md`, `plugins/autopilot/skills/plan-tasks/references/design-rationale.md`, `plugins/autopilot/skills/plan-tasks/references/task-examples.md`, `plugins/autopilot/skills/review-blindly/references/rubric.md`, `plugins/autopilot/skills/review-plan/references/question-examples.md`, `plugins/autopilot/skills/review-work-completion/references/agent-invocation.md`, `plugins/autopilot/skills/review-work-completion/references/agent-registry.md`, `plugins/autopilot/skills/review-work-completion/references/design-rationale.md`, `plugins/autopilot/skills/review-work-completion/references/output-formats.md`, `plugins/autopilot/skills/review-work-completion/references/retry-policy.md`, `plugins/autopilot/skills/review-work-completion/references/review-coverage-format.md`, `plugins/autopilot/skills/review-work-completion/references/review-dimensions.md`, `plugins/autopilot/skills/review-work-completion/references/rubric.md`, `plugins/autopilot/skills/run-autopilot/references/audit-log-format.md`, `plugins/autopilot/skills/run-autopilot/references/batch-report-format.md`, `plugins/autopilot/skills/run-autopilot/references/dashboard-format.md`, `plugins/autopilot/skills/run-autopilot/references/decision-framework.md`, `plugins/autopilot/skills/run-autopilot/references/design-rationale.md`, `plugins/autopilot/skills/run-autopilot/references/doubt-review-rubric.md`, `plugins/autopilot/skills/run-autopilot/references/hook-recovery.md`, `plugins/autopilot/skills/run-autopilot/references/lane-fast-track.md`, `plugins/autopilot/skills/run-autopilot/references/lane-solo.md`, `plugins/autopilot/skills/run-autopilot/references/model-ladder.md`, `plugins/autopilot/skills/run-autopilot/references/phase-build.md`, `plugins/autopilot/skills/run-autopilot/references/phase-done.md`, `plugins/autopilot/skills/run-autopilot/references/phase-review.md`, `plugins/autopilot/skills/run-autopilot/references/recovery.md`, `plugins/autopilot/skills/run-autopilot/references/state-schema.md`, `plugins/autopilot/skills/run-autopilot/references/unattended-contract.md`, `plugins/autopilot/skills/run-autopilot/references/waves.md`, `plugins/autopilot/skills/use-codex/references/dispatch-contract.md`, `plugins/autopilot/skills/use-codex/references/host-markers.md`, `plugins/autopilot/skills/work/references/adversarial-test-prompt.md`, `plugins/autopilot/skills/work/references/attempt-logging.md`, `plugins/autopilot/skills/work/references/code-quality-examples.md`, `plugins/autopilot/skills/work/references/code-quality-principles.md`, `plugins/autopilot/skills/work/references/codex-implementor.md`, `plugins/autopilot/skills/work/references/codex-integration.md`, `plugins/autopilot/skills/work/references/dashboard-state-sync.md`, `plugins/autopilot/skills/work/references/design-rationale.md`, `plugins/autopilot/skills/work/references/final-verification.md`, `plugins/autopilot/skills/work/references/gate-failure.md`, `plugins/autopilot/skills/work/references/gemini-integration.md`, `plugins/autopilot/skills/work/references/pat-rerun-prompt.md`, `plugins/autopilot/skills/work/references/per-task-review.md`, `plugins/autopilot/skills/work/references/qwen-integration.md`, `plugins/autopilot/skills/work/references/red-check.md`, `plugins/autopilot/skills/work/references/rework-mode.md`, `plugins/autopilot/skills/work/references/self-deslop-prompt.md`, `plugins/autopilot/skills/work/references/simplification-mandate.md`, `plugins/autopilot/skills/work/references/style-gate.md`, `plugins/autopilot/skills/work/references/subagent-dispatch.md`, `plugins/autopilot/skills/work/references/task-boundary-handoff.md`, `plugins/autopilot/skills/work/references/task-splitting.md`, `plugins/autopilot/skills/work/references/tess-prompt.md`, `plugins/autopilot/skills/work/references/tess-retry-prompt.md`, `plugins/autopilot/skills/work/references/test-author-prompt.md`, `plugins/autopilot/references/personas/alice.md`, `plugins/autopilot/references/personas/blake.md`, `plugins/autopilot/references/personas/bob.md`, `plugins/autopilot/references/personas/carl.md`, `plugins/autopilot/references/personas/cora.md`, `plugins/autopilot/references/personas/eve.md`, `plugins/autopilot/references/personas/grace.md`, `plugins/autopilot/references/personas/ivan.md`, `plugins/autopilot/references/personas/mallory.md`, `plugins/autopilot/references/personas/pat.md`, `plugins/autopilot/references/personas/rita.md`, `plugins/autopilot/references/personas/toby.md`, `plugins/autopilot/references/personas/trent.md`, `plugins/autopilot/references/personas/victor.md`, `plugins/autopilot/references/personas/worker-fable.md`, `plugins/autopilot/references/personas/worker-haiku.md`, `plugins/autopilot/references/personas/worker-opus.md`, `plugins/autopilot/references/personas/worker-sonnet.md`
New symbols: `plugins/autopilot/LICENSE`, `plugins/autopilot/plugin.json`, `plugins/autopilot/README.md`, `plugins/autopilot/CHANGELOG.md`, `plugins/autopilot/skills/design-solution/SKILL.md`, `plugins/autopilot/skills/fast-track/SKILL.md`, `plugins/autopilot/skills/plan-tasks/SKILL.md`, `plugins/autopilot/skills/review-blindly/SKILL.md`, `plugins/autopilot/skills/review-plan/SKILL.md`, `plugins/autopilot/skills/review-work-completion/SKILL.md`, `plugins/autopilot/skills/run-autopilot/SKILL.md`, `plugins/autopilot/skills/use-codex/SKILL.md`, `plugins/autopilot/skills/use-gemini/SKILL.md`, `plugins/autopilot/skills/use-sonnet/SKILL.md`, `plugins/autopilot/skills/work/SKILL.md`, `plugins/autopilot/skills/design-solution/references/cardinal-sins.md`, `plugins/autopilot/skills/fast-track/references/lane-dispatch.md`, `plugins/autopilot/skills/fast-track/references/spec-card.md`, `plugins/autopilot/skills/plan-tasks/references/design-rationale.md`, `plugins/autopilot/skills/plan-tasks/references/task-examples.md`, `plugins/autopilot/skills/review-blindly/references/rubric.md`, `plugins/autopilot/skills/review-plan/references/question-examples.md`, `plugins/autopilot/skills/review-work-completion/references/agent-invocation.md`, `plugins/autopilot/skills/review-work-completion/references/agent-registry.md`, `plugins/autopilot/skills/review-work-completion/references/design-rationale.md`, `plugins/autopilot/skills/review-work-completion/references/output-formats.md`, `plugins/autopilot/skills/review-work-completion/references/retry-policy.md`, `plugins/autopilot/skills/review-work-completion/references/review-coverage-format.md`, `plugins/autopilot/skills/review-work-completion/references/review-dimensions.md`, `plugins/autopilot/skills/review-work-completion/references/rubric.md`, `plugins/autopilot/skills/run-autopilot/references/audit-log-format.md`, `plugins/autopilot/skills/run-autopilot/references/batch-report-format.md`, `plugins/autopilot/skills/run-autopilot/references/dashboard-format.md`, `plugins/autopilot/skills/run-autopilot/references/decision-framework.md`, `plugins/autopilot/skills/run-autopilot/references/design-rationale.md`, `plugins/autopilot/skills/run-autopilot/references/doubt-review-rubric.md`, `plugins/autopilot/skills/run-autopilot/references/hook-recovery.md`, `plugins/autopilot/skills/run-autopilot/references/lane-fast-track.md`, `plugins/autopilot/skills/run-autopilot/references/lane-solo.md`, `plugins/autopilot/skills/run-autopilot/references/model-ladder.md`, `plugins/autopilot/skills/run-autopilot/references/phase-build.md`, `plugins/autopilot/skills/run-autopilot/references/phase-done.md`, `plugins/autopilot/skills/run-autopilot/references/phase-review.md`, `plugins/autopilot/skills/run-autopilot/references/recovery.md`, `plugins/autopilot/skills/run-autopilot/references/state-schema.md`, `plugins/autopilot/skills/run-autopilot/references/unattended-contract.md`, `plugins/autopilot/skills/run-autopilot/references/waves.md`, `plugins/autopilot/skills/use-codex/references/dispatch-contract.md`, `plugins/autopilot/skills/use-codex/references/host-markers.md`, `plugins/autopilot/skills/work/references/adversarial-test-prompt.md`, `plugins/autopilot/skills/work/references/attempt-logging.md`, `plugins/autopilot/skills/work/references/code-quality-examples.md`, `plugins/autopilot/skills/work/references/code-quality-principles.md`, `plugins/autopilot/skills/work/references/codex-implementor.md`, `plugins/autopilot/skills/work/references/codex-integration.md`, `plugins/autopilot/skills/work/references/dashboard-state-sync.md`, `plugins/autopilot/skills/work/references/design-rationale.md`, `plugins/autopilot/skills/work/references/final-verification.md`, `plugins/autopilot/skills/work/references/gate-failure.md`, `plugins/autopilot/skills/work/references/gemini-integration.md`, `plugins/autopilot/skills/work/references/pat-rerun-prompt.md`, `plugins/autopilot/skills/work/references/per-task-review.md`, `plugins/autopilot/skills/work/references/qwen-integration.md`, `plugins/autopilot/skills/work/references/red-check.md`, `plugins/autopilot/skills/work/references/rework-mode.md`, `plugins/autopilot/skills/work/references/self-deslop-prompt.md`, `plugins/autopilot/skills/work/references/simplification-mandate.md`, `plugins/autopilot/skills/work/references/style-gate.md`, `plugins/autopilot/skills/work/references/subagent-dispatch.md`, `plugins/autopilot/skills/work/references/task-boundary-handoff.md`, `plugins/autopilot/skills/work/references/task-splitting.md`, `plugins/autopilot/skills/work/references/tess-prompt.md`, `plugins/autopilot/skills/work/references/tess-retry-prompt.md`, `plugins/autopilot/skills/work/references/test-author-prompt.md`, `plugins/autopilot/references/personas/alice.md`, `plugins/autopilot/references/personas/blake.md`, `plugins/autopilot/references/personas/bob.md`, `plugins/autopilot/references/personas/carl.md`, `plugins/autopilot/references/personas/cora.md`, `plugins/autopilot/references/personas/eve.md`, `plugins/autopilot/references/personas/grace.md`, `plugins/autopilot/references/personas/ivan.md`, `plugins/autopilot/references/personas/mallory.md`, `plugins/autopilot/references/personas/pat.md`, `plugins/autopilot/references/personas/rita.md`, `plugins/autopilot/references/personas/toby.md`, `plugins/autopilot/references/personas/trent.md`, `plugins/autopilot/references/personas/victor.md`, `plugins/autopilot/references/personas/worker-fable.md`, `plugins/autopilot/references/personas/worker-haiku.md`, `plugins/autopilot/references/personas/worker-opus.md`, `plugins/autopilot/references/personas/worker-sonnet.md`

### Module: Contracts
- **Maps to capability**: Contracts
- **Responsibility**: Define evidence data and local capability declarations; provide source checks, CI and read-only backlog dependencies.
- **Exports**: Local capability output, policy export and python3 tools/autopilot/prerequisites.py --prd NNNNN.
New symbols: `tools/autopilot/source-inventory.json`, `tools/autopilot/check-source.py`, `plugins/autopilot/contracts/review-evidence-v1.json`, `plugins/autopilot/contracts/review-policy-v1.json`, `plugins/autopilot/contracts/review-fixtures-v1.json`, `plugins/autopilot/scripts/autopilot.py`, `tools/autopilot/export-policy.py`, `tools/autopilot/prerequisites.py`, `tools/autopilot/source-map.json`, `tools/autopilot/source-pin.json`, `tools/autopilot/requirements-test.txt`, `tests/autopilot/test_contract.py`, `tests/autopilot/test_package.py`, `tests/autopilot/test_prerequisites.py`

## Dependency Graph

### Foundation Layer (Phase 0)
No OVCAQ prerequisite. Current containment: AGENTS.md:39; manifest validation: scripts/validate.py:61. Gate unfinished commands. Create a read-only prerequisite table: 00013→00012; 00014→00012+00013; 00015→00013+00014; 00018→00012; 00019→00018; 00020→00019; 00021→00020; 00016→00015+00020+00021; 00017→00016. Exit 0 only when every predecessor has a done-bucket file; missing/unknown IDs exit 1 with diagnostics. Never fetch/write or probe OVCAQ. No self-dependency on tools created by a later PRD. The backlog `eligibility:` lines gate selection with plain `ls` checks on the done bucket; this tool is the maintainer view of the same table and never gates selection. Python 3.12 is the Autopilot execution/test baseline; retain the validator's existing Python 3.10 CI job. The local Autopilot test command is `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`: the sandbox cannot pip-install into the mise interpreters, and uv provisions 3.12 and the test dependencies itself.
- **Characterization/contracts**: Establish the inputs consumed by Assets and Contracts.

### Core Layer (Phase 1)
- **Assets**: Depends on the Phase 0 inputs.
- **Contracts**: Depends on Phase 0 and the explicitly ordered task prerequisites below.

### Integration Layer (Phase 2)
- **Public-boundary tests and documentation**: Depend on Assets and Contracts.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Verify source premises and establish exact contracts.

**Tasks**:
- [ ] Freeze the independent pinned inventory, behavior/regression mappings and per-file/section disposition; define evidence/policy schemas and source-derived fixtures, with test-only jsonschema validation. (depends on: declared prerequisites) — Acceptance: source_inventory_mapping and review_schema reject omitted IDs, unmapped regressions, weakened lane rosters and stale or unattributed evidence while accepting clean complete reviews; source pin/target premise is rechecked, with skip/report on conflict.

**Exit Criteria**: The named task tests pass. Recheck changed-content premises; if false, skip/report affected edits without forcing them.

### Phase 1: Core
**Goal**: Implement behavior under the correct owner.

**Tasks**:
- [ ] Port canonical metadata, eleven skill files and personas without merging source references. (depends on: Phase 0) — Acceptance: content_roster checks preserved byte hashes and documented section adaptations against committed pinned provenance; check-source verifies the capture using an explicitly supplied checkout.
- [ ] Copy every skill reference file 1:1 using the declared locations and source map. (depends on: Phase 1 task 1) — Acceptance: reference_tree_preserved and resource_closure require every promised file and in-package runtime dependency; declared external capabilities retain explicit fallbacks and unfinished entry points refuse before old calls.
- [ ] Implement the minimal local capability facade and deterministic policy export. (depends on: Phase 1 task 2) — Acceptance: policy_export_reproducible proves stable digests and package relocation without requiring unimplemented controller capabilities or source checkout.

**Exit Criteria**: The named task tests pass. Recheck changed-content premises; if false, skip/report affected edits without forcing them.

### Phase 2: Integration
**Goal**: Prove public behavior and document capability evidence.

**Tasks**:
- [ ] Implement the exact read-only prerequisite contract, including both content and controller branches before 00016 exists. (depends on: Phase 1) — Acceptance: prerequisites_missing and local_prerequisites_ignore_ovcaq verify predecessor truth, stable exit codes and no writes/subprocess lookup on local paths.
- [ ] Add a Python 3.12 Autopilot CI job that installs `tools/autopilot/requirements-test.txt` and runs `python -m pytest tests/autopilot -q`, preserving the existing Python 3.10 validator job, run the new tests immediately, and update package changelog/root table as gated. (depends on: Phase 2 task 1) — Acceptance: package_self_contained, resource_closure, target_only_checkout and ci_autopilot_wired run from an isolated target copy with source/author-home/network unavailable; no missing-source skip. Preserve the existing plugins job and its pinned actions.

**Exit Criteria**: The named integration scenarios and `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record real-host unavailability explicitly; it does not certify execution. No publishing or cutover occurs.

## Test Strategy

### Critical Scenarios
- **Happy path**: reference_tree_preserved → Every source skill/reference/persona has a declared destination and intact required sections.
- **Edge case**: local_prerequisites_ignore_ovcaq → Local readiness is identical with missing or broken OVCAQ.
- **Error case**: review_schema → Malformed review artifacts cannot claim runtime completion.

## Risks

- Metadata and content validation do not certify host execution.
- The independent source inventory defines expected obligations; the destination map cannot shrink that set. Future unavailable rows remain incomplete for their promised release profiles.

---
default_model: opus
model_tier_rationale: Large procedure equivalence and precise runtime capability boundaries require judgment.
lane: full
rework_cap: 3
plan_expansion: allow
eligibility: ls docs/dev/project-management/prds/done/00013-* docs/dev/project-management/prds/done/00014-* # link-ok: lifecycle output
---
# Autopilot skill procedures and runtime boundaries

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Implementation specification only; no publication, live installation, migration or source retirement.

## Overview

### Problem Statement
All skill procedures must preserve source behavior while separating explicit local work from controller-owned queue, state and phase execution.

### Target Users
Users invoking individual skills and OVCAQ sessions executing a phase with the same plugin content.

### Success Metrics
The named behavior scenarios pass, and source-map evidence assigns every affected behavior to its correct owner. No unsupported capability is advertised.

## Functional Decomposition

### Capability: Procedures

#### Feature: Local skills and managed procedure templates
- **Description**: Local skills and managed procedure templates within the declared ownership boundary.
- **Inputs**: Preserved skill/reference tree, local helpers, host capabilities and explicit input artifacts.
- **Outputs**: Executable local procedures, managed templates and a per-command capability map.
- **Behavior**: Adapt source sections in place with provenance. Design/planning/review and work on explicit tasks/cards can produce local artifacts; they do not mark queued PRDs complete or maintain attempts/state. Stateful commands remain gated until PRD 00016 wires the bundled controller; then selection, durable resume, handoff and history work without OVCAQ. Automatic cross-session scheduling alone requires OVCAQ. Do not imply every source option works locally merely because its skill loads.

### Capability: Review policy

#### Feature: Lenses, classification and integrations
- **Description**: Lenses, classification and integrations within the declared ownership boundary.
- **Inputs**: Explicit local procedure choice or controller-issued effort-lane decision, review evidence and optional tools.
- **Outputs**: Complete required review artifacts and classified proposals ready for runtime persistence.
- **Behavior**: Keep Alice/Blake/Bob and all source fast-track lenses, blindness, R1–R5, semantic rework grouping and custody/cap classification in the plugin. The Autopilot controller owns effort-lane routing/escalation and durable custody/review updates. Only controller-accepted evidence certifies phase completion in either launch mode. Preserve Qwen, engram, catchup, consensus and notification fallbacks; do not remove required lenses when tools are absent. Full requires Alice/Blake/Bob plus policy-activated roles; fast-track preserves Alice/Blake/Eve/Bob plus conditional Carl; solo requires its zero-context consensus result and escalation checks. Keep roles separate from provider placement and retain the source-parity implementor-diversity guard. Verification records and record-store commits are controller operations, not helper side effects.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/skills/design-solution/SKILL.md  # Procedures
plugins/autopilot/skills/fast-track/SKILL.md  # Procedures
plugins/autopilot/skills/plan-tasks/SKILL.md  # Procedures
plugins/autopilot/skills/review-blindly/SKILL.md  # Procedures
plugins/autopilot/skills/review-plan/SKILL.md  # Procedures
plugins/autopilot/skills/review-work-completion/SKILL.md  # Procedures
plugins/autopilot/skills/run-autopilot/SKILL.md  # Procedures
plugins/autopilot/skills/use-codex/SKILL.md  # Procedures
plugins/autopilot/skills/use-gemini/SKILL.md  # Procedures
plugins/autopilot/skills/use-sonnet/SKILL.md  # Procedures
plugins/autopilot/skills/work/SKILL.md  # Procedures
plugins/autopilot/skills/design-solution/references/  # Procedures
plugins/autopilot/skills/fast-track/references/  # Procedures
plugins/autopilot/skills/plan-tasks/references/  # Procedures
plugins/autopilot/skills/review-blindly/references/  # Procedures
plugins/autopilot/skills/review-plan/references/  # Procedures
plugins/autopilot/skills/review-work-completion/references/  # Procedures
plugins/autopilot/skills/run-autopilot/references/  # Procedures
plugins/autopilot/skills/use-codex/references/  # Procedures
plugins/autopilot/skills/work/references/  # Procedures
plugins/autopilot/README.md  # Procedures
plugins/autopilot/CHANGELOG.md  # Procedures
tests/autopilot/test_procedures.py  # Procedures
tests/autopilot/test_blind_inputs.py  # Procedures
plugins/autopilot/scripts/review_stage.py  # Review
plugins/autopilot/scripts/rework_groups.py  # Review
plugins/autopilot/scripts/custody.py  # Review
plugins/autopilot/scripts/integrations.py  # Review
plugins/autopilot/scripts/verification.py  # Review
plugins/autopilot/scripts/reports.py  # Review
plugins/autopilot/scripts/autopilot.py  # Review
plugins/autopilot/contracts/capabilities.json  # Review
tools/autopilot/source-map.json  # Review
tests/autopilot/test_review_rosters.py  # Review
tests/autopilot/test_integrations.py  # Review
tests/autopilot/test_inventory.py  # Review
```

### Module: Procedures
- **Maps to capability**: Procedures
- **Responsibility**: Adapt all source procedure sections without collapsing their references.
- **Exports**: Local skill invocations and explicit controller-required diagnostics.
- **Location**: `plugins/autopilot/skills/design-solution/references/cardinal-sins.md`, `plugins/autopilot/skills/fast-track/references/lane-dispatch.md`, `plugins/autopilot/skills/fast-track/references/spec-card.md`, `plugins/autopilot/skills/plan-tasks/references/design-rationale.md`, `plugins/autopilot/skills/plan-tasks/references/task-examples.md`, `plugins/autopilot/skills/review-blindly/references/rubric.md`, `plugins/autopilot/skills/review-plan/references/question-examples.md`, `plugins/autopilot/skills/review-work-completion/references/agent-invocation.md`, `plugins/autopilot/skills/review-work-completion/references/agent-registry.md`, `plugins/autopilot/skills/review-work-completion/references/design-rationale.md`, `plugins/autopilot/skills/review-work-completion/references/output-formats.md`, `plugins/autopilot/skills/review-work-completion/references/retry-policy.md`, `plugins/autopilot/skills/review-work-completion/references/review-coverage-format.md`, `plugins/autopilot/skills/review-work-completion/references/review-dimensions.md`, `plugins/autopilot/skills/review-work-completion/references/rubric.md`, `plugins/autopilot/skills/run-autopilot/references/audit-log-format.md`, `plugins/autopilot/skills/run-autopilot/references/batch-report-format.md`, `plugins/autopilot/skills/run-autopilot/references/dashboard-format.md`, `plugins/autopilot/skills/run-autopilot/references/decision-framework.md`, `plugins/autopilot/skills/run-autopilot/references/design-rationale.md`, `plugins/autopilot/skills/run-autopilot/references/doubt-review-rubric.md`, `plugins/autopilot/skills/run-autopilot/references/hook-recovery.md`, `plugins/autopilot/skills/run-autopilot/references/lane-fast-track.md`, `plugins/autopilot/skills/run-autopilot/references/lane-solo.md`, `plugins/autopilot/skills/run-autopilot/references/model-ladder.md`, `plugins/autopilot/skills/run-autopilot/references/phase-build.md`, `plugins/autopilot/skills/run-autopilot/references/phase-done.md`, `plugins/autopilot/skills/run-autopilot/references/phase-review.md`, `plugins/autopilot/skills/run-autopilot/references/recovery.md`, `plugins/autopilot/skills/run-autopilot/references/state-schema.md`, `plugins/autopilot/skills/run-autopilot/references/unattended-contract.md`, `plugins/autopilot/skills/run-autopilot/references/waves.md`, `plugins/autopilot/skills/use-codex/references/dispatch-contract.md`, `plugins/autopilot/skills/use-codex/references/host-markers.md`, `plugins/autopilot/skills/work/references/adversarial-test-prompt.md`, `plugins/autopilot/skills/work/references/attempt-logging.md`, `plugins/autopilot/skills/work/references/code-quality-examples.md`, `plugins/autopilot/skills/work/references/code-quality-principles.md`, `plugins/autopilot/skills/work/references/codex-implementor.md`, `plugins/autopilot/skills/work/references/codex-integration.md`, `plugins/autopilot/skills/work/references/dashboard-state-sync.md`, `plugins/autopilot/skills/work/references/design-rationale.md`, `plugins/autopilot/skills/work/references/final-verification.md`, `plugins/autopilot/skills/work/references/gate-failure.md`, `plugins/autopilot/skills/work/references/gemini-integration.md`, `plugins/autopilot/skills/work/references/pat-rerun-prompt.md`, `plugins/autopilot/skills/work/references/per-task-review.md`, `plugins/autopilot/skills/work/references/qwen-integration.md`, `plugins/autopilot/skills/work/references/red-check.md`, `plugins/autopilot/skills/work/references/rework-mode.md`, `plugins/autopilot/skills/work/references/self-deslop-prompt.md`, `plugins/autopilot/skills/work/references/simplification-mandate.md`, `plugins/autopilot/skills/work/references/style-gate.md`, `plugins/autopilot/skills/work/references/subagent-dispatch.md`, `plugins/autopilot/skills/work/references/task-boundary-handoff.md`, `plugins/autopilot/skills/work/references/task-splitting.md`, `plugins/autopilot/skills/work/references/tess-prompt.md`, `plugins/autopilot/skills/work/references/tess-retry-prompt.md`, `plugins/autopilot/skills/work/references/test-author-prompt.md`
New symbols: `tests/autopilot/test_procedures.py`, `tests/autopilot/test_blind_inputs.py`

### Module: Review
- **Maps to capability**: Review policy
- **Responsibility**: Keep semantic procedures and artifact reports external; classify each command/option by runtime requirement.
- **Exports**: Review artifacts, grouped findings and capability declarations, not runtime routing or transitions.
New symbols: `plugins/autopilot/scripts/integrations.py`, `plugins/autopilot/scripts/reports.py`, `plugins/autopilot/contracts/capabilities.json`, `tests/autopilot/test_review_rosters.py`, `tests/autopilot/test_integrations.py`, `tests/autopilot/test_inventory.py`

## Dependency Graph

### Foundation Layer (Phase 0)
Plugin 00013/00014 completed. Preserve the 00012 reference tree and section mappings; recheck ownership/pin before edits, skip/report conflicts. Before any mapped edit, repin the source and land the open rows in `docs/dev/project-management/reviews/00012-post-pin-source-drift.md`. Fix the replan budget defect D1-D3 in `docs/dev/project-management/plans/00018-replan-3.md` (the 40000 floor sits below the 55000 estimator overhead, so every replan from 2 on stalls) when adapting `recovery.md`, `plan-tasks/SKILL.md` and `state-schema.md`. Containment rules: AGENTS.md:39. Runtime-only behavior may be tested with fake responses, but remains unavailable to real users until 00016. Phase-wide review still needs the required fresh-session boundary; local invocation does not waive it.
- **Characterization/contracts**: Establish the inputs consumed by Procedures and Review.

### Core Layer (Phase 1)
- **Procedures**: Depends on the Phase 0 inputs.
- **Review**: Depends on Phase 0 and the explicitly ordered task prerequisites below.

### Integration Layer (Phase 2)
- **Public-boundary tests and documentation**: Depend on Procedures and Review.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Verify source premises and establish exact contracts.

**Tasks**:
- [ ] Map every frozen inventory ID, field/default/failure rule and source regression to its local, controller-dependent or advanced-runtime owner, delivery PRD and acceptance scenario. (depends on: declared prerequisites) — Acceptance: source_behavior_coverage rejects unowned rows and lifecycle capabilities incorrectly advertised as local.

**Exit Criteria**: The named task tests pass. Recheck changed-content premises; if false, skip/report affected edits without forcing them.

### Phase 1: Core
**Goal**: Implement behavior under the correct owner.

**Tasks**:
- [ ] Adapt design-solution, plan-tasks and review-plan to explicit inputs and artifacts. (depends on: Phase 0) — Acceptance: local_design_plan_artifacts preserves rework/expansion/tier recommendations without persisting queue/task state.
- [ ] Adapt work and provider-runner skills with isolated roles, test-first/adversarial/red checks and actual verification evidence. (depends on: Phase 1 task 1) — Acceptance: local_explicit_task_work proves useful work without runtime bookkeeping or automatic next-task selection.
- [ ] Adapt review-work-completion, review-blindly and fast-track procedures with complete lenses and retained section-level semantics. (depends on: Phase 1 task 2) — Acceptance: blind_input_exclusion and fast_track_roster prove isolation, rubric coverage and explicit controller-required refusals where lifecycle is needed.

**Exit Criteria**: The named task tests pass. Recheck changed-content premises; if false, skip/report affected edits without forcing them.

### Phase 2: Integration
**Goal**: Prove public behavior and document capability evidence.

**Tasks**:
- [ ] Wire optional integrations and controller-dependent templates; update capability documentation and changelog. (depends on: Phase 1) — Acceptance: optional_integrations_absent and controller_entry_not_yet_wired cover source fallback rules and refusal before state mutation.
- [ ] Reconcile every content/helper/behavior and regression row against the independent source inventory, destination map and external-via-verb boundary; unavailable rows stay unresolved for promised profiles. (depends on: Phase 2 task 1) — Acceptance: source_behavior_coverage and no_plugin_supervisor verify no supervisor or helper-owned writer; controller-owned lifecycle/routing/records are intentional.

**Exit Criteria**: The named integration scenarios and `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record real-host unavailability explicitly; it does not certify execution. No publishing or cutover occurs.

## Test Strategy

### Critical Scenarios
- **Happy path**: local_design_plan_artifacts → Useful design/task/review files are produced with no OVCAQ dependency.
- **Edge case**: optional_integrations_absent → Documented fallbacks preserve every mandatory review lens.
- **Error case**: controller_entry_not_yet_wired → Stateful commands refuse until controller integration; after 00016 only automatic scheduling needs OVCAQ.

## Risks

- The distributable plugin includes its one controller; it must not contain OVCAQ's process scheduler or Lantern.
- Specflow handoff remains outside this PRD.

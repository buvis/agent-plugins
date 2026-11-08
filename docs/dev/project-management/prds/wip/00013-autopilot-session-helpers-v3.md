---
default_model: opus
session_model: opus
model_tier_rationale: Race-free descriptor handling and fail-closed containment need judgment, not transcription.
lane: full
rework_cap: 2
design: run
doubt_reviewer: fable
---
# Autopilot session-local helpers v3

Filename: 00013-autopilot-session-helpers-v3.md. Same feature identity as v1 and v2. This is the one bounded corrective recovery the user authorized on 2026-11-05 after v2 held at its exhausted cap (cycle 2/2, `cap_regression`). It does not reset, reopen or overwrite v1 or v2 caps, attempts, reviews, stubs or deferrals. Mark v2 superseded only after v3 passes its fresh full completion review. Only the corrective tasks below remain. No publication, live installation, migration, retirement or automatic push is authorized by this PRD. No v4 follows automatically.

Source: docs/dev/project-management/prds/hold/00013-autopilot-session-helpers-v2.md; docs/dev/project-management/prds/hold/00013-autopilot-session-helpers-v1.md; docs/dev/project-management/designs/00013-autopilot-session-helpers-v1-design.md; docs/dev/project-management/autopilot/reports/00013-v3-admission.md. The coordinator selects v3 explicitly; this specification grants no worker PRD lifecycle authority.

Review evidence: docs/dev/project-management/reviews/00013-autopilot-session-helpers-v2-review-2.md:79-110. T1 fixes R1. T2 fixes R3. T3 fixes R4/R6/R9/R12 as one defect. T4 fixes R15/R21 and refreshes delivery evidence for R20/R23. The admission report records every other row's disposition with evidence. Recheck each premise against current code first; if it is false, keep the code and report the evidence.

Recovery bindings: docs/dev/project-management/prds/hold/00034-triage-cycle-2-of-2-hit-the-rework-cap-with-2-u-v1.md is the cap stall stub; docs/dev/project-management/prds/hold/00036-triage-parent-alias-defect-confirmed-at-head-pi-v1.md binds R1; docs/dev/project-management/prds/hold/00037-triage-r1-s-failed-artifact-obligation-remains-v1.md binds R3; docs/dev/project-management/prds/hold/00035-triage-the-19-ap00018-controller-failures-remai-v1.md is the AP 00018 controller deferral. Preserve these and stubs 00022-00033. The coordinator owns their closure.

## Overview

### Problem Statement
V2 delivered the corrective helper work but its rework left two HIGH regressions. The pinned sink descent accepts a path that leaves the repository and returns through a symlink to the root, and it resolves below-root symlinks when the root is spelled two ways. A failed result artifact is invalidated by pathname after its descriptor closes, so a renamed written inode keeps reusable JSON. A third, medium defect: a Git probe timeout escapes staging as a traceback instead of a controlled refusal. Fix these without rebuilding settled work or widening helper ownership.

### Target Users
Users preparing local artifacts and standalone or managed sessions submitting results to the same controller.

### Success Metrics
The named scenarios pass. Source-map evidence assigns every affected behavior to its owner. No unsupported capability is advertised. A fresh full completion review certifies the whole retained feature contract with Alice, Blake, Bob, Carl and the explicit Anthropic doubt lens selected by doubt_reviewer: fable. Each review cycle keeps every lens and runs in a fresh session after the build handoff. Blake gets only the permitted PRD inputs, never design, history, coordinator rulings or other reviewers' findings. Record actual model provenance; never substitute auto or downgrade.

The rework cap is two for this v3. Preserve the v1 and v2 exhausted caps. At v3's cap, use the existing bounded recovery and deferral policy and report the blocker. Do not create v4 or reset counters. A focused helper pass does not certify the full gate. The 19 known AP 00018 controller failures stay separate, recorded blockers; never mask, delete, xfail or relabel them.

## Functional Decomposition

### Capability: Helpers
Retain the complete original preparation and classification capability (v2 PRD "Helpers" features) and close the staging probe defect.

#### Feature: Controlled refusal when Git detection cannot answer
- **Description**: A Git metadata probe that times out or cannot start refuses through the existing controlled path.
- **Inputs**: Artifact destination, project root.
- **Outputs**: The existing controlled unsafe-output refusal, before any write.
- **Behavior**: `_is_inside_git_dir` treats `subprocess.TimeoutExpired` and `OSError` (git missing or not executable) as "inside git internals", the same fail-closed answer it gives other detection failures. `stage_review` then returns its existing refusal dict; nothing is staged and no traceback reaches the CLI. Keep `LC_ALL=C`, the 60-second timeout and the "not a git repository" rule. Never override Git configuration.

### Capability: Artifacts
Retain the complete original verification and local-boundary capability (v2 PRD "Artifacts" features) and close the two sink regressions.

#### Feature: Root-anchored symlink refusal
- **Description**: A sink path is judged by its unresolved components below the root, whichever way the root is spelled.
- **Inputs**: Verification artifact and log paths, project root (resolved or through an alias).
- **Outputs**: Controlled `unsafe-artifact-path` refusal before spawn, or the existing success.
- **Behavior**: `_symlinked_component` stops only at the leading root spelling, never at a later component that resolves to the root. A path that leaves the repository and returns through a symlink, including a symlink that points at the root itself, is refused. `_pinned_parent_fd` descends the unresolved names below the root with `O_NOFOLLOW` and never calls `resolve()` on below-root components; when the root is spelled through an alias, strip only the root prefix. A path that is not under the root by either root spelling raises before any descriptor opens. Both spellings refuse with the same slug. A symlinked ancestor of the root stays allowed.

#### Feature: Descriptor-bound invalidation of a failed artifact
- **Description**: A result artifact whose write or close failed can never stay reusable.
- **Inputs**: The artifact sink acquired before spawn.
- **Outputs**: Controlled `sink-write-failed` or `sink-close-failed`; the written inode holds no reusable JSON.
- **Behavior**: Keep a descriptor for the written inode through finalization. On write or close failure, truncate that inode through the kept descriptor, wherever its name now points. Remove a leaf this run created only while the name still points at that inode. A replacement file installed under the original name stays byte-identical. Preserve existing success bytes and the pre-spawn ordering.

#### Feature: Accurate delivery evidence
- **Description**: Docs and receipts match the corrected package.
- **Inputs**: Committed product changes, actual verification results.
- **Outputs**: CHANGELOG, README, receipts, source map and recovery report.
- **Behavior**: Merge the overlapping CHANGELOG `--verify` bullets into one that agrees with README ("keeps an existing log byte-identical when the spawn fails"; remove "leaves no log behind" wording). Make the alias and symlink bullets match the fixed behavior. Add task 5's evidenced served-model provenance to the receipt without inferring unrecorded data. Split `effort` into served and configured values, with `not captured` only where nothing was recorded. Preserve historical receipts.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/scripts/log_sink_refusal.py                     # Artifacts: T1
plugins/autopilot/scripts/verification.py                         # Artifacts: T2
plugins/autopilot/scripts/review_stage.py                         # Helpers: T3
tests/autopilot/test_helper_recovery_v3.py                        # T1-T3 regressions (new)
tests/autopilot/test_helper_rework_sinks.py                       # T1/T2, existing tests may be adjusted only to the fixed contract
tests/autopilot/test_helper_rework_stage.py                       # T3, same rule
tests/autopilot/test_helper_recovery_v2_sinks.py                  # T1/T2, same rule
tests/autopilot/test_helper_recovery_v2.py                        # T1-T3, same rule
plugins/autopilot/README.md                                      # Delivery: T4
plugins/autopilot/CHANGELOG.md                                   # Delivery: task entries/T4
tools/autopilot/source-map.json                                 # Delivery: T4
docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json # Delivery: T4
docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md        # Delivery: T4 (new)
```

These are the complete implementation write paths, with one delivered deviation: the strengthened T2 failed-artifact cases live in `tests/autopilot/test_helper_recovery_v3_artifact.py`, because `tests/autopilot/test_helper_recovery_v3.py` had reached 799 lines, one line under the 800-line ceiling in `rules/coding-style.md`. T2's Verify selector `-k failed_artifact` on the old file no longer matches them; see "Deviations from the PRD" in `docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md` for the replacement command. Tests use temporary fixtures only. An existing test changes only when its assertion encodes the defect being fixed; record each such change in the task outcome. AP12 contracts, v1/v2 design, specs and reviews, source characterization, the source-map generator, provenance tests, controller files and workflow state are read-only. The coordinator alone owns PRD lifecycle and review records.

### Module: Helpers
- **Maps to capability**: Helpers.
- **Responsibility**: Fail closed with a controlled refusal when Git detection cannot answer.
- **Exports**: Existing stage-review behavior; no new facade operation or protocol version.
- **Location**: plugins/autopilot/scripts/review_stage.py; tests/autopilot/test_helper_recovery_v3.py.
New symbols: `tests/autopilot/test_helper_recovery_v3.py`

### Module: Artifacts
- **Maps to capability**: Artifacts.
- **Responsibility**: Race-free sink descent and descriptor-bound invalidation.
- **Exports**: Existing verification and log-sink refusal results.
- **Location**: plugins/autopilot/scripts/log_sink_refusal.py; plugins/autopilot/scripts/verification.py; tests/autopilot/test_helper_recovery_v3.py.

### Module: Delivery
- **Maps to capability**: Artifacts.
- **Responsibility**: Bind delivery evidence to tested package bytes and keep prior history.
- **Exports**: Updated receipt and source map; v3 recovery report and user-facing docs.
- **Location**: plugins/autopilot/README.md; plugins/autopilot/CHANGELOG.md; tools/autopilot/source-map.json; docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json; docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md.
New symbols: `docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md`

## Dependency Graph

### Foundation Layer (Phase 0)
V1 and v2 implementation and history are prerequisites, not rebuild tasks. The v2 cycle-2 review and stubs 00034-00037 supply the disposition.
- **Artifacts**: T1 fixes the descent primitive both sinks share.

### Core Layer (Phase 1)
- **Artifacts**: T2 depends on T1 because both touch the sink fixtures. T3 is independent in code but follows T2 to serialize the shared test file.

### Integration Layer (Phase 2)
- **Delivery**: T4 depends on T1-T3 and refreshes evidence after the product commits.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Refuse leave-and-return and mixed-spelling symlink paths.

**Tasks**:
- [ ] T1: Anchor symlink refusal to the leading root spelling. (depends on: v2 baseline) Writable paths: plugins/autopilot/scripts/log_sink_refusal.py, tests/autopilot/test_helper_recovery_v3.py, tests/autopilot/test_helper_rework_sinks.py, tests/autopilot/test_helper_recovery_v2_sinks.py, plugins/autopilot/CHANGELOG.md. Acceptance: new tests, each failing at the v2 HEAD, cover (a) a path that leaves the repo and returns through a symlink to a below-root directory, (b) a return symlink that points at the root itself, (c) the same paths under an aliased root spelling and under the resolved spelling, (d) a component swapped to a symlink between preflight and open under mixed spelling. Each refuses before spawn with `unsafe-artifact-path` (preflight) or a controlled sink failure (race), writes nothing through the symlink, and leaves sentinels byte-identical. A symlinked root ancestor still succeeds. Run the new file with `-k sink_alias` plus tests/autopilot/test_helper_rework_sinks.py, tests/autopilot/test_helper_recovery_v2_sinks.py, tests/autopilot/test_cycle1_hardening_sinks.py, tests/autopilot/test_local_paths.py.

**Exit Criteria**: T1's tests pass and the named existing sink suites stay green. Record exact commands and outcomes.

### Phase 1: Core
**Goal**: Make failed artifacts unusable by inode and make staging refuse instead of crash.

**Tasks**:
- [ ] T2: Invalidate a failed artifact through a kept descriptor. (depends on: T1) Writable paths: plugins/autopilot/scripts/verification.py, tests/autopilot/test_helper_recovery_v3.py, tests/autopilot/test_helper_rework_sinks.py, tests/autopilot/test_helper_recovery_v2.py, plugins/autopilot/CHANGELOG.md. Acceptance: a new test, failing at the v2 HEAD, renames the artifact during the run, installs a replacement under the original name, and injects a close failure; the renamed inode holds no parseable JSON and the replacement stays byte-identical. Also cover an injected write failure and a created leaf (removed only while the name still points at it). Existing tests/autopilot/test_verification.py, tests/autopilot/test_cycle1_boundaries_verify.py, tests/autopilot/test_facade.py and tests/autopilot/test_helper_recovery_v2.py stay green.
- [ ] T3: Fail closed on Git probe timeout or spawn error. (depends on: T2) Writable paths: plugins/autopilot/scripts/review_stage.py, tests/autopilot/test_helper_recovery_v3.py, tests/autopilot/test_helper_rework_stage.py, plugins/autopilot/CHANGELOG.md. Acceptance: tests with a stubbed `subprocess.run` raising `TimeoutExpired` and `FileNotFoundError` show `stage_review` returns the controlled refusal with no artifact written and no traceback. Run them with tests/autopilot/test_helper_rework_stage.py, tests/autopilot/test_review_helpers.py, tests/autopilot/test_review_helpers_contract.py, tests/autopilot/test_cycle1_boundaries_context.py.

**Exit Criteria**: T2/T3 tests pass, named suites stay green, subprocess probes have explicit timeouts, and no existing assertion is weakened.

### Phase 2: Integration
**Goal**: Bind delivery evidence to the corrected bytes.

**Tasks**:
- [ ] T4: Refresh docs, receipts and helper provenance. (depends on: T1-T3) Writable paths: plugins/autopilot/README.md, plugins/autopilot/CHANGELOG.md, tools/autopilot/source-map.json, docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json, docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md. Acceptance: CHANGELOG `--verify` bullets merged and consistent with README; alias and symlink bullets match fixed behavior; receipt adds task 5's evidenced provenance and splits served from configured effort; historical receipts unchanged. Commit README/CHANGELOG first, record that full 40-hex SHA as the receipt package_revision, then generate receipt and map evidence in a later commit without changing tested package bytes. Run the generator below, its `--check`, tests/autopilot/test_helper_provenance.py and tests/autopilot/test_provenance.py.

Generator command from the repository root (T4 only):

```sh
python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json
python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json --check
```

**Exit Criteria**: Run the full gate once after all tasks: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`, `python3 -m unittest discover -s scripts`, `python3 scripts/validate.py`, and `python3 scripts/generate_marketplace.py --check`. Keep CI definitions unchanged. Record exact failed nodes and owners. The 19 AP 00018 controller failures stay an explicit external deferral; any other failure is a v3 defect. No push until the controller tests and all required checks pass. Hand off before a fresh full-lens completion review; no review runs from the work session.

## Test Strategy

### Critical Scenarios
All v1 and v2 acceptance obligations stay in force and must be certified (v2 PRD "Critical Scenarios"), though only corrective work gets tasks:
- **Leave-and-return symlink**: refused under resolved and aliased root spellings, including a return link to the root itself; no byte written through any symlink.
- **Mixed-spelling race**: a component swapped to a symlink after preflight never redirects the open.
- **Renamed failed artifact**: rename plus close or write failure leaves no reusable JSON on the written inode; the replacement survives.
- **Probe failure**: timeout or missing git gives the controlled staging refusal with nothing written.
- **Regression guard**: every existing helper suite stays green; the 19 AP 00018 nodes remain the only full-gate failures.

All pytest invocations use `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest` with the named file, node or filter and -q. Run narrow tests during tasks; reserve the full suite for final integration. Use `os.path.realpath` where a symlink loop could reach `Path.resolve()`.

## Risks

- **Cap history loss**: Preserve v1 and v2 history. v3 is the last authorized corrective version.
- **Primitive regression**: The descent is shared by both sinks. Keep the existing alias matrix tests green and add the return-to-root cases.
- **Controller ownership leak**: Keep provenance, manifests, custody, task persistence and lifecycle with their controller owners.
- **False green**: AP 00018's controller failures block the full gate and any push; never claim helper-only checks satisfy them.
- **Stale evidence**: Recheck each finding against current source at task start. Never rewrite historical red results.

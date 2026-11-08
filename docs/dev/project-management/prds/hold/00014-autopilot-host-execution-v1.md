---
default_model: opus
model_tier_rationale: Provider process behavior, hook boundaries and isolation require judgment.
lane: full
eligibility: ls docs/dev/project-management/prds/done/00012-* docs/dev/project-management/prds/done/00013-* # link-ok: lifecycle output
critical_on_master: 635e37640b82c66f8ed7e5063605ce4481f81407..273be89f1d993447b49a1d1b895b71e28259a0e6
ledger: deferred/202610250001-deferred.json#cf5f8a63cae1
---
# Autopilot host execution and enforcement

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Implementation specification only; no publication, live installation, migration or source retirement.

## Overview

### Problem Statement

> **Custody (cap_critical, batch 202610250001):** cycle 2 of 2 (cap) left R1 unresolved CRITICAL: tests/autopilot/test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes still fails (assert_refreshed_evidence compares CHANGELOG.md at pinned package_revision 444d733a against current bytes; AP00014 edited it after that revision) [3/4 consensus, review-2.md R1]; four HIGH rows also open: R3 claude-free profile unimplemented, R4 compatibility assets are capability lists not client assets, R5 phase-2 probes static only, R6 codex declares isolation with no implementation, R7 build-compatibility imports a module named by contract input Commits 635e37640b82c66f8ed7e5063605ce4481f81407..273be89f1d993447b49a1d1b895b71e28259a0e6 (53) are live on master. Resolve with autopilot custody resolve.

Client hooks and native session bindings stay in the plugin. Workflow authority belongs to its controller; OVCAQ owns cross-session/cross-driver process launch.

### Target Users
Supported-client users in manual or supervised controller-bound sessions.

### Success Metrics
The named behavior scenarios pass, and source-map evidence assigns every affected behavior to its correct owner. No unsupported capability is advertised.

## Functional Decomposition

### Capability: Host execution

#### Feature: Phase-local jobs
- **Description**: Phase-local jobs within the declared ownership boundary.
- **Inputs**: Declared host capability, native session identity, role/tier/effort and explicit job inputs.
- **Outputs**: Isolated worker/reviewer results with raw artifacts and completed cleanup.
- **Behavior**: Implement native session identity and explicitly permitted in-session delegation. In managed mode cross-session/cross-driver jobs become controller job intents consumed by OVCAQ; never spawn headless provider CLI children inside plugin scripts. In standalone mode emit next-session instructions for manual launch. Preserve bounded recursion and permissions. Characterize Sonnet effort and require the intended effort in job metadata; actual CLI forwarding is OV 00059. Native child cancellation stays host-scoped. Keep role IDs independent of provider/model names; record actual native sessions and resolved input digests for controller evidence. No coordinator relaunch, scheduler or TUI.

Required Claude-free profile: Codex implements; Gemini provides independent doubt review, with every policy-required role in isolated Codex or Gemini contexts. Implement applicable native identity/input/guard support for those roles; Claude cannot be a fallback. AP 00017 owns real certification, OV 00059 owns managed Gemini process launch. A missing mandatory host capability remains an explicit blocker to this profile's certification.

### Capability: Enforcement

#### Feature: Client-native guards
- **Description**: Client-native guards within the declared ownership boundary.
- **Inputs**: Nine source hook duties, applicable local context and read-only controller-bound results.
- **Outputs**: Supported compatibility bundles and explicit capability/refusal evidence.
- **Behavior**: Retain Claude hooks through supported packaging and prove each additional client's registration/identity/interception. Stateful guards call the same controller seam in both modes; pure helpers remain artifact-only. Preserve document-location, custody-push, delegation, post-handoff, departure, context/reinjection, state-integrity, review-completeness and live-job duties. Missing enforcement refuses affected operations; MCP/portable packaging is not universal interception. Shared procedures/helpers cannot require Claude-only variables, home/cache paths or APIs; isolate those references in declared adapters or informational provenance. Probes classify every required resource edge and fail if packaged resources escape.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/scripts/hosts.py  # Adapters
plugins/autopilot/scripts/claude.py  # Adapters
plugins/autopilot/scripts/codex.py  # Adapters
plugins/autopilot/scripts/gemini.py  # Adapters
plugins/autopilot/scripts/jobs.py  # Adapters
plugins/autopilot/scripts/autopilot.py  # Adapters
plugins/autopilot/contracts/hosts.json  # Adapters
tests/autopilot/test_jobs.py  # Adapters
tests/autopilot/test_host_argv.py  # Adapters
tests/autopilot/test_sessions.py  # Adapters
plugins/autopilot/scripts/guards.py  # Compatibility
plugins/autopilot/scripts/doctor.py  # Compatibility
plugins/autopilot/compatibility/claude.json  # Compatibility
plugins/autopilot/compatibility/codex.json  # Compatibility
plugins/autopilot/CHANGELOG.md  # Compatibility
tools/autopilot/build-compatibility.py  # Compatibility
tools/autopilot/probe-host.py  # Compatibility
docs/dev/tmp/autopilot/  # Compatibility
tests/autopilot/test_guards.py  # Compatibility
tests/autopilot/test_compatibility.py  # Compatibility
```

### Module: Adapters
- **Maps to capability**: Host execution
- **Responsibility**: Own native identity/delegation and job-intent preparation; expose a controller-binding seam tested with fakes until 00016. Provider-named modules adapt native host capabilities, not headless process launch.
- **Exports**: Host probes, native-child delegation and cross-session job request payloads.
New symbols: `plugins/autopilot/scripts/hosts.py`, `plugins/autopilot/scripts/claude.py`, `plugins/autopilot/scripts/codex.py`, `plugins/autopilot/scripts/gemini.py`, `plugins/autopilot/scripts/jobs.py`, `plugins/autopilot/contracts/hosts.json`, `tests/autopilot/test_jobs.py`, `tests/autopilot/test_host_argv.py`, `tests/autopilot/test_sessions.py`

### Module: Compatibility
- **Maps to capability**: Enforcement
- **Responsibility**: Generate self-contained supported client assets and verify pre-action decisions.
- **Exports**: Compatibility builds, doctor diagnostics and capability evidence.
New symbols: `plugins/autopilot/scripts/guards.py`, `plugins/autopilot/scripts/doctor.py`, `plugins/autopilot/compatibility/claude.json`, `plugins/autopilot/compatibility/codex.json`, `tools/autopilot/build-compatibility.py`, `tools/autopilot/probe-host.py`, `tests/autopilot/test_guards.py`, `tests/autopilot/test_compatibility.py`

## Dependency Graph

### Foundation Layer (Phase 0)
Plugin 00012/00013 completed. Recheck pinned hook/runner behavior and target ownership; skip/report conflicts. AGENTS.md:39 requires package containment. Host probes isolate project/plugin locations under docs/dev/tmp/autopilot, preserve existing host authentication/configuration and never install into live user configuration. Missing binary/auth/capability records unavailable; only successful real probes enable host execution claims.
- **Characterization/contracts**: Establish the inputs consumed by Adapters and Compatibility.

### Core Layer (Phase 1)
- **Adapters**: Depends on the Phase 0 inputs.
- **Compatibility**: Depends on Phase 0 and the explicitly ordered task prerequisites below.

### Integration Layer (Phase 2)
- **Public-boundary tests and documentation**: Depend on Adapters and Compatibility.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Verify source premises and establish exact contracts.

**Tasks**:
- [ ] Characterize source hook decisions and runner argv/effort; define local versus controller-bound guard applicability. (depends on: declared prerequisites) — Acceptance: hook_behavior_equivalence and effort_forwarding preserve source invariants while exposing the known effort mismatch as a corrected target case.

**Exit Criteria**: The named task tests pass. Recheck changed-content premises; if false, skip/report affected edits without forcing them.

### Phase 1: Core
**Goal**: Implement behavior under the correct owner.

**Tasks**:
- [ ] Implement native identity/delegation plus structured cross-session job requests; refuse nested provider CLI spawning. (depends on: Phase 0) — Acceptance: recursive_child_denied, no_nested_driver_cli and reviewer_isolation verify native host seams and request payloads in temporary roots.
- [ ] Implement pre-action guards and generated client compatibility assets, using fake read-only controller responses at the seam. (depends on: Phase 1 task 1) — Acceptance: custody_push_denied and missing_controller_seam_refused prohibit unsafe bound operations without adding a helper-owned writer.

**Exit Criteria**: The named task tests pass. Recheck changed-content premises; if false, skip/report affected edits without forcing them.

### Phase 2: Integration
**Goal**: Prove public behavior and document capability evidence.

**Tasks**:
- [ ] Add headless probes in isolated plugin/project locations and record unavailable hosts honestly. (depends on: Phase 1) — Acceptance: relocated_host_probe, shared_core_without_claude, codex_gemini_role_capabilities and missing_guard_refused verify real invocation/resources/identity/interception for the selected roles and report denied mandatory capabilities; no availability result is converted into a success claim.
- [ ] Update the source map and changelog for supported and still-unavailable client duties. (depends on: Phase 2 task 1) — Acceptance: no_coordinator_runtime_in_plugin rejects supervisor/queue implementations in the distributed package.

**Exit Criteria**: The named integration scenarios and `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record real-host unavailability explicitly; it does not certify execution. No publishing or cutover occurs.

## Test Strategy

### Critical Scenarios
- **Happy path**: relocated_host_probe → A supported installed host proves native identity/isolation and packaged job resources; cross-session launches stay external.
- **Edge case**: child_cleanup → Native-child cancellation preserves evidence without controlling OVCAQ processes.
- **Error case**: missing_guard_refused → An unavailable mandatory guard prevents the affected execution profile.

## Risks

- A host loading a skill does not prove hook or session semantics.
- Do not copy headless provider runner scripts as hidden supervisors; managed execution belongs to OVCAQ.

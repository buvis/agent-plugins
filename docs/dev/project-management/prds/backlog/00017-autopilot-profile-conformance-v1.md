---
default_model: opus
model_tier_rationale: Session identity, fresh-review boundaries and installed artifact equivalence require judgment.
lane: full
eligibility: ls docs/dev/project-management/prds/done/00016-* # link-ok: lifecycle output
---
# Autopilot standalone and managed conformance

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
Distribution must certify the bundled controller's independent use and distinguish it from optional orchestration and host-specific enforcement.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
standalone_independent → one controller works with upper layers unavailable. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Conformance

#### Feature: Capability-based profiles
- **Description**: Prove standalone stateful behavior and optional managed parity.
- **Inputs**: Relocated package, source map, AP 00016 diagnostics and optional installed OVCAQ.
- **Outputs**: Artifact-only, standalone-stateful, managed and advanced evidence.
- **Behavior**: Standalone requires same controller core/jobs/reviews/records and supported host identity/guards, never OVCAQ. Exercise init/entry/task/review/rework/complete/records with OVCAQ and Lantern removed from PATH/imports. Managed checks use an OVCAQ 00060 artifact passed explicitly as `tools/autopilot/conformance.py --ovcaq-argv JSON` (an argv array); without that flag managed is unavailable; waves require 00061. Missing managed inputs report unavailable without blocking standalone. Fake hosts certify protocol behavior only. Export separate implementation and real-host certification statuses; unavailable capabilities cannot produce a passed completion receipt. Profile checks use AP 00012's frozen behavior/regression inventory and evidence map; every obligation required by that profile needs current passing evidence.

User-selected certification profile (2026-10-25): Codex builds; Gemini supplies the independent provider's doubt voice, including Eve when required. Every resolved role uses an isolated Codex or Gemini context under AP 00012's unchanged roster/rubric rules, including Carl's availability predicate. No Claude fallback or Codex-only completion certificate. Run real standalone build/fresh-review/rework/complete/records; managed adds next-PRD continuation and final drain. Isolate Claude executables/configuration/credentials, source checkout and author-home runtime resources; expose only required Codex/Gemini authentication. Standalone handoffs remain manual; any automated test harness stays maintainer-only. Receipts bind exact package/controller/driver versions/digests, policy, actual provider/model/session, allowed inputs and code identity. Missing auth or capability reports unavailable and prevents port completion/cutover, without blocking unrelated implementation.

### Capability: Distribution

#### Feature: Self-contained candidates
- **Description**: Package controller and plugin assets without upper layers.
- **Inputs**: Canonical manifest, preserved references and supported compatibility outputs.
- **Outputs**: Unpublished package candidates and accurate capability documentation.
- **Behavior**: Ship controller/runtime resources and LICENSE inside plugin root, no OVCAQ supervisor/drivers/TUI. Validate the complete packaged dependency closure, distinguishing explicit external capabilities and informational citations; existing source/home files cannot make an archive pass. Python 3.12 execution floor is explicit. Test arbitrary cwd/relocation and isolated real host loading where available. Do not install into user configuration, publish or retire source. Release candidates are written under `docs/dev/tmp/autopilot/dist/`.

## Structural Decomposition

### Repository Structure

```text
tools/autopilot/conformance.py
tests/autopilot/test_profiles.py
tests/autopilot/test_installed_standalone.py
tests/autopilot/test_installed_managed.py
tools/autopilot/package.py
tools/autopilot/source-inventory.json
tools/autopilot/source-map.json
tests/autopilot/test_distribution.py
plugins/autopilot/README.md
plugins/autopilot/CHANGELOG.md
README.md
AGENTS.md
.github/workflows/validate.yml
docs/dev/tmp/autopilot/
```

### Module: Conformance
- **Maps to capability**: Conformance
- **Responsibility**: Prove standalone stateful behavior and optional managed parity.
- **Exports**: Artifact-only, standalone-stateful, managed and advanced evidence.
New symbols: `tools/autopilot/conformance.py`, `tests/autopilot/test_profiles.py`, `tests/autopilot/test_installed_standalone.py`, `tests/autopilot/test_installed_managed.py`

### Module: Distribution
- **Maps to capability**: Distribution
- **Responsibility**: Package controller and plugin assets without upper layers.
- **Exports**: Unpublished package candidates and accurate capability documentation.
New symbols: `tools/autopilot/package.py`, `tests/autopilot/test_distribution.py`

## Dependency Graph

### Foundation Layer (Phase 0)
AP 00016 completed. OVCAQ and Lantern are not prerequisites. Recheck existing package/CI premises; preserve the validator's Python 3.10 job. Containment: AGENTS.md:39. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Conformance**: Depends on Phase 0 and the explicit task order below.
- **Distribution**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Conformance and Distribution.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Define profile evidence and source row acceptance ownership. (depends on: declared prerequisites) — Acceptance: profile_truth and source_inventory_mapping compare the frozen expected ID set, delivery owners, regression dispositions and profile-required evidence; reject claims based only on headings/metadata or unavailable host probes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Add installed standalone scenarios and conditional managed cross-driver cases. (depends on: Phase 0) — Acceptance: standalone_independent, codex_gemini_standalone, codex_gemini_managed and managed_unavailable_is_explicit distinguish real certification from protocol tests and absence; Claude fallback, missing Gemini or substituted provider identity cannot pass.
- [ ] Validate candidate contents, source reference preservation and Python floor. (depends on: Phase 1 task 1) — Acceptance: distribution_has_one_controller, resource_closure and distribution_no_supervisor reject sibling imports, escaped runtime references, bundled UI or nested driver launchers. Run the target-only checks with source and author-home paths inaccessible.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Generate unpublished candidates, wire offline CI and the separate opt-in real-host certification command, and update package documentation, the root `README.md` plugin table and the `AGENTS.md` boundaries (`plugins/autopilot/`, `tools/autopilot/`, `tests/autopilot/`, `docs/dev/tmp/autopilot/`). (depends on: Phase 1) — Acceptance: documentation_matches_evidence and archived_relocation verify shipped resources and unsupported-profile refusal; persist real Codex + Gemini receipts when supported, otherwise record certification incomplete without making ordinary CI require credentials.

**Exit Criteria**: Named integration scenarios, `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass.

## Test Strategy

### Critical Scenarios
- **Happy path**: standalone_independent → one controller works with upper layers unavailable.
- **Edge case**: managed_unavailable_is_explicit → standalone delivery does not wait for OVCAQ.
- **Error case**: distribution_no_supervisor → plugin cannot secretly carry the old loop/TUI.
- **Certification gate**: codex_gemini_standalone and codex_gemini_managed → actual isolated hosts complete the selected lifecycle; fake, stale, unavailable or Claude-dependent evidence cannot mark the port complete.

## Risks

- Source retirement requires managed/wave/TUI parity beyond standalone delivery.
- Actual host conformance remains unavailable until real isolated probes succeed.

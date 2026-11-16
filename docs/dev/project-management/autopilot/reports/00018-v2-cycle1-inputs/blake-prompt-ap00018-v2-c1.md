HOST TOOL POLICY (overrides launcher-specific shell examples below):
Use only your read, glob and grep tools. NEVER use a shell, including git, rg,
tests, linters, package managers, or process commands. Do not modify files.
The coordinator supplies the gate results. Use bounded reads and grep for
large generated files. A denied read invalidates review: report it explicitly.
Do not read ignored paths, workflow state, prior reviews or sibling outputs.
Repository root: /Users/bob/git/src/github.com/buvis/agent-plugins

You are Blake, a hostile auditor reviewing code you've never seen before.
You know ONLY what was supposed to be built. You must find the code,
read it, and determine if it does what the spec says.

Never call bash `head`, `tail`, `cat`, `grep`, or `find` - a hook blocks them. Use the Read tool (offset/limit), `rg`, or `rg --files` instead. Never pipe between heterogeneous commands and never combine an inspection (read, list, search, diff) with a test, lint or build invocation in one Bash call - run them as separate calls. Pass an explicit `timeout` on every Bash call: 60000 ms for an inspection, 300000 ms for a lint run or a narrow test run, 600000 ms for a full suite or a full build.

When your run inputs carry a `## Test gate` block, it is this cycle's full-suite result at HEAD: do not rerun the full suite; a narrow run of one test file to check a spec claim is fine.

## The Specification

---
default_model: opus
model_tier_rationale: Extraction equivalence, public contracts and concurrent workflow authority require judgment.
lane: full
rework_cap: 3
plan_expansion: allow
eligibility: ls docs/dev/project-management/prds/done/00012-* # link-ok: lifecycle output
---
# Autopilot canonical controller kernel and protocol

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Recovery revision authorized 2026-11-09 by the request to finish portable Autopilot. Supersedes the held v1 for delivery, preserving v1 and its attempt evidence. No publication, live installation, source retirement or custody acceptance.

## Overview

### Problem Statement
Standalone and supervised workflows need the same enforceable writer. The current tested writer lives inside OVCAQ; adding a second legacy backend would split authority.

The v1 attempt stopped during task 7 after prompt-size/replan exhaustion; tasks 1–6 and task-7 tests already landed. Reuse those implementations and evidence after characterization, not by marking new tasks complete from old checkboxes. Close the existing owner, recovery and capacity failures, then complete export and relocation. Preserve the old batch state and counters. Plan bounded tasks with the installed planner's normal budget; do not reuse the failed 40K budget, increase prompt caps or omit test/review roles.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
controller_without_upper_layers → one installed writer runs without either upper layer. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Kernel

#### Feature: Extract the existing writer
- **Description**: Reuse tested transactional behavior without supervisor dependencies.
- **Inputs**: Pinned OVCAQ state services and characterized source invariants.
- **Outputs**: One packaged Python 3.12 controller and workflow store.
- **Behavior**: Premise: OVCAQ state/store.py and schema.py implement atomic writes, locking and revisions. Extract the workflow kernel with attribution and equivalent corruption/lock/recovery behavior; separate process fields from workflow schema. Recheck current source before moving behavior. Never mutate live source state; no OVCAQ import, process launcher or TUI dependency.

### Capability: Protocol

#### Feature: Typed commands and actor fencing
- **Description**: Publish the canonical controller boundary.
- **Inputs**: Contract A in the design, scoped actor credentials and temporary project roots.
- **Outputs**: Contract/snapshot/apply CLI, immutable export bundle and request receipts.
- **Behavior**: Implement protocol-major 1 and exact envelope/errors from Contract A. Define JSON schemas for every core operation, including explicit fresh-open bootstrap (expected revision zero, workflow ID assigned once). Fresh workflow.open alone permits null workflow/actor/epoch and revision zero on an absent store. Bootstrap creates an operator credential under the private state root (directory 0700, file 0600) and returns only its path. Other apply calls require --actor-file PATH matched to actor ID/scope; credentials never appear in command values or logs. Opening an existing workflow is not an ownership bypass. One execution lease, epoch-fenced job/operator credentials, CAS, identical-payload replay, conflicting-ID refusal and path containment. Bound output/time in clients; no credential values in logs. Publish only implemented kernel operations; later families remain declared but unavailable. CLI: `--json contract`, `--json snapshot --project-root PATH`, `--json apply --project-root PATH --request FILE`, `--actor-file PATH`. Contract output: protocol_major=1, package_version, schema_digest, fixture_digest, operations, capabilities; capability IDs workflow.core.v1, workflow.jobs.v1, workflow.reviews.v1, workflow.records.v1 and optional workflow.waves.v1. Envelope fields: protocol_major, operation, request_id, expected_revision, project_id, workflow_id, actor_id, job_id (nullable for operator actions), lease_epoch, payload. Response fields: ok, revision, result, error_code, retryable. Error codes, exactly: invalid_request, incompatible_contract, revision_conflict, wrong_binding, missing_capability, rejected_evidence, recovery_required. Closed operations: workflow.open, policy.bind, owner.acquire/release/recover, prd.enter, task.replace/start/finish/attempt, lane.route, job.plan/claim/record_exit, review.record_stage/close, custody.record/discharge, verification.record, phase.handoff, prd.stall/park/defer/complete, artifact.record, records.commit, plus the optional wave operations.

Contract A bundle for OVCAQ: commit `plugins/autopilot/contracts/controller-v1.json` as a regular file (no symlink in its path, under 16 MiB). It is a strict JSON object (no duplicate keys, no NaN/Infinity) with exactly these keys: protocol_major (int 1), package_version (nonempty str, the plugin manifest version), schema_digest (nonempty str), fixture_digest (nonempty str), operations (list of str), capabilities (list of str). `python3 controller/main.py --json contract` returns the same protocol_major, schema_digest and fixture_digest, a package_version equal to the bundle's or the bundle's plus `+<build>`, and operations/capabilities that are supersets of the bundle's lists. Document the `sha256sum plugins/autopilot/contracts/controller-v1.json` output (sha256 of the raw file bytes) in `plugins/autopilot/README.md`; OVCAQ pins path and digest as `[workflow] contract_bundle` and `contract_bundle_sha256`. The installed controller argv, stated once here and set by OVCAQ as `[workflow] controller_argv`, is `["python3", "<installed-plugin-root>/controller/main.py"]`.

## Structural Decomposition

### Repository Structure

```text
plugins/autopilot/controller/main.py
plugins/autopilot/controller/autopilot_state/__init__.py
plugins/autopilot/controller/autopilot_state/schema.py
plugins/autopilot/controller/autopilot_state/store.py
plugins/autopilot/controller/autopilot_state/paths.py
tests/autopilot/test_controller_kernel.py
plugins/autopilot/controller/autopilot_state/protocol.py
plugins/autopilot/controller/autopilot_state/actors.py
plugins/autopilot/contracts/controller/workflow-v1.json
plugins/autopilot/contracts/controller/fixtures-v1.json
plugins/autopilot/contracts/controller/provenance.json
plugins/autopilot/contracts/controller-v1.json
tools/autopilot/export-controller-contract.py
tests/autopilot/test_controller_protocol.py
tests/autopilot/test_controller_actors.py
plugins/autopilot/README.md
plugins/autopilot/CHANGELOG.md
tests/autopilot/test_controller_capacity.py
tests/autopilot/test_controller_owner.py
tests/autopilot/test_controller_owner_recovery.py
tests/autopilot/test_controller_bootstrap.py
tests/autopilot/test_controller_bootstrap_recovery.py
tests/autopilot/test_helper_provenance_real.py
tests/autopilot/test_package.py
tools/autopilot/source-map.json
tools/autopilot/update_helper_map.py
```

### Module: Kernel
- **Maps to capability**: Kernel
- **Responsibility**: Reuse tested transactional behavior without supervisor dependencies.
- **Exports**: One packaged Python 3.12 controller and workflow store.
New symbols: `plugins/autopilot/controller/main.py`, `plugins/autopilot/controller/autopilot_state/__init__.py`, `plugins/autopilot/controller/autopilot_state/schema.py`, `plugins/autopilot/controller/autopilot_state/store.py`, `plugins/autopilot/controller/autopilot_state/paths.py`, `tests/autopilot/test_controller_kernel.py`

### Module: Protocol
- **Maps to capability**: Protocol
- **Responsibility**: Publish the canonical controller boundary.
- **Exports**: Contract/snapshot/apply CLI, immutable export bundle and request receipts.
New symbols: `contract_bundle_sha256`

This consumer configuration key is defined by Contract A, not an additional runtime dependency.
New symbols: `plugins/autopilot/controller/autopilot_state/protocol.py`, `plugins/autopilot/controller/autopilot_state/actors.py`, `plugins/autopilot/contracts/controller/workflow-v1.json`, `plugins/autopilot/contracts/controller/fixtures-v1.json`, `plugins/autopilot/contracts/controller/provenance.json`, `plugins/autopilot/contracts/controller-v1.json`, `tools/autopilot/export-controller-contract.py`, `tests/autopilot/test_controller_protocol.py`, `tests/autopilot/test_controller_actors.py`

## Dependency Graph

### Foundation Layer (Phase 0)
AP 00012 completed. No OVCAQ runtime prerequisite. Characterize OVCAQ source pin cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7 in /Users/bob/git/src/github.com/buvis/ovcaq, read with `git show` at that pin, not checkout HEAD; record source-to-target maps, including tests. Package containment is required by AGENTS.md:39. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Kernel**: Depends on Phase 0 and the explicit task order below.
- **Protocol**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Kernel and Protocol.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Map state fields by workflow versus process ownership and freeze kernel/protocol fixtures. (depends on: declared prerequisites) — Acceptance: kernel_field_ownership and contract_examples reject unowned fields; recheck source pin and preserve existing fixes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Extract atomic store, schema and root resolver without copying supervisor ownership. (depends on: Phase 0) — Acceptance: kernel_equivalence, concurrent_cas and corrupt_state_recovery preserve source outcomes under real subprocess contention.
- [ ] Implement CLI dispatch, scoped actors, execution lease and idempotent receipts. (depends on: Phase 1 task 1) — Acceptance: lease_exclusion, wrong_actor, epoch_revoked, lost_ack_replay and fresh_open_replay reject bypasses without partial writes.
- [ ] Close the interrupted owner/capacity implementation against existing regressions. (depends on: Phase 1 task 2) — Acceptance: tests/autopilot/test_controller_capacity.py, tests/autopilot/test_controller_owner.py, tests/autopilot/test_controller_owner_recovery.py, tests/autopilot/test_controller_bootstrap.py and tests/autopilot/test_controller_bootstrap_recovery.py pass without skips, weaker assertions or fixtures that bypass the public protocol.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Export canonical schemas/fixtures/provenance and prove installed relocation. (depends on: Phase 1) — Acceptance: controller_bundle_reproducible and controller_without_upper_layers run with OVCAQ/Tower/source checkout inaccessible. contract_bundle_pinnable asserts `plugins/autopilot/contracts/controller-v1.json` is a regular file under 16 MiB with no symlink in its path, parses as a strict JSON object with exactly the keys protocol_major, package_version, schema_digest, fixture_digest, operations, capabilities and the stated types, that `--json contract` matches it as the Protocol feature states, and that the README digest equals the sha256 of its raw bytes.
- [ ] Document Python floor and supported kernel capabilities. (depends on: Phase 2 task 1) — Acceptance: unsupported_operation_refused verifies later operation families are unavailable until implemented.
- [ ] Refresh delivery evidence for final package bytes, including shared files changed since AP00013, without changing historical receipts. (depends on: Phase 2 task 2) — Acceptance: tests/autopilot/test_helper_provenance_real.py and tests/autopilot/test_package.py pass against truthful current revision/digest evidence; no broad path exemption, test exclusion or fabricated successful gate is introduced. If the existing provenance format cannot represent subsequent ownership, add an explicit tested successor receipt rather than rewriting the earlier receipt's claim.

**Exit Criteria**: Named integration scenarios, `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass. Record missing real-host capabilities as unavailable.

## Test Strategy

### Critical Scenarios
- **Happy path**: controller_without_upper_layers → one installed writer runs without either upper layer.
- **Edge case**: lost_ack_replay → original receipt survives revision changes.
- **Error case**: lease_exclusion → manual and supervised schedulers cannot both own the workflow.

## Risks

- Do not copy OVCAQ process/run fields into authoritative workflow truth.
- A local credential fence prevents accidental wrong-role calls; it is not a sandbox against unrestricted filesystem access.
- The supported installed workflow builds this package; unavailable package skill entry points stay gated until their own implementation and certification pass. Never modify or run a loop in the frozen claude-autopilot repository.
- Completion requires a fresh-session full review of the whole v2 contract, including reused behavior. Historical AP00018 failures are no longer an acceptable baseline exemption.

## The Rubric (binary pass/fail rules, spec-only)

# Review-Blindly Rubric

This rubric provides binary pass/fail criteria for the spec-only hostile audit performed by the review-blindly skill. The reviewer's prompt contains ONLY the PRD — no diff, no file list, no implementation summary, no implementer self-review. The reviewer must independently locate and read the relevant code to evaluate each rule against the spec.

Rule ids use the `B` prefix (PRD 00108). The three review rubrics once shared a
single id namespace, which made a bare rule id ambiguous across consensus, blind
and doubt — a latent misroute now that rubric ids live inside agent files. The
consensus set keeps the `R` prefix, doubt took `D`, blind took `B`. Ids are
stable within a set: the prefix changed, no rule was renumbered.

## Rules

### Spec Compliance

B1: The implementation satisfies all specified behaviors and outputs described in the PRD.

B2: All stated data formats and structures in the PRD are preserved in the implementation.

B3: Every API endpoint or interface specified in the PRD is implemented with the correct signature and behavior.

B4: All stated performance requirements and constraints from the PRD are met.

B5: The implementation matches all specified error handling behaviors and status codes.

### Scope Creep

B6: No new functionality or features beyond those explicitly specified in the PRD are present.

B7: No additional parameters, options, or flags are added beyond those in the PRD.

B8: No new external dependencies or libraries are introduced beyond those specified.

### Security

B9: All specified authentication mechanisms from the PRD are implemented and enforced.

B10: Required input validation and sanitization are present as specified in the PRD.

B11: Any specified rate-limiting or throttling controls are implemented as described.

### Data Safety

B12: No destructive operations (delete, update, etc.) are performed without proper safeguards.

B13: All data migrations include rollback or reversal mechanisms as specified.

B14: No unguarded database queries or file operations are present in the implementation.

### Acceptance Criteria

B15: All acceptance criteria for Phase 1 tasks are satisfied in the implementation.

B16: All acceptance criteria for Phase 2 tasks are satisfied in the implementation.

B17: All acceptance criteria for Phase 3 tasks are satisfied in the implementation.

### Out-of-Scope

B18: All items explicitly marked as out-of-scope in the PRD are absent from the implementation.

B19: No features or functionality mentioned in the PRD as out-of-scope are present in the codebase the reviewer inspected.

## Your Job

Read the actual codebase and verify against the spec above.
You have NO implementation context. Find the code yourself.

**Check for:**

1. **Spec compliance** — Every requirement implemented? Anything
   extra? Requirements misinterpreted?

2. **Security and deployment readiness** — Secrets with empty
   defaults? Missing auth checks? Fail-open paths? Race conditions
   (check-then-act)?

3. **Data safety** — Backward compatibility? Migration paths?
   Malformed/missing data handling?

4. **Missing error paths** — Token expiry, network failure, partial
   writes? Retry and recovery?

**IMPORTANT: If you cannot find implementation files, you MUST still
produce a full report.** Enumerate every spec requirement, flag every
security concern derivable from the spec. "Code not found" is a
Critical finding, not a reason to stop.

OUTPUT FORMAT IS MANDATORY. Follow exactly:
## Agent Output Format (Single Source of Truth)

Each agent outputs issues in this exact format:

```
[{AGENT_NAME}] {emoji} {description} | File: {path or "N/A"} | Task: {id or "general"}
```

**Severity emojis:** 🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Low

**Rules:**
- One issue per line
- Use "N/A" for file if issue is architectural/cross-cutting
- Use "general" for task if issue spans multiple tasks or is a PRD gap
- If zero issues found: `[{AGENT_NAME}] ✅ No issues found`

**Examples:**
```
[ALICE] 🔴 SQL injection in query builder | File: src/db/query.ts | Task: 3
[BOB] 🟠 Missing error handling strategy | File: N/A | Task: general
[CARL] 🟡 PRD section 2.3 not implemented | File: N/A | Task: 5
```

Your agent name is BLAKE.

Cite files repo-relative as path:line (for example skills/work/SKILL.md:166), never absolute and never with a "(lines a-b)" suffix.

PER-RULE VERDICTS ARE MANDATORY. For every rule in The Rubric above, emit one line:
B{n}: pass   or   B{n}: fail
(one rule per line, no other text on the line, no rationale; a rule you
cannot evaluate counts as fail; never omit the line; never renumber).

## Test gate

Tests: counts unavailable (suite run this cycle, exit 0, no PASS/FAIL/SKIP/EXIT summary line)

## Additional gate evidence

Repository validator: 3 packages and 15 skills passed. Validator unittest: 59 passed.
Marketplace --check, bundle exporter --check, helper map --map tools/autopilot/source-map.json --check: exit 0.
Current HEAD full suite completed with exit 0: 1554 passed in 657.15s (0:10:57)
The earlier counts-unavailable line reflects the installed summary parser, not a test failure. The coordinator is running the source-required counted verification pass; do not rerun the suite.

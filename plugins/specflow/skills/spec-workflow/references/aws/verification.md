# AWS guidance: verification

Adaptation: Read this file when a task or a spec is verified. Each passage under a source line is AWS AI-DLC text, copied verbatim with cuts shown as `[...]`; each `Adaptation:` line is specflow's own. Where the two differ, the specflow artifact contract wins. Read only the passages marked with the active profile or `[both]`.

## How many tests

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 8. Depth Guidance > Test Strategy @ v2.11.0 (6a378b5) [quick]

**Minimal — Nyquist model** (inspired by GSD's Nyquist validation layer):

Just as the Nyquist rate is the minimum sampling frequency to reconstruct a signal, Minimal test strategy generates the minimum tests needed to verify every requirement — no more, no less.
- 1 verifiable test per identified requirement (requirement-driven, not component-driven)
- Happy-path floor: every component gets at least 1 happy-path unit test regardless of requirement mapping
- Unit tests by default. A `bugfix` / `security-patch` targeted regression may
  use integration or E2E when that is the narrowest level that reproduces the
  defect; this additive scope floor does not expand unrelated test volume.
- ~5-15 tests total for a typical project
- Soft guideline — LLM can exceed when safety-critical context demands it (e.g., security-critical bugfix)

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 8. Depth Guidance > Test Strategy @ v2.11.0 (6a378b5) [standard]

**Standard — per-component model:**
- 5-8 tests per component
- Unit tests + integration tests (key boundaries)
- E2E, performance, security tests skipped unless NFR requirements exist
- Test pyramid proportions apply within the generated set (75% unit / 20% integration / 5% E2E)
- Soft guideline

Adaptation: A test is named for the rule it enforces and must be able to fail when that rule breaks. Counts are a guide; never add a test only to reach one.

## Every target gets a verdict

> Source: A1 `core/aidlc-common/stages/construction/build-and-test.md` > Steps > Step 1: Analyze Testing Requirements @ v2.11.0 (6a378b5) [standard]

Build a source-complete inventory of every measurable quality target before
generating instructions. [...]

For each target, record a stable target ID (derive one from the source path and
section when the source has none), source path/section, expected value, the
check or instruction file that will produce its actual value, and the later
validation stage that owns it when Build and Test cannot execute it locally.

Adaptation: The targets are the measurable acceptance criteria of `requirements.md` and the targets `design.md` sets. Each one names, in `tasks.md`, the task and the check that proves it.

> Source: A1 `core/aidlc-common/stages/construction/build-and-test.md` > Steps > Step 9: Execute Build and Tests @ v2.11.0 (6a378b5) [both]

**Failure predicate**: Build and Test has failed when any build or test command
fails OR any applicable target is `Not Met` or `Unverified`. Before entering
failure handling, finalize the matrix and summary with all evidence available
on that exit path. Weakening, relaxing, lowering, or disabling a defined
quality target is never an acceptable fix.

Adaptation: A task is checked only when its checks pass. A check that was not run is reported as not run, never as passed, and a skipped or filtered test is reported with its count.

## When something fails

> Source: A1 `core/aidlc-common/stages/construction/build-and-test.md` > Steps > Step 9: Execute Build and Tests @ v2.11.0 (6a378b5) [both]

1. **In-stage fix (max 2 attempts)** — for root causes inside this stage's own
   remit (test config, build scripts, environment setup, or an executable target
   check): read the failure evidence, identify the failing configuration or
   scaffolding, apply the fix, re-run the failing step, and refresh the target
   matrix.
2. **Classify and estimate impact** — when in-stage attempts are exhausted OR the
   diagnosis points upstream: decide whether the root cause lies in the
   generated source or test code — regardless of defect size — or an approach
   chosen at code-generation (library/version, container image, instance type,
   algorithm, flag). If so, look for an identifiable fix in a swappable
   dimension (newer image, driver, wheel index, a CLI flag) and ESTIMATE ITS
   IMPACT — effort, financial cost, risk. Never declare a feasible path out of
   scope on an IMPACT-UNESTIMATED effort assumption.
[...] Giving up is the human's decision to make, never the
   agent's. [...]

Adaptation: specflow has no autonomous loop-back. After two in-task fixes fail, stop and tell the developer the failure, its likely cause, and each candidate fix with its estimated effort and risk. When the cause lies in an approved artifact, the fix goes back through that artifact and its approval.

> Source: A1 `core/aidlc-common/stages/construction/build-and-test.md` > Steps > Step 9: Execute Build and Tests @ v2.11.0 (6a378b5) [both]

**On success**: Only when every executed command passed AND every applicable
target is `Met` (or the inventory has the single explanatory `N/A` row), update
the Build and Test Summary with a successful readiness result.

## The spec is covered

> Source: A1 `core/aidlc-common/stages/construction/build-and-test.md` > Steps > Step 10: Cross-Unit Final Coverage Gate @ v2.11.0 (6a378b5) [both]

[...] Verify each
enumerated ID is covered with status `OK` in at least one stage-level or Unit
entry and that its target file exists. [...] Any uncovered ID is a build-and-test finding that must be
surfaced at the approval gate.

Adaptation: Before the spec is complete, every acceptance criterion of `requirements.md` is cited by a checked task whose `Outcome:` line shows its check passed. An uncovered criterion is reported, never closed by a task that does not build it.

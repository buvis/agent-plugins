---
prd: docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v1.md
review: 1
date: 2026-11-02
head_sha: 6c1352c6416e7a21bbbb72980973a01541c7e926
codex_thread_id: 01a19b97-9cb3-7b52-93d7-e3b836fe3ed9
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: 9c5431df
  carl: b11ec139
---

# Review: 00013-autopilot-session-helpers-v1

Diff range: `843e6e7d51c56377adc1c01fab9ae7ea7755e1f4..6c1352c6416e7a21bbbb72980973a01541c7e926`

codex_rung_guard: not fired

## Review Summary

Reviewed: 11 completed tasks
PRDs checked: 00013-autopilot-session-helpers-v1.md
Cycle: 1 of cap 2. Consensus engine: legacy. Doubt reviewer: codex.
Context pack: ok. Consolidation: `consolidate_findings.py` (script), exit 0.
Settled-decisions ledger: none on entry (cycle 1), so no `--ledger` flags were passed.

### Agent Status

- Alice: available (native subagent, consensus lens)
- Blake: available (native subagent, blind lens, PRD-only)
- Bob: available (codex, doubt lens + de-slop; one retry, see below)
- Carl: available (copilot backend, model gemini-3.8-flash)
- Eve: disabled (resolved doubt reviewer is codex and no task was implemented by codex, so the roster guard did not activate her)

### Dispatch notes

- Bob's first dispatch failed: codex refused the inlined prompt at 1,627,530 characters against its 1,048,576-character input cap. The one-retry budget was spent on a rebuilt inlined prompt of 887,608 characters, which omits two paths from the inlined diff purely for size and names them explicitly to him: `tools/autopilot/source-map.json` (+8185 -11, generated provenance map whose generator `tools/autopilot/update_helper_map.py` IS inlined) and `docs/dev/project-management/**` (+2536 -42 across 29 work-management files). Everything else in the range reached him verbatim. The retry succeeded and produced a complete review with all five `D{n}` lines.
- Bob's dispatch row `prompt_bytes` understates what codex received on the first attempt and matches the retry row `9c5431df`.
- Carl ran on the copilot backend with model gemini-3.8-flash and returned non-empty reviewer text.

### Test gate

`review-stage` ran the full suite at HEAD this cycle and its parser could not read counts from the bare `pytest -q` tail, so `autopilot verify` was run once at the same HEAD through a wrapper that emits the canonical summary line. Both runs agree on 20 failures and a clean tree; they disagree on the pass count (the staging run logged `20 failed, 800 passed in 347.40s`, the verify run `PASS 793 FAIL 20 SKIP 0 EXIT 1`). The 7-test difference is unexplained and is recorded here rather than smoothed over; the `Tests:` line below carries the `autopilot verify` result, which is the run that wrote `last-verification.json`.

19 of the 20 failures are the PRD 00018 task-7 red tests in `tests/autopilot/test_controller_capacity.py`, `tests/autopilot/test_controller_owner.py` and `tests/autopilot/test_controller_owner_recovery.py` (committed at b4655fe with no implementation, a parked separate PRD). The 20th, `tests/autopilot/test_package.py::TargetPackageTest::test_ci_autopilot_wired_with_python312_and_complete_pinned_plugins_job`, is new this cycle and three reviewers traced it independently to the remote dependency bumps merged at 6c1352c: `.github/workflows/validate.yml` now pins `actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` while the test still asserts `5fda3b95a4ea91299a34e894583c3862153e4b97`. It is a pin-synchronization failure, not a helper defect, but it does leave this PRD's Phase 2 exit criterion unmet.

## Alice

Consensus lens, implementation-aware. Six findings: one Medium on unhandled `OSError` when `--verify`'s argv cannot be spawned (reproduced against `/nonexistent/cmd`), two Mediums on the 50-line function limit plus a duplicated staged-file map, one Medium attributing the `test_package.py` red test to the merged workflow bumps, and two Lows (`git status` index refresh under concurrency, and a silent `pytest.skip` that drops the real-source provenance check where `AUTOPILOT_SOURCE_ROOT` is unset).

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: fail
R11: pass
R12: fail
R13: pass

## Blake

Blind lens, PRD-only prompt: no diff, no file list, no review history, no design doc, and no settled ledger. He located the code himself.

Two High findings: `--export-policy --out PATH` writes inside the live autopilot state directory with no refusal because `_in_live_state` guards only the declared input flags and skips `--out` and `--project-root` (confirmed in a temporary tree); and the Phase 2 exit criterion "pytest tests/autopilot passes" is not met at HEAD. One Medium: `--group-findings` escapes as an uncaught `AttributeError` when the findings list holds a non-object. Two Lows on write-ordering and on `reuse_verdict` trusting a recorded `log.sha256` without re-hashing.

He reported these checks as compliant: all fourteen helper scripts present and stateless; `review_close` returning controller-required (exit 3) with no snapshot supplied; expected bindings taken from the explicit `expected_context` rather than the submitted evidence; reviewer completion read from per-reviewer `outcome` fields rather than finding counts; the blind manifest and prompt restricted to blind input kinds; `--controller-action` refusing before any mutation; and the characterization review, README, CHANGELOG and `helper_dispositions` provenance all present.

B1: pass
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: fail
B15: pass
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

Doubt lens plus de-slop, on codex, in a read-only sandbox with the context and the size-trimmed diff inlined. Twenty findings in his FIX bucket: seven High boundary and authentication defects (review-title authentication bypassed by a matching ref; non-blind prompts receiving inputs outside their manifest; external artifact roots escaping repository and live-state checks; nested-repository refusal failing when the output's parent does not yet exist; verification not refusing command-input and output overlap; fresh verification certifying dirty content reached through a tracked symlink; carry snapshots passing validation without a task status) and thirteen Mediums spanning missing git timeouts, table-parsing tolerance, regression classification, derived consensus, unvalidated facade and `prepare_close` scalars, an unbounded `range` allocation in attempt validation, two provenance-map defects, the two over-limit functions, a dead `_cap` branch, and the `test_package.py` pin.

His VERIFY bucket is empty, so no verification-check queue was written this cycle. His KNOWN bucket records the 19 PRD 00018 controller failures as outside this PRD.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: pass

## Carl

Frontend and design specialist, generalist here (this PRD ships no UI). Four findings: one High on the CI pin and workflow drift, and three Medium simplifications — the two over-limit functions and the missing explicit 30-second timeout on `_git`'s `subprocess.run`.

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: fail
R13: pass

## Mechanical checks

The tautological-test detector checked 353 test functions across 23 test files and found none whose shape cannot fail.

The fail-first replay ran 649 touched tests against the pre-change code at `843e6e7d51c5`: 604 failed there and 45 passed, and one test file could not be collected at base. The 45 that passed are absorbed below as rows R35 to R39, finder `mech-check`. Four of the five are characterization suites, whose tests pass against the pre-change code by design; the fifth, `tests/autopilot/test_local_boundary_state.py`, is a single refusal test.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/4] | 🟡 | Two new functions exceed the 50-line limit. `prepare_close` is 55 lines and `stage_review` is 52 lines (signature and docstring included). Extract the argument validation and the input assembly. | plugins/autopilot/scripts/review_close.py:467 | 6 | ALICE, CARL |
| R2 | [2/4] | 🟡 | `stage_review` is 52 lines, over the 50-line limit. It also builds the staged file map twice: once at line 513 to collect output paths, and again in `_write_cycle` at line 448. Build it once and pass it down. | plugins/autopilot/scripts/review_stage.py:513 | 5 | ALICE, CARL |
| R3 | [1/4] | 🟠 | `--export-policy --out PATH` writes to a path inside docs/dev/project-management/autopilot/ with no refusal. I confirmed this in a temp tree: the file was created. The live-state guard `_in_live_state` only checks `_INPUTS` (stage_review, group_findings, check_evidence, expected_context, policy, prepare_close). It skips `--out` and `--project-root`. The spec says no helper reads or writes the live autopilot state directory, and this write is an unguarded overwrite (`write_bytes`). | plugins/autopilot/scripts/autopilot.py:49 | Phase 2 task 1 | BLAKE |
| R4 | [1/4] | 🟠 | The Phase 2 exit criterion "pytest tests/autopilot passes" is not met. The gate shows 20 failures. The 19 controller tests (AP 00018 task 7: owner, capacity and owner_recovery) are documented as red on purpose. The 20th is `test_package.py::test_ci_autopilot_wired_with_python312_and_complete_pinned_plugins_job`. I re-ran it: the workflow's setup-python pin is 6d4fd22b..., but the test expects 5fda3b95.... The merge at HEAD caused this and no document records it. The 13 other test files tied to 00013 passed (369 passed), so the failure is in the pin or test, not in the helpers. | tests/autopilot/test_package.py:454 | Phase 2 task 2 | BLAKE |
| R5 | [1/4] | 🟠 | A matching ref bypasses review-title authentication: `_backed` compares only severity/file, so chosen evidence can describe a different issue from the hashed review row. Require the normalized title to match that selected row too. | plugins/autopilot/scripts/review_close.py:232 | 6 | BOB |
| R6 | [1/4] | 🟠 | Nonblind prompts receive context, diff, pack and history regardless of their allowed refs. Removing a job's diff ref and recomputing the manifest still exposes the diff path. Gate every rendered input and referenced artifact by that job's manifest. | plugins/autopilot/scripts/review_stage.py:251 | 5 | BOB |
| R7 | [1/4] | 🟠 | External artifact roots bypass repository checks. An artifact root in another repository can overwrite tracked outputs or write its live autopilot directory because only the supplied project's boundaries are checked. Validate the destination's repository and live-state boundaries before writing. | plugins/autopilot/scripts/review_stage.py:376 | 5 | BOB |
| R8 | [1/4] | 🟠 | Nested-repository refusal fails when the output's immediate parent does not exist: the Git probe raises OSError and `_in_nested_repo` returns false. A destination such as `nested/new/deep/run.log` is consequently allowed. Probe its nearest existing ancestor. | plugins/autopilot/scripts/log_sink_refusal.py:143 | 4 | BOB |
| R9 | [1/4] | 🟠 | Verification never checks output/input overlap. Setting the log to an untracked Python script passed in argv deletes that script before execution; selecting it as the artifact overwrites it afterward. Refuse command-input collisions before opening either output. | plugins/autopilot/scripts/verification.py:70 | 9 | BOB |
| R10 | [1/4] | 🟠 | Fresh verification can certify dirty product content reached through a tracked symlink into the management store. `_dirty_check` excludes the changed target; only reuse performs the symlink-target check. Apply that check before execution and when calculating reusable evidence. | plugins/autopilot/scripts/dirty_tree.py:209 | 9 | BOB |
| R11 | [1/4] | 🟠 | Carry snapshots need not contain a task status. Removing `status` passes `_snapshot_valid`, and `None != "completed"` then proves an unfinished task incorrectly. Validate all required CarryTaskSnapshot fields before evaluating carry eligibility. | plugins/autopilot/scripts/review_close.py:120 | 6 | BOB |
| R12 | [1/4] | 🟠 | Pinned CI test fails due to python-version 3.15 and workflow step drift | .github/workflows/validate.yml:25 | general | CARL |
| R13 | [1/4] | 🟡 | `--verify` crashes with a raw traceback when the argv cannot be spawned (missing or non-executable command). `Popen` raises `FileNotFoundError` or `PermissionError`, which `_call` (catches only TypeError and ValueError) does not handle. The log sink is left behind with no artifact and no JSON on stdout. I reproduced it with `--verify ... -- /nonexistent/cmd`. The contract says a failing command still returns an artifact or a clear refusal. No test covers an unspawnable command. Catch OSError around `Popen` in `_execute` (or in `run_verification`) and return a refusal or a failed artifact, and add a regression test. | plugins/autopilot/scripts/verification.py:141 | 4 | ALICE |
| R14 | [1/4] | 🟡 | The 20th failure, `test_ci_autopilot_wired_with_python312_and_complete_pinned_plugins_job`, is not caused by this PRD's helper code. Remote bumps merged at 6c1352c changed `.github/workflows/validate.yml` (commits c8e9b69 and fa3ae94: setup-python 6d4fd22 / v7.1.0 and python-version 3.15). The test still pins the old SHA (`SETUP`) and `"3.10"` at line 456. The PRD's own edits to this test file did not refresh these pins, so the merged HEAD is red. Update the pins in the test, or hold the bump. | tests/autopilot/test_package.py:25 | general | ALICE |
| R15 | [1/4] | 🟡 | `--group-findings` crashes with an uncaught AttributeError traceback when the findings list holds a non-object. `rework_groups.group` calls `finding.get(...)` and raises ValueError only for dicts with bad fields. `_call` catches only TypeError and ValueError, so there is no clean exit-2 usage error. | plugins/autopilot/scripts/rework_groups.py:105 | Phase 1 task 1 | BLAKE |
| R16 | [1/4] | 🟡 | Git probes have no timeout despite the required 30-second bound. Verification's execution deadline does not cover these preflight/postflight calls. Add the timeout and translate TimeoutExpired into the documented fail-closed outcomes. | plugins/autopilot/scripts/dirty_tree.py:19 | 9 | BOB |
| R17 | [1/4] | 🟡 | Table parsing accepts rows missing trailing columns and mishandles embedded issue pipes when File precedes Issue. The overflow branch assumes Issue precedes File. Parse escaped delimiters consistently, respect named-column order, and reject truncated rows. | plugins/autopilot/scripts/findings.py:83 | 2 | BOB |
| R18 | [1/4] | 🟡 | Regression classification returns false for an empty parsed file cell and returns true before checking later invalid line references, such as an introduced line followed by line 99999. Validate every referenced path/line first; any unresolved cell must produce null. | plugins/autopilot/scripts/cap_check.py:220 | 7 | BOB |
| R19 | [1/4] | 🟡 | Derived consensus is discarded when checking gates. A two-reviewer finding with omitted optional `found_by` passes attribution but fails the single-voice check because the gate receives the original row. Evaluate consensus using the validated derived reviewer set. | plugins/autopilot/scripts/review_close.py:491 | 6 | BOB |
| R20 | [1/4] | 🟡 | Malformed requests can escape as tracebacks: `findings: [null]` raises AttributeError, as do malformed staging task/text values. Validate these field shapes before invoking helpers so the facade returns the required usage exit 2. | plugins/autopilot/scripts/autopilot.py:125 | 10 | BOB |
| R21 | [1/4] | 🟡 | `prepare_close` accepts invalid scalar types, including boolean cycles and object-valued model tiers, and emits them in successful proposals. Validate cycle, batch_id and default_tier before proposal generation; map malformed snapshot reports to usage exit 2 as specified. | plugins/autopilot/scripts/review_close.py:467 | 6 | BOB |
| R22 | [1/4] | 🟡 | Attempt validation allocates `list(range(1, highest + 1))` from an unrestricted input integer. One oversized attempt can exhaust memory instead of returning a defect. Compare the sorted attempts against a sequence bounded by the number of submitted attempts. | plugins/autopilot/scripts/review_evidence.py:276 | 3 | BOB |
| R23 | [1/4] | 🟡 | Provenance maps `custody:capture_range` to custody.py, but the implementation resides in cap_check.py and custody.py does not expose it. Support function-specific target paths and record the actual implementation location. | tools/autopilot/update_helper_map.py:286 | 11 | BOB |
| R24 | [1/4] | 🟡 | Helper receipts marked passed retain `tested_package_revision: null`; regeneration can also attach old receipts to changed helper bytes. Bind helper evidence to the receipt's package revision and verify those bytes before retaining passed status. | tools/autopilot/update_helper_map.py:478 | 11 | BOB |
| R25 | [1/4] | 🟡 | `prepare_close` exceeds the function limit at 55 lines, per the supplied AST facts. Extract the final proposal/report construction into a named transformation while preserving validation order. | plugins/autopilot/scripts/review_close.py:467 | 6 | BOB |
| R26 | [1/4] | 🟡 | `stage_review` exceeds the function limit at 52 lines, per the supplied AST facts. Extract destination preparation and validation into one named operation while preserving unresolved paths. | plugins/autopilot/scripts/review_stage.py:467 | 5 | BOB |
| R27 | [1/4] | 🟡 | `_cap` retains an explicitly unreachable fallback for fewer than two non-prose groups while more than four groups exist. Remove that branch under the fixed NON_CRITICAL_CAP invariant. | plugins/autopilot/scripts/rework_groups.py:73 | 2 | BOB |
| R28 | [1/4] | 🟡 | The supplied suite reports a setup-python SHA assertion failure after the workflow pin update. Synchronize the assertion with the intended pinned action so this unrelated mismatch stops blocking the completion gate. | tests/autopilot/test_package.py:438 | general | BOB |
| R29 | [1/4] | 🟡 | Simplification: _git lacks explicit 30s timeout on subprocess.run | plugins/autopilot/scripts/dirty_tree.py:20 | 4 | CARL |
| R30 | [1/4] | ⚪ | `dirty_tree` claims "Git reads only, never writes", but plain `git status` refreshes `.git/index` opportunistically. Set `GIT_OPTIONAL_LOCKS=0` or pass `--no-optional-locks` so a concurrent controller's index lock is not contended. | plugins/autopilot/scripts/dirty_tree.py:19 | 4 | ALICE |
| R31 | [1/4] | ⚪ | `pytest.skip` when the pinned source checkout is unavailable silently drops the real-source provenance check in any environment without `AUTOPILOT_SOURCE_ROOT` (CI included). It passed here (0 skipped). Consider a loud, non-skip marker or document the CI gap. | tests/autopilot/test_helper_provenance_real.py:331 | 1 | ALICE |
| R32 | [1/4] | ⚪ | The verification artifact and the log are written by unlink-and-recreate, not temp-file-and-rename. A crash between the log write and the artifact write leaves a log with no artifact. A prior artifact is already deleted before the new one is written. The sink is guarded to explicit paths, so this is not a security issue. | plugins/autopilot/scripts/log_sink_refusal.py:200 | Phase 1 task 2 | BLAKE |
| R33 | [1/4] | ⚪ | `reuse_verdict` accepts a prior artifact's `log.sha256` without comparing it to the log on disk. The spec leaves acceptance to the controller, so this is acceptable. A caller could still treat "reused" as proof the log is intact. | plugins/autopilot/scripts/verification.py:287 | Phase 1 task 2 | BLAKE |
| R34 | [1/4] | ⚪ | The supplied suite has 19 controller capacity/owner/recovery failures from committed PRD 00018 task-7 red tests. Their implementations belong to the separate controller workstream and are outside AP00013. | N/A | general | BOB |
| R35 | [1/4] | 🟡 | 38 touched test(s) pass against the pre-change code: test_accepted_manifest_is_returned_intact_without_writes, test_author_field_order_is_insertion_order, test_escaping_manifest_precedes_json_validation, test_field_rejections, test_file_check_precedes_containment, test_first_failure_across_checks +32 more | scripts/test_validate_characterization.py | general | mech-check |
| R36 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_capabilities_are_exact_contract_formats_without_runtime_side_effects | tests/autopilot/test_facade.py | general | mech-check |
| R37 | [1/4] | 🟡 | 3 touched test(s) pass against the pre-change code: test_preexisting_regression_ownership_is_referenced_not_reassigned, test_unrelated_arrays_and_original_owners_stay_byte_semantic, test_readme_keeps_every_historical_section | tests/autopilot/test_helper_provenance_real.py | general | mech-check |
| R38 | [1/4] | 🟡 | 2 touched test(s) pass against the pre-change code: test_export_policy_is_the_unwrapped_canonical_policy, test_malformed_missing_and_non_object_inputs_are_usage_errors | tests/autopilot/test_local_boundary.py | general | mech-check |
| R39 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_no_hidden_workflow_state_inputs_spelling_live_state_in_another_case_are_refused_unread | tests/autopilot/test_local_boundary_state.py | general | mech-check |

## Follow-up Tasks Created

Created by the decision gate's single `autopilot review-close --batch-id decision-gate` call, not by this skill (PRD 00249). See the cycle's decision-gate record in `state.json`.

Verdict: 39 findings
Tests: 793 passed, 20 failed, 0 skipped (suite run this cycle)

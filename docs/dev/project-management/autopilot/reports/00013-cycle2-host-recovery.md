# AP 00013 cycle 2 host recovery

2026-11-02. Coordinator: Codex. Review is incomplete; this is NOT a completion review or another cycle.

Duplicate reconciliation is committed as 49a27f9 in reviews/00013-duplicate-review-reconciliation.md. Keep it and all review history away from Blake. The restored cycle-1 Bob thread is 01a19b8f-6516-7a22-92b6-f45b995d9744; base is 6c1352c6416e7a21bbbb72980973a01541c7e926. No production code changed in this recovery.

## Dispatch evidence

- Alice: native Claude, claude-sonnet-5-5, high effort, session 807ecf32-911e-4a79-840f-c723308d51f6, exit 0. Model verified from native session JSONL. Complete output below.
- Blake: native Claude, claude-sonnet-5-5, high effort, session 858c6af6-aef3-4289-9744-41cd4f9e258a, exit 0. Model verified from native session JSONL. Complete output below. PRD-only prompt plus raw test-gate result; no history, design, reconciliation, diff, or file list supplied.
- Bob: installed codex-run.sh, exit 3, refusing nested dispatch (already inside a CLI agent). No model ran. Replacement measured row 437e79ba closed error; original staged placeholder row c9ec8601 closed superseded. Prompt is 247928 bytes, inlined with the design excluded. Resume flag used the restored thread.
- Carl: installed gemini-run.sh, exit 3, same host-marker refusal. No model ran. Row 64303074 closed error. This is not model unavailability; do not batch-latch Carl unavailable.

No marker was cleared by this coordinator and no recursion guard was bypassed. The installed run-autopilot cli/runner.py child_env explicitly starts fresh native sessions without inherited host identity markers while preserving AUTOPILOT_DISPATCH_DEPTH. Use the supported `autopilot review-once` route to resume the incomplete cycle in a fresh native session, with exclusive PRD ownership. Preserve all lenses and the cycle-2 cap.

## Staged evidence

Scratch cycle ID: ap00013-c2-20261102. Complete Alice/Blake outputs and all four prompts are docs/dev/tmp/{persona}-{output|prompt}-ap00013-c2-20261102.{txt|md}. Prior-findings input is docs/dev/tmp/prior-findings-ap00013-c2.md; it carries restored dispositions and the duplicate reconciliation for implementation-aware lenses only. Bob prompt builder is docs/dev/tmp/build_bob_c2.py. All reviewer prompts came from the installed registry.

First required suite command: 900 passed, 19 failed in 203.09s. Raw log: docs/dev/tmp/gate-ap00013-c2-20261102.log. All failures belong to AP 00018 owner/capacity/recovery task-7 tests. Validator passed (3 packages, 15 skills). The installed gate parser requires PASS/FAIL/SKIP/EXIT syntax and did not recognize pytest output.

The first count-adapter attempt ran pytest in-process and caused one additional isolation-test failure: 899 passed, 20 failed, log docs/dev/tmp/gate-49a27f9.log. That failure was the adapter appearing in the Python module graph, not a product change. Adapter now runs pytest in a separate process; the affected isolation test passed (1 passed). Full corrected verification is running and must be checked before handoff. Never claim either full run green.

## Wave plan

`autopilot wave plan` completed, planned wave 202611022006. One lane holds 00014, 00015, 00016, 00017, 00019, 00020, 00021. It overlaps AP 00013/00018 in protocol.py, source-map.json, plugin README and other paths. No lane launched. After closeout push, plan again and execute in sequence. The installed planner emits a sibling under github.com; before launch, respect the user rule that all worktrees live under ~/git/src/worktrees/agent-plugins. Do not launch the current forbidden path or patch the frozen source repo.

## Alice raw output

Cycle-1 findings R1–R14 are resolved in the code, and I found three new issues in the rework. I confirmed two of them by running the code.

The scoped diff itself addressed R1, R4–R14 (R2 and R3 were fixed in separate commits). I read each fix and did not re-run the suite.

[ALICE] 🟡 External artifact roots are now refused whenever any ancestor is a symlink, so macOS system aliases like `/tmp` and `/var` are refused. I ran `_destination_problem` with a root under `/tmp` and it returned "artifact_root is reached through a symlink". The contract only refuses symlink components below the supplied root, and the new test passes only because pytest `tmp_path` is pre-resolved. Compare the root's own components, or accept ancestors that resolve to the same location | File: plugins/autopilot/scripts/review_stage.py:457 | Task: 5
[ALICE] 🟡 A missing or non-executable argv[0] raises an uncaught `FileNotFoundError` from `Popen` in `_execute`, after the log sink is opened. I ran `run_verification(argv=['/no/such/cmd'])` and got the exception plus an empty `l.log`. This contradicts the docstring ("nothing written"), and the facade `_call` catches only TypeError/ValueError, so the user gets a traceback and no JSON report. This is the spawn failure from the reconciliation's D13, not the discarded R16 sink case. Catch the spawn `OSError`, remove or avoid the log, and return `ok=false` with a controlled error | File: plugins/autopilot/scripts/verification.py:144 | Task: 9
[ALICE] 🟡 Simplification: `_in_live_state` is implemented twice with the same casefold four-part scan, in the facade and in review_stage. Only the inputs differ (facade also applies realpath). Have the facade import the review_stage helper and pass both spellings | File: plugins/autopilot/scripts/autopilot.py:88 | Task: 10

Reconciliation items D19 (derived `found_by` ignored by the single-voice gate) and D22 (unbounded `range` from the attempt number) are reported there as open coordinator decisions. I did not re-derive them here.

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
R12: pass
R13: pass


## Blake raw output

[BLAKE] 🟠 Tail-sweep close is refused whenever the chosen rows are a subset of the review's evidence findings. `_link` demands every evidence finding be linked by exactly one chosen row, but tail sweep is designed to skip coverage (`_cross_check(..., coverage=False)`). I probed R2 and R4 chosen out of R2, R3 and R4 with a valid snapshot: `ok: False`, `attribution_mismatch`, "never linked ['F5']". The tail-sweep path only succeeds when the evidence holds exactly the swept findings, and the tests build evidence that way. | File: plugins/autopilot/scripts/review_close.py:222 | Task: 3
[BLAKE] 🟠 The PRD's Phase 2 exit criterion is not met. The full `tests/autopilot` suite ran with 19 failures in `test_controller_capacity.py`, `test_controller_owner.py` and `test_controller_owner_recovery.py`. I reproduced the first one: the `self.acquire(operator)` step returns exit 1 instead of 0. These are controller tests, not helper tests, so I can't tie the cause to this PRD. The criterion is still red. | File: tests/autopilot/test_controller_capacity.py:94 | Task: general
[BLAKE] 🟡 `reuse_verdict` checks that the prior artifact's head is an ancestor of the supplied `head_sha`, that only store paths changed between them, and that the working tree is clean. It never checks that `head_sha` is the repository's actual HEAD. A caller passing an older `head_sha` while HEAD carries later product commits gets "reused", because cleanliness is judged against HEAD. This weakens "changed code invalidates it". | File: plugins/autopilot/scripts/dirty_tree.py:62 | Task: 4
[BLAKE] 🟡 The facade's live-state refusal covers only request and policy inputs (`_INPUTS`) plus `--out`. `--project-root`, `--artifact` and `--log` are not checked. Writes under the project-management store are still refused by `log_sink_refusal.refuse`, but the facade does not itself refuse a `--project-root` inside `docs/dev/project-management/autopilot`. The verification argv would run with that directory as cwd. | File: plugins/autopilot/scripts/autopilot.py:188 | Task: 11
[BLAKE] ⚪ `_write` opens staged review artifacts with `O_TRUNC` and `O_NOFOLLOW` but not `O_EXCL`. `_file_problem` checks the destination before the write, so a hard link or file swapped in between would be truncated. The window is small and only affects caller-supplied artifact roots. | File: plugins/autopilot/scripts/review_stage.py:463 | Task: 5
[BLAKE] ⚪ `cap_check`, `custody` and `gate_lead` have no facade command. They are covered only by function-level tests and source-map entries. This fits the PRD's "port by function", and I flag it only because the README's facade list omits them. | File: plugins/autopilot/README.md:252 | Task: 12

B1: fail
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
B14: pass
B15: pass
B16: fail
B17: pass
B18: pass
B19: pass


## Corrected verification result

The corrected subprocess adapter completed: PASS 900 FAIL 19 SKIP 0 EXIT 1, recorded by autopilot verify for code revision 49a27f9ddfb8401f5864960d4ce12e8e55939f8a, no dirty paths, timeout, or head movement. The current docs/dev/tmp/gate-49a27f9.log holds this corrected run and replaced the earlier adapter-failure log; the earlier error was `assert not [PosixPath(.../docs/dev/tmp/pytest_gate.py)]` at test_cap_custody_helpers.py:555. There is no additional product failure. This is still a red suite, never a pass.

For the installed runner use gate command `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python docs/dev/tmp/pytest_gate.py tests/autopilot -q` so the runner sees actual count syntax. The adapter calls the original `python -m pytest` in a separate process and preserves its exit status.

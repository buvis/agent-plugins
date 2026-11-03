# AP00013 v2 task 2 verification and review recovery

2026-11-03. Task 1 stays complete. Task 2 remains incomplete; no cycle or cap resets.

Native session `ee956537-984e-4cb6-8610-1aeff2e5a3a5` completed the full-scope Devon dispatch, one Tess strengthening pass, initial Ivan implementation, de-slop and a partial Pat review. The coordinator stopped it with exit 130 while the sole MEDIUM-fix continuation was running. No peer now owns the PRD.

## Exact evidence

- Devon `103d2c13`: exact runner **20 passed, 1 PermissionError, 18 deselected**, not 21 passed. The separate cleanup probe is supplementary evidence. Eight weaknesses went to Tess. Actual worker Opus/high; actual inline prompt 5745 bytes versus rendered 5746, only a terminal newline differs.
- Tess `9ee08c5f` answered all eight points; strengthened commit `964faee`. Actual red check: **12 failed, 14 passed, 18 deselected**. Do not repeat the initial authoring or adversarial cycle.
- Ivan `a3aeabcd` implemented the changes in `4a93821`. Actual inline prompt 27758 bytes versus rendered telemetry 27674; both below cap. Narrow verification: **25 passed, 1 PermissionError, 18 deselected**. The denied `ps` call is in the test harness, not product code. A substitute probe passed, but the test as written still fails.
- De-slop `c5ab4eaf5e40d0cf46e74c435d363bfbe5f33efc` removed the pipe-close guards. Its claim that read-only pipe closure cannot raise `OSError` is unsupported: [CPython's `FileIO.internal_close`](https://github.com/python/cpython/blob/3.12/Modules/_io/fileio.c#L95-L118) raises it on a failed `close(fd)` independently of file mode. The reviewed contract explicitly requires cleanup errors not to replace a run result. Revert `43789d8` restores that contract. De-slop is not rerun.
- Pat's three oversized render-only rows were **137125, 52783, 52408 bytes** and were never dispatched. Repeated trimming exceeded the one-trim procedure; this is recorded as a process deviation, not relabelled. The actual **33286-byte** dispatch omitted the original task-2 test diff. It is a partial review only. Its output is committed at `reviews/00013-v2-task2-pat-partial-01.md`.
- Pat used native `claude-sonnet-5-5`, transcript effort `high`, no tools, session **29c0b516-5d37-4c52-939e-289e4bf0523c**. Parser exit 0: one MEDIUM and two LOW findings. The supported MEDIUM concerns uncaught result-artifact sink errors. Preserve its finding and the same review-only conversation for the mandatory follow-up.
- Interrupted Ivan row `7194e7a0` supplied a partial artifact-error fix. Its patch was preserved, reapplied after the de-slop revert, and committed as `60eb370`. A direct public-interface probe with a read-only existing artifact returned `sink-failed` and retained the prior bytes. It also proved the child had already started, so it does **not** satisfy pre-spawn artifact validation.
- Root ran the complete six-file Verify command after restoring the guard and applying that fix: **145 passed, 1 failed in 84.66s**, exit 1. The only failure is the denied `ps` call. No skip, waiver or all-green claim applies.

## Remaining bounded correction

PRD F2 explicitly says: "Validate both verification sinks and their parent descent before spawning". Pat described artifact preflight as ideal, but the PRD makes it required. Continue the existing MEDIUM fix to validate both the log and result-artifact sink before the child starts, preserve prior bytes on failed spawn, retain descriptor-pinned/no-follow/inode protections, and report later artifact open/write/close failures as controlled errors with the existing precedence. Do not replace a pinned sink by reopening its pathname after validation. No new output-management subsystem or unrelated policy expansion is authorized.

First use isolated Opus Tess for a narrowly scoped verification correction, not another initial or adversarial strengthening cycle. Replace the denied `ps` observation with a real owned-child handle and arm cleanup before `run_gate`. A pass-through `Popen` spy must preserve actual execution and observe that the implementation already terminated/reaped its child before test polling or waiting. Keep the started/PID/late-marker and failure-report assertions; never fake status, skip the case, or treat permission failure as death. Preserve test names; moving the cleanup test/helpers between the two existing recovery files is allowed to respect the 800-line limit. Add the missing result-artifact preflight and controlled-failure regressions from the PRD/Pat finding. Tests remain role-authored.

Then continue the interrupted sole MEDIUM fix with isolated Opus Ivan. Commit and run the complete Verify command, quality/style and split-hygiene gates. The required command includes both recovery files, all task-1 staging cases, and the four existing acceptance files; no global `-k` filter applies. Self-de-slop already ran once and its unsupported removal was reverted; do not repeat it.

## Complete Pat scope in the existing follow-up

Original task base: `9dc395e26152b088cc6b4d22db46fd61c3bb58be`.
Last reviewed SHA: `c5ab4eaf5e40d0cf46e74c435d363bfbe5f33efc`.

The next Pat dispatch is cycle 2, resuming **29c0b516-5d37-4c52-939e-289e4bf0523c** with `-R`, tool-less and high effort. Supply two explicitly labelled inputs in this order:

1. The previously omitted original-test diff, task base through last-reviewed SHA: `docs/dev/tmp/ap00013-v2/task2d/previously-omitted-tests.diff` (19857 bytes). It has never been reviewed by Pat.
2. The nonempty last-reviewed-SHA-to-current-HEAD delta for all three task-2 production modules, CHANGELOG and both recovery test files. Include fresh exact verification results.

Use the installed `pat-rerun-prompt.md` renderer with the combined inputs as `DELTA_DIFF`, the original MEDIUM finding verbatim, and a truthful `UNCHANGED_NOTE`: the first review covered production plus the sibling test file, not the whole task range. Ask Pat to integrate the newly supplied omitted tests and the final delta with its prior context. This completes the full review scope without sending a single oversized prompt or restarting the review counter. Measure the actual payload; preserve all code and tests within the 45000-byte target/50000-byte cap. No further file exclusion is allowed. Follow the existing MEDIUM-retry result handling after this one follow-up.

The task is not accepted until required checks and review handling are complete. Tasks 3/4 remain pending. Task 4's receipts and AP18's later helper revalidation must include `test_helper_recovery_v2_sinks.py`. AP18 and all seven backlog PRDs remain queued; controller failures still block push.

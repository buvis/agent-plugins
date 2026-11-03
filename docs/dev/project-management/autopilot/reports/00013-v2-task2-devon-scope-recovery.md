# AP00013 v2 task 2 complete adversarial scope

2026-11-03. Task 1 remains completed; task 2 remains incomplete. No counters reset.

Session bb4c3c5e-a867-41ff-98e8-f22100f228e3 completed isolated Tess correction (claude-opus-5/high, row d3696b0a), quality/style gates and commit 1c6212f98d6ec98a8138f8f31e5ebedd1035196b. Six preservation cases supplement the original fifteen task-2 cases at eccf5c6. The sibling-file exception is recorded in autonomous decisions and the deferred log. Existing task-1 tests were preserved.

The session then dispatched Devon af622d15 against only the six new cases and only verification.py/log_sink_refusal.py, omitting the original fifteen cases and autopilot.py. The root stopped the session (exit 130) before a complete handback. Two partial exploit runs occurred; no complete gate verdict is claimed. Adversarial mutations in two production files were preserved as 00013-v2-task2-incomplete-devon.patch, then those exact files were restored from HEAD. `git diff --exit-code -- plugins/autopilot/scripts` returned 0 after restoration. Transcript retained in ignored scratch task2-incomplete-devon-session.log and native session storage.

Recovery: use the root-prepared requirements-blind Devon prompt at docs/dev/tmp/ap00013-v2/task2c/devon-complete-prompt.md verbatim. It reads both test files, permits mutations only in the three task-2 production modules, and runs both files with `-k 'not staging'`. Collect-only verification selected exactly 21 cases and deselected 18 task-1 staging cases, exit 0. This is not a test pass. No third initial Tess run is needed: preserve its committed output and complete the interrupted adversarial gate. A successful exploit still triggers the single prescribed Tess strengthening pass; the actual red check, Opus Ivan, scoped verification, de-slop/style/split hygiene and isolated Pat remain mandatory.

Original task base stays 9dc395e26152b088cc6b4d22db46fd61c3bb58be, so final Pat sees the whole task-2 change. The full Verify command now explicitly includes both test files. PRD failed-spawn byte preservation and all safety defenses remain binding. AP18 and the backlog are queued; no push.

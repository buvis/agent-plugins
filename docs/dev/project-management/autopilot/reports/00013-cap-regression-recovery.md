# AP 00013 cap-regression recovery

The cycle-2 review reached cap 2 and stalled AP 00013. Review records 01 and 02,
the settled ledger, the batch deferred records, and triage stubs 00022–00029
remain authoritative history. The full suite last measured 900 passed and
19 failed; all 19 failures belong to AP 00018 controller task 7. No push occurred.

## Authorized recovery

The installed run-autopilot `references/recovery.md` cap_regression handler
permits fixing the regression on a branch and returning the original PRD to
backlog when ready. The user's standing authorization covers these reversible
repairs; no additional approval is required. This is one bounded branch repair,
not a new automatic rework allowance.

- Branch: `repair/ap00013-cap-regression`.
- Worktree: `/Users/bob/git/src/worktrees/agent-plugins/ap00013-repair`.
- Owner: Codex subagent `/root/repair_ap13`, actual model identifier not exposed.
- Scope: supported review-02 R1, R2, R4–R8; R13 test weakness and R15 bounded
  allocation when supported. R3 belongs to AP 00018 and is not changed here.
- Verification: focused reproductions before fixes, focused regression tests,
  repository validator, updated delivery provenance, and clean commit checks.
- Review: only after the work owner finishes, in a fresh native session with
  Alice, Blake, Bob and Carl, plus the additional Anthropic doubt lens required
  by the Codex implementor guard. Blake receives no review history or design.

## Review numbering and cap

The installed phase-review contract says the cap limits **rework**, not the
Phase 5 decision gate. Preserve review-01 and review-02. Number the post-repair
verification review 03 and retain `rework_cap: 2`. Restore the completed task
history from commit `cef3f51`, append the branch repair with truthful Codex
provenance, preserve the original work-start SHA, and enter review through
`phase-done --outcome tasks_done`. Do not reset the counter to gain more rework,
raise the cap, overwrite prior reviews, or dispatch further automatic rework.
The fresh gate must certify convergence or take its existing cap-out path.

## Remaining sequence

AP 00013 must complete before AP 00018 resumes. Then apply all 15 steps of
`plans/00018-replan-3.md`, including the retrospective Pat reviews. Push only
after all 19 controller tests and required checks pass. The dry-run wave has
one overlapping lane, so no backlog lane starts before closeout is pushed.

## Branch handoff

Repair completed in cce5dad, evidence a4d4ad0, map 0f86a75. The exact focused
command in the receipt passed 494 tests with no failures or skips; provenance
tests passed 44. Validator and source-map check passed. The branch was clean
after every commit; no formatter cleanup was needed. The normal merge into
master is complete. No controller changes, completion review or push occurred
in the work session. Original 15 task records were restored through statectl;
completed Codex repair task 16 was appended. `phase-done --outcome tasks_done`
queued the fresh review 03, with cap 2 unchanged.

## Review 03 and bounded v2 recovery

Fresh native session 2126dbe6-a944-4408-8807-3f4d463041b8 completed all five
lenses and stalled v1 again. The review found three staging regressions
(R7–R9), plus supported sink defects. The full suite measured 917 passed,
19 failed, 0 skipped; the exact helper command measured 494 passed,
0 failed, 0 skipped. Neither result authorizes a push.

The installed cap_regression handler also permits a v2 PRD against the
triage stub. Admit 00013-autopilot-session-helpers-v2 as one bounded,
four-task correction retaining the entire original feature contract. Keep
v1 held and preserve its exhausted cap, reviews, deferrals and task history.
V2 receives cap 2 and a fresh full review with Alice, Blake, Bob, Carl and
Eve. Do not automatically create v3 or reset an exhausted counter. Only
after v2 completion may the coordinator mark v1 superseded by that evidence;
never describe the failed v1 gate as passed.

The historical task snapshot is 00013-v1-before-review3-stall.json. It retains
all 16 completed tasks and Codex repair provenance. Abbreviated repair commit
identifiers are expanded in this preserved copy; the original snapshot and
committed live history remain unchanged.

Review 03's R7 test-evidence dismissal was too strong. With default Git
configuration the two existing metadata tests passed. With command-scoped
safe.bareRepository=explicit both failed. The coordinator reproduced both
outcomes without source changes. Preserve the safety configuration and fix
the detection; do not weaken Git policy. The review carries the correction.

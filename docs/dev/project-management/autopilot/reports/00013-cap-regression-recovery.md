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

# AP00019 close-out, 2026-11-28

Attended close-out of `00019-autopilot-controller-lifecycle-v1.md`. Review
cycle 3 (`00019-autopilot-controller-lifecycle-v1-review-3.md`) hit the rework
cap on 2026-11-25 with six HIGH rows open, each raised by one of four
reviewers. The loop moved the PRD to `hold/` and minted triage stubs. Every
backlog PRD gates on `done/00019-*` or `done/00014-*`, so the batch drained
with no PRD completed. The operator chose on 2026-11-28 to fix R3-R6 by hand,
accept R2/R7 as the deferral the PRD's Risks section already names, and close
the PRD. No review cycle was re-run; each fix commit got a per-commit patch
review.

## Cap-overflow rows

| Row | Disposition | Commit |
|---|---|---|
| R2 | Deferred to backlog PRD 00020 (atomic review acceptance: "lower-level handoff/recovery cannot bypass it"). Pinned by the strict xfail in `tests/autopilot/test_controller_rework13_lifecycle.py`, which turns red when 00020 lands. | none |
| R3 | Fixed. `workflow.jobs` is cleared at every PRD boundary: `files._bookkeeping` (stall, park, complete) and `lifecycle.reset_prd_fields` (entry, `more_prds`). | `21b03ab` |
| R4 | Fixed. `apply_unlocked` passes the admitted revision to the files sagas, and `_run_saga_body` raises `RevisionConflictError` when state moved since admission; `lifecycle.complete` passes its revision too. | `21b03ab` |
| R5 | Fixed for the resume gap. `proven_replay` also admits a stale request whose own recovery marker (operation id equals the request id, payload matches) is still active, so a saga that crashed before its ledger append resumes. | `21b03ab` |
| R6 | Fixed. Derived planning drops a dependency only on a completed task with no job row; an aborted dependency still makes `job.plan` refuse. | `21b03ab`, `dd74550` |
| R7 | Same deferral as R2. | none |

Tests: `tests/autopilot/test_closeout_00019.py`, 9 cases. The R3 park, R4 x2,
R5 and R6 completed-dependency cases were run against the code at `e09c5d2`
and failed; the aborted-dependency case was run against `21b03ab` and failed.
The "another id" case is a control and passed at `e09c5d2`. The R3 stall case
and the "another payload" control were added later and were not run against
the old code.

## Patch review (Pat, Claude Sonnet, read-only)

Commit `21b03ab`: R3, R4, R5 closed; R6 closed for completed dependencies.

| Finding | Disposition |
|---|---|
| MEDIUM: R6 also dropped a dependency on an aborted task, so `job.next` offered work whose prerequisite failed. | Fixed in `dd74550` with a test. |
| LOW: boundary sagas clear a claimed job row, so a running worker's `job.record_exit` gets `rejected_evidence` and `owner.recover` no longer sees that claim. | Accepted. The PRD left `wip/`, so the job's output is moot, and refusing a park while a job is claimed would block crash recovery. Recorded below as a follow-up for 00020/00016, which own job reconciliation. |
| LOW: the R3 test covered park only. | Stall case added in `dd74550`. Complete is reached only through `review->converged`, covered by the same `_bookkeeping` line. |
| LOW: no test for the same request id with another payload against an active marker. | Added in `dd74550`. |

Accepted residual, unchanged from cycle 3: the recovery marker and the ledger
row carry no authorizing actor, so another registered actor that reuses the
same request id and payload is admitted as a replay. Pat found no consequence
worse than the ledger case: the replay receipt binds to that actor, and the
original requester's retry gets `wrong_binding`.

## Triage stubs closed

`prds/hold/00087`-`00093` and `00095` (00086 renumbered) were minted for these
rows. R3-R6 are fixed above; R2/R7 and the review-acceptance row are owned by
00020. Closed in `e3cd8d4`.

## Still open, durable elsewhere

- `deferred/202611242306-deferred.json`, cycle-3 known gaps: saga receipts
  written in a second transaction (task 9), `workflow-v1.json` state and
  response shapes behind the runtime (task 10), and `prd.enter` recording
  `source: wip` after an interrupted backlog entry. No PRD owns these yet.
- Claimed jobs dropped at a PRD boundary (Pat LOW above).

## Delivery evidence

`reports/00018-v2-controller-delivery-receipts.json` pins `package_revision`
`dd745502abaeb144984aefcf51e10f334d0e4880` with counts measured at that commit
(89, 75, 48 and 79 passed). `reports/00014-v2-host-delivery-receipts.json`
supersedes it at the same revision. `tools/autopilot/source-map.json` is
regenerated. The controller schema and fixtures did not change, so
`contracts/controller-v1.json` and its README digest are unchanged.

## Verification

- `update_helper_map.py --check` and `export-controller-contract.py --check`: exit 0.
- `python3 scripts/validate.py`: 4 plugin packages, 16 skills.
- `python3 -m unittest discover -s scripts`: 59 tests, OK.
- Full suite at `e3cd8d4` (package bytes of `dd74550`), the 00014 receipt
  command: 2194 passed, 0 failed, 0 skipped, 1 xfailed (the 00020 strict
  xfail), 852 s. Recorded in the 00014 receipt; the source map was then
  regenerated, `--check` exit 0, and the four provenance and package test
  files passed again (103 passed).

## Host notes

Loupe reflowed `files.py`, `lifecycle.py` and `protocol.py` at an agent stop
(+995/-366 lines). The reflow was reverted, the edits were re-applied, and
loupe was switched off for this repository (`.claude/loupe.json`, untracked).

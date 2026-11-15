# Backlog and hold drain

Written 2026-11-15 at HEAD `c988f45`. Scope: 8 backlog PRDs and 48 files in
`prds/hold/`. Not in scope: specflow 00001 and 00009 open tasks, three items
in `intake/new/`.

## Why it is slow (measured)

| Cause | Evidence |
|---|---|
| Attempts end in `hold/`, not `done/` | Since 2026-10-25: 2 PRDs done (00012, 00013 v3), 5 attempts parked (00013 v1 plan gate then cap, 00013 v2 cap, 00014 v1 cap with CRITICAL, 00018 v1 replan budget, 00018 v2 dollar budget). Each park needed a hand-written recovery PRD and a full rerun. |
| One park blocks the whole queue | Every backlog PRD gates on `ls prds/done/<dep>`. Batch 202611090642 drained with 0 PRDs done. No commit since 2026-11-11. |
| A converged PRD was parked | AP00018 v2 converged at cycle 3 (0 CRITICAL/HIGH, 1615 passed at `b8e5f21`). The wrapper then parked it: `$335.97 > $300`. Its 8-finding tail sweep was queued and never ran. |
| Review is the spend | `ledger/loop-metrics.jsonl`: 00013 v2 $258 (review $151), 00013 v3 $114 (all review), 00014 v1 $259 (review $190), 00018 v2 $336 (all review; build ran on Codex, not in this ledger). 6-7 h metered per attempt. |
| Pin churn | A byte change to `workflow-v1.json`, `fixtures-v1.json`, README or CHANGELOG stales `controller-v1.json`, the README digest, the delivery receipt and `source-map.json`. 8 of the 27 AP00014 v1 stubs and AP00018 v2 R1/R5/R6/R10 are this. |
| Reviewer routes fail | Carl: Gemini CLI refuses the client tier (latched unavailable). Codex: quota-limited, and `cyber_policy` blocks Devon. |

## Dependency graph

```text
00018 v2 (converged, in hold) ─┬─ 00019 ─ 00020 ─ 00021 ─┐
                               └─ 00014 v2 ─ 00015 ──────┴─ 00016 ─ 00017
00067 engram plugin: gated on `engram nudge` (buvis/engram PRD 00012, backlog there)
```

## Steps

### 1. Close AP00018 v2 (attended, one session)

This unblocks all seven autopilot PRDs.

1. Move the PRD `hold/` to `wip/`.
2. Run the queued tail sweep through `/autopilot:work` in rework mode: review-3
   rows R1, R2, R4, R5, R8, R10, R13, R16, in at most 4 tasks. The state reset
   dropped the task records; rebuild them from the review file.
3. Run the full suite and `python3 scripts/validate.py`. Re-seal the pins last.
4. Push master (fast-forward, 50+ commits). A green `Validate` run closes the
   deferred R6.
5. Move the PRD to `done/`.

Needs the user's go: this spends past the $300 budget that parked it.

### 2. Empty `hold/` (same session, one commit)

No stub becomes a new PRD. Record each disposition in
`reviews/2026-11-15-hold-triage.md`, then `git rm` the files.

| Files | Count | Disposition |
|---|---:|---|
| 00022-00034, 00036, 00037 | 15 | Source 00013 v1/v2. Closed by 00013 v3 (done, fresh full review; `reports/00013-v3-admission.md` maps R1 to 00036, R3 to 00037). Check each of 00022-00033 against HEAD before closing; that mapping is not yet verified per stub. |
| 00035 | 1 | The 19 controller failures. Closed by AP00018 v2. |
| 00038-00064 | 27 | Source 00014 v1. Owned by 00014 v2 Phase 0 task 2, which must disposition every v1 finding. Add the stub list to that task as input. |
| 00013 v1, 00013 v2, 00014 v1, 00018 v1 | 4 | Superseded PRDs. Never move them to `done/`: `done/00014-*` and `done/00018-*` would satisfy the gates of 00015 and 00019. |
| 00018 v2 | 1 | Step 1. |

### 3. Remove the known park causes (before any launch)

1. Amend 00019 and 00020: add `contracts/controller-v1.json`,
   `plugins/autopilot/README.md`, `tools/autopilot/source-map.json`,
   `tools/autopilot/update_helper_map.py`, `test_package.py` and
   `test_helper_provenance_real.py` to the tree, and a last task "re-seal
   delivery evidence" as in 00018 v2 Phase 2 task 3. Both edit the schema and
   fixtures, so the bundle digest changes; today the paths are missing, which is
   the `module_drift` plan-gate stall that parked 00013 v1.
2. Add `rework_cap: 3` to 00016, 00017 and 00021 (default 2 parked 00014 v1;
   00018 v2 converged at 3).
3. Raise the wrapper's per-PRD budget to $450 for these opus full-lane PRDs.
   Knob name not found in this repo; it lives in the installed wrapper.
4. Plan every task to a rendered prompt of at most 45000 bytes
   (`plans/00018-replan-3.md` section 1), so the 40K replan floor is never hit.
5. Build on the Claude host. Keep Codex for Bob only; Claude runs Bob's prompt
   when Codex is out of quota.
6. Delete the stale `autopilot/wave.json` (planned 2026-11-02, names 00014 v1,
   worktree beside the repo).
7. Run `/review-prd-backlog` once on the amended backlog.

All review lenses stay. Nothing here thins a review.

### 4. Drain in two lanes

| Lane | Where | PRDs |
|---|---|---|
| C | master | 00019, 00020, 00021 |
| H | `~/git/src/worktrees/agent-plugins/host-chain`, branch `feature/autopilot-host-chain` | 00014 v2, 00015 |

1. Start lane C with the normal loop on master.
2. Start lane H with a second loop in the worktree. Unverified: that a loop
   runs from a linked worktree. Check with a status call first; if it fails,
   run H after C on master.
3. When both lanes are done, merge H into master. Expect conflicts only in the
   pin files (README digest, `source-map.json`, receipt, CHANGELOG). Resolve by
   re-running the generators, then run the full suite.
4. Run 00016, then 00017, on master.

The wave tool is not used: with the pin files listed, it cuts one lane, and it
puts worktrees beside the repo.

Critical path: 5 PRD slots (3 + 2) instead of 7. One slot was 6-7 h metered.
Estimate, from 3 samples: about $300 per PRD, $2,100 for the seven.

### 5. Engram plugin (00067)

1. Run buvis/engram PRD 00012 in that repo. It can start now; it shares no file
   with this repo.
2. When `engram nudge --help` exits 0, run 00067 here. Sonnet tier, one short
   session. Run it in a gap, not beside 00017 (both edit root `README.md` and
   `validate.yml`).

## User-owned items

1. Approve the spend past $300 for step 1, and the $450 budget for step 3.
2. Fix Gemini CLI authentication. Without it Carl stays unavailable, and 00017
   can only record its Codex + Gemini certification as incomplete.

## Unresolved questions

1. Delete the four superseded PRD files from `hold/`, or keep them there as
   records? 00014 v2 says v1 "remains intact". Recommendation: delete; git and
   the reviews keep the history.
2. 00020 includes the optional `workflow.waves.v1` operations, and 00017 says
   waves need OVCAQ 00061. Defer `waves.py` to cut 00020's diff?
3. Is $450 per PRD acceptable, about $2,100 for the seven?

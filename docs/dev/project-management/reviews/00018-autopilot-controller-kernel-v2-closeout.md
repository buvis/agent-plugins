# AP00018 v2 close-out, 2026-11-15

Attended close-out of `00018-autopilot-controller-kernel-v2.md`. Cycle 3
converged on 2026-11-11 (review `00018-autopilot-controller-kernel-v2-review-3.md`:
no CRITICAL or HIGH, 1615 passed at `b8e5f21`). The wrapper then parked the PRD
on its dollar budget (`$335.97 > $300`) before the queued tail sweep ran. The
operator asked on 2026-11-15 to unblock the backlog; this session ran the sweep,
re-sealed the delivery evidence and closed the PRD. No review cycle was re-run
and no reviewer lens was dropped: this is the Medium/Low tail of a converged
cycle, with a per-commit patch review.

## Tail sweep

The eight swept rows are the review-3 rows that were neither discarded nor a
settled deferral. Implementors ran as isolated sub-agents on disjoint file
allowlists; the lead read each diff and committed it.

| Rows | Commit | Implementor | Change |
|---|---|---|---|
| R13 | `c50ec55` | Claude Sonnet | Deterministic tests for the bounded state-lock retry (k=1, k=limit-1, k=limit). |
| R4, R8 | `7549562` | Claude Sonnet | One binding check at the parse boundary; `credential required` reaches the caller; unit cases for a wrong secret and a wrong binding. |
| R1, R16 | `e6f9f31` | Claude Opus | Sigkill row retargeted at the crash-injection test; stale `evidence` divergence rewritten; two rows recorded as explicit gaps; staging-divergence test selects its entry by topic. |
| R5, R10, R2 | `ec8a829` | Claude Opus | Successor check skips only outside every repository, decided from the file system, under `LC_ALL=C`; refresh keeps authored sentences; receipt validators moved (`update_helper_map.py` 788 to 716 lines). |

R6 (CI proof at the reworked head) was the settled deferral: see CI below.

## Patch review (Pat, Claude Sonnet, read-only, one per commit)

Every swept row got the verdict closed. No CRITICAL or HIGH.

| Commit | Findings | Disposition |
|---|---|---|
| `c50ec55` | MEDIUM: under pytest the in-loop `skipTest` ended the whole race test at the first round that missed the rendezvous. LOW x2: valid assertions skipped for such a round; the exhaustion test did not pin its cause. | All fixed in `1d83b89`: every round runs every assertion, the test skips once only when no round met, and the cause is asserted. |
| `7549562` | LOW x3: a whitespace slip; `job_id` clauses left in `fresh_binding` and `actor_binding`; a repeated `project_id` check in `apply_locked`. | Slip fixed; the `job_id` clauses carry a defence-in-depth comment (the option R4 offered), in `1d83b89`. The `project_id` repeat is accepted: R4 did not name it, and AP00019 rewrites this dispatch. |
| `e6f9f31` | LOW x5: the sigkill row's partial gap was not listed; bare `pending`/`planned` matched in divergences; the gap check ran one way; negative cases asserted any problem; pins not yet refreshed. | First four fixed in `1d83b89`; pins refreshed in `01fd160`. |
| `ec8a829` | LOW x7: bare-layout repository and unsearchable root can still skip; the locale test cannot fail without a German catalogue; four untested branches; ambient `GIT_DIR` breaks the skip tests; only the first sentence kept; map rows not yet restored. | Fixed in `1d83b89`: a deterministic `LC_ALL` test, three more refusal cases, the fixture clears `GIT_DIR` and `GIT_WORK_TREE`, every claim-free sentence is kept. Map rows restored in `01fd160`. Accepted: the bare-layout and unsearchable-root skips, which the generator cannot reach because it reads the helper paths under the root first; a symlinked-root case was not added. |

## Delivery evidence

`reports/00018-v2-controller-delivery-receipts.json` pins `package_revision`
`1d83b8950a8cbd7cfe4e3916f600d807cdd2645d` with counts measured at that commit
(89, 71, 48 and 79 passed). `tools/autopilot/source-map.json` is regenerated;
the ten controller rows carry their authored leading sentence again. The
controller schema and fixtures did not change, so `contracts/controller-v1.json`
and its README digest are unchanged.

## Verification at `01fd160`

- `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`: 1634 passed, 0 failed, 0 skipped (658 s).
- `python3 scripts/validate.py`: 3 plugin packages, 15 skills.
- `python3 -m unittest discover -s scripts`: 59 tests, OK.
- `update_helper_map.py --check` and `export-controller-contract.py --check`: exit 0.

## CI (closes review-3 R6)

`Validate` run 43707393873 on master at `01fd160`: success, jobs `plugins` and
`autopilot` both green. The push was a fast-forward of 61 commits from
`1b588a7`. This is the first green master run since 2026-11-01.

## Host notes

The loupe formatter reflowed whole files at each agent stop, including
`actors.py`; the reflow was reverted and loupe was switched off for this
repository during the sweep (`.claude/loupe.json`, untracked).

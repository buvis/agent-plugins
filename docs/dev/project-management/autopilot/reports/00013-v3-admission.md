# AP 00013 v3 admission and v2 cycle-2 finding dispositions

Written 2026-11-05 by the closeout coordinator at HEAD `8e6c4a4`.

## Authorization

The user's closeout prompt of 2026-11-05 authorizes exactly one bounded
corrective AP 00013 v3 recovery through the existing versioned recovery
procedure (`run-autopilot/references/recovery.md`, `cap_regression`: "write a
v2 PRD against the stub"; v2 precedent `1bc2c7a`). Terms:

- Keep feature number 00013. Set `rework_cap: 2`.
- Keep `lane: full`, `session_model: opus`, `default_model: opus`,
  `doubt_reviewer: fable`, `design: run`.
- Scope: R1 mixed-root symlink handling, R3 failed-artifact invalidation, and
  other confirmed in-scope defects.
- Preserve v1 and v2 caps, attempts, reviews, stubs 00022-00037 and
  deferrals. Do not reactivate v1 or v2. Do not create v4 or extend another
  exhausted budget automatically.
- All five lenses (Alice, Blake, Bob, Carl, Eve) run each cycle in a fresh
  session. Blake gets PRD-only inputs.

## Dispositions of `reviews/00013-autopilot-session-helpers-v2-review-2.md`

Evidence is the committed review, `reports/00013-v2-cycle2-closeout/`, and
the coordinator's own read of HEAD source on 2026-11-05.

| Ref | Disposition | Evidence |
|---|---|---|
| R1 | v3 T1 | Reproduced by Alice (runtime) and Eve (helper, HEAD bytes). `log_sink_refusal.py:146-158` stops the walk at any component that resolves to the root; `:191-193` resolves below-root names in the mixed-spelling fallback. Stub 00036. |
| R3 | v3 T2 | Code read confirms it: `_write_artifact` closes the sink (`verification.py:299-300`), then `_empty_pinned` (`:365-380`) finds the leaf by name. A renamed written inode keeps its JSON. Stub 00037. |
| R4, R6, R9, R12 | v3 T3 (one fix) | Four reviewers. `review_stage.py:411-418` has no handler for `subprocess.TimeoutExpired` or `OSError`, so `stage_review` raises instead of returning the contracted refusal. |
| R5 | resolved by v3 grant | The three extra test modules are test code, not product scope. v3 lists them as write paths. |
| R7 | external deferral, unchanged | The 19 AP 00018 controller nodes. Owned by AP 00018 (stub 00035). They block every push. |
| R13, R28, R29, R30 | rejected | `[MECH]` base-passing nodes are preservation controls. Their docstrings say so, and the cycle-1 ledger settled the same rows. |
| R15, R21 | v3 T4 | Doc defect: the CHANGELOG `--verify` bullets overlap and one contradicts README:303-305. |
| R20, R23 | v3 T4 | Receipt accuracy. T4 must refresh receipts anyway, because v3 changes package bytes. |
| R16 | rejected | Fail-closed on any git failure except "not a git repository" is the PRD's stated rule (v2 PRD line 48, "Git detection failure must not silently grant permission"). |
| R19 | rejected | Blake records his own input limit. He names no defect. |
| R2 | deferred | `killpg` after reap. This needs pid recycling into a new group leader inside a tiny window. Not reproduced. Low. |
| R8 | deferred | A close error on a directory descriptor can replace the first exception. Not reproduced. Medium, single voice. |
| R10, R11 | deferred | Test-strength gaps (drain after stop, nested-pointer read audit). No production defect shown. Medium, single voice. |
| R17 | deferred | `mkdir` leaves empty parent directories after a refused log sink. No tracked byte changes. Low. |
| R14, R18, R22, R24, R25, R26, R27 | deferred | Cosmetic or evidence-shape items. Low. |

Deferred rows stay in the batch deferred JSON (`deferred/202610250001-deferred.json`)
where the v2 cap-out put them. This file adds no rows and removes none.

## Not changed by this admission

- v2 stays in `prds/hold/`. It is not marked superseded until v3 passes its
  fresh full completion review.
- v1 stays in `prds/hold/` with its own history.
- AP 00018 stays on hold until AP 00013 completes.

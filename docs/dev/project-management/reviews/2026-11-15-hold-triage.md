# Hold triage, 2026-11-15

Attended triage of every file in `prds/hold/`. No stub becomes a new PRD. The
removed files stay readable with
`git show e6f9f31:docs/dev/project-management/prds/hold/<file>`; each stub's
finding is also a row in `autopilot/deferred/202610250001-deferred.json`.

`S/` is `plugins/autopilot/scripts/`, `T/` is `tests/autopilot/`.

## Source AP00013 v1 (stubs 00022-00033)

Checked against the working tree on 2026-11-15 by code read plus a probe per
defect on a case-insensitive host. The helper scripts had no uncommitted change.

| Stub | Defect | Disposition | Evidence |
|---|---|---|---|
| 00022 | Cycle-2 cap-out summary (R6, R8 at `6984cf5`) | Closed, duplicate of 00027 and 00029 | review-02 R6 and R8 |
| 00023 | Tail-sweep close refused for a subset of evidence findings | Closed, fixed | `S/review_close.py:238`, `:545`; `T/test_cap_recovery_helpers.py::test_tail_sweep_accepts_a_subset_of_evidence_findings` |
| 00024 | Full suite red: 19 controller failures | Closed, fixed by AP00018 v2 | Full suite at `c988f45`: 1615 passed, 0 failed, 0 skipped |
| 00025 | Per-job context exposes kinds the manifest did not grant | Closed, fixed | `S/review_stage.py:325-357`, `:384-388`; `test_staged_context_filters_each_input_kind_independently` |
| 00026 | External `--separate-git-dir` accepted as artifact root | Closed, fixed | `S/review_stage.py:403-426`, `:505-507`; `test_staging_refuses_nonstandard_external_git_directory` |
| 00027 | Policy export truncates `state.json` through a hard link | Closed, fixed | `S/autopilot.py:302-316`; `test_policy_export_refuses_a_hard_link_to_live_state` |
| 00028 | `.git` guard misses `.GIT` on case-insensitive filesystems | Closed, fixed | `S/log_sink_refusal.py:101-129`; `test_sink_refuses_case_alias_of_worktree_pointer` |
| 00029 | argv and log paths compared by spelling, not identity | Closed, fixed | `S/verification.py:79-91`; `test_verify_refuses_case_alias_of_an_argv_file` |
| 00030 | Cycle-3 cap-out summary (R7, R8, R9 at `cce5dad`) | Closed, duplicate of 00031, 00032, 00033 | review-03 R7, R8, R9 |
| 00031 | Git-internals guard fails open under `safe.bareRepository=explicit` | Closed, fixed | `S/review_stage.py:420-426`; `test_staging_refuses_git_metadata_when_the_bare_guard_blocks_the_probe` |
| 00032 | `_scoped` blanks the PRD for a blind job with no `prd:` grant | Closed, fixed | `S/review_stage.py:218-228`, `:638-640`; `test_staging_refuses_a_prd_inlining_job_whose_grant_lists_no_prd_ref` |
| 00033 | Shared context file always written with every kind | Closed, fixed | `S/review_stage.py:381`; `test_staging_fills_the_shared_context_artifact_from_granted_kinds_only` |

Limits of this check: the pins for 00028 and 00029 skip on a case-sensitive
filesystem, so Linux CI does not run them. `_staged_files`
(`S/review_stage.py:365-377`) still writes the tasks, merged PRD, diff and pack
files into the artifact root whatever the grants; no stub claims that, and it
is noted here for AP00015, which owns `review_stage.py`.

## Source AP00013 v2 (stubs 00034-00037)

| Stub | Disposition | Evidence |
|---|---|---|
| 00034 | Closed, cap summary of 00036 and 00037 | `reviews/00013-autopilot-session-helpers-v2-review-2.md` |
| 00035 | Closed, fixed by AP00018 v2 | Same suite run as 00024 |
| 00036 | Closed, fixed by AP00013 v3 task T1 | `autopilot/reports/00013-v3-admission.md` row R1; v3 is in `done/` after a fresh full review |
| 00037 | Closed, fixed by AP00013 v3 task T2 | Same report, row R3 |

## Source AP00014 v1 (stubs 00038-00064)

All 27 are handed to AP00014 v2. Its Phase 0 task 2 already requires a
disposition, with a repair test or an evidence-backed rejection, for every v1
cycle-2 finding; the stub list is now named there as input. None is closed
here.

## Superseded PRD versions

| File | Superseded by |
|---|---|
| `00013-autopilot-session-helpers-v1.md`, `-v2.md` | `done/00013-autopilot-session-helpers-v3.md` |
| `00014-autopilot-host-execution-v1.md` | `backlog/00014-autopilot-host-execution-v2.md` |
| `00018-autopilot-controller-kernel-v1.md` | `00018-autopilot-controller-kernel-v2.md` |

Removed, not moved to `done/`: `done/00014-*` and `done/00018-*` are the
eligibility globs of AP00015 and AP00019. Their reviews, designs, reports and
custody records are untouched.

# Assumption ledger - AP 00013 v3 (autopilot session helpers, corrective plan T1-T4)

Per-plan ledger: replaced at the first completed task of this plan, per the work
skill's assumption-ledger rule. The v2 plan's ledger remains in git history at
the commit before this one.

## 1: T1 Anchor sink symlink refusal to the leading root spelling

Tess (initial):
- `refuse` is asserted to make no `os.open` call before the `..` refusal; an implementation that spawned git with `stdin=DEVNULL` before that check would fail it.
- A `..` that appears only inside the leading root spelling (`base/side/../repo/logs/a.log`) is accepted by `refuse` (read from the contract's `".." in log_path.parts[k:]`).
- `Path("")` counts as a relative path, so `_root_anchor` returns None.
- A symlink loop before the root spelling makes `_root_anchor` return None without raising (non-strict `os.path.realpath`).
- `_symlinked_component` is called with `toplevel` equal to the given root, since the contract says it may go unused.
- The `os.open` spy patches the global `os` module; the accept test checks the spy saw at least one open.

Tess (strengthen after Devon):
- `refuse` returns exactly "is a symlink" for a symlinked leaf.
- `seed(path, body)` returns the path.
- A parent swapped for a link after `refuse` ends in `sink-failed` (not `unsafe-artifact-path`) even when the log sits two directories below it.

Ivan:
- The `..` check sits after the tracked probe, directly before `_symlinked_component`, as the contract says; the no-os.open tests pass with that order.
- With no anchor, `refuse` skips the `..` check and lets `_symlinked_component` fail closed with "is a symlink".
- The OSError message for `..` in `_pinned_parent_fd` is the implementor's own wording.

## 2: T2 Invalidate a failed artifact through a kept descriptor

Orchestrator:
- The T2 tests moved to a new sibling `tests/autopilot/test_helper_recovery_v3_artifact.py` to keep `test_helper_recovery_v3.py` under 800 lines (recorded in `state.autonomous_decisions`).

Tess (initial):
- `<ftruncate error>` / `<pwrite error>` in the reason are text that contains each OSError's message; the test checks order after the phrase, not an exact format.
- "Stop at the first step that succeeds" means exactly one `ftruncate` call when it succeeds and no further `ftruncate`/`pwrite`.
- "Complete JSON bytes forwarded" means the bytes written so far parse with `json.loads`.
- The artifact sink is the handle `_open_log_sink` returns for the artifact path.

Tess (strengthen after Devon):
- A sibling directory under the git-ignored `docs/dev/tmp/moved/` counts as "another directory"; the hard-link variant was not added.
- The `/dev/fd` listing is an acceptable descriptor count; children are reaped before the second snapshot.

Ivan:
- The fallback reason uses `str()` of each OSError.

Pat (LOW, recorded for the completion review): the `os.dup` failure branch has no test; the plan's Verify line still names `test_helper_recovery_v3.py -k failed_artifact` instead of the new file.

## 3: T3 Fail closed on git probe timeout or spawn error

Tess (initial):
- `PermissionError` is a second `OSError` case inside the contract's `except (TimeoutExpired, OSError)`.
- The refusal has exactly the keys `{schema_version, ok, error, detail}`.
- The probe passes the ancestor as `cwd` and `env` is `{**os.environ, LC_ALL: C, LANGUAGE: C}`.
- `review_stage` calls `subprocess.run` through the shared `subprocess` module object.
- Header imports and `__all__ = ["project"]` count as not changing existing tests.

Tess (strengthen after Devon):
- The refusal detail is pinned to the existing "artifact_root is inside git internals" text (design Review log keeps that wording).
- The answers-"true" control and the interrupt test use one destination only, to stay under 800 lines.
- `KeyboardInterrupt` propagating is in contract (only `TimeoutExpired` and `OSError` are caught).

Ivan:
- The CHANGELOG bullet goes last in the existing Fixed list.

Pat (LOW, recorded for the completion review): parallel id lists instead of `pytest.param(id=...)`; the `__all__ = ["project"]` re-export device (same shape as v2 review R27); the direct `_is_inside_git_dir` test overlaps the stage_review test.

## 5: [D1] plugins/autopilot/scripts/ (review cycle 1 rework)

Tess (initial):
- The facade's `--verify` exit code for a green run is not documented, so every CLI test compares the relative run's exit code with the absolute run's instead of asserting a literal (observed: 0 on success, 2 on the path refusal).
- `refuse()` is exercised with absolute candidates only; the task does not say whether a RELATIVE candidate anchors at cwd or at `repo_root`, so that contract was not invented. The relative-output behaviour is pinned at the CLI level, where the README fixes it.
- The duplication step is injected by failing `os.dup`/`os.dup2` on the artifact sink's inode inside the `verification` module; the task named the step but not the call. The tests assert the injection was reached, so a different duplication mechanism fails loudly rather than passing vacuously.
- `reason` is asserted to CONTAIN the injected OSError text, not to equal it, because the task says "carrying the underlying OSError text" without pinning the wrapper format.
- The regression was attributed to commit 27a16a3 from its subject plus the observed accept/reject split, not from reading the source.

Tess (strengthen after Devon):
- The project's pytest invocation is `uv run --no-project --with pytest python -m pytest` (from `tools/autopilot/source-map.json`; no pytest config exists in the repo).
- The five extra refusal reason strings asserted (`is not a regular file`, `is executable`, `has more than one hard link`, `resolves inside the store`, `resolves inside the git directory`) are treated as the existing contract because `tests/autopilot/test_local_paths.py` already pins them.
- "Two spellings of one file" includes a relative/absolute pair, since the documented contract resolves relative output paths against the project root.
- A `..` inside the project-root spelling (`unrelated cwd/../target project`) names the same directory and must behave like the absolute spelling; the `..` rule is about sink components below the root.
- `report["artifact"]["log"]["path"]` for an absolutely spelled output is not pinned by the requirements, so it is asserted only through the resolve-join.
- An exact `json.dumps(...) + b"\n"` byte assertion was declined as an invented serialization contract; a one-JSON-value read is equivalent against the dropped-`truncate(0)` exploit.
- The leaf symlink points at an untracked regular file rather than `src/app.py`, because the tracked rule fires first and would mask a final-component exemption.

Ivan:
- The failing tests pin only a relative project ROOT (their `refuse` cases always pass absolute candidates), so the spelling is fixed at the `run_verification` boundary rather than teaching `refuse`/`_pinned_parent_fd` to absolutise relative candidates themselves; both would pass, and this is the smaller diff.
- The new CHANGELOG bullet belongs at the top of the existing Unreleased "Fixed" list (newest first, matching where the recent verify-sink bullets sit).

Orchestrator (recorded, not an assumption of a subagent): the ⚪ finding (pass the computed anchor into `_symlinked_component`, dropping its dead `toplevel` parameter and a duplicate realpath scan) was deliberately deferred, because closing it changes the signature of a private helper that `tests/autopilot/test_helper_recovery_v3.py:223` and `:293` call directly with three arguments, in a file at 799 of its 800-line limit and outside this task's write set. Pat's CLOSURE verdict for it is `unresolved`, accepted on that basis and routed to the PRD-level review. Recorded in `state.autonomous_decisions` and in the batch deferred JSON.

Pat: no findings beyond the three CLOSURE verdicts (two resolved, one the deferral above). The documented `sonnet-run.sh` reviewer lane failed twice on this host (`OAuth session expired and could not be refreshed`, then `Session ID ... is already in use` once the first attempt had consumed the id), so the review ran through the native `autopilot:pat` worker on the same rendered prompt; the attempt record carries `review: resume_failed` as the fail-loud marker for that substitution.

## 6: [D1] prose (review cycle 1 rework)

Tess: skipped (docs-only task). Devon and the red check skipped with her.

Ivan:
- For "narrow it", the false fourth disclaimer was replaced with the still-true "or that the 19 AP 00018 controller failures are resolved", plus one sentence stating the provenance failures are resolved; the narrowed wording was not dictated.
- The new section heading ("## Gate at the reviewed head (`feca0d1`, after map regeneration)") was chosen to mirror the existing "## Final gate (run at `6888765`, before map regeneration)" stamp style.
- The new nested-repository bullet repeats the subject "`--verify` and the log-sink check" so it stands alone as a bullet; no fact was added or dropped.

Orchestrator: the task first took the micro lane (2 findings, 2 files, both clean at claim time), but the post-edit ceiling measured net 34 lines against the lane's 30-line limit, so the edit was reverted with `git checkout --` and the task re-ran through the normal lane. The attempt carries `micro_lane: "overrun"`. The gate measurements handed to Ivan were verified first-hand, not taken from the review's summary: `docs/dev/tmp/gate-ap00013-v3-c1.log:467` reads "19 failed, 1217 passed in 452.99s", the log holds exactly 19 `FAILED` lines, and grouping them by file gives 8 `test_controller_capacity.py` + 7 `test_controller_owner.py` + 4 `test_controller_owner_recovery.py`, with no provenance or package node among them. That last fact is what let the report's "not verified" hedge be closed as verified rather than restated.

Pat: skipped for this task (documentation-only diff, per the step-5.7 docs-only skip). The `review` field carries no docs-only value in the attempt grammar, so it is absent; this note is the fail-loud record of the skip. The PRD-level review lenses cover the prose.


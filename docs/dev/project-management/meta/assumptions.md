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

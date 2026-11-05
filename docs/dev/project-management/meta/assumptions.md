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

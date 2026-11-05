# Design: 00013-autopilot-session-helpers-v3

PRD: `docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v3.md`.
Base: HEAD `d3cd7fa`. Three surgical product fixes plus delivery evidence.

## Architecture fit

All changes stay in the session-helper layer of `plugins/autopilot/scripts/`
(stdlib-only, no controller imports, no state access). The controller
(`plugins/autopilot/controller/`) and AP12 contracts are untouched.

- `log_sink_refusal.py` owns the sink decision (`refuse`) and the
  descriptor-pinned descent (`_pinned_parent_fd`, `_descend`,
  `_open_log_sink`). Both R1 halves live here and share one new helper.
- `verification.py` owns the run and the result artifact
  (`_acquire_sink`, `_write_artifact`, `_close_result_sink`). R3 lives here.
- `review_stage.py` owns staging; `_is_inside_git_dir` is the only timed git
  probe in it. R4/R6/R9/R12 live here.

Prior fix: v2 cycle-1 rework commit `ce23348` (R1) added the root-alias stop
rule to `_symlinked_component` and the `resolve()` fallback to
`_pinned_parent_fd`; `8d5c325` (R3) added name-based `_empty_pinned`. Both
were introduced by that rework (cap-check attribution in the v2 cycle-2
review).

## Module placement

Edits only, plus one new test file:

| Path | Kind | Task |
|---|---|---|
| `plugins/autopilot/scripts/log_sink_refusal.py` | edit | T1 |
| `plugins/autopilot/scripts/verification.py` | edit | T2 |
| `plugins/autopilot/scripts/review_stage.py` | edit | T3 |
| `tests/autopilot/test_helper_recovery_v3.py` | new | T1-T3 |
| `tests/autopilot/test_helper_rework_sinks.py`, `test_helper_recovery_v2_sinks.py`, `test_helper_recovery_v2.py`, `test_helper_rework_stage.py` | edit only where an assertion encodes the fixed defect | T1-T3 |
| `plugins/autopilot/CHANGELOG.md` | edit | T1-T4 |
| `plugins/autopilot/README.md`, `tools/autopilot/source-map.json`, `docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json`, `docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md` | edit/new | T4 |

## Interfaces & contracts

### T1 - `log_sink_refusal.py`

New private helper:

```python
def _root_anchor(path: Path, root: Path) -> int | None:
    """Number of leading parts of the UNRESOLVED absolute `path` that form
    its root spelling: the SHORTEST prefix whose os.path.realpath equals
    os.path.realpath(root). None when `path` is relative or no prefix
    resolves to the root."""
```

- Compare with `os.path.realpath` (never `Path.resolve()`, which raises
  `RuntimeError` on a symlink loop on 3.12).
- Prefixes are built from `path.parts`; `path.parts[:k]` for k = 1..len.

`_symlinked_component(log_path: Path, repo_root: Path, toplevel: Path) -> bool`
(signature unchanged; `toplevel` may go unused but stays for the call site):

- `k = _root_anchor(log_path, repo_root)`; `k is None` → return `True`
  (fail closed: the path reaches the repo only through a symlink).
- For every prefix `path.parts[:j]`, j = k+1..len(parts), return `True` if
  `os.path.islink(prefix)`. Else return `False`.
- No other stop rule. A later component that resolves to the root is checked
  like any other.

`refuse(log_path, repo_root)` gains one check, placed directly before the
`_symlinked_component` call:

- If `".."` is in `log_path.parts[k:]` (k from `_root_anchor`, k not None)
  → return `"has a parent-directory component"`.
- Callers map any non-None reason to `unsafe-artifact-path` (unchanged).
  The new reason string is new public text: list it in CHANGELOG.

`_pinned_parent_fd(parent: Path, root: Path) -> int` (signature unchanged):

- `k = _root_anchor(parent, root)`; `k is None` → `raise OSError(f"{parent} is not under {root}")` before opening anything.
- `names = parent.parts[k:]`; `".." in names` → `raise OSError(...)` before opening anything.
- Open `os.path.realpath(root)` with `os.O_DIRECTORY`, then `_descend` each
  name (unchanged `O_DIRECTORY | O_NOFOLLOW`). No `resolve()` of any
  below-root name. Descriptor-leak rules unchanged.

Outcomes required by the PRD (T1 tests):

| Case | `run_verification` result | Effect |
|---|---|---|
| leave-and-return (`R/sub/out -> /ext`, `/ext/back -> R/sub2`) resolved spelling | `unsafe-artifact-path` | nothing spawned, no write |
| same path, root spelled via alias `A -> R` | `unsafe-artifact-path` | same |
| return link targets root itself (`/ext/back -> R`) | `unsafe-artifact-path` | same |
| component swapped to symlink after `refuse`, mixed spelling | controlled `sink-failed` | no write through the link, sentinel bytes unchanged |
| root reached via symlinked ancestor, no symlink below root | success (unchanged) | log and artifact written |

### T2 - `verification.py`

`_write_artifact(art: dict, sink) -> dict | None` (signature unchanged):

- First `keep = os.dup(sink.fileno())`. If `dup` raises `OSError`: close
  `sink` (guarded), return `{"error": "sink-write-failed", "reason": str(error)}`;
  nothing was written.
- Then truncate, write, close exactly as today.
- On any failure (`failure is not None`), invalidate through `keep`, in this
  order, stopping at the first step that succeeds:
  1. `os.ftruncate(keep, 0)`;
  2. else `os.pwrite(keep, b"\0", 0)` (a NUL first byte makes the record
     unparseable JSON, so `reuse_verdict` can never accept it);
  3. else append `"; artifact invalidation failed: <ftruncate error>; <pwrite error>"`
     to `failure["reason"]`, so the caller sees that the record may still
     parse. The slug stays `sink-write-failed` / `sink-close-failed` and
     `ok` stays `False`.
- Always `os.close(keep)` (guarded) before returning.

Effect: the written inode is emptied (or made unparseable) through a
descriptor, wherever its name points now. The only residual is two
independent syscall failures on a regular file this process holds open;
that residual is reported in `reason`, never silent. The run already returns
`ok: False`, and artifact acceptance stays controller-owned.

`_close_result_sink(sink, pin, drop, untrusted)`:

- `drop` branch unchanged.
- `untrusted` and `pin[3]` (created) → `_unlink_pinned(pin)` (identity-checked
  by name; a replacement under the name survives).
- `untrusted` and not created → nothing more (already emptied in
  `_write_artifact`).
- Remove `_empty_pinned` (its only caller is gone).

Result slugs unchanged: `sink-write-failed`, `sink-close-failed`.

### T3 - `review_stage.py`

`_is_inside_git_dir(ancestor: Path) -> bool`:

```python
try:
    probe = subprocess.run(... unchanged args, timeout=60, env=... unchanged ...)
except (subprocess.TimeoutExpired, OSError):
    return True  # cannot tell: fail closed
```

`stage_review` then returns its existing refusal for git-internal outputs.
No other change; `_git` is not modified.

### T4 - delivery

- CHANGELOG: one `--verify` bullet saying an existing log stays byte-identical
  when the spawn fails (drop "leaves no log behind"); alias/symlink bullets
  describe the root-anchored rule; add the new refusal reason; add T2/T3
  user-visible effects under the existing Unreleased section.
- Receipt JSON: new v3 receipt entry; task 5 served-model provenance only
  from what its recovery report records (native `claude-sonnet-5-5/medium`
  workers, `claude-sonnet-5-5/high` Pat, per v2 review R20); nothing inferred;
  `effort` split into `effort_served` and `effort_configured`, value
  `"not captured"` where none was recorded. Historical entries unchanged.
- Generator commands exactly as in the PRD.

## Data flow

`run_verification` → `_unsafe_paths` → `refuse` (now root-anchored, `..`
check) → dirty/HEAD checks → `_run_and_record` → `_acquire_sink(artifact)`
→ `_pinned_parent_fd` (anchored descent) → `_execute` → `_acquire_sink(log)`
→ spawn/drain → `_artifact` → `_write_artifact` (dup kept; ftruncate on
failure) → `_close_result_sink` (identity-checked unlink of created leaf).

Staging: `stage_review` → `_existing_ancestor` → `_is_inside_git_dir`
(timeout/OSError → True) → existing refusal dict.

## Reuse inventory

- `log_sink_refusal._descend` - keep as the per-name `O_NOFOLLOW` step.
- `verification._unlink_pinned` - keep for the created-leaf case.
- `os.path.realpath` - loop-safe resolver; already used for the same reason
  in `autopilot.py:93` (policy-export path check).
- Existing fixtures in `tests/autopilot/test_helper_rework_sinks.py` and
  `test_helper_recovery_v2_sinks.py` build aliased roots and sentinels; T1/T2
  tests import or copy their patterns.
- Search for an existing "anchor/prefix that resolves to root" helper:
  `rg -n "realpath|relative_to\(|is_relative_to|samefile" plugins/autopilot/scripts`
  (hits in six modules, all per-call) and
  `rg -n "realpath|def .*anchor|def .*root" plugins/autopilot/scripts`
  found no shared anchor helper (control: `relative_to` hits
  `log_sink_refusal.py:190`).

## Alternatives considered

1. **Smallest diff (chosen for T2/T3).** dup + ftruncate in one function;
   one try/except in T3.
2. **T1 smallest diff:** drop only the `resolve()` fallback and the stop rule
   line. Rejected: without an anchor the mixed-spelling case still needs some
   prefix rule, and a bare `relative_to` fails for every aliased root (breaks
   the existing alias matrix). `_root_anchor` is ~10 lines and serves both
   call sites, so the two checks cannot drift again.
3. **T1 heavy:** compare inode chains (`fstat` each step against a
   preflight-recorded chain). Rejected: more code, and `O_NOFOLLOW` descent
   below an anchored root already gives the race-free property.

## Risks & edge cases

- `_root_anchor` cost: one `realpath` per prefix; depth is small.
- A root that is itself reached through a symlink loop: `realpath` returns a
  path that never equals the root → anchor None → refused. Acceptable.
- In-repo `..` sinks become refused. No existing test or caller uses one
  (`rg` over tests: only outside-root `..` cases, which stay refused earlier).
- ftruncate on the kept descriptor after a close failure: POSIX frees the
  fd on close even on error; the dup keeps the inode open, so truncation is
  well-defined.
- Likely next changes: R2 (killpg after reap) and R8 (guarded cleanup in
  `_acquire_sink`), both deferred; neither is boxed in by this design.

## Test strategy outline

New file `tests/autopilot/test_helper_recovery_v3.py`, test names prefixed so
`-k sink_alias`, `-k failed_artifact`, `-k probe_failure` select each task:

- T1 `sink_alias`: the five rows of the T1 table; sentinels via sha256
  before/after; spawn marker file proves no spawn.
- T2 `failed_artifact`: argv renames the artifact and writes a replacement;
  inject close failure by wrapping `verification._open_log_sink`'s returned
  object so `close()` closes then raises `OSError`; assert renamed inode is
  empty (no parseable JSON), replacement byte-identical; same for an injected
  write failure; created-leaf removal only while identity matches; with
  `verification.os.ftruncate` patched to raise, the renamed inode's first
  byte is NUL (unparseable); with both `ftruncate` and `pwrite` patched to
  raise, `reason` contains `artifact invalidation failed`.
- T3 `probe_failure`: monkeypatch `review_stage.subprocess.run` to raise
  `TimeoutExpired` / `FileNotFoundError`; assert refusal dict, no artifacts.
- Each new test fails at `d3cd7fa` (fail-first evidence recorded).
- Regression suites listed per task in the PRD.

## Review log

Dispatch 1 (claude, `autopilot:worker-opus`), recorded, not fixed (non-blockers and questions):

- non-blocker: Fail-first holds only for T1 rows 3-4; rows 1-2 are already covered green at HEAD by `test_helper_rework_sinks.py::test_an_output_path_that_leaves_the_project_and_returns_through_a_symlink_is_refused`, row 5 is a success control. Label rows 1, 2, 5 as regression controls.
- non-blocker: Prior-fix attribution: `ce23348` added only the `_symlinked_component` stop rule; `8d5c325` added the `_pinned_parent_fd` `resolve()` fallback and `_empty_pinned`.
- non-blocker: T3 test must patch `subprocess.run` with a wrapper that raises only for argv containing `--is-inside-git-dir` (`_toplevel` -> `dirty_tree._git` runs first), with an artifact_root outside project_root spelled by its resolved path (`review_stage.py:_destination_problem`).
- non-blocker: T3 catch tuple misses `UnicodeDecodeError` (`text=True` strict decode of a non-UTF-8 path in stderr); add `ValueError` to the tuple.
- non-blocker: T2 dup-failure branch leaves an existing leaf's prior JSON in place (old `_empty_pinned` emptied it); call `sink.truncate(0)` (guarded) before closing in that branch.
- question: T3 maps a probe failure to the "artifact_root is inside git internals" refusal text, a false location fact; accept or name the probe failure.
- question: `_root_anchor` accepts a prefix that reaches the root through an in-repo symlink chain before the anchor; writes still go to `realpath(root)/names` with `O_NOFOLLOW`; HEAD also accepts it.
- question: The new `refuse` reason string is never shown to users (`_unsafe_paths` returns a bool); describe the CHANGELOG effect as `unsafe-artifact-path` for an in-repo `..` path.
- question: T4 receipt: say whether task 5 provenance and the effort split go into a new v3 entry only or correct the v2 task-5 entry in place.

dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 5, question 4

Dispatch 2 (codex `gpt-6-astra`, read-only; first pass `design-codex-output-00013v3-2.txt` gave two findings and could not read repo files, so it was re-run once with everything inlined, `design-codex-output-00013v3-2b.txt`; a Claude fallback started while the re-run looked empty was stopped unread once the re-run's output arrived):

- blocker (fixed): T2 swallowed an `ftruncate` failure, so a renamed inode could keep reusable JSON. T2 now falls back to `pwrite` NUL at offset 0, then reports `artifact invalidation failed` in `reason`; test strategy covers both fallbacks.
- non-blocker: `_root_anchor` refuses relative paths, so a relative `project_root` would refuse every output (current code accepts it). Suggested: anchor `path.absolute()` (no lexical normalization) instead.
- non-blocker: `## Risks & edge cases` overstates POSIX close-on-error semantics (EINTR); the dup does not depend on it. Reword.
- non-blocker: T1 tests should cover the `..` rule directly in both `refuse` and `_pinned_parent_fd` (`R/sub/../out`, `R/../R/out`) before any `os.open`.
- non-blocker: T2 tests must put the renamed and replacement files in ignored locations and include a control proving the record would otherwise be `reusable: true`; inject the write error after the full JSON bytes.
- checked, correct (codex): T1 anchoring on aliases, `/var`/`/tmp` and symlinked ancestors; `..` agreement across both paths; both `_acquire_sink` descents; descent fd ownership; T2 invalidation ordering and dup semantics; `_close_result_sink` after `_empty_pinned` removal; T3 refusal mapping (`error='unsafe-output'`); test feasibility.

dispatch 2 (codex): cardinal-sin 0, blocker 1, non-blocker 4, question 0

Dispatch 3 (codex verification, `design-codex-output-00013v3-3.txt`): checked, correct - revised `## Interfaces & contracts` T2 closes the dispatch-2 blocker (dup before mutation, ftruncate then NUL `pwrite`, double failure reported with slug and `ok: false` kept); `## Test strategy outline` T2 lines cover all three invalidation outcomes. No new cardinal sin or blocker.

dispatch 3 (codex): cardinal-sin 0, blocker 0, non-blocker 0, question 0

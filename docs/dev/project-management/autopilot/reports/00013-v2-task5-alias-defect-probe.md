# AP00013 v2 task 5: measured scope of Pat's MEDIUM alias defect

2026-11-04, coordinator claude-opus-5/high, review cycle 1 rework. Read-only
probe plus one pytest fixture measurement. No production or test file was
changed to produce this record.

## Why the first correction round went green

The first isolated Tess dispatch (dispatch 8c8a8cf5, 37292 bytes, native
claude-sonnet-5-5/medium) returned 40 passed / 0 failed: 23 pre-existing nodes
and 17 new ones. All eight cases of its new symlink test passed against the
UNFIXED tree, so that test bound nothing.

The cause was a false premise in the coordinator's brief, not a worker error.
The brief asserted that `world.target` and `world.target.resolve()` differ on
this host. Measured under the project's own runner:

    TMP_PATH          : /private/var/folders/m6/.../pytest-2355/test_report_tmp_path_aliasing0
    TMP_PATH.resolve(): /private/var/folders/m6/.../pytest-2355/test_report_tmp_path_aliasing0
    ALIASED           : False

pytest's `tmp_path` is already resolved, so both spellings are the same string
and the test's four parametrized spellings collapsed onto the one combination
that is already refused. `tempfile.mkdtemp()` IS aliased on this host
(`/var/folders/...` against `/private/var/folders/...`), which is why the
out-of-pytest probe below reproduces what pytest could not.

The worker reported the all-green result and explicitly flagged that it had not
verified whether its cases miss the regression. That report is what surfaced
the gap.

## The defect is wider than the finding states

Probe: a throwaway git repository under `tempfile.mkdtemp()`, holding a
COMMITTED directory symlink `sub` that points at the repository root, so the
work tree stays clean and no `dirty-tree` refusal can mask the result. Three
spellings of the project root crossed with three spellings of the output path,
asked of the packaged refusal module. `refuse=None` means the path was
ACCEPTED as a log sink.

    root=real      path=real      _symlinked_component=True  refuse='is a symlink'
    root=real      path=alias     _symlinked_component=False refuse=None
    root=real      path=resolved  _symlinked_component=False refuse=None
    root=alias     path=real      _symlinked_component=False refuse=None
    root=alias     path=alias     _symlinked_component=True  refuse='is a symlink'
    root=alias     path=resolved  _symlinked_component=False refuse=None
    root=resolved  path=real      _symlinked_component=False refuse=None
    root=resolved  path=alias     _symlinked_component=False refuse=None
    root=resolved  path=resolved  _symlinked_component=True  refuse='is a symlink'

`real` is the unresolved repository path, `resolved` its `.resolve()`, `alias` a
symlink outside the repository pointing at the resolved root. Only the diagonal
refuses. **Six of nine combinations accept a symlink below the repository root**
whenever the root and the output path are spelled differently, and
`_pinned_parent_fd` then resolves the parent and writes the sink through the
link. PRD criterion 8 is broken under every mixed spelling, not only under the
single `/tmp` -> `/private/tmp` example the finding gives.

Pat's reported case is therefore confirmed and is one row of six.

## The escape the break was added for still works under the fix

`_symlinked_component`'s `break` exists so that a symlink in the REPOSITORY'S
OWN ancestry - a root reached through an alias - is not mistaken for a symlink
of the sink's. Traced against the probe values, the suggested condition keeps
that: with `repo_root` a symlink to the real repository, the alias component is
relative to neither `repo_root` nor `repo_root.resolve()`, so the walk still
breaks there. A component BELOW the root is relative to `repo_root.resolve()`,
so the walk no longer breaks and the symlink is seen.

## Dispositions carried into the Ivan fix

- MEDIUM `log_sink_refusal.py:146` - confirmed, fixed, with the measured table
  above as its evidence rather than the single reported example.
- LOW `verification.py:326` - fixed. `_acquire_sink` closes the exclusive-create
  descriptor before `_open_log_sink(preserve=True)` reopens by name, so the
  inode number can be reused inside that window and the identity comparison can
  match a different file. The descriptor is retained until the comparison
  completes, with bounded cleanup.
- LOW `log_sink_refusal.py:99` - NO CHANGE. `refuse` refuses any case-aliased
  spelling with "resolves outside the repository" at its containment check,
  strictly before `_identity_hit` can read a pointer, so the described path is
  already refused more strictly than the suggestion would make it. Expanding
  pointer policy would add scope, not safety.
- LOW `tests/.../test_helper_rework_sinks.py:~375` (group id in reports) - NO
  CHANGE. `tests/autopilot/test_verification.py:141`, `:145` and `:157` already
  pin the exact key sets of the report, of the artifact, and of the stored
  bytes, so a leaked `pgid` key fails them. An added assertion would be the
  tautology the cycle-1 adjudication rules out.
- LOW `verification.py:307` (`_Pin` as a `NamedTuple`) and LOW
  `log_sink_refusal.py:211` (duplicated `if preserve:`) - noted, not fixed. Both
  are cosmetic and no unrelated refactor is authorized for this task.
- The remaining two LOW rows (created-artifact write/close coverage and
  descendant log-close/write coverage) are fixed by the correction's new tests,
  per the cycle-1 adjudication's R1/R9 instruction.

## Count discrepancy, recorded

`reviews/00013-v2-task5-pat-complete.md` states "one MEDIUM and eight LOW
findings remain" but carries seven LOW lines. The seven lines are treated as
authoritative; no eighth LOW exists in the file to adjudicate. Every one of the
seven has a disposition above.

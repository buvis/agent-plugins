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

## Addendum: the first fix was incomplete at depth 2, measured

The fix the coordinator specified (take the escape only when `current` is
outside both spellings of the root) left two of the four target tests failing.
The implementor reported this, diagnosed it, and added
`current.parent.resolve() not in stops`, after which all 40 tests passed.

That patch closes depth 1 only. Probed against the patched code with a
committed symlink one level deeper (`<root>/dir/nest-link/...`, `dir` a real
directory, `nest-link` pointing at the repository root), four of nine spelling
combinations still ACCEPT it:

    OK    root=real     path=real     depth2-link  refuse='is a symlink'
    WRONG root=real     path=alias    depth2-link  refuse=None
    OK    root=real     path=resolved depth2-link  refuse='is a symlink'
    WRONG root=alias    path=real     depth2-link  refuse=None
    OK    root=alias    path=alias    depth2-link  refuse='is a symlink'
    OK    root=alias    path=resolved depth2-link  refuse='is a symlink'
    WRONG root=resolved path=real     depth2-link  refuse=None
    WRONG root=resolved path=alias    depth2-link  refuse=None
    OK    root=resolved path=resolved depth2-link  refuse='is a symlink'

Depth is not part of criterion 8, so this is the same defect, not a new one.
Both the coordinator's first specification and the implementor's patch reasoned
about the component's own spelling; the discriminator is whether the component
sits below the repository at all.

A candidate formulation was then validated BEFORE being specified, against 63
rows - three spellings of the root crossed with three of the output path,
crossed with seven path shapes (below-root symlinks at depths 1, 2 and 3, a
symlink to a subdirectory, a symlink leaving the repository, and plain paths at
two depths):

    while current not in stops and current.parent != current:
        try:
            inside = current.parent.resolve().is_relative_to(repo_root.resolve())
        except OSError:
            inside = False
        if not inside:
            break
        if os.path.islink(current):
            return True
        current = current.parent

A component is below the repository exactly when its own parent RESOLVES inside
it; the walk stops at the first component whose parent resolves outside, which
is the root or a root alias. `WRONG rows: 0 of 63`. The `toplevel` variant of
the same rule is also 0 of 63; `repo_root.resolve()` was chosen because
`refuse` has already constrained the sink to sit under `repo_root`, so it stays
correct when `project_root` is a subdirectory of the git toplevel, where
`toplevel` would reach above it.

Both earlier specifications were the coordinator's errors. Each was reported by
the worker that hit it rather than worked around, which is what made them
visible.

## Why the probe shows more WRONG rows than the test suite can

The depth-coverage test fails 4 of its 16 cases, all of them
`resolved-root-alias-outputs`, while the probe table above marks four rows
WRONG at depth 2, including `alias-root-real-outputs` and
`resolved-root-real-outputs`. The test author raised the difference and did not
guess at it. It is not a contradiction.

The probe has THREE spellings available because `tempfile.mkdtemp()` returns an
aliased path: `real` (`/var/folders/...`), `resolved` (`/private/var/...`) and
`alias` (an explicit symlink). pytest's `tmp_path` is already resolved, so a
test can only build TWO: `resolved` and an explicit `alias`. Restricting the
probe's depth-2 rows to the two spellings a test can express leaves exactly
`root=resolved path=alias` WRONG and the other three combinations OK - which is
precisely the 4 failed / 12 passed the suite reports.

**WITHDRAWN, 2026-11-04:** this section previously claimed that the `path=real`
rows are "a third spelling the pytest world cannot construct, so no test can
cover them". That is false, and the per-task reviewer said so. A test can build
a third spelling with a second symlink - `tmp_path/ancestor-link -> tmp_path`,
giving `ancestor-link/<repo>`, the macOS `/tmp` shape of a symlinked ANCESTOR
rather than a symlink to the project itself. The claim is retracted and the
coverage gap it asserted does not exist. See
`reviews/00013-v2-task5-pat-delta.md`.

## Addendum 2: the validated fix itself regressed a shape the probe never built

The formulation above (0 wrong of 63) was applied and committed, and the
per-task reviewer's one permitted delta re-run then found a regression IN it: a
path that leaves the repository through a committed symlink and returns through
a second symlink outside it is no longer refused, because the walk stops at the
first component whose parent resolves outside. Measured over four spellings of
the root crossed with four of the output path:

    pre-task-5 original  leave-and-return accepted in  0 of 16 spellings
    first fix round      leave-and-return accepted in  0 of 16 spellings
    installed now        leave-and-return accepted in 16 of 16 spellings
    pat candidate        leave-and-return accepted in  0 of 16 spellings

So it is a regression this cycle's rework introduced, it bites under every
spelling rather than only mixed ones, and the reviewer's suggested condition -
break only when the component whose parent resolves outside is itself a
spelling of the root - is clean. Re-probed over 96 rows (four root spellings x
four path spellings x six path shapes, now including the leave-and-return
chain): installed 16 wrong, candidate 0 wrong, control 16 wrong.

The lesson is about the validation, not the rule: a 63-row table proves only
the shapes its author thought of. The coordinator chose the shapes and never
considered a path that leaves the repository and comes back; the reviewer, who
did not choose them, found it. A probe is evidence for a hypothesis, not a
substitute for an independent lens.

## Count discrepancy, recorded

`reviews/00013-v2-task5-pat-complete.md` states "one MEDIUM and eight LOW
findings remain" but carries seven LOW lines. The seven lines are treated as
authoritative; no eighth LOW exists in the file to adjudicate. Every one of the
seven has a disposition above.

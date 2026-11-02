# AP00013 v2 — Session-local helpers, corrective repair

Source: PRD `docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v2.md`; v1 design
`docs/dev/project-management/designs/00013-autopilot-session-helpers-v1-design.md`; review evidence
`docs/dev/project-management/reviews/00013-autopilot-session-helpers-v1-review-03.md:40-71` (Decision
gate, Consolidated Findings). Current source read with the Read tool at HEAD
`944f9005de26b34f43cfc54216e856fe589742cb`, not assumed. This is a four-task
corrective design against existing, shipped code — no new modules, no rebuild
of settled v1 implementation. Design pending adversarial review; no
implementation.

## Architecture fit

Unchanged from v1: helpers under `plugins/autopilot/scripts/` prepare
artifacts, parse findings, classify evidence and propose effects; they never
become a second writer of persistent workflow state (that remains AP00018's
controller). This PRD corrects four review-03 defect clusters inside that
existing boundary — it does not move the boundary:

- **T1 (staging fail-open → fail-closed)** closes R7 (bare-repo git-internals
  detection fails open on `safe.bareRepository=explicit`), R8 (a missing
  `prd:` grant silently blanks the PRD instead of refusing), R9 (the shared
  context artifact always carries every input kind regardless of what any
  job was granted). All three are "isolation/containment must fail closed,
  not open" — the same invariant, three sites in `review_stage.py`.
- **T2 (sink safety: validate before effects, not after)** closes R2 (the
  verification log sink opens after the child process has already spawned,
  so a sink failure escapes as an uncaught exception into a started
  process), R3/R12 (`_write_policy`'s blocking open hangs forever on a FIFO
  with no reader, and unconditionally touches `os.O_NOFOLLOW`, which does
  not exist on Windows), plus the inexpensive R6 containment-before-read
  reorder (confirmed **not** a real bypass in review-03's Decision gate —
  `_identity_hit` can only add refusals — but still worth moving ahead of
  the pointer-content read on hygiene grounds, per the PRD's explicit
  instruction not to reopen it as a finding).
- **T3 (test-only evidence strengthening)** replaces R13's
  implementation-shaped `range`-monkeypatch test with a behavioral
  `tracemalloc` bound. No production code changes; the existing
  `attempt_sequence_invalid` defect is the thing under test, unchanged.
- **T4 (delivery evidence refresh)** rewords R16 (README overstates what
  `plan` grants) and R23 (CHANGELOG uses internal jargon), and regenerates
  the source map/receipts bound to the actual tested revision. It also must
  account for a **new** master-Validate failure discovered at this
  session's catchup (`tests/autopilot/test_helper_provenance_real.py`: `git
  show <revision>:plugins/autopilot/README.md` fails with exit 128, "path
  ... exists on disk, but not in" the pinned `tested_package_revision`) —
  the prior receipt's pinned revision predates a README commit, so the
  provenance check can no longer `git show` it. T4's regeneration (committing
  README/CHANGELOG first, then generating receipts against that exact
  commit, per the PRD's own ordering) is what fixes this, so no separate
  task is needed — it is called out here so the task isn't closed without
  confirming the new `tested_package_revision` resolves cleanly for every
  `REFRESHED` path.

R1/R5 (the AP00018 controller suite, 19 failing tests) and R14 (resolved by
run) stay out of scope, per the PRD: T4 records their red state, never masks
it. The full gate run at T4's Exit Criteria is expected to still show these
same ~19 controller failures; that is correct, not a regression to chase.

## Module placement

No new files. All four tasks edit existing files in place:

- T1: `plugins/autopilot/scripts/review_stage.py` (three functions:
  `_destination_problem`'s git-internals probe, `stage_review`'s per-job
  manifest validation, `_staged_files`'s shared-context `variant`
  computation).
- T2: `plugins/autopilot/scripts/verification.py` (`_execute`'s sink-open
  ordering), `plugins/autopilot/scripts/autopilot.py` (`_write_policy`'s
  open flags and platform guard), `plugins/autopilot/scripts/log_sink_refusal.py`
  (`refuse`'s check ordering).
- T3: `tests/autopilot/test_cap_recovery_helpers.py` (one test body).
- T4: `plugins/autopilot/README.md`, `plugins/autopilot/CHANGELOG.md`,
  `tools/autopilot/source-map.json` (regenerated, not hand-edited),
  `docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json`
  (regenerated), `docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md` (new
  report, per PRD Structural Decomposition).

New test file `tests/autopilot/test_helper_recovery_v2.py` (T1 and T2
regressions, per PRD Repository Structure) — one file, staging cases first
(T1), sink cases appended by T2, so T1's `-k staging` filter keeps working
once T2 lands.

## Interfaces & contracts

### T1 — `review_stage.py`

**R7 — git-internals probe must fail closed, not open, on an ambiguous
answer.** Current code (`_destination_problem`, line ~463-466):

```python
ancestor = _existing_ancestor(art_real)
git_probe = _git(ancestor, "rev-parse", "--is-inside-git-dir")
if git_probe.returncode == 0 and git_probe.stdout.strip() == "true":
    return "artifact_root is inside git internals"
```

Reproduced failure mode: on a bare-repo-backed root with
`safe.bareRepository=explicit` set, `git rev-parse --is-inside-git-dir` exits
128 (`fatal: cannot use bare repository ... (safe.bareRepository is
'explicit')`); the `returncode == 0` guard then reads that failure as "not
inside git internals" and accepts the destination. Replace with a helper
that retries the probe with `safe.bareRepository=explicit` passed as a
command-scoped `-c` override (never written to any config), and refuses
when the probe is unanswerable either way — detection failure must not
silently grant permission:

```python
def _is_inside_git_dir(ancestor: Path) -> bool:
    """True when `ancestor` is inside git internals. A probe that cannot
    answer (ordinary or bare-repo `safe.bareRepository=explicit`) refuses
    rather than granting — git detection failure must not open the gate."""
    for extra_args in ((), ("-c", "safe.bareRepository=explicit")):
        probe = _git(ancestor, *extra_args, "rev-parse", "--is-inside-git-dir")
        if probe.returncode == 0:
            return probe.stdout.strip() == "true"
    return True
```

`_destination_problem` calls it: `if _is_inside_git_dir(ancestor): return
"artifact_root is inside git internals"`. `_git`'s signature already accepts
arbitrary positional args forwarded to `git`, so no change to `_git` itself
is needed (verify this at task start by reading `_git`'s current signature
in `dirty_tree.py`; if it does not forward arbitrary args, extend it there
instead of duplicating the call shape in `review_stage.py`).

**R8 — a roster job whose prompt inlines the PRD must refuse, not blank, a
missing `prd:` grant.** Current code (`_scoped`, line ~290-291):

```python
if "prd" not in kinds:
    scoped["prd"] = ""
```

This blanks silently for every job. Only `blake` and `eve` inline the PRD
text directly into their prompt (`_plan`'s `blake`/`eve` branches read
`run["prd"]` through `supplied`/`_eve_inputs`); every other job reaches the
PRD only through the context file's `## PRD` block, which `_context_file`
already omits correctly when `"prd" not in variant`. So the fix is scoped to
those two jobs, at the point `stage_review` validates its roster — before
any artifact is written:

```python
_PRD_INLINE_JOBS = frozenset({"blake", "eve"})

def _missing_prd_grant(manifest: dict[str, list[str]]) -> str | None:
    """The first roster job in _PRD_INLINE_JOBS whose manifest omits a
    `prd:` ref, or None. Those two jobs inline PRD text into their own
    prompt body (never only the shared context file), so an omitted grant
    must refuse rather than substitute an empty PRD."""
    for job in _PRD_INLINE_JOBS & manifest.keys():
        kinds = {ref.split(":", 1)[0] for ref in manifest[job]}
        if "prd" not in kinds:
            return job
    return None
```

`stage_review` calls `_missing_prd_grant(context["manifest"])` immediately
after validating `expected_context` (before any `_staged_files`/`_write`
call) and returns `{"schema_version": 1, "ok": false, "error":
"invalid-input", "reason": f"job {job!r} has no prd: grant"}` on a hit. The
existing `_scoped` blanking line is left in place for every OTHER job (it is
correct there — those jobs never see raw PRD text regardless), so this is an
added precondition, not a change to `_scoped`'s body.

**R9 — the shared context artifact must carry the union of what was
granted, never every kind unconditionally.** Current code (`_staged_files`,
line ~365):

```python
variants = inputs.get("variants", {})
shared = CONTEXT_KINDS
```

Fix: derive `shared` from the actual per-job variants, falling back to
`CONTEXT_KINDS` only when there are no variants to union (no context-reading
jobs on the roster at all — the pre-existing no-op case):

```python
shared = frozenset().union(*variants.values()) if variants else CONTEXT_KINDS
```

This is the one-line fix the PRD names directly. No other line in
`_staged_files` changes; the per-job `review-context-{job}.md` override path
(`if variant != shared:`) is unaffected because it already compares against
whatever `shared` now correctly holds.

### T2 — sink and process safety

**R2 — the verification log sink must be opened, and proven openable,
before the child process starts; a sink failure must never escape into an
already-spawned process.** Current code (`_execute`, `verification.py`
line ~154-163):

```python
try:
    proc = subprocess.Popen(
        argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True,
    )
except OSError as error:
    return {"error": "spawn-failed", "reason": str(error)}
try:
    with _open_log_sink(log, root) as sink:
        tail, drained, capped = _drain(proc, sink, digest, deadline)
    ...
```

Reproduced failure mode: a log path whose parent segment is an existing
regular file (`afile/x.log`) passes `refuse()` (which checks `log_path`
itself, not that an ancestor component is a non-directory) and is only
rejected inside `_open_log_sink`'s `_pinned_parent_fd`/`_descend` walk
(`os.mkdir`/`os.open(..., O_DIRECTORY | O_NOFOLLOW)` raising
`NotADirectoryError`) — which today runs AFTER `Popen` has already started
the child, so the exception propagates out of the `with` block uncaught,
leaving a running, unreaped child in the process group. Fix: reorder so the
sink is opened and proven BEFORE the child spawns, and a sink-open failure
is reported the same controlled way as `spawn-failed`, with the child never
started:

```python
def _execute(argv: list[str], root: Path, log: Path, deadline: float) -> dict:
    digest = hashlib.sha256()
    try:
        sink_cm = _open_log_sink(log, root)
    except OSError as error:
        return {"error": "sink-failed", "reason": str(error)}
    with sink_cm as sink:
        try:
            proc = subprocess.Popen(
                argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except OSError as error:
            return {"error": "spawn-failed", "reason": str(error)}
        try:
            tail, drained, capped = _drain(proc, sink, digest, deadline)
            exited = False
            if drained:
                try:
                    proc.wait(timeout=max(0.0, deadline - time.monotonic()))
                    exited = True
                except subprocess.TimeoutExpired:
                    pass
            if not exited:
                _kill(proc)
        except BaseException:
            _kill(proc)
            raise
        finally:
            proc.stdout.close()
            proc.stderr.close()
    return {
        "exit_code": proc.returncode if exited else None,
        "tail": tail,
        "timed_out": not exited and not capped,
        "capped": capped,
        "sha256": digest.hexdigest(),
    }
```

`run_verification`'s caller already branches on `"error" in run` the same
way for `spawn-failed`; `sink-failed` needs no new caller-side branch — it
flows through the existing `if "error" in run: return {"schema_version": 1,
"ok": False, **run}` line unchanged. Note the new `error` key is
`sink-failed`, distinct from `spawn-failed`, so a failure mode is
distinguishable in the artifact/log for whoever reads it later.

**R3/R12 — `_write_policy`'s open must not block on a FIFO, and must not
assume `os.O_NOFOLLOW` exists.** Current code (`autopilot.py`, line
~270-278):

```python
def _write_policy(out: Path, output: bytes) -> None:
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o666)
    with os.fdopen(fd, "wb") as sink:
        info = os.fstat(sink.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"{out} must be a regular file with one hard link")
        os.ftruncate(sink.fileno(), 0)
        sink.write(output)
```

Two defects: (a) `os.open` with a blocking `O_WRONLY` on a FIFO with no
reader blocks inside the `open()` syscall itself, before the `fstat`
regular-file check ever runs; (b) `os.O_NOFOLLOW` is a POSIX-only attribute
and raises `AttributeError` on Windows, which escapes `_export_policy`'s
`except (OSError, ValueError)` (neither matches `AttributeError`) as an
unhandled crash. Fix: guard the POSIX-only flag explicitly, and open
nonblocking so a FIFO without a reader refuses immediately instead of
hanging — the nonblocking flag is cleared before the write, since
`O_NONBLOCK` has no effect on a regular file's `write()` but is irrelevant
noise to carry past the type check:

```python
def _write_policy(out: Path, output: bytes) -> None:
    """Inspect the opened inode before truncating; aliases cannot redirect a
    write. Opens nonblocking so a FIFO with no reader refuses instead of
    hanging; refuses up front on a platform without O_NOFOLLOW rather than
    crashing on the attribute lookup."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError(f"{out}: platform has no O_NOFOLLOW support")
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(out, flags, 0o666)
    except OSError as error:
        if error.errno == errno.ENXIO:
            raise ValueError(f"{out} has no reader (FIFO)") from error
        raise
    os.set_blocking(fd, True)
    with os.fdopen(fd, "wb") as sink:
        info = os.fstat(sink.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"{out} must be a regular file with one hard link")
        os.ftruncate(sink.fileno(), 0)
        sink.write(output)
```

`errno` needs importing in `autopilot.py` if not already present (check at
task start). `ValueError` is already in `_export_policy`'s caught set, so no
caller-side change. `os.set_blocking(fd, True)` restores ordinary blocking
writes for the `sink.write(output)` call — `O_NONBLOCK` only needed to exist
for the `open()` itself to refuse on a FIFO with no reader; carrying it into
the write would risk a spurious partial write on a large payload.

**R6 — containment must be checked before any pointer-content read, even
though review-03 confirmed this specific instance was never an exploitable
bypass.** Current code (`log_sink_refusal.py`, `refuse`, line ~30-38):

```python
identity = _identity_hit(resolved, repo_root, toplevel)
if identity is not None:
    return identity
# Containment comes before the symlink walk, so a path that never
# touches the repository is reported as outside.
if not resolved.is_relative_to(toplevel) or not resolved.is_relative_to(
    repo_root.resolve()
):
    return _OUTSIDE
```

`_identity_hit` calls `_worktree_gitdir_pointer`, which does
`resolved.read_text()` on a linked-worktree `.git` FILE candidate before the
containment check below it ever runs. Review-03's Decision gate verified
this cannot flip an accept into an unsafe one (`_identity_hit` only ever
*adds* a refusal reason, never clears one), so this is a hygiene reorder,
not a new refusal branch: swap the two blocks so containment runs first,
with the comment moved to explain why ordering matters even when it cannot
change the outcome today:

```python
# Containment runs before any pointer-content read: a path that never
# touches the repository is refused before `_identity_hit` can open it,
# even though `_identity_hit` can only ever add a refusal, never clear one.
if not resolved.is_relative_to(toplevel) or not resolved.is_relative_to(
    repo_root.resolve()
):
    return _OUTSIDE
identity = _identity_hit(resolved, repo_root, toplevel)
if identity is not None:
    return identity
```

No other line in `refuse` changes; the function's return value is identical
for every existing test, by review-03's own verification.

**R10 — test-only, no production change.** Add a relative `gitdir:` pointer
test to `test_helper_recovery_v2.py` that runs on every filesystem (not
gated by the case-alias skip), per the PRD's T2 acceptance line.

### T3 — `test_cap_recovery_helpers.py`

Replace the `range`-monkeypatch body
(`test_attempt_validation_does_not_allocate_from_the_supplied_attempt`,
current line ~155-169) with a `tracemalloc`-measured behavioral bound. The
PRD fixes the representative input at `attempt=200000` (not R13's literal
`10**12` — large enough that a proportional `[0] * attempt` allocation is
clearly over the 1,000,000-byte ceiling on a 64-bit host, small enough that
the test cannot itself exhaust the host):

```python
import tracemalloc

def test_attempt_validation_does_not_allocate_from_the_supplied_attempt() -> None:
    checker = library("review_evidence")
    context, evidence = clean()
    result(evidence, "alice")["attempt"] = 200000

    tracemalloc.start()
    try:
        report = checker.check_evidence(checker.load_policy(), context, evidence)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()

    assert peak < 1_000_000, f"peak traced allocation {peak} bytes is not bounded"
    assert not report["ok"]
    assert "attempt_sequence_invalid" in report["defects"]
```

No production change: `check_evidence`'s existing bounded validation (the
behavior review-03 already treats as correct) is what this test measures,
not a thing it fixes. The PRD's own wording applies: "no production rewrite
is authorized by this test-only task" — if `tracemalloc` shows the current
implementation already stays under the ceiling, the task is done; if it
does not, that is a stale premise to report, not a license to touch
`review_evidence.py` under this task.

### T4 — delivery evidence refresh

**R16 — README wording.** Current text (`README.md:287`, within the
Review-staging paragraph at line ~285-292):

> `implementation-audit` grants broad context, `plan` grants tasks and
> design text, `prd` grants the raw PRD, and `test-results` grants the test
> gate.

Replace the `plan` clause: design text reaches a job's context only when
`prd` is *also* granted, because the merged PRD+design file is what carries
it (`_staged_files`'s `merged` variable, `review_stage.py` line ~346-348,
appends `## Design Doc` onto the PRD text itself before anything is staged
under the `review-prd` kind — there is no separate `design` context kind).
Corrected wording:

> `implementation-audit` grants broad context, `plan` grants tasks (design
> text reaches context only when `prd` is also granted, since the merged
> PRD file is what carries it), `prd` grants the raw PRD, and `test-results`
> grants the test gate.

**R23 — CHANGELOG wording.** Current entry (`CHANGELOG.md:32`):

> **autopilot**: cap recovery refuses hardlinked policy outputs, case
> aliases of verification inputs and worktree Git pointers, and external
> Git metadata staging roots; failed process starts preserve outputs and
> return a controlled report.

This v2 entry adds a new line (the existing line describes v1/cap-recovery
work and stays as historical record; v2's own user-visible effect is a
separate bullet, not a rewrite of history) stating the actual v2 fixes in
user-visible terms, e.g.:

> **autopilot**: session helpers now refuse staging into bare-repository
> Git internals and FIFO policy exports without a reader instead of
> silently accepting them or hanging, and a verification run that cannot
> open its log sink is reported as a controlled failure instead of leaving
> an unreaped process behind.

**Source-map/receipt regeneration.** Per the PRD's Phase 2 (T4) exit
criteria ordering: commit the README/CHANGELOG wording fixes first, record
that exact 40-hex commit SHA, then run the generator in a second commit
without touching the already-tested bytes:

```sh
python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json
python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json --check
```

Before trusting the regenerated receipt, confirm it resolves the
`test_helper_provenance_real.py` failure this session's catchup found (git
show of `plugins/autopilot/README.md` against the OLD pinned
`tested_package_revision` fails with exit 128 because that revision
predates the current README). The generator derives `tested_package_revision`
from the receipt's own `package_revision` field (there is no CLI flag for
it, per the PRD) — as long as the README/CHANGELOG commit lands before
generation, the new receipt pins the commit that actually contains the
current README, and the provenance test's `git show
{tested_package_revision}:plugins/autopilot/README.md` resolves. If it
still does not resolve after that ordering, report the actual `git show`
error rather than treating generation as having silently fixed it — this is
exactly the class of claim review-03's R14 flagged under a different
symptom (an unrun/unconfirmed check cited as passing).

Write `docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md`: the four
tasks' exact commands and outcomes, the resolved provenance check, and the
unchanged ~19 AP00018 controller failures recorded as a deferred external
obligation (never relabeled as part of this PRD's own result).

## Data flow

Unchanged from v1 at the architecture level: explicit PRD/tasks/evidence
enter staging and local checks; findings feed grouping and proposals;
verification executes explicit argv and emits explicit reports. This PRD
changes only *when* three of those checks run relative to an effect they
guard (T1's staging refusals move from "accept, then leak" to "refuse before
write"; T2's sink/process checks move from "spawn, then validate" to
"validate, then spawn") and *what* one derived value is scoped to (T1 R9's
shared-context union). No new data enters or leaves the helper boundary.

## Reuse inventory

Sweep used rationalizations verb/noun synonyms (containment: refuse/reject/
validate/guard, inside/internals/boundary; sink: open/write/spawn, fifo/pipe/
nonblocking/platform; probe: detect/check, bare/worktree/gitdir). Search
roots: `plugins/autopilot/scripts/`, `tests/autopilot/`.

- No existing `O_NONBLOCK` or `hasattr(os, "O_NOFOLLOW")` platform guard
  exists anywhere in `plugins/autopilot/scripts/` (confirmed by grep) — the
  R3/R12 fix is new, not a pattern to copy.
- No existing `safe.bareRepository=explicit` or multi-attempt git-probe
  pattern exists (confirmed by grep) — the R7 fix's retry-then-refuse shape
  is new.
- `log_sink_refusal._open_log_sink`'s descriptor-pinned open
  (`_pinned_parent_fd`/`_descend`) already exists and is reused unchanged by
  T2's R2 fix — the fix only reorders *when* it is called, not its
  implementation.
- `review_stage._context_file`'s `variant` parameter already supports a
  restricted kind set; T1's R9 fix reuses it exactly as designed — only the
  `shared` variable that feeds it was wrong.
- `verification._execute`'s existing `except BaseException: _kill(proc);
  raise` / `finally: proc.stdout.close(); proc.stderr.close()` cleanup is
  reused unchanged inside the new sink-then-spawn ordering.

## Alternatives considered

1. **Smallest-diff version: patch only the exact failing branch per
   finding**, e.g. for R7 just widen the `returncode == 0` check to also
   treat exit 128 as "not inside" (the opposite of the fix chosen). Reject:
   that keeps the fail-open shape the PRD explicitly forbids
   ("Git detection failure must not silently grant permission"); a future
   git version or config could produce yet another nonzero code this
   wouldn't anticipate. The multi-attempt-then-refuse shape fails closed by
   construction regardless of which specific exit code git returns.
2. **Chosen: fail-closed corrections scoped to the exact finding sites**,
   as designed above — one function changed per finding, no broader
   refactor, no new abstraction layer for "pre-effect validation" even
   though two findings (R2, and R3/R12) share that shape. A shared helper
   was considered and rejected: the two call sites (`verification.py`'s
   subprocess spawn and `autopilot.py`'s file write) have different
   resources to validate and different failure vocabularies
   (`sink-failed`/`spawn-failed` vs. a `ValueError` message); forcing them
   through one abstraction would cost more than the four lines of
   duplication it saves.
3. **Broader hardening pass**: also convert `_write` in `review_stage.py`
   (R17, flagged ⚪ in review-03, out of scope for this PRD) to the same
   descriptor-pinned pattern `verification.py` already uses. Reject: R17 is
   not in this PRD's four tasks; the PRD's own Risk section ("Unsupported
   policy expansion") forbids exactly this kind of unrequested scope
   growth.

## Risks & edge cases

- **R6's reorder could be read as "nothing to verify."** It changes no
  test's expected outcome by review-03's own confirmation. The acceptance
  check for T2 is therefore that `refuse`'s existing test suite stays green
  with no new assertions required for R6 itself — only R2/R3/R12 need new
  test coverage.
- **R10 is a test-only addition riding inside T2's file.** Nothing in
  `log_sink_refusal._worktree_gitdir_pointer` needs to change for it; adding
  the test without checking that first would be solving an already-fixed
  problem a second time.
- **T4's provenance-check dependency on commit ordering is fragile by
  construction**: if the README/CHANGELOG commit and the generator commit
  land in the wrong order, or get squashed together, the receipt's
  `tested_package_revision` will again predate (or now postdate, pointing
  at uncommitted generator output) the files it claims to describe. T4's
  exit criteria must show both commit SHAs and confirm `git show` resolves
  every `REFRESHED` path at the recorded revision, not just that the
  generator exited 0.
- **Likely next changes after this PRD**: AP00018's controller suite
  eventually turns green, after which the PRD's own deferred full-gate
  obligation becomes checkable for the first time; and any future helper
  that opens a sink or spawns a process should follow T2's
  validate-then-effect ordering as the established pattern, not rediscover
  it.

## Test strategy outline

New file `tests/autopilot/test_helper_recovery_v2.py`:

- **T1 (`-k staging`)**: bare-repo-backed root with
  `safe.bareRepository=explicit` configured — assert refusal (R7); a
  `blake`/`eve` manifest missing its `prd:` ref — assert `invalid-input`,
  never a successful empty-PRD stage (R8); a roster with per-job variants
  narrower than `CONTEXT_KINDS` — assert the shared `review-context-{id}.md`
  carries no kind outside the union of granted variants (R9). Also run
  existing `tests/autopilot/test_review_helpers.py`,
  `tests/autopilot/test_review_helpers_contract.py`,
  `tests/autopilot/test_cycle1_boundaries_context.py` per the PRD.
- **T2 (file, excluding `-k staging`)**: a log path under a non-directory
  ancestor (`afile/x.log`) — assert `sink-failed`, no child process left
  running, no uncaught exception (R2); a later sink write error — assert
  controlled failure with child cleanup, not a traceback; a failed spawn —
  assert prior output bytes preserved; a FIFO policy-export path with and
  without a reader — assert bounded refusal, never a hang (R3); `O_NOFOLLOW`
  made unavailable (monkeypatch `hasattr`/delattr on `os` or patch the
  function's own guard) — assert controlled platform refusal (R12); a
  relative `gitdir:` pointer on every filesystem, not only case-insensitive
  ones (R10). Also run existing `tests/autopilot/test_cycle1_hardening_sinks.py`,
  `tests/autopilot/test_cycle1_boundaries_verify.py`,
  `tests/autopilot/test_verification.py`, `tests/autopilot/test_facade.py`.
- **T3**: the single rewritten test in `test_cap_recovery_helpers.py`, plus
  existing `tests/autopilot/test_review_evidence_helpers.py`.
- **T4**: `python3 tools/autopilot/update_helper_map.py ... --check`, plus
  `tests/autopilot/test_helper_provenance.py` and
  `tests/autopilot/test_provenance.py` — these must pass against the NEW
  revision, and specifically must resolve the README `git show` that is
  currently failing on master.

Final integration (once per PRD, not per task): full
`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`,
`python3 -m unittest discover -s scripts`, `python3 scripts/validate.py`,
`python3 scripts/generate_marketplace.py --check`. Expect the same ~19
AP00018 controller failures to remain (recorded, not fixed, not masked);
every AP00013 helper node must be green, including the new
`test_helper_recovery_v2.py` and the regenerated provenance check.

## Review log

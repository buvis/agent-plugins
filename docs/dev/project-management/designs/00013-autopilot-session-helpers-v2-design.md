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
- **T4 (delivery evidence refresh)** corrects README/Unreleased changelog wording, authors measured receipts preserving history, and regenerates only the source map. The older remote-CI missing-README pin is already fixed at the current receipt revision; v2 still needs fresh evidence for its changed bytes.

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
  (authored from measured results), `docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md` (new
  report, per PRD Structural Decomposition).

New test file `tests/autopilot/test_helper_recovery_v2.py` (T1 and T2
regressions, per PRD Repository Structure) — one file, staging cases first
(T1), sink cases appended by T2. Naming convention so the Test Strategy's
`-k staging` filter stays exact: every T1 (`review_stage.py`) test function
name contains `staging`; no T2 (`verification.py`/`autopilot.py`/
`log_sink_refusal.py`) test function name does, even where its subject is
also an artifact root or a file path (e.g. name a FIFO-export test
`test_write_policy_refuses_fifo_without_reader`, not
`...staging_fifo...`).

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
inside git internals" and accepts the destination. The fix must NOT simply
refuse on every nonzero exit: `ancestor` is reached only when `art_real` is
NOT relative to `project` (the earlier `_repo_problem` branch owns that
case), so a perfectly ordinary artifact root that sits outside any git
repository at all also makes this probe exit 128 — with stderr `fatal: not
a git repository (or any of the parent directories): .git`, not a
`safe.bareRepository` complaint. That case has nothing to protect and must
still be accepted, exactly as today. Distinguish the two by stderr content,
and only fail closed on the ambiguous bare-repo case specifically — a probe
that cannot answer about an ACTUAL repository must not silently grant
permission, but a probe correctly reporting "there is no repository here"
is not an ambiguous failure:

A substring check on `safe.bareRepository` is the wrong shape for this: it
POSITIVELY identifies the bare-repo case but only NEGATIVELY identifies
"nothing to protect" (by the substring's absence), so an unrelated git
failure this doc has not enumerated — e.g. a `safe.directory`
ownership-validation error on a bare repo permitted by
`safe.bareRepository=all` — falls through the negative check and is wrongly
accepted. Invert the logic: positively identify the one genuinely benign
answer (`fatal: not a git repository`, git's own fixed message for "no
repository here at all"), and fail closed on every OTHER unclassified
failure, not only the specific bare-repo message this PRD happened to
reproduce:

```python
def _is_inside_git_dir(ancestor: Path) -> bool:
    """True when `ancestor` is inside git internals. Only git's own fixed
    "not a git repository" message is treated as benign (nothing here to
    protect); every other failure — the bare-repo `safe.bareRepository`
    restriction this PRD reproduced, an ownership/`safe.directory` error,
    or anything else fails closed without overriding Git configuration. Detection failure on
    an ACTUAL repository must not silently grant permission, and that
    includes failures this comment cannot enumerate in advance."""
    probe = _git(ancestor, "rev-parse", "--is-inside-git-dir")
    if probe.returncode == 0:
        return probe.stdout.strip() == "true"
    if probe.stderr.strip().startswith("fatal: not a git repository"):
        return False
    return True
```

`startswith`, not a bare `in` substring test: git's fixed prefix for this
specific diagnostic always leads the message (`fatal: not a git repository
(or any of the parent directories): .git`, no path interpolated before it),
whereas the bare-repo diagnostic's fixed prefix is the different string
`fatal: cannot use bare repository`. An `in` check would wrongly accept a
bare-repo failure whose quoted, attacker-or-operator-controlled path
happens to literally contain the substring `fatal: not a git repository`
(e.g. a repo path named `.../fatal: not a git repository.git`) — anchoring
to the start of the message is immune to that, since git never puts
anything before its own fixed prefix for this diagnostic.

`_destination_problem` calls it: `if _is_inside_git_dir(ancestor): return
"artifact_root is inside git internals"`. `_git` (imported from
`dirty_tree.py`) already forwards arbitrary positional args and returns a
`subprocess.CompletedProcess` with `.stderr` captured as text (confirmed by
reading its definition), so no change to `_git` itself is needed.

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
    """The first (by name, for a deterministic refusal message) roster job
    in _PRD_INLINE_JOBS whose manifest omits a `prd:` ref, or None. Those
    two jobs inline PRD text into their own prompt body (never only the
    shared context file), so an omitted grant must refuse rather than
    substitute an empty PRD."""
    for job in sorted(_PRD_INLINE_JOBS & manifest.keys()):
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
leaving a running, unreaped child in the process group. `_open_log_sink`
(`log_sink_refusal.py` line ~202-223) is a **plain function that returns an
already-opened file object** from `os.fdopen(...)` — not a
`@contextmanager` generator — so the walk and the `os.open` that can raise
`NotADirectoryError` both execute synchronously inside the call itself,
before `with` ever runs; wrapping the call in `try`/`except OSError` catches
it. (Confirmed by reading the function body, not assumed from its name.)

Fix: reorder so the sink is opened and proven BEFORE the child spawns, a
sink-open failure is reported the same controlled way as `spawn-failed`
with the child never started, and a write failure that surfaces DURING
drain (a later, not an open-time, sink error — e.g. the sink's backing
disk fills) is also converted to a controlled result rather than left to
the existing `except BaseException: _kill(proc); raise` re-raise, which
would otherwise still propagate a traceback out of `_execute` for exactly
the write-failure case T2's own test strategy requires to be controlled.
`_open_log_sink` returns `os.fdopen(sink_fd, "wb", buffering=0)` —
**unbuffered** (confirmed by reading `log_sink_refusal.py` line ~215-223)
— so an ordinary flush-at-close failure is not the exposure here; the
descriptor's own `close()` syscall can still fail (e.g. a delayed-allocation
or quota error surfacing only at close on some filesystems), and that
failure must not be left to a bare `with sink_cm as sink:` — a `with`
block's `__exit__` runs during unwinding of ANY `return` inside it,
including the `spawn-failed` and `sink-write-failed` returns below, so a
close error at that point would silently replace the already-decided
return value with an uncaught exception. Close the sink explicitly,
outside the inner control flow, and only let a close failure override the
result when the run otherwise looked clean — a write failure already
decided above takes priority over whatever close reports:

```python
def _run_against_sink(argv: list[str], root: Path, sink, digest, deadline: float) -> dict:
    """Spawns and drains `argv` against an already-open `sink`. Always
    returns a result dict (never raises OSError); re-raises any other
    exception after killing the child."""
    try:
        proc = subprocess.Popen(
            argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as error:
        return {"error": "spawn-failed", "reason": str(error)}
    try:
        sink.truncate(0)  # Only after successful spawn; preserve prior bytes on failure.
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
    except OSError as error:
        # A write failure during drain (not at sink-open time): kill the
        # child and report a controlled result instead of letting the
        # exception propagate as a traceback.
        _kill(proc)
        return {"error": "sink-write-failed", "reason": str(error)}
    except BaseException:
        _kill(proc)
        raise
    finally:
        # Best-effort pipe cleanup: a close failure here must not override
        # whatever `tail`/`error` result the block above already decided
        # (the same priority rule as the log sink's own close, below).
        for pipe in (proc.stdout, proc.stderr):
            try:
                pipe.close()
            except OSError:
                pass
    return {
        "exit_code": proc.returncode if exited else None,
        "tail": tail,
        "timed_out": not exited and not capped,
        "capped": capped,
        "sha256": digest.hexdigest(),
    }


def _execute(argv: list[str], root: Path, log: Path, deadline: float) -> dict:
    digest = hashlib.sha256()
    try:
        sink = _open_log_sink(log, root)
    except OSError as error:
        return {"error": "sink-failed", "reason": str(error)}
    close_error: OSError | None = None
    try:
        result = _run_against_sink(argv, root, sink, digest, deadline)
    finally:
        try:
            sink.close()
        except OSError as error:
            close_error = error
    if close_error is not None and "error" not in result:
        # The run itself looked clean but the sink could not be closed
        # cleanly: the log cannot be trusted, so this takes priority over
        # a result that otherwise looked like success. A write failure
        # already decided above (an "error" key already in `result`) is
        # not overridden by a close failure — the earlier, more specific
        # cause wins.
        return {"error": "sink-close-failed", "reason": str(close_error)}
    return result
```

`except OSError` is listed before `except BaseException` so it matches
first; the `except BaseException` clause still exists for every other
error class (e.g. a deliberate cancellation) and keeps re-raising those
unchanged — on that path `_execute`'s `finally` still attempts `sink.close()`
but the function never reaches its own return, so a close failure there is
swallowed by design (the caller is already getting an exception, not a
result dict). `run_verification`'s caller already branches on `"error" in
run` the same way for `spawn-failed`; `sink-failed`, `sink-write-failed` and
`sink-close-failed` need no new caller-side branch — all three flow through
the existing `if "error" in run: return {"schema_version": 1, "ok": False,
**run}` line unchanged. The four distinct `error` keys (`spawn-failed`,
`sink-failed`, `sink-write-failed`, `sink-close-failed`) keep each failure
mode distinguishable for whoever reads the result later.

A previously absent log may be created empty before a failed spawn. An EXISTING log must retain its exact prior bytes on spawn failure; existing result artifacts also remain unchanged. Open a descriptor-pinned sink without unlinking or truncating the existing file, validate it before spawn, and clear that same validated sink only after Popen succeeds. Keep no-follow parent/leaf defenses, regular-file validation and hard-link isolation/refusal before any byte change; opening must not block on a raced FIFO. Reject unsafe aliases before spawn. An OSError while clearing the sink after successful spawn uses the controlled sink-write-failed cleanup path. Reuse the existing parent traversal; do not introduce backup/restore races or a new output-management subsystem.

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
hanging. Clear the nonblocking flag only AFTER the descriptor is owned by
the `with os.fdopen(...)` block, not between `os.open` and `fdopen` — doing
it before `fdopen` risks leaking the raw `fd` if `set_blocking` itself
raises, since nothing would be holding it open for cleanup yet. `O_NONBLOCK`
is a no-op for a regular file's I/O (confirmed: `open(2)`'s man page states
it has no effect outside FIFOs and certain device files), so restoring
blocking mode on the accepted regular-file case changes nothing observable
— it is defensive consistency, not a correctness fix for that path:

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
    with os.fdopen(fd, "wb") as sink:
        # `fd` is now owned by `sink`: any exception from here on, including
        # from set_blocking itself, still closes it via this `with` block.
        os.set_blocking(sink.fileno(), True)
        info = os.fstat(sink.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"{out} must be a regular file with one hard link")
        os.ftruncate(sink.fileno(), 0)
        sink.write(output)
```

`errno` needs importing in `autopilot.py` if not already present (check at
task start). `ValueError` is already in `_export_policy`'s caught set, so no
caller-side change.

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

### T3 — bounded behavioral allocation evidence

Measure allocation inside a fresh bounded subprocess using the same Python interpreter, with a 30-second timeout. Import the existing checker/test fixtures and prepare policy, context and evidence before starting the measurement; set the supplied attempt to 200000. In that child only, stop any pre-enabled tracing and start a fresh tracemalloc measurement immediately before check_evidence. Read the absolute peak from that fresh measurement, assert it is below 1,000,000 bytes, and retain the not-ok and attempt_sequence_invalid assertions. Preserve the parent runner's tracing state; a child-local stop/start must not affect it. Do not subtract a historical peak: an earlier larger peak makes that delta zero even when the checker allocates proportionally.

Prove the measurement detects a deliberately injected [0] * 200000 allocation in a scratch-only copy/probe. It must fail the same ceiling, including when the parent starts with PYTHONTRACEMALLOC enabled and a prior peak above 8 MB. Keep the normal test isolated and deterministic; add no production resource-control mechanism. Only the existing test file may change. Do not modify review_evidence.py.

### T4 — delivery evidence refresh

Refresh docs, receipts and generated helper provenance. Depends on T1, T2, T3.

Writable paths: plugins/autopilot/README.md, plugins/autopilot/CHANGELOG.md, tools/autopilot/source-map.json, docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json, docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md.

Premise: verify T1-T3 are committed and inspect the current README grant paragraph and Unreleased CHANGELOG entry before editing. If those premises changed, skip/report the affected literal edit rather than forcing it. The remote CI failure at old pin 527d880c is historical: the current receipt pin cce5dadcfe5c951e541ef8e395ffd930b1d56b0e already contains README.md (git cat-file -e returned 0). Refresh evidence because v2 changes package bytes; do not claim to newly repair that already-fixed missing-file failure.

README: clarify that plan grants tasks; design text reaches context only when prd is also granted because the merged PRD file carries it. Preserve the other grant meanings and document the new controlled refusals.

CHANGELOG: the existing phrase "cap recovery refuses" is under Unreleased, not a published historical release. Replace it with "session helpers refuse" to address R23 while preserving its factual behavior list. Add the v2 user-visible fixes without workflow jargon. Keep prior historical receipts and review evidence intact.

Receipt/map sequence (the generator writes only the map, not the receipt):
1. Commit the final README/CHANGELOG and all product changes; record that full 40-hex package revision.
2. Run the named task-scoped verification against those exact package bytes and record actual commands, exits, counts, model/commit evidence and changed-file hashes. Do not manufacture a pass or copy old counts into a new receipt. Preserve the prior receipt as historical evidence in the existing representation. Author the new receipt fields and task records explicitly, with package_revision set to the tested commit.
3. Run the existing generator: python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json
4. Run the same command with --check, then the named provenance tests. The map reads receipt data and hashes; it does not create task receipts or run verification. Commit receipt/map/report evidence without changing the tested package bytes.
5. Confirm git cat-file -e <package_revision>:plugins/autopilot/README.md succeeds and all recorded hashes match. Explain the resolved v2 defects and remaining AP18 red tests in the new recovery report using actual evidence.

Do not rerun the full suite per task; the final integration gate below runs once after all tasks. If the full gate later adds evidence to the receipt, regenerate/check the map and commit that evidence while preserving the already-tested package bytes and its revision.


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
- R7 uses one probe with existing Git safety settings intact; it refuses unclassified errors and accepts only the anchored benign non-repository diagnostic.
- Reuse `_pinned_parent_fd`/`_descend`, but make `_open_log_sink` acquisition non-destructive until spawn succeeds. Its old unlink/recreate implementation violates the PRD when moved before Popen unchanged.
- `review_stage._context_file`'s `variant` parameter already supports a
  restricted kind set; T1's R9 fix reuses it exactly as designed — only the
  `shared` variable that feeds it was wrong.
- `verification._execute`'s existing `except BaseException: _kill(proc);
  raise` cleanup is reused unchanged inside the new sink-then-spawn
  ordering; its pipe-close `finally` is reused with one addition (each
  close now individually guarded against `OSError`, per dispatch 3's
  finding below).

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

- **R2's fail-closed sink-then-spawn ordering creates an empty log file on
  a `spawn-failed` return**, where the old ordering left nothing on disk
  (the sink now opens before `Popen` is attempted). Accepted: the file is
  empty only when absent beforehand. Existing log and artifact bytes must survive a failed spawn exactly; validate without changing bytes and clear only after successful spawn.
- **R7's fix must not refuse every destination outside a git repository,
  nor accept every destination it cannot classify.** `ancestor` reaching
  this probe already means the destination is outside the caller's own
  project tree; a destination that is *also* outside any git repository at
  all is ordinary and must still be accepted. The fix positively identifies
  only that one benign case (`fatal: not a git repository` in stderr) and
  fails closed on everything else, including failure modes this doc never
  reproduced (an ownership/`safe.directory` error, for example) — a
  negative check ("accept unless it mentions `safe.bareRepository`") would
  have silently accepted exactly that unenumerated case.
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

Dispatch 1 used a fresh native Claude subagent (`general-purpose`), isolated
from this design's authoring context — it received the design doc only, no
PRD, no prior review file.

dispatch 1 (claude): cardinal-sin 0, blocker 3, non-blocker 2, question 2

- Resolved blocker: R7's `_is_inside_git_dir` fix as first drafted refused
  every probe failure, including the ordinary case of a destination
  outside any git repository at all (nonzero exit with "not a git
  repository", not a `safe.bareRepository` complaint). Now distinguishes by
  stderr content: only the ambiguous bare-repo case fails closed.
- Resolved blocker: confirmed `_open_log_sink` is a plain function (not a
  `@contextmanager` generator) by reading its body, so the try/except
  around the call does catch the open-time failure as intended; no change
  needed there, but added an explicit sink-write-failure branch (new
  `except OSError` clause before `except BaseException`) because the
  existing re-raise would otherwise still let a write failure DURING drain
  escape as a traceback, contradicting the Test strategy's own
  "controlled failure, not a traceback" requirement for that case.
- Resolved blocker: `except BaseException: _kill(proc); raise` and the
  write-failure test-strategy line were inconsistent as first drafted;
  resolved by the same `except OSError` branch above.
- Non-blocker addressed: the reorder's side effect (an empty log file left
  behind on `spawn-failed`, where none existed before) is now named in
  Risks & edge cases as an accepted tradeoff.
- Non-blocker addressed: `_missing_prd_grant`'s job iteration now sorts the
  intersection so the refused job name in a dual-omission case is
  deterministic.
- Question addressed: an explicit test-naming convention (T1 names contain
  `staging`, T2 names never do) is now stated under Module placement so
  the `-k staging` filter partition is not left to implementor guesswork.
- Question noted, not changed: T4's commit-ordering dependency stays a
  documented manual check (the task's own exit criteria command output),
  not a scripted gate — in scope for this PRD's four named tasks, adding
  a new automated ordering check would be scope the PRD does not ask for.

Dispatch 2 ran as a direct background `codex` CLI call (mandatory
cross-model dispatch), read-only sandbox, isolated from this design's
authoring context — it received the design doc only.

dispatch 2 (codex): cardinal-sin 0, blocker 2, non-blocker 2, question 1

- Resolved blocker: `_is_inside_git_dir`'s "not `safe.bareRepository`"
  check as drafted was a negative test that silently accepted every OTHER
  unclassified git failure (e.g. a `safe.directory` ownership error),
  not only the genuinely benign "no repository here" case. Inverted to a
  positive check on git's fixed `fatal: not a git repository` message;
  everything else now fails closed, retried once, same as the
  `safe.bareRepository` case.
- Resolved blocker: `with sink_cm as sink:` let a close-time `OSError`
  (from the sink's `__exit__`) override an already-decided
  `spawn-failed`/`sink-write-failed` return, since `__exit__` runs during
  unwinding of any `return` inside the `with` block. Restructured into a
  `_run_against_sink` helper that returns a plain result dict, with the
  sink closed explicitly afterward in `_execute`'s `finally`; a close
  failure only overrides the result when the run otherwise looked clean,
  never when a more specific failure was already decided.
- Non-blocker addressed: `os.set_blocking(fd, True)` moved to after
  `fd` is owned by the `with os.fdopen(...)` block, so a `set_blocking`
  exception no longer leaks the raw descriptor; the inaccurate
  "partial write" rationale for restoring blocking mode is replaced with
  the correct reason (consistency; `O_NONBLOCK` is a no-op on a regular
  file per `open(2)`).
- Non-blocker addressed: T3's `tracemalloc.start()`/`stop()` now measures
  a delta against a baseline and only starts/stops tracing when it was not
  already running, so a test runner's own `PYTHONTRACEMALLOC` tracing is
  neither corrupted by an inflated peak nor disabled as a side effect.
- Question addressed: confirmed by reading `update_helper_map.py` that the
  generator copies `package_revision` from the input receipts JSON
  verbatim into `tested_package_revision` — it does not compute it from
  `HEAD`. T4's sequence now states explicitly that the task must edit the
  receipts JSON's `package_revision` field to the just-committed SHA
  before running the generator, not only commit docs first.

Dispatch 3 ran as a conditional codex verification pass (dispatch 2 found
blockers, so a third dispatch is mandatory), focused on the two
blocker-fix sections and their immediate neighbors per instruction.

dispatch 3 (codex): cardinal-sin 0, blocker 1, non-blocker 1, question 1

- Resolved blocker: `_is_inside_git_dir`'s "fatal: not a git repository" `in`
  substring check could be fooled by a bare-repo failure whose own quoted,
  path-controlled diagnostic happens to literally contain that substring
  (e.g. a repository path named to embed it), wrongly accepting that case
  as benign. Changed to `probe.stderr.strip().startswith(...)`: git's fixed
  prefix for this diagnostic always leads the message with nothing
  interpolated before it, while the bare-repo diagnostic's fixed prefix is
  the distinct string `fatal: cannot use bare repository` — anchoring to
  the start is immune to the embedding case `in` was vulnerable to.
- Non-blocker addressed: `_run_against_sink`'s pipe-close `finally`
  (`proc.stdout.close()`/`proc.stderr.close()`) was unguarded, so a close
  failure on either pipe could override an already-decided
  `sink-write-failed` result or a propagating cancellation — the same class
  of priority bug the log-sink close fix (dispatch 2) already solved one
  level up, just not yet applied here. Each close is now individually
  wrapped in `except OSError: pass`, best-effort, consistent with that
  same priority rule.
- Question noted, not changed: dispatch 3's prompt excerpted only the R7
  and R2/R3 sections (per its own verification-scope instruction) and did
  not re-show T3's `tracemalloc` fix, so the reviewer could not see it was
  already addressed by dispatch 2 — not a new gap, just an excerpt
  boundary. No doc change needed.

No cardinal sin or blocker remains open after dispatch 3. Dispatch ceiling
(3) reached.

## Coordinator correction after compiled-plan audit

The three required design dispatches remain historical evidence; this is an
author correction, not a claimed fourth reviewer pass. The compiler omitted
the PRD model floor and produced several incorrect instructions. See
autopilot/reports/00013-v2-self-debug.md for exact observed evidence.

- All task tiers are Opus/floor and Qwen-ineligible, matching the PRD.
- T1 has no command-scoped Git safety override; the redundant retry is removed.
- T1's regression command has no global -k filter, which deselected 85 of 87 existing tests.
- T3 uses a fresh child-local trace; historical-peak subtraction falsely accepted a 1.6 MB allocation with zero reported growth.
- T4 authors receipts and generates only the map, preserves historical receipt data, corrects Unreleased jargon, and does not claim to fix an already-resolved historical CI pin.

Product implementation, scoped tests and the fresh complete review remain required.

## Coordinator contract correction — 2026-11-03 task 2

Coordinator correction, 2026-11-03: PRD F2 and New sink cases outrank the earlier compiled design's destructive spawn-failure side effect. Preserve accepted task 1 and committed task 2 draft eccf5c6. Resume task 2 with fresh isolated Opus Tess from requirements only: add nonempty pre-existing log and artifact cases for missing and non-executable programs, assert exact bytes unchanged on spawn-failed, and retain a successful-run control proving old log bytes are replaced rather than appended. A previously absent log may remain empty. Update fault-injection wrappers only as necessary to retain real descriptor behavior. Legacy early unsafe-artifact-path refusal remains valid for aliases rejected before sink acquisition; sink-failed describes acquisition errors. Preserve existing safety assertions. Devon ef85cc76 was interrupted by the coordinator before any product mutation or verdict. After correction quality/style gates and test commit, run one complete fresh isolated Opus Devon pass, its one permitted strengthening pass if needed, actual red verification, Opus Ivan and all later gates including Pat. Do not reuse stale tess-2/ivan-2 scratch contracts. No completed task, cap or review counter is reset.

This is a PRD-conformance correction, not another clean design-review verdict. The three earlier reviews remain historical. Full implementation verification and fresh completion review remain mandatory. Evidence: ../autopilot/reports/00013-v2-task2-contract-correction.md.

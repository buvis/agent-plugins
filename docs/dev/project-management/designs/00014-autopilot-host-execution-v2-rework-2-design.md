# Design: AP00014 v2 rework, review cycle 2

Source review: docs/dev/project-management/reviews/00014-autopilot-host-execution-v2-review-2.md (head_sha 949af1a01ada89b05cdb2a9c295d68db25810c88)

The five 🔴 Critical rows this design closes, verbatim from that review's
`## Consolidated Findings`:

- **R4** [2/4] — The R11 fix makes every controller-keyed duty refuse with
  `missing_controller_seam` when the session is unbound. The change removed the
  unbound-skip in `evaluate_hook` and made `_evaluate_duty_call` refuse when
  `not bound or seam is None`. Design §8 (design lines 760-761) says unbound
  sessions skip these duties. Design line 1239 says "Unbound projects see only
  the local pure duties". Once activated, the hooks would deny every `git push`
  in any repo without `.autopilot/controller`. (`plugins/autopilot/scripts/interception.py:154`)
- **R9** [1/4] — The rework leaves the gate red: 14 failed, 1869 passed at HEAD.
  The prior cycle was 1848 passed, 0 failed, so all 14 failures are regressions
  from the rework. (`N/A`)
- **R10** [1/4] — Phase 2 task 3 is unmet. The suite at HEAD has 14 failures and
  `test_new_helper_files_are_owned_and_digested_from_current_bytes` still fails,
  which was the open CRITICAL R1 from v1. The cause is
  `plugins/autopilot/README.md`: the source-map digest is `3ce9d328...`, the
  current bytes hash to `ca110114...`. (`plugins/autopilot/README.md`)
- **R11** [1/4] — The shipped hooks deny unrelated work in every project. Every
  controller-keyed duty refuses when the session is unbound or has no seam, with
  no check that autopilot is involved. (`plugins/autopilot/scripts/interception.py:156`)
- **R12** [1/4] — The live host probe cannot observe interception, because the
  real guard denies the unbound control push. Five tests report
  `control_did_not_execute` where they expect `observed`.
  (`tools/autopilot/probe-host.py:156`)

## Architecture fit

Prior fix: the cycle-1 rework ran as tasks 14-17 over
`a133498261a65eed36ce0d9516770626c7955b2a..949af1a01ada89b05cdb2a9c295d68db25810c88`
(15 commits; `plugins/autopilot/scripts/` 52+/40- in `jobs.py`, 46+/10- in
`guards.py`, 28+/3- in `claude.py`, 8+/9- in `interception.py`, 6+/1- in
`autopilot.py`; `tools/autopilot/probe-host.py` 66+/2-;
`tests/autopilot/test_interception.py` 210+/21-; plus a 1051-line
`tools/autopilot/source-map.json` digest reconciliation). It closed eleven
cycle-1 findings genuinely (R1, R2/R14, R5, R6, R9/R17, R19, R20, R23, R25, R26,
and R3 for the common push spellings) and broke the suite from
`1848 passed, 0 failed` to `1869 passed, 14 failed`.

Four of this cycle's five 🔴 rows were **introduced by that fix**; one was
**only exposed** by it:

- **Introduced.** R4 and R11 are one defect. Cycle-1's Blake R11 said
  controller-keyed guards were "skipped entirely when no `.autopilot/controller`
  directory is found". The fix read that as "never skip" and made
  `_evaluate_duty_call` refuse on `not bound or seam is None`
  (`interception.py:156-161`), dropping the `skipped` population entirely
  (`evaluate_hook`'s `skipped` list is now initialised and returned empty,
  `interception.py:192` and `:210`). That contradicts the main design, which is
  explicit at lines 760-763: "Unbound: stateful duties and duties with
  controller-bound keys are skipped with `"unbound"`; local pure duties run.
  Bound: every call runs; ... with `seam is None` each such duty returns
  `GuardOutcome(allowed=False, reason="missing_controller_seam", ...)`." The two
  conditions were conflated into one.
- **Introduced.** R12 is the same defect seen through the probe. `probe-host.py`
  requires the unbound `control/` push to reach the remote, and the real hook now
  refuses any unbound push, so `observed` can never be reached for interception.
  No separate probe defect is implied: fixing R4/R11 restores the probe's
  premise.
- **Introduced.** R9 is the aggregate. Its five named causes are the unbound
  refusal (4 probe tests), the `_resolve_roles` gemini override (4 tests, 9
  subtests), `guards._normalize_rel`'s `while True` (1 test), the un-re-sealed
  README digest (4 tests), and `test_local_boundary.py`'s stale `OPERATIONS` set
  (1 test). All five entered with the cycle-1 fix.
- **Exposed, not introduced.** R10 is cycle-1's own CRITICAL R1 re-surfacing:
  `plugins/autopilot/README.md` was edited by commit `30fb2c2` *after*
  `tools/autopilot/source-map.json` was reconciled by `d718cfc`/`24f75e1`, so the
  map's `destination_blob_sha256` (`3ce9d328...`) no longer matches the file's
  bytes (`ca110114...`), and the AP00014 host receipts still pin
  `package_revision: d6f014f95d510d3714f6e6351919989320ccfd63`, a commit whose
  README bytes differ from the current ones. The provenance chain is a
  *sequencing* contract, and the cycle-1 rework violated the sequence rather than
  the content.

The work lands in the existing layers only: `plugins/autopilot/scripts/`
(the pure-duty and interception layer), `tools/autopilot/` (the probe and
provenance tooling), and `tests/autopilot/`. No new module, no new layer.

## Module placement

Edits to existing files only. No new files.

- `plugins/autopilot/scripts/interception.py` — split the conflated condition in
  `_evaluate_duty_call`; repopulate `skipped` in `evaluate_hook`.
- `plugins/autopilot/scripts/autopilot.py` — delete the `_resolve_roles` gemini
  override; add `"hook-v1"` nothing (already present, see R7/R31: the test is
  what is stale).
- `plugins/autopilot/scripts/guards.py` — replace `_normalize_rel`'s `while True`
  with a bounded walk.
- `tools/autopilot/probe-host.py` — `shlex`-quote the record-session command and
  give it an explicit instruction (R21); no change is needed for R12 beyond the
  interception fix.
- `tests/autopilot/test_interception.py` — the cycle-1 rework rewrote
  `test_interception.py:127-182` and `:870-886` to pin the refuse-when-unbound
  behavior. Those assertions are the regression; they must be rewritten to pin
  the skip, not deleted wholesale.
- `tests/autopilot/test_local_boundary.py` — add `"hook-v1"` to `OPERATIONS`.
- `tests/autopilot/test_facade_session_roles.py` — no change: these four tests
  are correct and the code is wrong.
- `docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json`
  and `tools/autopilot/source-map.json` — re-sealed last, see the contract below.

## Interfaces & contracts

Closes: R4, R11, R12 — `plugins/autopilot/scripts/interception.py`

```python
def _evaluate_duty_call(
    call: DutyCall,
    *,
    bound: bool,
    session: NativeSession | None,
    project_root: str,
    seam: ControllerSeam | None,
) -> tuple[GuardOutcome | None, dict, str | None]:
    """The outcome for one duty call, the context it decided from, and the skip
    reason when the call was skipped.

    Returns `(None, context, "unbound")` for a controller-keyed duty in an
    unbound project: the duty did not run and nothing is refused.
    Returns `(GuardOutcome(duty=duty, allowed=False,
    reason="missing_controller_seam", stateful=True), context, None)` for a
    controller-keyed duty in a BOUND project with `seam is None`.
    Returns `(outcome, context, None)` otherwise.
    """
```

The two conditions are separate and must not be merged again:

- `controller_keyed and not bound` → **skip**, reason string exactly `"unbound"`.
- `controller_keyed and bound and seam is None` → **refuse**, reason string
  exactly `"missing_controller_seam"`.
- `controller_keyed` is unchanged: `duty in _STATEFUL_DUTIES or duty in _FACTS_SCHEMA`.

```python
def evaluate_hook(
    host_id: str,
    event: str,
    payload: Mapping[str, object],
    *,
    env: Mapping[str, str],
    seam: ControllerSeam | None,
) -> HookDecision
```

`evaluate_hook` collects the skips. **The loop body is part of this contract**,
because the existing body dereferences the outcome unconditionally
(`interception.py:200`) and `CONTEXT_REINJECTION` is itself controller-keyed
(`_FACTS_SCHEMA`, `interception.py:41-49`) and is the duty `SessionStart` emits
(`codex.translate_shared_hook`, `codex.py:112-113`, which `claude.py:123`
delegates to). Write it exactly so:

```python
    for call in duty_calls:
        outcome, decided_context, skip_reason = _evaluate_duty_call(
            call, bound=bound, session=session, project_root=project_root, seam=seam
        )
        if skip_reason is not None:
            skipped.append((call.duty.value, skip_reason))
            continue
        outcomes.append(outcome)
        if call.duty is GuardDuty.CONTEXT_REINJECTION and outcome.allowed:
            additional_context = decided_context.get("contract_card_body")
```

The `continue` is load-bearing: without it an unbound `SessionStart` reads
`outcome.allowed` on `None`, raises `AttributeError`, and `run_hook` swallows it
into `_invalid_input_reply` (`interception.py:259-260`), so the hook answers
`autopilot: hook_input_invalid` instead of a clean allow — the same class of
defect R11 reports. `HookDecision.skipped` keeps its declared type
`tuple[tuple[str, str], ...]` (main design line 737, `(duty, "unbound" |
"not_applicable_on_host")`). `allowed` stays
`all(outcome.allowed for outcome in outcomes)`, which is `True` when every
controller-keyed duty was skipped and no pure duty refused — that is the whole
point: an unbound, unrelated project sees only its local pure duties.

Closes: R9 (cause 2) — `plugins/autopilot/scripts/autopilot.py`

Delete these four lines from `_resolve_roles` (currently
`autopilot.py:293-296`), comment included:

```python
    # Gemini role eve is resolvable for the full lane of codex-gemini, the
    # same way --diagnose lists it unconditionally for that profile.
    if args.profile == "codex-gemini" and args.lane == "full":
        facts = replace(facts, gemini_cli_available=True)
```

`_resolve_roles` must pass the caller's `facts` through unchanged: the default
`ProfileFacts(gemini_cli_available=False, doubt_reviewer=None,
implementor_codex_present=False)` when `--facts` is absent, else exactly the
validated body of the `--facts` file. Inventing a host-availability fact is
forbidden; `roles.resolve_profile` receives `observed=None` as today. If the
`replace` import becomes unused, remove it.

Closes: R9 (cause 3) — `plugins/autopilot/scripts/guards.py`

```python
def _normalize_rel(path: str, project_root: str | None) -> str:
```

Same signature, same return contract, no `while True`. **This block replaces
`guards.py:163-174` only**: the `if not isinstance(project_root, str) or not
project_root: return path` guard at `guards.py:161-162` stays, because
`project_root` reaches here from an untrusted hook payload (`claude.py:107`
reads `payload.get("cwd")`) and `posixpath.normpath(None)` raises `TypeError`.
Walk a bounded sequence of candidate roots instead:

```python
    norm = posixpath.normpath(path)
    root = posixpath.normpath(project_root)
    parents = [str(parent) for parent in PurePosixPath(root).parents]
    candidates = [root, *(p for p in parents if p != "."), ""]
    for candidate in candidates:
        if norm == candidate:
            return ""
        prefix = candidate.rstrip("/") + "/"
        if norm.startswith(prefix):
            return norm[len(prefix):]
    return path
```

The trailing `""` candidate is load-bearing and must not be dropped as dead
weight. It reproduces the terminal empty root the `posixpath.dirname` walk
reached for a RELATIVE `project_root` (`posixpath.dirname("rel") == ""`, whose
next prefix is `"/"`), which is how the current body honours its own docstring:
"an unrelated absolute path still loses its leading slash so the whole-path
store scan still runs on it". Measured against both bodies:
`path="/x/docs/a.md", project_root="rel"` → current `x/docs/a.md`, a candidate
list without `""` → `/x/docs/a.md`. That difference is a security weakening, not
a cosmetic one: `_store_path_verdict` (`guards.py:177-184`) tests
`parts[0] in _LIFECYCLE_DIRS`, so `"/wip/x.md"` under a relative root denies
today and would be ALLOWED without the `""` candidate, and the same weakening
reaches the command-token path at `guards.py:236-239`. Absolute roots and
`root == "/"` behave identically in both bodies.

The `p != "."` filter is equally load-bearing, and for the symmetric reason:
`PurePosixPath("rel").parents` yields a synthetic `.` that the
`posixpath.dirname` walk never visits (it goes `"rel"` → `""`). Keeping it
diverges on a `path` that normalises to `.`: measured
`path="a/..", project_root="rel"` → current `a/..`, unfiltered candidates `""`.
The filter does not lose a genuine `.` root, because `root` itself is the first
candidate: `path=".", project_root="."` returns `""` either way. With both the
`""` candidate and this filter, the two bodies agree on every case measured —
`("a/..", "rel")`, `("/x/docs/a.md", "rel")`, `("/wip/x.md", "rel")`,
`("/r/backlog/x.md", "/r")`, `("/r/backlog/x.md", "/r/sub")`,
`("/r//backlog/x.md", "/r")`, `("a/b", ".")`, `(".", ".")`, `("/a", "/")` and
`("x/y", "rel")`. Those ten pairs are the equivalence test.

`test_compatibility.py::NoCoordinatorRuntimeInPluginTest::test_no_ap00014_module_file_contains_a_coordinator_runtime_pattern`
scans `guards.py` for coordinator-runtime patterns, `while True` among them, and
is the gate on this. `interception.find_binding`'s own `while True`
(`interception.py:90`) is **out of scope for this cycle**: that file is not in
`NEW_MODULE_FILES`, the test does not scan it, and Blake's R30 naming it is a
🟡 single-voice row the gate discarded.

Closes: R9 (cause 5) — `tests/autopilot/test_local_boundary.py`

Add `"hook-v1"` to the `OPERATIONS` set at `test_local_boundary.py:33-39`.
`_CAPABILITIES` (`autopilot.py:24-32`) already advertises 19 ids: the 3 `LEGACY`
plus 16 operations, and the test's set holds 15. The test asserts
`set(ids[3:]) == OPERATIONS`, so position does not matter. The implementation is
correct here and the expectation is stale; do not remove `"hook-v1"` from
`_CAPABILITIES`.

Closes: R10, and R9 (cause 4) — the provenance re-seal, **last step of this cycle**

This is a sequencing contract, not a content change. In this exact order, after
every other fix above is committed and the suite is green except for the four
digest tests:

1. Commit the final bytes of every path listed in
   `docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json`
   (`.paths`, 18 entries, `plugins/autopilot/README.md` among them). No later
   commit in this cycle may touch any of those paths.
2. Set that file's `package_revision` to the full 40-hex sha of that commit.
   `helper_map_successor.verify_listed_paths_match_revision(root, revision, paths)`
   runs `git show <revision>:<path>` for every listed path and refuses when the
   committed bytes differ from the current bytes, with
   `successor package_revision <revision> is stale for '<path>'`.
3. Regenerate the map:
   `python3 tools/autopilot/update_helper_map.py --map tools/autopilot/source-map.json`
   (the `--receipts`, `--successor-receipts` and `--host-receipts` paths all
   default from the root). Then prove it with
   `python3 tools/autopilot/update_helper_map.py --map tools/autopilot/source-map.json --check`,
   which must exit 0.
4. Commit the regenerated `source-map.json` and the receipts together.

The four tests this closes are
`test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes`,
`test_helper_provenance_real.py::test_generator_check_accepts_the_committed_map`,
`test_package.py::TargetPackageTest::test_content_roster_matches_frozen_inventory_and_actual_package_bytes`,
and `test_package.py::TargetPackageTest::test_readme_retains_every_source_heading_with_completed_adaptation_receipts`.
No exemption, no hand-edited digest: the digests come from the generator.

Closes: R9 (the aggregate) — the exit criterion

`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`
exits 0 with `0 failed`, and `python3 scripts/validate.py` exits 0. A cycle that
leaves any of the 14 named failures red has not closed R9.

## Data flow

One hook invocation, unchanged in shape, corrected in one branch:

`run_hook(host_id, event, stdin, env=...)` → `_parse_hook_input` → `evaluate_hook`
→ `hosts.adapter(host_id).translate_hook(event, payload)` yields `DutyCall`s →
`find_binding(cwd)` decides `bound` and `project_root` → per call,
`_evaluate_duty_call` now routes three ways instead of two: **skip** (unbound,
controller-keyed; recorded in `HookDecision.skipped`, contributes no outcome),
**refuse** (bound, controller-keyed, `seam is None`), or **run**
(`guards.run_guard`) → `HookDecision.allowed` is the conjunction of the outcomes
that exist → `adapter.render_hook_reply` → `_write_trace`.

In the probe, `probe-host.py`'s unbound `control/` run therefore reaches
`git push` with no controller-keyed duty refusing it, the push lands on the
probe remote, and `observed` becomes reachable for interception again. The bound
`project/` run still refuses, which is what the probe compares against.

## Reuse inventory

- `shlex.quote` — already imported and used in
  `plugins/autopilot/scripts/jobs.py:16,470-471` to build the child bind command.
  Reuse it for `probe-host.py`'s record-session command (R21). Do not add a
  local quoting helper. Greps run: `rg -n 'import shlex|shlex\.' plugins/autopilot/scripts/ tools/autopilot/`.
- `posixpath.normpath` plus `pathlib.PurePosixPath.parents` — stdlib, already the
  idiom `guards.py` uses for path handling (`posixpath` imported there). No new
  dependency, no new helper. Greps run: `rg -n 'parents' plugins/autopilot/scripts/guards.py`
  (nothing found, so the bounded walk is new code in that file, built from
  stdlib).
- `tools/autopilot/update_helper_map.py` (`main`, `--map`, `--check`) and
  `tools/autopilot/helper_map_successor.py`
  (`verify_listed_paths_match_revision`) — the existing re-seal path. The
  re-seal writes no digest by hand; it runs these. Greps run:
  `rg -n 'package_revision' tools/autopilot/helper_map_successor.py tools/autopilot/update_helper_map.py`.
- `HookDecision.skipped` and its `(duty, reason)` tuple type already exist
  (main design line 737; the field is still declared and returned, just always
  empty). The fix repopulates an existing field rather than adding one.
- `~/.claude/rules-library/rationalizations.md` was not read for this sweep (the
  sweep is scoped to three named symbols in a rework, not to a new capability),
  so the synonym sets above are the author's own: skip/bypass/ignore,
  refuse/deny/block, quote/escape/shlex, seal/digest/provenance.

## Alternatives considered

1. **Smallest diff: restore the unbound skip only** (R4, R11, R12), and leave
   the other four R9 causes to the 🟠 rows' own fix tasks. Rejected as the
   *design* scope but adopted as the *task* scope: R9 is an aggregate row whose
   acceptance criterion is a green gate, so a design that closes only three of
   its five causes cannot close it. The contract above therefore names all five
   causes while keeping each fix minimal — four of them are a deletion, a
   bounded loop, a set entry and a re-sealing sequence.
2. **Accept the refuse-when-unbound behavior and change the design instead**
   (that is, ratify cycle-1's reading of Blake's R11). Rejected: it makes the
   shipped hooks deny `git push`, every `Edit` and every `Stop` in any
   repository without `.autopilot/controller`, which Blake demonstrated by
   running the CLI against an unbound `/tmp` repo. The main design states the
   opposite rule twice (lines 760-763 and 1239). Changing a two-place design
   invariant to match a regression is the cardinal sin this review exists to
   catch. If the stricter behavior is ever wanted, it needs its own PRD and a
   bound-only scope.
3. **Fix the probe instead of the guard** (R12 alone): let `probe-host.py` treat
   a refused unbound push as evidence of interception. Rejected: it would record
   `observed` for a product behavior that is itself the defect, and the four
   non-probe failures would stay red. The probe is a measuring instrument; it
   must not be recalibrated to make a regression look like a pass.
4. **Hand-edit the four stale digests** rather than re-running the generator
   (R10). Rejected outright: the digests exist to prove the bytes were sealed by
   a tool, and `--check` would fail the next time anyone ran it. Bob's own row
   says "regenerate the map without exemptions".

The extra size over option 1 buys the only acceptance criterion R9 has: a green
gate.

## Risks & edge cases

- **The skip must not become a silent hole.** An unbound project now runs only
  pure duties, so a test must assert both halves: the skip is *recorded* in
  `HookDecision.skipped` with reason `"unbound"`, and `allowed` is `True` only
  because no pure duty refused. A test that asserts `allowed is True` alone
  would pass against a version that dropped the duty entirely.
- **`test_interception.py:127-182` and `:870-886` were rewritten by cycle 1 to
  pin the regression.** Rewriting them back must not quietly delete the
  bound-with-no-seam coverage that lives beside them; both branches need a case.
  Rule: fix the implementation, not the test — but here the test encodes the
  wrong contract, so say so explicitly in the commit.
- **Re-seal ordering is fragile by construction.** Any later commit touching one
  of the 18 receipt paths re-stales `package_revision`. The two likely next
  changes after this PRD — the hook-activation/publication PRD (which will edit
  `plugin.json`, `README.md` and `contracts/hosts.json`) and the remaining 🟠
  probe work (which edits `probe-host.py`, not a listed path) — both collide with
  this. This design boxes them in: each must end with the same re-seal step. A
  follow-up worth considering is a pre-commit or CI check running
  `update_helper_map.py --check`, so staleness is caught at the commit that
  causes it rather than a review cycle later.
- **A third likely next change** is passing the binding root and hook `env` into
  `translate_hook` (cycle-2 rows R17 and R26, both 🟠/🟡). That will touch
  `_evaluate_duty_call`'s signature again. The three-way return above is
  deliberately a tuple rather than a richer type so that change stays additive.
- **`PurePosixPath(root).parents` on a relative root** yields `.` as its last
  element; `posixpath.normpath` of a relative `project_root` has no leading
  slash, so the `.`-prefix branch cannot match a normalised absolute `path` and
  the function falls through to `return path`, which is the documented
  unrelated-path behavior. Cover a relative `project_root` explicitly.
- **`allowed` with an empty `outcomes` tuple** is `all(()) is True`. An event
  whose every duty is controller-keyed and unbound (Blake's `Stop` case) is
  therefore allowed with three recorded skips. That is correct and is the
  behavior Blake's R11 evidence demands, but it deserves its own assertion so a
  future refactor cannot flip it to a refusal by accident.

## Test strategy outline

- **Unbound skip** (R4, R11): one test per controller-keyed duty class asserting
  `("<duty>", "unbound")` is in `HookDecision.skipped`, no outcome was produced
  for it, and `allowed is True`. Run it through `run_hook` (the real CLI path,
  `seam=None`) for `PreToolUse` with a `Bash` `git push` payload, for a `Skill`
  payload naming a non-autopilot skill, and for `Stop` — the three cases Blake
  reproduced. Each must fail against the current code.
- **Unbound `SessionStart`** (the `continue` in the loop-body contract): run
  `run_hook` for `SessionStart` in an unbound project and assert the reply is the
  clean one, NOT `autopilot: hook_input_invalid`, and that
  `("context_reinjection", "unbound")` is in `skipped`. Without the `continue`
  this is an `AttributeError` that `run_hook` converts into
  `hook_input_invalid` (`interception.py:200`, `:259-260`), so this case is the
  only one that pins the `continue` itself.
- **Bound refusal kept** (regression guard): same duties, a project with a real
  `.autopilot/controller` directory and `seam=None`, asserting
  `reason == "missing_controller_seam"` and `allowed is False`. This is the
  coverage that must survive the test rewrite.
- **Pure duties still run unbound**: a document-location violation in an unbound
  project is still denied, proving the fix did not disable enforcement wholesale.
- **Probe** (R12): the five named tests — `test_probe_control_is_unbound_inside_a_bound_source_repo`,
  `test_relocated_host_probe_observes_identity_isolation_interception`, and the
  three in `test_host_argv_failed_runs.py` — go green with no change to their
  expectations. They are the acceptance test for R12; do not relax them.
- **Role resolution** (R9 cause 2): the four existing
  `test_facade_session_roles.py` tests go green unchanged, including
  `test_resolve_roles_reports_blocked_when_a_host_lacks_a_required_capability`,
  whose `assertGreater(len(roles_on), len(roles_off))` is what catches an
  invented fact.
- **Bounded normalisation** (R9 cause 3): there are **no** direct
  `_normalize_rel` tests today (`rg -l normalize_rel tests/` finds nothing), so
  "keep the existing cases green" would be vacuous. Write a direct unit test on
  `_normalize_rel` covering an absolute root, a sub-cwd root, a double slash, a
  sibling absolute path and a **relative** `project_root`, plus a
  `document_location` case with a relative `project_root` and a `wip/` path
  asserting the deny survives. Then let
  `test_no_ap00014_module_file_contains_a_coordinator_runtime_pattern` gate the
  loop shape.
- **Capability list** (R9 cause 5): `test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations`
  goes green with `"hook-v1"` added to `OPERATIONS`.
- **Provenance** (R10): `update_helper_map.py --check` exits 0, and the four
  digest tests go green. These run last, after the re-seal commit.
- **Full gate** (R9): the PRD exit criterion, green, with the count recorded.

## Review log

### Dispatch 1 (claude)

Both blockers were fixed in the doc before dispatch 2.

- **blocker (fixed)** — The three-way return made `evaluate_hook` dereference a
  `None` outcome on `SessionStart`: `CONTEXT_REINJECTION` is controller-keyed, so
  it is skipped when unbound, and the existing loop body reads `outcome.allowed`
  at `interception.py:200`. `run_hook` swallows the `AttributeError` into
  `hook_input_invalid`. Fixed by making the loop body part of the contract, with
  an explicit `continue` on a skip.
- **blocker (fixed)** — The `_normalize_rel` replacement silently weakened the
  guard for a relative `project_root`: measured `path="/x/docs/a.md",
  project_root="rel"` → current `x/docs/a.md`, proposed `/x/docs/a.md`, which
  turns a `wip/` deny into an allow at `guards.py:177-184` and `:236-239`.
  Fixed by appending the `""` candidate and documenting why it is load-bearing;
  the `guards.py:161-162` type guard is now stated as retained.

Non-blockers and questions, recorded and deliberately not fixed:

- **non-blocker** — The probe test strategy names five failing tests; only four
  fail. `test_relocated_host_probe_kills_a_host_that_outlives_the_timeout`
  (`test_host_argv_failed_runs.py:59`) passes today. The two that fail there are
  `..._never_turns_a_failed_run_into_observation` and
  `..._derives_isolation_and_interception_from_the_trace`.
- **non-blocker** — The fact-invention gate is misattributed: the
  `assertGreater(len(roles_on), len(roles_off))` assertion lives in
  `test_resolve_roles_defaults_equal_all_false_facts`
  (`test_facade_session_roles.py:141`), not in
  `test_resolve_roles_reports_blocked_when_a_host_lacks_a_required_capability`.
- **non-blocker** — The restored skip is invisible in the trace: `_trace_line`
  (`interception.py:283-296`) emits `outcomes` only and has no `skipped` key, so
  an operator cannot tell "skipped as unbound" from "no such duty emitted" —
  the ambiguity that let the cycle-1 regression ship. Worth a follow-up.
- **non-blocker** — The re-seal sequence has no abort path (a failed step-3
  `--check` leaves a stale `package_revision` committed; the recovery is to
  revert the step-2 commit, never to hand-edit), and the doc does not say
  whether a `CHANGELOG.md` entry is owed — `plugins/autopilot/CHANGELOG.md` is
  one of the 18 sealed paths, so a changelog edit after step 1 re-stales the
  digest.
- **non-blocker** — Two editorial defects: the `## Module placement`
  `autopilot.py` bullet is garbled (the real instruction is the R9-cause-5
  contract), and that section folds R21's `shlex.quote` work into this design
  although R21 is a 🟠 row outside the five CRITICALs, and
  `tools/autopilot/probe-host.py` is not a sealed path.
- **question** — `"not_applicable_on_host"` is a declared `skipped` reason with
  no producer anywhere; this cycle emits `"unbound"` only and the other value
  stays reserved.
- **question** — (resolved by the blocker-2 fix) whether the `_normalize_rel`
  block replaced the `project_root` validity guard; it does not.

dispatch 1 (claude): cardinal-sin 0, blocker 2, non-blocker 5, question 2

### Dispatch 2 (codex)

- **blocker (fixed)** — The bounded walk still diverged from the current body on
  a `path` that normalises to `.`: `PurePosixPath("rel").parents` yields a
  synthetic `.` that the `posixpath.dirname` walk never visits, so
  `path="a/..", project_root="rel"` returned `""` where the current body returns
  `a/..`. Fixed by filtering `p != "."` out of the candidate list and recording
  the ten measured equivalence pairs in the contract.
- **non-blocker (fixed as part of blocker 1's own suggested fix)** — The test
  strategy named `PreToolUse`, `Skill` and `Stop` but not the unbound
  `SessionStart` case, which is the only one that pins the `continue`. A
  dedicated bullet was added.

**Engagement.** Dispatch 2 returned two findings, which trips the
minimum-engagement check (fewer than three). Its one-per-dispatch engagement
re-run was dispatched with a sharpened prompt naming six surfaces to inspect;
codex exited 0 but emitted no answer text at all, so the re-run produced no
evidence of engagement. Dispatch 2 is therefore marked **weak**. This is
advisory: both of its findings were specific, section-anchored and correct, and
both were fixed.

dispatch 2 (codex): cardinal-sin 0, blocker 1, non-blocker 1, question 0 weak

### Dispatch 3 (codex)

Verification pass, run because dispatch 2 found a blocker.

- `verdict: blocker-1 closed` — "the skip branch executes `continue` before
  either dereference of `outcome`. `(call.duty.value, skip_reason)` matches the
  declared `(str, str)` element type. `allowed=all(...)` correctly excludes
  skipped duties and returns `True` when no duties produce outcomes. A bound
  duty with no seam still produces a denying outcome."
- `verdict: blocker-2 closed` — "both bodies visit the same effective
  candidates. Relative roots reach `""`; the new implementation excludes the
  `"."` ancestor that `posixpath.dirname` does not visit. Absolute roots
  terminate at `/` or `//`; the new trailing `""` adds no match because its
  prefix test duplicates theirs and normalized paths are never empty. All ten
  listed pairs agree. I checked the specified edge cases and found no differing
  pair." (It was asked about a trailing slash, `project_root="//"`, a `..` path,
  an empty `path`, and `/rootx` against `/root`.)
- `no new findings`.

Its single caveat — "compatibility with consumers omitted from the supplied text
remains unverified", i.e. a consumer requiring one outcome per duty call — was
checked here and is closed: every consumer of `HookDecision.outcomes` iterates
and filters rather than indexing or assuming length parity
(`interception.py:294`, `claude.py:130`, `codex.py:151`).

dispatch 3 (codex): cardinal-sin 0, blocker 0, non-blocker 0, question 0

result: ok

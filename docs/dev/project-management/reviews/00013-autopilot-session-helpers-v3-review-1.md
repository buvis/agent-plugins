---
prd: docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v3.md
review: 1
date: 2026-11-08
head_sha: feca0d1a519c46fd2782d1cfd29f5ba4d14ac36e
codex_thread_id: 01a1bb4c-039d-73e2-b812-7bf04cb26d94
reviewers: alice,blake,bob,carl,eve
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: available
dispatch_rows:
  bob: a2c087a4
  carl: 12e3301e
---

# Review: 00013-autopilot-session-helpers-v3

Diff range: `b786f5aa98f0b2b796666a0a410e9ae138e152b1..feca0d1a519c46fd2782d1cfd29f5ba4d14ac36e`

codex_rung_guard: not fired

## Review Summary

Reviewed: 4 completed tasks (T1-T4)
PRDs checked: 00013-autopilot-session-helpers-v3.md

### Agent Status

- Alice (consensus, Claude subagent, opus/high): available
- Blake (blind lens, Claude subagent, PRD-only, opus/high): available
- Bob (doubt lens + de-slop, codex, static-only sandbox): available
- Carl (UI/design, gemini-run backend=copilot model=gemini-3.8-flash): available (salvaged)
- Eve (doubt lens, Claude Fable 5 subagent): available

Notes on reviewer lanes, recorded loud rather than smoothed over:

- **Carl's lane exited 1**, not 0. The copilot backend hit five consecutive
  `Response was interrupted due to a server error` retries and a DNS
  `ENOTFOUND` against `api.individual.githubcopilot.com`. Despite the non-zero
  exit he published a complete, usable review: all twelve `R{n}` verdict lines
  and `[CARL] ✅ No issues found`. That output was salvaged (the same reasoning
  the skill applies to a codex exit-4 whose sidecar holds a complete review) and
  no retry was dispatched. His dispatch row was closed `ok`. One of his own
  sub-shells also failed on a missing `pyflakes` module; he worked around it
  with an AST check.
- **Bob's prompt was the inlined shape**, rebuilt to 307133 bytes over the
  9 KB staged render. His dispatch row's `prompt_bytes` therefore understates
  what codex received; the row was not re-opened by hand.
- **Consensus engine**: `legacy` (single Alice subagent). No `review-fanout`
  workflow run, so no `consensus_run_id`.
- **Engram context pack**: ok.
- **Settled-decisions ledger**: none for this PRD stem (cycle 1). The v1 and v2
  ledgers belong to earlier PRD stems and were deliberately not fed in, per the
  standing "v1/v2 holds untouched" invariant. `consolidate_findings.py` ran
  without `--ledger`/`--ledger-dismiss`, so no Blake re-raise was auto-dismissed.

### Mechanical absorption

The staged context carried two `[MECH]` lines, both from the fail-first replay
block, and no tautological-shape lines. Eve relayed both verbatim, so both
already had rows; `mech-check` was appended to their Found By and their severity
raised to the 🟡 the mechanical line states (Eve had filed them ⚪). Rows R13 and
R14 are Bob's prose about the same two computed facts as R19 and R20 - four rows,
two underlying facts. They were left unmerged rather than silently folded,
because the consolidator's own paraphrase matcher did not merge them and
rewriting its output by hand would hide that.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/5] | 🟡 | The new `os.dup` failure branch of `_write_artifact` has no test. Pat flagged this as LOW in the recovery report, and `rg` finds no `dup` fault injection in tests/autopilot. The same branch leaves an existing leaf's earlier record in place, where the v2 `_empty_pinned` emptied it. The `_close_result_sink` docstring ("`_write_artifact` already emptied it") and the CHANGELOG ("leaves no reusable artifact after a failed write or close") are therefore not true on that path. The contract keeps this behavior, but it should be tested and the wording narrowed. | plugins/autopilot/scripts/verification.py:296 | 2 | ALICE, BOB, EVE |
| R2 | [3/5] | 🟡 | The new CHANGELOG bullet fuses two clauses badly. "...and no longer read a nested repository's Git pointer: any symlink there ... is refused" makes the colon explain the nested-repo clause instead of the root-anchored rule. It also duplicates the first bullet's "leaves no reusable artifact after a failed write or close" with the new T2 bullet. Split the symlink rule into its own bullet and drop the repeated clause. | plugins/autopilot/CHANGELOG.md:1367 | 4 | ALICE, BOB, EVE |
| R3 | [3/5] | ⚪ | The failed-artifact tests moved to tests/autopilot/test_helper_recovery_v3_artifact.py. That path is not in the PRD's complete write-path list (the PRD names only test_helper_recovery_v3.py). The split is justified because test_helper_recovery_v3.py is at 799 of 800 lines. Record the deviation in the PRD or report. The PRD's Verify line for T2 (`-k failed_artifact` on the old file) no longer selects those tests. | tests/autopilot/test_helper_recovery_v3_artifact.py:1 | 2 | ALICE, BLAKE, EVE |
| R4 | [2/5] | 🟡 | The recovery report and the receipt's T4 entry record only the pre-regeneration gate at 6888765 (24 failed, 1212 passed). They say that "3 failed" provenance nodes are unresolved. The reviewed HEAD run (19 failed, 1217 passed, only the AP 00018 nodes) is recorded in neither file. The delivery evidence is stale against the final state. Record the final run, or state clearly that the final gate lives elsewhere. | docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md:773 | 4 | ALICE, EVE |
| R5 | [2/5] | 🟡 | The T3 fix covers only `_is_inside_git_dir`, as specified. Sibling Git probes on the same staging path still go through `dirty_tree._git`, which has no timeout and no OSError handling (`_resolve_roots` -> `_toplevel`, `_repo_problem`, `_tracked_problem`). If git is really missing, or one of these probes hangs, `stage_review` still raises before it reaches the guarded probe. The new tests stub only the `--is-inside-git-dir` call, so they do not exercise this. The PRD wording limits scope to `_is_inside_git_dir`, so this is a residual risk and not a spec violation. | plugins/autopilot/scripts/dirty_tree.py:19 | 3 | BLAKE, EVE |
| R6 | [2/5] | ⚪ | `refuse` calls `_root_anchor` once directly and again inside `_symlinked_component`. That is two realpath scans of the same path, and the `toplevel` parameter of `_symlinked_component` is now unused. Both follow the design contract. Passing the computed anchor in would remove the duplicate work and the dead parameter. | plugins/autopilot/scripts/log_sink_refusal.py:156 | 1 | ALICE, EVE |
| R7 | [1/5] | 🟠 | `_root_anchor` returns None for any relative path, so `--verify` with a relative `--project-root` (for example `.`) is now refused with `unsafe-artifact-path`. The pre-change code (b786f5a) accepted it. README.md:263 documents `--project-root PATH` with no absolute-path requirement, and the CLI passes `Path(args.project_root)` through unchanged (plugins/autopilot/scripts/autopilot.py:171). `run_verification` builds `root / artifact_path` (plugins/autopilot/scripts/verification.py:469), which stays relative. Reproduced from the repo root: `_root_anchor(Path('docs/dev/tmp/x.log'), Path('.'))` returns None, and `refuse` returns "is a symlink" for it, but None for the absolute spelling. No test covers a relative root, and the CHANGELOG does not mention it. Anchoring on `path.absolute()` (no normalization) in `_root_anchor`, as design dispatch 2 suggested, would keep relative roots working. Or document and test the refusal. | plugins/autopilot/scripts/log_sink_refusal.py:147 | 1 | ALICE |
| R8 | [1/5] | 🟡 | `_is_inside_git_dir` still lets a `UnicodeDecodeError` or `ValueError` from the strict `text=True` decode escape `stage_review` as a traceback. This is the same defect class T3 fixes, and the design deferred it explicitly "for the completion review". A probe failure also reports "artifact_root is inside git internals", which is a false location fact. Consider catching the decode error and naming the probe failure in the refusal text. | plugins/autopilot/scripts/review_stage.py:420 | 3 | ALICE |
| R9 | [1/5] | 🟡 | Delivery evidence stops at three unresolved provenance failures, although the supplied reviewed-revision results show only the 19 external controller failures. Append the final revision, command, result and provenance resolution to the recovery report; preserve earlier failed runs as history. | docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md:98 | 4 | BOB |
| R10 | [1/5] | 🟡 | The T1 receipt command contains literal `...`, violating the required exact-command evidence. Recover the complete invocation from its raw log, or record a fresh exact invocation and result without rewriting the historical measurement. | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:16 | 4 | BOB |
| R11 | [1/5] | ⚪ | Commit 44bb21e reverts "Tower" to "Lantern" in two discovery files, which are outside the PRD's write paths and contradict the current vocabulary in AGENTS.md. The commit message gives a recorded user decision and a digest-pin reason, so this is accepted. It is worth noting so the next reader does not "fix" it back. | docs/dev/project-management/discovery/00011-autopilot-agent-plugins-port.md:11 | general | ALICE |
| R12 | [1/5] | ⚪ | `_root_anchor` takes the shortest prefix whose realpath equals the root's realpath as "the root spelling". A path that starts outside the repository and enters it through a symlink to the root (for example `/out/back/logs/x` where `/out/back` is a link to the root) is therefore accepted as an alias spelling. It writes only inside the root, and it matches the spec's rule that a symlinked ancestor or alias of the root is allowed. Recorded only because the "leaves and returns" wording could be read more strictly. | plugins/autopilot/scripts/log_sink_refusal.py:141 | 1 | BLAKE |
| R13 | [1/5] | ⚪ | Mechanical replay reports 46 T1/T3 cases passing against the base. These include intentionally retained behavior and success controls; making every control fail would contradict the design's explicit regression-control requirement. | tests/autopilot/test_helper_recovery_v3.py:197 | general | BOB |
| R14 | [1/5] | ⚪ | Mechanical replay reports four artifact cases passing against the base. The four explicitly named controls preserve success and unchanged-name cleanup behavior; they are outside the corrective fail-first obligation. | tests/autopilot/test_helper_recovery_v3_artifact.py:168 | 2 | BOB |
| R15 | [1/5] | ⚪ | The full suite retains 19 AP00018 controller failures. They remain an external deferral and block pushing; repairing controller behavior is outside this PRD's authorized scope. | N/A | general | BOB |
| R16 | [1/5] | ⚪ | Receipt v3-T1 `command` holds a literal `...` elision (`-k sink_alias ... -q`) and `duration_seconds: "not captured"`; T1 exit criteria require exact commands | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:36 | T4 | EVE |
| R17 | [1/5] | ⚪ | PRD T1(d) "a component swapped to a symlink between preflight and open under mixed spelling" is pinned for the log sink only (`test_sink_alias_a_log_parent_swapped_for_a_symlink_after_refuse_fails_the_sink`); no v3 case swaps the artifact sink's parent under mixed spelling | tests/autopilot/test_helper_recovery_v3.py:539 | T1 | EVE |
| R18 | [1/5] | ⚪ | Commit 44bb21e edits two digest-pinned discovery docs outside every PRD write path and reintroduces "Lantern (provisional)" wording the taxonomy settled as Tower on 2026-11-05 | docs/dev/project-management/discovery/00011-autopilot-agent-plugins-port.md:205 | general | EVE |
| R19 | [2/5] | 🟡 | [MECH] 46 touched tests in the new file pass against the pre-change code | tests/autopilot/test_helper_recovery_v3.py | general | EVE, mech-check |
| R20 | [2/5] | 🟡 | [MECH] 4 touched tests in the artifact file pass against the pre-change code | tests/autopilot/test_helper_recovery_v3_artifact.py | general | EVE, mech-check |
| R21 | [1/5] | ⚪ | The source map has no helper-disposition row for `_root_anchor` (nor `_acquire_sink`, `_write_artifact`), and `_pinned_parent_fd`'s row still sits under `verification:` though it lives in log_sink_refusal; the generator's `log_sink_refusal` roster at update_helper_map.py:196 is a hardcoded pinned-source list | tools/autopilot/source-map.json:285899 | T4 | EVE |

## Alice

Implementation-aware consensus lens, run as a Claude subagent at high effort on
the staged context, full diff and engram pack.

Eight findings, carried verbatim into the table as R7, R1, R8, R4, R2, R6, R3 and
R11. Her highest call is R7 (🟠): she reproduced the relative-`--project-root`
refusal herself from the repo root rather than inferring it from the diff, and
cites the three call sites that keep the path relative.

Per-rule verdicts:

```
R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass
```

Her two `fail` verdicts attach to R1 (R1 of the consensus rubric: new behavior
untested - the `os.dup` branch) and R4 (integration with existing callers - the
relative-root regression of R7).

## Blake

Blind lens: PRD-only prompt, no diff, no file list, no review history, no design
doc, no engram pack, no settled ledger. He located the code himself.

Three findings, all ⚪, carried into the table as R3, R5 and R12. He verified T1
through T4 against the spec by reading the implementation, and ran 13 named test
files narrowly: 496 passed. He explicitly did not rerun the full suite, the
`unittest` discovery, `validate.py` or `generate_marketplace.py --check`, and
recorded that the staged test-gate block gave him an exit-1 line with no counts
he could tie to the 19 AP 00018 controller failures - which is exactly the gate
parser defect noted under Tests below.

Per-rule verdicts: B1 through B19 all `pass`.

## Bob

Doubt lens plus de-slop, run on codex in the static-only sandbox from the
inlined 307133-byte prompt. Thread id `01a1bb4c-039d-73e2-b812-7bf04cb26d94`
captured for cycle-2 resume.

Four FIX findings (R1, R9, R10, R2) and three KNOWN findings (R13, R14, R15).
His VERIFY bucket was empty.

Per-rule verdicts:

```
R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass
```

Doubt-rubric verdicts:

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Carl

UI and design specialist, gemini-run on backend `copilot`, model
`gemini-3.8-flash`. Lane exited 1 on transient server/DNS errors after
publishing a complete review; salvaged, not retried (see Agent Status).

`[CARL] ✅ No issues found`

He read the context, diff and engram pack, checked file and function sizes by
AST, ran the two v3 test files, the `unittest`/`validate.py`/marketplace checks,
the provenance and map `--check`, and a nine-file helper suite, and swept the
diff for TODO/FIXME/debug markers and for skip/xfail in the new tests. No marker
and no skip was found.

Per-rule verdicts:

```
R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass
```

## Eve

Fifth lens, Claude Fable 5 subagent carrying the same doubt prompt as Bob. She
joined because the resolved `doubt_reviewer` is `fable`; the codex rung guard did
not fire (no task was codex-implemented).

Twelve issue lines, carried into the table as R6, R1, R4, R2, R16, R17, R5, R3,
R18, R19, R20 and R21. She bucketed them as 5 FIX, 1 VERIFY, 6 KNOWN - counts
that reconcile to her twelve lines.

Her VERIFY item names an exact command and was queued to
`docs/dev/project-management/reviews/00013-autopilot-session-helpers-v3-checks-1.json`:
whether the artifact sink's parent swap under mixed spelling is pinned somewhere
other than the log-sink case.

She also counted the 46+4 pass-at-base tests per test function and reports each
one as either a labelled control or a pin of behavior the rewrite had to
preserve, concluding none is a missing pin - and noting that the PRD's "each
failing at the v2 HEAD" is therefore not literal, while the receipt's red split
(48 failed, 42 passed) is honest.

Doubt-rubric verdicts:

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Follow-up Tasks Created

None by this skill. Under autopilot the decision gate in
`run-autopilot/references/phase-review.md` classifies these rows and makes the
single `autopilot review-close --batch-id decision-gate` call that creates every
task the cycle needs.

Verdict: 21 findings
Tests: 1217 passed, 19 failed, 0 skipped (suite run this cycle)

Test-gate provenance, stated plainly rather than smoothed: the staged
`review-stage` run executed the full gate once at this HEAD
(`uv run --no-project --python 3.12 --with-requirements
tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`,
452.99s) and its own summary line came back
`Tests: counts unavailable (suite run this cycle, exit 1, no PASS/FAIL/SKIP/EXIT
summary line)` - the known `-q` summary parser defect this PRD's build gate hit
too. The counts above were read from that same run's raw log,
`docs/dev/tmp/gate-ap00013-v3-c1.log:467` (`19 failed, 1217 passed in 452.99s`),
not from a second suite run and not estimated. All 19 failures are the AP 00018
controller nodes, a pre-existing external deferral: the base commit carried them
and nothing in this PRD's scope is red. The build session's own gate at f2a7e43
showed 20 failed / 1216 passed; the extra node there was
`test_helper_provenance_real.py::test_source_audit_accepts_the_generated_map`,
resolved by commit 44bb21e, so the predicted "only the 19" state is confirmed at
this HEAD.

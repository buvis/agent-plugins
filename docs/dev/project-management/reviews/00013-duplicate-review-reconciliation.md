# AP 00013 duplicate-review reconciliation

Date: 2026-11-02. Examined HEAD: `afe3e12`.

Coordinator-only reconciliation of the duplicate `agent-plugins-6d` cycle-1
review, before cycle 2. This is not another review cycle, a replacement ledger,
or a completion verdict. Do not include this document or its source artifacts
in Blake's inputs. The restored review remains authoritative for cycle-1 task
and decision identities; its Bob thread is `01a19b8f-6516-7a22-92b6-f45b995d9744`,
not the duplicate review's thread.

Inputs:

- `docs/dev/tmp/00013-review-01-by-agent-plugins-6d.md`, SHA-256
  `791b36ee3683ca8272a5c28f5edd3a46454ec0be9fc198df8a359eaa309370bd`.
- `docs/dev/tmp/00013-ledger-by-agent-plugins-6d.json`, SHA-256
  `bc8853cd565bd7dc635948120f553e1808207138557d99383bd3400cff98caea`.
- `00013-autopilot-session-helpers-v1-review-01.md` and
  `00013-autopilot-session-helpers-v1-ledger.json` in this directory.
- Current helper sources and rework commits from `6c1352c` through `afe3e12`.

`D<n>` below means row R<n> of the duplicate review; `R<n>` means the restored
review. The duplicate ledger's 27 entries repeat D13-D39; it adds no separate
finding. Its `single-voice` dispositions are historical inputs, not proof that
the claims are false. No duplicate ledger entry was imported into the settled
ledger, and no workflow state was changed by this reconciliation.

## Dispositions

| Duplicate | Restored identity | Disposition and evidence |
| --- | --- | --- |
| D1 | R1 | Fixed by `85c073d`; current AST spans are 48 lines for `prepare_close` and 49 for `stage_review`. |
| D2 | R1, plus a simplification | Size fixed by `85c073d`. The duplicate `_staged_files` construction remains in `stage_review` and `_write_cycle`; retain as a Low simplification observation, not a correctness failure. Both calls use the same inputs, and the first intentionally computes destinations before validation/writes. No extra rework is inferred here. |
| D3 | R6 | Fixed by `6984cf5`: facade output uses sink refusal before writing. Cycle-1 boundary tests cover live-state output destinations. |
| D4 | R2 | Fixed by `b0361c1`: CI pin, Python version, and marketplace-step assertions follow the Renovate-updated plugins job. The 19 controller failures retain AP 00018 ownership. |
| D5 | R13 | Fixed by `527d880`: `_backed` compares the normalized issue in addition to ref, severity, and file. |
| D6 | R7 | Fixed by `6984cf5` and `e0b255b`: job manifests control rendered refs and each job's context artifact. |
| D7 | R8 | Fixed by `6984cf5`: external destination validation probes its repository, tracked outputs, live-state paths, and symlink ancestry. |
| D8 | R10 | Fixed by `527d880`: `_in_nested_repo` probes the nearest existing ancestor. |
| D9 | R11 | Fixed by `6984cf5`: `_unsafe_paths` compares both resolved sinks with identifiable argv token paths before opening either sink. |
| D10 | R12 | Fixed by `6984cf5`: `_dirty_check` includes tracked symlink targets; verification calls it before and after execution. |
| D11 | R14 | Fixed by `527d880`: carry task snapshots require and validate status before matching unfinished tasks. |
| D12 | R2 | Same CI drift as D4; fixed by `b0361c1`. |
| D13 | Additional; adjacent to R16 | **Open Medium, coordinator decision required.** `_execute` calls `Popen` before its exception-handling block. A missing executable raises `FileNotFoundError`; facade `_call` does not catch `OSError`. R16 discusses sink/path failures, not this spawn failure. Probe below confirms the exception without running a child. |
| D14 | R2 | Same CI drift as D4; fixed by `b0361c1`. |
| D15 | R4 | Fixed by `6984cf5`: `group` rejects non-object findings with `ValueError`, which the facade converts to exit 2. |
| D16 | R18 | Existing settled Medium deferral, still present. `_git` has no timeout. Keep the restored deferral; do not create a duplicate. |
| D17 | R20, with an additional variant | **Existing discarded Medium plus verified additional variant.** Short-row handling is already R20. File-before-Issue plus an escaped issue pipe corrupts the parsed file and issue too; the bounded probe below confirms it. Keep the R20 history but surface this extra evidence for the coordinator's decision; do not represent either variant as fixed. |
| D18 | R19 | Existing discarded Medium, not fixed. `_pairs_verdict` returns false for no pairs, and `_pair_commit` returns at the first introducing line before examining later invalid lines. Preserve its explicit history; this reconciliation does not turn `discarded` into `false`. |
| D19 | Additional | **Open Medium, coordinator decision required.** `_row_links` derives two reviewers when optional `found_by` is absent, but `prepare_close` passes the original row to `_gate_refusal`; `_found_by_count` then returns zero. The bounded probe below confirms a valid derived pair followed by `single_voice_fix`. |
| D20 | R4 | Fixed by `6984cf5`: group, stage input, and close parameter shape checks reject the described malformed inputs. |
| D21 | R4 | Fixed by `6984cf5`: exact integer cycle, nonempty string batch ID, known tier, and string review ref are validated. Carry snapshot hardening follows in `527d880`. |
| D22 | Additional | **Open Medium, coordinator decision required.** `job_history_defects` materializes `list(range(1, highest + 1))`; the evidence schema permits any positive integer attempt. A safe interception proves the requested range is controlled by the supplied attempt, without allocating it. |
| D23 | R22 | Existing settled Medium provenance deferral, still present. The function-specific location for custody `capture_range` is `cap_check.py`, not the generic custody destination. Keep R22. |
| D24 | R21, with an additional binding concern | **Existing settled Medium deferral, expanded evidence.** The null tested revision is R21. Additionally, `validate_receipts` checks receipt shape but never compares helper bytes at the receipt revision; `apply` hashes current files and can attach unchanged passed receipt evidence. Preserve both aspects under the R21 provenance decision; regenerated current receipts do not fix the generator's binding behavior. |
| D25 | R1 | Same size issue as D1; fixed by `85c073d`. |
| D26 | R1 | Same size issue as D1; fixed by `85c073d`. |
| D27 | R23 | Existing discarded Medium simplification, still present. The comment explicitly identifies the `len(code) < 2` branch as unreachable with cap 4. No behavioral failure is established. |
| D28 | R2 | Same CI drift as D4; fixed by `b0361c1`. |
| D29 | R18 | Same timeout issue as D16; retain the existing settled deferral. Two duplicate-review voices do not constitute an additional independent review cycle. |
| D30 | Additional | **Open Low documentation/side-effect concern.** `_git` still invokes ordinary `git status` without disabling optional locks while its module says "Git reads only, never writes." The source omission is verified; an actual index refresh was not measured here. Keep the concern visible for coordinator disposition; no claim of a demonstrated destructive write. |
| D31 | R25 | Existing environmental limitation. The real-source test deliberately skips without the pinned source checkout; preserve R25 and do not claim a skipped test certified source parity. |
| D32 | Additional | Accepted limitation, not a demonstrated AP 00013 contract breach. `_open_log_sink` deliberately unlinks/recreates guarded untracked outputs with pinned-parent and no-follow flags. No two-file atomic publication guarantee is specified for these non-authoritative reports. A crash can leave a log without an artifact; no completion or reuse should be inferred from a lone log. Do not replace this security-sensitive sink mechanism on this observation alone. |
| D33 | Additional | Accepted boundary. `reuse_verdict` validates artifact shape and code/tree compatibility but does not hash the current log. The duplicate finding itself states that controller acceptance owns this decision. The helper returns a proposal/report, not authoritative verification acceptance. Preserve the limitation; do not claim log integrity was checked. |
| D34 | Preexisting failure report | Known AP 00018 task-7 red tests, not an AP 00013 helper defect. `00013-preexisting-suite-failures.md` owns their attribution. They remain a master-push blocker until AP 00018 turns them green. |
| D35 | Mechanical-check scope note | Characterization tests intentionally preserve prior validator behavior. Their passing at the base is not evidence that a new behavior test is ineffective. These files are also outside AP 00013's helper rework scope. |
| D36 | R3 | Duplicate ledger's blanket dismissal is superseded by the restored R3 decision: `fdb9918` pins all helper capability IDs in `test_facade`, making omission of a newly added ID fail. |
| D37 | Mechanical-check scope note | Preservation tests for original owners, unrelated arrays, and historical README sections intentionally pass before the change. No additional defect shown. |
| D38 | Mechanical-check scope note | Canonical export and malformed-input refusal were already behavior at base; the two tests retain regression value. No new-behavior claim is established by their base pass. |
| D39 | R15 and R5 | Restored R15 identifies the meaningful test weakness; R5's cycle-1 boundary tests create real case-variant paths. Preserve that stronger disposition, not the duplicate ledger's generic "already held" rationale. |

## Additional evidence and limits

These focused probes ran on current helper modules, using only in-memory
objects. They are diagnostic observations, not new committed tests or a
completion review:

- D13: `_execute(['/definitely-not-an-ap00013-command'], cwd, BytesIO(), deadline)`
  raised `FileNotFoundError`. `Popen` did not start a child.
- D17: `_row_from_table` with columns `Ref, Consensus, Severity, File, Issue,
  Task` and row `R1, [1/4], medium, src/x.py:1, left\|right, 1` returned
  `Row(ref='R1', severity='medium', file='left\\', issue='')`.
- D19: `_row_links` accepted two same-key findings attributed to Alice and Bob
  and derived `found_by=['alice', 'bob']`. `_single_voice_refusal` on the same
  chosen Medium fix row without optional `found_by` returned `single_voice_fix`.
- D22: the module's `range` lookup was intercepted before allocation. A single
  result with `attempt=1000000000` requested `(1, 1000000001)`. No large range
  was materialized. Schema inspection confirms `minimum: 1` with no maximum.
- AST inspection, not layout heuristics, measured the two functions for D1.

Open additions requiring the coordinator's cycle-2 disposition are D13, D19,
D22, and D30; D17 and D24 add evidence to existing R20 and R21 respectively.
D2's remaining duplicate construction is a non-blocking simplification
observation. No additional unresolved High or Critical was found in this
reconciliation. Existing cap, fresh-session, full-lens, and blind-input rules
remain unchanged; these observations authorize no extra review cycle.

## Verification

`python3 scripts/validate.py` passed: 3 plugin packages and 15 skills.
The cycle-1 regression subset passed: **115 passed in 69.05 seconds**, using
`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest`
with these files and `-q`:

- `tests/autopilot/test_cycle1_boundaries_stage.py`
- `tests/autopilot/test_cycle1_boundaries_verify.py`
- `tests/autopilot/test_cycle1_hardening_close.py`
- `tests/autopilot/test_cycle1_hardening_sinks.py`
- `tests/autopilot/test_cycle1_boundaries_context.py`
- `tests/autopilot/test_package.py`
- `tests/autopilot/test_facade.py`

No full-suite pass is claimed by this document.

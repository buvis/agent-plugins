---
prd: docs/dev/project-management/prds/wip/00018-autopilot-controller-kernel-v2.md
review: 3
date: 2026-11-11
head_sha: b8e5f21a1ab3fd30c5a2ee585cce3a4d5ed31fa0
reviewers: alice,blake,bob,eve
agents:
  alice: available
  blake: available
  bob: available (claude fallback ran the doubt prompt; codex is quota-limited until 8:09 AM)
  carl: permanently unavailable (copilot backend crashed with a V8 fatal error, exit 1; native gemini rejected the client tier, exit 4)
  eve: available
dispatch_rows:
  bob: 7f8291fa
  carl: fbfc9a60
---

# Review: 00018-autopilot-controller-kernel-v2

Diff range: `da798294f5c48c92f3610f28458181bd6202d78e..b8e5f21a1ab3fd30c5a2ee585cce3a4d5ed31fa0` (incremental — cycle 1 reviewed `dacba71..292f893`, cycle 2 reviewed `292f893..da79829`)

codex_rung_guard: fired (7 codex-implemented task(s))

Tests: 1615 passed, 0 failed, 0 skipped (reused from last-verification.json at b8e5f21)

carl: skipped after two failed dispatches; latched unavailable for batch 202611090642 from cycle 3 of 00018-autopilot-controller-kernel-v2.md

## Cycle notes (read these before the findings)

**Carl is gone for this batch.** His first dispatch died inside the copilot
backend (`Check failed: isolate_->IsOnCentralStack()`, SIGTRAP, exit 1), and his
one retry on the native Gemini CLI was refused with
`IneligibleTierError: This client is no longer supported for Gemini Code Assist
for individuals` (exit 4 — permanent configuration unavailability). Per the
exit-4 rule he is latched in `state.batch.unavailable_reviewers`, so later
cycles and PRDs in this batch will not dispatch him. His empty `-o` file from
the crashed first dispatch was NOT consolidated. Consensus is therefore computed
over four reviewers, `[n/4]`.

**Bob ran on Claude, not codex.** A direct probe returned
`You've hit your usage limit ... try again at 8:09 AM`, so codex is in the same
quota class as in cycle 2. A Claude subagent ran Bob's exact assembled inlined
prompt (650 KB: context plus full diff inlined verbatim), with the read-only
shell instruction replaced by the Read tool. The doubt lens did not drop.
`codex_thread_id` is deliberately omitted: codex produced no review this cycle.

Carl's retry dispatch row is `d490eb05` (opened from `fbfc9a60`); both are closed
as errors in the dispatch ledger.

**Both Alice and Bob omitted the `R5` verdict line** on their first output and
each spent its single retry re-emitting the complete R1-R13 block. Both returned
`R5: fail`.

**The test gate is green at this head.** `autopilot verify` ran the full gate at
b8e5f21 (the two state-only chore commits above the cycle-2 head were committed
first so the tree was clean): 1615 passed, 0 failed, 0 skipped, exit 0. The
cycle-2 flake `test_competing_initializers_publish_exactly_one_intact_winner`
(prior R45) passed; Eve repeated it 20 times plus `StateLockRaceTest` for 22
passes, and measured the ENOENT cause directly (1170/1600 with
`O_CREAT|O_NOFOLLOW`, 0/1600 with `O_CREAT|O_EXCL`), so the bounded `_open_lock`
retry addresses a real race.

**Eve's output is in the doubt contract's FIX/VERIFY/KNOWN shape, not the
`[EVE] … | File: … | Task: …` issue-line shape**, so `consolidate_findings.py`
could not read it. Her twelve FIX rows and her VERIFY row were hand-merged into
the table below: seven onto rows Alice or Bob already raised (raising those
rows' consensus), five as new single-voice rows. Her seven KNOWN rows are
recorded as the discard reasons they justify rather than as findings.

**Hand-merges beyond the script's own.** The script merged prior-R1's two
provenance lines (`:1134` and `:1062`) into one row. Four further rows were
folded by hand because the script's matcher compares `path:line` and these cite
different lines of one defect: R7 into R5 (`helper_map_successor.py:51` and
`:50`, the successor check's silent skip), R9 into R6 (the same CI proof gap),
R17 into R8 (`test_controller_actors.py:93` and `:101`, `authenticate`'s
credential-required quirk and its missing unit cases), R14 into R10
(`helper_map_successor.py:88` and `:91`, the `adaptation_reason` rewrite).

**The cycle-3 verification-check queue is empty, deliberately.** The only VERIFY
item either doubt lens raised is R6, and its check cannot be queued: it requires
a `git push` first, and `gh run list` is not a project verification command.
Both are excluded by the queue's command-shape rule, so R6 is **not queued:
command shape** and stays an ordinary finding — already a settled deferral from
cycle 2. The two cycle-2 queued checks both exited 0 (they ran and reported that
the finding stands), so the carry-forward rule added nothing mechanically; R6 is
in the table below on its reviewers' own voices.

**Blake's four re-raises were auto-dismissed by the ledger** (`--ledger-dismiss
BLAKE`); the dismissal section is reproduced verbatim below.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/4] | 🟡 | Prior R1 is only mostly fixed. The scope and `unverified` text are corrected and 16 of 17 `test_map` rows now name tests. The row for `test_sigkill_at_each_locked_mutation_boundary...` still targets a configuration test and its note says "runtime injection pending" (provenance.json:1134). The `evidence` divergence still says the tests "validate configuration only; fixtures declare future runtime scenarios, not executed durability/auth evidence" (provenance.json:1062). Both contradict the new scope ("every mapped runtime check is covered by ... executed tests"), and this file ships in the pinned digests. Eve adds a third part: two re-pointed rows cite tests that do not exercise the source invariant — :1127 (reader finishes under a shared holder, writer blocks) points at a three-writer test with no reader, and no test in tests/autopilot takes `LOCK_SH`; :1152 (directory inode swapped during open) points at a static symlink test. The pin test only checks that a target name exists and forbids a null target, so an honest "not covered" cannot be recorded. Retarget the sigkill row at a real crash-injection test (for example `test_controller_bootstrap_recovery.py::test_bootstrap_recovers_exactly_once_at_every_declared_crash_boundary`), rewrite or drop the stale `evidence` divergence, cite or add tests for the two re-pointed rows (or set target null and list the gap), and extend `test_controller_provenance_scope_prose.py` to sweep `deliberate_divergences` and every `test_map` note. | plugins/autopilot/contracts/controller/provenance.json:1134 | 12 | ALICE, BOB, EVE |
| R2 | [2/4] | ⚪ | Prior R11 is only partly addressed. Splitting out `helper_map_successor.py` brings `update_helper_map.py` to 788 lines, still 12 lines under the 800-line limit, so the next small edit breaches R13. Move more of the receipt and successor functions (`validate_receipts`, `validate_successor_receipts`) into `helper_map_successor.py` while the split is fresh. | tools/autopilot/update_helper_map.py:788 | 17 | ALICE, BOB |
| R3 | [1/4] | 🟡 | The state-lock retry is an unrecorded divergence from the pinned `StateStore`. The pinned OVCAQ `_locked` opens the lock once and raises on any OSError. `_open_lock` now retries `FileNotFoundError` up to `LOCK_OPEN_ATTEMPTS` times. The PRD requires `provenance.json` to list deliberate divergences from the pin, and `deliberate_divergences` has no entry for it. Add one entry (source: a single open, no retry; target: bounded retry with every alias guard repeated). Add a sentence to the code comment saying which platform shows the ENOENT, because "on this platform" names nothing. | plugins/autopilot/controller/autopilot_state/store.py:268 | 18 | ALICE |
| R4 | [2/4] | 🟡 | Simplification: the new `parse_request` job_id check makes the older ones unreachable through the CLI. `parse_request` raises `wrong_binding` for a non-null `job_id` (protocol.py:107), so the same clause in `run` (protocol.py:234) and in `apply_locked` (protocol.py:181) can no longer fire. Eve adds that once `fresh_binding` passes, `workflow_id` is null and `parse_request` already guarantees `workflow.open` at revision 0, so the `missing_capability` raise at :202-203 and the `revision_conflict` raise at :242-245 are also dead. Keep one check at the parse boundary and delete the repeats, or state in a comment that the repeats are defence in depth. Today the copies can drift apart. | plugins/autopilot/controller/autopilot_state/protocol.py:234 | 18 | ALICE, EVE |
| R5 | [3/4] | 🟡 | Prior R17's first clause survives verbatim: `verify_listed_paths_match_revision` still returns silently when the `rev-parse --is-inside-work-tree` probe exits 0 with output other than "true" (bare repo, `GIT_DIR` set, cwd inside `.git`), so the stale-receipt guard can vanish with no signal. The skip also keys on the English substring `not a git repository` anywhere in stderr, so a localized git makes the synthetic non-git fixtures raise instead of skip, and the new test asserts that English string. Eve probed three cases that each returned None for a bogus revision: `GIT_DIR=/nonexistent-git-dir`, a `.git` directory with HEAD removed, and a probe answering `false` at exit 0; she also found the docstring ("Every other git failure is a refusal, never a skip") and CHANGELOG:40 claim otherwise, and that the tests deliberately avoid the phrase (`assert "not a git repository" not in expected`). Refuse everything except a genuine outside-a-work-tree case (filesystem check on `GIT_DIR`/`GIT_WORK_TREE` and a `.git` entry, or an explicit fixture opt-out), run the probe under `LC_ALL=C`, add the three cases to `PROBE_FAILURES`, and fix the docstring and CHANGELOG:40. | tools/autopilot/helper_map_successor.py:50 | 17 | ALICE, BOB, EVE |
| R6 | [3/4] | 🟡 | R6 (CI proof) is still unproven at the reworked head. `fetch-depth: 0` is on the autopilot job, but no CI run exists at or after this head and master is 47 commits ahead of origin, because loop mode defers pushes; the newest `validate.yml` run on master is 1b588a7 with conclusion failure. Both cycle-2 queued checks ran and reported exactly this. A listed `package_revision` absent from CI history (for example after a squash merge) is now refused as unresolvable where before it was reported as stale, so the push must be a fast-forward. Settled deferral: already in `state.deferred_decisions` from cycle 2; it cannot be closed from inside an unattended session. | .github/workflows/validate.yml:63 | general | ALICE, BOB, EVE |
| R8 | [3/4] | ⚪ | Prior R5 is only half-resolved, and neither offered option was taken. `authenticate` still raises `BindingError("credential required")` inside its own `try`, so that message never reaches a caller, and the test now pins both the visible message and the `__cause__` chain — an implementation detail no caller sees — which codifies the quirk instead of fixing it. The second clause is also unresolved: `AuthenticateTest` still exercises only `path is None`; the `credential mismatch` and secret-digest branches have no unit case beside it (they are reached only through the CLI permissions test). Move the `path is None` check above the `try` and assert "credential required", or delete the test; then add two cases built from `credential_bytes` (wrong secret, wrong binding) asserting `BindingError("credential rejected")`. | tests/autopilot/test_controller_actors.py:101 | 16 | ALICE, BOB, EVE |
| R10 | [3/4] | ⚪ | `refresh_listed_row` rewrites prose by keyword sniffing (`planned\|pending\|on hold`) and replaces the whole `adaptation_reason` with a third wording, so ten controller rows lost their only record of why they have no pinned source ("Newly authored AP00018 controller file; no pinned source asset or source sections"), while the freshly registered bundle row keeps the old shape. A legitimate authored reason mentioning "pending intent" would be clobbered silently. The current map has no such row and the tests pin the rewrite, so this is not a live defect. Keep the leading sentence and append the landed-evidence sentence (or strip only the matched clause), or reuse the `register_controller_asset` template for every listed controller path; keep the status sync either way. | tools/autopilot/helper_map_successor.py:88 | 17 | ALICE, BOB, EVE |
| R11 | [1/4] | ⚪ | The exporter hard-codes OPERATIONS and CAPABILITIES as a literal copy of protocol.py's lists. It never imports them, so drift is caught only by tests. The code comment admits this. | tools/autopilot/export-controller-contract.py:32 | Phase 2 task 1 | BLAKE |
| R12 | [1/4] | ⚪ | A fresh-open replay (null workflow, actor and epoch, same request_id and payload) returns the stored response without credential authentication. It exposes workflow_id, actor_id and the credential path, but never the secret, and the caller needs access to the project root. Low risk, and consistent with the spec's lost-ack replay requirement. | plugins/autopilot/controller/autopilot_state/protocol.py:141 | Phase 1 task 2 | BLAKE |
| R13 | [2/4] | ⚪ | The new retry branch has no deterministic test. `test_concurrent_lock_creators_either_win_or_lose_without_an_io_error` depends on the platform producing ENOENT inside the rendezvous window (it did fail at base in this cycle's replay, so the pin works today), but no test injects a single `FileNotFoundError` at the `openat` and asserts `_open_lock` retries, nor asserts it gives up after `LOCK_OPEN_ATTEMPTS`; the exhaustion branch and the "guards applied on every attempt" claim (CHANGELOG:44) are unpinned, and on Linux CI the transient does not occur so CI covers nothing. Eve adds that the race test's `raced == [1] * CREATORS` check also passes when the 1.5 s rendezvous times out. Patch `os.open` to raise `FileNotFoundError` k times: k=1 and k=15 return a descriptor with `_reject_aliased_artifact` called k+1 times, k=16 raises `StateIOError`. | tests/autopilot/test_controller_staging_admission.py:322 | 18 | BOB, EVE |
| R15 | [1/4] | ⚪ | `test_refreshed_listed_rows_drop_planned_pending_and_on_hold_prose` asserts no claim word anywhere in a refreshed row (`strings(row)`), a rule the generator does not implement: it rewrites only `adaptation_reason` and `acceptance_cases[].expected_outcome`. The real certified README row carries `entry_point_gate.status: "planned"` (source-map.json:150), which the refresh is right to leave alone, so adding that shape to a fixture would redden the suite with no production defect. Scope the sweep to the two fields the generator actually rewrites. | tests/autopilot/test_helper_map_refresh_agreement.py:181 | 17 | BOB |
| R16 | [2/4] | ⚪ | The staging-divergence test still passes if any entry mentions any of four keywords in `json.dumps`, so it cannot fail when the "staging cleanup" entry itself regresses. Prior R41 was discarded on the reason that R1's task would rebuild this file; the file is untouched since a02fbc7, and the new scope test now uses it as its `CONTROL`, so that reason no longer holds. Select the entry whose `topic` is "staging cleanup" and assert `_cleanup_stale_temps` in `source` and `admit_staging` plus the budget in `target`. | tests/autopilot/test_provenance_staging_divergence.py:21 | 18 | BOB, EVE |
| R18 | [1/4] | ⚪ | `_open_lock` retries the create-if-absent open up to 16 times with no yield or backoff, so under heavier contention than the measured five-creator case the transient ENOENT can still escape. | plugins/autopilot/controller/autopilot_state/store.py:253 | 18 | BOB |
| R19 | [1/4] | ⚪ | [MECH] 1 touched test passes against the pre-change code: test_owner_recover_refuses_nonempty_job_evidence_and_admits_an_empty_list | tests/autopilot/test_controller_contract_agreement.py | 18 | BOB, mech-check |
| R20 | [1/4] | ⚪ | [MECH] 1 touched test passes against the pre-change code: test_controller_bundle_reproducible_check_rejects_an_oversized_committed_bundle | tests/autopilot/test_controller_export.py | 16 | BOB, mech-check |
| R21 | [1/4] | ⚪ | [MECH] 4 touched tests pass against the pre-change code: test_accepts_reconciled_job_ids_with_a_single_entry, test_accepts_reconciled_job_ids_with_multiple_entries, test_rejects_duplicate_reconciled_job_ids, test_controller_refuses_nonempty_reconciled_job_ids_with_rejected_evidence | tests/autopilot/test_controller_kernel_recover_jobs.py | 16 | BOB, mech-check |
| R22 | [1/4] | ⚪ | [MECH] 3 touched tests pass against the pre-change code: test_refuses_reconciliation_once_the_staging_budget_is_exhausted, test_refuses_reconciliation_once_the_staging_byte_ceiling_is_exceeded, test_repeated_crashes_stay_refused_while_exhausted_and_finish_once_freed | tests/autopilot/test_controller_owner_recovery_staging_budget.py | 16 | BOB, mech-check |
| R23 | [1/4] | ⚪ | [MECH] 5 touched tests pass against the pre-change code: test_bootstrap_reconciliation_publishes_revision_zero_without_owned_orphans, test_existing_open_still_publishes_with_large_orphans_under_both_budgets, test_existing_open_without_owned_orphans_advances_the_revision_by_one, test_near_miss_artifact_names_never_consume_the_existing_open_budget, test_a_corrupt_state_lock_sidecar_is_an_io_error_not_a_lost_race | tests/autopilot/test_controller_staging_admission.py | 18 | BOB, mech-check |
| R24 | [1/4] | 🟡 | Bootstrap reconciliation is refused under orphan pressure even when it publishes nothing, while the owner path admits the same case: `finish_bootstrap` calls `admit_staging` unconditionally, where `owner.finish_intent` guards it with `if current != candidate`. Probe: a bootstrap crash at `state_published` plus 65 owned orphans makes the identical request return `recovery_required` at revision 0 and the snapshot stays `recovery_required`; the same owner-path case returns ok. README:416-418 and CHANGELOG:46 say a pending intent over budget "refuses every request, the reconciliation included", which is false for the owner path. No test covers either cleanup-only case. | plugins/autopilot/controller/autopilot_state/actors.py:431 | 18 | EVE |
| R25 | [1/4] | ⚪ | Two new runtime tests re-test behaviour already pinned at test_controller_owner.py:163-168 and test_controller_owner_v2.py:183-184 (non-empty `reconciled_job_ids` gives `rejected_evidence`), and both pass at base. The recover_jobs copy also repeats the tree check `reject_unchanged` already makes, with `assertTrue(a == b)`. Delete `OwnerRecoverRefusesJobClaimsTest` and keep at most the contract-agreement one. | tests/autopilot/test_controller_kernel_recover_jobs.py:55 | 16 | EVE |
| R26 | [1/4] | ⚪ | Anti-exploit scaffolding in the three new test files pins wording and document shape rather than contract: the `ACCEPTANCE` regex, an eleven-way `UNRESOLVED` regex for one message, doubled attempts with `seen` counting and random request ids, word-count asserts on fixture prose, an exact `MAPPED_ROWS = 17`, `SECTION_MINIMUM`, `AFFIRMATIONS` keyword groups. Any honest provenance or fixture edit breaks them. Keep the behavioural assertions, drop the guards. | tests/autopilot/test_helper_map_refresh_agreement.py:52 | 17 | EVE |
| R27 | [1/4] | ⚪ | Fix commit e1ca894 (refuse an unreadable listed path) shipped without a test: no test removes a listed work-tree file that exists at the revision. Add a case that commits, unlinks a listed file, and expects a `ValueError` naming the path and "work tree". | tools/autopilot/helper_map_successor.py:65 | 17 | EVE |
| R28 | [1/4] | ⚪ | Prior R8's "repeated crashes" half is still untested. The test named for it replays `apply` twice while refused (no crash can happen there), then deletes the orphans; it does not show that crashes during reconciliation stop growing temporaries at the ceiling. Rename it to what it proves, or add a publication-boundary crash loop asserting the temporary count stops at the limit. | tests/autopilot/test_controller_owner_recovery_staging_budget.py:88 | 16 | EVE |

### Auto-dismissed (ledger)

- [BLAKE] 🟡 Only 4 of the closed operations are implemented (workflow.open, owner.acquire/release/recover). Job-scoped credentials are absent, and any non-null job_id is refused as wrong_binding. Only workflow.core.v1 is advertised, not jobs, reviews or records. | File: plugins/autopilot/controller/autopilot_state/protocol.py:45 — Already settled at cycle 1 as a scope decision (same finding, then cited at schema.py:253): the PRD permits later operation families to stay declared-but-unavailable, so implementing the remaining operations is a successor PRD. Re-raised with no new evidence, so the cycle-1 reason still holds.
- [BLAKE] ⚪ reserved_operations maps operations to capability IDs the spec never names. | File: plugins/autopilot/contracts/controller/workflow-v1.json:811 — single-voice and low impact by Blake's own account: the IDs are not advertised. Touching the schema would re-trigger the pinned digest chain for no behavioral gain.
- [BLAKE] ⚪ StateStore keeps public restore, transaction, read and initialize methods that no controller path calls. | File: plugins/autopilot/controller/autopilot_state/store.py:183 — single-voice and deliberate: store.py is retained from the pinned OVCAQ source under its provenance record, which justifies retained symbols; deleting them widens the divergence the record has to explain.
- [BLAKE] ⚪ The state flock is taken with no timeout. | File: plugins/autopilot/controller/autopilot_state/store.py:236 — single-voice and not a defect: Blake records that it matches the spec, which puts the time bound in clients, and the README documents it.

## Alice

Eight findings: three 🟡 (prior R1's residual provenance claims, the unrecorded
lock-retry divergence, the now-unreachable `job_id` checks) and five ⚪ (the
English-text work-tree probe, prior R5's half-fix, prior R11's 788 lines, prior
R6's unprovable CI claim, `refresh_listed_row`'s keyword rewrite). No Critical,
no High.

Prior-finding disposition, verified in code and by running the 54 tests in the
changed test files (all pass): resolved R2, R3, R4, R7, R8, R9, R10, R12, R13,
R17, R21, R36, R45; not resolved R1 (residual), R5 and R11 (partial), R6
(unverifiable). She read the fail-first replay's 14 pass-at-base tests as
matching the settled "passes at base by design" calls and did not re-raise them.

R1: pass
R2: pass
R3: pass
R4: pass
R5: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Six findings, one 🟡 and five ⚪; no Critical, no High. Four were auto-dismissed
by the ledger (above). Blake verified the contract bundle live on Python 3.12
(the six required keys, the digests, `package_version 0.10.0` matching
`plugin.json`, and the raw-byte shasum `a296acb4…c7f5` equal to the digest in
README:334), the CLI's three operations and its version guard, the ten-key
envelope and seven error codes, bootstrap credential modes (0700/0600, SHA-256
plus `hmac.compare_digest`, O_NOFOLLOW descent, hard-link checks), idempotent
receipts and CAS under flock, the two-phase credential intent, the 64-file /
16 MiB staging budget, lease-epoch rotation, kernel isolation from OVCAQ, and a
test for every PRD exit-criteria scenario. He ran four test files (56 passed)
and did not rerun the full suite.

B1-B19: all pass.

## Bob

Fourteen findings: three 🟡 (provenance's two remaining self-contradictions,
R17's surviving silent skip, R6 unproven) and eleven ⚪ (the unpinned lock
retry, the `adaptation_reason` rewrite, the refresh test's unimplemented rule,
the keyword-any divergence test, R5's missing unit cases, R11's 788 lines, the
backoff-free retry, and five [MECH] pass-at-base rows). No Critical, no High.

His own gate note: R9 fails only on the provenance artifact the PRD requires to
be a truthful current record, and R10 fails only on the retained silent skip in
`verify_listed_paths_match_revision`. He honoured every settled decision
(R14-R16, R22-R25, R27-R33, R37-R40, R43, R44 not re-raised) and recorded the
mech-replay rows as by-design in his KNOWN bucket.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

R1: pass
R2: pass
R3: pass
R4: pass
R5: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

## Eve

Twenty findings: 12 FIX (four medium, eight low), 1 VERIFY, 7 KNOWN. Nothing
critical. She probed rather than read: the cleanup-only reconciliation asymmetry
(R24) was demonstrated in temp dirs on both paths; the successor check's silent
skip was demonstrated three ways; the ENOENT lock race was measured at 1170/1600
with `O_CREAT|O_NOFOLLOW` against 0/1600 with `O_CREAT|O_EXCL`; the receipt
counts were re-collected at HEAD (a=89, b=71, c=48, d=60, all matching, task d
also executed at 60 passed). She wrote no repo file and did not rerun the full
suite.

Her KNOWN bucket supplies the by-design explanation for all five [MECH]
pass-at-base rows, the 64-file admission trade-off settled in cycle 2, the
outside-a-work-tree skip (single-voice discard in cycle 2), and R11's 788 lines
as a refactor outside this rework.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Carl: permanently unavailable. First dispatch: copilot backend
`gemini-3.8-flash` terminated by SIGTRAP after a V8 fatal error
(`Check failed: isolate_->IsOnCentralStack()`), exit 1, no review text. Retry on
the native Gemini CLI: `IneligibleTierError … UNSUPPORTED_CLIENT`, free-tier
"Gemini Code Assist for individuals" rejected, exit 4. Latched for batch
202611090642. No Carl output was consolidated.

Verdict: 24 findings
Tests: 1615 passed, 0 failed, 0 skipped (reused from last-verification.json at b8e5f21)

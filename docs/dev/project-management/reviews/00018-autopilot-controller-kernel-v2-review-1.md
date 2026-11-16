---
prd: docs/dev/project-management/prds/wip/00018-autopilot-controller-kernel-v2.md
review: 1
date: 2026-11-10
head_sha: 292f893e16d64ada8fe4933acb8b0ede539d20aa
codex_thread_id: 01a1c771-e08c-75b3-8404-4a4e69d4b028
reviewers: alice,blake,bob,carl,eve
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: available
dispatch_rows:
  bob: b4943d96
  carl: 66317477
---

# Review: 00018-autopilot-controller-kernel-v2

Diff range: `dacba71638e04269e9370a1765adf1cd58b57027..292f893e16d64ada8fe4933acb8b0ede539d20aa`

codex_rung_guard: fired (7 codex-implemented task(s))

Tests: 1554 passed, 0 failed, 0 skipped (reused from last-verification.json at 1b588a7)

## Cycle notes (read these before the findings)

**Diff scoping — a deliberate, recorded narrowing.** The raw range is 198 files
and 22.8 MB. About 100 of those files are autopilot *operational* artifacts
under `docs/dev/project-management/autopilot/` — archived inputs of the previous
(blocked) review attempt, codex session transcripts, and metrics JSONL — not
implementation. The reviewers' diff was scoped with
`:(exclude)docs/dev/project-management/autopilot`, leaving 322 KB over
`plugins/autopilot/`, `tools/autopilot/`, `tests/autopilot/`, the PRD and the
design doc. The unscoped diff is retained at
`docs/dev/tmp/review-diff-ap00018-c1-20261110.full.diff`. Nothing in the
excluded set is product code; ALICE independently flagged the remaining
non-AP00018 documents in range as pollution (R23).

**Local gate vs CI — they disagree, and CI is the one that counts.** The
`Tests:` line above is the reused local verdict at `1b588a7`. EVE checked CI at
that same sha and found it red (R6). The local 1554/0/0 therefore does not hold
on the project's own runner. This is recorded as a HIGH finding, not papered
over by the green local line.

**Consolidation correction — applied by hand, declared here.** `consolidate_findings.py`
merged row R1 across `update_helper_map.py:549 ~ :574 ~ :578` after suffix
stripping. Two of those citations are the same defect (generator duplication,
ALICE + EVE), but BOB's `:574` finding is a *different and more severe* defect:
successor evidence not binding controller bytes to the tested revision. The
merge had silently replaced that 🟠 text with the 🟡 duplication text. R1 is
restored to 🟡 with three finders, and BOB's finding is re-entered as **R39**.
The R2 merge (`actors.py:411 ~ :412`, ALICE + EVE) is a correct merge of one
defect.

The script also **under**-merged: it left six rows standing that restate a
defect another reviewer had already raised, which understated consensus and
would have had the decision gate discard real multi-voice findings as
single-voice. Those were merged by hand, each onto the row carrying the
strongest statement of the defect, and the absorbed refs are named here so the
trail is complete:

- **R3** (High; ALICE + BLAKE + EVE) absorbs **R8** and **R14** — the
  provenance.json record is untruthful, and the missing `_cleanup_stale_temps`
  divergence entry is one instance of that.
- **R9** (Medium; BLAKE + EVE) absorbs **R10** and **R31** — the declared-but-
  absent `test_controller_actors.py` and the unnamed acceptance scenarios are
  one PRD-structure/traceability gap.
- **R11** (Medium; BOB + EVE) absorbs **R32** — the exporter's size limit is
  neither enforced on read nor pinned by a test.
- **R20** (Low; ALICE + BLAKE) absorbs **R25** — the operation and capability
  lists are duplicated between the exporter and the protocol.

The table therefore carries 37 rows for 43 raised findings. No finding was
dropped: every absorbed one is quoted in the row that absorbed it.

**No settled-decisions ledger exists yet** (cycle 1), so the two `--ledger`
flags were omitted and no Blake re-raise was auto-dismissed.

**No verification-check queue was written.** EVE's single VERIFY item names a
multi-step Python probe (patch `protocol.response`, call `protocol.apply_locked`
in a temp root), not one runnable project verification command, so per the
not-queued rule it stays an ordinary finding — R38 — and is classified normally.

**Mechanical blocks.** The tautological-shape detector found nothing across 109
test functions in 10 files. The fail-first replay found 6 `[MECH]` rows (22
touched tests passing against the pre-change code); two were folded into rows
that already named the same file and tests (R22, R36) and four are entered as
R40–R43. EVE's KNOWN bucket justifies all of them as PRD-ordered
characterization of retained v1 behavior.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R6 | [1/5] | 🟠 | CI is red on a PRD-named acceptance test at the pushed implementation head 1b588a7 (run 42710174255, ubuntu, Python 3.12: 1 failed, 1542 passed, 11 skipped): test_new_helper_files_are_owned_and_digested_from_current_bytes runs `git show 50c8c2f...:plugins/autopilot/README.md`, which cannot resolve in the autopilot job's depth-1 checkout (.github/workflows/validate.yml:60 lacks fetch-depth 0), so the local 1554-passed gate does not hold in CI | tests/autopilot/test_helper_provenance_real.py:363 | general | EVE |
| R7 | [1/5] | 🟠 | Runtime contradicts the published controller schema: owner.recover with nonempty reconciled_job_ids now parses in validate_payload and returns rejected_evidence, while workflow-v1.json keeps maxItems 0 (line 228) and fixture recover-nonempty-jobs expects invalid_request; both digests are pinned in contracts/controller-v1.json | plugins/autopilot/controller/autopilot_state/protocol.py:65 | general | EVE |
| R39 | [1/5] | 🟠 | Successor evidence does not bind controller bytes to the tested revision: apply_successor hashes current files but copies the receipt revision unchecked, and the new controller provenance test only compares those hashes with current files. Editing owner.py and regenerating can certify new bytes under the old receipt. Verify every listed file against the receipt's git revision and add a stale-receipt rejection test. | tools/autopilot/update_helper_map.py:574 | 7 | BOB |
| R5 | [1/5] | 🟠 | Staging admission excludes publication temporaries, and intent reconciliation bypasses admission entirely. Repeated crashes at BACKUP_TEMP_FSYNCED can accumulate state-sized orphans without limit. Budget publication and reconciliation allocations before creation; test repeated recovery crashes against both ceilings. | plugins/autopilot/controller/autopilot_state/owner.py:176 | 4 | BOB |
| R3 | [3/5] | 🟠 | plugins/autopilot/contracts/controller/provenance.json contradicts the shipped runtime and is nevertheless certified "passed" by the successor receipt. Its scope says "Configuration characterization only. No runtime has been extracted or certified by this task" and its `unverified` list includes "runtime implementation and runtime test execution". About 11 of 16 `test_map` rows have `target: null` with notes like "runtime ... pending", although test_controller_kernel*.py now cover them. `deliberate_divergences` (provenance.json:1023-1063) omits the removal of `StateStore._cleanup_stale_temps`, which the pinned OVCAQ store.py calls at 4 sites (deleted here from initialize, transaction, restore and the commit failure path); `preserved_invariants` is silent and only README and CHANGELOG mention it. The pin test at test_controller_protocol.py:311 can only resolve targets inside its own class. The PRD requires recorded source-to-target maps "including tests" and a truthful current record. This file is hashed into the published fixture/schema digests and the contract bundle, so the stale claim ships. Fix: update scope and test_map targets, add a "stale publication temporaries" divergence (source deletes them, target retains and counts them under the 64-file/16 MiB budget), let the pin test resolve `file::test` targets, then refresh receipt, digests and map. | plugins/autopilot/contracts/controller/provenance.json:78 | general | ALICE, BLAKE, EVE |
| R4 | [1/5] | 🟠 | The kernel implements only 4 of the ~26 closed operations: `workflow.open` and `owner.acquire/release/recover`. The rest return `missing_capability`. `schema.validate_state` forces `workflow == _WORKFLOW`, so tasks, jobs and review stay frozen at initial values, and no source workflow field is carried by the kernel. Job claim, record_exit and job-credential fencing are absent. The PRD allows later families to stay "declared but unavailable", but it also asks for "epoch-fenced job/operator credentials" and an extracted workflow kernel. Source-outcome equivalence therefore covers only the store, locking and identity layer, not workflow-state behavior. | plugins/autopilot/controller/autopilot_state/schema.py:253 | general | BLAKE |
| R1 | [3/5] | 🟡 | Duplicated logic in the generator. The `CONTROLLER_CONTRACT` block in `apply_successor` rebuilds the same asset row and owner row as `register_controller_asset`. Only the two prose strings differ. Pass the adaptation and outcome strings into `register_controller_asset` and call it once for the bundle and for each listed controller asset. | tools/autopilot/update_helper_map.py:549 | 7 | ALICE, BOB, EVE |
| R2 | [2/5] | 🟡 | `actors.read_intent` hard-codes `{"owner.acquire","owner.release","owner.recover"}` and lazy-imports `owner`. `protocol.OWNER_OPERATIONS` already holds that set. `owner.py` lazy-imports `protocol` in three functions. The set can drift silently, and the actors/owner/protocol import cycle is hidden. Move the owner-operation set (or the intent dispatch) into one module that both sides import. | plugins/autopilot/controller/autopilot_state/actors.py:411 | 3 | ALICE, EVE |
| R9 | [2/5] | 🟡 | PRD structure and traceability gap. `tests/autopilot/test_controller_actors.py` is listed in the PRD's structure and new-symbols but does not exist; actor and credential behavior is spread across test_controller_owner*.py, test_controller_bootstrap*.py and test_controller_staging_limits.py. Separately, 8 of 14 named acceptance scenarios appear nowhere in tests or contracts (`lease_exclusion`, `wrong_actor`, `epoch_revoked`, `fresh_open_replay`, `kernel_equivalence`, `concurrent_cas`, `corrupt_state_recovery`, `unsupported_operation_refused`); the behavior is covered by differently named tests, for example test_controller_owner.py:176 (two-subprocess acquire, one winner) and test_controller_kernel.py:295, 574. Fix: create the declared file from the credential and actor tests, and name the covering tests after their scenarios as the export tests already do. | tests/autopilot/test_controller_actors.py | general | BLAKE, EVE |
| R11 | [2/5] | 🟡 | The bundle exporter's size limit is neither enforced on read nor pinned by a test. `--check` reads the entire existing bundle without enforcing the limit, so a large regular file causes an unbounded allocation before rejection; and no test feeds an input of 16 MiB or more although the CHANGELOG says the exporter "refuses ... oversized inputs". Fix: compare `st_size` with `len(expected)` then use a bounded read, and add a sparse 16 MiB fixtures case for both export and `--check`. | tools/autopilot/export-controller-contract.py:63 | 5 | BOB, EVE |
| R12 | [1/5] | 🟡 | Three frozen invalid-request fixture cases return a different error at runtime (null-existing-actor gives wrong_binding, bootstrap-nonzero-revision gives retryable revision_conflict, bootstrap-acquire gives missing_capability on an absent store and wrong_binding on an existing one, fixtures say invalid_request) because parse_request lacks the schema's null-binding rules, and no test applies fixture cases through the controller (test_contract_examples checks jsonschema only) | plugins/autopilot/controller/autopilot_state/protocol.py:74 | general | EVE |
| R13 | [1/5] | 🟡 | A pending owner intent with a damaged embedded request makes any caller's valid apply fail with invalid_request or incompatible_contract instead of recovery_required: owner.validate_intent lets the ProtocolError from protocol.parse_request (and from actor_binding at line 120) escape the StateError mapping | plugins/autopilot/controller/autopilot_state/owner.py:99 | general | EVE |
| R15 | [1/5] | 🟡 | Ten controller rows in tools/autopilot/source-map.json contradict themselves (evidence.status passed beside acceptance case status planned, "delivery evidence is still planned" and "AP00018 is on hold") because apply_successor refreshes only digest and evidence for existing rows, and test_helper_provenance_successor.py pins that | tools/autopilot/update_helper_map.py:606 | general | EVE |
| R16 | [1/5] | 🟡 | An authenticated existing workflow.open mutation skips staging admission: with 70 retained publication temporaries owner.acquire refuses but a new-request-id open still commits a revision, so the 64-file and 16 MiB bound and the unsafe-artifact refusal are not enforced in existing_open | plugins/autopilot/controller/autopilot_state/protocol.py:153 | general | EVE |
| R17 | [1/5] | 🟡 | The test isolation guard cannot see the controller's own I/O: it resolves audit open paths against cwd, so every dir_fd-relative open passes (a dir_fd walk reads the checkout's plugin.json under the guard), leaving "checkout inaccessible" proven for imports only, and the guard self-test probes only an absolute open | tests/autopilot/test_controller_export.py:68 | general | EVE |
| R18 | [1/5] | 🟡 | owner.finish_intent re-validates an intent that both callers validated one step earlier (prepare at line 80 and actors.read_intent), re-serializing a state of up to 14 MiB several more times per operation | plugins/autopilot/controller/autopilot_state/owner.py:185 | general | EVE |
| R19 | [1/5] | 🟡 | README prose heuristics in the export tests (heading parser and NEGATION regex) fail on any harmless "not" near the installed argv and pin wording instead of contract | tests/autopilot/test_controller_export.py:49 | general | EVE |
| R40 | [1/5] | 🟡 | 7 touched test(s) pass against the pre-change code: test_initialization_refuses_nonzero_revision_without_creating_state_or_backup, test_positive_stale_revisions_reject_transactions_and_restore_without_side_effects, test_real_process_cas_allows_exactly_one_writer_for_the_same_revision, test_restore_requires_backup_without_creating_or_changing_artifacts, test_security_identical_restore_advances_current_revision_and_preserves_security, test_store_refuses_aliased_state_backup_and_lock_artifacts +1 more | tests/autopilot/test_controller_kernel.py | general | mech-check |
| R41 | [1/5] | 🟡 | 8 touched test(s) pass against the pre-change code: test_kernel_accepts_independent_states_beyond_frozen_examples, test_kernel_actor_registry_rejects_three_valid_descriptors, test_kernel_owner_rejects_process_identity, test_kernel_review_cap_remains_two, test_kernel_revision_rejects_noninteger_text, test_kernel_revisions_and_epochs_reject_negative_values +2 more | tests/autopilot/test_controller_recovery_characterization.py | general | mech-check |
| R42 | [1/5] | 🟡 | 1 touched test(s) pass against the pre-change code: test_unrelated_arrays_and_original_owners_stay_byte_semantic | tests/autopilot/test_helper_provenance_real.py | general | mech-check |
| R43 | [1/5] | 🟡 | 1 touched test(s) pass against the pre-change code: test_without_a_successor_receipt_the_generator_behaves_as_today | tests/autopilot/test_helper_provenance_successor.py | general | mech-check |
| R20 | [2/5] | ⚪ | The operation and capability lists are hardcoded in two places — `protocol.public_contract` (plugins/autopilot/controller/autopilot_state/protocol.py:45) and the exporter — and a test pins the exporter's copy to a literal set. Tests therefore guard drift, but the bundle is not derived from the runtime: it can only drift through that test. Fix: derive the exporter's lists from the protocol-side definition, or at minimum point a comment at it so the coupling is explicit. | tools/autopilot/export-controller-contract.py:27 | 5 | ALICE, BLAKE |
| R21 | [1/5] | ⚪ | `assertTrue(tree(private_path(self.root)) == before, ...)` throws away the diff on failure. Use `assertEqual`. | tests/autopilot/test_controller_owner.py:139 | 3 | ALICE |
| R22 | [2/5] | ⚪ | The fail-first replay lists 22 touched tests that pass against the pre-change code. Most are PRD-required characterization of retained store, schema and CLI behavior, or no-regression guards, which is intended. One tests only the test harness's isolation guard, not product code: `test_controller_without_upper_layers_guard_denies_checkout_and_author_home`. It is useful scaffolding, but it pins no controller behavior and should not count toward `controller_without_upper_layers`. (mech-check: 2 touched tests in this file pass against the pre-change code, this one and test_controller_without_upper_layers_rejects_argument_misuse_without_state) | tests/autopilot/test_controller_export.py:434 | 5 | ALICE, mech-check |
| R23 | [1/5] | ⚪ | The diff range also carries unrelated documents: the engram PRD 00067, intake ideas 00065 and 00066, `plans/specflow-release-fast-path.md`, and a 497-line `meta/assumptions.md` change. None belongs to AP00018. They look like range pollution rather than implementation scope creep, and no code is affected. | N/A | general | ALICE |
| R24 | [1/5] | ⚪ | The workflow-v1.json `unavailable_capabilities` list declares IDs the PRD never names: `workflow.policy.v1`, `workflow.lifecycle.v1`, `workflow.tasks.v1`, `workflow.custody.v1` and `workflow.verification.v1`. The PRD names only core, jobs, reviews, records and optional waves. These are not advertised, so the impact is low. | plugins/autopilot/contracts/controller/workflow-v1.json:836 | general | BLAKE |
| R26 | [1/5] | ⚪ | store.py uses an absolute import (`from autopilot_state import schema`) while the sibling modules use relative imports. It works only because main.py's directory is on `sys.path`. | plugins/autopilot/controller/autopilot_state/store.py:43 | general | BLAKE |
| R27 | [1/5] | ⚪ | A failure after state publication reports a stale revision: apply_locked captures revision before the mutation, so when owner cleanup fails after _transaction_locked the response says recovery_required with revision N while durable state is N+1, and revision_hint only patches 0 | plugins/autopilot/controller/autopilot_state/protocol.py:166 | general | EVE |
| R28 | [1/5] | ⚪ | controller_without_upper_layers exercise_install runs only contract, fresh open and snapshot from the relocated install; owner.acquire, owner.release and owner.recover never run there | tests/autopilot/test_controller_export.py:462 | general | EVE |
| R29 | [1/5] | ⚪ | recover_matching accepts recovery_required after an intact crash and returns, so the PRD-named owner recovery test cannot fail if forward recovery regresses | tests/autopilot/test_controller_owner_recovery.py:66 | general | EVE |
| R30 | [1/5] | ⚪ | Characterization tests assert fixtures against literals: expected_error is compared to the constant "invalid_request" and contract_examples rejection is proven only with jsonschema, never with protocol.parse_request, while a state.json with an unowned field would yield recovery_required at the CLI | tests/autopilot/test_controller_recovery_characterization.py:57 | general | EVE |
| R33 | [1/5] | ⚪ | Only README and CHANGELOG are verified against the successor package_revision with git show; the 12 controller paths the successor certifies are checked against current bytes only in test_controller_assets_digest_current_bytes_and_cite_the_successor | tests/autopilot/test_helper_provenance_real.py:416 | general | EVE |
| R34 | [1/5] | ⚪ | The autopilot README recovery text is wrong in three places: "The next mutation then refuses." is unconditional though mutations succeed below the limits, the orphan procedure (line 425) does not say that stage and rollback files named by a pending credential-intent.json are not orphans, and "with its original credential" (line 432) contradicts rotated-operator recovery and omits that the request can be read from the intent file | plugins/autopilot/README.md:414 | general | EVE |
| R35 | [1/5] | ⚪ | The owner operations feature (feat commit f7cf82c) is logged under Fixed in the autopilot CHANGELOG; no Added entry says owner.acquire, owner.release and owner.recover exist and are advertised by --json contract | plugins/autopilot/CHANGELOG.md:39 | general | EVE |
| R36 | [2/5] | ⚪ | test_controller_store_guards_v2.py duplicates existing tests: two tests that pass at base are near copies of test_controller_kernel_adversarial.py lines 102 to 166, and the third guard test repeats test_controller_kernel.py's changed-guard test with a replacement mutator (mech-check: 3 touched tests in this file pass against the pre-change code) | tests/autopilot/test_controller_store_guards_v2.py:71 | general | EVE, mech-check |
| R37 | [1/5] | ⚪ | Unreachable branch in test_retained_historical_final_credentials_do_not_consume_staging_file_budget re-creates an owner credential if revocation removed it, which test_controller_owner.py line 44 asserts never happens | tests/autopilot/test_controller_staging_limits.py:549 | general | EVE |
| R38 | [1/5] | ⚪ | Fixture scenario oversized-response expects invalid_request, but every size refusal read in the code maps to recovery_required (actors.admit, schema._receipts, the protocol.apply_locked error mapping) and no CLI path can build a 65 KiB response; unprobed, needs the named unit check before aligning one side | plugins/autopilot/contracts/controller/fixtures-v1.json:2230 | general | EVE |

## Alice

Consensus lens, implementation-aware. Seven findings, two Medium and five Low:
R1, R8 (Medium); R2 (merged into R2), R20, R21, R22, R23 (Low).

Checks she ran herself: `python3 tools/autopilot/export-controller-contract.py
--check` exits 0; the README `sha256sum` pin (`7bef27ad...`) matches the
committed bundle; `python3 scripts/validate.py` passes. She did not rerun the
test suite. Function sizes are all at or under 47 lines. Files are all under 800
lines, `tools/autopilot/update_helper_map.py` largest at 774. No TODO, skip,
xfail or debug markers found.

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

## Blake

Blind lens, PRD-only prompt. He received no diff, no file list, no design doc
and no review history, and located the implementation himself. Two High, two
Medium, three Low: R3, R4 (High); R9, R10 (Medium); R24, R25, R26 (Low).

Verified clean by him: `--json contract` output matches
`plugins/autopilot/contracts/controller-v1.json` (same digests,
`package_version` 0.10.0 equal to plugin.json, operations and capabilities
identical); the README sha256 equals the bundle's actual `sha256sum`; the bundle
is a regular file with the exact six keys and the exporter refuses symlinks; CLI
signatures, flags and the seven error codes match the spec; fresh-open bootstrap
requires a null binding and revision 0; the operator credential is 0600 under a
0700 private tree and only its path is returned; credentials are compared with
`hmac.compare_digest`, replay is by request ID and digest, a conflicting payload
gives `invalid_request`, crash-recovery intents are validated; the Python 3.12
floor is enforced in main.py; the controller has no OVCAQ imports and no
subprocess use; MIT attribution to the pinned source commit is present in
store.py and paths.py. Narrow runs passed (test_package.py,
test_helper_provenance_real.py, test_controller_export.py: 41 passed) plus
`scripts/validate.py`. He did not rerun the full suite.

B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

Doubt lens on codex (static-only sandbox), dispatched with the inlined prompt
(678 KB: context, the scoped diff, and the persona with the two prescribed
edits). Thread `01a1c771-e08c-75b3-8404-4a4e69d4b028` is recorded for the next
cycle to resume. Two High, two Medium: R39, R5 (High); R1, R11 (Medium).

FIX: R5, R39, R11, R1 (his four findings above).
VERIFY: (none)
KNOWN: (none)

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Available (backend=copilot model=gemini-3.8-flash), exit 0, non-empty output.
Frontend and design specialist; this PRD ships a JSON-protocol CLI with no user
interface, so his specialty had no surface to judge and he reports no issues.

[CARL] ✅ No issues found

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

## Eve

Fifth lens (Fable 5), activated by the codex doubt-roster guard. The heaviest
contributor this cycle: two High, eight Medium, fourteen Low, with most findings
*probed* rather than read — she ran the CLI against real bindings in temp roots,
and checked CI through `gh`. Her first output carried the FIX/VERIFY/KNOWN
buckets and complete `D{n}` verdicts but omitted the mandatory `[EVE]` issue
lines; the one permitted format retry recovered them with every finding intact.

Her VERIFY item (R38) names a multi-step Python probe rather than one runnable
project command, so it was not queued — see the Cycle notes.

KNOWN (carried, not swept): all five `[MECH]` replay groups as PRD-ordered
characterization of retained v1 behavior; the identical-request intent
admission rule as design intent; the 4095/4096 receipt capacity tests as
unreachable through the protocol; and revoked owner credential files persisting
in `actors/` outside the 64-file budget as design intent bounded by receipt
capacity.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 37 findings
Tests: 1554 passed, 0 failed, 0 skipped (reused from last-verification.json at 1b588a7)

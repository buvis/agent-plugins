# AP00013 implementation assumptions

## 1: Characterize pinned helper semantics and ownership exclusions

- The "185 selected" controller-owned rows are the six exact-name test files test_{review_stage,rework_groups,custody,catchup_probe,verification,cap_check}.py, inferred from the exact count; the design does not define the selection.
- Helper-to-regression binding is by test-file name pattern; gate_lead has no own test file and maps to test_gate_findings_{shapes,unread_shapes,classification}, overlapping findings_section.
- "Pure" includes read-only Git and filesystem probes with explicit inputs (dirty_tree, log_sink_refusal, reuse_verdict, capture_range).

## 2: Extract finding parsing, lead stripping and deterministic grouping

- Tess: packaged table header is `| Ref | Consensus | Severity | Issue | File | Found By |`; other orders found by column name. Ref-less tables and bullets give `ref == ""`.
- Tess: modules import as top-level `findings`, `gate_lead`, `rework_groups` with `plugins/autopilot/scripts` on sys.path.
- Tess: `file_key("docs/x.md") == "prose"` (pinned folds markdown inside `group()`; packaged `file_key` folds it, grouping result unchanged).
- Tess: unknown severity label reads as `""` (pinned `_split_severity_cell`), not refused; bullet without "Found by:" keeps its last segment as the file.
- Tess: merged group `name_hint` is the shared directory with trailing `/`, or `mixed`; file groups use `file_key`.
- Tess: `group()` rejects non-emoji severity (`high`, `🔵`) per contract, diverging from pinned which accepted them.
- Ivan: critical group `name_hint` stays the citation-free path even for `.md` (private `_citation_free`); untested.
- Ivan: `N/A (reason)` also maps to general (pinned fullmatch regex kept).
- Ivan: invalid finding raises ValueError; table-row regex kept private.

## 3: Implement advisory AP00012 evidence consistency checking

- Tess: module imports as top-level `review_evidence`; mutated non-fixture inputs must match the oracle's defect set after outer outcome mapping.
- Tess: context shape failures report `schema_invalid`; `invalid_expected_context` is for well-formed but semantically wrong contexts.
- Tess: `check_evidence` reads only `.py`/`.pyc`/`.so` files and files under `plugins/autopilot/contracts`; reports survive a JSON round trip.
- Tess: float `schema_version: 1.0` inside AP00012 evidence left untested (oracle/jsonschema accepts it); duplicate-ID cases assert only `duplicate_id` membership.
- Ivan: JSON Schema "integer" follows jsonschema (bool never, integral float yes); policy `schema_version` and rework ints need a real int.
- Ivan: packaged policy is the source of normative values for policy checks; policy/schema checks return `schema_invalid` on KeyError/TypeError/AttributeError/IndexError.
- Pat LOW (not fixed): `policy_bindings_valid` uses `HEX64.search` without the `len==64` guard, so a policy digest with a trailing newline passes.

## 4: Port read-only dirty-tree and safe artifact path primitives

- Tess: `STORE_PREFIXES == {"docs/dev/project-management/", "docs/dev/tmp/"}`; `_store_roots` = show-prefix + each, in order.
- Tess: a committed `docs/dev/tmp/` change makes `_ancestor_and_clean` False (committed reuse tolerates management-store changes only).
- Tess: tests isolate git config (GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_NOSYSTEM=1, XDG_CONFIG_HOME) after Devon found the user's global excludes hid docs/dev/tmp.
- Tess: hidden-flag paths are dirt even unmodified and are not excused by `extra_excluded` (pinned).
- Tess: `_open_log_sink(log_path, root)` returns an unbuffered binary file; unlinks then O_EXCL-creates the leaf.
- Ivan: `_log_rel_and_tracked` uses `git ls-files -z -- :(literal)rel` with exact match (pinned `--error-unmatch` matched a directory with tracked files); git failure returns None (fail closed).
- Ivan: `refuse` catches the Python 3.12 symlink-loop RuntimeError and returns "is a symlink"; `_untracked_log_exclusion` still raises on a loop.
- Pat LOWs (not fixed): `_ancestor_and_clean` lets `_GitProbeFailed` escape (callers must catch OSError); duplicated try/except in `_dirty_outside_store`/`_dirty_check`; repeated show-prefix in `_ancestor_and_clean`; `_log_rel_and_tracked` does not catch RuntimeError.

## 5: Prepare isolated review artifacts and complete reviewer prompts

- Tess: refusals are dicts with `ok: False`, `schema_version: 1`; only PRD and tree mismatches assert `error == "invalid-input"`; tests use `tasks=[]` and a fresh `git init` project root each time.
- Tess: render_tasks/findings_precedent shapes pinned from the source (header, `\|` escape, newline to space, anchored heading, two fallbacks); `\r` in cells left untested.
- Tess: settled/prior/gate text must reach some non-Blake artifact (exact home unpinned); a bare artifact root outside the project, an extra unknown ref, a diff mismatch and artifact `kind` values are in-contract (unpinned).
- Ivan: refusal codes invalid-input, invalid-expected-context, persona-unavailable, unsafe-output, write-failed; undeclared input refs are refused; prompts also appear in `artifacts` with kind "prompt"; `pack_text` stages an extra `review-pack-ID.md`.
- Ivan: Blake's manifest is filtered in code to prd/card/repo-tree/rubric/test-results kinds; Eve's mechanical-checks block is the fixed text "(no mechanical test checks this cycle)" (no runner ported).
- Pat LOWs (not fixed): no owner (st_uid) check and no fstat re-validation after open (O_TRUNC); write-failed can leave partial output; settled ledger appears twice in alice/bob/carl prompts; `_staged_files`/`findings_precedent` run more than once; tasks/design/context/diff types and lone-surrogate or over-long cycle_id raise instead of refusing; `_cell` does not escape `\r`; CHANGELOG entry prefix style differs.

## 6: Prepare authenticated classified review-close proposals

- Tess: unpinned refusals (artifact mismatch, broken link, found_by mismatch, duplicate/conflicting refs, snapshot cycle mismatch, unknown classification) only need `ok` false, schema_version 1, a non-empty `error`; the order between link checks and the table cross-check is unpinned.
- Tess: chosen rows use the source shape (`ref?`, emoji severity, file, issue, classification, `found_by?`, `reason?`, `finding_ids`); clean evidence uses `## Consolidated Findings` with `None.`; a missing section is `findings_malformed` even with no rows.
- Ivan: refusal tokens chosen where tests leave them open: `invalid-evidence`, `review_artifact_mismatch`, `unknown_classification`, `snapshot_cycle_mismatch`, `attribution_mismatch`; a bookkeeping row is verify/discard with no `ref` and no `finding_ids`; a non-list `found_by` is a refusal, a missing one counts as zero finders.
- Ivan: a supplied snapshot is always validated and cycle-checked, and every task needs list-of-str `carry_refs` and an int `carry_cycle` (Pat MEDIUM, fixed in 3b3b7b5 with 5 regression tests); tail sweep keeps the source's `require_coverage=False` for the table check while evidence linkage still covers every finding.
- Pat LOW (not fixed): the fix commit 3b3b7b5 carries formatter reflow of seven unrelated sites in review_close.py (no behavior change).

## 7: Extract regression classification and pure custody proposals

- Tess: review text follows the pinned `findings_section._reviewed_keys` format; the output `line` is the first line of the deciding pair; `previous_head=""` counts as missing (returns `[]`); git runs through `subprocess.run(..., timeout=30)`; the custody notice keeps the source text and names the controller.
- Tess: the `capture_range` error type is `CapCheckError` or a module-defined `CustodyError`; `migration_records(None, ...)` keeps the source AttributeError; `capture_range` does not require the base to be an ancestor of HEAD (source parity).
- Ivan: `migration_records` keeps every dict decision because the pinned `render_report._is_pending` is not in the package (carry to the PRD-level review: port a pending predicate or document the deviation); the notice reads "Resolving custody requires the autopilot controller: run autopilot custody resolve."
- Orchestrator: Pat MEDIUM (an empty or annotation-only File cell returns regression=false, not null) was DISCARDED as source parity: the pinned `_pairs_verdict` (source/cap_check.py:337) returns the same, and the task says to keep the source null-versus-false unresolved-path behavior. Revisit at the PRD-level review if an empty cell should stall.
- Pat LOWs (not fixed): a line range like `a.py:1-999999999999` is expanded into an in-memory list before any git call (cap the span or iterate lazily).

## 8: Expose stateless optional catchup probes

- Tess: result keys are exactly `schema_version`, `gh`, `engram`, `skip` (named from the pinned source); only OSError and TimeoutExpired become `absent`, every other exception propagates; `check=True` and an `env` override are forbidden; the engram marker match is case-sensitive.
- Ivan: the CHANGELOG line sits after the cap-check/custody entry to keep task order.
- Pat LOW (not fixed): the gh token uses a nested conditional while the engram token uses an if/elif/else block (style only).

## 9: Execute bounded verification and assess explicit artifact reuse

- Tess: invalid timeout or argv may raise ValueError/TypeError or return ok=false (both accepted by the tests, no spawn, no writes); a completed run writes the artifact JSON to artifact_path equal to the returned artifact; `artifact.log.path` may be absolute or project_root-relative; scratch dir `docs/dev/tmp/` is excluded from run-time dirt; whether a failing-exit run is `reusable` is not asserted.
- Ivan: `reusable` is true only for a fully green run (exit 0, summary failed=0 and EXIT=0, not timed out, not capped, no dirt, HEAD unmoved); `exit_code` is null for a timed-out or capped run; invalid timeout or argv raises ValueError; the platform check runs before input validation (an unsupported host gets the refusal dict first); the source's SIGTERM/SIGINT/SIGHUP guards are not ported; stdout is read before stderr when both are ready, so the log order is deterministic.
- Orchestrator: Pat MEDIUM (no explicit unsupported-platform error) was confirmed against the contract and fixed in a92ac8f with a regression test.
- Pat LOWs (not fixed): `_parse_summary` repeats the summary key tuple next to `_SUMMARY_KEYS`; `_artifact` has six unannotated positional parameters.

## 10: Wire versioned local facade operations and controller refusals

- Tess: refusals from stage-review map invalid-input/unsafe-output/write-failed to exit 2 and other refusals (invalid-expected-context, persona-unavailable) to exit 1; `--verify` dirty-tree and head-moved may exit 1 or 2; `--controller-action` echoes OPERATION verbatim; live state means `docs/dev/project-management/autopilot/` of ANY project (executing host or the target root), refused without opening the file; the legacy capability array keeps its compact JSON format with the three legacy IDs first.
- Orchestrator: the legacy test `tests/autopilot/test_facade.py` pinned EXACTLY three capability IDs; the contract adds seven new IDs "only when implemented", so one assertion was relaxed to "legacy IDs first, then the new ones" (the only edit to that file, in the feature commit 44be3ee).
- Ivan: helper `TypeError`/`ValueError` from a call is a usage error (exit 2); every non-ok `prepare_close` result other than controller-required is exit 1; the first `--` splits the `--verify` argv; the facade sets `sys.dont_write_bytecode` before importing helpers because `python -I` ignores PYTHONDONTWRITEBYTECODE.
- Orchestrator: split hygiene reports `HELPERS` in test_local_boundary.py as UNUSED but test_local_boundary_state.py imports and asserts on it (single-file checker false positive); recorded as `split_hygiene: failed:...`, not fixed.
- Pat MEDIUM (live-state check compared path case exactly, so a case-varied path on macOS reached the live file) was confirmed and fixed in c3e7cce with a regression test that failed first.
- Pat LOWs (not fixed): `_check_evidence` calls its library functions without `_call`, so a malformed `--policy` may traceback (exit 1) instead of exit 2; `_read_json` reads any path (FIFO/device) without an S_ISREG check; `_COMPANIONS`/`_REQUIRED` tables and repeated flag-name formatting; long one-line expressions in `_stage_review` and `_run_operation`.
- Foreign edits seen in the work tree during this task (not mine, left uncommitted by me; the other party committed them as 4da2d68 and 65ea41b): review_stage.py subdirectory-root fix with a CHANGELOG Fixed entry and a test in test_review_helpers.py, PRD 00015 text, and reviews/00012-post-pin-source-drift.md. Earlier in the batch I reverted formatter-reflow changes with `git checkout --` after trusting the implementor's report rather than diffing each file first; I found no evidence that any foreign edit was lost, but the check was not made for those reverts.

## 11: Record helper provenance and document delivered capability limits

Orchestrator decisions for the unpinned contract (the tests encode these):
- `helper_dispositions` = {schema_version 1, source_commit, functions[], regressions[]}; function rows {key module:function, module, function, scope extracted|controller-owned, target_module, target_scenario, owner_scope helper-facet|controller-only, controller_exclusion, evidence}; regression rows {source_regression_id, key (module), disposition, target_scenario, owner_scope, controller_exclusion, evidence}. Regressions of modules with no controller-owned effects are `helper-facet`; regressions of mixed modules are `controller-only` ("the per-row helper split is not claimed, the module-level helper scenario carries the helper facet"). The covered set is the characterization's 601-row union.
- The generator also adds asset and `authored_file_owners` rows (owner 00013) for the 13 new helper files, refreshes the digests of autopilot.py, README.md and CHANGELOG.md, never adds the AP00018 controller files, never marks controller execution or any host profile passed. README.md and CHANGELOG.md rows keep the legacy self-referential delivery evidence with `tested_package_revision` from the receipts `package_revision`; other rows cite the receipts file. `--receipts` defaults to reports/00013-helper-delivery-receipts.json under the root when it exists.
- Ivan: scenarios per module, evidence test per module and the all-controller-owned rows using `controller_action_not_yet_wired` were chosen from file names and the characterization table, not by reading each test.
- Orchestrator: two legacy assertions in `tests/autopilot/test_package.py` pinned the pre-AP00013 state and were relaxed (capability array = legacy three first then the seven new IDs; authored owners = the 21 frozen 00012 rows unchanged plus 00013 rows). `test_content_roster_matches_frozen_inventory_and_actual_package_bytes` already failed before AP00013 because the held AP00018 controller files are not in the map; it still fails and is NOT an AP00013 regression.
- Pat MEDIUM (a helper-facet regression row of a mixed module was never rejected because the controller-key check compared module names with `module:function` keys) was confirmed and fixed in 7a07b82 with a regression test that failed first.
- Pat LOWs (not fixed): `SELECTORS["gate_lead"]` is unreachable (a subset of findings_section's files); regressions whose source path is in no selector are dropped silently; the duplicate-id check is written twice.
- Generated outputs: the real source map and the receipts file are coordinator commits (394fa65 and fbbdc3f), produced by `python3 tools/autopilot/update_helper_map.py --map tools/autopilot/source-map.json`, and `--check` exits 0 on the committed map.

## 12-15: Cycle-1 rework of the AP 00013 review

- Orchestrator (task 14): the `test_package` CI wiring test failed in three layers, all from Renovate PRs #8 and #11 merged in 6c1352c (the `plugins` job's setup-python pin, its Python 3.10 to 3.15, a new `generate_marketplace.py --check` step). The test now follows the `plugins` job; the `autopilot` job keeps its own v7.0.0 pin. Python 3.15 in CI is a foreign decision, left as is. The test stays brittle against the next Renovate bump of either job.
- Orchestrator (task 15): the facade capability test asserts the exact 3 + 7 operation list again.
- Tess/Ivan (task 12): `KNOWN_TIERS` = haiku, sonnet, opus; `batch_id` must be a nonempty string; live-state detection refuses any root whose path contains `docs/dev/project-management/autopilot` in any case; an artifact root outside the project is refused when any path component is a symlink. That last rule also refuses ordinary roots under macOS `/tmp` and `/var/folders` (Pat LOW, not fixed: the tests pin refusing a symlinked ancestor). The default staging root `docs/dev/tmp` inside the project is unaffected.
- Ivan (task 12): `_in_live_state` exists in both `autopilot.py` and `review_stage.py` because helpers must not import the facade (Pat LOW: one shared copy would stop drift). Per-job context files are named `{job}-review-context-{cycle}.md`; the shared `review-context-{cycle}.md` stays the full variant because older tests pin its text.
- Orchestrator (task 12): `test_review_helpers_contract.py::test_settled_prior_gate_and_precedent_inputs_reach_a_nonblind_artifact` passed at the base commit and failed after the first fix commit, because it relied on history text being rendered when the manifest lists no `history` ref, which finding R7 removes. It now grants alice the pack and history refs through the manifest (one test edited, count unchanged).
- Ivan (task 13): `_refusal` carries empty `task_proposals` and `decision_proposals` lists (additive wire change, read by the new tests); a snapshot task's `escalation_reason` only has to be a string, other values still end in `carry_unmatched`.
- Orchestrator: `tools/autopilot/source-map.json` was regenerated with `update_helper_map.py` and the receipts file's `package_revision` moved to 527d880 (the commit holding the final CHANGELOG and README bytes). The receipt test counts stay valid: the counted test files are unchanged except one edited test body.
- Pat LOWs (not fixed, tasks 12-14): precedent text is delivered twice to jobs that keep the pack (prompt block plus context file); `_stage_inputs` repacks eight values through two tuples to stay under 50 lines; `--config=path` style argv tokens are not checked for output overlap; `KNOWN_TIERS` is a local constant; `_store_symlink_targets_changed` is a one-line wrapper; `_backed` repeats one tuple comparison in two branches; cross-test-module imports of `context_with` and the marker constants.
- Peer incident: a second autopilot loop session (`agent-plugins-6d`) reviewed the same PRD in parallel and overwrote the untracked cycle-1 review file and ledger. Both were rewritten from the session that applied the decision gate; the other session's review is kept at `docs/dev/tmp/00013-review-01-by-agent-plugins-6d.md`. Its state writes (four decision entries) were removed; its `review_lenses` and rubric verdicts match this review.

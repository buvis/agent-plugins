# AP00013 helper source characterization

- Source: `buvis/claude-autopilot` at pin `e960ef1cc43e72bf92593b2f16c7a37c71ea7e48` (matches `tools/autopilot/source-pin.json`). Every file was read with `git show <pin>:<path>`, never from the working tree.
- Map: `tools/autopilot/source-map.json`, inspected only through bounded Python projections (counts, ids, digests). The full document was never printed.
- Scope: characterization only. It claims no target execution and no host certification. No shipped runtime file changed.
- Probes: copies of the pinned files were written to a session scratch directory. Each probe ran with `python3 -I` in a fresh `mktemp` root (`ap13-*`). No probe touched the live `docs/dev/project-management/autopilot/` of any repository.

## Per-helper table

All source paths are under `skills/run-autopilot/cli/`. The sha256 is over the exact blob bytes at the pin. "Pure/extracted" means the function computes from explicit inputs, or does read-only Git or filesystem probes, and can become a helper. "Controller-owned" means it writes state, journals, markers, locks or records, dispatches work, finds roots on its own, or runs a supervisor or script.

| Helper | Source path | sha256 | Pure / extracted | Controller-owned effects | Source regression IDs |
|---|---|---|---|---|---|
| review_stage | `review_stage.py` (949 lines) | `feb6a19329927be164493bfad70ac591e2f596afe7a20b632e6ece833cea32a3` | `render_tasks`, `_cell`, `findings_section` (pack precedent), `_prd_body`, `_run_inputs`/`_plan`/`_eve_inputs`/`_mech_checks` (per-persona input selection), `_section`, `_output_format`, `_incremental_block`, `_filesystem_notes`, `preflight_persona`, `render_roster` planning | `stage` (mkdir `docs/dev/tmp` under repo root), `_write_inputs` (writes files), `_gather` (`bash gather-context.sh`), `run_pack` (engram subprocess), `_run_script` (Popen), `run_gate_line`/`_gate_result_line` (verification gate and record), `_render_one` (`render_prompt.py` subprocess plus write), `_open_row` (`record_dispatch.py`), `_arm` (statectl state stamping), `_append`; imports `frontmatter, schema, state, statectl, verification` | 54 rows: `test_review_stage.py` 36, `_paths` 8, `_run_script` 4, `_run_script_signals` 4, `_gate_result_line` 1 (AP00020); `review-work-completion/scripts/test_skill_stages_via_review_stage.py` 1 (AP00016). Sorted-ID sha256 prefix `0a1b270fc8bbbeb8` |
| findings_section | `findings_section.py` (225) | `1eb19673286ac9a9ad0c965c28aa3239e5545cb789eb8a71c57aaed8cfcf2e17` | All of it: `_reviewed_keys`, `_section_bounds`, `_table_keys`, `_table_header`, `_row_from_table`, `_table_cells`, `_finding_key`, `_normalize_issue`, `_split_severity_cell`, `Row`; stdlib only (`re`, `typing`) | none | 125 rows in `test_gate_findings_{classification,real_fixtures,shapes,table,unread_shapes}.py`, all AP00020 (reached through `gate.py`, which re-exports these names). Prefix `10a6dada3829e53b` |
| rework_groups | `rework_groups.py` (140) | `4c6da5d06092303d48e1c27677e98440fc44aba5aa85adfa0df4ca8863af05ec` | All of it: `file_key`, `_dirs`, `_merge_pair`, `_cap`, `group`; stdlib only | none | 37 rows: `test_rework_groups.py` 34, `scripts/test_rework_groups_prose.py` 3, all AP00020. Prefix `3fd7f65b0f1c8e02` |
| gate_lead | `gate_lead.py` (93) | `7279a7f1a7c1c0b35f75019c6a6e7d813bd4b3104eccdbb73e1cf02701cef701` | `_strip_lead`; imports `findings_section._SEVERITY_EMOJI`, `re`, `unicodedata` | none | No dedicated test file. It is exercised through `test_gate_findings_{shapes,unread_shapes,classification}.py`: 89 rows, a subset of findings_section's 125, AP00020. Prefix `d264c0ef96ba5f33` |
| review_close | `review_close.py` (769) | `46b92bbf8435d22fb78f677a94bb2d62445fe4582d9f2ed5d10d673a323d84f1` | `_frontmatter_lines`, `_nested_pairs`, `_findings_block`, `_mutation_context`, `_add_decisions`, `_add_rework_tasks` (dict transform used inside the mutator), `_lens_states`, `_dispatch_outcomes`, `_no_verdict_refusal`, `_findings_refusal` (via pure `gate.findings_verdict`), `_carry_unmatched`, `_carry_reason`, `_severity_file_key`, `_matches_open_deferral`, `_single_voice_refusal`, `_found_by_count`, `_tail_sweep_preconditions` | `close` (orchestrates), `_close_mutator` + `statectl.mutate`, `_set_lens_state`, `_prelock_refusal` (`state.load` plus the `applied_review_batches` idempotency key), `_carry_refusal`/`_tail_sweep_refusal` (judge loaded live state), `_end_dispatch_rows` (subprocess dispatch end), `_read_review_file`/`_gate_review` (`gate.run_gate` reads the file); imports `gate, rework_groups, statectl, state` | 96 rows: `test_review_close.py` 21, `_apply` 18, `_carry` 15, `_lowsev` 7, `_tail_sweep` 11, `test_main_review_close_validation.py` 23, `scripts/test_phase_review_closes_via_review_close.py` 1; owners AP00020 72, AP00019 23, AP00016 1. Prefix `214d42bccbb44019` |
| cap_check | `cap_check.py` (421) | `70bf2215f50735545dc8d2ba83aee5840560871605074621e39c83499681555f` | `CapCheckError`, `_parse_number_list`, `_split_file_line`, `_clean_segment`, `_segment_lines`, `_normalise_path`, `_parse_file_cell`, `_missing_path_error`, `_unreadable_cell_error`, `_verify_range`, `_introducing_commit`, `_first_commit_touching`, `_file_exists_at`, `_pair_commit`, `_pairs_verdict`, `_classify_row`, `classify_findings` (read-only `git` via `_git`/`_toplevel`) | `rework_range`/`_head_sha`/`_read_text` derive heads from frontmatter and state rather than taking explicit heads (inferred from the `frontmatter` import and function names; bodies not read line by line). No writes found. | 41 rows: `test_cap_check.py` 33, `test_cap_check_cells.py` 8, all AP00019. Prefix `a7d9d655fdb21fae` |
| custody | `custody.py` (602) | `ad7222804b5a895e640a9ee4e95e39f1aebd53451e88d00fd9dfa58b78078b59` | `upsert_entry`, `marker_entry`, `refresh_hold_prd`, `_refresh_block`, `_insert_notice`, `_notice_prefix`, `migration_records`, `git_argv`, `capture_range` (read-only git), journal parsers `read_journal`/`_live_rows`/`unresolved_from_journal` | `marker_lock` (flock), `append_journal`, `compact_journal`, `pending`, `project_root`, `repo_and_git_dir`, `store_git`, `load_marker`, `write_marker` (unlink), `record_critical` (write), `mirror_mutator`, `_drop_mirror`, `_recorded_choice`, `_refuse_unless_clean`, `_reverted_targets`, `_pin_custody_branch`, `_apply_git`, `_cleanup`, `_resolve_locked`, `resolve`; imports `notify_out, records, render_report, schema, state, store_tree` | 134 rows: `test_custody.py` 34, `_entry` 8, `_loud` 12, `_prose` 16, `_prose_schema` 10, `_resolve` 19, `_stall` 16, `test_render_custody.py` 8, `test_store_tree_custody.py` 11; owners AP00020 115, AP00019 11, AP00021 8. Prefix `1a257dcd226c7ea9` |
| catchup_probe | `catchup_probe.py` (88) | `85db823ff1861ad72f4fc7ebb897a791a759558142aa817815935fb18d390e84` | `_run_probe` (injected `run`/`which`, 15 s timeout, explicit cwd), `_skips` | `probe` (`state.load`, per-batch reuse of `state.catchup_probe`, `custody.project_root` discovery, `statectl.mutate` write), `_utc_now`; imports `cli.custody, state, statectl` | 26 rows: `test_catchup_probe.py` 21, `test_catchup_probe_cli.py` 5, all AP00019. Prefix `58a4a1a4a7adb501` |
| verification | `verification.py` (758) | `828b0d5657640bd1138b5488f3a479e72a44a368c4d7e8c103394ea00f7222d1` | `normalize_command`, `_record_shape_ok`, `_parse_summary`, result constructors (`_timed_out_result`, `_lock_timeout_result`, `_head_moved_result`, `_dirty_result`), `reuse_verdict` (read-only git); runner mechanics (`_spawn_gate`, `_drain_bounded`, `_reap`, `_kill_gate`, `_SignalGuard`, `_deferred_signals`, `_pinned_parent_fd`, `_descend`, `_open_log_sink`) can move to an explicit-path runner | `run_gate` (lock, mkdir, open), `_acquire_lock`/`_lock_and_check` (workflow lock), `_write_record` (writes `last-verification` record), `_record_gate`, `_run_locked_gate`/`_gate_under_lock` (unlinks), `_refuse_verify_log_path` | 37 rows: `test_verification.py` 27, `_normalize` 5, `_reuse_verdict` 5, all AP00021. Prefix `2a83a2af25367781` |
| dirty_tree | `dirty_tree.py` (270) | `f5c42ec6ebec41a73cafc65cf8e73338866517d1d1d59fbf3781462f3dd664f3` | All of it is read-only: `_iter_porcelain_z_records`, `_dirty_path_is_in_store`, `_store_roots`, `_dirty_store_paths`, `_store_symlink_targets_changed`, `_dirty_outside_store_paths`, `_hidden_flag_edits`, `_dirty_outside_store`, `_dirty_check`, `_ancestor_and_clean`, `_log_rel_and_tracked`, `_untracked_log_exclusion` (`git` subprocess, no writes); depends on `cli.store_tree.STORE_PREFIXES` | none | 47 rows: `test_verification_dirty.py` 26, `_dirty_paths` 5, `_dirty_symlink` 9, `_hidden_flags` 7, all AP00021. Prefix `5da0f66c02c992ce` |
| log_sink_refusal | `log_sink_refusal.py` (175) | `a3ec1e3f9e4b0ed40a3023522fd1562f1639a26f0a3b9e1c8e40ec39b3a01040` | All of it is read-only: `refuse`, `_toplevel`, `_identity_targets`, `_identity_hit`, `_worktree_gitdir_pointer`, `_symlinked_component`, `_in_nested_repo` (`os.stat`, read-only git) | none | 4 rows: `test_verification_log_sink.py`, all AP00021. Prefix `cca766d677c1fe51` |

How the effect column was built: an AST walk listed the calls in each top-level function (`write_text`, `open`, `mkdir`, `unlink`, `replace`, `run`, `Popen`, `flock`) and the module imports. `replace` hits in `_cell`, `_normalize_issue`, `_finding_key` and `_clean_segment` are `str.replace`, so those functions are not effects. `gate.py` (sha256 not recorded here) imports only stdlib, `findings_section` and `gate_lead`, so its `findings_verdict` cross-check is pure.

The regression-ID column binds each helper by test-file selector. "Prefix" is the first 16 hex characters of the sha256 of the sorted IDs joined by `\n`. The union of all helper selectors is 601 distinct rows, because gate_lead's rows overlap findings_section's.

## helper_source_parity

Observed outputs are verbatim from the probes against the pinned code.

### Valid findings

- `findings_section._reviewed_keys`, table with a lowercase `r1` ref and an escaped pipe in the issue: `[["R1","high","src/b.py:10","Wrong Default | x"]]`, problem `null`. The ref is uppercased, the severity emoji becomes its word, display case is kept, and a later `## Next` table is ignored.
- Bullet shape `- [2/3] 🟠 wrong | default | src/b.py:10 | Found by: …`: `[["","high","src/b.py:10","wrong | default"]]`. The issue is right-split, so its own pipe stays in the issue.
- Word severity cell `high`: accepted as `high`.
- `_finding_key(" 🟠 "," src/B.py "," Wrong  Default ")` gives `["high","src/B.py","wrong default"]`. The issue is lowercased and whitespace collapses. File case is kept.
- `gate.findings_verdict` with a chosen row matching by ref: `["ok", null]`.
- `gate_lead._strip_lead`: `1. - [ ] 🟠 x` gives `🟠 x`, `<!-- c --> 🟡 y` gives `🟡 y`, U+3164 + `🟠 w` gives `🟠 w`, `` `code` 🟡 v `` gives `🟡 v`, and `(🔴) z` is unchanged (bare Ps/Pe brackets are excluded).
- `rework_groups.group` on seven findings (cap 4): critical `src/b.py` stays a singleton first; `N/A` (general) merges into the smallest code group `lib/e.py`; `src/a.py` and `src/c/d.py` merge into `src/`; `docs/x.md` becomes `prose`; `tools/f.py` stays alone. The input was unchanged afterward (`true`).

### Invalid findings

- Row missing its terminal pipe gives `[]`, `unreadable-table`.
- Duplicate `R1` refs give `[]`, `unreadable-table`.
- Header without a File column gives `[]`, `unreadable-table`.
- No `## Consolidated Findings` heading gives `[]`, `no-section`.
- `findings_verdict`, invented chosen finding: `mismatch`, "chosen finding absent from the review file's consolidated findings: 🟡 x.py | new".
- `findings_verdict`, consolidated row not covered by any chosen row: `uncovered` (naming R1). With `require_coverage=False` (tail sweep) the same input is `ok`.
- `findings_verdict`, chosen row matching by key but carrying no ref, against a table that has a Ref column: `uncovered`. Under coverage the source needs the ref.
- `findings_verdict`, Ref-less table with two rows of the same key: `ref-required`.
- `findings_verdict`, malformed table: `malformed` with the long header/rows detail.
- `gate.KNOWN_CLASSIFICATIONS` = `["verify","discard","fix","defer","carry"]`.

### Clean reviewer results (completed, no findings)

- `Verdict: converged` plus an empty `## Consolidated Findings` section plus `[]` chosen findings: `findings_verdict` gives `["ok", null]` and `VERDICT_RE` matches.
- With the section missing entirely and `[]` chosen findings, the result is `malformed` with the exact detail "no '## Consolidated Findings' section in the review file". `review_close._findings_refusal` exempts that exact string, so source `close()` goes on through the legacy no-section path instead of refusing. If the findings JSON is not empty, the detail differs and close refuses `findings_malformed`. The contract says not to inherit this escape hatch for AP00012 evidence.
- A missing verdict line is refused `no_verdict` before the shape gate (`_no_verdict_refusal`).
- Source completion comes from the review text: the verdict line plus `gate.check` against frontmatter `reviewers:`. It never comes from per-reviewer result records. The target must take completion from validated `reviewer_results` instead.
- `close()` itself was not run, because it needs `state.load` and `statectl.mutate`. This behavior comes from reading the code at L721-769 and L233-259 plus the pure `findings_verdict` probe.

### Stale PRD/code bindings

- PRD: source `_write_inputs` reads the PRD from a live path and stages `read_text().rstrip() + "\n"`. Probe: input ending `…PRD\n\n  \n` was staged ending `…PRD\n`, so `raw_equals_input_bytes = false`. The source has no PRD sha256 binding and no tree-sha check. A stale or changed PRD goes through undetected. The target's exact-bytes plus `prd_sha256` refusal is new behavior, not parity.
- Code: `verification.reuse_verdict` (probed in a temp git repo):
  - Green record at the same head: `reused`. A later commit that only touches `docs/dev/project-management/`: `reused`.
  - Dirty `src.py`: `stale`, and `_dirty_check` gives `(True, ['src.py'])`. A committed code change: `stale`. A non-ancestor record sha: `stale`. A 12-character sha: `stale`. `failed=1`: `stale`. `None` record: `stale`.
  - `normalize_command(" make \t test ")` gives `"make test"`. The source collapses whitespace inside the command. The contract forbids whitespace normalization of argv, which is a known divergence.

### Blind input exclusions

- `review_stage._plan("blake")` gives Blake only `PRD` (`run["prd_body"]`), the blind `RUBRIC`, `OUTPUT_FORMAT`, the `Test gate` section and `_filesystem_notes(root)`. Blake never gets the context file, diff, pack, checklist, history, ledger or incremental block. Eve and Bob get pack findings; Bob also gets Eve's doubt appendix and the citation line.
- Probe of `_prd_body` with a raw sibling present, where the PRD contains a literal `## Design Doc` heading and a design doc was appended to the merged file: the blind body kept the literal heading (`true`) and excluded the design (`true`).
- Without the raw sibling, the source falls back to splitting on `"\n\n## Design Doc\n\n"`. Design is still excluded, but the PRD's own literal-heading content is cut off (`fallback_split_keeps_literal_heading = false`). The target must stage the raw PRD and drop this fallback.
- `_filesystem_notes` puts the absolute project root and the store realpath into Blake's prompt when the store is a symlink or the root is a dot-directory. That is a path leak against the contract's "never ... broad context path" isolation rule, and it is flagged for the staging task.
- `render_tasks` escapes pipes and folds newlines: `| T1 | a \| b c | done |  |  |  |`. The pack precedent stops at a same-or-higher heading (`P1\n### sub\nP2`). With no section the result is `(the pack has no Findings precedent section)`. With no pack the result is `(no pack available this cycle)`.

### Probe fallbacks (catchup_probe)

| Case | Result |
|---|---|
| gh exit 0 | `ok` |
| gh exit 1 | `unauthenticated` |
| gh binary missing | `absent` |
| gh `TimeoutExpired` | `absent` |
| gh `OSError` | `absent` |
| engram stderr has `not inside a registered repo` | `unregistered` |
| engram exit 2 with other stderr | `ok` (the source's odd fallback) |
| engram exit 0 | `ok` |

- Timeout is 15 s. `_skips` gives `["github-state","engram"]` when both fail and `[]` when both are ok.
- The verdict mapping was copied from `probe()` L81-84, because `probe()` itself writes state and was not called.

## Target-ownership recheck

The map was rechecked live (bounded projection; `helper_dispositions` key absent; 0 rows have `delivery_prd` `00013`).

- The 185 preexisting controller-owned selected rows were reproduced exactly. They are the exact-name test files `skills/run-autopilot/cli/test_{review_stage,rework_groups,custody,catchup_probe,verification,cap_check}.py`:

  | Test file | Rows | Owner |
  |---|---|---|
  | `test_review_stage.py` | 36 | AP00020 |
  | `test_rework_groups.py` | 34 | AP00020 |
  | `test_custody.py` | 34 | AP00020 |
  | `test_cap_check.py` | 33 | AP00019 |
  | `test_verification.py` | 27 | AP00021 |
  | `test_catchup_probe.py` | 21 | AP00019 |

  All are `owner_repository: buvis/agent-plugins`, `disposition: replaced`, with no duplicate IDs. The sha256 of the sorted IDs joined by `\n` is `be27d9036a716e0140bd128010c842b2a4bf68d96c44a49d3fae74067759501d`.
- Conflicts: every one of those 185 rows conflicts with a blanket helper port. They are **skipped and reported, not reassigned**. A later helper task may only append `helper_dispositions` entries that reference them.
- 416 more helper-related rows (601-row union minus the 185) are also already owned by AP00016, AP00019, AP00020 or AP00021, per the table above. They are treated the same way: skipped, reported, never reassigned.
- No helper regression row is free for AP00013 to claim. AP00013 parity evidence must be recorded as additional dispositions, never as an owner change.

## Known source-versus-contract divergences

These inform later tasks; this task does not resolve them.

1. Raw PRD bytes are trimmed (`rstrip()+"\n"`), and the source has no `prd_sha256` or tree binding.
2. `normalize_command` collapses argv whitespace.
3. Legacy no-section close escape hatch.
4. Blake filesystem notes leak the root path.
5. `catchup_probe.probe` caches the result in state per batch.
6. Completion comes from the verdict line and frontmatter, not reviewer results.
7. `rework_range`/`_head_sha` infer heads rather than taking them explicitly.

## Method notes

- Pure modules (`findings_section`, `gate_lead`, `rework_groups`, `gate`) and `cli.verification`/`cli.dirty_tree` (with pinned `store_tree.py`) were imported unmodified from the scratch copies.
- `review_stage.py` and `catchup_probe.py` were loaded by AST with only their runtime imports (`from . import …`, `from cli import custody, state, statectl`) removed, then `exec`'d in a throwaway namespace. The function bodies were not changed.
- Not run: `review_close.close`, `review_stage.stage`, `cap_check.classify_findings`, and all of custody's effectful functions (they need runtime `state`/`statectl` or live Git topology). Their behavior here comes from reading the code statically.

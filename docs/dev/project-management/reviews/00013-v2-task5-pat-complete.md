# Task 5 Pat review — complete scope, findings remain

Native Sonnet claude-sonnet-5-5/high, tool-less session
5f560368-70d2-459e-b9ec-257a789d8070, product HEAD 8d5c325.
The first 37660-byte message supplied production, changelog and existing-test
changes; its scope omission was rejected. The 36460-byte continuation supplied
the complete new test module and explicitly withdrew the exclusion. The exact
union is the full 38620-byte task diff across all five changed files. No code
changed between messages. This completes initial review scope, not a clean
verdict or another PRD review cycle. Parse-review exit 0; one MEDIUM and eight
LOW findings remain. All six quoted consolidated findings have closure rows.

CLOSURE | resolved | "The ownership-window defect ... `_open_result_sink` decides 'this run created the leaf' with a separate `artifact.exists()` ... identity from a later `os.lstat` by name ... also the artifact write/close failure leaving a reusable record, the spawn-failed empty-log residue, the unguarded `os.close(pin[0])`, the un-restorable truncated pre-existing artifact (out of scope)" | `_acquire_sink` takes creation from `O_CREAT|O_EXCL` and identity from `fstat` on the descriptor, and `_close_pin` guards the parent-fd close. The new tests exercise each obligation: `test_an_absent_log_stays_absent_after_a_failed_spawn`, `test_an_artifact_leaf_survives_only_when_it_existed_before...`, `test_a_different_file_that_took_the_artifacts_name_survives...` and the write/close reuse-verdict test. The restore case stays out of scope.

CLOSURE | resolved | "Two more v1 tests fail because _open_log_sink changed contract ... test_sink_opener_creates_parents_and_a_fresh_unbuffered_binary_file and ::test_sink_opener_refuses_symlinked_parents_and_replaces_symlinked_leaf" | The default `_open_log_sink` is back to unlink plus `O_CREAT|O_EXCL`, and the non-destructive mode is the separate `preserve=True`. Both legacy nodes are unchanged and green in the recorded 223-passed run.

CLOSURE | resolved | "`_worktree_gitdir_pointer` reads any in-repo file that is the same inode as a sibling `.git` file, for example a nested repo's pointer" | The guard `if resolved.parent == toplevel else None` is in place. `test_refuse_calls_a_nested_repositorys_git_pointer_outside_without_reading_it` covers it with two nested pointers and the real worktree pointer as a control.

CLOSURE | resolved | "Late sink failures do not terminate surviving process-group descendants" | `pgid` is retained and `_kill_group` runs on close failure and on write failure. `test_a_late_artifact_close_failure_ends_the_descendant_the_child_left_running` uses a real surviving descendant, with a control test showing it does write its marker when no sink fails. The log-close and write-failure kill branches are not driven (see LOW below).

CLOSURE | resolved | "`_open_log_sink`'s post-open validation checks `S_ISREG` and `st_nlink == 1` but not the executable bit" | `preserve=True` validation now includes `or info.st_mode & 0o111` on the opened descriptor. The `executable`, `hard-linked` and `swapped-file` cases in `test_a_log_is_judged_by_the_file_opened_not_by_the_path_judged_earlier` each refuse with `sink-failed` and no spawn.

CLOSURE | resolved | "neither new test file drives `run_verification` with a symlinked `project_root` ... against a resolved-spelling `log_path`/`artifact_path`" | `test_a_run_is_accepted_when_the_root_and_the_output_paths_are_spelled_differently` and `test_a_tracked_log_is_refused_under_every_spelling_of_the_project_root` drive `run_verification` through `gate_at` with `child_argv` and a spawn marker, with a real symlinked root. The first accepts under both mixed spellings and the second refuses pre-spawn (`unsafe-artifact-path`, no marker).

MEDIUM | plugins/autopilot/scripts/log_sink_refusal.py:146 | The new alias escape in `_symlinked_component` (`not current.is_relative_to(repo_root) and current.resolve() in stops`, then `break`) also stops the walk at a symlink below the root when the path uses the resolved spelling. Example: `repo_root=/tmp/repo`, log `/private/tmp/repo/sub/x.log`, with `sub` a symlink to the repo root. `/private/tmp/repo/sub` is not relative to `/tmp/repo`, and its `resolve()` equals `repo_root.resolve()`, so the walk breaks and does not refuse. The unresolved spelling `/tmp/repo/sub/x.log` is refused. The `_pinned_parent_fd` fallback then resolves the parent and opens the root, so the sink is written through a symlinked component. This breaks criterion 8. No test in the new module covers a below-root symlink under an aliased root, so the suite does not catch it. | Apply the escape only when `current` is outside both spellings: `not current.is_relative_to(repo_root) and not current.is_relative_to(repo_root.resolve()) and current.resolve() in stops`. Add a resolved-spelling alias test with a below-root symlink, asserting `unsafe-artifact-path` and no spawn.

LOW | plugins/autopilot/scripts/verification.py:326 | `_acquire_sink` closes the exclusive-create descriptor before `_open_log_sink(preserve=True)` reopens by name, then compares inode numbers. In that window the created inode can be freed and its number reused, so the identity check could match a different file. | Keep the first descriptor open until the reopened sink's `fstat` has been compared, then close it.

LOW | plugins/autopilot/scripts/log_sink_refusal.py:99 | `resolved.parent == toplevel` is a string comparison. On a case-insensitive volume a case-aliased parent spelling would skip the pointer read. | Compare with `os.path.samefile` or a normalized path if case aliases of the pointer matter here.

LOW | tests/autopilot/test_helper_rework_sinks.py:~227 | `test_a_failed_artifact_write_or_close_leaves_nothing_reuse_verdict_accepts` runs a green first run, so the artifact already exists when the write or close fails. It only covers the "existing leaf is emptied" branch. The "leaf created by this run is unlinked after an untrusted write or close" branch (`pin[3]` with `untrusted`) is untested. | Add a case where the artifact is absent before the run, and assert it is gone and `reuse_verdict` is `stale`.

LOW | tests/autopilot/test_helper_rework_sinks.py:~253 | The real-descendant test breaks only the artifact close. The log-close branch in `_execute` and the artifact write-failure branch also call `_kill_group` but are not exercised. `swap_log_before_open` only targets an existing leaf, so the "created, then swapped before reopen" mismatch branch is untested too. | Parametrize the descendant test over a log-close failure and a write failure. Add a case where the swap happens on an absent log.

LOW | tests/autopilot/test_helper_rework_sinks.py:~375 | Nothing asserts that the group id stays out of returned reports (criterion 6). `pgid` now sits in the `run` dict that feeds `_artifact`. | In the accepted-run tests, assert `"pgid" not in json.dumps(report)` and that it is absent from the stored artifact.

LOW | plugins/autopilot/scripts/verification.py:307 | `_Pin` is a 4-tuple accessed as `pin[0]` and `pin[3]`. `_unlink_pinned` and `_empty_pinned` repeat the same lstat-and-identity prologue. | Use a `NamedTuple` and share one identity-check helper.

LOW | plugins/autopilot/scripts/log_sink_refusal.py:211 | `_open_log_sink` tests `if preserve:` twice, in two separate blocks. | Branch once, or move the validation into the first branch.


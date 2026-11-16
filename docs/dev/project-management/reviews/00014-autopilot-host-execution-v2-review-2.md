---
prd: docs/dev/project-management/prds/wip/00014-autopilot-host-execution-v2.md
review: 2
date: 2026-11-16
head_sha: 949af1a01ada89b05cdb2a9c295d68db25810c88
codex_thread_id: 01a1e166-515a-79f3-ac3f-6907494e402d
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: e24e916f
  carl: ecef313e
---

# Review: 00014-autopilot-host-execution-v2

Diff range: `a133498261a65eed36ce0d9516770626c7955b2a..949af1a01ada89b05cdb2a9c295d68db25810c88`

codex_rung_guard: not fired

## Review Summary

Reviewed: 17 completed tasks (13 original + 4 cycle-1 rework tasks)
PRDs checked: 00014-autopilot-host-execution-v2.md

### Agent Status
- Alice: available (Claude subagent, consensus lens)
- Blake: available (Claude subagent, blind lens, PRD-only)
- Bob: available (codex, doubt lens D1-D5 + de-slop, resumed cycle-1 thread)
- Carl: available (gemini via copilot backend, model gemini-3.8-flash, UI/design lens)

pack: ok

### Notes on this cycle

- Incremental review (cycle 2), diff scoped with `--since a133498261a6` to the
  cycle-1 rework commits only.
- **The gate is red at this HEAD.** `review-stage` ran the PRD exit-criteria
  command and it exited 1: `14 failed, 1869 passed in 658.38s`
  (`docs/dev/tmp/gate-c2-20261116.log:369-384`). Cycle 1 recorded
  `1848 passed, 0 failed`, so every one of the 14 failures entered with the
  cycle-1 rework. `review-stage`'s parser matched no counts line in the `-q`
  output and reported
  `Tests: counts unavailable (suite run this cycle, exit 1, ...)`; the counts in
  the `Tests:` line below are read verbatim from that same run's log. No
  second suite run was performed, because `autopilot verify` uses the same
  parser and would have produced the same no-counts record at an 11-minute cost.
  This is the same parser quirk the cycle-1 review recorded.
- Carl independently ran `tests/autopilot/test_package.py` and
  `test_facade_session_roles.py` in his own environment and reproduced the
  README-digest failures (2) and the role-resolution failures (9 subtests).
- Bob's first dispatch failed before reaching the model: the inlined prompt was
  1,643,108 characters against codex's 1,048,576 limit. His retry used an
  inlined prompt of 413,336 characters, built by omitting two paths from the
  inlined diff only - `tools/autopilot/source-map.json` (1051 changed lines of
  machine-generated digest churn) and everything under
  `docs/dev/project-management/` (this PRD's own review and ledger artifacts).
  The omission is stated in his prompt. Every source, test and contract file in
  the rework range was inlined in full. His dispatch row is closed
  `ok --detail retry`.
- `consolidate_findings.py` warned that seven rows merged citations matching
  only after suffix stripping (rows 1, 2, 3, 4, 6, 7, 8). Each merge names the
  same defect in the same file at a neighbouring line.
- The five `[MECH]` fail-first replay lines are carried as their own rows
  R37-R41: no consolidated row names the same test file *and* the same test
  names, so none absorbed them.
- Two Blake re-raises were auto-dismissed against the settled ledger; both are
  listed under "Auto-dismissed (ledger)" below.
- Bob's VERIFY bucket is empty, so this cycle queues no verification checks.
- Cycle 1's queue file (`-checks-1.json`) does not exist, so no failed check was
  carried forward.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/4] | 🟠 | The R13 fix is wrong. `_resolve_roles` now forces `gemini_cli_available=True` for `codex-gemini` + `full`, overwriting the caller's `--facts` file. That adds Carl, not Eve. The comment says Eve and Blake complained about the missing Eve, but Eve's predicate is `doubt_reviewer == "fable"` or `implementor_codex_present`. Design §6 pins that `gemini_cli_available=False` makes Carl not mandatory. This breaks 4 tests: test_facade_session_roles.py::RoleAndSessionModesTest test_resolve_roles_reports_each_real_profile_and_lane, test_resolve_roles_defaults_equal_all_false_facts, test_resolve_roles_adds_eve_for_a_fable_doubt_reviewer_or_a_codex_implementor and test_resolve_roles_reports_blocked_when_a_host_lacks_a_required_capability. Revert it. If Eve should show for this profile, derive `implementor_codex_present` from the profile the way `--diagnose` does, and only when the facts file does not set it. | plugins/autopilot/scripts/autopilot.py:293 | Phase 1 task 3 | ALICE, BLAKE, CARL |
| R2 | [3/4] | 🟠 | The Gemini live probe can record identity and isolation as observed from the prompt text alone. `run_live_gemini` prompts "Probe tag: --record-session gemini-<i>" and takes the "session id" from the first `--record-session (\S+)` match in stdout. A host that echoes the prompt yields `gemini-0` and `gemini-1`, which count as distinct sessions, so identity and isolation read `observed` without any native session id. The prompt never asks the host to run `autopilot.py --record-session`. The fake in tests mints its own id, so no test shows the real-host path. Have the child run the real `--record-session` command and parse its output, or take the id from a host-reported field. | tools/autopilot/probe-host.py:173 | 9 | ALICE, BLAKE, BOB |
| R3 | [3/4] | 🟡 | tests/autopilot/test_interception.py grew to 970 lines, past the 800-line limit (the rework added about 200). Split the render-reply and push-grammar classes into their own file. | tests/autopilot/test_interception.py:970 | 5 | ALICE, BOB, CARL |
| R4 | [2/4] | 🔴 | The R11 fix makes every controller-keyed duty refuse with `missing_controller_seam` when the session is unbound. The change removed the unbound-skip in `evaluate_hook` and made `_evaluate_duty_call` refuse when `not bound or seam is None`. Design §8 (design lines 760-761) says unbound sessions skip these duties. Design line 1239 says "Unbound projects see only the local pure duties". Once activated, the hooks would deny every `git push` in any repo without `.autopilot/controller`. They would also block every Edit through state_integrity, every Stop through review_completeness, live_job and departure, and refuse SessionStart. The probe's unbound control run now cannot push, so 4 probe tests fail with `control_did_not_execute`: test_host_argv.py::ProbeHostLiveRunTest (2) and test_host_argv_failed_runs.py::ProbeHostFailedRunTest (2). Restore the unbound skip. If Blake's R11 is accepted, put the decision in the design first. The tests were rewritten to pin the new behavior (test_interception.py:127-182, 870-886). | plugins/autopilot/scripts/interception.py:154 | 5 | ALICE, BOB |
| R5 | [2/4] | 🟠 | R7/R18 is fixed for Codex only. `claude.py` no longer aliases `codex.render_hook_reply`. It now has its own copy with the old weak shapes (claude.py:126-150). PostToolUse refused emits `systemMessage` instead of `{"decision":"block"}`. A Stop refusal with `stop_active` emits nothing. A SessionStart refusal emits nothing. PreToolUse deny uses `denied[0]` only. The design says the shapes are "identical for both hosts", and Claude is the primary intercepting host. `test_pre_tool_deny_carries_the_first_denied_reason` and `test_post_tool_failure_is_reported_without_blocking` were narrowed to Claude, so they pin the divergence (test_interception.py:712-745). Delete the Claude copy and restore the alias, or copy the Codex body. Run the contract tests against both hosts. | plugins/autopilot/scripts/claude.py:126 | 6 | ALICE, BOB |
| R6 | [2/4] | 🟠 | The README edit was not re-sealed. `plugins/autopilot/README.md` changed, but the `source-map.json` digest and the delivery evidence were not regenerated for it (diff of tools/autopilot/source-map.json:7341 onward). That fails 4 tests: test_package.py::TargetPackageTest test_content_roster_matches_frozen_inventory_and_actual_package_bytes and test_readme_retains_every_source_heading_with_completed_adaptation_receipts, and test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes and test_generator_check_accepts_the_committed_map. The error is "successor package_revision ... is stale for plugins/autopilot/README.md". Run the `update_helper_map` re-seal after the last edit to that file. | tools/autopilot/source-map.json | 12 | ALICE, CARL |
| R7 | [2/4] | 🟠 | `hook-v1` was added to `_CAPABILITIES` (R26 fixed), but test_local_boundary.py's operations list was not updated. test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations fails with 19 != 3 + 15. test_facade.py and test_package.py were updated; this file was missed. | tests/autopilot/test_local_boundary.py:245 | 10 | ALICE, BOB |
| R8 | [2/4] | 🟠 | R3/R15 is only partly fixed in `is_git_push`. The wrapper-option allowlist (`_FLAG_WITH_VALUE = -u -g -n -C`, `timeout` takes one positional) is open-ended, so unknown wrappers still fail open. I ran it: `timeout -s KILL 5 git push`, `sudo --user x git push`, `sudo -h host git push`, `ionice -c 2 git push`, `stdbuf -o0 git push`, `exec -a x git push`, `/usr/bin/env git push` and `FOO="a b" git push` all return False. The design §7 says the push check must be a conservative superset. A scan of each segment for any token named `git` followed by `push` would close all of these, and a false positive is cheap. The new test cases (test_guards_pure_duties.py:557-566) cover only the spellings the fix handles. | plugins/autopilot/scripts/guards.py:329 | 4 | ALICE, BOB |
| R9 | [1/4] | 🔴 | The rework leaves the gate red: 14 failed, 1869 passed at HEAD (gate-c2-20261116.log). The prior cycle was 1848 passed, 0 failed, so all 14 failures are regressions from the rework. Five causes, listed as separate findings below: unbound refusal (4 probe tests), the R13 resolve-roles fix (4 tests), guards.py `while True` (1), README digest not re-sealed (4: 2 in test_package.py, 2 in test_helper_provenance_real.py), and the missing `hook-v1` in the test_local_boundary.py operations list (1). | N/A | general | ALICE |
| R10 | [1/4] | 🔴 | Phase 2 task 3 is unmet. The suite at HEAD has 14 failures (1869 passed), and `tests/autopilot/test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes` still fails, which was the open CRITICAL R1 from v1. The cause is `plugins/autopilot/README.md`: the source-map digest is 3ce9d328..., the current bytes hash to ca110114..., and README was last changed by 30fb2c2 after the map was sealed. `test_generator_check_accepts_the_committed_map` fails with "successor package_revision d6f014f9... is stale for README". `test_package.py` fails on the same digest in two tests (`test_content_roster_matches_frozen_inventory_and_actual_package_bytes` and `test_readme_retains_every_source_heading_with_completed_adaptation_receipts`). The PRD exit criterion (full pytest) is therefore not met. | plugins/autopilot/README.md | Phase 2 task 3 | BLAKE |
| R11 | [1/4] | 🔴 | The shipped hooks deny unrelated work in every project. `interception.run_hook` always calls `evaluate_hook(..., seam=None)`, and the package contains no seam. I ran `--hook claude --event PreToolUse` against an unbound `/tmp` repo and the results below follow. They are caused by one condition: every controller-keyed duty refuses when the session is unbound or has no seam, with no check that autopilot is involved. A Skill call for the non-autopilot skill `commit` is denied with `missing_controller_seam`, because `post_handoff` needs controller facts. `git push origin x` is denied in an unrelated unbound repo. Every Stop event is blocked once with three `missing_controller_seam` reasons. The spec says to refuse "unsafe bound operations". This refuses unbound and unrelated ones too. | plugins/autopilot/scripts/interception.py:156 | Phase 1 task 2 | BLAKE |
| R12 | [1/4] | 🔴 | The live host probe cannot observe interception, because the real guard denies the unbound control push. `probe-host.py` requires the unbound `control/` push to land on the remote (`control_did_not_execute` otherwise), but the real hook refuses any unbound push. Five tests fail on this: `test_probe_control_is_unbound_inside_a_bound_source_repo`, `test_relocated_host_probe_observes_identity_isolation_interception`, and three in `test_host_argv_failed_runs.py`. Each reports `control_did_not_execute` where it expects `observed`. `relocated_host_probe` and `missing_guard_refused` therefore do not pass, and no real host could ever earn an interception claim. | tools/autopilot/probe-host.py:156 | Phase 2 task 1 | BLAKE |
| R13 | [1/4] | 🟠 | The new `_normalize_rel` uses `while True` (guards.py:165). That trips test_compatibility.py::NoCoordinatorRuntimeInPluginTest::test_no_ap00014_module_file_contains_a_coordinator_runtime_pattern, because the "no coordinator runtime" test scans `guards.py`. Use a bounded loop over `PurePosixPath(root).parents`. The ancestor walk also reduces any absolute path to a root-relative one when `project_root` is deep, so a sibling `/x/backlog/f.md` outside `/x/y` is denied. The design says an absolute path outside the root keeps the whole-path store check, so this contradicts it. | plugins/autopilot/scripts/guards.py:165 | 4 | ALICE |
| R14 | [1/4] | 🟠 | The Claude hooks are not wired into the package. `plugins/autopilot/plugin.json` has no `hooks` field, and CHANGELOG line 9 says the assets "are not activated". Both `contracts/hosts.json` and `compatibility/claude.json` still declare `interception` capability with `activation: client-manifest-hooks-field`. The spec says to "retain Claude hooks through supported packaging". This is the old R3/R4 gap, only partly documented, and the capability constants still overstate the state. | plugins/autopilot/contracts/hosts.json:7 | Phase 1 task 2 | BLAKE |
| R15 | [1/4] | 🟠 | The Codex compatibility asset uses a Claude-only placeholder. `compatibility/codex/hooks.json` runs `"${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py"`, and the generator hardcodes the string. The probe hand-substitutes it for Codex (`probe-host.py:96`), so the shipped Codex asset cannot resolve on Codex as written. The spec forbids Claude-only variables outside declared adapters. | tools/autopilot/build-compatibility.py:33 | Phase 1 task 2 | BLAKE |
| R16 | [1/4] | 🟠 | The role-resolution repair changes the wrong fact: forcing `gemini_cli_available=True` adds Carl, not Eve, and overrides an explicitly supplied false value. Four role CLI tests fail. Remove this override; address Eve through the policy’s implementor predicate without falsifying host availability. | plugins/autopilot/scripts/autopilot.py:293 | 14 | BOB |
| R17 | [1/4] | 🟠 | Prior R4 remains partly unresolved: adapters still receive neither the discovered binding root nor the supplied hook environment. Walking arbitrary ancestors in `_normalize_rel` guesses a root instead of using the binding, while Claude still reads process-global child-session state. Pass the binding root and hook environment into translation and test both independently. | plugins/autopilot/scripts/interception.py:174 | 14 | BOB |
| R18 | [1/4] | 🟠 | Prior R5 fixes exclusive creation but leaves parent traversal unprotected. `_write_request_file` opens an absolute pathname after resolution and creates parents through pathname operations; a parent replacement can redirect creation outside the validated root. Create through the existing pinned directory descriptor and add a parent-swap regression. | plugins/autopilot/scripts/jobs.py:450 | 14 | BOB |
| R19 | [1/4] | 🟠 | Gemini success classification ignores invocation failures and conflates identity with isolation. Distinct stdout markers can yield observations despite non-zero exits or timeouts; identical valid sessions incorrectly lose identity. Check invocation outcomes first, observe identity independently, and report auth failures and unavailable interception using the specified statuses. | tools/autopilot/probe-host.py:173 | 15 | BOB |
| R20 | [1/4] | 🟠 | The added Claude/Codex recording command uses `--project-root <run_dir>`, but its trace is under `<run_dir>/project/docs/...` or `<run_dir>/control/docs/...`. The trace writer rejects both locations against that root. Build the command per invocation using its cwd, and verify an identity trace when hooks do not load. | tools/autopilot/probe-host.py:220 | 15 | BOB |
| R21 | [1/4] | 🟠 | The recording command interpolates executable and project paths without shell quoting. Spaces break execution, and shell metacharacters in a project path can become executable syntax. Construct the command with `shlex.join` over explicit arguments. | tools/autopilot/probe-host.py:220 | 15 | BOB |
| R22 | [1/4] | 🟠 | Prior R22 remains unimplemented: neither probe prompts nor observation logic exercise parent and nested Agent dispatches. Add the bounded child-lineage scenario and require an allowed parent dispatch plus a nested `recursion_depth` refusal before observing delegation. | tools/autopilot/probe-host.py:204 | 15 | BOB |
| R23 | [1/4] | 🟠 | Prior R20 remains incomplete: preparation checks source symlinks but never validates assets named by the compatibility bundle. Also, `except Exception` labels unrelated git, copy, and permission failures as `resource_escape`. Validate declared resources before launch and distinguish containment failures from preparation errors. | tools/autopilot/probe-host.py:204 | 15 | BOB |
| R24 | [1/4] | 🟠 | Doctor now silently falls back to older evidence when the newest record is malformed or has an unsupported version. An older successful probe can therefore clear gaps after the latest probe became invalid. Select the newest record first and report it as invalid without resurrecting older success evidence. | plugins/autopilot/scripts/doctor.py:54 | 14 | BOB |
| R25 | [1/4] | 🟠 | Prior R8/R24 remain unresolved beyond push classification. Equivalence still installs `_doc_translate_hook`, excludes non-document cases, and retains the held-out phase fixture. Run recorded cases through shipped adapters and assert their target decisions, including Stop behavior and explicit divergences. | tests/autopilot/test_interception.py:386 | 16 | BOB |
| R26 | [1/4] | 🟡 | R4 is only partly fixed. Normalization now walks ancestors, but `evaluate_hook` still discards the binding root. Adapters still copy payload `cwd` into `project_root` (claude.py:110-113). The design §2 `project_root` parameter is still not passed. `claude.py:120` still reads `os.environ` for `CLAUDE_CODE_CHILD_SESSION` instead of the hook `env`. The new test `test_env_argument_not_os_environ_resolves_session_identity` only checks `session_from_environment`, which already used `env` before the rework (interception.py:184), so it cannot fail against the old code. | plugins/autopilot/scripts/claude.py:120 | 5 | ALICE |
| R27 | [1/4] | 🟡 | R21 is only nominally fixed for Claude and Codex. `record_cmd` is appended after "Do nothing else. Probe tag: ..." with no instruction to run it, and the earlier text says to run exactly one command. A real host will not execute it. The test only runs the extracted line itself (test_host_argv_record_session.py:21-34). The path is unquoted, so it breaks on spaces. Add an explicit instruction and `shlex.quote`. R22 (the Claude child-lineage observation) is not addressed in this diff. | tools/autopilot/probe-host.py:234 | 9 | ALICE |
| R28 | [1/4] | 🟡 | `run_live` catches bare `Exception` from `prepare` and reports every failure, including a copytree I/O error, as `resource_escape` with no stderr or message. That hides the cause and mislabels it. Catch only the escape `ValueError`, or record the message. `run_hook` likewise swallows `TypeError, AttributeError, KeyError, IndexError` from the whole `evaluate_hook` and turns them into `hook_input_invalid`. That includes programming errors in guards or seams, with no stderr line. It fails closed, but it hides defects. Narrow it to the translate step or log the exception type. | plugins/autopilot/scripts/interception.py:257 | 5 | ALICE |
| R29 | [1/4] | 🟡 | Test shapes. `test_stripped_job_env_with_only_dispatch_depth_still_refuses` opens with `assertNotIn(jobs.JOB_ENV, {"AUTOPILOT_DISPATCH_DEPTH": "1"})`, a constant assertion on a literal dict. Drop it. The R8/R24 equivalence test still uses the test-local `_doc_translate_hook` (not in the diff). The new `PushGrammarCharacterizationTest` binds only denied `push-*` Bash fixtures to `is_git_push`, not to the shipped adapters, so Stop and phase fixtures remain unbound. The `assertRaises(Exception)` in test_probe_host_resource_containment.py:36 is too broad to bind the escape error. | tests/autopilot/test_jobs.py:306 | 3 | ALICE |
| R30 | [1/4] | 🟡 | `test_no_ap00014_module_file_contains_a_coordinator_runtime_pattern` fails with the pattern `while True`. It is probably the directory walk in `interception.find_binding`, a false positive for a coordinator, but the scenario `no_coordinator_runtime_in_plugin` is red as written. | plugins/autopilot/scripts/interception.py:89 | Phase 2 task 2 | BLAKE |
| R31 | [1/4] | 🟡 | `test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations` fails (19 capability ids against the test's 3+15). `_CAPABILITIES` has `hook-v1` and `record-session-v1` that the test's operations list does not account for. | plugins/autopilot/scripts/autopilot.py:24 | Phase 1 task 1 | BLAKE |
| R32 | [1/4] | 🟡 | Native session identity depends on unverified environment variables. `GEMINI_SESSION_ID` has no recorded evidence (`host-markers.md` says Gemini was never probed), and `CLAUDE_CODE_SESSION_ID` has none either. `evaluate_hook` takes the session from `env` only. The hook payload `session_id` helpers (`session_from_hook_input`) exist but are never called, so a hook run without the variable gets `session=None`. | plugins/autopilot/scripts/interception.py:184 | Phase 1 task 1 | BLAKE |
| R33 | [1/4] | 🟡 | The new Gemini fake prints exactly the marker the implementation searches for; it never executes the packaged recording command. These tests can pass while native identity and resource provenance remain entirely unobserved. Make the fake execute the requested command with its native session variable and assert the resulting trace. | tests/autopilot/probe_host_support.py:40 | 15 | BOB |
| R34 | [1/4] | 🟡 | The normalization repair introduces `while True`, causing the supplied coordinator-pattern gate to fail. Remove ancestor guessing by passing the actual binding root, then normalize against that root directly; retain the coordinator check. | plugins/autopilot/scripts/guards.py:156 | 14 | BOB |
| R35 | [1/4] | 🟡 | The README edit invalidates pinned delivery evidence: the supplied gate reports README digest failures in provenance and package tests, plus a stale revision during generator checking. Finalize the documented receipt chain against the final bytes and regenerate the map without exemptions. | plugins/autopilot/README.md:345 | 17 | BOB |
| R36 | [1/4] | ⚪ | Hook activation remains deferred deliberately: §9 prohibits shipping manifest pointers in this PRD. Prior R12 should retain that scope disposition; adding a live activation surface belongs to the publication/install work. | plugins/autopilot/README.md:348 | 17 | BOB |
| R37 | [1/4] | 🟡 | 2 touched test(s) pass against the pre-change code: test_a_valid_schema_version_is_still_consumed_and_clears_the_gap, test_wrong_schema_version_does_not_crash_diagnosis | tests/autopilot/test_doctor.py | general | mech-check |
| R38 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_live_gemini_probe_is_still_rejected_without_a_binary_on_path | tests/autopilot/test_gemini_live_probe.py | general | mech-check |
| R39 | [1/4] | 🟡 | 5 touched test(s) pass against the pre-change code: test_stops_at_the_first_git_toplevel, test_env_argument_not_os_environ_resolves_session_identity, test_post_tool_failure_is_reported_without_blocking, test_pre_tool_deny_carries_the_first_denied_reason, test_pre_tool_deny_with_a_single_reason_does_not_add_a_separator | tests/autopilot/test_interception.py | general | mech-check |
| R40 | [1/4] | 🟡 | 4 touched test(s) pass against the pre-change code: test_a_dispatch_depth_env_value_below_max_job_depth_is_not_refused, test_effort_is_required_and_never_in_argv, test_standalone_never_writes_through_an_existing_symlink, test_two_independent_standalone_calls_do_not_interfere | tests/autopilot/test_jobs.py | general | mech-check |
| R41 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_prepare_accepts_a_source_tree_whose_symlink_stays_inside_it | tests/autopilot/test_probe_host_resource_containment.py | general | mech-check |

### Auto-dismissed (ledger)
- [BLAKE] 🟡 CHANGELOG line 15 contradicts `hosts.json`. It says "Codex declares isolation only; Gemini declares none", but `hosts.json` has Codex with identity, interception and isolation, and Gemini with identity and isolation. This is stale evidence for the capability claims. | File: plugins/autopilot/CHANGELOG.md:15 — single-voice
- [BLAKE] ⚪ `--close-child` hardcodes the parent host as `claude`. That fits the current in-session delegation set, which is Claude-only. | File: plugins/autopilot/scripts/autopilot.py:269 — single-voice

## Alice

Consensus lens, implementation-aware. 14 findings: 2 🔴, 5 🟠, 7 🟡.
Full output: `docs/dev/tmp/alice-output-c2-20261116.txt`.

Verified resolved by Alice this cycle: cycle-1 R1 (`request_job` split),
R2/R14 (`DEPTH_ENV` parsed and enforced), R5 (`O_EXCL`, no truncate),
R6 (`HOOK_REGISTRATIONS = ()` in gemini.py), R9/R17 (malformed payloads render
`hook_input_invalid`), R19 (gemini live probe accepted), R20 (symlink escape
check before copy), R23 (doctor validates `schema_version`), R25 (binding test
uses its own temp root), R26 (`hook-v1` in `_CAPABILITIES`), and R3 for the
common push spellings.

R1: pass
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: fail

## Blake

Blind lens, PRD-only prompt. 12 findings: 3 🔴, 4 🟠, 4 🟡, 1 ⚪
(two of the 🟡/⚪ auto-dismissed against the ledger).
Full output: `docs/dev/tmp/blake-output-c2-20261116.txt`.

Blake reports as implemented and sound: `jobs.py` request validation, recursion
refusal and input-digest verification; job requests carrying effort and the
requester session; exclusive `O_NOFOLLOW|O_EXCL` binding records; plugin scripts
spawning no provider CLIs; malformed controller verdicts refusing; and
`ProbeResult` forcing `certified` false.

B1: fail
B2: fail
B3: fail
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
B15: fail
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

Doubt lens (D1-D5) plus de-slop, codex, cycle-1 thread resumed. 20 FIX items,
0 VERIFY, 1 KNOWN. Full output: `docs/dev/tmp/bob-output-c2-20261116.txt`.

Bob's KNOWN item: hook activation remains deferred deliberately (§9 prohibits
shipping manifest pointers in this PRD); prior R12 should retain that scope
disposition.

R1: fail
R2: fail
R3: fail
R4: fail
R6: pass
R7: fail
R8: fail
R9: fail
R10: fail
R11: fail
R12: pass
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

UI/design lens, gemini via copilot backend (model `gemini-3.8-flash`).
3 findings: 2 🟠, 1 🟡. Full output:
`docs/dev/tmp/carl-output-c2-20261116.txt`.

R1: pass
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: fail

Verdict: 41 findings
Tests: 1869 passed, 14 failed (suite run this cycle)

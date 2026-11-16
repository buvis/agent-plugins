---
prd: docs/dev/project-management/prds/wip/00014-autopilot-host-execution-v2.md
review: 3
date: 2026-11-16
head_sha: 827f210741953d18b5404488366f9d5876a0fefa
codex_thread_id: 01a1e166-515a-79f3-ac3f-6907494e402d
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: b198ce37
  carl: 962606a3
---

# Review: 00014-autopilot-host-execution-v2

Diff range: `949af1a01ada89b05cdb2a9c295d68db25810c88..827f210741953d18b5404488366f9d5876a0fefa`

codex_rung_guard: not fired

## Review Summary

Reviewed: 26 completed tasks (all tasks of the PRD)
PRDs checked: 00014-autopilot-host-execution-v2.md
Cycle: 3 of rework_cap 3 (incremental review of the cycle-2 rework)

### Agent Status

- Alice: available
- Blake: available
- Bob: available (first dispatch refused by codex with `input_too_large`
  at 1849770 characters against a 1048576 limit; the one retry re-dispatched a
  618671-byte prompt that excludes four generated or record-only paths from the
  inlined diff - `tools/autopilot/source-map.json`, the autopilot `*.jsonl`
  telemetry, `docs/dev/project-management/autopilot/ledger/*` and this PRD's own
  `reviews/*` records. Everything else in the range was inlined verbatim.)
- Carl: available (copilot/gemini backend)

### Notes on this cycle

- Test gate: green at HEAD `827f210`, `PASS 1935 FAIL 0 SKIP 0 EXIT 0`, recorded
  by `autopilot verify` into `last-verification.json`; `review-stage` reused that
  record. The 14 cycle-2 regressions Alice reported are closed.
- Carl's own run of the suite inside his review reported `1 failed, 1934 passed`
  on `tests/autopilot/test_helper_map_refresh_agreement.py::test_a_probe_failure_that_is_not_an_absent_work_tree_is_refused[probe-answers-false]`.
  That failure did not reproduce: re-running the same test at HEAD gives
  `9 passed in 0.28s`. Treated as a single-run environment artefact of his
  sandbox, not a finding; the recorded gate at `827f210` is the cycle's result.
- `codex_rung_guard: not fired` - no task of this PRD has a `codex` implementor
  attempt, so the doubt roster is Bob alone and Eve was not activated.
- Bob's dispatch row `prompt_bytes` understates what codex received: the staged
  render was measured before the inlined prompt overwrote it.
- Pack: ok. Prior-cycle findings and the 42-entry settled ledger were fed to
  Alice, Bob and Carl; Blake stayed blind.
- No VERIFY bucket entry this cycle (Bob emitted `VERIFY: - (none)`), so no
  verification-check queue file was written.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/4] | 🟠 | `run_live_gemini` runs `_check_no_escaping_symlink`, `copytree` and `mkdir` outside the try block that `run_live` uses for `prepare`. The gemini branch returns at line 306, before that try. A symlink escape or a copy error in the Gemini path therefore ends the probe with a traceback. Claude and Codex report `resource_escape` or `preparation_failed` and launch nothing. No test covers a Gemini preparation failure. Route the Gemini preparation through the same handler, and add a test. | tools/autopilot/probe-host.py:257 | 15 | ALICE, BOB |
| R2 | [1/4] | 🟠 | Claude hooks are not retained through supported packaging, and no client's registration is activated. plugin.json has no hooks field, no .claude-plugin manifest ships, and both registrations carry "activated": false (README says so too). The enforcement therefore exists only as generated assets. The probe proves registration only in a temp copy where it writes its own manifest. The spec asks to retain Claude hooks and prove each extra client's registration. | plugins/autopilot/contracts/hosts.json:7 | Phase 1 task 2 | BLAKE |
| R3 | [1/4] | 🟠 | "isolation" and the other host capabilities are still constants. Each adapter sets IMPLEMENTED_CAPABILITIES = frozenset({...}), and no adapter holds isolation-specific code. statuses_from turns that constant plus an auth-presence check into "supported". resolve_profile marks a profile "resolvable" from the same constants, and --resolve-roles passes observed=None. The spec says host support, isolation and real probing cannot be closed by a capability constant. | plugins/autopilot/scripts/hosts.py:146 | Phase 1 task 3 | BLAKE |
| R4 | [1/4] | 🟠 | Phase 2 task 1 evidence is missing. probe-host.py can run live probes, but every adapter probe in the package is static and the tests use fakes (tests/autopilot/host_fakes.py). The repo holds no recorded probe output, and docs/dev/tmp/autopilot/ does not exist. The spec requires recording real-host unavailability explicitly, and doctor reads its observed evidence only from that directory. | tools/autopilot/probe-host.py | Phase 2 task 1 | BLAKE |
| R5 | [1/4] | 🟠 | Stateful guards behave differently in the two modes. interception.py skips controller-keyed duties (custody_push, state_integrity, review_completeness, live_job, post_handoff, departure, context_reinjection) when no .autopilot/controller directory is found. A repo without that marker gets no custody-push or state-integrity enforcement, which is fail-open. In a bound repo, run_hook hard-codes seam=None, so every push, Stop and patch write refuses with no way to supply a seam. The spec says stateful guards call the same seam in both modes. | plugins/autopilot/scripts/interception.py:157 | Phase 1 task 2 | BLAKE |
| R6 | [1/4] | 🟠 | Gemini still launches as `["gemini", "-p"]`, although the contract requires the prompt as the argument following `-p`. Sending it only through stdin does not satisfy that invocation. The fake accepts this malformed argv, masking the integration defect. Pass the prompt in argv and assert the complete invocation. | tools/autopilot/probe-host.py:253 | 24 | BOB |
| R7 | [1/4] | 🟠 | Successful Gemini evidence always has `resource_check="not_run"`, so doctor discards every observed Gemini capability. The required profile can never become certifiable through this probe. Validate the recording trace’s copied plugin root, invalidate resource escapes, and report a passed resource check for a valid run. | tools/autopilot/probe-host.py:253 | 24 | BOB |
| R8 | [1/4] | 🟠 | `recorded_session` accepts any schema-1 object containing `host_id`, without validating the expected host, native session shape, or session ID type. Empty strings, numbers, or another host’s records can produce observed identity and isolation. Validate the record against the requested host and `NativeSession` rules before accepting its ID. | tools/autopilot/probe-host.py:83 | 24 | BOB |
| R9 | [1/4] | 🟠 | Delegation observation combines outcomes across both bound runs. One run containing only an allowed parent and another containing only a refused nested dispatch incorrectly establishes delegation. Require the complete ordered parent/nested scenario within a single invocation, and add a test with complementary incomplete runs. | tools/autopilot/probe-host.py:201 | 24 | BOB |
| R10 | [1/4] | 🟠 | Push classification still misses ordinary executable pushes with attached redirection, such as `git push>push.log`: `shlex.split` retains `push>push.log`, so the required `push` token is absent and custody enforcement is bypassed. Tokenize shell operators separately and assert denial through the real bound hook path. | plugins/autopilot/scripts/guards.py:329 | 23 | BOB |
| R11 | [1/4] | 🟠 | Declared-resource validation remains incomplete. `prepare` reads a hardcoded hooks path and validates its scripts, but never reads the compatibility bundle’s `registration.asset`. A bundle naming a missing or escaping asset is therefore ignored. Resolve and validate the bundle-declared registration asset before launching. | tools/autopilot/probe-host.py:135 | 24 | BOB |
| R12 | [1/4] | 🟡 | `_normalize_rel` still reduces an absolute path outside the project root to a root-relative one, by trying every ancestor of the root and finally `""`. I ran it: `_normalize_rel('/home/u/done/notes.md', '/home/u/proj')` gives `done/notes.md`, and `/tmp/wip/x` gives `tmp/wip/x`. `document_location` then denies edits to unrelated files such as `/home/u/done/notes.md` or `/backlog/x`. Design §7 (design lines 669-670) says an absolute path outside the root keeps the whole-path store check. `NormalizeRelTest` pins the contradiction with the case `("/r/backlog/x.md", "/r/sub") -> "backlog/x.md"`. Only the `while True` was fixed, not the semantics. Behavior-preserving to the design: reduce only when `norm == root` or it starts with `root + "/"`. Otherwise return the path unchanged, and change the pinned case. | plugins/autopilot/scripts/guards.py:156 | 14 | ALICE |
| R13 | [1/4] | 🟡 | `is_git_push` still fails open for any wrapper not in `_PREFIX_CMDS`. I ran these, and all return False: `doas git push`, `setsid git push`, `flock /tmp/l git push`, `watch -n1 git push`, `chrt 1 git push`, `caffeinate git push`, `unbuffer git push`, `strace git push`. The new tests cover only the spellings the fix handles (test_guards_pure_duties.py:603 onward). The rework added `ionice`/`stdbuf` and generalized option skipping, which closes the cases listed in prior R8. The fail-open set is still open-ended, so the design's "conservative superset" contract (design line 681) is not met for unlisted wrappers. A cheap closer: also return True when any token named `git` in the segment is followed by `push`, unless the leading executable is a known non-wrapper such as `echo` (design allows `echo git push`). | plugins/autopilot/scripts/guards.py:329 | 4 | ALICE |
| R14 | [1/4] | 🟡 | Redundancy and a stale docstring after the alias fix. `RenderHookReplyTest` iterates single-element tuples `(("claude", claude_adapter),)` (lines 25 and 53). `CodexRenderHookReplyContractTest` re-asserts the same shapes for `codex_adapter`. Its docstring (line 140) still says "codex.py:147's reply shapes diverge from claude's", which is now false because the two adapters share one function. Replace both with a loop over `INTERCEPTING` and drop the duplicate class and the stale docstring. This is behavior-preserving, since the contract is one function. | tests/autopilot/test_interception_render_reply.py:25 | 25 | ALICE |
| R15 | [1/4] | 🟡 | AP00014 rows are still excluded in a provenance test. skipped = set(REFRESHED) | HELPER_TARGETS | AP00014_TARGETS drops them from the "other assets" digest. Phase 2 task 3 requires passing without AP00014 exclusions. The AP00014 rows are checked separately at line 500, but the exclusion list remains. | tests/autopilot/test_helper_provenance_real.py:268 | Phase 2 task 3 | BLAKE |
| R16 | [1/4] | 🟡 | Static capability names are claimed for a host with no auth check against reality. The Codex and Gemini identity variables (CODEX_SESSION_ID, GEMINI_SESSION_ID) are asserted without observed proof in the repo. The live probe relies on the Claude -p headless Bash run being permitted, and the codex flag --dangerously-bypass-hook-trust is used unverified. A refused Bash run would make the control push fail and report interception as not observed. | tools/autopilot/probe-host.py:325 | Phase 2 task 1 | BLAKE |
| R17 | [1/4] | 🟡 | doctor.py indexes record["observed"] and gemini[1]["invocations"] without shape checks. A schema_version 2 evidence file with a missing key raises KeyError and crashes the diagnosis instead of reporting no evidence. Evidence files are also trusted without provenance. | plugins/autopilot/scripts/doctor.py:82 | Phase 1 task 3 | BLAKE |
| R18 | [1/4] | 🟡 | Gemini auth refusals still produce `not_observed/no_auth`, while the contract requires `unavailable` with the reported error class. The new tests explicitly pin the divergent status. Implement the specified auth-refusal result and update the verdict tests. | tools/autopilot/probe-host.py:253 | 24 | BOB |
| R19 | [1/4] | 🟡 | The split rendering tests retain duplicate Claude and Codex suites despite restoring their shared renderer. Parameterize the shared contract cases over `INTERCEPTING`, retain the single-reason case, and remove the redundant Codex class and its obsolete divergence description. | tests/autopilot/test_interception_render_reply.py:140 | 25 | BOB |
| R20 | [1/4] | ⚪ | _check_identity rejects only the exact provider, host and tier names. Role ids such as "claude-reviewer" pass, so independence from provider and model names is only partly enforced. | plugins/autopilot/scripts/jobs.py:104 | Phase 1 task 1 | BLAKE |
| R21 | [1/4] | ⚪ | Shared skill and reference bodies still contain ${CLAUDE_PLUGIN_ROOT}, ~/.claude/... and claude -p text. They are labelled "unavailable" or historical provenance, so I accept this under the spec's informational-provenance allowance. Adaptation is left to AP 00015. | plugins/autopilot/skills/run-autopilot/SKILL.md:8 | general | BLAKE |
| R22 | [1/4] | 🟡 | 6 touched test(s) pass against the pre-change code: test_every_generated_hook_command_is_built_from_the_adapters_plugin_root_expression, test_no_generated_asset_for_a_non_claude_host_names_the_claude_variable, test_a_host_without_registration_declares_no_activated_key, test_every_registered_host_declares_activated_exactly_false, test_every_shipped_bundle_registration_equals_the_contracts, test_readme_and_changelog_state_the_registration_is_not_activated | tests/autopilot/test_compatibility.py | general | mech-check |
| R23 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_a_valid_newest_evidence_file_clears_the_gap_even_with_an_older_malformed_file | tests/autopilot/test_doctor.py | general | mech-check |
| R24 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_live_gemini_probe_derives_identity_and_isolation_from_session_ids_only | tests/autopilot/test_gemini_live_probe.py | general | mech-check |
| R25 | [1/4] | 🟡 | 3 touched test(s) pass against the pre-change code: test_allows_a_command_with_no_git_or_push_tokens, test_denies_every_unfamiliar_wrapper_form, test_normalizes_each_path_and_project_root_pair | tests/autopilot/test_guards_pure_duties.py | general | mech-check |
| R26 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_relocated_host_probe_never_turns_a_failed_run_into_observation | tests/autopilot/test_host_argv_failed_runs.py | general | mech-check |
| R27 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_probe_control_is_unbound_inside_a_bound_source_repo | tests/autopilot/test_host_argv_live_runs.py | general | mech-check |
| R28 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_unbound_with_no_duty_calls_allows_trivially | tests/autopilot/test_interception.py | general | mech-check |
| R29 | [1/4] | 🟡 | 9 touched test(s) pass against the pre-change code: test_every_denied_push_fixture_is_a_grammar_match, test_hook_behavior_equivalence, test_a_child_session_dispatch_is_refused_for_depth, test_a_skill_is_refused_only_after_this_sessions_own_leave, test_bound_stop_without_seam_blocks_then_releases, test_dispatching_a_whole_phase_skill_in_the_prompt_is_denied +3 more | tests/autopilot/test_interception_push_grammar.py | general | mech-check |
| R30 | [1/4] | 🟡 | 12 touched test(s) pass against the pre-change code: test_post_tool_refusal_blocks_with_a_reason, test_pre_tool_allow_never_denies, test_pre_tool_deny_joins_every_reason, test_session_start_refusal_surfaces_a_system_message, test_session_start_surfaces_additional_context_only_when_present, test_stop_blocks_once_then_lets_the_stop_through +6 more | tests/autopilot/test_interception_render_reply.py | general | mech-check |
| R31 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_creates_missing_parent_directories_and_writes_the_payload | tests/autopilot/test_jobs_write_request_file.py | general | mech-check |
| R32 | [1/4] | 🟡 | 4 touched test(s) pass against the pre-change code: test_a_failed_or_escaped_run_still_reports_delegation_with_the_failure_reason, test_delegation_reports_the_precise_gap_when_one_half_of_the_scenario_is_missing, test_a_declared_script_that_stays_inside_the_copied_tree_is_accepted, test_a_missing_declared_hook_script_fails_preparation_and_launches_nothing | tests/autopilot/test_probe_host_delegation.py | general | mech-check |
| R33 | [1/4] | 🟡 | 6 touched test(s) pass against the pre-change code: test_record_command_is_the_shlex_join_of_the_explicit_argument_list, test_recorded_session_is_none_for_a_prompt_echo_and_for_empty_text, test_recorded_session_returns_the_session_id_of_the_record_object, test_gemini_probe_never_reads_a_session_id_out_of_an_echoed_prompt, test_gemini_probe_observes_identity_and_isolation_for_two_distinct_ids, test_gemini_probe_reports_no_auth_for_a_non_zero_exit_with_an_auth_message | tests/autopilot/test_probe_host_record_session.py | general | mech-check |
| R34 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_run_live_marks_every_capability_not_observed_when_the_source_escapes | tests/autopilot/test_probe_host_resource_containment.py | general | mech-check |

### Auto-dismissed (ledger)

- [BLAKE] 🟡 Hook identity ignores the hook payload. evaluate_hook takes the session only from hosts.current_session(host_id, env). session_from_hook_input exists in claude.py and codex.py and nothing calls it. If the host does not export the session variable to hook subprocesses, session is None and the seam facts and the trace carry no identity. | File: plugins/autopilot/scripts/interception.py:187 — single-voice
- [BLAKE] 🟡 The CHANGELOG line for the host adapters is stale and contradicts the contract. It says "Codex declares isolation only; Gemini declares none". hosts.json says Codex declares identity, interception and isolation, and Gemini declares identity and isolation. This breaks "no unsupported capability advertised" and the task to update the changelog. | File: plugins/autopilot/CHANGELOG.md:15 — single-voice

## Alice

## Alice review - PRD 00014 cycle 3 (incremental, base 949af1a)

Gate: 1935 passed, 0 failed (context). I re-ran the changed test files under `python3 -m unittest`, which also runs `subTest` bodies: test_guards_pure_duties (63), test_compatibility (37), test_interception* (57), test_probe_host* (32) and test_doctor (8) are all OK. Eight of the mech replay's "passes at base" entries are `subTest` tests, so I count them as replay noise. The rest are accept-side controls, labelled as such in the tests.

Prior findings, verified in code:
- R1 resolved: the `replace(facts, gemini_cli_available=True)` override is gone from `autopilot.py`.
- R2 resolved: Gemini identity now comes from a real `--record-session` JSON object (`recorded_session`), not the echoed prompt.
- R3 resolved: `test_interception.py` is 748 lines, and the render-reply and push-grammar tests moved to their own files.
- R4 resolved: controller-keyed duties skip when unbound (`interception.py:154` area), and the probe control push lands again.
- R5 resolved: `claude.render_hook_reply` aliases `codex.render_hook_reply`.
- R6, R9, R10 resolved: the README digest is re-sealed and the gate is green.
- R7 resolved: `hook-v1` is in the operations list.
- R12, R13 first half, R14, R15, R16, R17, R18 (resolved: `_write_request_file` now creates through `_pinned_parent_fd`, with a parent-swap test), R19, R20, R21, R22, R23 and R24 are resolved or superseded.
- R8 only partly resolved, and R13 second half is not resolved (new findings below).

[ALICE] 🟡 `_normalize_rel` still reduces an absolute path outside the project root to a root-relative one, by trying every ancestor of the root and finally `""`. I ran it: `_normalize_rel('/home/u/done/notes.md', '/home/u/proj')` gives `done/notes.md`, and `/tmp/wip/x` gives `tmp/wip/x`. `document_location` then denies edits to unrelated files such as `/home/u/done/notes.md` or `/backlog/x`. Design §7 (design lines 669-670) says an absolute path outside the root keeps the whole-path store check. `NormalizeRelTest` pins the contradiction with the case `("/r/backlog/x.md", "/r/sub") -> "backlog/x.md"`. Only the `while True` was fixed, not the semantics. Behavior-preserving to the design: reduce only when `norm == root` or it starts with `root + "/"`. Otherwise return the path unchanged, and change the pinned case. | File: plugins/autopilot/scripts/guards.py:156 | Task: 14

[ALICE] 🟡 `is_git_push` still fails open for any wrapper not in `_PREFIX_CMDS`. I ran these, and all return False: `doas git push`, `setsid git push`, `flock /tmp/l git push`, `watch -n1 git push`, `chrt 1 git push`, `caffeinate git push`, `unbuffer git push`, `strace git push`. The new tests cover only the spellings the fix handles (test_guards_pure_duties.py:603 onward). The rework added `ionice`/`stdbuf` and generalized option skipping, which closes the cases listed in prior R8. The fail-open set is still open-ended, so the design's "conservative superset" contract (design line 681) is not met for unlisted wrappers. A cheap closer: also return True when any token named `git` in the segment is followed by `push`, unless the leading executable is a known non-wrapper such as `echo` (design allows `echo git push`). | File: plugins/autopilot/scripts/guards.py:329 | Task: 4

[ALICE] 🟡 `run_live_gemini` runs `_check_no_escaping_symlink`, `copytree` and `mkdir` outside the try block that `run_live` uses for `prepare`. The gemini branch returns at line 306, before that try. A symlink escape or a copy error in the Gemini path therefore ends the probe with a traceback. Claude and Codex report `resource_escape` or `preparation_failed` and launch nothing. No test covers a Gemini preparation failure. Route the Gemini preparation through the same handler, and add a test. | File: tools/autopilot/probe-host.py:257 | Task: 15

[ALICE] 🟡 Redundancy and a stale docstring after the alias fix. `RenderHookReplyTest` iterates single-element tuples `(("claude", claude_adapter),)` (lines 25 and 53). `CodexRenderHookReplyContractTest` re-asserts the same shapes for `codex_adapter`. Its docstring (line 140) still says "codex.py:147's reply shapes diverge from claude's", which is now false because the two adapters share one function. Replace both with a loop over `INTERCEPTING` and drop the duplicate class and the stale docstring. This is behavior-preserving, since the contract is one function. | File: tests/autopilot/test_interception_render_reply.py:25 | Task: 25

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: fail
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

BLAKE review, cycle 3, PRD 00014 (blind). I read the code and did not rerun the suite. The gate reports 1935 passed at 827f210. I did not read prior review files, apart from confirming that 00014-v2-finding-dispositions.md names every stub from 00038 to 00064.

Verified as built:
- Adapters: plugins/autopilot/scripts/hosts.py, claude.py, codex.py, gemini.py, jobs.py and contracts/hosts.json.
- Guards and compatibility: guards.py, interception.py, doctor.py, roles.py, the compatibility/ bundles, tools/autopilot/build-compatibility.py and tools/autopilot/probe-host.py.
- Jobs: requests are structured, there is a recursion bound, and no provider CLI is spawned. The plugin scripts that spawn processes (verification.py, catchup.py, cap_check.py, dirty_tree.py, review_stage.py) belong to earlier PRDs and do not launch provider CLIs.
- Guards: all nine duties are present. Malformed controller verdicts refuse, and absolute and relative project paths normalise the same way.
- Probing: unavailable hosts record no_binary or no_auth, and certified is always false.
- Claude-free profile: the codex-gemini profile in contracts/review-policy-v1.json excludes Claude for every role.

[BLAKE] 🟠 Claude hooks are not retained through supported packaging, and no client's registration is activated. plugin.json has no hooks field, no .claude-plugin manifest ships, and both registrations carry "activated": false (README says so too). The enforcement therefore exists only as generated assets. The probe proves registration only in a temp copy where it writes its own manifest. The spec asks to retain Claude hooks and prove each extra client's registration. | File: plugins/autopilot/contracts/hosts.json:7 | Task: Phase 1 task 2
[BLAKE] 🟠 "isolation" and the other host capabilities are still constants. Each adapter sets IMPLEMENTED_CAPABILITIES = frozenset({...}), and no adapter holds isolation-specific code. statuses_from turns that constant plus an auth-presence check into "supported". resolve_profile marks a profile "resolvable" from the same constants, and --resolve-roles passes observed=None. The spec says host support, isolation and real probing cannot be closed by a capability constant. | File: plugins/autopilot/scripts/hosts.py:146 | Task: Phase 1 task 3
[BLAKE] 🟠 Phase 2 task 1 evidence is missing. probe-host.py can run live probes, but every adapter probe in the package is static and the tests use fakes (tests/autopilot/host_fakes.py). The repo holds no recorded probe output, and docs/dev/tmp/autopilot/ does not exist. The spec requires recording real-host unavailability explicitly, and doctor reads its observed evidence only from that directory. | File: tools/autopilot/probe-host.py | Task: Phase 2 task 1
[BLAKE] 🟠 Stateful guards behave differently in the two modes. interception.py skips controller-keyed duties (custody_push, state_integrity, review_completeness, live_job, post_handoff, departure, context_reinjection) when no .autopilot/controller directory is found. A repo without that marker gets no custody-push or state-integrity enforcement, which is fail-open. In a bound repo, run_hook hard-codes seam=None, so every push, Stop and patch write refuses with no way to supply a seam. The spec says stateful guards call the same seam in both modes. | File: plugins/autopilot/scripts/interception.py:157 | Task: Phase 1 task 2
[BLAKE] 🟡 Hook identity ignores the hook payload. evaluate_hook takes the session only from hosts.current_session(host_id, env). session_from_hook_input exists in claude.py and codex.py and nothing calls it. If the host does not export the session variable to hook subprocesses, session is None and the seam facts and the trace carry no identity. | File: plugins/autopilot/scripts/interception.py:187 | Task: Phase 1 task 1
[BLAKE] 🟡 The CHANGELOG line for the host adapters is stale and contradicts the contract. It says "Codex declares isolation only; Gemini declares none". hosts.json says Codex declares identity, interception and isolation, and Gemini declares identity and isolation. This breaks "no unsupported capability advertised" and the task to update the changelog. | File: plugins/autopilot/CHANGELOG.md:15 | Task: Phase 2 task 2
[BLAKE] 🟡 AP00014 rows are still excluded in a provenance test. skipped = set(REFRESHED) | HELPER_TARGETS | AP00014_TARGETS drops them from the "other assets" digest. Phase 2 task 3 requires passing without AP00014 exclusions. The AP00014 rows are checked separately at line 500, but the exclusion list remains. | File: tests/autopilot/test_helper_provenance_real.py:268 | Task: Phase 2 task 3
[BLAKE] 🟡 Static capability names are claimed for a host with no auth check against reality. The Codex and Gemini identity variables (CODEX_SESSION_ID, GEMINI_SESSION_ID) are asserted without observed proof in the repo. The live probe relies on the Claude -p headless Bash run being permitted, and the codex flag --dangerously-bypass-hook-trust is used unverified. A refused Bash run would make the control push fail and report interception as not observed. | File: tools/autopilot/probe-host.py:325 | Task: Phase 2 task 1
[BLAKE] 🟡 doctor.py indexes record["observed"] and gemini[1]["invocations"] without shape checks. A schema_version 2 evidence file with a missing key raises KeyError and crashes the diagnosis instead of reporting no evidence. Evidence files are also trusted without provenance. | File: plugins/autopilot/scripts/doctor.py:82 | Task: Phase 1 task 3
[BLAKE] ⚪ _check_identity rejects only the exact provider, host and tier names. Role ids such as "claude-reviewer" pass, so independence from provider and model names is only partly enforced. | File: plugins/autopilot/scripts/jobs.py:104 | Task: Phase 1 task 1
[BLAKE] ⚪ Shared skill and reference bodies still contain ${CLAUDE_PLUGIN_ROOT}, ~/.claude/... and claude -p text. They are labelled "unavailable" or historical provenance, so I accept this under the spec's informational-provenance allowance. Adaptation is left to AP 00015. | File: plugins/autopilot/skills/run-autopilot/SKILL.md:8 | Task: general

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
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

FIX:
- [BOB] 🟠 Gemini still launches as `["gemini", "-p"]`, although the contract requires the prompt as the argument following `-p`. Sending it only through stdin does not satisfy that invocation. The fake accepts this malformed argv, masking the integration defect. Pass the prompt in argv and assert the complete invocation. | File: tools/autopilot/probe-host.py:253 | Task: 24
- [BOB] 🟠 Successful Gemini evidence always has `resource_check="not_run"`, so doctor discards every observed Gemini capability. The required profile can never become certifiable through this probe. Validate the recording trace’s copied plugin root, invalidate resource escapes, and report a passed resource check for a valid run. | File: tools/autopilot/probe-host.py:253 | Task: 24
- [BOB] 🟠 Gemini preparation bypasses the preparation-error handler: `run_live` returns `run_live_gemini` before entering its `try`. A source symlink escape or copy failure therefore raises instead of producing refusal evidence. Apply the same resource/preparation failure classification to Gemini and test both failures through the CLI. | File: tools/autopilot/probe-host.py:304 | Task: 24
- [BOB] 🟠 `recorded_session` accepts any schema-1 object containing `host_id`, without validating the expected host, native session shape, or session ID type. Empty strings, numbers, or another host’s records can produce observed identity and isolation. Validate the record against the requested host and `NativeSession` rules before accepting its ID. | File: tools/autopilot/probe-host.py:83 | Task: 24
- [BOB] 🟠 Delegation observation combines outcomes across both bound runs. One run containing only an allowed parent and another containing only a refused nested dispatch incorrectly establishes delegation. Require the complete ordered parent/nested scenario within a single invocation, and add a test with complementary incomplete runs. | File: tools/autopilot/probe-host.py:201 | Task: 24
- [BOB] 🟠 Push classification still misses ordinary executable pushes with attached redirection, such as `git push>push.log`: `shlex.split` retains `push>push.log`, so the required `push` token is absent and custody enforcement is bypassed. Tokenize shell operators separately and assert denial through the real bound hook path. | File: plugins/autopilot/scripts/guards.py:329 | Task: 23
- [BOB] 🟠 Declared-resource validation remains incomplete. `prepare` reads a hardcoded hooks path and validates its scripts, but never reads the compatibility bundle’s `registration.asset`. A bundle naming a missing or escaping asset is therefore ignored. Resolve and validate the bundle-declared registration asset before launching. | File: tools/autopilot/probe-host.py:135 | Task: 24
- [BOB] 🟡 Gemini auth refusals still produce `not_observed/no_auth`, while the contract requires `unavailable` with the reported error class. The new tests explicitly pin the divergent status. Implement the specified auth-refusal result and update the verdict tests. | File: tools/autopilot/probe-host.py:253 | Task: 24
- [BOB] 🟡 The split rendering tests retain duplicate Claude and Codex suites despite restoring their shared renderer. Parameterize the shared contract cases over `INTERCEPTING`, retain the single-reason case, and remove the redundant Codex class and its obsolete divergence description. | File: tests/autopilot/test_interception_render_reply.py:140 | Task: 25

VERIFY:
- (none)

KNOWN:
- (none)

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

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

Verdict: 34 findings
Tests: 1935 passed, 0 failed, 0 skipped (reused from last-verification.json at 827f210)

---
prd: docs/dev/project-management/prds/wip/00014-autopilot-host-execution-v1.md
review: 2
date: 2026-11-09
head_sha: 273be89f1d993447b49a1d1b895b71e28259a0e6
codex_thread_id: 01a1bcbb-31e5-7991-8235-7d1815614b6a
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: 034273d0 (failed, input_too_large) -> b02ccacf (retry, ok)
  carl: d4536293
---

# Review: 00014-autopilot-host-execution-v1 (cycle 2)

Diff range: `68418c5a3c8951abfbac494ddc9cdae0d6408a06..273be89f1d993447b49a1d1b895b71e28259a0e6` (incremental: rework since cycle 1)

codex_rung_guard: not fired

## Review Summary

Reviewed: 20 completed tasks
PRDs checked: 00014-autopilot-host-execution-v1.md

### Agent Status
- Alice: available (Claude subagent, consensus lens)
- Blake: available (Claude subagent, blind lens, PRD-only)
- Bob: available (codex, doubt lens D1-D5 + de-slop; resumed cycle-1 thread)
- Carl: available (gemini via copilot backend, UI/design lens)

pack: ok

### Notes on this cycle

- Bob's first dispatch failed with codex exit 1,
  `input_too_large` (1,440,792 characters against a 1,048,576 limit). The one
  permitted CLI retry re-sent the same inlined prompt with the review context's
  `## Completed Tasks` section clipped (300 characters per line, 60 KB total);
  the FULL DIFF stayed untrimmed. The retry succeeded and resumed the cycle-1
  codex thread. Bob's evidence is therefore complete for the diff and clipped
  for the task descriptions.
- The staged gate run and a second, explicit `autopilot verify` run both exited
  1 with `counts unavailable`: this project's `-q` summary line
  (`20 failed, 1433 passed in 353.91s`) matches no pattern the parser accepts,
  so `last-verification.json` was NOT recorded either time. The counts in the
  `Tests:` line below are read from the verify run's own log
  (`docs/dev/tmp/gate-273be89.log:528`). That is a no-record outcome, not a
  clean gate.
- All 20 failures are the deferred pre-existing set: 19 in
  `test_controller_capacity.py`, `test_controller_owner.py` and
  `test_controller_owner_recovery.py` (a different PRD), plus
  `test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes`,
  which three reviewers raise as R1 below. Cycle 1's AP00014-specific failures
  (prior R4, R5, R6, R8) are gone: the suite moved from 24 failed / 1352 passed
  to 20 failed / 1433 passed.
- `consolidate_findings.py` warned that row R1 merged two citations matching
  only after suffix stripping (`test_helper_provenance_real.py:300 ~ :303`).
  The merge is correct: both cite the same failing assertion, though Bob rates
  it 🟡 (deferred scope) against Alice's and Carl's 🔴, and the consolidated row
  carries the higher severity.
- Six `[MECH]` fail-first replay lines were absorbed as rows R27-R32; none
  matched an existing row's test file and test.
- No verification-check queue was written: Bob's VERIFY bucket is empty.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/4] | 🔴 | Prior R7/R24 is NOT resolved. `test_new_helper_files_are_owned_and_digested_from_current_bytes` still fails. I ran tests/autopilot test_guards*, test_compatibility, test_host_argv, test_sessions, test_jobs, test_package, test_helper_provenance_real, test_local_boundary and test_facade: 228 passed, 1 failed. The failure is `assert_refreshed_evidence`, which compares the blob of plugins/autopilot/CHANGELOG.md at `tested_package_revision` with the current bytes. The rework refreshed `destination_blob_sha256` (task 16), but the test also requires the file at the tested revision to equal the file on disk. AP00014 edited CHANGELOG.md and autopilot.py after that revision, so the test cannot pass as written. The test passed at the PRD base commit, so this is still an AP00014 regression. Fix: re-test the package and update the evidence revision, or scope the check as AP00018 did for its rows. Also add the AP00014-touched REFRESHED paths to the exemption. | tests/autopilot/test_helper_provenance_real.py:300 | 16 | ALICE, BOB, CARL |
| R2 | [2/4] | 🟡 | `doctor.diagnose` calls `run_guard(duty, {}, ...)` for all nine duties. The five pure duties now deny on missing input, so `autopilot.py --diagnose` always reports document_location, delegation, post_handoff, departure and context_reinjection as `allowed: false`. I ran it and confirmed. The assumptions file records this as a deferred out-of-scope item, but the doctor is a caller of the changed guards and its report is now misleading. No test covers `diagnose` output. Fix: pass a representative allow-context per pure duty, or label these entries "not evaluated", and add one diagnose test. | plugins/autopilot/scripts/doctor.py:38 | 20 | ALICE, BLAKE |
| R3 | [1/4] | 🟠 | Claude-free profile is not implemented. Codex declares only `isolation` and Gemini declares nothing, so both `session_identity()` return None, `can_delegate()` is False and `build_job_argv()` is None. The spec says to implement applicable native identity/input/guard support for the Codex implementer and Gemini doubt reviewer. Documenting a blocker is allowed for certification only. `doctor.diagnose` derives profile "mixed" because "identity" is not covered. Only Claude has identity, delegation or interception. | plugins/autopilot/scripts/codex.py:23 | 1.1 | BLAKE |
| R4 | [1/4] | 🟠 | Compatibility assets are capability lists, not client assets. `compatibility/*.json` hold only host_id, capabilities and probe_kind. There is no hook registration, no packaged Claude hooks and no Codex hook bundle. `guards.py` is a library invoked only through `--run-guard`, and nothing intercepts any client action. The spec requires retaining Claude hooks through supported packaging and proving each additional client's registration, identity and interception, and generating self-contained supported client assets. `interception` is declared "supported" for Claude on binary-on-PATH plus an env var alone. | plugins/autopilot/compatibility/claude.json:1 | 1.2 | BLAKE |
| R5 | [1/4] | 🟠 | Phase 2 headless probes are static only (binary on PATH plus auth presence). `probe-host.py` and every adapter `probe()` perform no real invocation. They use no isolated plugin or project location, and they check no resource, identity or interception. The acceptance text requires `relocated_host_probe` and `missing_guard_refused` to verify real invocation/resources/identity/interception and report denied mandatory capabilities. No `relocated_host_probe` test exists. `missing_guard_refused` is only a pure-guard input-shape check. | tools/autopilot/probe-host.py:31 | 2.1 | BLAKE |
| R6 | [1/4] | 🟠 | Codex still declares isolation implemented, but its adapter contains no isolation implementation: identity and argv remain unconditional None, delegation remains False, and probing only checks binary/auth presence. Remove isolation from the implemented set, declaration, and bundle until a concrete adapter path supports it; renaming the status to supported does not close this part of prior R10/R11. | plugins/autopilot/scripts/codex.py:24 | 18 | BOB |
| R7 | [1/4] | 🟠 | The generator now imports a module named directly by contract input, replacing the previous restricted host dispatcher. An unknown host can execute an unrelated module’s import-time code before the missing IMPLEMENTED_CAPABILITIES attribute fails. Validate host IDs against an explicit adapter table before importing; test that rejected names execute no module. | tools/autopilot/build-compatibility.py:24 | 19 | BOB |
| R8 | [1/4] | 🟡 | Prior R15/R21 is unresolved. `doctor.profile` is still derived as `"identity" in codex ∪ gemini declared capabilities`. After this rework that is a constant "mixed", because codex and gemini no longer declare identity, so "claude-free" is unreachable. The spec derives the profile from whether every mandatory review-policy role resolves to codex or gemini. | plugins/autopilot/scripts/doctor.py:40 | 7 | ALICE |
| R9 | [1/4] | 🟡 | `IMPLEMENTED_CAPABILITIES` is a bare literal that no code or test ties to behavior. Claude "isolation" and "interception" and Codex "isolation" have no adapter code behind them; `build_job_argv` returns None for every host. `build-compatibility.py` checks hosts.json against that same literal, so "no unsupported capability is advertised" can never fail. Add a test per claimed capability that exercises the adapter surface it names (e.g. `session_identity()` returns a record when `CLAUDE_SESSION_ID` is set). Otherwise state in the module docstring that these are declarations. | plugins/autopilot/scripts/codex.py:23 | 17 | ALICE |
| R10 | [1/4] | 🟡 | Behavior change in `claude.probe`. The old code kept interception "available" regardless of auth, because hook registration is a client feature. `statuses_from` now gates every Claude capability, interception included, on `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`. In a keychain-login session, `--diagnose` shows all four Claude capabilities as `unavailable/no_auth`. The auth check still ignores login-based auth (prior R16 residue). | plugins/autopilot/scripts/claude.py:33 | 11 | ALICE |
| R11 | [1/4] | 🟡 | `CAPABILITY_STATUSES` is defined but unused in production. `CapabilityStatus` does not validate `status` against it. Its only consumer is a test that equates the tuple with a literal, which pins the constant but not the vocabulary actually emitted. Either validate in `CapabilityStatus.__post_init__` or drop the constant. | plugins/autopilot/scripts/hosts.py:28 | 11 | ALICE |
| R12 | [1/4] | 🟡 | Recursion bound is only an exact (host_id, job_id) ancestry match. There is no depth cap, and a child that carries a new job_id on the same host is not denied. The spec says to preserve bounded recursion and permissions. No `reviewer_isolation` or `child_cleanup` scenario is implemented or tested, although the spec's Phase 1 acceptance and Test Strategy name both. | plugins/autopilot/scripts/jobs.py:70 | 1.1 | BLAKE |
| R13 | [1/4] | 🟡 | Standalone mode emits no usable next-session instruction. `host.build_job_argv` returns None for all three adapters, so `request_cross_session_job` yields `{"argv": None, ...}`. The spec says standalone mode emits next-session instructions for manual launch. | plugins/autopilot/scripts/jobs.py:89 | 1.1 | BLAKE |
| R14 | [1/4] | 🟡 | Phase 0 characterization is thin. `test_host_argv.py` tests probe dispatch, not runner argv. `effort_forwarding` only asserts that argv is never produced. There is no `hook_behavior_equivalence` scenario, and no corrected-target case exposing the known Sonnet effort mismatch. | tests/autopilot/test_host_argv.py:1 | 0.1 | BLAKE |
| R15 | [1/4] | 🟡 | Changelog and README do not cover the full required scope. The changelog entry mentions only the adapters and bundles. It omits guards, `jobs.py` and `doctor.py`, and it does not list the duties still unavailable per client. The README does not document `--probe-host`, `--run-guard` or `--diagnose`. | plugins/autopilot/CHANGELOG.md:7 | 2.2 | BLAKE |
| R16 | [1/4] | 🟡 | The new pure-guard requirements break diagnose’s existing caller: its empty contexts now produce five permanent missing-input refusals. Supply explicit simulated passing contexts for the library self-check and retain guards_simulated=True; add a diagnose integration test. A task-specific file allowlist does not make this integration regression outside AP00014. | plugins/autopilot/scripts/guards.py:94 | 20 | BOB |
| R17 | [1/4] | 🟡 | Document-location enforcement depends on path spelling: backlog/x.md is denied, while /repo/backlog/x.md is allowed because parts[0] is "/". Normalize against an explicit project root before checking root-level lifecycle directories, and test equivalent absolute and relative paths. | plugins/autopilot/scripts/guards.py:138 | 20 | BOB |
| R18 | [1/4] | 🟡 | The new scanner test labels while 10 as benign, although it is an unconditional loop just like while 1. Remove that false negative expectation and inspect literal truthiness with AST parsing if unconditional-loop detection remains the intended rule. | tests/autopilot/test_compatibility.py:545 | 19 | BOB |
| R19 | [1/4] | 🟡 | The collision test pre-seeds only a short wall-clock window and assumes the subprocess starts within it. A delayed runner selects an unseeded timestamp and fails the required -2.json assertion despite correct behavior. Freeze the tool’s clock in a controlled invocation and test collision retries deterministically. | tests/autopilot/test_host_argv.py:513 | 17 | BOB |
| R20 | [1/4] | 🟡 | Bundle tests retain a recursive schema-agnostic token collector while now asserting exact keys and exact serialized bytes. Remove the redundant collector and its assertions; the existing exact-byte comparison checks the same capability content more directly. | tests/autopilot/test_compatibility.py:182 | 19 | BOB |
| R21 | [1/4] | 🟡 | Prior R9 remains partially unresolved: static observation and evidence labeling are implemented, but live execution certification is absent. The rework explicitly assigns certification to AP00017 and managed launch to OV00059. | tools/autopilot/probe-host.py:2 | 17 | BOB |
| R22 | [1/4] | 🟡 | Prior R13–R15/R21 retain their deferred portions: facade/doctor coverage, policy-driven role resolution, and correct profile derivation were excluded by the recorded scope cap. Probe-host coverage now exists; it does not close those remaining obligations. | tests/autopilot/test_sessions.py:135 | general | BOB |
| R23 | [1/4] | 🟡 | Prior R17–R19 retain their deferred execution/resource, standalone-instruction, and hook-packaging obligations. This incremental rework changes capability reporting and guard decisions, while the recorded scope-cap decision leaves those features for later work. | N/A | general | BOB |
| R24 | [1/4] | ⚪ | In the evidence-filename retry loop, `if attempt == 10: raise` inside `except FileExistsError` is a hand-rolled bound. A `for ... else` or a named constant would read simpler with the same behavior. | tools/autopilot/probe-host.py:46 | 8 | ALICE |
| R25 | [1/4] | ⚪ | `claude.session_identity()` trusts the `CLAUDE_SESSION_ID` env var, which has no verification and so cannot be called native identity proof. `codex.py` evaluates `Path.home()` at import time, so the auth probe is frozen to the importing process's HOME. | plugins/autopilot/scripts/claude.py:56 | 1.1 | BLAKE |
| R26 | [1/4] | ⚪ | The test gate reported exit 1 with no summary line. My narrow run of test_jobs, test_guards, test_guards_pure_duties, test_sessions, test_host_argv and test_compatibility passed (171 passed). `python3 scripts/validate.py` passed. The cause of the full-suite exit 1 is unverified. | N/A | general | BLAKE |
| R27 | [1/4] | 🟡 | 7 touched test(s) pass against the pre-change code: test_scrubbed_authenticated_and_alien_envs_reach_the_child_process, test_accepts_project_root_flag_exits_zero_and_never_touches_the_real_repo, test_committed_bundles_are_what_the_repo_contract_builds, test_does_not_flag_near_miss_substrings, test_no_autopilot_python_file_imports_a_scheduler_or_a_tui_runtime, test_rejects_while_one_in_synthetic_source +1 more | tests/autopilot/test_compatibility.py | general | mech-check |
| R28 | [1/4] | 🟡 | 2 touched test(s) pass against the pre-change code: test_pure_duties_do_not_refuse_without_seam, test_seam_rules_for_the_pure_duty_are_ignored | tests/autopilot/test_guards.py | general | mech-check |
| R29 | [1/4] | 🟡 | 16 touched test(s) pass against the pre-change code: test_allows_a_file_in_a_known_store_directory, test_allows_a_path_outside_the_store, test_allows_a_path_that_only_resembles_the_store_segment, test_allows_a_prd_in_each_lifecycle_directory, test_allows_a_traversal_that_resolves_to_an_allowed_location, test_allows_each_keeper_file_directly_under_meta +10 more | tests/autopilot/test_guards_pure_duties.py | general | mech-check |
| R30 | [1/4] | 🟡 | 2 touched test(s) pass against the pre-change code: test_probe_host_refuses_a_symlinked_probes_dir, test_undispatchable_host_id_exits_nonzero_and_writes_no_evidence | tests/autopilot/test_host_argv.py | general | mech-check |
| R31 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_target_only_checkout_denies_source_home_and_network_but_exports_policy | tests/autopilot/test_package.py | general | mech-check |
| R32 | [1/4] | 🟡 | 5 touched test(s) pass against the pre-change code: test_build_job_argv_succeeds_for_codex_and_gemini, test_can_delegate_succeeds_for_codex_and_gemini, test_probe_host_succeeds_for_codex_and_gemini, test_every_adapter_rejects_a_probe_without_a_keyword_project_root, test_every_adapter_takes_project_root_as_its_only_required_keyword | tests/autopilot/test_sessions.py | general | mech-check |

### Auto-dismissed (ledger)

- [BLAKE] 🟠 Stateful guard relay is fail-open on malformed seam verdicts. `_relay` copies `verdict["allowed"]` without a bool check. I verified that a seam returning `{"allowed": "no", "reason": None}` yields `GuardOutcome(allowed='no')`, which is truthy to any consumer. A verdict missing keys raises a bare KeyError instead of a refusal. The pure guards fail closed on mistyped input; the stateful ones do not. | File: plugins/autopilot/scripts/guards.py:39 — single-voice
- [BLAKE] 🟠 Job intents do not require effort or record input digests. `build_job_intent` accepts empty strings for job_id, role, tier and effort, and I verified `effort=''` builds a JobIntent. The spec says to require the intended effort in job metadata. It also says to record actual native sessions and resolved input digests for controller evidence. `JobIntent` carries no session record and no digest computation or validation, and `inputs` is a free-form dict. | File: plugins/autopilot/scripts/jobs.py:49 — single-voice

## Alice

[ALICE] 🔴 Prior R7/R24 is NOT resolved. `test_new_helper_files_are_owned_and_digested_from_current_bytes` still fails. I ran tests/autopilot test_guards*, test_compatibility, test_host_argv, test_sessions, test_jobs, test_package, test_helper_provenance_real, test_local_boundary and test_facade: 228 passed, 1 failed. The failure is `assert_refreshed_evidence`, which compares the blob of plugins/autopilot/CHANGELOG.md at `tested_package_revision` with the current bytes. The rework refreshed `destination_blob_sha256` (task 16), but the test also requires the file at the tested revision to equal the file on disk. AP00014 edited CHANGELOG.md and autopilot.py after that revision, so the test cannot pass as written. The test passed at the PRD base commit, so this is still an AP00014 regression. Fix: re-test the package and update the evidence revision, or scope the check as AP00018 did for its rows. Also add the AP00014-touched REFRESHED paths to the exemption. | File: tests/autopilot/test_helper_provenance_real.py:300 | Task: 16
[ALICE] 🟡 `doctor.diagnose` calls `run_guard(duty, {}, ...)` for all nine duties. The five pure duties now deny on missing input, so `autopilot.py --diagnose` always reports document_location, delegation, post_handoff, departure and context_reinjection as `allowed: false`. I ran it and confirmed. The assumptions file records this as a deferred out-of-scope item, but the doctor is a caller of the changed guards and its report is now misleading. No test covers `diagnose` output. Fix: pass a representative allow-context per pure duty, or label these entries "not evaluated", and add one diagnose test. | File: plugins/autopilot/scripts/doctor.py:38 | Task: 20
[ALICE] 🟡 Prior R15/R21 is unresolved. `doctor.profile` is still derived as `"identity" in codex ∪ gemini declared capabilities`. After this rework that is a constant "mixed", because codex and gemini no longer declare identity, so "claude-free" is unreachable. The spec derives the profile from whether every mandatory review-policy role resolves to codex or gemini. | File: plugins/autopilot/scripts/doctor.py:40 | Task: 7
[ALICE] 🟡 `IMPLEMENTED_CAPABILITIES` is a bare literal that no code or test ties to behavior. Claude "isolation" and "interception" and Codex "isolation" have no adapter code behind them; `build_job_argv` returns None for every host. `build-compatibility.py` checks hosts.json against that same literal, so "no unsupported capability is advertised" can never fail. Add a test per claimed capability that exercises the adapter surface it names (e.g. `session_identity()` returns a record when `CLAUDE_SESSION_ID` is set). Otherwise state in the module docstring that these are declarations. | File: plugins/autopilot/scripts/codex.py:23 | Task: 17
[ALICE] 🟡 Behavior change in `claude.probe`. The old code kept interception "available" regardless of auth, because hook registration is a client feature. `statuses_from` now gates every Claude capability, interception included, on `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`. In a keychain-login session, `--diagnose` shows all four Claude capabilities as `unavailable/no_auth`. The auth check still ignores login-based auth (prior R16 residue). | File: plugins/autopilot/scripts/claude.py:33 | Task: 11
[ALICE] 🟡 `CAPABILITY_STATUSES` is defined but unused in production. `CapabilityStatus` does not validate `status` against it. Its only consumer is a test that equates the tuple with a literal, which pins the constant but not the vocabulary actually emitted. Either validate in `CapabilityStatus.__post_init__` or drop the constant. | File: plugins/autopilot/scripts/hosts.py:28 | Task: 11
[ALICE] ⚪ In the evidence-filename retry loop, `if attempt == 10: raise` inside `except FileExistsError` is a hand-rolled bound. A `for ... else` or a named constant would read simpler with the same behavior. | File: tools/autopilot/probe-host.py:46 | Task: 8

Prior findings verified resolved: R1 (unavailable gemini returns capability None via `hosts.unavailable`, and `ProbeResult.__post_init__` enforces it), R2/R20 (pure guards now check real inputs, fail closed, traversal denied), R3/R10/R11/R16 (declared set equals the implemented set, and bundles are machine-independent and deterministic), R5/R6 (test_package and test_local_boundary updated, now passing), R8 (generator check passes), R12 (AP00014 row-integrity tests added), R22 (bundles are no longer probe-derived), R23 (`O_EXCL` plus retry), R26/R36 (evidence path and binary path recorded), R42 (trailing newline).

Prior R7 is not resolved (first finding above). R9/R13/R14/R17/R18/R19 (real probes, the diagnose/run-guard CLI tests, the job-request resolver test, child cleanup, standalone instructions, hook packaging) were not addressed by this rework, and I found no deferral for them in the ledger.

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
R13: pass

## Blake

[BLAKE] 🟠 Claude-free profile is not implemented. Codex declares only `isolation` and Gemini declares nothing, so both `session_identity()` return None, `can_delegate()` is False and `build_job_argv()` is None. The spec says to implement applicable native identity/input/guard support for the Codex implementer and Gemini doubt reviewer. Documenting a blocker is allowed for certification only. `doctor.diagnose` derives profile "mixed" because "identity" is not covered. Only Claude has identity, delegation or interception. | File: plugins/autopilot/scripts/codex.py:23 | Task: 1.1
[BLAKE] 🟠 Compatibility assets are capability lists, not client assets. `compatibility/*.json` hold only host_id, capabilities and probe_kind. There is no hook registration, no packaged Claude hooks and no Codex hook bundle. `guards.py` is a library invoked only through `--run-guard`, and nothing intercepts any client action. The spec requires retaining Claude hooks through supported packaging and proving each additional client's registration, identity and interception, and generating self-contained supported client assets. `interception` is declared "supported" for Claude on binary-on-PATH plus an env var alone. | File: plugins/autopilot/compatibility/claude.json:1 | Task: 1.2
[BLAKE] 🟠 Stateful guard relay is fail-open on malformed seam verdicts. `_relay` copies `verdict["allowed"]` without a bool check. I verified that a seam returning `{"allowed": "no", "reason": None}` yields `GuardOutcome(allowed='no')`, which is truthy to any consumer. A verdict missing keys raises a bare KeyError instead of a refusal. The pure guards fail closed on mistyped input; the stateful ones do not. | File: plugins/autopilot/scripts/guards.py:39 | Task: 1.2
[BLAKE] 🟠 Phase 2 headless probes are static only (binary on PATH plus auth presence). `probe-host.py` and every adapter `probe()` perform no real invocation. They use no isolated plugin or project location, and they check no resource, identity or interception. The acceptance text requires `relocated_host_probe` and `missing_guard_refused` to verify real invocation/resources/identity/interception and report denied mandatory capabilities. No `relocated_host_probe` test exists. `missing_guard_refused` is only a pure-guard input-shape check. | File: tools/autopilot/probe-host.py:31 | Task: 2.1
[BLAKE] 🟠 Job intents do not require effort or record input digests. `build_job_intent` accepts empty strings for job_id, role, tier and effort, and I verified `effort=''` builds a JobIntent. The spec says to require the intended effort in job metadata. It also says to record actual native sessions and resolved input digests for controller evidence. `JobIntent` carries no session record and no digest computation or validation, and `inputs` is a free-form dict. | File: plugins/autopilot/scripts/jobs.py:49 | Task: 1.1
[BLAKE] 🟡 Recursion bound is only an exact (host_id, job_id) ancestry match. There is no depth cap, and a child that carries a new job_id on the same host is not denied. The spec says to preserve bounded recursion and permissions. No `reviewer_isolation` or `child_cleanup` scenario is implemented or tested, although the spec's Phase 1 acceptance and Test Strategy name both. | File: plugins/autopilot/scripts/jobs.py:70 | Task: 1.1
[BLAKE] 🟡 Standalone mode emits no usable next-session instruction. `host.build_job_argv` returns None for all three adapters, so `request_cross_session_job` yields `{"argv": None, ...}`. The spec says standalone mode emits next-session instructions for manual launch. | File: plugins/autopilot/scripts/jobs.py:89 | Task: 1.1
[BLAKE] 🟡 Phase 0 characterization is thin. `test_host_argv.py` tests probe dispatch, not runner argv. `effort_forwarding` only asserts that argv is never produced. There is no `hook_behavior_equivalence` scenario, and no corrected-target case exposing the known Sonnet effort mismatch. | File: tests/autopilot/test_host_argv.py:1 | Task: 0.1
[BLAKE] 🟡 Changelog and README do not cover the full required scope. The changelog entry mentions only the adapters and bundles. It omits guards, `jobs.py` and `doctor.py`, and it does not list the duties still unavailable per client. The README does not document `--probe-host`, `--run-guard` or `--diagnose`. | File: plugins/autopilot/CHANGELOG.md:7 | Task: 2.2
[BLAKE] 🟡 `doctor.diagnose` runs every guard against an always-allow FakeSeam with an empty context `{}`. It is labelled `guards_simulated`, but the pure guards all deny on `{}`. The report therefore shows guards "denying" for no real reason and proves nothing about interception. `FakeSeam` also ships in the distributed package (`jobs.py`). | File: plugins/autopilot/scripts/doctor.py:38 | Task: 1.2
[BLAKE] ⚪ `claude.session_identity()` trusts the `CLAUDE_SESSION_ID` env var, which has no verification and so cannot be called native identity proof. `codex.py` evaluates `Path.home()` at import time, so the auth probe is frozen to the importing process's HOME. | File: plugins/autopilot/scripts/claude.py:56 | Task: 1.1
[BLAKE] ⚪ The test gate reported exit 1 with no summary line. My narrow run of test_jobs, test_guards, test_guards_pure_duties, test_sessions, test_host_argv and test_compatibility passed (171 passed). `python3 scripts/validate.py` passed. The cause of the full-suite exit 1 is unverified. | File: N/A | Task: general

B1: fail
B2: pass
B3: fail
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
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

FIX:

- [BOB] 🟠 Codex still declares isolation implemented, but its adapter contains no isolation implementation: identity and argv remain unconditional None, delegation remains False, and probing only checks binary/auth presence. Remove isolation from the implemented set, declaration, and bundle until a concrete adapter path supports it; renaming the status to supported does not close this part of prior R10/R11. | File: plugins/autopilot/scripts/codex.py:24 | Task: 18
- [BOB] 🟠 The generator now imports a module named directly by contract input, replacing the previous restricted host dispatcher. An unknown host can execute an unrelated module’s import-time code before the missing IMPLEMENTED_CAPABILITIES attribute fails. Validate host IDs against an explicit adapter table before importing; test that rejected names execute no module. | File: tools/autopilot/build-compatibility.py:24 | Task: 19
- [BOB] 🟡 The new pure-guard requirements break diagnose’s existing caller: its empty contexts now produce five permanent missing-input refusals. Supply explicit simulated passing contexts for the library self-check and retain guards_simulated=True; add a diagnose integration test. A task-specific file allowlist does not make this integration regression outside AP00014. | File: plugins/autopilot/scripts/guards.py:94 | Task: 20
- [BOB] 🟡 Document-location enforcement depends on path spelling: backlog/x.md is denied, while /repo/backlog/x.md is allowed because parts[0] is "/". Normalize against an explicit project root before checking root-level lifecycle directories, and test equivalent absolute and relative paths. | File: plugins/autopilot/scripts/guards.py:138 | Task: 20
- [BOB] 🟡 The new scanner test labels while 10 as benign, although it is an unconditional loop just like while 1. Remove that false negative expectation and inspect literal truthiness with AST parsing if unconditional-loop detection remains the intended rule. | File: tests/autopilot/test_compatibility.py:545 | Task: 19
- [BOB] 🟡 The collision test pre-seeds only a short wall-clock window and assumes the subprocess starts within it. A delayed runner selects an unseeded timestamp and fails the required -2.json assertion despite correct behavior. Freeze the tool’s clock in a controlled invocation and test collision retries deterministically. | File: tests/autopilot/test_host_argv.py:513 | Task: 17
- [BOB] 🟡 Bundle tests retain a recursive schema-agnostic token collector while now asserting exact keys and exact serialized bytes. Remove the redundant collector and its assertions; the existing exact-byte comparison checks the same capability content more directly. | File: tests/autopilot/test_compatibility.py:182 | Task: 19

VERIFY:

- (none)

KNOWN:

- [BOB] 🟡 Prior R4/R24 remain partially unresolved: the supplied run still fails the historical delivery-receipt assertion after digest regeneration. This is explicitly deferred because the pinned AP00013 package revision and receipt ownership are outside this rework’s assigned scope; it must not be recorded as a fully closed test-regression cluster. | File: tests/autopilot/test_helper_provenance_real.py:303 | Task: 16
- [BOB] 🟡 Prior R9 remains partially unresolved: static observation and evidence labeling are implemented, but live execution certification is absent. The rework explicitly assigns certification to AP00017 and managed launch to OV00059. | File: tools/autopilot/probe-host.py:2 | Task: 17
- [BOB] 🟡 Prior R13–R15/R21 retain their deferred portions: facade/doctor coverage, policy-driven role resolution, and correct profile derivation were excluded by the recorded scope cap. Probe-host coverage now exists; it does not close those remaining obligations. | File: tests/autopilot/test_sessions.py:135 | Task: general
- [BOB] 🟡 Prior R17–R19 retain their deferred execution/resource, standalone-instruction, and hook-packaging obligations. This incremental rework changes capability reporting and guard decisions, while the recorded scope-cap decision leaves those features for later work. | File: N/A | Task: general

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: fail
R9: fail
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

I am reviewing the review context, the diff, and the engram pack for cycle 2 of AP00014.

 MD Read docs/dev/tmp/review-context-ap14c2.md 1 line read

 ● Read docs/dev/tmp/review-diff-ap14c2.diff 1 line read

 MD Read docs/dev/tmp/engram-pack-ap14c2.md 225 lines read

I will inspect the review context and diff to understand the changes made during rework and check the prior cycle's findings.

 $ Shell Check line counts of review context and diff 3 lines…
   wc -l docs/dev/tmp/review-context-ap14c2.md docs/dev/tmp/review-diff-ap14c2.diff

 MD Read docs/dev/tmp/review-context-ap14c2.md L1:200 (11 lines read)

 $ Shell Find section headings in review context 55 lines…
   grep -n "^#" docs/dev/tmp/review-context-ap14c2.md

 MD Read docs/dev/tmp/review-context-ap14c2.md L28:74 (47 lines read)

 MD Read docs/dev/tmp/review-context-ap14c2.md L893:950 (58 lines read)

 MD Read docs/dev/tmp/review-context-ap14c2.md L1250:1332 (83 lines read)

 $ Shell Run autopilot test suite 21 lines…                                                      30s
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/

 $ Shell List all files in diff 32 lines…
   grep "^diff --git" docs/dev/tmp/review-diff-ap14c2.diff

 ● Read shell output Waiting up to 10 seconds for command output 32 lines…                       10s

 $ Shell Check recent commits 5 lines…
   git log -n 5 --oneline

 $ Shell Check last 15 commits 15 lines…
   git log -n 15 --oneline

 $ Shell Check last 30 commits 30 lines…
   git log -n 30 --oneline

 ● Read shell output Waiting up to 5 seconds for command output 38 lines…                         5s

 $ Shell Run tests for AP00014 touched files 65 lines…                                           30s
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_compatibility.py tests/autopilot/test_guards.py
   tests/autopilot/test_guards_pure_duties.py tests/autopilot/test_helper_provenance_real.py
   tests/autopilot/test_host_argv.py tests/autopilot/test_local_boundary.py
   tests/autopilot/test_package.py tests/autopilot/test_sessions.py -q

 PY Read tests/autopilot/test_helper_provenance_real.py L280:335 (56 lines read)

 PY Read tests/autopilot/test_helper_provenance_real.py L20:70 (51 lines read)

 / Search "REFRESHED\s*=" (tests/autopilot/test_helper_provenance.py) 1 file found

 PY Read tests/autopilot/test_helper_provenance.py L50:85 (36 lines read)

 / Search "REFRESHED" (tests/autopilot/test_helper_provenance.py) 6 lines found

 PY Read tests/autopilot/test_helper_provenance.py L35:50 (16 lines read)

 / Search "package_revision" (tools/autopilot/source-map.json) 28 lines found

 $ Shell Check diff of CHANGELOG.md 13 lines…
   git diff 68418c5a3c8951abfbac494ddc9cdae0d6408a06 -- plugins/autopilot/CHANGELOG.md

 $ Shell Check evidence for refreshed assets in source-map.json 7 lines…
   python3 -c '
   import json, pathlib
   root = pathlib.Path(".")
   smap = json.loads((root / "tools/autopilot/source-map.json").read_bytes())
   assets = {a["destination_path"]: a for a in smap["assets"]}
   for p in ["plugins/autopilot/scripts/autopilot.py", "plugins/autopilot/README.md",
   "plugins/autopilot/CHANGELOG.md"]:
       print(p, assets[p]["evidence"])
   '

 $ Shell Check sha256 of CHANGELOG.md at revision vs current 2 lines…
   git show 444d733a32c76623a388a0ee64098b4d1eb60757:plugins/autopilot/CHANGELOG.md | sha256sum;
   sha256sum plugins/autopilot/CHANGELOG.md

 $ Shell Check commit 5008cd5 8 lines…
   git show --stat 5008cd5

 $ Shell View diff of commit 5008cd5 118 lines…
   git show 5008cd5

 $ Shell Run test_package.py and test_local_boundary.py 2 lines…                                 18s
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_package.py tests/autopilot/test_local_boundary.py -q

 ● Read shell output Reading command output 65 lines…

 ● Stop shell  1 line…

 $ Shell Run repository validation 1 line…
   python3 scripts/validate.py

 $ Shell Run validator tests 5 lines…
   python3 -m unittest discover -s scripts

 PY Read plugins/autopilot/scripts/gemini.py L1:60 (55 lines read)

 PY Read plugins/autopilot/scripts/hosts.py L45:125 (81 lines read)

 PY Read plugins/autopilot/scripts/guards.py L80:180 (101 lines read)

 PY Read plugins/autopilot/scripts/guards.py L180:235 (56 lines read)

 {} Read plugins/autopilot/contracts/hosts.json 8 lines read

 PY Read plugins/autopilot/scripts/codex.py L1:65 (60 lines read)

 PY Read plugins/autopilot/scripts/claude.py L1:60 (59 lines read)

 {} Read plugins/autopilot/compatibility/claude.json 10 lines read

 {} Read plugins/autopilot/compatibility/codex.json 7 lines read

 {} Read plugins/autopilot/compatibility/gemini.json 5 lines read

 PY Read tools/autopilot/build-compatibility.py L1:65 (64 lines read)

 / Search "task 1[56]" (docs/dev/project-management/designs/00014-autopilot-host-e… No matches found

 / Search "Task \d+" (docs/dev/project-management/designs/00014-autopilot-host-exe… No matches found

 / Search "^#+ " (docs/dev/project-management/designs/00014-autopilot-host-execution… 30 lines found

 MD Read docs/dev/project-management/designs/00014-autopilot-host-execution-v1-  L631:706 (75 lines…
         rework-1-design.md

 MD Read docs/dev/project-management/designs/00014-autopilot-host-execution-v1-  L788:816 (28 lines…
         rework-1-design.md

 / Search "REFRESHED" (tools/autopilot/update_helper_map.py) 3 lines found

 PY Read tools/autopilot/update_helper_map.py L525:565 (41 lines read)

 PY Read tools/autopilot/update_helper_map.py L500:525 (26 lines read)

 $ Shell View diff of test_helper_provenance_real.py 65 lines…
   git diff 68418c5a3c8951abfbac494ddc9cdae0d6408a06 --
   tests/autopilot/test_helper_provenance_real.py

 / Search "test_.*fail" (docs/dev/project-management/reviews/00014-autopilot-host-ex… 13 lines found

 $ Shell Run tests ignoring AP00018 controller suites 5 lines…                                   30s
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/ --ignore=tests/autopilot/test_controller_capacity.py
   --ignore=tests/autopilot/test_controller_owner.py
   --ignore=tests/autopilot/test_controller_owner_recovery.py -q

 $ Shell Check diff of probe-host.py 66 lines…
   git diff 68418c5a3c8951abfbac494ddc9cdae0d6408a06 -- tools/autopilot/probe-host.py

 ● Read shell output Waiting up to 10 seconds for command output 6 lines…                        10s

 $ Shell Check diff of test_sessions.py 356 lines…
   git diff 68418c5a3c8951abfbac494ddc9cdae0d6408a06 -- tests/autopilot/test_sessions.py

 ● Read shell output Waiting up to 10 seconds for command output 7 lines…                        10s

 $ Shell Check diff of test_compatibility.py 14 lines…
   git diff 68418c5a3c8951abfbac494ddc9cdae0d6408a06 -- tests/autopilot/test_compatibility.py

 $ Shell Run test_compatibility.py 2 lines…
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_compatibility.py -q

 $ Shell Run test_guards_pure_duties.py 2 lines…
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_guards_pure_duties.py -q

 $ Shell Run test_guards.py 2 lines…
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_guards.py -q

 $ Shell Run test_host_argv.py 2 lines…
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_host_argv.py -q

 $ Shell Run test_sessions.py 2 lines…
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_sessions.py -q

 $ Shell Run test_package.py 2 lines…
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_package.py -q

 $ Shell Run test_local_boundary.py 2 lines…                                                     16s
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_local_boundary.py -q

 ✗ Shell  ....F.........                                                           [100%] ==========
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_helper_provenance_real.py -q
   ....F.........                                                           [100%]
   =================================== FAILURES ===================================
   _______ test_new_helper_files_are_owned_and_digested_from_current_bytes ________
   
   mapping = {'assets': [{'acceptance_cases': [{'case_id': 'asset-.claude-plugin/plugin.json', 
   'expected_outcome': 'Installed plugi...hosts and missing receipts remain incomplete; no source 
   retirement or profile release is authorized by this map.', ...}
   
       def test_new_helper_files_are_owned_and_digested_from_current_bytes(
           mapping: dict,
       ) -> None:
           assets = single_assets(mapping, sorted(HELPER_TARGETS) + list(REFRESHED))
           owners = by_key(mapping["authored_file_owners"], "path")
           for path in sorted(HELPER_TARGETS) + list(REFRESHED):
               assert assets[path]["destination_blob_sha256"] == digest(
                   (ROOT / path).read_bytes()
               ), path
           for path in sorted(HELPER_TARGETS):
               row = assets[path]
               assert row["source_asset_id"] is None and row["source_blob_sha256"] is None
               assert_receipts_file(row["evidence"])
               owner = owners[path]
               assert owner["delivery_prd"] == "00013"
               assert owner["owner_repository"] == "buvis/agent-plugins"
               assert owner["source_asset_id"] is None and owner["source_blob_sha256"] is None
               assert owner["acceptance_cases"]
   >       assert_refreshed_evidence(assets)
   
   tests/autopilot/test_helper_provenance_real.py:321: 
   _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
   
   assets = {'plugins/autopilot/CHANGELOG.md': {'acceptance_cases': [{'case_id': 
   'asset-new-CHANGELOG.md', 'expected_outcome': 
   'Th...c3d31a3cc980e953a18edcce09cb3ce9ee9091651bb5', 'destination_path': 
   'plugins/autopilot/scripts/cap_check.py', ...}, ...}
   
       def assert_refreshed_evidence(assets: dict) -> None:
           receipts_evidence = assets[sorted(HELPER_TARGETS)[0]]["evidence"]
           assert assets[REFRESHED[0]]["evidence"] == receipts_evidence
           receipts = json.loads((ROOT / receipts_evidence["artifact_id"]).read_bytes())
           revision = receipts["package_revision"]
           assert re.fullmatch(r"[0-9a-f]{40}", revision), revision
           for path in REFRESHED[1:]:
               sha = digest((ROOT / path).read_bytes())
               assert assets[path]["evidence"] == {
                   "status": "passed",
                   "artifact_id": path,
                   "artifact_sha256": sha,
                   "tested_package_revision": revision,
               }, path
               shown = subprocess.run(
                   ["git", "-C", str(ROOT), "show", f"{revision}:{path}"],
                   capture_output=True,
                   timeout=60,
               )
               assert shown.returncode == 0, shown.stderr
   >           assert digest(shown.stdout) == sha, path
   E           AssertionError: plugins/autopilot/CHANGELOG.md
   E           assert '358363778bb4...b32426b89008f' == 'a478a34bcea1...c6e85a7a5e7b6'
   E             
   E             - a478a34bcea1c2593c8b0d26fd0818b9ae1b4caf5f820637d65c6e85a7a5e7b6
   E             + 358363778bb44e6d7ef87e3be2518456f1605f967ba9db1d870b32426b89008f
   
   tests/autopilot/test_helper_provenance_real.py:300: AssertionError
   =========================== short test summary info ============================
   FAILED tests/autopilot/test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digest
   ed_from_current_bytes
   1 failed, 13 passed in 8.08s
   Failed with exit code 1

 ● Stop shell  1 line…

 / Search "test_helper_provenance_real" (docs/dev/project-management/autopilot/state… 16 lines found

 {} Read docs/dev/project-management/autopilot/state.json L970:1010 (27 lines read)

 {} Read docs/dev/project-management/autopilot/state.json L1180:1235 (56 lines read)

 / Search "source-map.json" (docs/dev/project-management/autopilot/state.json) 16 lines found

 {} Read docs/dev/project-management/autopilot/state.json L1010:1050 (19 lines read)

 $ Shell Check SHA of CHANGELOG.md at base commit 635e376 1 line…
   git show 635e376:plugins/autopilot/CHANGELOG.md | sha256sum

 $ Shell Check file line counts 16 lines…
   wc -l plugins/autopilot/scripts/claude.py plugins/autopilot/scripts/codex.py
   plugins/autopilot/scripts/gemini.py plugins/autopilot/scripts/guards.py
   plugins/autopilot/scripts/hosts.py tools/autopilot/probe-host.py
   tools/autopilot/build-compatibility.py tools/autopilot/update_helper_map.py
   tests/autopilot/test_guards_pure_duties.py tests/autopilot/test_compatibility.py
   tests/autopilot/test_host_argv.py tests/autopilot/test_sessions.py
   tests/autopilot/test_helper_provenance_real.py

 ✗ Shell Check for TODO/FIXME in diff  Failed with exit code 1
   git diff 68418c5a3c8951abfbac494ddc9cdae0d6408a06 -- plugins/ tools/ tests/ | grep -E
   "^\+[[:space:]]*#(.*)(TODO|FIXME|XXX|DEBUG)"

 ✗ Shell Check for skipped tests in diff  Failed with exit code 1
   git diff 68418c5a3c8951abfbac494ddc9cdae0d6408a06 -- tests/ | grep -E
   "^\+[[:space:]]*@(pytest\.mark\.)?skip"

 $ Shell Test autopilot.py --list-capabilities 1 line…
   python3 plugins/autopilot/scripts/autopilot.py --list-capabilities

 ✗ Shell  usage: autopilot.py [-h] (--list-capabilities | --export-policy | --stage-review STAGE_REV
   python3 plugins/autopilot/scripts/autopilot.py --diagnose
   usage: autopilot.py [-h] (--list-capabilities | --export-policy |
                       --stage-review STAGE_REVIEW |
                       --group-findings GROUP_FINDINGS |
                       --check-evidence CHECK_EVIDENCE |
                       --prepare-close PREPARE_CLOSE | --catchup-probe |
                       --verify | --controller-action CONTROLLER_ACTION |
                       --probe-host PROBE_HOST | --run-guard RUN_GUARD |
                       --diagnose) [--out OUT]
                       [--expected-context EXPECTED_CONTEXT] [--policy POLICY]
                       [--project-root PROJECT_ROOT] [--artifact ARTIFACT]
                       [--log LOG] [--context CONTEXT] [--head-sha HEAD_SHA]
                       [--timeout TIMEOUT]
   autopilot.py: error: --diagnose requires --project-root
   Failed with exit code 2

 $ Shell Test autopilot.py --diagnose with project-root 1 line…
   python3 plugins/autopilot/scripts/autopilot.py --diagnose --project-root .

 MD Read docs/dev/project-management/reviews/00014-autopilot-host-execution-v1  L100:160 (61 lines …
         -review-1.md

 $ Shell Run test_jobs.py 2 lines…
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_jobs.py -q

 $ Shell Run test_facade.py 2 lines…                                                             30s
   uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt
   python -m pytest tests/autopilot/test_facade.py -q

 ● Read shell output Waiting up to 5 seconds for command output 2 lines…                          5s

 ● Read shell output Waiting up to 10 seconds for command output 2 lines…                        10s

 ● Read shell output Waiting up to 15 seconds for command output 2 lines…

 PY Read plugins/autopilot/scripts/claude.py L1:75 (71 lines read)

 PY Read plugins/autopilot/scripts/codex.py L1:65 (60 lines read)

 PY Read plugins/autopilot/scripts/hosts.py L1:80 (80 lines read)

 PY Read plugins/autopilot/scripts/hosts.py L81:143 (63 lines read)

 PY Read plugins/autopilot/scripts/guards.py L1:80 (80 lines read)

 $ Shell Check diff of update_helper_map.py 46 lines…
   git diff 68418c5a3c8951abfbac494ddc9cdae0d6408a06 -- tools/autopilot/update_helper_map.py

[CARL] 🔴 test_new_helper_files_are_owned_and_digested_from_current_bytes fails because assert_refreshed_evidence expects CHANGELOG.md to match AP00013 package revision 444d733a, but AP00014 modified CHANGELOG.md | File: tests/autopilot/test_helper_provenance_real.py:300 | Task: general

R1: pass
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

Verdict: 32 findings
Tests: 1433 passed, 20 failed (suite run this cycle)

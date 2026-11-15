# AP00014 v2 finding dispositions

Source: AP00014 v2 design, §13 finding dispositions. This file gives one row
per retained finding and one row per stub, each with a disposition and an
owner.

Dispositions: `F` = fixed by the named contract and test; `R` = rejected with
evidence; `D` = deferred to the named owner. A row marked `F + D` names both
owners.

## Closure rule

A row whose closure class is host support, registration, identity, isolation
or real probing closes only on a test that runs the real code path: the real
binary lookup or a fake host binary on `PATH`, the shipped hook asset, the
real environment variable, a real child process, or the real probe tool. A
capability constant or a resolver defined inside the test does not close such
a row.

## Characterization

`tests/autopilot/hook_characterization.json` records the source hook and
effort behavior at claude-autopilot `e960ef1` as 51 cases (`case_id`,
`source_ref`, `host`, `event`, `payload`, `bound`, `facts`, `expected`,
`divergence`). Most cases carry `divergence: null` (the target reproduces the
source decision exactly). Two cases carry a non-null divergence that is not a
behavior fix: the narrowed `autopilot:`-only delegation lexicon, and
`missing_controller_seam` denying a bound session the source never modeled.
The two `host: "runner"` effort cases where `sonnet-run.sh` drops `--effort`
carry a non-null divergence naming v1c2-R14 as the corrected target.

## Cycle 1 rows (v1c1)

| Finding | Stub | Disp. | Owner | Contract | Repair or evidence test | Closure class |
|---|---|---|---|---|---|---|
| v1c1-R1 | 00042 | F (v1 rework, verified) | AP00014 v2 | §1 | `test_sessions.py::GeminiCapabilityContractTest::test_missing_binary_yields_no_capability_and_a_recorded_reason` | host support |
| v1c1-R2 | 00060 | F (v1 rework) + §7 normalization | AP00014 v2 | §7 | `test_guards_pure_duties.py` path and command cases | - |
| v1c1-R3 | 00049 | F | AP00014 v2 | §2 capability-behavior binding, §9 | `test_sessions.py::test_each_implemented_capability_has_its_behavior` | host support |
| v1c1-R4 | 00043 | F (v1 rework, verified 203 passed) | AP00014 v2 | §12 | full gate | - |
| v1c1-R5 | 00044 | F (v1 rework, verified 203 passed) | AP00014 v2 | §12 | full gate | - |
| v1c1-R6 | 00045 | F (v1 rework, verified 203 passed) | AP00014 v2 | §12 | full gate | - |
| v1c1-R7 | 00046 | F (v1 rework, verified 203 passed) | AP00014 v2 | §12 | full gate | - |
| v1c1-R8 | 00047 | F (v1 rework, verified 203 passed) | AP00014 v2 | §12 | full gate | - |
| v1c1-R9 | 00048 | F | AP00014 v2 | §10 real probe | `test_host_argv.py::test_relocated_host_probe_*` with fake host binaries; Phase 2 real run evidence | real probing |
| v1c1-R10 | 00050 | F | AP00014 v2 | §2 capability-behavior binding, §9 | `test_sessions.py::test_each_implemented_capability_has_its_behavior` | host support |
| v1c1-R11 | 00051 | F | AP00014 v2 | §2 capability-behavior binding, §9 | `test_sessions.py::test_each_implemented_capability_has_its_behavior` | host support |
| v1c1-R12 | 00052 | F | AP00014 v2 | §12 | `test_ap00014_rows_cite_the_host_receipt_and_digest_current_bytes` | - |
| v1c1-R13 | 00053 | F | AP00014 v2 | §10, §11 | `test_facade.py` CLI cases for `--diagnose`, `--hook`, `--request-job`; `test_host_argv.py` probe CLI | - |
| v1c1-R14 | 00054 | F | AP00014 v2 | §6, §10 | `test_roles.py` | host support |
| v1c1-R15 | 00055 | F | AP00014 v2 | §6, §10 | `test_roles.py` | host support |
| v1c1-R16 | 00056 | F | AP00014 v2 | §2 capability-behavior binding, §9 | `test_sessions.py::test_each_implemented_capability_has_its_behavior` | host support |
| v1c1-R17 | 00057 | F (isolation, cleanup, digests, sessions; recursion for cooperating sessions) + D (adversarial standalone recursion: controller `job.plan` lineage) | F: AP00014 v2; D: AP 00016/00019 | §5 | `test_jobs.py::ReviewerIsolationTest`, `ChildCleanupTest`, `RecursionBoundTest` (env, depth variable and lineage record each refuse alone; stripped env with a lineage record still refuses) | isolation |
| v1c1-R18 | 00058 | F | AP00014 v2 | §5 standalone instruction | `test_jobs.py::StandaloneInstructionTest` | isolation |
| v1c1-R19 | 00059 | F (package assets) + D (activation) | F: AP00014 v2; D: publication/install PRD | §9 | `test_compatibility.py::test_hooks_assets_*`, `test_interception.py` | registration |
| v1c1-R20 | 00060 | F (v1 rework) + §7 normalization | AP00014 v2 | §7 | `test_guards_pure_duties.py` path and command cases | - |
| v1c1-R21 | 00061 | F | AP00014 v2 | §6, §10 | `test_roles.py` | host support |
| v1c1-R22 | 00062 | F | AP00014 v2 | §9 stale removal | `test_compatibility.py::test_undeclared_host_bundle_is_removed` | registration |
| v1c1-R23 | 00063 | F (v1 rework, `O_EXCL`) | AP00014 v2 | §10 | `test_probe_host_never_writes_through_an_existing_evidence_name` | real probing |
| v1c1-R24 | 00064 | F (v1 rework, verified 203 passed) | AP00014 v2 | §12 | full gate | - |
| v1c1-R25 | - | F (v1 rework, verify) | AP00014 v2 | - | re-run | - |
| v1c1-R26 | - | F | AP00014 v2 | §10 | evidence-path test | real probing |
| v1c1-R27 | - | F (documented) | AP00014 v2 | §11 | README text test | - |
| v1c1-R28 | - | F | AP00014 v2 | §5 | `test_jobs.py::BuildJobRequestValidationTest`, mutation test | - |
| v1c1-R29 | - | F | AP00014 v2 | §4 | `test_guards.py::test_malformed_verdict_refuses`, `test_jobs.py::test_seam_cannot_override_mode` | - |
| v1c1-R30 | - | F | AP00014 v2 | §2 `CLAUDE_CODE_SESSION_ID` | `test_sessions.py::test_claude_identity_reads_claude_code_session_id` | identity |
| v1c1-R31 | - | F | AP00014 v2 | §5 | `test_jobs.py::BuildJobRequestValidationTest`, mutation test | - |
| v1c1-R32 | - | F | AP00014 v2 | §5 | `test_jobs.py::BuildJobRequestValidationTest`, mutation test | - |
| v1c1-R33 | - | F | AP00014 v2 | §6, §10 | `test_roles.py` | host support |
| v1c1-R34 | - | F (v1 rework, verify) | AP00014 v2 | - | re-run | - |
| v1c1-R35 | - | F | AP00014 v2 | §10, §11 | `test_facade.py` CLI cases for `--diagnose`, `--hook`, `--request-job`; `test_host_argv.py` probe CLI | - |
| v1c1-R36 | - | F | AP00014 v2 | §10 | evidence-path test | real probing |
| v1c1-R37 | - | F (v1 rework, verify) | AP00014 v2 | - | re-run; must read `SCRIPTS / "autopilot.py"` directly | - |
| v1c1-R38 | - | F | AP00014 v2 | §4 (FakeSeam out), §9 | `test_package` roster has no `FakeSeam` in `scripts/jobs.py` | - |
| v1c1-R39 | - | F | AP00014 v2 | §4 (FakeSeam out), §9 | `test_package` roster has no `FakeSeam` in `scripts/jobs.py` | - |
| v1c1-R40 | - | R | AP00014 v2 (rejection recorded) | - | a passing preservation invariant | - |
| v1c1-R41 | - | R | AP00018 | - | belongs to AP00018 and is fixed there (stub 00040: full suite 1615 passed at `c988f45`) | - |
| v1c1-R42 | - | F | AP00014 v2 | §4 (FakeSeam out), §9 | `test_package` roster has no `FakeSeam` in `scripts/jobs.py` | - |
| v1c1-R43 | - | F (v1 rework, verify) | AP00014 v2 | - | re-run; must read `SCRIPTS / "autopilot.py"` directly | - |

## Cycle 2 rows (v1c2)

| Finding | Stub | Disp. | Owner | Contract | Repair or evidence test | Closure class |
|---|---|---|---|---|---|---|
| v1c2-R1 | 00039, 00041 | F (on master) | AP00014 v2 | §12 keeps it fixed | `test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes` stays green after AP00014 edits, through §12's chain rule and its named test edits | - |
| v1c2-R2 | - | F | AP00014 v2 | §10 simulation | `test_facade.py::test_diagnose_reports_simulation_apart_from_observation` | real probing |
| v1c2-R3 | - | F | AP00014 v2 | §2, §6 | `test_roles.py::test_codex_gemini_full_lane_resolves_without_claude` | host support |
| v1c2-R4 | - | F (package assets) + D (activation) | F: AP00014 v2; D: publication/install PRD | §9 | `test_compatibility.py::test_hooks_assets_*`, `test_interception.py` | registration |
| v1c2-R5 | - | F | AP00014 v2 | §10 real probe | `test_host_argv.py::test_relocated_host_probe_*` with fake host binaries; Phase 2 real run evidence | real probing |
| v1c2-R6 | - | F | AP00014 v2 | §2 capability-behavior binding, §9 | `test_sessions.py::test_each_implemented_capability_has_its_behavior` | host support |
| v1c2-R7 | - | F | AP00014 v2 | §1 `adapter()`, §9 | `test_compatibility.py::test_unknown_host_executes_no_module` | host support |
| v1c2-R8 | - | F | AP00014 v2 | §6, §10 | `test_roles.py` | host support |
| v1c2-R9 | - | F | AP00014 v2 | §2 capability-behavior binding, §9 | `test_sessions.py::test_each_implemented_capability_has_its_behavior` | host support |
| v1c2-R10 | - | R | AP00014 v2 (rejection recorded) | §10 | static auth is a hint only; authority is the real probe. Evidence: `ProbeResult.certified` is False and doctor exposes `observed` separately | real probing |
| v1c2-R11 | - | F | AP00014 v2 | §1 `CapabilityStatus.__post_init__` | `test_host_argv.py::test_capability_status_rejects_unknown_status` | - |
| v1c2-R12 | - | F (isolation, cleanup, digests, sessions; recursion for cooperating sessions) + D (adversarial standalone recursion: controller `job.plan` lineage) | F: AP00014 v2; D: AP 00016/00019 | §5 | `test_jobs.py::ReviewerIsolationTest`, `ChildCleanupTest`, `RecursionBoundTest` | isolation |
| v1c2-R13 | - | F | AP00014 v2 | §5 standalone instruction | `test_jobs.py::StandaloneInstructionTest` | isolation |
| v1c2-R14 | - | F | AP00014 v2 | §13 characterization | `test_host_argv.py::test_effort_mismatch_is_a_corrected_target`, `test_interception.py::test_hook_behavior_equivalence`; data in `tests/autopilot/hook_characterization.json` | - |
| v1c2-R15 | - | F | AP00014 v2 | §14 | README/CHANGELOG tests | - |
| v1c2-R16 | - | F | AP00014 v2 | §10 simulation | `test_facade.py::test_diagnose_reports_simulation_apart_from_observation` | real probing |
| v1c2-R17 | - | F | AP00014 v2 | §7 | `test_guards_pure_duties.py::test_absolute_and_relative_spellings_decide_alike` | - |
| v1c2-R18 | - | F | AP00014 v2 | - | `while 10` asserted as a violation; scanner checks literal truthiness via `ast` | - |
| v1c2-R19 | - | F | AP00014 v2 | - | collision test seeds via a frozen clock (`PROBE_HOST_NOW` env read only by the tool's timestamp function) | real probing |
| v1c2-R20 | - | F | AP00014 v2 | - | redundant token collector removed | - |
| v1c2-R21 | - | F | AP00014 v2 | §10 real probe | `test_host_argv.py::test_relocated_host_probe_*` with fake host binaries; Phase 2 real run evidence | real probing |
| v1c2-R22 | - | F | AP00014 v2 | §6, §10 | `test_roles.py` | host support |
| v1c2-R23 | - | F + D (live certification) | F: AP00014 v2; D: AP 00017 | §10 real probe | `test_host_argv.py::test_relocated_host_probe_*`; live certification deferred | real probing |
| v1c2-R24 | - | F | AP00014 v2 | §10 | named retry constant `EVIDENCE_NAME_ATTEMPTS = 10` | real probing |
| v1c2-R25 | - | F | AP00014 v2 | §2 `CLAUDE_CODE_SESSION_ID` | `test_sessions.py::test_claude_identity_reads_claude_code_session_id` | identity |
| v1c2-R26 | - | R | AP00018 | - | cause recorded: the 19 controller failures, fixed by AP00018 v2 | - |
| v1c2-R27 | - | F | AP00014 v2 | - | each touched test file gains at least one fail-first test per behavior it covers (§ Test strategy) | - |
| v1c2-R28 | - | F | AP00014 v2 | - | each touched test file gains at least one fail-first test per behavior it covers (§ Test strategy) | - |
| v1c2-R29 | - | F | AP00014 v2 | - | each touched test file gains at least one fail-first test per behavior it covers (§ Test strategy) | - |
| v1c2-R30 | - | F | AP00014 v2 | - | each touched test file gains at least one fail-first test per behavior it covers (§ Test strategy) | - |
| v1c2-R31 | - | F | AP00014 v2 | - | each touched test file gains at least one fail-first test per behavior it covers (§ Test strategy) | - |
| v1c2-R32 | - | F | AP00014 v2 | - | each touched test file gains at least one fail-first test per behavior it covers (§ Test strategy) | - |
| v1c2 auto-dismissed: effort | - | F | AP00014 v2 | §5 | `test_jobs.py::BuildJobRequestValidationTest`, mutation test | - |
| v1c2 auto-dismissed: digests | - | F | AP00014 v2 | §5 | `test_jobs.py::BuildJobRequestValidationTest`, mutation test | - |
| v1c2 auto-dismissed: relay | - | F | AP00014 v2 | §4 | `test_guards.py::test_malformed_verdict_refuses`, `test_jobs.py::test_seam_cannot_override_mode` | - |

## Stubs

| Stub | Finding | Disp. | Owner |
|---|---|---|---|
| 00038 | cycle-1 cap summary (content mapped to the v1c1 rows above) | R (meta) | AP00014 v2 (rejection recorded) |
| 00039 | v1c2-R1 | F (on master) | AP00014 v2 |
| 00040 | controller-suite failure set | R (meta) | AP00018 (fixed by AP00018 v2) |
| 00041 | v1c2-R1 | F (on master) | AP00014 v2 |
| 00042 | v1c1-R1 | F | AP00014 v2 |
| 00043 | v1c1-R4 | F | AP00014 v2 |
| 00044 | v1c1-R5 | F | AP00014 v2 |
| 00045 | v1c1-R6 | F | AP00014 v2 |
| 00046 | v1c1-R7 | F | AP00014 v2 |
| 00047 | v1c1-R8 | F | AP00014 v2 |
| 00048 | v1c1-R9 | F | AP00014 v2 |
| 00049 | v1c1-R3 | F | AP00014 v2 |
| 00050 | v1c1-R10 | F | AP00014 v2 |
| 00051 | v1c1-R11 | F | AP00014 v2 |
| 00052 | v1c1-R12 | F | AP00014 v2 |
| 00053 | v1c1-R13 | F | AP00014 v2 |
| 00054 | v1c1-R14 | F | AP00014 v2 |
| 00055 | v1c1-R15 | F | AP00014 v2 |
| 00056 | v1c1-R16 | F | AP00014 v2 |
| 00057 | v1c1-R17 | F + D | F: AP00014 v2; D: AP 00016/00019 |
| 00058 | v1c1-R18 | F | AP00014 v2 |
| 00059 | v1c1-R19 | F + D | F: AP00014 v2; D: publication/install PRD |
| 00060 | v1c1-R2, v1c1-R20 | F | AP00014 v2 |
| 00061 | v1c1-R21 | F | AP00014 v2 |
| 00062 | v1c1-R22 | F | AP00014 v2 |
| 00063 | v1c1-R23 | F | AP00014 v2 |
| 00064 | v1c1-R24 | F | AP00014 v2 |

## Phase 2 gate (final verification, task 13)

Named bug-fix scenarios re-confirmed passing on current master (commit
`36d4bfbddd263f2ae67cacb90eb4b9e02430b8b0`, after task 12's receipt mint):
`test_claude_identity_reads_claude_code_session_id`,
`test_absolute_and_relative_spellings_decide_alike`,
`test_malformed_verdict_refuses`, `test_unknown_host_executes_no_module`,
`test_capability_status_rejects_unknown_status`,
`test_undeclared_host_bundle_is_removed`,
`test_diagnose_reports_simulation_apart_from_observation` — 7 passed, 0
failed, 1841 deselected (`-k` filtered run).

Gate commands:

```
uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q
```
Final summary line: **5 failed, 1843 passed in 738.73s (0:12:18)**, exit code 1.

```
python3 scripts/validate.py
```
Final summary line: **Validated 3 plugin package(s) and 15 skill(s).**, exit code 0.

`tests/autopilot/test_package.py` and `tests/autopilot/test_helper_provenance_real.py`
both pass with zero AP00014 exclusions beyond §12's documented scoped skip set
(`AP00014_TARGETS` skipped from `OTHER_ASSETS_SHA`, positively asserted
instead by `test_ap00014_rows_cite_the_host_receipt_and_digest_current_bytes`)
— `test_package.py`'s own 2 failures below are unrelated to any AP00014
exclusion; they are genuine, newly surfaced drift, not a relabeled or
exempted requirement.

### Real-host-unavailability summary (from the §12 receipt, verbatim)

> Only static host probes exist in this package: each adapter observes a
> binary on PATH plus auth presence, and never invokes the host. On
> 2026-11-15 the probes reported claude available without auth, codex
> available with auth, and gemini available without auth; every probe was
> static and certified is False. No live host invocation ran, so no host is
> certified; live certification is AP 00017's work.

No unsupported capability is advertised: every `--list-capabilities` ID this
PRD added (`hosts-v1`, `guards-v1`, `diagnose-v1`, `hook-v1`, `request-job-v1`,
`bind-job-v1`, `close-child-v1`, `resolve-roles-v1`, `record-session-v1`) maps
to a real, implemented CLI mode; none claims live host execution or
certification.

### Items found at the Phase 2 gate, closed by the step-7 regression loop

The full-gate run first surfaced 5 failures, all outside task 13's
`Location:` (this doc only) and task 12's `files:` list. Both were fixed
immediately after, in `/autopilot:work`'s mandatory step-7 final-verification
regression loop (2 fix cycles, reopening tasks 7 and 10 respectively — never
reopening or editing anything under task 13's own scope):

| Finding | Disp. | Owner | Repair commit | Evidence test(s) |
|---|---|---|---|---|
| The two generated `compatibility/{claude,codex}/hooks.json` assets' embedded `${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py` references had no resource edges in `tools/autopilot/source-map.json` (12 defects) | F | AP00014 v2 (task 7, reopened at step 7) | `f6a58a9` — adds the 12 missing `resource_edges` rows and refreshes `FROZEN["resource_edges"]` in `test_helper_provenance_real.py` | `test_package.py::test_resource_closure_declares_inside_resources_and_external_failure_rules`, `test_resource_closure.py::test_whole_tree_closure` |
| Task 10's five new `--list-capabilities` IDs were not reflected in three pre-existing tests' expected-capability-list fixtures | F | AP00014 v2 (task 10, reopened at step 7) | `7c10f5d` — adds `request-job-v1`, `bind-job-v1`, `close-child-v1`, `resolve-roles-v1`, `record-session-v1` to the three fixtures' expected lists | `test_facade.py::test_capabilities_are_exact_contract_formats_without_runtime_side_effects`, `test_local_boundary.py::test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations`, `test_package.py::test_target_only_checkout_denies_source_home_and_network_but_exports_policy` |

Neither fix relabeled a required behavior as certification-only or weakened
an assertion; both are additive (new resource-edge rows, new capability IDs
appended to existing expected-value lists). The full gate is confirmed green
after both commits (re-run below).

---
prd: docs/dev/project-management/prds/wip/00014-autopilot-host-execution-v1.md
review: 1
date: 2026-11-08
head_sha: 68418c5a3c8951abfbac494ddc9cdae0d6408a06
codex_thread_id: 01a1bcbb-31e5-7991-8235-7d1815614b6a
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: 0bad5c28
  carl: 8f626661
---

# Review: 00014-autopilot-host-execution-v1

Diff range: `635e37640b82c66f8ed7e5063605ce4481f81407..68418c5a3c8951abfbac494ddc9cdae0d6408a06`

codex_rung_guard: not fired

## Review Summary

Reviewed: 10 completed tasks
PRDs checked: 00014-autopilot-host-execution-v1.md

### Agent Status
- Alice: available (Claude subagent, consensus lens)
- Blake: available (Claude subagent, blind lens, PRD-only)
- Bob: available (codex, doubt lens D1-D5 + de-slop)
- Carl: available (gemini via copilot backend, UI/design lens)

pack: ok

### Notes on this cycle

- The per-task patch reviewer (Pat) failed on every one of the 10 tasks
  (`review: "failed:runner_unavailable"`, host OAuth could not refresh), so this
  cycle's lenses carry the whole per-task load. Recorded here because it changes
  what this review is evidence for.
- `review-stage`'s gate run used a gate command without the PRD's pinned test
  requirements and produced `Tests: counts unavailable`. The gate was re-run with
  the PRD's own exit-criteria command
  (`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`),
  which is where the counts in the `Tests:` line below come from. `autopilot verify`
  did not record `last-verification.json`: its parser matches no summary-line
  pattern against this project's `-q` summary (`24 failed, 1352 passed in 351.13s`).
  That is a no-record outcome, not a clean gate.
- `consolidate_findings.py` warned that row R1 merged three citations that match
  only after suffix stripping
  (`gemini.py:42 ~ gemini.py:51 ~ gemini.py:40`). The merge is partly wrong: it
  folded Blake's CRITICAL "native session identity not implemented for the
  Claude-free profile" onto Alice's/Bob's/Carl's MEDIUM ProbeResult-contract
  finding. R1 is therefore read as covering BOTH defects, at the CRITICAL
  severity the merge produced.
- One `[MECH]` fail-first replay line was absorbed onto R40, which already names
  the same test file and test.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [4/4] | 🔴 | The gemini probe returns available=False together with a non-None capability, contradicting the ProbeResult contract ("None when available is False"). I confirmed this with probe-host gemini in a temp root. Claude and codex return None in the same state, so build-compatibility.py skips them while writing a gemini bundle. | plugins/autopilot/scripts/gemini.py:42 | 4 | ALICE, BLAKE, BOB, CARL |
| R2 | [2/4] | 🟠 | The pure guards are placeholders. `_check` allows or denies on `context.get("ok")` only. DOCUMENT_LOCATION, DELEGATION, POST_HANDOFF, DEPARTURE and CONTEXT_REINJECTION implement no real artifact or marker check. Task 6 said DOCUMENT_LOCATION re-implements the PRD-location rule locally, and the PRD says to preserve those duties. The generic `ok` flag means diagnose reports these duties as passing without checking anything. | plugins/autopilot/scripts/guards.py:43 | 6 | ALICE, BLAKE |
| R3 | [2/4] | 🟠 | Codex advertises capabilities its adapter cannot back. hosts.json and the codex probe report "delegation" available when auth exists, but codex.can_delegate() is False and codex.session_identity() is always None. The CHANGELOG then says "Codex: identity, delegation, isolation supported". The PRD success metric is "No unsupported capability is advertised", and Task 3 says codex delegation must be False. Gemini has the same problem for identity (available, but session_identity() is None). | plugins/autopilot/scripts/codex.py:47 | 3 | ALICE, BOB |
| R4 | [1/4] | 🔴 | Five tests fail that pass at the PRD base commit 635e376, so they are regressions from this PRD, not pre-existing. I ran tests/autopilot/test_package.py, test_helper_provenance_real.py and test_local_boundary.py in a worktree at 635e376 (47 passed, 1 skipped) and at HEAD (5 failed). The build session and Task 10 recorded them as pre-existing, which is false. | tests/autopilot/test_package.py:203 | 10 | ALICE |
| R5 | [1/4] | 🔴 | test_package.py::test_content_roster_matches_frozen_inventory_and_actual_package_bytes fails with AssertionError '00014' != '00013'. The test hardcodes `later = "00018" if "/controller/" in row["path"] else "00013"`. Task 10 added 13 owner rows with delivery_prd "00014" and did not extend the test the way AP00018 did. | tests/autopilot/test_package.py:202 | 10 | ALICE |
| R6 | [1/4] | 🔴 | test_package.py::test_target_only_checkout_denies_source_home_and_network_but_exports_policy and test_local_boundary.py::test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations fail. The `_CAPABILITIES` list grew by hosts-v1, guards-v1 and diagnose-v1, so the list now has 13 entries where the tests expect 3+7. Only tests/autopilot/test_facade.py was updated for this. | tests/autopilot/test_local_boundary.py:242 | 7 | ALICE |
| R7 | [1/4] | 🔴 | Stale source-map digests. The `plugins/autopilot/scripts/autopilot.py` and `plugins/autopilot/CHANGELOG.md` rows have `destination_blob_sha256` values that no longer match the files on disk. I recomputed all digests: the 13 new AP00014 rows match, and only these two are stale. This breaks test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes. | tools/autopilot/source-map.json | 10 | ALICE |
| R8 | [1/4] | 🔴 | test_helper_provenance_real.py::test_generator_check_accepts_the_committed_map fails with "source-map.json is not the generated helper map". The 13 AP00014 rows were hand-added and the generator does not produce them, so the committed map drifts from the tool that owns it. | tools/autopilot/source-map.json | 10 | ALICE |
| R9 | [1/4] | 🔴 | Phase 2 task 1 (real headless probes) is not done. All adapter probes are static (`shutil.which` plus an env var or auth-file existence check). Nothing invokes a host, proves identity, isolation or interception, or records unavailable hosts. `docs/dev/tmp/autopilot/probes/` does not exist, and nothing under `docs/dev/tmp/autopilot` holds probe evidence. This breaks "only successful real probes enable host execution claims". | plugins/autopilot/scripts/codex.py:31 | general | BLAKE |
| R10 | [1/4] | 🔴 | Availability is claimed without proof, and the claim contradicts the adapter's own code. `codex.probe` reports identity, delegation and isolation "available" whenever a binary and an auth file exist. But `codex.session_identity()` always returns None (codex.py:64) and `codex.can_delegate()` always returns False (codex.py:68). `claude.probe` hardcodes interception "available" (claude.py:50) with no hook registration or interception test. | plugins/autopilot/scripts/codex.py:47 | general | BLAKE |
| R11 | [1/4] | 🔴 | The shipped compatibility bundles and changelog advertise capabilities from the builder's environment, not from verified behavior. `plugins/autopilot/compatibility/codex.json:3` lists delegation, identity and isolation as supported, and `plugins/autopilot/CHANGELOG.md:7` repeats this. `claude.json` lists only interception, while hosts.json declares four capabilities for Claude and `claude.can_delegate()` is True. `tools/autopilot/build-compatibility.py` derives bundle content from live auth presence, so output varies by machine. This violates "No unsupported capability is advertised". | plugins/autopilot/compatibility/codex.json:3 | general | BLAKE |
| R12 | [1/4] | 🟠 | The AP00014_TARGETS exclusion in tests/autopilot/test_helper_provenance_real.py is a legitimate scoping fix on its own. It mirrors the AP00018 CONTROLLER_PREFIXES precedent, and the frozen OTHER_ASSETS_SHA hash should not cover a later PRD's rows. It is not a masked failure in itself, because the three real failures above still fail loudly. But nothing replaces it: no test checks that the AP00014 rows exist, have correct digests or have correct owners, and the generator cannot regenerate them. The skip also does not fix the regression Task 10 claimed it fixed, because the rest of that file still fails. Add an AP00014 row-integrity test, as AP00018 has. | tests/autopilot/test_helper_provenance_real.py:241 | 10 | ALICE |
| R13 | [1/4] | 🟠 | doctor.py, tools/autopilot/probe-host.py and the new autopilot.py modes (--probe-host, --run-guard, --diagnose) have no tests. rg over tests/ finds no test calling diagnose, probe-host.py or those flags. The PRD scenarios relocated_host_probe (probe writes only under docs/dev/tmp/autopilot/) and missing_guard_refused at the CLI level are not exercised. Task 8 required a temp-root test that no path outside the root is touched. | tests/autopilot/test_sessions.py | 8 | ALICE |
| R14 | [1/4] | 🟠 | The codex_gemini_role_capabilities test does not exercise the PRD requirement. `_resolve_candidate_hosts` is a test-local function that only checks hosts.json set containment. The "required capabilities" per role are invented inside the test, not derived from review-policy-v1.json job_ids. Claude is excluded by construction, and the assertNotEqual({"claude"}) is vacuous. No production code resolves job_id to host, and no mandatory role is checked. | tests/autopilot/test_sessions.py:105 | 4 | ALICE |
| R15 | [1/4] | 🟠 | doctor `profile` is not derived as specified. It is "claude-free" iff "identity" is in codex's or gemini's declared capabilities, which is a constant for the committed hosts.json. The spec says claude-free when every mandatory review-policy role resolves to codex or gemini. | plugins/autopilot/scripts/doctor.py:40 | 7 | ALICE |
| R16 | [1/4] | 🟠 | The committed compatibility/*.json and the CHANGELOG line record the build machine's environment, not the contract. claude.json lists only "interception" because no CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY was set at generation time. Claude's declared identity, delegation and isolation are therefore shipped as absent. gemini.json is empty, and gemini.json is not in the PRD file list. The CHANGELOG says "Gemini: no capabilities supported", which contradicts the Task 10 text ("Gemini: identity only"). Claude's auth check also ignores keychain or login auth. | plugins/autopilot/compatibility/claude.json | 9 | ALICE |
| R17 | [1/4] | 🟠 | Several spec scenarios and behaviors have no implementation or test: no `reviewer_isolation`, `child_cleanup`, `relocated_host_probe` or `missing_guard_refused` scenario tests were found; there is no native-child cancellation or cleanup code; there are no resolved input digests and no recording of actual native sessions in job metadata; there is no relocated-package resource-edge probe, though the spec requires probes that classify every required resource edge and fail on escape; the Outputs line "raw artifacts and completed cleanup" is unimplemented. | N/A | general | BLAKE |
| R18 | [1/4] | 🟠 | Standalone mode emits no usable next-session instruction. Every adapter's `build_job_argv` returns None, so `request_cross_session_job` yields `{"argv": None, ...}`. The spec requires "emit next-session instructions for manual launch". | plugins/autopilot/scripts/jobs.py:89 | general | BLAKE |
| R19 | [1/4] | 🟠 | Hook packaging is missing. The spec says "Retain Claude hooks through supported packaging" and "Generate self-contained supported client assets". The compatibility bundles are bare capability lists, and no hook registration asset exists in the plugin. The README says the hooks are unavailable. | plugins/autopilot/compatibility/claude.json:1 | general | BLAKE |
| R20 | [1/4] | 🟠 | Five pure guards implement caller approval instead of their required checks: `_check` allows empty context and ignores paths/artifacts. Implement each duty’s actual local rule, including document-location validation, and test prohibited artifacts rather than `ok` booleans. | plugins/autopilot/scripts/guards.py:43 | 6 | BOB |
| R21 | [1/4] | 🟠 | Doctor reports `claude-free` solely because a declaration contains identity, even when both non-Claude hosts are unavailable and every role lacks argv. Derive the profile from mandatory policy roles and supported host paths, preserving explicit blockers. | plugins/autopilot/scripts/doctor.py:31 | 7 | BOB |
| R22 | [1/4] | 🟠 | Compatibility generation preserves stale positive claims when a previously available host loses its binary: `capability is None` skips rewriting its existing bundle. Replace that bundle with an empty capability set or remove it safely; test available-to-unavailable regeneration. | tools/autopilot/build-compatibility.py:37 | 9 | BOB |
| R23 | [1/4] | 🟠 | Probe evidence can truncate an external file through a pre-existing hard link: `O_NOFOLLOW` protects symlinks, but `O_TRUNC` follows the hard-linked inode. Create uniquely named evidence with `O_EXCL` and retry collisions; test that planted hard links remain unchanged. | tools/autopilot/probe-host.py:42 | 8 | BOB |
| R24 | [1/4] | 🟠 | Five reported failures belong to AP00014’s own earlier tasks; being pre-existing relative to task 10 does not exempt them from this PRD’s completion gate. Resolve the package, provenance, and local-boundary regressions before marking AP00014 complete. | docs/dev/project-management/autopilot/state.json:229 | general | BOB |
| R25 | [1/4] | 🟡 | Hedged or tautological assertions: `assertIn(codex.can_delegate(), (True, False))` and `assertIn(gemini.can_delegate(), (True, False))` can never fail; `assertTrue(result is None or isinstance(result, list))` is the same shape. The same either-or pattern appears in test_jobs.py:306. test_compatibility.py:173 guards its assertion with `if expected:`, so it is vacuous on a host with no codex. Assert codex.can_delegate() is False. | tests/autopilot/test_sessions.py:95 | 4 | ALICE |
| R26 | [1/4] | 🟡 | `ProbeResult.evidence_path` is always None, even though probe-host.py writes an evidence file. The tool could return the path. build-compatibility.py also continues silently for hosts with no capability, which can leave a stale bundle on disk. | tools/autopilot/probe-host.py:34 | 8 | ALICE |
| R27 | [1/4] | 🟡 | `--run-guard` in autopilot.py always passes seam=None. Every stateful duty therefore refuses at the CLI, and the mode cannot demonstrate allow paths. This is consistent with the design but undocumented. Document it or add a test. | plugins/autopilot/scripts/autopilot.py:182 | 7 | ALICE |
| R28 | [1/4] | 🟡 | Recursion is bounded only by an exact (host_id, job_id) ancestry match. There is no depth limit, and a malformed ancestry entry raises KeyError. `build_job_intent` accepts any effort, role or tier, so "require the intended effort in job metadata" is unenforced. | plugins/autopilot/scripts/jobs.py:70 | general | BLAKE |
| R29 | [1/4] | 🟡 | `_relay` trusts `verdict["allowed"]` and `["reason"]` without type or shape validation, so a truthy non-bool from a seam would pass. In `request_cross_session_job`, `{"mode": "controller", **seam.submit_job(...)}` lets the seam response override `mode`. | plugins/autopilot/scripts/guards.py:36 | general | BLAKE |
| R30 | [1/4] | 🟡 | `claude.session_identity` depends on a `CLAUDE_SESSION_ID` env var that I could not confirm the host exports. `doctor.profile` is derived from declared hosts.json data ("identity" in codex or gemini caps), not from verified capability. `doctor` always runs guards against an allow-everything FakeSeam. It is flagged `guards_simulated`, but it still looks like a diagnostic pass. | plugins/autopilot/scripts/doctor.py:32 | general | BLAKE |
| R31 | [1/4] | 🟡 | `build_job_intent` performs no validation despite promising a validated intent. Invalid isolation/tier values, missing effort, provider-named roles, and raw-content inputs pass directly to the seam. Validate the documented fields and artifact-reference shape before submission. | plugins/autopilot/scripts/jobs.py:49 | 5 | BOB |
| R32 | [1/4] | 🟡 | Frozen intents retain caller-owned mutable dictionaries, and FakeSeam stores the same objects. Mutating input digests or constraints after submission changes recorded evidence. Snapshot nested data at construction and submission, with mutation regression tests. | plugins/autopilot/scripts/jobs.py:40 | 5 | BOB |
| R33 | [1/4] | 🟡 | Role-capability tests exercise a test-only resolver over declarations, never associate mandatory jobs with requirements, and never request those jobs. Replace this surrogate with policy-driven job-request tests that expose unsupported roles and exercise jobs.py with Claude unimportable. | tests/autopilot/test_sessions.py:105 | 4 | BOB |
| R34 | [1/4] | 🟡 | Compatibility tests depend on the developer’s installed Codex: the unimplemented-capability test dereferences `probe.capability` when a missing binary produces None. Use deterministic binary/auth fixtures, including an explicitly unavailable capability case. | tests/autopilot/test_compatibility.py:180 | 9 | BOB |
| R35 | [1/4] | 🟡 | Doctor and probe-host lack behavioral tests for profile derivation, evidence output, relocation, and write containment. Add temporary-root CLI tests, including symlink/hard-link refusal and unavailable hosts; dispatch-table tests do not cover these acceptance scenarios. | tests/autopilot/test_host_argv.py:115 | general | BOB |
| R36 | [1/4] | 🟡 | Probe evidence serializes `evidence_path=None` and discards the discovered binary path; it cannot identify its own evidence artifact or explain the static observation. Populate the evidence reference and retain non-secret probe inputs/results. | tools/autopilot/probe-host.py:34 | 8 | BOB |
| R37 | [1/4] | 🟡 | The coordinator scan guesses a second autopilot.py location and skips when neither exists, although the task fixes the location. Read `SCRIPTS / "autopilot.py"` directly so a missing required dispatcher fails instead of skipping. | tests/autopilot/test_compatibility.py:248 | 9 | BOB |
| R38 | [1/4] | ⚪ | claude.py hardcodes interception "available" without a signal. The comment documents this, which the task allows. The gemini.py module has no docstring, unlike the sibling adapters. | plugins/autopilot/scripts/gemini.py:1 | 4 | ALICE |
| R39 | [1/4] | ⚪ | `compatibility/gemini.json` is not in the spec's file list. `FakeSeam` ships in the production module `jobs.py`. | plugins/autopilot/compatibility/gemini.json:1 | general | BLAKE |
| R40 | [1/4] | ⚪ | The supplied replay shows `test_unrelated_arrays_and_original_owners_stay_byte_semantic` passes against the base revision. This is expected for its preservation invariant; it does not independently verify AP00014 additions and is not itself a regression. | tests/autopilot/test_helper_provenance_real.py:237 | 10 | BOB, mech-check |
| R41 | [1/4] | ⚪ | The supplied run attributes 48 failures to AP00018 controller suites. Their repair belongs to that separate PRD and should remain distinct from AP00014’s five failures. | N/A | general | BOB |
| R42 | [1/4] | ⚪ | build-compatibility.py writes JSON without trailing newline causing EOF warnings | tools/autopilot/build-compatibility.py:48 | 9 | CARL |
| R43 | [1/4] | ⚪ | Defensive test skips rather than fails when autopilot.py is missing | tests/autopilot/test_compatibility.py:254 | 9 | CARL |

## Alice

```text
[ALICE] 🔴 Five tests fail that pass at the PRD base commit 635e376, so they are regressions from this PRD, not pre-existing. I ran tests/autopilot/test_package.py, test_helper_provenance_real.py and test_local_boundary.py in a worktree at 635e376 (47 passed, 1 skipped) and at HEAD (5 failed). The build session and Task 10 recorded them as pre-existing, which is false. | File: tests/autopilot/test_package.py:203 | Task: 10
[ALICE] 🔴 test_package.py::test_content_roster_matches_frozen_inventory_and_actual_package_bytes fails with AssertionError '00014' != '00013'. The test hardcodes `later = "00018" if "/controller/" in row["path"] else "00013"`. Task 10 added 13 owner rows with delivery_prd "00014" and did not extend the test the way AP00018 did. | File: tests/autopilot/test_package.py:202 | Task: 10
[ALICE] 🔴 test_package.py::test_target_only_checkout_denies_source_home_and_network_but_exports_policy and test_local_boundary.py::test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations fail. The `_CAPABILITIES` list grew by hosts-v1, guards-v1 and diagnose-v1, so the list now has 13 entries where the tests expect 3+7. Only tests/autopilot/test_facade.py was updated for this. | File: tests/autopilot/test_local_boundary.py:242 | Task: 7
[ALICE] 🔴 Stale source-map digests. The `plugins/autopilot/scripts/autopilot.py` and `plugins/autopilot/CHANGELOG.md` rows have `destination_blob_sha256` values that no longer match the files on disk. I recomputed all digests: the 13 new AP00014 rows match, and only these two are stale. This breaks test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes. | File: tools/autopilot/source-map.json | Task: 10
[ALICE] 🔴 test_helper_provenance_real.py::test_generator_check_accepts_the_committed_map fails with "source-map.json is not the generated helper map". The 13 AP00014 rows were hand-added and the generator does not produce them, so the committed map drifts from the tool that owns it. | File: tools/autopilot/source-map.json | Task: 10
[ALICE] 🟠 The AP00014_TARGETS exclusion in tests/autopilot/test_helper_provenance_real.py is a legitimate scoping fix on its own. It mirrors the AP00018 CONTROLLER_PREFIXES precedent, and the frozen OTHER_ASSETS_SHA hash should not cover a later PRD's rows. It is not a masked failure in itself, because the three real failures above still fail loudly. But nothing replaces it: no test checks that the AP00014 rows exist, have correct digests or have correct owners, and the generator cannot regenerate them. The skip also does not fix the regression Task 10 claimed it fixed, because the rest of that file still fails. Add an AP00014 row-integrity test, as AP00018 has. | File: tests/autopilot/test_helper_provenance_real.py:241 | Task: 10
[ALICE] 🟠 doctor.py, tools/autopilot/probe-host.py and the new autopilot.py modes (--probe-host, --run-guard, --diagnose) have no tests. rg over tests/ finds no test calling diagnose, probe-host.py or those flags. The PRD scenarios relocated_host_probe (probe writes only under docs/dev/tmp/autopilot/) and missing_guard_refused at the CLI level are not exercised. Task 8 required a temp-root test that no path outside the root is touched. | File: tests/autopilot/test_sessions.py | Task: 8
[ALICE] 🟠 The codex_gemini_role_capabilities test does not exercise the PRD requirement. `_resolve_candidate_hosts` is a test-local function that only checks hosts.json set containment. The "required capabilities" per role are invented inside the test, not derived from review-policy-v1.json job_ids. Claude is excluded by construction, and the assertNotEqual({"claude"}) is vacuous. No production code resolves job_id to host, and no mandatory role is checked. | File: tests/autopilot/test_sessions.py:105 | Task: 4
[ALICE] 🟠 The pure guards are placeholders. `_check` allows or denies on `context.get("ok")` only. DOCUMENT_LOCATION, DELEGATION, POST_HANDOFF, DEPARTURE and CONTEXT_REINJECTION implement no real artifact or marker check. Task 6 said DOCUMENT_LOCATION re-implements the PRD-location rule locally, and the PRD says to preserve those duties. The generic `ok` flag means diagnose reports these duties as passing without checking anything. | File: plugins/autopilot/scripts/guards.py:43 | Task: 6
[ALICE] 🟠 Codex advertises capabilities its adapter cannot back. hosts.json and the codex probe report "delegation" available when auth exists, but codex.can_delegate() is False and codex.session_identity() is always None. The CHANGELOG then says "Codex: identity, delegation, isolation supported". The PRD success metric is "No unsupported capability is advertised", and Task 3 says codex delegation must be False. Gemini has the same problem for identity (available, but session_identity() is None). | File: plugins/autopilot/scripts/codex.py:47 | Task: 3
[ALICE] 🟠 doctor `profile` is not derived as specified. It is "claude-free" iff "identity" is in codex's or gemini's declared capabilities, which is a constant for the committed hosts.json. The spec says claude-free when every mandatory review-policy role resolves to codex or gemini. | File: plugins/autopilot/scripts/doctor.py:40 | Task: 7
[ALICE] 🟠 The committed compatibility/*.json and the CHANGELOG line record the build machine's environment, not the contract. claude.json lists only "interception" because no CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY was set at generation time. Claude's declared identity, delegation and isolation are therefore shipped as absent. gemini.json is empty, and gemini.json is not in the PRD file list. The CHANGELOG says "Gemini: no capabilities supported", which contradicts the Task 10 text ("Gemini: identity only"). Claude's auth check also ignores keychain or login auth. | File: plugins/autopilot/compatibility/claude.json | Task: 9
[ALICE] 🟡 The gemini probe returns available=False together with a non-None capability, contradicting the ProbeResult contract ("None when available is False"). I confirmed this with probe-host gemini in a temp root. Claude and codex return None in the same state, so build-compatibility.py skips them while writing a gemini bundle. | File: plugins/autopilot/scripts/gemini.py:42 | Task: 4
[ALICE] 🟡 Hedged or tautological assertions: `assertIn(codex.can_delegate(), (True, False))` and `assertIn(gemini.can_delegate(), (True, False))` can never fail; `assertTrue(result is None or isinstance(result, list))` is the same shape. The same either-or pattern appears in test_jobs.py:306. test_compatibility.py:173 guards its assertion with `if expected:`, so it is vacuous on a host with no codex. Assert codex.can_delegate() is False. | File: tests/autopilot/test_sessions.py:95 | Task: 4
[ALICE] 🟡 `ProbeResult.evidence_path` is always None, even though probe-host.py writes an evidence file. The tool could return the path. build-compatibility.py also continues silently for hosts with no capability, which can leave a stale bundle on disk. | File: tools/autopilot/probe-host.py:34 | Task: 8
[ALICE] 🟡 `--run-guard` in autopilot.py always passes seam=None. Every stateful duty therefore refuses at the CLI, and the mode cannot demonstrate allow paths. This is consistent with the design but undocumented. Document it or add a test. | File: plugins/autopilot/scripts/autopilot.py:182 | Task: 7
[ALICE] ⚪ claude.py hardcodes interception "available" without a signal. The comment documents this, which the task allows. The gemini.py module has no docstring, unlike the sibling adapters. | File: plugins/autopilot/scripts/gemini.py:1 | Task: 4

Summary: the five test regressions are the main blocker. Task 10 should have refreshed the stale autopilot.py and CHANGELOG digests, taught the generator or tests about the 00014 rows, and updated the capability-count and delivery_prd expectations. Pat failed every task, so none of this was caught earlier. Baseline verified in a temporary worktree at 635e376, removed afterwards.

R1: fail
R2: fail
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
```

## Blake

```text
BLAKE blind review of AP00014 (autopilot host execution and enforcement).

Checks run:
- The five AP00014 test files pass narrowly: 96 passed.
- `python3 scripts/validate.py` passes.
- The supplied full-suite gate reported exit 2 with no summary line. I did not rerun it.
- The passing tests are mostly fake-driven or tautological, so they prove little about the spec.

[BLAKE] 🔴 Phase 2 task 1 (real headless probes) is not done. All adapter probes are static (`shutil.which` plus an env var or auth-file existence check). Nothing invokes a host, proves identity, isolation or interception, or records unavailable hosts. `docs/dev/tmp/autopilot/probes/` does not exist, and nothing under `docs/dev/tmp/autopilot` holds probe evidence. This breaks "only successful real probes enable host execution claims". | File: plugins/autopilot/scripts/codex.py:31 | Task: general
[BLAKE] 🔴 Availability is claimed without proof, and the claim contradicts the adapter's own code. `codex.probe` reports identity, delegation and isolation "available" whenever a binary and an auth file exist. But `codex.session_identity()` always returns None (codex.py:64) and `codex.can_delegate()` always returns False (codex.py:68). `claude.probe` hardcodes interception "available" (claude.py:50) with no hook registration or interception test. | File: plugins/autopilot/scripts/codex.py:47 | Task: general
[BLAKE] 🔴 The shipped compatibility bundles and changelog advertise capabilities from the builder's environment, not from verified behavior. `plugins/autopilot/compatibility/codex.json:3` lists delegation, identity and isolation as supported, and `plugins/autopilot/CHANGELOG.md:7` repeats this. `claude.json` lists only interception, while hosts.json declares four capabilities for Claude and `claude.can_delegate()` is True. `tools/autopilot/build-compatibility.py` derives bundle content from live auth presence, so output varies by machine. This violates "No unsupported capability is advertised". | File: plugins/autopilot/compatibility/codex.json:3 | Task: general
[BLAKE] 🔴 Native session identity is not implemented for the Claude-free profile. `session_identity()` returns None and `can_delegate()` returns False for both Codex and Gemini. The spec requires "applicable native identity/input/guard support" for Codex implementer and Gemini doubt reviewer. `contracts/hosts.json:5` still declares codex identity, delegation and isolation, and `tests/autopilot/test_sessions.py` only checks that declaration against test-local resolver data. The blocker is not reported anywhere. | File: plugins/autopilot/scripts/gemini.py:51 | Task: general
[BLAKE] 🟠 The five "pure" guards are placeholders. `_check` allows or denies on a caller-supplied `context["ok"]` flag. It has no document-location, delegation, post-handoff, departure or context-reinjection logic, and the source hook decisions are not ported. The `hook_behavior_equivalence` scenario has no test. | File: plugins/autopilot/scripts/guards.py:43 | Task: general
[BLAKE] 🟠 Several spec scenarios and behaviors have no implementation or test: no `reviewer_isolation`, `child_cleanup`, `relocated_host_probe` or `missing_guard_refused` scenario tests were found; there is no native-child cancellation or cleanup code; there are no resolved input digests and no recording of actual native sessions in job metadata; there is no relocated-package resource-edge probe, though the spec requires probes that classify every required resource edge and fail on escape; the Outputs line "raw artifacts and completed cleanup" is unimplemented. | File: N/A | Task: general
[BLAKE] 🟠 Standalone mode emits no usable next-session instruction. Every adapter's `build_job_argv` returns None, so `request_cross_session_job` yields `{"argv": None, ...}`. The spec requires "emit next-session instructions for manual launch". | File: plugins/autopilot/scripts/jobs.py:89 | Task: general
[BLAKE] 🟠 Hook packaging is missing. The spec says "Retain Claude hooks through supported packaging" and "Generate self-contained supported client assets". The compatibility bundles are bare capability lists, and no hook registration asset exists in the plugin. The README says the hooks are unavailable. | File: plugins/autopilot/compatibility/claude.json:1 | Task: general
[BLAKE] 🟡 Recursion is bounded only by an exact (host_id, job_id) ancestry match. There is no depth limit, and a malformed ancestry entry raises KeyError. `build_job_intent` accepts any effort, role or tier, so "require the intended effort in job metadata" is unenforced. | File: plugins/autopilot/scripts/jobs.py:70 | Task: general
[BLAKE] 🟡 `_relay` trusts `verdict["allowed"]` and `["reason"]` without type or shape validation, so a truthy non-bool from a seam would pass. In `request_cross_session_job`, `{"mode": "controller", **seam.submit_job(...)}` lets the seam response override `mode`. | File: plugins/autopilot/scripts/guards.py:36 | Task: general
[BLAKE] 🟡 `claude.session_identity` depends on a `CLAUDE_SESSION_ID` env var that I could not confirm the host exports. `doctor.profile` is derived from declared hosts.json data ("identity" in codex or gemini caps), not from verified capability. `doctor` always runs guards against an allow-everything FakeSeam. It is flagged `guards_simulated`, but it still looks like a diagnostic pass. | File: plugins/autopilot/scripts/doctor.py:32 | Task: general
[BLAKE] ⚪ `compatibility/gemini.json` is not in the spec's file list. `FakeSeam` ships in the production module `jobs.py`. | File: plugins/autopilot/compatibility/gemini.json:1 | Task: general

Positives:
- No process spawning appears in the adapters or `jobs.py`.
- Stateful guards refuse without a seam.
- Source-map entries for the AP00014 files exist.
- No coordinator or scheduler runtime was found in the package.

B1: fail
B2: pass
B3: fail
B4: pass
B5: pass
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
```

## Bob

```text
FIX:
- [BOB] 🟠 Five pure guards implement caller approval instead of their required checks: `_check` allows empty context and ignores paths/artifacts. Implement each duty’s actual local rule, including document-location validation, and test prohibited artifacts rather than `ok` booleans. | File: plugins/autopilot/scripts/guards.py:43 | Task: 6
- [BOB] 🟠 Capability claims contradict adapter behavior: Codex advertises identity/delegation/isolation despite `session_identity()` always returning None and `can_delegate()` returning False; Gemini advertises identity when authenticated despite no identity implementation. Correct probe statuses, declarations, generated bundles, and changelog together. | File: plugins/autopilot/scripts/codex.py:47 | Task: general
- [BOB] 🟠 Doctor reports `claude-free` solely because a declaration contains identity, even when both non-Claude hosts are unavailable and every role lacks argv. Derive the profile from mandatory policy roles and supported host paths, preserving explicit blockers. | File: plugins/autopilot/scripts/doctor.py:31 | Task: 7
- [BOB] 🟠 Compatibility generation preserves stale positive claims when a previously available host loses its binary: `capability is None` skips rewriting its existing bundle. Replace that bundle with an empty capability set or remove it safely; test available-to-unavailable regeneration. | File: tools/autopilot/build-compatibility.py:37 | Task: 9
- [BOB] 🟠 Probe evidence can truncate an external file through a pre-existing hard link: `O_NOFOLLOW` protects symlinks, but `O_TRUNC` follows the hard-linked inode. Create uniquely named evidence with `O_EXCL` and retry collisions; test that planted hard links remain unchanged. | File: tools/autopilot/probe-host.py:42 | Task: 8
- [BOB] 🟡 `build_job_intent` performs no validation despite promising a validated intent. Invalid isolation/tier values, missing effort, provider-named roles, and raw-content inputs pass directly to the seam. Validate the documented fields and artifact-reference shape before submission. | File: plugins/autopilot/scripts/jobs.py:49 | Task: 5
- [BOB] 🟡 Frozen intents retain caller-owned mutable dictionaries, and FakeSeam stores the same objects. Mutating input digests or constraints after submission changes recorded evidence. Snapshot nested data at construction and submission, with mutation regression tests. | File: plugins/autopilot/scripts/jobs.py:40 | Task: 5
- [BOB] 🟡 ProbeResult semantics differ across adapters: Claude/Codex report available with missing auth, while Gemini returns a capability object when unavailable, contrary to the specified shape. Apply one consistent availability contract and test binary/auth combinations for every adapter. | File: plugins/autopilot/scripts/gemini.py:42 | Task: general
- [BOB] 🟡 Role-capability tests exercise a test-only resolver over declarations, never associate mandatory jobs with requirements, and never request those jobs. Replace this surrogate with policy-driven job-request tests that expose unsupported roles and exercise jobs.py with Claude unimportable. | File: tests/autopilot/test_sessions.py:105 | Task: 4
- [BOB] 🟡 Compatibility tests depend on the developer’s installed Codex: the unimplemented-capability test dereferences `probe.capability` when a missing binary produces None. Use deterministic binary/auth fixtures, including an explicitly unavailable capability case. | File: tests/autopilot/test_compatibility.py:180 | Task: 9
- [BOB] 🟡 Doctor and probe-host lack behavioral tests for profile derivation, evidence output, relocation, and write containment. Add temporary-root CLI tests, including symlink/hard-link refusal and unavailable hosts; dispatch-table tests do not cover these acceptance scenarios. | File: tests/autopilot/test_host_argv.py:115 | Task: general
- [BOB] 🟡 Probe evidence serializes `evidence_path=None` and discards the discovered binary path; it cannot identify its own evidence artifact or explain the static observation. Populate the evidence reference and retain non-secret probe inputs/results. | File: tools/autopilot/probe-host.py:34 | Task: 8
- [BOB] 🟡 The coordinator scan guesses a second autopilot.py location and skips when neither exists, although the task fixes the location. Read `SCRIPTS / "autopilot.py"` directly so a missing required dispatcher fails instead of skipping. | File: tests/autopilot/test_compatibility.py:248 | Task: 9
- [BOB] 🟠 Five reported failures belong to AP00014’s own earlier tasks; being pre-existing relative to task 10 does not exempt them from this PRD’s completion gate. Resolve the package, provenance, and local-boundary regressions before marking AP00014 complete. | File: docs/dev/project-management/autopilot/state.json:229 | Task: general

VERIFY:
- (none)

KNOWN:
- [BOB] ⚪ The supplied replay shows `test_unrelated_arrays_and_original_owners_stay_byte_semantic` passes against the base revision. This is expected for its preservation invariant; it does not independently verify AP00014 additions and is not itself a regression. | File: tests/autopilot/test_helper_provenance_real.py:237 | Task: 10
- [BOB] ⚪ The supplied run attributes 48 failures to AP00018 controller suites. Their repair belongs to that separate PRD and should remain distinct from AP00014’s five failures. | File: N/A | Task: general

R1: fail
R2: fail
R3: fail
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: fail
R12: pass
R13: pass
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Carl

Backend: gemini via `copilot`. Carl's raw output is a tool transcript; its
findings and verdict lines are reproduced here.

```text
[CARL] 🟡 gemini.probe returns non-None capability when available is False, violating ProbeResult contract | File: plugins/autopilot/scripts/gemini.py:40 | Task: 4
[CARL] ⚪ build-compatibility.py writes JSON without trailing newline causing EOF warnings | File: tools/autopilot/build-compatibility.py:48 | Task: 9
[CARL] ⚪ Defensive test skips rather than fails when autopilot.py is missing | File: tests/autopilot/test_compatibility.py:254 | Task: 9
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
```

Verdict: 43 findings
Tests: 1352 passed, 24 failed (suite run this cycle)

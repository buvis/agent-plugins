---
prd: docs/dev/project-management/prds/wip/00014-autopilot-host-execution-v2.md
review: 1
date: 2026-11-16
head_sha: a133498261a65eed36ce0d9516770626c7955b2a
codex_thread_id: 01a1e166-515a-79f3-ac3f-6907494e402d
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: 912357b6
  carl: 1c1a859a
---

# Review: 00014-autopilot-host-execution-v2

Diff range: `3a2c5a1a79534b10cf047b3a4016cb70731630b3..a133498261a65eed36ce0d9516770626c7955b2a`

codex_rung_guard: not fired

## Review Summary

Reviewed: 13 completed tasks
PRDs checked: 00014-autopilot-host-execution-v2.md

### Agent Status
- Alice: available (Claude subagent, consensus lens)
- Blake: available (Claude subagent, blind lens, PRD-only)
- Bob: available (codex, doubt lens D1-D5 + de-slop)
- Carl: available (gemini via copilot backend, UI/design lens)

pack: ok

### Notes on this cycle

- Full review (cycle 1), diff scoped to the PRD's whole work range with
  `--since 3a2c5a1a`.
- `review-stage`'s own gate run executed the PRD's exit-criteria command and
  exited 0, but its parser matched no summary line against this project's `-q`
  shape (`1848 passed in 719.52s`), so it reported
  `Tests: counts unavailable (suite run this cycle, exit 0, ...)` and wrote no
  `last-verification.json`. The counts in the `Tests:` line below are read from
  that same run's log (`docs/dev/tmp/gate-ap00014-v2-c1.log:27`). This is the
  same parser quirk the v1 cycle-1 review recorded; it is a no-record outcome,
  not an unrun gate.
- Carl ran the suite himself in his own environment and got
  `1 failed, 1847 passed`: `test_a_probe_failure_that_is_not_an_absent_work_tree_is_refused[probe-answers-false]`
  in `tests/autopilot/test_helper_map_refresh_agreement.py:573` did not raise.
  That test file is not in this diff and the same test passes in the gate run at
  this HEAD, so the failure is ambient-git-config sensitive rather than a
  regression from this PRD. Recorded because it is evidence the test is not
  environment-independent.
- Bob's dispatch used the inlined prompt (962 KB); his dispatch row's
  `prompt_bytes` was measured against the 9 KB staged render and understates it.
- The three `[MECH]` fail-first replay lines were absorbed onto R46, R47 and R48,
  which already name the same test files and tests.
- `consolidate_findings.py` warned that four rows merged citations matching only
  after suffix stripping (R2, R4, R5, R6). The merges read correctly: each pair
  names the same defect in the same file at a neighbouring line.
- Bob's VERIFY bucket is empty, so this cycle queues no verification checks.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/4] | 🟠 | `request_job` is 60 lines (mechanical facts, line 442). That breaks the 50-line rule. Behavior-preserving split: move the standalone branch into `_write_request_file(resolved_file, root, payload)` and `_standalone_instruction(request, argv, request_file, root)`. | plugins/autopilot/scripts/jobs.py:442 | 3 | ALICE, BOB, CARL |
| R2 | [2/4] | 🟠 | `AUTOPILOT_DISPATCH_DEPTH` is never read as a lineage signal. Task 3 requires three independent signals: `JOB_ENV`, the depth env var, and the lineage record. A non-integer value must refuse `invalid_request`, and a value >= `MAX_JOB_DEPTH` must refuse `recursion_depth`. `DEPTH_ENV` is only written into the standalone instruction (jobs.py:491, 495). `derive_ancestry` and `build_job_request` ignore it, and no test covers it. A child that strips `JOB_ENV` but keeps the depth variable is not refused. | plugins/autopilot/scripts/jobs.py:300 | 3 | ALICE, BLAKE |
| R3 | [2/4] | 🟠 | `is_git_push` misses push forms the source grammar denies, so `custody_push` is never consulted for them. I ran it: `sudo -u x git push`, `env -i git push`, `nice -n 5 git push`, `timeout 5 git push`, `(git push)`, `{ git push; }`, `if true; then git push; fi` and `! git push` all return False. The prefix-skip loop stops at the first option token. The segment executable is never found after a subshell, brace, `then` or `!`. The characterization fixture records `sudo -u git git push` as expected "deny" with `divergence: null` (hook_characterization.json:248-256), but the target returns False. No test asserts this. The design's own prefix rule is silent on options, but it calls the function a "conservative superset" where a false positive is cheap. A safe fix scans each segment for any token whose name is `git` followed by `push`. | plugins/autopilot/scripts/guards.py:313 | 4 | ALICE, BLAKE |
| R4 | [2/4] | 🟠 | `evaluate_hook` discards the resolved `project_root`. Design §2 gives `translate_hook(event, payload, *, project_root)`, but the adapters take no `project_root`, and `evaluate_hook` calls `translate_hook(event, payload)` (interception.py:183). Each adapter then copies the payload `cwd` into `project_root` (claude.py:106,109; codex.py:102,105,134). With a bound session whose `cwd` is a subdirectory of the binding root, an absolute `/repo/backlog/x.md` is not normalized against the root. I ran it: `project_root='/repo/sub'` returns allowed, and `'/repo'` returns the lifecycle deny. This defeats the v1c2-R17 normalization on the real hook path. The `env` argument of `evaluate_hook` is also ignored, so claude.py:119 reads `os.environ` for the child-session signal where the design says hook environment. | plugins/autopilot/scripts/interception.py:183 | 5 | ALICE, BOB |
| R5 | [2/4] | 🟠 | `request_job` writes the request file with `os.open(..., O_CREAT|O_WRONLY|O_NOFOLLOW)` plus `truncate(0)`, with no `O_EXCL` and no pinned parent descriptor. It can overwrite any existing regular file inside the project, and only the final component is symlink-protected. The CLI pre-checks `lexists` (autopilot.py:234), but the library function does not. Use the same exclusive pinned creation as `_write_new`. | plugins/autopilot/scripts/jobs.py:467 | 3 | ALICE, BOB |
| R6 | [2/4] | 🟡 | `gemini.py` exports no `HOOK_REGISTRATIONS`. The §2 contract says every adapter exports it, empty when interception is not implemented. `run_hook` and `build-compatibility.py` paper over this with `getattr(..., {})` and `getattr(..., ())`. `run_hook` also carries a `dict` branch (interception.py:250-253) that exists only for test fakes (test_interception.py:244, 260, 275). Add `HOOK_REGISTRATIONS = ()` to gemini.py and drop the dict branch. | plugins/autopilot/scripts/gemini.py:27 | 6 | ALICE, CARL |
| R7 | [1/4] | 🟠 | `render_hook_reply` departs from the design §8 shapes, and the tests pin the departure. (a) PostToolUse refused emits `{"systemMessage": ...}` where the design requires `{"decision": "block", "reason": ...}`. (b) Stop refused with `stop_active=True` emits empty stdout where the design requires `{"systemMessage": "autopilot: <reasons>"}`. (c) SessionStart refused emits nothing where the design requires a `systemMessage`. (d) PreToolUse deny uses only `denied[0]` where the design requires reasons joined by '; '. The tests assert the divergent shapes: test_interception.py:619-631 (PostToolUse not block), 657-659 and 763-764 (Stop released only asserts "not block"), and 594-606 (first reason only). | plugins/autopilot/scripts/codex.py:147 | 6 | ALICE |
| R8 | [1/4] | 🟠 | `test_hook_behavior_equivalence` does not bind to the real adapters or the push grammar. It installs a test-local `translate_hook` (`_doc_translate_hook`) at test_interception.py:296. It covers only `doc-file-*` and `doc-bash-*` fixtures at test_interception.py:290-294. The 14 `push-*` fixtures are never asserted against `guards.is_git_push` or the real adapters. `_push_commands()` is only used for an unbound-skip check. This is how the `sudo -u git git push` regression above passes unnoticed. The task also asked for the source `test_guard_push_grammar.py` cases to be ported, and the wrapper-with-option rows are absent from test_guards_pure_duties.py:542-577. | tests/autopilot/test_interception.py:288 | 5 | ALICE |
| R9 | [1/4] | 🟠 | Hook CLI fails open on malformed payloads. `tool_input: null` (also a non-dict `tool_input`, or a non-str `patch` or `prompt`) raises an uncaught AttributeError or TypeError inside `translate_hook`, and the process exits 1 with a traceback. I reproduced it with `echo '{"cwd":"/tmp","tool_name":"Bash","tool_input":null}' | python3 plugins/autopilot/scripts/autopilot.py --hook claude --event PreToolUse`. Claude Code treats exit 1 as a non-blocking hook error, so the tool call proceeds. The spec says malformed input refuses, and `_invalid_input_reply` only covers bad JSON and a missing `cwd`. | plugins/autopilot/scripts/codex.py:104 | Phase 1 task 4 | BLAKE |
| R10 | [1/4] | 🟠 | "Equivalent absolute and relative project paths yield the same guard decision" is not met. The Claude and Codex adapters pass the session `cwd` as `project_root`, not the binding root, and `_normalize_rel` only strips an exact string prefix. These return different decisions for the same file: `document_path=/r/backlog/x.md` with `project_root=/r` is denied, but `project_root=/r/sub` is allowed, and `/r//backlog/x.md` with `project_root=/r` is allowed. `command='echo hi > /r/wip/x.md'` with `project_root=/r/sub` is also allowed. A session started in a subdirectory therefore defeats the document-location guard for absolute paths. I ran `run_guard(DOCUMENT_LOCATION, …)` to confirm. | plugins/autopilot/scripts/guards.py:156 | Phase 1 task 4 | BLAKE |
| R11 | [1/4] | 🟠 | Controller-keyed guards are skipped entirely when no `.autopilot/controller` directory is found. In standalone or unbound sessions the custody-push, state-integrity, review-completeness, live-job, post-handoff, departure and context-reinjection duties never run, and the skip is only recorded in `skipped`. The spec says stateful guards call the same controller seam in both modes and that missing enforcement refuses affected operations. Enforcement also disappears if that marker directory is absent or removed. | plugins/autopilot/scripts/interception.py:197 | Phase 1 task 2 | BLAKE |
| R12 | [1/4] | 🟠 | The shipped package has no activation path for the Claude hooks, so "retain Claude hooks through supported packaging" is not delivered. There is no `.claude-plugin` manifest, and `plugin.json` has no hooks field. `hosts.json` says activation is `client-manifest-hooks-field`, yet nothing in the package supplies that manifest. Only `tools/autopilot/probe-host.py` writes one, into a temporary copy. The README says the assets "are not activated", and the dispositions defer activation to a "publication/install PRD". That is honest, but the v1 finding that compatibility assets were not real client assets is closed only on paper. | plugins/autopilot/contracts/hosts.json:7 | Phase 1 task 2 / Phase 2 task 1 | BLAKE |
| R13 | [1/4] | 🟠 | `--resolve-roles` for the Claude-free profile silently drops Gemini. `resolve_roles` defaults `implementor_codex_present=False` and `gemini_cli_available=False`, so `--resolve-roles --profile codex-gemini --lane full` returns `status: resolvable` with only Codex roles (alice, blake, bob, implementor). I ran it, and Eve (the Gemini doubt reviewer) is absent. `--diagnose` derives the fact from the profile, so the two paths disagree. The required Gemini role should appear and block, not vanish. | plugins/autopilot/scripts/autopilot.py:281 | Phase 1 task 3 | BLAKE |
| R14 | [1/4] | 🟠 | The dispatch-depth backstop is never enforced. `DEPTH_ENV` is written but neither parsed nor checked; a session carrying only `AUTOPILOT_DISPATCH_DEPTH=1` can request another job. Validate this signal independently, including malformed values. | plugins/autopilot/scripts/jobs.py:300 | 3 | BOB |
| R15 | [1/4] | 🟠 | Push detection misses executable pushes, including `sudo -u git git push`, `git 'push'`, and `"git" push`. Whitespace splitting cannot establish the promised conservative superset. Tokenize shell quoting and fail closed for uncertain wrapper options; assert bound hook denials for these cases. | plugins/autopilot/scripts/guards.py:313 | 4 | BOB |
| R16 | [1/4] | 🟠 | Hook evaluation ignores `session_from_hook_input`. A valid payload session with no session environment variable produces `session=None`, losing native identity in controller reads and traces. Use the adapter’s validated hook-input identity. | plugins/autopilot/scripts/interception.py:184 | 5 | BOB |
| R17 | [1/4] | 🟠 | Malformed tool payloads escape hook validation: `tool_input=null` raises `AttributeError`, and an Agent prompt with a non-string value raises `TypeError`. These bypass the structured deny/warning reply. Validate event-specific payload types and render `hook_input_invalid` consistently. | plugins/autopilot/scripts/interception.py:236 | 5 | BOB |
| R18 | [1/4] | 🟠 | Reply rendering weakens the specified enforcement: PostToolUse refusals become informational messages rather than block decisions; active Stop and refused SessionStart events emit nothing. Implement the exact contract shapes and replace tests that currently require the weaker behavior. | plugins/autopilot/scripts/codex.py:147 | 6 | BOB |
| R19 | [1/4] | 🟠 | Gemini’s required live probe is absent: `LIVE_HOSTS` excludes Gemini and the CLI rejects it before writing evidence. Implement its two hook-free `--record-session` invocations and explicit unavailable/auth outcomes. | tools/autopilot/probe-host.py:215 | 9 | BOB |
| R20 | [1/4] | 🟠 | Probe preparation performs no required resource-containment check. `copytree` follows symlinks by default, so an external target can be copied into the package and subsequently reported as contained. Check source symlink targets and declared assets before launch; invalidate every capability on escape. | tools/autopilot/probe-host.py:56 | 9 | BOB |
| R21 | [1/4] | 🟠 | Probe prompts never execute `--record-session`; they include it only as a “Probe tag” after “Do nothing else.” Identity therefore remains unobservable when hooks do not load. Append the actual absolute Python command and test that it executes. | tools/autopilot/probe-host.py:157 | 9 | BOB |
| R22 | [1/4] | 🟠 | The required Claude child-lineage observation is missing. The probe exercises only Bash pushes and never attempts top-level and nested Agent dispatches. Add that bounded scenario and observe delegation only when the parent dispatch succeeds and the nested dispatch receives `recursion_depth`. | tools/autopilot/probe-host.py:157 | 9 | BOB |
| R23 | [1/4] | 🟠 | Doctor never validates evidence `schema_version`. A record with another version and observed status strings can clear capability gaps; malformed newest JSON instead crashes diagnosis. Validate version and record shape before consuming evidence, and report invalid evidence explicitly. | plugins/autopilot/scripts/doctor.py:54 | 9 | BOB |
| R24 | [1/4] | 🟠 | Characterization does not prove source equivalence: document cases use a test-local translator, push expectations are derived from the implementation under test, Stop cases are largely unexercised, and one phase fixture is explicitly excluded. Run every applicable fixture through shipped adapters and compare recorded target verdicts; resolve divergences explicitly. | tests/autopilot/test_interception.py:288 | 5 | BOB |
| R25 | [1/4] | 🟠 | The binding test creates and recursively removes `.autopilot` under the temporary directory’s shared parent. This can remove unrelated pre-existing contents or another test’s fixture. Put both the enclosing binding and nested repository beneath one test-owned temporary root. | tests/autopilot/test_interception.py:105 | 5 | BOB |
| R26 | [1/4] | 🟠 | Design §11 and Task 10 contract mandate _CAPABILITIES appends 'hook-v1' before 'request-job-v1', but 'hook-v1' was omitted from _CAPABILITIES, causing --list-capabilities to not advertise the implemented --hook mode | plugins/autopilot/scripts/autopilot.py:25 | 10 | CARL |
| R27 | [1/4] | 🟡 | `_write_new` re-implements `log_sink_refusal._pinned_parent_fd` and `_descend`. The same mkdir-then-`O_DIRECTORY|O_NOFOLLOW` descent loop is duplicated. Task 3 names these two as the required reuse for the job file and close-child artifact. Replace the loop with `parent_fd = _pinned_parent_fd(root / relative.parent, root)`. | plugins/autopilot/scripts/jobs.py:324 | 3 | ALICE |
| R28 | [1/4] | 🟡 | Relative `request_file` handling is inconsistent. `request_job` resolves it against the cwd (jobs.py:460). The child env var and the steps carry the unresolved `str(request_file)` (jobs.py:491, 494). `derive_ancestry` joins the env value to `project_root` (jobs.py:306), while `--bind-job` reads it relative to the child cwd (autopilot.py:252). With `--out` relative and cwd different from `--project-root`, the child cannot find or ancestry-check the file. Emit the resolved path in `env`, `stdin` and `steps`. | plugins/autopilot/scripts/jobs.py:491 | 3 | ALICE |
| R29 | [1/4] | 🟡 | `derive_ancestry` opens the `JOB_ENV` file without confirming it is a regular file. The contract says regular file, at most 2 MiB. Opening a FIFO blocks the hook or CLI. | plugins/autopilot/scripts/jobs.py:306 | 3 | ALICE |
| R30 | [1/4] | 🟡 | `roles.py` names its dataclasses `RoleRow` and `ResolvedProfile`. The design §6 contract (verbatim) and later consumers (design lines 911 and 1283 reference `ProfileResolution`) name them `RoleResolution` and `ProfileResolution`. Rename to match the contract. | plugins/autopilot/scripts/roles.py:38 | 8 | ALICE |
| R31 | [1/4] | 🟡 | `--hook` reads stdin before `run_hook` rejects an unregistered event. The §8 contract says an event outside `HOOK_REGISTRATIONS` is a usage error (exit 2) before stdin is read. `run_hook` raising `SystemExit` from a library function is a second smell. Validate the event in `_hook` before reading stdin, or have `run_hook` raise `ValueError`. | plugins/autopilot/scripts/autopilot.py:327 | 10 | ALICE |
| R32 | [1/4] | 🟡 | `_request_job` picks the requester host as the first adapter whose `SESSION_ENV_VAR` is set. A codex session launched from a claude session inherits `CLAUDE_CODE_SESSION_ID`, so the requester is recorded as claude. Resolve it from the adapter whose session env is set and whose `source` matches the host, or refuse when more than one is set. | plugins/autopilot/scripts/autopilot.py:236 | 10 | ALICE |
| R33 | [1/4] | 🟡 | `session_from_hook_input` is exported by both intercepting adapters and unit-tested, but `evaluate_hook` only calls `hosts.current_session(host_id, env)`. The `hook_input` session source is unreachable on the real hook path. If the hook process lacks the session env var, the trace and `read_facts` record no session. Fall back to `session_from_hook_input(payload)` in `evaluate_hook`. | plugins/autopilot/scripts/interception.py:184 | 5 | ALICE |
| R34 | [1/4] | 🟡 | `bind_job_session` writes the lineage record itself (jobs.py:386). The Task 3 contract says it writes nothing and the CLI caller records it. This is a harmless deviation but should be documented or aligned. | plugins/autopilot/scripts/jobs.py:386 | 3 | ALICE |
| R35 | [1/4] | 🟡 | The shipped Codex hook asset uses the Claude-only variable `${CLAUDE_PLUGIN_ROOT}`. The probe replaces it by string substitution (`hooks.replace("${CLAUDE_PLUGIN_ROOT}", …)`). The live Codex probe therefore does not exercise the variable resolution of the asset that actually ships. This also conflicts with the rule that shared assets must not require Claude-only variables. | plugins/autopilot/compatibility/codex/hooks.json:9 | Phase 2 task 1 | BLAKE |
| R36 | [1/4] | 🟡 | Role resolution looks only at the adapters' `IMPLEMENTED_CAPABILITIES` constants, never at the static probe results. In `--diagnose` with no Claude or Gemini auth, `hosts[]` shows those hosts' capabilities as `unavailable: no_auth`. The profiles still show `status: resolvable` with every role `resolved`. A missing binary would resolve the same way. The spec asks for resolution "to supported isolated hosts" and for specific role/capability blockers. `certifiable` is false, but `status` says resolvable. | plugins/autopilot/scripts/roles.py:79 | Phase 1 task 3 | BLAKE |
| R37 | [1/4] | 🟡 | Role resolution ignores the policy's per-role input requirements and exclusions. `JobRequest` accepts whatever `excluded_input_kinds` the caller supplies. It never applies `policy.input_exclusions` for the role, so a `blind` job can be built with a `diff` input and an empty exclusion list. `role_id` is not checked against the policy role ids either. `contracts/hosts.json` `role_requirements` and `implementor_duties` are read by no code or test; `roles.REQUIRED_CAPABILITIES` duplicates the capability rows and nothing checks that the duties are covered. The spec asks roles to resolve "with their input/guard requirements". | plugins/autopilot/scripts/jobs.py:147 | Phase 1 task 3 | BLAKE |
| R38 | [1/4] | 🟡 | `_check_relative_path` blocks only the `docs/dev/project-management/autopilot` tree. A job input or child artifact can name `.autopilot/controller/...` (state, 0600 credential files), which would be digested and listed to the reviewer. `request_job` opens an existing project file with O_CREAT and truncates it, with no exclusive create; only the CLI pre-checks existence. | plugins/autopilot/scripts/jobs.py:90 | Phase 1 task 4 | BLAKE |
| R39 | [1/4] | 🟡 | The Phase 2 probe requirement is only partly met. `probe-host.py` allows a live probe only for claude and codex (`LIVE_HOSTS`) and rejects gemini. Doctor's `gemini_ran` therefore can never be true, and the codex-gemini profile can never become certifiable. The delivery receipt records "No live host invocation ran". That is honest unavailability, but the spec's "verify real invocation/resources/identity/interception for the selected roles" has no Gemini coverage. The receipt text also says probes "never invoke the host", which contradicts the live mode in `probe-host.py`, and it records 1841 tests against the 1848 in the gate. | tools/autopilot/probe-host.py:41 | Phase 2 task 1 / task 3 | BLAKE |
| R40 | [1/4] | 🟡 | The source-map behaviors owned by 00014 (8 rows) all remain `evidence.status: planned`, with null artifacts and no recorded supported or unavailable duty split. Phase 2 task 2 asks the source map to be updated for supported and still-unavailable client duties. The duty status lives only in README, CHANGELOG and the bundles. The dispositions doc also lists a `hook-v1` capability ID that does not exist in `_CAPABILITIES`. | tools/autopilot/source-map.json | Phase 2 task 2 | BLAKE |
| R41 | [1/4] | 🟡 | Hook stdin is read without a bound and before host/event validation. The later length check cannot prevent unlimited allocation or waiting on stdin for an invalid event. Validate registration first, then read at most `MAX_HOOK_INPUT_BYTES + 1`. | plugins/autopilot/scripts/autopilot.py:321 | 10 | BOB |
| R42 | [1/4] | 🟡 | Probe timeout defaults to 600 instead of 120 and accepts values above 600, non-positive values, and non-finite floats. Validate the documented range before creating evidence or launching hosts. | tools/autopilot/probe-host.py:215 | 9 | BOB |
| R43 | [1/4] | 🟡 | Delivery evidence is promoted to `passed` while its cited receipt records seven failures and exit 1. The supplied final green gate does not repair that receipt, whose real-host explanation also incorrectly says only static probes exist. Record successful final verification and actual probe outcomes before promoting evidence. | docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json:29 | 12 | BOB |
| R44 | [1/4] | 🟡 | Role capability requirements duplicate `contracts/hosts.json` instead of reading it. Contract changes can therefore leave role resolution reporting an unsupported profile as resolvable. Load the contract’s `role_requirements` and add a contract-change regression. | plugins/autopilot/scripts/roles.py:23 | 8 | BOB |
| R45 | [1/4] | 🟡 | `_validate` resolves the same adapter twice through a single-caller `_implemented` wrapper. Resolve the module once and read `IMPLEMENTED_CAPABILITIES` directly; remove the wrapper. | tools/autopilot/build-compatibility.py:88 | 7 | BOB |
| R46 | [1/4] | 🟡 | Mechanical replay identifies two touched compatibility tests passing against base: `test_scrubbed_and_authenticated_envs_reach_the_child_process` and `test_aborting_build_leaves_no_bundle_behind_for_any_declared_host`. Retain preservation controls, but add assertions binding the new hooks assets and schema-2 behavior. | tests/autopilot/test_compatibility.py:187 | 7 | BOB, mech-check |
| R47 | [1/4] | 🟡 | Mechanical replay identifies eight touched pure-duty tests passing against base. These preservation cases do not establish the new normalization/depth behavior; pair them with discriminating contract cases, including dispatch-depth enforcement and project-root normalization from a subdirectory. | tests/autopilot/test_guards_pure_duties.py:235 | 4 | BOB, mech-check |
| R48 | [1/4] | 🟡 | Mechanical replay identifies `test_accepts_every_valid_name_status_reason_combination` passing against base. Keep it as a construction control and pair it with rejection cases covering invalid field types as well as invalid strings. | tests/autopilot/test_hosts_contract.py:95 | 2 | BOB, mech-check |
| R49 | [1/4] | ⚪ | `doctor._newest_evidence` calls `json.loads` unguarded (doctor.py:66), and `_observed_capabilities` indexes `record["observed"]` unguarded (doctor.py:72). A corrupt or v1-shaped evidence file crashes `--diagnose` with a traceback. Treat it as not probed and report the reason. | plugins/autopilot/scripts/doctor.py:66 | 9 | ALICE |
| R50 | [1/4] | ⚪ | A stale, contradictory CHANGELOG bullet remains: "Codex declares isolation only; Gemini declares none, because neither host implements native session identity". The code and `hosts.json` now declare Codex identity, isolation and interception, and Gemini identity and isolation. | plugins/autopilot/CHANGELOG.md:15 | Phase 2 task 2 | BLAKE |
| R51 | [1/4] | ⚪ | `--diagnose` crashes with a traceback on a corrupt or hand-edited probe evidence JSON or a missing key; there is no error path for `json.loads` or `record["observed"]`. A forged evidence file with `resource_check: passed` makes a profile read `certifiable: true`, since the evidence is not authenticated. | plugins/autopilot/scripts/doctor.py:66 | Phase 1 task 3 | BLAKE |
| R52 | [1/4] | ⚪ | Claude's static probe reports every implemented capability as `unavailable: no_auth` unless `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` is in the environment. A Keychain-logged-in user is misreported. `CODEX_SESSION_ID`, `CLAUDE_CODE_CHILD_SESSION` and `GEMINI_SESSION_ID` are asserted as host variables without any recorded real-host confirmation. | plugins/autopilot/scripts/claude.py:58 | Phase 1 task 1 | BLAKE |

## Alice

```
[ALICE] 🟠 `AUTOPILOT_DISPATCH_DEPTH` is never read as a lineage signal. Task 3 requires three independent signals: `JOB_ENV`, the depth env var, and the lineage record. A non-integer value must refuse `invalid_request`, and a value >= `MAX_JOB_DEPTH` must refuse `recursion_depth`. `DEPTH_ENV` is only written into the standalone instruction (jobs.py:491, 495). `derive_ancestry` and `build_job_request` ignore it, and no test covers it. A child that strips `JOB_ENV` but keeps the depth variable is not refused. | File: plugins/autopilot/scripts/jobs.py:300 | Task: 3
[ALICE] 🟠 `render_hook_reply` departs from the design §8 shapes, and the tests pin the departure. (a) PostToolUse refused emits `{"systemMessage": ...}` where the design requires `{"decision": "block", "reason": ...}`. (b) Stop refused with `stop_active=True` emits empty stdout where the design requires `{"systemMessage": "autopilot: <reasons>"}`. (c) SessionStart refused emits nothing where the design requires a `systemMessage`. (d) PreToolUse deny uses only `denied[0]` where the design requires reasons joined by '; '. The tests assert the divergent shapes: test_interception.py:619-631 (PostToolUse not block), 657-659 and 763-764 (Stop released only asserts "not block"), and 594-606 (first reason only). | File: plugins/autopilot/scripts/codex.py:147 | Task: 6
[ALICE] 🟠 `is_git_push` misses push forms the source grammar denies, so `custody_push` is never consulted for them. I ran it: `sudo -u x git push`, `env -i git push`, `nice -n 5 git push`, `timeout 5 git push`, `(git push)`, `{ git push; }`, `if true; then git push; fi` and `! git push` all return False. The prefix-skip loop stops at the first option token. The segment executable is never found after a subshell, brace, `then` or `!`. The characterization fixture records `sudo -u git git push` as expected "deny" with `divergence: null` (hook_characterization.json:248-256), but the target returns False. No test asserts this. The design's own prefix rule is silent on options, but it calls the function a "conservative superset" where a false positive is cheap. A safe fix scans each segment for any token whose name is `git` followed by `push`. | File: plugins/autopilot/scripts/guards.py:313 | Task: 4
[ALICE] 🟠 `evaluate_hook` discards the resolved `project_root`. Design §2 gives `translate_hook(event, payload, *, project_root)`, but the adapters take no `project_root`, and `evaluate_hook` calls `translate_hook(event, payload)` (interception.py:183). Each adapter then copies the payload `cwd` into `project_root` (claude.py:106,109; codex.py:102,105,134). With a bound session whose `cwd` is a subdirectory of the binding root, an absolute `/repo/backlog/x.md` is not normalized against the root. I ran it: `project_root='/repo/sub'` returns allowed, and `'/repo'` returns the lifecycle deny. This defeats the v1c2-R17 normalization on the real hook path. The `env` argument of `evaluate_hook` is also ignored, so claude.py:119 reads `os.environ` for the child-session signal where the design says hook environment. | File: plugins/autopilot/scripts/interception.py:183 | Task: 5
[ALICE] 🟠 `test_hook_behavior_equivalence` does not bind to the real adapters or the push grammar. It installs a test-local `translate_hook` (`_doc_translate_hook`) at test_interception.py:296. It covers only `doc-file-*` and `doc-bash-*` fixtures at test_interception.py:290-294. The 14 `push-*` fixtures are never asserted against `guards.is_git_push` or the real adapters. `_push_commands()` is only used for an unbound-skip check. This is how the `sudo -u git git push` regression above passes unnoticed. The task also asked for the source `test_guard_push_grammar.py` cases to be ported, and the wrapper-with-option rows are absent from test_guards_pure_duties.py:542-577. | File: tests/autopilot/test_interception.py:288 | Task: 5
[ALICE] 🟠 `request_job` is 60 lines (mechanical facts, line 442). That breaks the 50-line rule. Behavior-preserving split: move the standalone branch into `_write_request_file(resolved_file, root, payload)` and `_standalone_instruction(request, argv, request_file, root)`. | File: plugins/autopilot/scripts/jobs.py:442 | Task: 3
[ALICE] 🟡 `_write_new` re-implements `log_sink_refusal._pinned_parent_fd` and `_descend`. The same mkdir-then-`O_DIRECTORY|O_NOFOLLOW` descent loop is duplicated. Task 3 names these two as the required reuse for the job file and close-child artifact. Replace the loop with `parent_fd = _pinned_parent_fd(root / relative.parent, root)`. | File: plugins/autopilot/scripts/jobs.py:324 | Task: 3
[ALICE] 🟡 `request_job` writes the request file with `os.open(..., O_CREAT|O_WRONLY|O_NOFOLLOW)` plus `truncate(0)`, with no `O_EXCL` and no pinned parent descriptor. It can overwrite any existing regular file inside the project, and only the final component is symlink-protected. The CLI pre-checks `lexists` (autopilot.py:234), but the library function does not. Use the same exclusive pinned creation as `_write_new`. | File: plugins/autopilot/scripts/jobs.py:467 | Task: 3
[ALICE] 🟡 Relative `request_file` handling is inconsistent. `request_job` resolves it against the cwd (jobs.py:460). The child env var and the steps carry the unresolved `str(request_file)` (jobs.py:491, 494). `derive_ancestry` joins the env value to `project_root` (jobs.py:306), while `--bind-job` reads it relative to the child cwd (autopilot.py:252). With `--out` relative and cwd different from `--project-root`, the child cannot find or ancestry-check the file. Emit the resolved path in `env`, `stdin` and `steps`. | File: plugins/autopilot/scripts/jobs.py:491 | Task: 3
[ALICE] 🟡 `derive_ancestry` opens the `JOB_ENV` file without confirming it is a regular file. The contract says regular file, at most 2 MiB. Opening a FIFO blocks the hook or CLI. | File: plugins/autopilot/scripts/jobs.py:306 | Task: 3
[ALICE] 🟡 `roles.py` names its dataclasses `RoleRow` and `ResolvedProfile`. The design §6 contract (verbatim) and later consumers (design lines 911 and 1283 reference `ProfileResolution`) name them `RoleResolution` and `ProfileResolution`. Rename to match the contract. | File: plugins/autopilot/scripts/roles.py:38 | Task: 8
[ALICE] 🟡 `gemini.py` exports no `HOOK_REGISTRATIONS`. The §2 contract says every adapter exports it, empty when interception is not implemented. `run_hook` and `build-compatibility.py` paper over this with `getattr(..., {})` and `getattr(..., ())`. `run_hook` also carries a `dict` branch (interception.py:250-253) that exists only for test fakes (test_interception.py:244, 260, 275). Add `HOOK_REGISTRATIONS = ()` to gemini.py and drop the dict branch. | File: plugins/autopilot/scripts/gemini.py:27 | Task: 6
[ALICE] 🟡 `--hook` reads stdin before `run_hook` rejects an unregistered event. The §8 contract says an event outside `HOOK_REGISTRATIONS` is a usage error (exit 2) before stdin is read. `run_hook` raising `SystemExit` from a library function is a second smell. Validate the event in `_hook` before reading stdin, or have `run_hook` raise `ValueError`. | File: plugins/autopilot/scripts/autopilot.py:327 | Task: 10
[ALICE] 🟡 `_request_job` picks the requester host as the first adapter whose `SESSION_ENV_VAR` is set. A codex session launched from a claude session inherits `CLAUDE_CODE_SESSION_ID`, so the requester is recorded as claude. Resolve it from the adapter whose session env is set and whose `source` matches the host, or refuse when more than one is set. | File: plugins/autopilot/scripts/autopilot.py:236 | Task: 10
[ALICE] 🟡 `session_from_hook_input` is exported by both intercepting adapters and unit-tested, but `evaluate_hook` only calls `hosts.current_session(host_id, env)`. The `hook_input` session source is unreachable on the real hook path. If the hook process lacks the session env var, the trace and `read_facts` record no session. Fall back to `session_from_hook_input(payload)` in `evaluate_hook`. | File: plugins/autopilot/scripts/interception.py:184 | Task: 5
[ALICE] 🟡 `bind_job_session` writes the lineage record itself (jobs.py:386). The Task 3 contract says it writes nothing and the CLI caller records it. This is a harmless deviation but should be documented or aligned. | File: plugins/autopilot/scripts/jobs.py:386 | Task: 3
[ALICE] ⚪ `doctor._newest_evidence` calls `json.loads` unguarded (doctor.py:66), and `_observed_capabilities` indexes `record["observed"]` unguarded (doctor.py:72). A corrupt or v1-shaped evidence file crashes `--diagnose` with a traceback. Treat it as not probed and report the reason. | File: plugins/autopilot/scripts/doctor.py:66 | Task: 9

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
R12: fail
R13: pass
```

## Blake

```
[BLAKE] 🟠 Hook CLI fails open on malformed payloads. `tool_input: null` (also a non-dict `tool_input`, or a non-str `patch` or `prompt`) raises an uncaught AttributeError or TypeError inside `translate_hook`, and the process exits 1 with a traceback. I reproduced it with `echo '{"cwd":"/tmp","tool_name":"Bash","tool_input":null}' | python3 plugins/autopilot/scripts/autopilot.py --hook claude --event PreToolUse`. Claude Code treats exit 1 as a non-blocking hook error, so the tool call proceeds. The spec says malformed input refuses, and `_invalid_input_reply` only covers bad JSON and a missing `cwd`. | File: plugins/autopilot/scripts/codex.py:104 | Task: Phase 1 task 4

[BLAKE] 🟠 "Equivalent absolute and relative project paths yield the same guard decision" is not met. The Claude and Codex adapters pass the session `cwd` as `project_root`, not the binding root, and `_normalize_rel` only strips an exact string prefix. These return different decisions for the same file: `document_path=/r/backlog/x.md` with `project_root=/r` is denied, but `project_root=/r/sub` is allowed, and `/r//backlog/x.md` with `project_root=/r` is allowed. `command='echo hi > /r/wip/x.md'` with `project_root=/r/sub` is also allowed. A session started in a subdirectory therefore defeats the document-location guard for absolute paths. I ran `run_guard(DOCUMENT_LOCATION, …)` to confirm. | File: plugins/autopilot/scripts/guards.py:156 | Task: Phase 1 task 4

[BLAKE] 🟠 Controller-keyed guards are skipped entirely when no `.autopilot/controller` directory is found. In standalone or unbound sessions the custody-push, state-integrity, review-completeness, live-job, post-handoff, departure and context-reinjection duties never run, and the skip is only recorded in `skipped`. The spec says stateful guards call the same controller seam in both modes and that missing enforcement refuses affected operations. Enforcement also disappears if that marker directory is absent or removed. | File: plugins/autopilot/scripts/interception.py:197 | Task: Phase 1 task 2

[BLAKE] 🟠 The shipped package has no activation path for the Claude hooks, so "retain Claude hooks through supported packaging" is not delivered. There is no `.claude-plugin` manifest, and `plugin.json` has no hooks field. `hosts.json` says activation is `client-manifest-hooks-field`, yet nothing in the package supplies that manifest. Only `tools/autopilot/probe-host.py` writes one, into a temporary copy. The README says the assets "are not activated", and the dispositions defer activation to a "publication/install PRD". That is honest, but the v1 finding that compatibility assets were not real client assets is closed only on paper. | File: plugins/autopilot/contracts/hosts.json:7 | Task: Phase 1 task 2 / Phase 2 task 1

[BLAKE] 🟡 The shipped Codex hook asset uses the Claude-only variable `${CLAUDE_PLUGIN_ROOT}`. The probe replaces it by string substitution (`hooks.replace("${CLAUDE_PLUGIN_ROOT}", …)`). The live Codex probe therefore does not exercise the variable resolution of the asset that actually ships. This also conflicts with the rule that shared assets must not require Claude-only variables. | File: plugins/autopilot/compatibility/codex/hooks.json:9 | Task: Phase 2 task 1

[BLAKE] 🟠 `--resolve-roles` for the Claude-free profile silently drops Gemini. `resolve_roles` defaults `implementor_codex_present=False` and `gemini_cli_available=False`, so `--resolve-roles --profile codex-gemini --lane full` returns `status: resolvable` with only Codex roles (alice, blake, bob, implementor). I ran it, and Eve (the Gemini doubt reviewer) is absent. `--diagnose` derives the fact from the profile, so the two paths disagree. The required Gemini role should appear and block, not vanish. | File: plugins/autopilot/scripts/autopilot.py:281 | Task: Phase 1 task 3

[BLAKE] 🟡 Role resolution looks only at the adapters' `IMPLEMENTED_CAPABILITIES` constants, never at the static probe results. In `--diagnose` with no Claude or Gemini auth, `hosts[]` shows those hosts' capabilities as `unavailable: no_auth`. The profiles still show `status: resolvable` with every role `resolved`. A missing binary would resolve the same way. The spec asks for resolution "to supported isolated hosts" and for specific role/capability blockers. `certifiable` is false, but `status` says resolvable. | File: plugins/autopilot/scripts/roles.py:79 | Task: Phase 1 task 3

[BLAKE] 🟡 Role resolution ignores the policy's per-role input requirements and exclusions. `JobRequest` accepts whatever `excluded_input_kinds` the caller supplies. It never applies `policy.input_exclusions` for the role, so a `blind` job can be built with a `diff` input and an empty exclusion list. `role_id` is not checked against the policy role ids either. `contracts/hosts.json` `role_requirements` and `implementor_duties` are read by no code or test; `roles.REQUIRED_CAPABILITIES` duplicates the capability rows and nothing checks that the duties are covered. The spec asks roles to resolve "with their input/guard requirements". | File: plugins/autopilot/scripts/jobs.py:147 | Task: Phase 1 task 3

[BLAKE] 🟡 `_check_relative_path` blocks only the `docs/dev/project-management/autopilot` tree. A job input or child artifact can name `.autopilot/controller/...` (state, 0600 credential files), which would be digested and listed to the reviewer. `request_job` opens an existing project file with O_CREAT and truncates it, with no exclusive create; only the CLI pre-checks existence. | File: plugins/autopilot/scripts/jobs.py:90 | Task: Phase 1 task 4

[BLAKE] 🟡 `AUTOPILOT_DISPATCH_DEPTH` is emitted in the standalone instruction but no code reads it. Recursion is bounded only by `AUTOPILOT_JOB_REQUEST` and the lineage record. The dispositions doc claims the "depth variable ... refuse[s] alone" (v1c1-R17), and no code backs that. | File: plugins/autopilot/scripts/jobs.py:31 | Task: Phase 1 task 1

[BLAKE] 🟡 The Phase 2 probe requirement is only partly met. `probe-host.py` allows a live probe only for claude and codex (`LIVE_HOSTS`) and rejects gemini. Doctor's `gemini_ran` therefore can never be true, and the codex-gemini profile can never become certifiable. The delivery receipt records "No live host invocation ran". That is honest unavailability, but the spec's "verify real invocation/resources/identity/interception for the selected roles" has no Gemini coverage. The receipt text also says probes "never invoke the host", which contradicts the live mode in `probe-host.py`, and it records 1841 tests against the 1848 in the gate. | File: tools/autopilot/probe-host.py:41 | Task: Phase 2 task 1 / task 3

[BLAKE] 🟡 The source-map behaviors owned by 00014 (8 rows) all remain `evidence.status: planned`, with null artifacts and no recorded supported or unavailable duty split. Phase 2 task 2 asks the source map to be updated for supported and still-unavailable client duties. The duty status lives only in README, CHANGELOG and the bundles. The dispositions doc also lists a `hook-v1` capability ID that does not exist in `_CAPABILITIES`. | File: tools/autopilot/source-map.json | Task: Phase 2 task 2

[BLAKE] ⚪ A stale, contradictory CHANGELOG bullet remains: "Codex declares isolation only; Gemini declares none, because neither host implements native session identity". The code and `hosts.json` now declare Codex identity, isolation and interception, and Gemini identity and isolation. | File: plugins/autopilot/CHANGELOG.md:15 | Task: Phase 2 task 2

[BLAKE] ⚪ `--diagnose` crashes with a traceback on a corrupt or hand-edited probe evidence JSON or a missing key; there is no error path for `json.loads` or `record["observed"]`. A forged evidence file with `resource_check: passed` makes a profile read `certifiable: true`, since the evidence is not authenticated. | File: plugins/autopilot/scripts/doctor.py:66 | Task: Phase 1 task 3

[BLAKE] ⚪ `is_git_push` misses an indirect push such as `GIT=git; $GIT push`: the `git` token is an assignment, and no indirect marker or `git` word match fires. Only the conservative cases are covered. | File: plugins/autopilot/scripts/guards.py:313 | Task: Phase 1 task 2

[BLAKE] ⚪ Claude's static probe reports every implemented capability as `unavailable: no_auth` unless `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` is in the environment. A Keychain-logged-in user is misreported. `CODEX_SESSION_ID`, `CLAUDE_CODE_CHILD_SESSION` and `GEMINI_SESSION_ID` are asserted as host variables without any recorded real-host confirmation. | File: plugins/autopilot/scripts/claude.py:58 | Task: Phase 1 task 1

Test gate was taken from the run inputs and not rerun. I ran only inspection commands and narrow reproductions (the malformed-hook run, the document-location guard cases, `--resolve-roles`, `--diagnose`).

B1: fail
B2: pass
B3: pass
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
```

## Bob

```
FIX:
- [BOB] 🟠 Standalone request output can overwrite an existing file: `request_job` opens without `O_EXCL` and explicitly truncates it. The CLI existence check leaves a race. Use descriptor-bound exclusive creation and refuse existing files atomically. | File: plugins/autopilot/scripts/jobs.py:442 | Task: 3
- [BOB] 🟠 The dispatch-depth backstop is never enforced. `DEPTH_ENV` is written but neither parsed nor checked; a session carrying only `AUTOPILOT_DISPATCH_DEPTH=1` can request another job. Validate this signal independently, including malformed values. | File: plugins/autopilot/scripts/jobs.py:300 | Task: 3
- [BOB] 🟠 Push detection misses executable pushes, including `sudo -u git git push`, `git 'push'`, and `"git" push`. Whitespace splitting cannot establish the promised conservative superset. Tokenize shell quoting and fail closed for uncertain wrapper options; assert bound hook denials for these cases. | File: plugins/autopilot/scripts/guards.py:313 | Task: 4
- [BOB] 🟠 Document guards normalize against payload cwd instead of the discovered project root. From `/repo/src`, an edit to `/repo/backlog/x.md` is allowed although `/repo` is bound. Discover the binding before translation and pass its root through the specified `project_root` parameter. | File: plugins/autopilot/scripts/interception.py:174 | Task: 5
- [BOB] 🟠 Hook evaluation ignores `session_from_hook_input`. A valid payload session with no session environment variable produces `session=None`, losing native identity in controller reads and traces. Use the adapter’s validated hook-input identity. | File: plugins/autopilot/scripts/interception.py:184 | Task: 5
- [BOB] 🟠 Malformed tool payloads escape hook validation: `tool_input=null` raises `AttributeError`, and an Agent prompt with a non-string value raises `TypeError`. These bypass the structured deny/warning reply. Validate event-specific payload types and render `hook_input_invalid` consistently. | File: plugins/autopilot/scripts/interception.py:236 | Task: 5
- [BOB] 🟡 Hook stdin is read without a bound and before host/event validation. The later length check cannot prevent unlimited allocation or waiting on stdin for an invalid event. Validate registration first, then read at most `MAX_HOOK_INPUT_BYTES + 1`. | File: plugins/autopilot/scripts/autopilot.py:321 | Task: 10
- [BOB] 🟠 Reply rendering weakens the specified enforcement: PostToolUse refusals become informational messages rather than block decisions; active Stop and refused SessionStart events emit nothing. Implement the exact contract shapes and replace tests that currently require the weaker behavior. | File: plugins/autopilot/scripts/codex.py:147 | Task: 6
- [BOB] 🟠 Gemini’s required live probe is absent: `LIVE_HOSTS` excludes Gemini and the CLI rejects it before writing evidence. Implement its two hook-free `--record-session` invocations and explicit unavailable/auth outcomes. | File: tools/autopilot/probe-host.py:215 | Task: 9
- [BOB] 🟠 Probe preparation performs no required resource-containment check. `copytree` follows symlinks by default, so an external target can be copied into the package and subsequently reported as contained. Check source symlink targets and declared assets before launch; invalidate every capability on escape. | File: tools/autopilot/probe-host.py:56 | Task: 9
- [BOB] 🟠 Probe prompts never execute `--record-session`; they include it only as a “Probe tag” after “Do nothing else.” Identity therefore remains unobservable when hooks do not load. Append the actual absolute Python command and test that it executes. | File: tools/autopilot/probe-host.py:157 | Task: 9
- [BOB] 🟠 The required Claude child-lineage observation is missing. The probe exercises only Bash pushes and never attempts top-level and nested Agent dispatches. Add that bounded scenario and observe delegation only when the parent dispatch succeeds and the nested dispatch receives `recursion_depth`. | File: tools/autopilot/probe-host.py:157 | Task: 9
- [BOB] 🟡 Probe timeout defaults to 600 instead of 120 and accepts values above 600, non-positive values, and non-finite floats. Validate the documented range before creating evidence or launching hosts. | File: tools/autopilot/probe-host.py:215 | Task: 9
- [BOB] 🟠 Doctor never validates evidence `schema_version`. A record with another version and observed status strings can clear capability gaps; malformed newest JSON instead crashes diagnosis. Validate version and record shape before consuming evidence, and report invalid evidence explicitly. | File: plugins/autopilot/scripts/doctor.py:54 | Task: 9
- [BOB] 🟠 Characterization does not prove source equivalence: document cases use a test-local translator, push expectations are derived from the implementation under test, Stop cases are largely unexercised, and one phase fixture is explicitly excluded. Run every applicable fixture through shipped adapters and compare recorded target verdicts; resolve divergences explicitly. | File: tests/autopilot/test_interception.py:288 | Task: 5
- [BOB] 🟠 The binding test creates and recursively removes `.autopilot` under the temporary directory’s shared parent. This can remove unrelated pre-existing contents or another test’s fixture. Put both the enclosing binding and nested repository beneath one test-owned temporary root. | File: tests/autopilot/test_interception.py:105 | Task: 5
- [BOB] 🟡 Delivery evidence is promoted to `passed` while its cited receipt records seven failures and exit 1. The supplied final green gate does not repair that receipt, whose real-host explanation also incorrectly says only static probes exist. Record successful final verification and actual probe outcomes before promoting evidence. | File: docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json:29 | Task: 12
- [BOB] 🟡 Role capability requirements duplicate `contracts/hosts.json` instead of reading it. Contract changes can therefore leave role resolution reporting an unsupported profile as resolvable. Load the contract’s `role_requirements` and add a contract-change regression. | File: plugins/autopilot/scripts/roles.py:23 | Task: 8
- [BOB] 🟡 `request_job` is 60 lines according to the supplied AST facts, exceeding the 50-line limit. Extract standalone instruction construction and file creation into focused helpers while preserving controller/standalone separation. | File: plugins/autopilot/scripts/jobs.py:442 | Task: 3
- [BOB] 🟡 `_validate` resolves the same adapter twice through a single-caller `_implemented` wrapper. Resolve the module once and read `IMPLEMENTED_CAPABILITIES` directly; remove the wrapper. | File: tools/autopilot/build-compatibility.py:88 | Task: 7
- [BOB] 🟡 Mechanical replay identifies two touched compatibility tests passing against base: `test_scrubbed_and_authenticated_envs_reach_the_child_process` and `test_aborting_build_leaves_no_bundle_behind_for_any_declared_host`. Retain preservation controls, but add assertions binding the new hooks assets and schema-2 behavior. | File: tests/autopilot/test_compatibility.py:187 | Task: 7
- [BOB] 🟡 Mechanical replay identifies eight touched pure-duty tests passing against base. These preservation cases do not establish the new normalization/depth behavior; pair them with discriminating contract cases, including dispatch-depth enforcement and project-root normalization from a subdirectory. | File: tests/autopilot/test_guards_pure_duties.py:235 | Task: 4
- [BOB] 🟡 Mechanical replay identifies `test_accepts_every_valid_name_status_reason_combination` passing against base. Keep it as a construction control and pair it with rejection cases covering invalid field types as well as invalid strings. | File: tests/autopilot/test_hosts_contract.py:95 | Task: 2

VERIFY:
- (none)

KNOWN:
- (none)

R1: fail
R2: fail
R3: fail
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Carl

```
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
R12: fail
R13: pass
[CARL] 🟠 Design §11 and Task 10 contract mandate _CAPABILITIES appends 'hook-v1' before 'request-job-v1', but 'hook-v1' was omitted from _CAPABILITIES, causing --list-capabilities to not advertise the implemented --hook mode | File: plugins/autopilot/scripts/autopilot.py:25 | Task: 10
[CARL] 🟡 Function request_job is 60 lines, exceeding the 50-line limit (R12); extract standalone instruction construction and request-file writing into a helper to separate controller submission from standalone dispatch | File: plugins/autopilot/scripts/jobs.py:442 | Task: 3
[CARL] 🟡 Design §2 adapter interface contract mandates every adapter export HOOK_REGISTRATIONS: tuple[HookRegistration, ...] (empty when interception is not implemented), but gemini.py omits HOOK_REGISTRATIONS = () | File: plugins/autopilot/scripts/gemini.py:34 | Task: 6
```

Verdict: 52 findings
Tests: 1848 passed, 0 failed (suite run this cycle)

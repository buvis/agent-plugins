# Design: specflow cross-host validation

## Overview

This spec produces the evidence the first release rests on. It builds the canonical fixtures, runs a full handoff across the three hosts, proves native-Kiro coexistence and concurrent-edit protection, reviews security, measures what a phase loads, builds the eval runners, runs every behavioral rule's eval on every supported host, judges the parity gate for each retiring skill, and checks the conversion skill against the one conversion that was done for real.

## Context and constraints

- Depends on 00003 to 00008: every reference, check, eval record, and host install exists before this spec starts.
- This spec owns evidence obligations: RULE-001 criteria 4 and 6, and success measures 1 to 3 and 6 to 8 (REL-002). Its other tasks prove again, on real hosts, criteria that earlier specs own, and cite them across the dependency.
- By decision 2026-10-04 #10, T-053 no longer checks the user documentation; that check moved to T-061 in 00001. T-081 came here from phase 5, because it needs the fixtures of T-050.
- Kiro host sessions use kiro-cli engine v3 headless with the installed specflow Power (R1; Power activation alone proven 2026-11-09). Only the three Kiro steps of T-051, T-052, and the own-spec-type notes of `intake-bugfix` and `shared-dialogue-design-first` stay manual in Kiro IDE. CLI records retain `host: kiro-ide`, use `mode: automated`, and name kiro-cli and Kiro Agent Server versions in `hostVersion`. Under R1, the shared Kiro Agent Server supplies the engine-behavior portion of REL-002.6; CLI runs do not prove IDE UI integration. The named manual checks supply that portion. Neither Power activation nor the `host` label proves a complete runner or IDE compatibility. Kiro CLI remains untested as a supported product and is not listed as supported (PKG-003.4 unchanged).
- Everything here lives outside the package, under `tests/specflow/` and `docs/dev/project-management/reviews/`; the release check of 00002 fails if any of it appears inside.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

## Architecture

```text
tests/specflow/
├── fixtures/
│   ├── workflow/                     # Canonical workflow fixtures (T-050)
│   ├── sessions/                     # Per-session inputs
│   ├── results/                      # Synthetic scorer records
│   └── conversion/calcard-00032/     # The reference conversion: source PRD and its artifact set as it stands (T-081)
├── rules/                            # Rule and runner/scorer tests
├── contract/                         # Schema, state, and fixture tests
├── compatibility/                    # Handoff, coexistence, context efficiency, conversion: records and tests
├── evals/
│   ├── sessions/                     # Developer turns and continuation graph
│   ├── runners/                      # run_claude.py, run_codex.py, run_kiro.py, score.py, manual-run.md
│   ├── schemas/result.schema.json    # The run record
│   ├── results/<host>/<session>/     # Stored run records with their scores, one file per run
│   └── README.md                     # How to run the evals on each host
├── security/                         # One regression test per security finding
└── parity/
    ├── README.md                     # How the parity gate is judged
    └── <skill>.md                    # One report per retiring skill
docs/dev/project-management/reviews/YYYY-MM-DD-specflow-security-review.md
```

A run and its score are separate steps. A runner plays one session on one host and stores a run record; the scorer reads that record and marks every eval that names the session. A manual run produces the same record by hand, so one scorer serves all three hosts.

## Module placement

Placement describes the current checkpoint; existing partial modules are edited, not recreated.

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `tests/specflow/fixtures/workflow/` | edit | T-050 | standard, quick, partially approved, stale, malformed, recovered, and completed specs, as feature and bugfix and as Design-First where that changes behavior; a spec with its intake item and `qa-log.md`; a spike in each form; a spec on hold; a configured workspace root and specs folder |
| `tests/specflow/contract/test_fixtures.py` | edit | T-050 | every fixture passes schema and artifact validation, or fails exactly where it is meant to |
| `tests/specflow/compatibility/cross-host-handoff.md` | new | T-051 | the recorded five-step handoff with the status document after each step |
| `tests/specflow/compatibility/native-kiro-coexistence.md` | new | T-052 | the recorded run |
| `tests/specflow/evals/sessions/concurrent-edit.json`, its eval record and fixture | new | T-053 | the session in which a second writer edits between the agent's read and its write |
| `docs/dev/project-management/reviews/YYYY-MM-DD-specflow-security-review.md` | new | T-054 | the security review |
| `tests/specflow/security/test_*.py` | new | T-054 | one regression test per finding, and `test_stdlib_only.py` |
| `tests/specflow/compatibility/context-efficiency.md` | new | T-055 | measured sizes, and which references each phase loaded |
| `tests/specflow/evals/runners/run_claude.py` | edit | T-056 | Claude Code runner |
| `tests/specflow/evals/schemas/result.schema.json`, `tests/specflow/rules/test_score.py`, `tests/specflow/fixtures/results/` | edit | T-056 | the run record, and scorer tests on stored records |
| `tests/specflow/evals/runners/run_codex.py` | edit | T-056 | Codex runner |
| `tests/specflow/evals/runners/run_kiro.py` | new | T-056 | kiro-cli v3 runner and Power activation evidence |
| `tests/specflow/evals/runners/score.py` | edit | T-056 | common scorer |
| `tests/specflow/evals/runners/manual-run.md` | edit | T-056 | manual IDE steps |
| `tests/specflow/evals/SR-<area>-NNN.json`, `tests/specflow/evals/sessions/` | edit | T-057 | any eval record or session still missing |
| `tests/specflow/evals/results/<host>/<session>/<n>.json` | new | T-057 | the stored results, per host and run |
| `tests/specflow/parity/<skill>.md`, `tests/specflow/parity/README.md`, `tests/specflow/evals/README.md` | new | T-058 | six parity reports and the two maintainer guides |
| `tests/specflow/fixtures/conversion/calcard-00032/` | new | T-081 | the seven copied files and the fixture notes; a seeded variant with two checked tasks |
| `tests/specflow/evals/sessions/conversion-calcard.json` | new | T-081 | the conversion session |
| `tests/specflow/compatibility/test_conversion_fixture.py` | new | T-081 | the structural comparison of a stored conversion run with the proven set |
| `.github/workflows/validate.yml` | edit | T-054, T-081 | one step each, added with the first test of its folder: `tests/specflow/security`, `tests/specflow/compatibility` |

## Components and interfaces

### Compatibility fixtures

- Create in Kiro-shaped workspace, resume in Codex fixture.
- Modify requirements in Claude fixture, observe design/tasks stale.
- Complete a task in Kiro IDE fixture, observe checkbox state elsewhere.
- Recover native-Kiro documents that predate `.specflow.json`.
- Resume captured Kiro bugfix and Design-First specs without creating stray artifacts or renumbering IDs.
- Create a Design-First spec in each host; Kiro IDE opens it as Design-First, and approving its requirements never stales the approved design.
- Create a bugfix spec in each host and match the §6.6 shape and `.config.kiro` of a Kiro capture; open it in Kiro IDE as a Bug Fix spec.
- Run a bugfix spec end to end: task 1 fails on unfixed code, task 2 passes, both pass after the fix; a refuted hypothesis reopens design; a flipped preservation test is never edited.
- Ensure quick profile still produces all three canonical documents.
- Resume a spec from a configured specs folder in each host.
- Get the same status JSON for the same fixture on every host.

Where each scenario above is proven:

| Scenario | Vehicle | Task |
|---|---|---|
| Create in Kiro, resume in Codex; a task completed in Kiro shows elsewhere | the five-step handoff record | T-051 |
| Modify requirements in Claude Code, design and tasks go stale | a step of the handoff record, repeated with the edit made by Kiro's native workflow | T-051, T-052 |
| Recover native-Kiro documents; resume the captured bugfix and Design-First specs | sessions `recover-native-kiro`, `resume-kiro-bugfix`, `resume-kiro-design-first`, on the captures of T-027 | T-057 |
| Create a Design-First spec, and a bugfix spec, in each host | sessions `shared-dialogue-design-first` and `intake-bugfix` of 00006, run on each host; that Kiro IDE opens each as its own type is noted in the manual record | T-057 |
| Bugfix spec end to end | sessions `bugfix-confirmed`, `bugfix-refuted`, `bugfix-flipped-preservation` of 00006 | T-057 |
| Quick profile still gives three documents | session `intake-all-supplied` of 00006 | T-057 |
| Resume from a configured specs folder in each host | session `configured-specs-folder` | T-057 |
| The same status document on every host | each run record ends with `validate_spec.py status --json`; the scorer compares them across hosts per session | T-057 |

T-057 also writes the comparison cases its source text names, as two sessions on designs and task plans copied from the second port plan's source skills: `comparison-design` (reuse, contracts, blockers, isolated and inline review) and `comparison-tasks` (sizing, risk evidence, coupling).

### Cross-host tests

- T-051, the handoff: requirements in Kiro IDE, design in Codex, tasks in Claude Code, implementation in Codex, verification in Kiro IDE, on one fixture. After each step the record holds the output of `validate_spec.py status --json`, the `.specflow.json` file, the list of files in the spec folder, and `validate_spec.py hash` of each artifact. After the tasks step, still in Claude Code, the approved requirements are edited, design and tasks are shown stale, and the three artifacts are approved again. The assertions: the artifact paths never move, each approval and hash survives the change of host, task state carries over, and no host-specific canonical file appears. The same five steps in another host order end in the same status document, compared in `phase`, `artifacts`, `gates`, `hold`, and whether `nextTask` is null; that order has Kiro IDE implementing (requirements in Codex, design in Claude Code, tasks in Codex, implementation in Kiro IDE, verification in Claude Code), so that a task completed in Kiro shows elsewhere.
- T-052, coexistence: Kiro's native Spec workflow edits an artifact without touching `.specflow.json`; the next resume in another host detects the changed hash, stales the right approvals, and reverts nothing.
- T-053, concurrent edit: a second writer changes a file after the first has read it and before it writes. The helper's own guard is already tested by T-025 of 00004; this task tests the agent. It is one session, `concurrent-edit`: after the turn in which the agent reads the artifact, the runner (or the developer, in a manual run) edits the file as the second writer, and the next turn must end with the agent reporting a conflict and the edit intact.

### Security review of T-054

Scope, from the source task: the catch-up skill's handling of fetched content and temporary clones; containment of configured paths; secret handling; destructive operations; spike cleanup; instructions hidden in artifact or upstream text; the file reads of the code baseline; cross-spec reshapes; the advisory scans and the link checker. It takes in the findings and regression tests that T-076 and T-077 of 00007 produced. Every finding gets a regression test under `tests/specflow/security/`. The dependency scan is one test, `test_shipped_and_maintainer_scripts_import_only_the_standard_library`. It reads every Python file under `plugins/specflow/`, `tools/specflow/`, and `tests/specflow/evals/runners/` and fails on an absolute import whose top-level module is neither in `sys.stdlib_module_names` nor defined under those folders or under the repository's `scripts/`. Relative imports are skipped. The run that counts is CI's, on Python 3.10.

### Context efficiency of T-055

One record with two parts. Sizes: lines and bytes of `SKILL.md`'s frontmatter and body, of each phase reference, and of each review reference. Loading: for each phase and profile, the files the routing table of 00006 expects (the three shared contracts, the phase reference, and that phase's AWS reference; for a design review, its tier's files), compared with the per-turn `filesRead` of the turns that ran that phase in the stored run records. A file outside the expected set is a finding. Which passages of a file were read cannot be seen from a path, so for the profile marks the record states the instruction and the measured sizes of the marked passages, and says that this half is not proven. A host whose event output does not list reads is recorded as not measured. T-055 uses the run records of T-057 and therefore runs after it. It proves 00006 AWS-002 criterion 2 on real hosts as far as paths can.

### Eval runners of T-056

- Runners: Claude Code headless (`claude -p` with the plugin loaded) and Codex (`codex exec`) run sessions unattended. Kiro sessions use `run_kiro.py` with `kiro-cli chat --v3 --no-interactive --output-format stream-json` and the installed Power; only the IDE-asserted steps use recorded manual runs: the same fixture and turns, the captured files and transcript, and the scoring of every eval on that session, stored with the results.
- A broken session fails every eval on it; the result names the session so the fix lands once.
- Eval records are written with each reference. Every eval runs on every supported host before release 0.1 (requirements §9); CI runs `check_rules.py` and deterministic tests on ordinary changes. Release evidence records the tested runtime/fixture revisions so changed inputs are rechecked before publication; unchanged results need not be rerun merely to repeat a gate.

```text
python3 tests/specflow/evals/runners/run_claude.py <session> --model MODEL [--out DIR]
python3 tests/specflow/evals/runners/run_codex.py <session> --model MODEL [--out DIR]
python3 tests/specflow/evals/runners/run_kiro.py <session> --model MODEL [--out DIR]
python3 tests/specflow/evals/runners/score.py <run-record.json>
```

A runner plays one session and writes a run record. `score.py` scores every eval naming that session. The exit-code table in Error handling is authoritative for runners, scoring, and comparison. `manual-run.md` uses the same fixture, evidence, isolation, and scoring rules.

#### Run environment — Decided

- D11 chooses a temporary `CODEX_HOME`, with specflow installed through the T-042 install surface and its tree checked against `runtimeRevision`. It does not authorize moving personal instructions or waiving contamination. The choice is settled; successful live isolation is not established.
- Each workspace is an independent Git repository with one baseline commit. The supervisor verifies its resolved Git root before any host setup. A session and its `continues` descendants form one serial batch. Each session is one conversation, resumed turn by turn; a continuation is a new conversation seeded from its parent's finished workspace and identified by `continuesRun`.
- Before each turn, apply its fixture `edit`. If its `expects` pattern does not match the previous reply, mark the session broken at that turn. A turn without `expects` is unconditional. A failed parent prevents its dependent sessions from running.
- Fixture-local instructions remain test inputs. Personal instructions, skills, hooks, and unrelated plugins are excluded from specflow runs. R3 source-skill runs intentionally use the normal profile and are identified separately in parity reports; they cannot supply specflow release results.
- The supervisor owns fixture preparation, host configuration, credentials, and record persistence. Agent tools get workspace writes, plugin reads, and the runtime files needed to execute helpers. They cannot modify the plugin, read credentials, or inspect another workspace. Both native file tools and shell descendants must respect this boundary; a writable-directory setting alone does not restrict reads.

#### Run environment — Proposed

This revision chooses the following implementation routes. They require design and task reapproval, then the proof below; they are not claims that the current partial adapters implement them.

**Workspace placement.** The old repository-local scratch root is unsuitable: the active Seatbelt profile denies `.git/hooks` writes throughout the source tree, and Claude discovers ancestor instructions independently of Git-root verification. The first explains the observed Codex initialization failure; the second explains why successful `git init` would not establish Claude isolation. See [Claude memory loading](https://code.claude.com/docs/en/memory#how-claudemd-files-load). Use a private batch directory created under `/private/tmp/specflow-evals-<random>/`, outside the checkout and the developer's home. Give it separate `workspaces/`, `resources/`, and `control/` children. The supervisor exports the committed plugin tree into `resources/specflow/` and verifies its hash. Only the per-session workspace is a Git root. Check resolved ancestors for instruction files before launch; reject unexpected ancestors, symlinks, or inherited `GIT_*` settings. Keep committed results at their existing repository paths. The location change is an explicit proposed setup change, not permission to rerun a denied operation: authorize the revised setup through the normal tool/OS approval route or a developer-run check first.

**Claude Code.** Use `claude -p` from the external workspace with an empty `CLAUDE_CONFIG_DIR` under `<batch>/control/claude-home/`, the existing supervisor-supplied setup token, an explicit model, `--plugin-dir <batch>/resources/specflow`, and `--add-dir <batch>/resources/specflow`. Load generated supervisor settings via `--settings`, exclude user settings, and admit only fixture project/local settings (`--setting-sources project,local`). Inspect those files against the committed fixture before launch; this preserves fixture rules while the external workspace removes checkout-parent settings. The generated configuration disables auto memory and unrelated hooks/MCP, excludes discovered non-fixture instruction paths with `claudeMdExcludes`, and preserves fixture-local instruction loading. This is the chosen route; `--bare` is rejected because its installed help excludes OAuth.

The added directory supplies the intended plugin read scope, but also widens default writes. Therefore generated settings must deny native Edit/Write access and sandbox writes to the plugin; enable the shell sandbox with failure when unavailable and no unsandboxed fallback; deny native Read and shell reads of `control/`, the real home, and other workspaces. Permit the exact plugin helper commands in the workspace, with only required runtime paths readable. Remove the setup-token variable from tool subprocesses using `sandbox.credentials.envVars` deny entries. Inspect the effective settings before use: ignored or unsupported controls fail preflight. These settings cannot override a managed policy or the outer Seatbelt boundary. [Claude settings reference](https://code.claude.com/docs/en/settings-reference) describes the separate tool and shell controls; installed-version acceptance remains to be proven.

**Codex.** Retain D11's temporary home at `<batch>/control/codex-home/`, mode 0700, with credential files mode 0600. Replace the existing active-sign-in copy with a fresh, independent `codex login` session issued directly into that home by the developer. Serialize the batch as the sole owner of that session; never copy refresh tokens from, or sync them back to, the normal profile. Generated config and host-created install/conversation metadata are allowed; inherited personal configuration is not. This credential source revises D11's implementation, not its isolation choice. Auth provisioning precedes the timed evaluation batch; installation and all host runs remain timed.

Use a generated Codex permissions profile: deny filesystem reads by default, allow minimal runtime reads, the workspace read/write, and the verified installed specflow subtree read-only. Deny the rest of `CODEX_HOME`, the real profile, other workspaces, and general temporary-directory access to tools. A narrower plugin exception is required because the installed package lives below the private home. The host process can access its home; model-controlled tools cannot access its credential or conversation files. Remove inherited secret environment variables from tool processes. Mode 0700 and `workspace-write` alone are insufficient, since tools share the host's UID. [Codex permissions](https://learn.chatgpt.com/docs/permissions) documents restricted-read profiles; support and enforcement on installed 0.167.0 must pass the proof gate. No broader-access fallback is selected.

**Kiro.** Use the installed Power with a custom agent that explicitly lists fixture-local resources and the Power, disables inherited default resources through `chat.disableInheritingDefaultResources`, and excludes unrelated MCP/Powers. Restrict tools to workspace writes and Power/runtime reads. This documented setting is a candidate mechanism, not proof that installed 2.35.1 honors it. R1's manual IDE checks remain mandatory. See [Kiro custom-agent configuration](https://kiro.dev/docs/custom-agents/configuration-reference/).

**Limits and cleanup.** Constants for every runner are `MAX_SESSION_TURNS = 24`, `TURN_TIMEOUT = 600`, `SESSION_TIMEOUT = 1800`, and `BATCH_TIMEOUT = 7200` (seconds). Validate the whole continuation graph and turn counts before setup; the longest current session has 17 turns. Claude retains `SESSION_BUDGET_USD = 5` across a resumed conversation. Codex and Kiro have no proven dollar ceiling; finite elapsed time does not bound their billed dollars. Record limits and reported usage in `notes`; do not invent rates or automatically retry sessions.

Use monotonic deadlines. The batch clock starts before setup/installation/scoring and the session clock before its first host turn. Each subprocess receives the minimum of its own timeout and remaining enclosing deadlines. Exhaustion prevents new work, including continuation sessions. On timeout, SIGINT, SIGTERM, or caught failure, terminate the active process group, wait at most five seconds, kill and reap survivors, then save incomplete records and clean up. Credentials and private workspaces are removed after successful record capture or failure. SIGKILL and machine failure cannot guarantee cleanup: report any residual private batch directory and stop before another batch until verified removal. Do not print credential contents while diagnosing leftovers.

#### Run environment — Blocked

| Route | Missing proof before release runs | Failure outcome |
|---|---|---|
| Shared setup | Authorized external scratch setup, own Git root, clean ancestor instructions, correct package hash | `notRun`; no host starts |
| Claude | Effective isolated settings; fixture instructions still load; plugin references and status helper succeed; plugin writes and control/home reads are denied | Automated Claude runs remain blocked; no silent switch to normal profile |
| Codex | Independent sign-in, installed tree match, temporary-home isolation, credential denial to both file and shell tools, cleanup | No active-token copy, personal-file move, or contaminated-evidence fallback |
| Kiro | Installed-version resource isolation and permissions, own-root status helper, both CLI and KAS versions | Power activation alone is insufficient; R1's full-manual fallback requires its recorded design/task change |

First prove boundary controls with synthetic sentinels, including forbidden reads through file tools, shell commands, and symlinks; never use a real credential as a test target. Then run the T-056 passing/deliberately-broken eval self-check on each automated adapter and round-trip a manual record. Record the generated policy, versions, normalized loaded instruction inventory, and outcomes without secrets. A model's assertion that it is isolated is not evidence. Any unsupported control, unknown instruction inventory, denied required operation, or failed boundary check keeps the route blocked. Obtain authorization for a denied prerequisite through the normal approval mechanism; do not change flags to bypass it.

Current implementation status: `run_claude.py` and `run_codex.py` deliberately block live entry. The latter still copies a supplied sign-in in its synthetic-tested helper; replace that path before any real authentication use. `run_kiro.py` is absent. The new limits, policies, and independent sign-in are not implemented. Probe history and the static diagnosis belong to `plans/specflow-release-fast-path.md` section 8.

#### Instruction classification and release eligibility

Resolve each loaded path before normalization. An allowed instruction must be inside the session workspace, present in the committed fixture or reproducible continuation baseline (or an explicit session `edit`), and match that expected content. Imports must meet the same rule recursively. The separately hash-verified plugin is allowed but excluded from `instructionFiles` by the schema's convention. Any other loaded instruction, including an unexpected ancestor, personal file, or generated instruction absent from those inputs, makes the run *tainted*. An incomplete inventory is *unknown*, not clean; an empty array with `instructionMeasurement: not-measured` proves nothing.

A release result requires `instructionMeasurement: measured`, no tainted instructions, successful boundary proof for that exact host/configuration, complete session/status, matching frozen revisions, every eval passing, and every required human rubric review complete. Read-based assertions additionally require `readMeasurement: measured`; unavailable reads never pass by an empty list. Set `releaseEvidence: true` only after these checks; missing/false means ineligible. Keep classification and boundary-proof references in normalized `notes`. Current code conservatively leaves release eligibility false; T-056 must implement and test this predicate. No tainted-evidence waiver is requested.

#### Scoring

- `messages` holds one entry per developer turn: the agent's final reply to that turn. `filesRead` holds one list per turn, in the same order.
- The scorer implements every assertion kind of the eval schema of 00005 and fails on a kind it does not know; a test compares the two lists.
- File kinds read `files` and `unchanged`. Read kinds read `filesRead`. `one_question_per_message` passes when no entry of `messages` has more than one sentence that ends in a question mark outside fenced code and outside its list of options. `recommended_option_first` passes when, in every entry that marks an option as recommended, that option is the first one listed.
- The status comparison across hosts is a second command, `score.py --compare <record> <record> ...`, given one session's latest record per host. It compares the named fields of each record's `status` only: `phase`, `artifacts`, `gates`, `hold`, and whether `nextTask` is null. Text a model wrote, such as a task title, is not compared.
- A `rubric` assertion is scored by a model judge through `claude -p` with a fixed prompt. Store `judge: model:<id>`, verdict, and reason. When testing Claude Code, use a judge model different from the model under test. The developer judges every model FAIL. For `P` model PASS verdicts per host/session, uniformly sample without replacement `S = min(P, max(10, ceil(P / 10)))`; if `P = 0`, sample none. Thus three passes require three reviews, eleven require ten, and 101 require eleven. Persist the sample so rescoring cannot reroll it. If `10 * wrong > S`, require human review of every rubric in that session; one disagreement among three escalates, one among ten does not, two among ten do. Bind reviews and samples to the evidence digest; changed evidence invalidates them. This proposed R2 clarification adds a minimum sample of ten (or all available); current code rounds up but samples as few as one. Until required judgments are complete, use the Error handling exit table.

### Conversion acceptance of T-081

The fixture folder has two parts. `input/` is the session's workspace: the PRD as an unprocessed intake item, and a snapshot of the calcard-mcp source files the proven artifacts cite, since the skill's discover step reads code. `expected/` holds the proven set and the seeded variant. The proven set is copied from `buvis/calcard-mcp` as it stands, seven files: the five spec files (`bugfix.md`, `design.md`, `tasks.md`, `.config.kiro`, `.specflow.json`) and the intake item's `idea.md` and `qa-log.md`, which hold the source PRD and the developer's five answers. The fixture notes give the copy date and each file's SHA-256, and say what the trial was: requirements and design approved, the task plan drafted and not approved, no completed work, no receipt, a `.specflow.json` written by hand, and artifact conversion and review shown, not implementation or a running runtime.

The session `conversion-calcard` gives the shipped `convert-prd` skill that `idea.md` as its source and answers its questions as the developer did. A run on a host is equivalent to the proven set when all of these hold: the same file set; the bugfix headings; the same clause numbers under each behavior section; four top-level tasks in Kiro's order; a `Sources:` line that names the processed intake item; every obligation of `idea.md` cited by a clause or by a recorded decision; and every task that is checked in the expected set checked in the run. Hashes, the `.config.kiro` UUID, timestamps, and prose are not compared. The receipt is checked by the `conversion-receipt` check of 00007, since the proven set has none. The regression for unchecked completed work cannot run on the proven set, which has no completed work; it runs on a seeded variant whose first two tasks are checked with outcomes. The developer accepted this on 2026-10-04 (ruling D9). T-081 runs after T-056, since its host runs need the runners.

### Parity gate

Before release 0.1, per source skill covered by RULE-001.6:

1. Collect the inputs: the fixture and the developer turns of each session whose evals carry the skill's rules.

2. Run the source skill by name on Claude Code with `claude -p --setting-sources user` in the normal profile (R3). Use source-skill paths rather than specflow assertion paths.
3. Run specflow on every supported host with the same inputs and its isolated profile.
4. Score each mapped rule with the same model judge. Apply R2 human review to failures and sampled passes.
5. Record, per rule, the source result and specflow's result per host in `tests/specflow/parity/<skill>.md`.
6. Have the developer review each of the six per-skill reports. The skill may retire only when every rule mapped from it passes on specflow on every host. A rule the source skill fails still has to pass on specflow: the rule is the contract, not the old behavior.

The retirement PRD in `buvis/agent-skills` cites these reports (Plan A "Retirement"). create-prd and review-prd-backlog also wait for the autopilot repoint (`qa-log.md` Q2).

## Data model

The run record, `tests/specflow/evals/results/<host>/<session>/<n>.json` with `n` counting runs from 1, so a rerun never overwrites an earlier result. It is checked with `check_schema` of 00004 against `result.schema.json`:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schemaVersion` | integer | yes | `1` |
| `host` | string | yes | `kiro-ide`, `codex`, or `claude-code` |
| `hostVersion` | string | yes | reported version; `not-started` if no version was obtained |
| `mode` | string | yes | `automated` or `manual` |
| `session` | string | yes | the session's `name` |
| `model` | string | yes | reported model after launch; explicit requested model before launch (identified as unverified in `notes`) |
| `instructionFiles` | array | yes | every instruction file the host loaded besides the plugin |
| `runtimeRevision` | string | yes | the git tree id of `plugins/specflow/` at the run |
| `fixtureRevision` | string | yes | the git tree id of the session's own fixture folder at the run |
| `sessionRevision` | string | yes | the git blob id of the session file at the run |
| `continuesRun` | object | no | for a `continues` session: the `host`, `session`, and `n` of the run whose finished workspace it started from; that workspace is then the baseline of `files` and `unchanged` |
| `status` | object or null | yes | the output of `validate_spec.py status --json` at the end of the run, or null when the helper could not run |
| `brokenAt` | integer | no | the turn at which the session went off script |
| `notRun` | string | no | the reason a run did not finish; such a record holds no scores and counts as not run |
| `notes` | string | no | normalized observations, configured limits, usage, instruction classification, boundary-proof references, and requested-versus-reported metadata |
| `messages` | array | yes | one string per developer turn: the agent's final reply to it |
| `filesRead` | array | yes | one array per developer turn: the paths the agent read in it |
| `files` | array | yes | one object per file the run created or changed in the workspace, with `path` and `text` |
| `unchanged` | array | yes | workspace paths whose content equals the fixture's |
| `readMeasurement` | enum | no | `measured` or `not-measured`; missing means unknown |
| `instructionMeasurement` | enum | no | `measured` or `not-measured`; missing means unknown |
| `releaseEvidence` | boolean | no | eligibility predicate above; missing/false never authorizes release |
| `scores` | array | no | each object requires `rule`, `evalRevision` (eval git blob id), `passed`, `failures`, and `rubrics` |
| `scores[].failures` | array | yes within a score | objects require `assertion` (integer), `kind`, `reason` (strings) |
| `scores[].rubrics` | array | yes within a score | objects require `assertion`, `verdict` (`PASS`/`FAIL`), `judge`, `reason`, `passed`; optional `review` object holds the human decision |
| `rubricReview` | object | no | requires `evidenceSha256`, `verdicts`, `sample`, `sampled`, `manualAll`, `required`; persists judge decisions and human-review selection |

`rubricReview.evidenceSha256` binds judgments to the record, reconstructed workspace, and eval inputs. Exclude derived `scores`, `rubricReview`, and `releaseEvidence` from that digest so final eligibility cannot invalidate the judgments it requires; current code excludes only the first two, so T-056 must add the third exclusion and test it. Changing source evidence, including instruction observations, must still invalidate judgments. `verdicts` maps assertion keys to decisions; `sample` and `required` are assertion-key arrays; `sampled` and `manualAll` are booleans. Human reviews carry the matching evidence digest, verdict, human judge identity, and reason. Schema shape validation does not replace these semantic checks in `score.py`.

When a reserved run never starts, keep the requested `model`, `hostVersion: not-started` unless a version was independently obtained, `status: null`, empty messages/reads/files/unchanged arrays, both measurements `not-measured`, `releaseEvidence: false`, and a nonempty `notRun`; omit scores. Keep valid requested-input revision IDs. If input validation fails before a record can be assigned valid identities, report the usage/setup error without fabricating a record. After a partial run retain captured evidence and known host/model metadata, but still omit scores and mark it ineligible.

A parity report, `tests/specflow/parity/<skill>.md`, has one row per mapped rule: source result, specflow result per host, and ready-to-retire verdict. Its run procedure is defined once in Parity gate. Source results remain separate from specflow release records.

## Data and control flow

Order, serially in task-file order: T-050, T-056, T-054, T-053, T-081, T-057, T-051, T-052, T-055, T-058. T-057 shakes down Claude Code first, freezes the package tree, then runs Codex and Kiro CLI on that tree. Package fixes return to Claude shakedown and stale all hosts; eval or judge corrections rerun only the affected sessions and hosts. T-051 and T-052 use the frozen package.

Evidence is tied to runtime, fixture, session, and eval revisions plus the judge/review evidence digest. T-053 and T-081 produce provisional host records before T-057 freezes the package. Those records count only if all these inputs still match the frozen candidate and the release-eligibility checks pass; otherwise rerun the affected host sessions. Package changes invalidate every host result; fixture/session/eval/judge changes invalidate their dependent records and reviews. Recheck before release (T-064 in 00001); unchanged valid records need not be repeated.

## Error handling

This is the only exit-code contract. Batch aggregation gives 2 precedence over 1, then 0.

| Command | 0 | 1 | 2 |
|---|---|---|---|
| Runner (including scoring) | complete run, every eval and required judgment passes | failed eval, unjudged rubric, broken session, or interruption/timeout after at least one reply | invalid input/turn limit, setup or host-start failure, plugin mismatch, or interruption/timeout before any reply |
| `score.py RECORD` | every eval passes with required reviews complete | failed eval, unjudged rubric, broken session, or `notRun` record | invalid record, unsupported assertion/schema, unavailable required evidence or revision input |
| `score.py --compare RECORD...` | valid same-session records from distinct hosts have equal selected status fields | selected status fields differ | invalid/incomplete records, missing status, inconsistent input revisions, duplicate host, or fewer than two hosts |

Limits produce `notRun` and no scores, not fabricated failed assertions. A broken scripted conversation instead fails every eval on that session. Record eligibility is a separate release gate: exit 0 alone does not prove privacy, instruction isolation, or revision freshness.

- A session that breaks fails every eval on it, and the result names the session, so the fix lands once.
- A host that cannot start, or a run that stops early, is recorded as not run with the reason; it is never counted as a pass.
- A rule the source skill fails still has to pass on specflow: the rule is the contract, not the old behavior.
- An eval that fails is investigated and the rule, the instruction, or the eval is corrected; a rerun is recorded as a rerun, with the earlier result kept.
- A conversion run that drops an obligation or unchecks completed work fails the comparison.

## Security and privacy

- Trust boundaries are the supervisor, the host process, its model-controlled tools, and committed evidence. Fixtures and model output are untrusted; they must not widen tool access or become supervisor instructions. No production data is used.
- A copied refresh token may rotate concurrently and invalidate the real sign-in. Use the proposed independent batch login, sole session ownership, and cleanup instead. This risk applies even if the file copy is private and later deleted. [OpenAI session guidance](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions) requires retaining replacement tokens and serializing refreshes; the observed Claude login incident is an analogy, not proof of identical Codex revocation behavior.
- The host can read its private authentication state; agent file tools and shell descendants must be denied it, including through sibling paths and symlinks. The selected native policies require synthetic denial tests. Never log credentials, authorization URLs, or inherited secret environment values. A suspected exposure requires rotation.
- Records include messages, file contents, instruction paths, and notes, so synthetic secrets alone do not make them public. Normalize workspace, plugin, batch/control, repository, and home roots recursively in every string before persistence. Preserve allowed/tainted classification before normalization; `<HOME>` is not evidence of cleanliness. Read every record for secrets and remaining absolute machine paths before commit. Reject a record containing either, fix collection, and repeat the run; do not publish a selectively edited passing transcript. Raw output and private configuration stay outside tracked results and are removed with the batch.
- The calcard-mcp fixture is copied from another repository of the developer. Before it is committed, it is read for anything that must not be public here.
- The security review reads code and text and runs the repository's own tests; it executes nothing from upstream.

## Testing strategy

This spec is testing, so its own tests guard the instruments.

- T-050, `test_fixtures.py`: each fixture validates, or fails with exactly the finding it was built to show.
- T-053 (provisional until the T-057 revision check): the `concurrent-edit` session's eval passes on each host: a conflict is reported and the second writer's edit is intact.
- T-054: the security tests and `test_stdlib_only.py` pass.
- T-056, `tests/specflow/rules/test_score.py`, in CI, on stored run records: a passing eval and a deliberately broken eval on one record are scored correctly; a manual record goes through the scorer and back without loss; a record validates against its schema; the scorer's kinds equal the eval schema's; an unjudged rubric exits 1. The live self-check, one session on each automated runner, needs signed-in hosts, so it runs once by hand and its result goes in the task's `Outcome:` line.
- T-056 boundary/limit tests (RULE-001.4): verify allowed fixture instructions and imports versus personal/ancestor/generated taint, unknown inventories, credential/plugin denial, deadline expiry between turns and during setup/scoring/continuations, hung descendants, cancellation cleanup, and residual-directory refusal. Sampling cases include P=0, 3, 10, 11, 101; one versus two disagreements out of ten; evidence-change invalidation and stable rescoring. Distinguish synthetic policy tests from installed-host enforcement.
- T-057: `python3 tools/specflow/check_rules.py` passes with no filter, so every behavioral rule has an eval; every eval passes on every supported host; the results are stored per host.
- T-058: each report lists every rule mapped from the skill with the source result and specflow's result per host; a skill is marked ready to retire only when every specflow result passes.
- T-081 (host records provisional until the T-057 revision check), `test_conversion_fixture.py`: the comparison passes for a faithful run and fails for a seeded obligation drop and for an unchecked completed task.

## Rollout and migration

The deterministic tests join CI when T-050 lands. Host runs do not run in CI: they need three signed-in hosts and, for Kiro IDE, the developer. They run before the release, on the candidate's package and fixtures, and their stored results are the release evidence. No personal skill is retired here; a parity report only says a skill is ready, and its owning repository does the rest.

## Risks and edge cases

- An eval passes on one run and fails on the next, since a model's output varies: impact m, likelihood m; mitigation: assertions are deterministic wherever one fits, and a rubric is marked as one; fallback: the failing run is kept and investigated, and the rule or its wording is fixed.
- Host runs cost more time than planned, with every session on three hosts and manual IDE assertions: impact m, likelihood h; mitigation: evals are grouped onto as few sessions as stay readable, so the run count follows sessions, not rules; fallback: none that keeps the release rule, since no eval may be skipped.
- Installed Codex read capture is currently unmeasured; another host may also omit read events: impact m, likelihood m; mitigation: the runner takes `filesRead` from the host's own event output; fallback: mark context efficiency not measured; use manual observation for affected eval assertions only if it supplies measured evidence, otherwise keep release blocked.
- Likely next change, a fourth supported host: each host is one runner or one manual procedure; impact l, likelihood m; mitigation: the scorer and the run record are host-neutral; fallback: a recorded manual run.
- Likely next change, a second version of the run record: results are stored per host and carry `schemaVersion`; impact l, likelihood m; mitigation: the scorer rejects a version it does not know; fallback: rerun the sessions.
- Likely next change, more sessions as rules are added: nothing limits their number; impact l, likelihood h; mitigation: a new rule joins an existing session when it can; fallback: none needed.
- Independent Codex authentication or restricted reads fail on the installed CLI: impact h, likelihood m; mitigation: prove the chosen profile with synthetic sentinels before signing in, then validate the independent login in T-056; fallback: keep Codex blocked and revise the route through the design gate, without copying active credentials or moving personal instructions.
- A host ignores generated isolation controls or discovers ancestor instructions: impact h, likelihood m; mitigation: inspect effective configuration and measured instruction inventory in the exact external workspace; fallback: fail preflight and obtain a separately reviewed route.
- Credential rotation races or interrupted cleanup expose authentication state: impact h, likelihood m; mitigation: independent session, sole owner, tool-read denial, and cleanup; fallback: stop launches, rotate any exposed credential, and verify removal before resuming.
- Codex/Kiro elapsed-time limits do not bound billed dollars: impact m, likelihood m; mitigation: explicit models, finite serial batches, no automatic session retries, and recorded usage where available; fallback: stop automated runs and retain the spending-cap requirement until an enforceable host control exists. Approval of this revision accepts this trade-off, not unlimited automatic batches.
- Edge case: a manual run and an automated run of the same session are scored by the same evals; `mode` only records how the run was made.

## Requirement traceability

| Design element | Criteria |
|---|---|
| Eval runners, the manual procedure, stored results per host | RULE-001.4 |
| Parity gate and its reports | RULE-001.6, REL-002.7 |
| Cross-host handoff (T-051) | REL-002.1, REL-002.3 |
| Native-Kiro coexistence (T-052): an edit to approved requirements stales design and tasks on the next validation | REL-002.2 |
| Compatibility tests and eval runs: Claude/Codex; Kiro Agent Server behavior through CLI under R1, plus mandatory manual IDE handoff/coexistence/type checks | REL-002.6 |
| The handoff reads gates and the next task from the status document alone | REL-002.8 |
| Security review, context efficiency, conversion acceptance, concurrent edit | criteria of 00003, 00004, 00006, and 00007, cited across the dependency |

## Alternatives considered

1. **Checklists run by hand on every host** (smallest diff: no runner, no scorer). Rejected. RULE-001 criterion 4 wants every eval run on every host; by hand, each change to a rule would cost three full manual passes.
2. **Three runners, one scorer, and manual IDE assertions** (chosen by R1). The same Kiro Agent Server loads the installed Power; the recorded IDE steps retain UI evidence.
3. **An eval framework.** Rejected without a registry search: it would have to drive three different host command lines and accept hand-made IDE records, and maintainer tooling carries no dependency (`AGENTS.md`).
4. **Host runs in CI.** Rejected for the first release: they need signed-in hosts and a person for Kiro IDE; CI runs the deterministic tests, and the release reads the stored results.

5. **Retain dollar caps on all hosts** (smallest diff). Safe but leaves Codex/Kiro
   blocked because no supported enforcement mechanism was found. **Bounded
   turns and elapsed time** is proposed to permit finite evaluation runs while
   exposing the financial limitation. A custom billing proxy or different API
   harness is rejected: it adds infrastructure, may not serve these sign-ins,
   and would change the host under test.

6. **Temporary Codex home versus moving personal instructions.** The temporary
   home was chosen by D11. This revision proposes independent batch authentication
   because copying an active refresh token can affect the original session. Moving personal files affects concurrent sessions;
   accepting instruction contamination would weaken the behavioral evidence.
   Neither alternative is authorized as a fallback by this revision.

## Reuse inventory

- The session and eval formats and `check_rules.py` of 00005; `check_schema` of 00004 for the run record.
- `validate_spec.py status --json` and `validate` of 00004: the handoff and coexistence assertions are comparisons of their output.
- The guard test of T-025 (00004), cited by the concurrent-edit session instead of repeated.
- The Kiro captures of 00004 (T-027), the sessions and fixtures written with each reference in 00006 and 00007, and the host records of 00008.
- The security findings and regression tests of T-076 and T-077 (00007).
- `claude -p`, `codex exec`, and kiro-cli v3 as the three headless engines; `sys.stdlib_module_names` for the import test.
- The calcard-mcp artifact set as it stands (task plan not approved, no receipt), as the acceptance fixture.
- Original design-time searches found no runner or scorer in `scripts`, `.github`, `plugins`, or `templates`. At the 2026-11-10 revision, reuse `tests/specflow/evals/runners/run_claude.py` for workspace verification, process-group termination, batch records, and tree hashing; `score.py` for scoring and normalization inputs; and `run_codex.py:temporary_home` for private installation and cleanup. `tests/specflow/rules/test_score.py` contains 41 deterministic instrument tests. These modules remain partial and blocked for live execution as their checkpoint documentation states.

## Open decisions

Pending design approval: the external scratch layout and explicit Claude permission/isolation route; independent Codex batch login and restricted tool-read profile; Codex/Kiro time/turn limits without a dollar ceiling; and the R2 minimum-sample/rounding clarification. D11's temporary-home choice is already decided and is not asked again. Installed-host proof is an acceptance condition, not another design ruling.

The request to unblock work authorizes preparing these changes, not recording artifact approval, permission approval, or a contaminated-evidence waiver. After design approval, update T-056's copied environment, authentication, limits, and sampling contracts and request task-plan reapproval. Until then tasks retain stale text and implementation remains paused. All task order, host coverage, review, and live self-check obligations remain.

Earlier rulings remain: D9 compares the real conversion fixture structurally and tests completed work on a seeded variant; R1 splits Kiro engine and IDE evidence; R2 amends D10 with model judging plus human review; R3 supplies normal-profile source-skill runs; D11 selects the temporary Codex home. This revision changes the credential source and makes the execution controls concrete; none of their live proof is claimed.

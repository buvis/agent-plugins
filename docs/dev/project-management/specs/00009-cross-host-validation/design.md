# Design: specflow cross-host validation

## Overview

This spec produces the evidence the first release rests on. It builds the canonical fixtures, runs a full handoff across the three hosts, proves native-Kiro coexistence and concurrent-edit protection, reviews security, measures what a phase loads, builds the eval runners, runs every behavioral rule's eval on every supported host, judges the parity gate for each retiring skill, and checks the conversion skill against the one conversion that was done for real.

## Context and constraints

- Depends on 00003 to 00008: every reference, check, eval record, and host install exists before this spec starts.
- This spec owns evidence obligations: RULE-001 criteria 4 and 6, and success measures 1 to 3 and 6 to 8 (REL-002). Its other tasks prove again, on real hosts, criteria that earlier specs own, and cite them across the dependency.
- By decision 2026-10-04 #10, T-053 no longer checks the user documentation; that check moved to T-061 in 00001. T-081 came here from phase 5, because it needs the fixtures of T-050.
- Kiro IDE has no headless mode. Its runs are recorded manual runs by the developer: the same fixture and turns, the captured files and transcript, scored like any other run.
- Everything here lives outside the package, under `tests/specflow/` and `docs/dev/project-management/reviews/`; the release check of 00002 fails if any of it appears inside.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

## Architecture

```text
tests/specflow/
├── fixtures/
│   ├── workflow/                     # Canonical workflow fixtures (T-050)
│   └── conversion/calcard-00032/     # The reference conversion: source PRD and its artifact set as it stands (T-081)
├── compatibility/                    # Handoff, coexistence, context efficiency, conversion: records and tests
├── evals/
│   ├── runners/                      # run_claude.py, run_codex.py, score.py, manual-run.md
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

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `tests/specflow/fixtures/workflow/` | new | T-050 | standard, quick, partially approved, stale, malformed, recovered, and completed specs, as feature and bugfix and as Design-First where that changes behavior; a spec with its intake item and `qa-log.md`; a spike in each form; a spec on hold; a configured workspace root and specs folder |
| `tests/specflow/contract/test_fixtures.py` | new | T-050 | every fixture passes schema and artifact validation, or fails exactly where it is meant to |
| `tests/specflow/compatibility/cross-host-handoff.md` | new | T-051 | the recorded five-step handoff with the status document after each step |
| `tests/specflow/compatibility/native-kiro-coexistence.md` | new | T-052 | the recorded run |
| `tests/specflow/evals/sessions/concurrent-edit.json`, its eval record and fixture | new | T-053 | the session in which a second writer edits between the agent's read and its write |
| `docs/dev/project-management/reviews/YYYY-MM-DD-specflow-security-review.md` | new | T-054 | the security review |
| `tests/specflow/security/test_*.py` | new | T-054 | one regression test per finding, and `test_stdlib_only.py` |
| `tests/specflow/compatibility/context-efficiency.md` | new | T-055 | measured sizes, and which references each phase loaded |
| `tests/specflow/evals/runners/run_claude.py`, `run_codex.py`, `score.py`, `manual-run.md` | new | T-056 | the runners, the scorer, the manual procedure |
| `tests/specflow/evals/schemas/result.schema.json`, `tests/specflow/rules/test_score.py`, `tests/specflow/fixtures/results/` | new | T-056 | the run record, and scorer tests on stored records |
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

- Runners: Claude Code headless (`claude -p` with the plugin loaded) and Codex (`codex exec`) run sessions unattended. Kiro IDE uses a recorded manual run per session: the same fixture and turns, the captured files and transcript, and the scoring of every eval on that session, stored with the results.
- A broken session fails every eval on it; the result names the session so the fix lands once.
- Eval records are written with each reference. Every eval runs on every supported host before release 0.1 (requirements §9); CI runs `check_rules.py` and deterministic tests on ordinary changes. Release evidence records the tested runtime/fixture revisions so changed inputs are rechecked before publication; unchanged results need not be rerun merely to repeat a gate.

```text
python3 tests/specflow/evals/runners/run_claude.py <session> [--out DIR]
python3 tests/specflow/evals/runners/run_codex.py <session> [--out DIR]
python3 tests/specflow/evals/runners/score.py <run-record.json>
```

A runner plays one session and writes a run record. `score.py` reads a run record, evaluates every eval whose `session` matches, and writes the scores into the record. Exit codes of all three: 0 done (for the scorer: every eval passed), 1 a failed eval, an unjudged rubric, or a broken session, 2 a usage error, a host that could not start, or an installed plugin that is not the revision under test. `manual-run.md` tells the developer how to produce the same run record from a Kiro IDE session, under the same preconditions.

Run environment:

- The runner copies the session's fixture to a scratch workspace under `docs/dev/tmp/specflow/evals/` and runs `git init` and one commit there, so every git command of the agent under test sees the workspace and not this repository. A session that names another in `continues` starts from that session's finished workspace; the runner plays a session and the sessions that continue it in one batch, and the record of the later one names the run it started from.
- One session is one conversation, resumed turn by turn (`claude -p --resume`, `codex exec resume`). A `continues` session is a new conversation. A turn may carry an `expects` pattern (00005): when the agent's previous reply does not match it, the session is broken at that turn and the record says so; a turn without one is fed unconditionally. This keeps a run that went off script from passing assertions about what is absent.
- The developer's own instructions, skills, hooks, and plugins must not reach the agent: they hold the personal skills specflow is compared with, and rules such as one question per message, which two assertion kinds test. The runner passes the host's flags that leave user-level settings out (the installed `claude --help` lists them; T-056 fixes the set), and the record lists every instruction file the host still loaded. For Codex the reviewer found no flag that leaves out the user-level instruction file, so its runner uses a temporary Codex home, described below. A run where they could not be left out says so and is not release evidence.
- Each runner fixes a permission or sandbox mode limited to the scratch workspace, a timeout per turn, and a spending cap per session, as constants in the runner.
- Claude Code loads the plugin per run with `--plugin-dir plugins/specflow` and installs nothing. Codex has no such option in `codex exec --help`, as the pre-pass reviewer read it. By the developer's ruling of 2026-10-04 (D11), its runner makes a temporary Codex home for the batch that holds only the sign-in and the plugin, installed by the install surface the T-042 record of 00008 names; it hashes the installed copy and exits 2 when that differs from `runtimeRevision`. The developer's own Codex home is not touched. The temporary home lives under the ignored `docs/dev/tmp/specflow/evals/` and holds a copy of the sign-in, so the runner removes it when the batch ends, also after a failure. Nobody has run this yet: T-056 first proves that the sign-in works from a temporary home, and if it does not, the task stops and the developer decides.

Scoring:

- `messages` holds one entry per developer turn: the agent's final reply to that turn. `filesRead` holds one list per turn, in the same order.
- The scorer implements every assertion kind of the eval schema of 00005 and fails on a kind it does not know; a test compares the two lists.
- File kinds read `files` and `unchanged`. Read kinds read `filesRead`. `one_question_per_message` passes when no entry of `messages` has more than one sentence that ends in a question mark outside fenced code and outside its list of options. `recommended_option_first` passes when, in every entry that marks an option as recommended, that option is the first one listed.
- The status comparison across hosts is a second command, `score.py --compare <record> <record> ...`, given one session's latest record per host. It compares the named fields of each record's `status` only: `phase`, `artifacts`, `gates`, `hold`, and whether `nextTask` is null. Text a model wrote, such as a task title, is not compared.
- A `rubric` assertion is judged by the developer, by hand: the scorer prints the rubric and the messages it applies to, and stores the verdict, the judge, and the reason in `scores`. Until it is judged the scorer exits 1.

### Conversion acceptance of T-081

The fixture folder has two parts. `input/` is the session's workspace: the PRD as an unprocessed intake item, and a snapshot of the calcard-mcp source files the proven artifacts cite, since the skill's discover step reads code. `expected/` holds the proven set and the seeded variant. The proven set is copied from `buvis/calcard-mcp` as it stands, seven files: the five spec files (`bugfix.md`, `design.md`, `tasks.md`, `.config.kiro`, `.specflow.json`) and the intake item's `idea.md` and `qa-log.md`, which hold the source PRD and the developer's five answers. The fixture notes give the copy date and each file's SHA-256, and say what the trial was: requirements and design approved, the task plan drafted and not approved, no completed work, no receipt, a `.specflow.json` written by hand, and artifact conversion and review shown, not implementation or a running runtime.

The session `conversion-calcard` gives the shipped `convert-prd` skill that `idea.md` as its source and answers its questions as the developer did. A run on a host is equivalent to the proven set when all of these hold: the same file set; the bugfix headings; the same clause numbers under each behavior section; four top-level tasks in Kiro's order; a `Sources:` line that names the processed intake item; every obligation of `idea.md` cited by a clause or by a recorded decision; and every task that is checked in the expected set checked in the run. Hashes, the `.config.kiro` UUID, timestamps, and prose are not compared. The receipt is checked by the `conversion-receipt` check of 00007, since the proven set has none. The regression for unchecked completed work cannot run on the proven set, which has no completed work; it runs on a seeded variant whose first two tasks are checked with outcomes. The developer accepted this on 2026-10-04 (ruling D9). T-081 runs after T-056, since its host runs need the runners.

### Parity gate

Before release 0.1, per source skill covered by RULE-001.6:

1. Collect the inputs: the fixture and the developer turns of each session whose evals carry the skill's rules.

2. Run the source skill (on Claude Code, where it lives) and specflow (on every supported host) on the same inputs.
3. Record, per rule, the source result and specflow's result per host in `tests/specflow/parity/<skill>.md`.
4. The skill may retire only when every rule mapped from it passes on specflow on every host. A rule the source skill fails still has to pass on specflow: the rule is the contract, not the old behavior.

The retirement PRD in `buvis/agent-skills` cites these reports (Plan A "Retirement"). create-prd and review-prd-backlog also wait for the autopilot repoint (`qa-log.md` Q2).

## Data model

The run record, `tests/specflow/evals/results/<host>/<session>/<n>.json` with `n` counting runs from 1, so a rerun never overwrites an earlier result. It is checked with `check_schema` of 00004 against `result.schema.json`:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schemaVersion` | integer | yes | `1` |
| `host` | string | yes | `kiro-ide`, `codex`, or `claude-code` |
| `hostVersion` | string | yes | the version the host reports |
| `mode` | string | yes | `automated` or `manual` |
| `session` | string | yes | the session's `name` |
| `model` | string | yes | the model the host reports |
| `instructionFiles` | array | yes | every instruction file the host loaded besides the plugin |
| `runtimeRevision` | string | yes | the git tree id of `plugins/specflow/` at the run |
| `fixtureRevision` | string | yes | the git tree id of the session's own fixture folder at the run |
| `sessionRevision` | string | yes | the git blob id of the session file at the run |
| `continuesRun` | object | no | for a `continues` session: the `host`, `session`, and `n` of the run whose finished workspace it started from; that workspace is then the baseline of `files` and `unchanged` |
| `status` | object | yes | the output of `validate_spec.py status --json` at the end of the run, or null when the helper could not run |
| `brokenAt` | integer | no | the turn at which the session went off script |
| `notRun` | string | no | the reason a run did not finish; such a record holds no scores and counts as not run |
| `notes` | string | no | free text of a manual run, such as what the host's own interface showed |
| `messages` | array | yes | one string per developer turn: the agent's final reply to it |
| `filesRead` | array | yes | one array per developer turn: the paths the agent read in it |
| `files` | array | yes | one object per file the run created or changed in the workspace, with `path` and `text` |
| `unchanged` | array | yes | workspace paths whose content equals the fixture's |
| `scores` | array | no | written by the scorer: one object per eval with `rule`, the git blob id of the eval file, `passed`, the failing assertions, and for a rubric the verdict, the judge, and the reason |

A parity report, `tests/specflow/parity/<skill>.md`: one row per rule mapped from the skill, with the source skill's result and specflow's result on each host, and the verdict ready to retire or not. specflow's results come from the stored run records. The source skill's result is a recorded judgement: the source skill is run by hand on Claude Code, where it lives, on the same input, and each rule is judged against what it produced and noted in the report; no runner plays the source skill, since the evals assert specflow's paths. The same input is the fixture and the developer turns of each session whose evals carry the skill's rules; an example of the skill's own counts once it is such a session.

## Data and control flow

Order: T-050 first, since everything else runs on its fixtures. Then the runners T-056, the handoff T-051, coexistence T-052, and the security review T-054, in any order. T-053 and T-081 are sessions and need T-056. Then T-057: every session on every host, every eval scored. Then T-055, which reads those run records, and T-058, the parity gate.

Evidence is tied to revisions. Each run record names the package and fixture revisions it ran on. When either changes afterwards, the affected sessions are run again before the release (T-064 in 00001); an unchanged result is not rerun merely to repeat a gate.

## Error handling

- A session that breaks fails every eval on it, and the result names the session, so the fix lands once.
- A host that cannot start, or a run that stops early, is recorded as not run with the reason; it is never counted as a pass.
- A rule the source skill fails still has to pass on specflow: the rule is the contract, not the old behavior.
- An eval that fails is investigated and the rule, the instruction, or the eval is corrected; a rerun is recorded as a rerun, with the earlier result kept.
- A conversion run that drops an obligation or unchecks completed work fails the comparison.

## Security and privacy

- Runs happen in scratch workspaces under the ignored `docs/dev/tmp/specflow/`, with no credential beyond the host's own sign-in, and touch no production data. The Codex runner's temporary home holds a copy of that sign-in and is removed when the batch ends.
- A run record stores the agent's messages and the files it wrote. Sessions use synthetic secrets only, and the scorer's redaction evals fail a record in which one of them was persisted.
- The calcard-mcp fixture is copied from another repository of the developer. Before it is committed, it is read for anything that must not be public here.
- The security review reads code and text and runs the repository's own tests; it executes nothing from upstream.

## Testing strategy

This spec is testing, so its own tests guard the instruments.

- T-050, `test_fixtures.py`: each fixture validates, or fails with exactly the finding it was built to show.
- T-053: the `concurrent-edit` session's eval passes on each host: a conflict is reported and the second writer's edit is intact.
- T-054: the security tests and `test_stdlib_only.py` pass.
- T-056, `tests/specflow/rules/test_score.py`, in CI, on stored run records: a passing eval and a deliberately broken eval on one record are scored correctly; a manual record goes through the scorer and back without loss; a record validates against its schema; the scorer's kinds equal the eval schema's; an unjudged rubric exits 1. The live self-check, one session on each automated runner, needs signed-in hosts, so it runs once by hand and its result goes in the task's `Outcome:` line.
- T-057: `python3 tools/specflow/check_rules.py` passes with no filter, so every behavioral rule has an eval; every eval passes on every supported host; the results are stored per host.
- T-058: each report lists every rule mapped from the skill with the source result and specflow's result per host; a skill is marked ready to retire only when every specflow result passes.
- T-081, `test_conversion_fixture.py`: the comparison passes for a faithful run and fails for a seeded obligation drop and for an unchecked completed task.

## Rollout and migration

The deterministic tests join CI when T-050 lands. Host runs do not run in CI: they need three signed-in hosts and, for Kiro IDE, the developer. They run before the release, on the candidate's package and fixtures, and their stored results are the release evidence. No personal skill is retired here; a parity report only says a skill is ready, and its owning repository does the rest.

## Risks and edge cases

- An eval passes on one run and fails on the next, since a model's output varies: impact m, likelihood m; mitigation: assertions are deterministic wherever one fits, and a rubric is marked as one; fallback: the failing run is kept and investigated, and the rule or its wording is fixed.
- Host runs cost more time than planned, with every session on three hosts and one host by hand: impact m, likelihood h; mitigation: evals are grouped onto as few sessions as stay readable, so the run count follows sessions, not rules; fallback: none that keeps the release rule, since no eval may be skipped.
- A headless host does not expose which files the agent read: impact m, likelihood m; mitigation: the runner takes `filesRead` from the host's own event output; fallback: the context-efficiency record marks that host as not measured, and the manual procedure is used for it.
- Likely next change, a fourth supported host: each host is one runner or one manual procedure; impact l, likelihood m; mitigation: the scorer and the run record are host-neutral; fallback: a recorded manual run.
- Likely next change, a second version of the run record: results are stored per host and carry `schemaVersion`; impact l, likelihood m; mitigation: the scorer rejects a version it does not know; fallback: rerun the sessions.
- Likely next change, more sessions as rules are added: nothing limits their number; impact l, likelihood h; mitigation: a new rule joins an existing session when it can; fallback: none needed.
- The temporary Codex home does not work with the developer's sign-in: impact m, likelihood m; mitigation: T-056 proves it before any Codex session is run; fallback: the developer chooses between moving the instruction file aside for a batch and recording the taint; a tainted run is release evidence only if the developer waives that rule.
- Edge case: a manual run and an automated run of the same session are scored by the same evals; `mode` only records how the run was made.

## Requirement traceability

| Design element | Criteria |
|---|---|
| Eval runners, the manual procedure, stored results per host | RULE-001.4 |
| Parity gate and its reports | RULE-001.6, REL-002.7 |
| Cross-host handoff (T-051) | REL-002.1, REL-002.3 |
| Native-Kiro coexistence (T-052): an edit to approved requirements stales design and tasks on the next validation | REL-002.2 |
| Compatibility tests and eval runs on Kiro IDE, Codex, and Claude Code | REL-002.6 |
| The handoff reads gates and the next task from the status document alone | REL-002.8 |
| Security review, context efficiency, conversion acceptance, concurrent edit | criteria of 00003, 00004, 00006, and 00007, cited across the dependency |

## Alternatives considered

1. **Checklists run by hand on every host** (smallest diff: no runner, no scorer). Rejected. RULE-001 criterion 4 wants every eval run on every host; by hand, each change to a rule would cost three full manual passes.
2. **Two runners, one scorer, and a recorded manual run for the host with no headless mode** (chosen). The added scripts buy repeatable runs on two hosts and one scoring path for all three.
3. **An eval framework.** Rejected without a registry search: it would have to drive two different host command lines and accept a hand-made record for the third, and maintainer tooling carries no dependency (`AGENTS.md`).
4. **Host runs in CI.** Rejected for the first release: they need signed-in hosts and a person for Kiro IDE; CI runs the deterministic tests, and the release reads the stored results.

## Reuse inventory

- The session and eval formats and `check_rules.py` of 00005; `check_schema` of 00004 for the run record.
- `validate_spec.py status --json` and `validate` of 00004: the handoff and coexistence assertions are comparisons of their output.
- The guard test of T-025 (00004), cited by the concurrent-edit session instead of repeated.
- The Kiro captures of 00004 (T-027), the sessions and fixtures written with each reference in 00006 and 00007, and the host records of 00008.
- The security findings and regression tests of T-076 and T-077 (00007).
- `claude -p` and `codex exec` as the two headless hosts; `sys.stdlib_module_names` for the import test.
- The calcard-mcp artifact set as it stands (task plan not approved, no receipt), as the acceptance fixture.
- Searches: nothing in `scripts`, `.github`, `plugins`, or `templates` runs a host or scores a transcript; the repository's only tests are `scripts/test_validate.py`.

## Open decisions

No decision is open. Rulings of 2026-10-04 (design gates report), taken in above: D9, the fixture is compared by structure, in its true condition, and completed work is tested on a seeded variant; D10, the developer judges each rubric assertion by hand; D11, the Codex runner uses a temporary Codex home, which T-056 proves first.

Choices the source left to the design, made above and listed for approval: the run record and its fields; one scorer for automated and manual runs; the run environment (a git repository per workspace, user-level settings left out, limits per turn and per session); one conversation per session and what makes a session broken; the three script names and their exit codes; host runs outside CI with stored results as evidence; the import test as the dependency scan; concurrent edit as a session; the source skill's parity result as a recorded judgement; and the folders for records, security tests, and results.

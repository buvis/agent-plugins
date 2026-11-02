# autopilot

**Current package: gated foundation, version 0.10.0.** No host execution, host support, certification, or publication is claimed. Every quoted block below is historical documentation from pinned source revision `e960ef1cc43e72bf92593b2f16c7a37c71ea7e48`; its commands and runtime claims are unavailable in this package. Do not execute those examples. Only the two local facade operations documented at the end are current.

<!-- Historical source body begins. -->
> 
> 
> A PRD-driven build and review pipeline for Claude Code. Hand it a spec; it plans
> the tasks, implements them one at a time, and then refuses to call the work done
> until three independent review lenses agree.
> 
> The point is the review, not the build. Anything can write code that looks right.
> This pack is built around the assumption that the code is subtly wrong until a
> reviewer who cannot see your reasoning says otherwise.
> 
<!-- Historical source body ends. -->

## What's inside

The eleven skill documents and eighteen persona references preserve source contracts as gated documentation. The historical worker, reviewer, and nine hook roles below are not agent or hook registrations; their controllers, runners, and host integrations are unavailable.

<!-- Historical source body begins. -->
> 
> 
> Eleven skills:
> 
> | Skill | Does |
> |---|---|
> | `run-autopilot` | Drives the whole lifecycle: catchup, design, plan, work, review-rework loop |
> | `design-solution` | Turns a PRD into a reviewed design doc before planning |
> | `plan-tasks` | Breaks a PRD into sequenced, session-sized tasks |
> | `work` | Executes one task at a time, dispatching an implementor and committing after each |
> | `review-work-completion` | Consensus review of finished work against the PRD |
> | `review-blindly` | Spec-only lens: never sees the diff, finds the code itself |
> | `review-plan` | Critiques a plan before implementation |
> | `fast-track` | Runs one spec card through the full review roster, skipping the loop phases |
> | `use-codex`, `use-gemini`, `use-sonnet` | Non-interactive dispatch to external model CLIs |
> 
> Eighteen agents. One implementor (`ivan`), four worker tiers (`worker-haiku`,
> `worker-sonnet`, `worker-opus`, `worker-fable`) that run an assembled persona
> at a set model and effort, and thirteen reviewers across four lenses: consensus (`alice`, `bob`, `carl`), blind (`blake`), doubt (`eve`), and
> dimensions (`rita` requirements, `cora` correctness, `grace` quality, `toby`
> tests, `mallory` security, `trent` rubric, `victor` adversarial verification,
> `pat` per-task patches).
> 
> Nine hooks. Seven keep a loop session on its contract:
> `guard_phase_delegation.py` (no phase skill handed to a subagent),
> `guard_skill_after_leave.py` (no autopilot skill after a hand-off),
> `note_session_leave.py` (records which session wrote its `leave` row),
> `guard_stop_on_live_lanes.py` (no stop while a codex or gemini lane runs),
> `autopilot_context_cap_hook.py` (hands off before the context cap),
> `review_coverage_hook.py` (no exit with an incomplete review file) and
> `validate_state_json_hook.py` (catches an unparseable `state.json` write). The
> other two are below.
> 
> `enforce_prd_location.py` keeps working documents in their
> declared homes instead of scattered through the repo. It runs on `PreToolUse`
> for `Edit`, `Write`, `MultiEdit` and `Bash`: file mode blocks a PRD written
> outside a `docs/dev/project-management/prds/` lifecycle directory, and Bash mode blocks a command
> that references a repo-root `backlog/`, `wip/`, `hold/` or `done/`.
> `guard_push_on_critical.py` runs on `PreToolUse` for `Bash` and denies a
> `git push` into a repository with pending cap_critical custody (a capped-out
> batch left an unresolved CRITICAL on master); run `autopilot custody resolve`
> first.
> 
> **If you already run this hook from your own config, disable one of them** —
> otherwise both fire and you get the same block twice.
> 
<!-- Historical source body ends. -->

## Recursion guard

The historical recursion guards and host markers below are documentation, not available runners. Recording a failed or unavailable source reviewer preserves history; it does not satisfy REQUIRED review evidence. A complete permitted replacement is required, otherwise the review must refuse acceptance. Continuing other reviews never authorizes accepting an incomplete required roster.

<!-- Historical source body begins. -->
> 
> 
> Two reviewers dispatch out to external CLIs: `bob` through `codex-run.sh` and
> `carl` through `gemini-run.sh`. Since this pack is reachable from those same
> CLIs, a lane could spawn codex inside codex.
> 
> Both runners now refuse. They exit 3 when `AUTOPILOT_DISPATCH_DEPTH` is already
> set, and again when a host marker (`CODEX_SESSION_ID`, `COPILOT_CLI`) says the
> process is already inside a CLI agent. `review-work-completion` treats a non-zero
> runner exit as a failed reviewer and continues with the rest, so the refusal
> degrades instead of halting a cycle. Markers are documented in
> `skills/use-codex/references/host-markers.md`.
> 
> **Known ceiling:** the native Gemini CLI could not be probed (it refuses to
> authenticate with `IneligibleTierError` as of 2026-08-25), so no marker is known
> for it. `gemini-run.sh` defaults to the Copilot backend, which is covered. If you
> force `GEMINI_BACKEND=gemini`, recursion through that path is bounded only by the
> depth counter, which permits exactly one nested call before refusing.
> 
<!-- Historical source body ends. -->

## Paths

Current resources stay inside this package root: `skills/`, `references/` (including `references/personas/`), `contracts/`, and `scripts/autopilot.py`. The local facade resolves packaged resources from its own location, without source-checkout or author-home fallback. The legacy substitution and helper-script rules below describe the source host only; they do not activate runtime paths.

<!-- Historical source body begins. -->
> 
> 
> Skill bodies use `${CLAUDE_PLUGIN_ROOT}`, which Claude Code substitutes when the
> skill loads. Files under `references/` are read at runtime and are **not**
> substituted — the four skills that have such references carry a note saying so
> and naming the resolved root. Scripts locate their own siblings from `$0` or
> `__file__` and never read an install path.
> 
<!-- Historical source body ends. -->

## Install

Host installation and execution are gated and unavailable. The native marketplace commands below are preserved historical examples, not installation instructions for this package. A local package copy permits only the current facade operations.

<!-- Historical source body begins. -->
> 
> 
> ```
> /plugin marketplace add buvis/claude-plugins
> /plugin install autopilot@buvis-plugins
> ```
> 
<!-- Historical source body ends. -->

## Update

Host update and version-distribution commands remain gated. The source update example below is unavailable here; replacing a local package copy does not certify a host or enable its historical controller.

<!-- Historical source body begins. -->
> 
> 
> ```
> /plugin update autopilot@buvis-plugins
> ```
> 
<!-- Historical source body ends. -->

## Alternative: install directly from this repo

Direct native installation is unavailable and gated. The source marketplace example below is historical; a local clone is not host certification or publication.

<!-- Historical source body begins. -->
> 
> 
> ```
> /plugin marketplace add buvis/claude-autopilot
> ```
> 
<!-- Historical source body ends. -->

## What intentionally stays out

All source exclusions below remain documented as historical boundaries. External controllers, wrappers, notification glue, storage workflows, Qwen routing, fan-out engines, and personal rules are unavailable. Historical fallback statements are not current execution promises or permission to load omitted files from source or home.

<!-- Historical source body begins. -->
> 
> 
> - **The `autoclaude` wrapper.** The shell front-end that relaunches headless
>   sessions across a batch lives in the author's dotfiles. A plugin cannot install
>   shell functions. Drive `/autopilot:run-autopilot` from your own automation instead.
> - **Run state.** Everything under `docs/dev/project-management/**` — `state.json`, reports,
>   transcripts — belongs to the repo being worked on, not to this pack.
> - **`notify.py`.** Desktop notification glue, host-specific, stays personal.
> - **`save-session` / `resume-session` / `restore-tasks`.** Codex storage
>   workflows with no meaningful Claude projection.
> - **The qwen lane.** `work` can route a task to a local Qwen model through
>   `use-qwen`, which is not part of this pack. Without it that route is simply
>   unavailable; nothing else changes.
> - **`review-fanout.workflow.js`.** The fan-out consensus engine is a host-local
>   workflow file, conventionally `~/.claude/workflows/review-fanout.workflow.js`.
>   It is needed only by the opt-in `workflow` and `shadow` values of a PRD's
>   `consensus_engine`. Absent, both fall back to `legacy`, which is the default
>   and needs no such file.
> - **`rules-library/rationalizations.md`.** `design-solution` reads it for the
>   synonym sets that drive its reuse sweep. Absent, the sweep runs on the model's
>   own synonyms and says so in its summary line.
> 
<!-- Historical source body ends. -->

## Development

Current repository integration validates the package and runs the maintained tests. The source release-check and publishing commands below are historical and unavailable here; they are not this package's development or release procedure.

<!-- Historical source body begins. -->
> 
> 
> ```
> bash dev/bin/release-checks     # the gate: registry + runner guards
> dev/bin/release minor           # bump, tag, stamp the central marketplace
> ```
> 
<!-- Historical source body ends. -->

## License

The package retains the MIT license. The source license statement below is preserved.

<!-- Historical source body begins. -->
> 
> 
> MIT. See [LICENSE](LICENSE).
> 
<!-- Historical source body ends. -->

### Autoclaude role effort

The source role and effort settings below are historical documentation only. They do not launch workers, select models, or authorize Fable in this gated package. Packaged policy provider profiles remain source-bound and are not rewritten to match a development host.

<!-- Historical source body begins. -->
> 
> 
> Coordinator effort defaults to `low` for build, review, and finalization.
> `_AUTOPILOT_COORDINATOR_EFFORT` overrides that default; existing phase effort
> settings override it for their phase. Invalid nonempty effort values fail before
> launch; empty values use the default. Model promotions and Fable authorization
> are unchanged. Unknown recovery phases retain Opus/xhigh.
> 
> Native worker agent definitions explicitly set Haiku/low, Sonnet/medium,
> Opus/high, and authorized Fable/xhigh. Alice and Blake use high effort. Worker
> and reviewer settings do not inherit coordinator effort. External Claude reviews
> pass `--effort high` to `sonnet-run.sh`; implementations use their tier default.
> These defaults require the updated plugin, not merely a lower launcher setting.
<!-- Historical source body ends. -->

## Current local facade

These are the original public operations; the local helper operations follow in the next section. Run them from this repository root,
or replace `plugins/autopilot` with the absolute path of your local package copy:

```sh
python3 plugins/autopilot/scripts/autopilot.py --list-capabilities
python3 plugins/autopilot/scripts/autopilot.py --export-policy
python3 plugins/autopilot/scripts/autopilot.py --export-policy --out /tmp/autopilot-policy.json
```

`--list-capabilities` lists the contract format IDs `review-policy-v1`,
`review-evidence-v1`, and `review-fixtures-v1`. These identify packaged contract
formats, not host capabilities or certification. `--export-policy` writes the
canonical packaged policy to standard output; `--out PATH` writes it to a file.
Relative output paths resolve against the caller's working directory.

The package includes the policy, evidence schema, expected-context definition,
and golden fixtures under `contracts/`. The facade reads its own packaged policy
without network access, a source checkout, author-home files, or a controller.
Skill execution remains gated: preserved source instructions and references
cannot establish runtime availability. Failed or unavailable required review
slots must receive a complete permitted replacement or cause refusal.

## Local helper operations

The facade also runs local helper operations. Pass one of the options below to
the packaged facade script, run the same way as the original operations above.
Each request file is a JSON object with `"schema_version": 1`, and each
operation prints one JSON report with `"schema_version": 1`:

```text
--stage-review REQUEST.json
--group-findings REQUEST.json
--check-evidence REQUEST.json --expected-context CONTEXT.json [--policy POLICY.json]
--prepare-close REQUEST.json
--catchup-probe --project-root PATH
--verify --project-root PATH --head-sha SHA --artifact PATH --log PATH [--timeout SECONDS] -- ARGV...
--controller-action NAME
```

`--list-capabilities` prints the three legacy IDs `review-policy-v1`,
`review-evidence-v1` and `review-fixtures-v1` first. The helper operation IDs
follow: `stage-review-v1`, `group-findings-v1`, `check-evidence-v1`,
`prepare-close-v1`, `catchup-probe-v1`, `verification-artifact-v1` and
`controller-required-v1`. A missing, unknown or higher request `schema_version`
is a usage error that exits with `2` before any effect.

`--controller-action NAME` never runs a workflow action. It prints
`{"schema_version": 1, "ok": false, "error": "controller-required", "operation": NAME}`
and exits with `3` before it reads or writes a request file. A helper step that
needs the controller returns the same `controller-required` report and exit code 3.

The helpers never run the cap or custody workflow; cap ranges, custody markers,
journals and locks stay with the controller. They do not find the project root on
their own, read or write `docs/dev/project-management/autopilot/`, move PRDs,
dispatch reviewers or start supervisors. Every artifact path is explicit, and
relative paths resolve against the explicit project root.

Review staging applies each reviewer's input manifest to the prompt and every
context file it references. `implementation-audit` grants broad context, `plan`
grants tasks and design text, `prd` grants the raw PRD, and `test-results` grants
the test gate. Pack and history inputs require their own grants. A tail sweep
may select a subset of validated findings without closing reviewer results.
Verification spawn failures return `ok: false` and `error: spawn-failed` while
preserving existing outputs. Output guards compare filesystem identity so case
aliases and hard links cannot overwrite command inputs or live state.

`tools/autopilot/source-map.json` records each helper function and regression in
`helper_dispositions`. Controller-owned functions stay controller-only, and no
existing regression owner is reassigned.

This package is not published to any marketplace. No installation is supported
yet; the historical Install and Update sections describe the source plugin.
Real-host evidence is unavailable: the helpers are tested in a sandbox only, and
no host profile is certified.

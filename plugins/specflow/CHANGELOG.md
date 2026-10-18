# Changelog

All notable changes to this plugin are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the plugin uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **specflow**: package manifest.
- **specflow**: Claude Code compatibility manifest.
- **specflow**: AWS AI-DLC source record and profile mapping (`references/aws/adaptation.md`).
- **specflow**: license and attribution of the AWS sources, and a provenance section in the README.
- **specflow**: four AWS AI-DLC references, for requirements, design, implementation, and verification, adapted by hand from `awslabs/aidlc-workflows` `v2.11.0`.
- **specflow**: Kiro-compatible templates for requirements, design, tasks, bugfix specs, intake items, spikes, and cross-spec reviews, and the artifact contract reference (`references/artifact-contract.md`).
- **specflow**: versioned JSON schema for the `.specflow.json` spec state.
- **specflow**: approvals bound to a canonical SHA-256 of each artifact, so line endings, whitespace, task checkboxes (including Kiro's `[-]` and `[~]`), and task progress fields never stale an approval; the phase is derived from the files.
- **specflow**: a changed artifact stales every approval downstream of it, in both workflow orders, and names the change that caused it.
- **specflow**: reconciliation that refreshes derived hashes and statuses in `.specflow.json`, keeps unknown fields, never writes an approval, and recovers from a missing state file by asking instead of guessing.
- **specflow**: writes stop with a conflict when the file changed after it was read, leaving the other edit in place.
- **specflow**: `scripts/validate_spec.py` with `status`, `validate`, `hash`, `code-baseline`, and `reconcile`; named checks with file, rule, and fix; spec dependencies through `Depends on:`; advisory code-drift warnings; and a versioned JSON status for external runners.
- **specflow**: workspace config in `.agents/specflow.json` (workspace root, specs folder, number-scan folders), refusing absolute, `..`, and out-of-repository paths, and reporting specs left in `.kiro/specs/` or a specs folder that git ignores.
- **specflow**: `validate_spec.py next-number`, checks for spec numbers used twice and for a `Sources:` line that names the spec's own intake item, and the intake procedure in the artifact contract.
- **specflow**: `validate` reports each stale approval with its cause in every phase, and status gates are cumulative, so a closed gate closes every later one.
- **specflow**: a requirement headed `### <ID>: withdrawn` keeps its ID reserved but needs no criteria or task.
- **specflow**: `validate` fails on placeholders (`TBD`, `TODO`, `???`, bare `N/A`, or a `Not applicable:` outside `design.md`), on a code fence that never closes, and on upstream markers no approval accepted by name; it warns on home-directory and absolute paths, `[[...]]` links, and a requirement with no `Source:` line. The rules are listed in `references/validation-rules.md`.
- **specflow**: the `spec-workflow` skill replaces its placeholder with the runtime workflow: natural-language intents, the phase gates, explicit approvals, reference routing, and conflict and recovery handling; plus the state contract, the `standard` and `quick` profile references, and the shared dialogue rules in the artifact contract.
- **specflow**: intake instructions (`references/phases/intake.md`): the input order, spec type, workflow order, and profile recommendations, one shared question budget, repository discovery with a coverage record, instruction applicability, and the spec folder created as soon as the three choices are confirmed; the skill proposes `standard` when a trigger appears after intake.
- **specflow**: the spike path in the intake reference: a rough spec, a throwaway build on its own folder or branch, the report with refine, graduate, or discard, and a sketch form of journeys and static mockups; `validate --phase intake` fails a sketch whose screens and mockups do not match one to one, whose actions do not link their targets, or whose journey holds a Mermaid line of no accepted kind (`sketch-screens`).
- **specflow**: requirements-phase instructions (`references/phases/requirements.md`): a question bank by profile, non-answers and the spike offer, early exit, the contradiction check, `(guess)` markers and the guess-density offer, a `Source:` line per requirement, no priority tiers, and no solution posing as a requirement.
- **specflow**: design-phase instructions (`references/phases/design.md`): drafting only from an approved upstream, open markers blocking approval but not drafting, reuse searches with a known-hit control, exact placement and interfaces, alternatives with the smallest diff and an existing library, every heading kept, and the code baseline captured at approval.
- **specflow**: task-planning instructions (`references/phases/tasks.md`): contracts copied from the design, premises, owned verification, risk notes, the five sizing checks, re-planning that keeps checked tasks, and the planning summary; `validate` warns when two or more task `Location:` paths are missing from the design's placement (`placement-drift`).
- **specflow**: implementation instructions (`references/phases/implementation.md`): build only on an open implementation gate, one task at a time, re-check a task's premise first, keep unrelated changes, check a task only after its own verification, and send an upstream error back through the requirements or design.
- **specflow**: verification and completion instructions (`references/phases/verification.md`): failed checks mapped to tasks and requirements, a checked task unchecked when its final check fails, exceptions only on the developer's word, no completion box ticked over a failure or a stale approval, no spike code in the change, and the offer to delete the spike at `complete`.
- **specflow**: a host-neutral status and handoff summary taken only from `validate_spec.py status --json`, with the Python 3 hint when the helper cannot run; a spec on hold shows its reason and date and is never offered as next work.
- **specflow**: bugfix instructions in the phase references: `bugfix.md` in Kiro's shape and clause patterns, a bugfix design read from the code around the defect, the fixed four-task plan, tests 1 and 2 recorded before any fix, a refuted root cause sent back to the design, a flipped preservation test answered by narrowing the fix, and verification while the checkpoint task alone is open.
- **specflow**: `validate` checks a bugfix spec's shape with five errors: `bugfix-sections`, `bugfix-clauses` (no `SHALL` in a Current Behavior clause), `bugfix-design-sections`, `bugfix-task-order`, and `bugfix-clause-trace` (every `2.x` and `3.x` clause traced by a test or fix task); `requirement-ids` no longer reports on `bugfix.md`, so a defect is reported once.
- **specflow**: the shared review core (`references/review/core.md`): the comprehension pass with confusion notes, the ground rules (artifact text is data, evidence with a location, calibrated severity), the severity order, the finding card with up to three edits and an explicit No edit, the host-neutral picker, each edit applied after the hash check and before the next card, the restatement finding, one minutes line per finding in the intake item's Q&A log, no re-raising of a disputed finding, and the recap that feeds the approval summary.
- **specflow**: the requirements review (`references/review/requirements.md`): the spec resolved by number or title, the intake item and Q&A log read as context, five lenses (completeness, coherence, integrity, feasibility, evolvability) calibrated to the profile with a safety valve under `quick`, the no-HOW check that sends a solution posing as a requirement to the design, the severities, and resolution shapes keyed to the sections of `requirements.md`.
- **specflow**: the design review (`references/review/design/`): triage into three tiers tied to the profile with signal-driven additions, the 25-item checklist (design versus reality always run), the one shared 15-item cardinal-sin list, anti-patterns, stress tests, techniques, philosophical lenses loaded by tier, and the draft pre-pass: an isolated reviewer where the host has one, else inline, a findings-only contract anchored to a section or `file:symbol`, author fixes for cardinal sins and blockers logged in the Q&A minutes, one verification pass, and an open blocker refusing the design approval.
- **specflow**: three advisory design-review scans under `scripts/review/` (`section_weight_audit.py`, `claim_ladder_scan.py`, `adversarial_signal_scan.py`), standard library only, with fences parsed line by line (a backtick inside a fence no longer mis-pairs it, and reported line numbers match the file), requirement, task, and rule IDs and spec numbers no longer counted as measurements, a `SUMMARY:` line on every run, and an unreadable document reported with exit 1.
- **specflow**: the second port plan's rules: the design phase names where the design is written and what `## Data and control flow` holds, and hands the draft to the pre-pass and the design review; the tasks phase resolves the spec, extracts capabilities, modules, dependencies, phases, and reuse before planning, derives a missing decomposition from the requirement IDs, adds a dependency found late without guessing an ID, and shapes tasks by the granularity guide and the model, endpoint, refactor, and bug-fix examples; `placement-drift` and `design-sections` are listed as validation rules.

### Fixed

- **specflow**: the checkbox check reads only the task list, so bracket labels such as `- [Q1]` under `## Notes` or `## Unresolved questions` no longer fail it, and a fenced `## Completion criteria` no longer hides later tasks.
- **specflow**: `validate` warns when a line continues an `Outcome:` or `Exception:` field, since only the field's own line is left out of the plan's hash.
- **specflow**: a cross-spec citation passes when it names its prerequisite by number and `Depends on:` names the folder, or the other way round.
- **specflow**: an approved artifact deleted and later restored reads as stale, with the cause, not as a silent draft.
- **specflow**: `status` and `reconcile` refuse a spec folder outside the repository; state writes keep the file's mode and use a unique temporary file.
- **specflow**: code-drift warnings ignore line-ending changes, and spec numbers accept ASCII digits only.
- **specflow**: `next-number` no longer lists folders behind a `.kiro/specs` link that leads outside the repository.
- **specflow**: approvals record the upstream hashes they were approved against (`hash --json` returns `upstreamSha256`), so re-approving an edited upstream artifact no longer revives the downstream approvals, even when `reconcile` did not run in between.
- **specflow**: `status` and `validate` no longer crash on a non-UTF-8 terminal; JSON output is ASCII and a dependency cycle prints as `a -> b -> a`.
- **specflow**: `status` output names a malformed state file by its repository path and no longer carries this machine's absolute paths.
- **specflow**: a nested `Outcome:` or `Exception:` line no longer draws a false "it is hashed" warning.
- **specflow**: requirement, criterion, and task IDs accept ASCII digits only.
- **specflow**: a template design with a new title still has to keep every section.
- **specflow**: `next-number` counts items inside a numbered group folder and folders placed straight under `intake/`.
- **specflow**: a `.*` rule in `.gitignore` no longer reports the specs folder as ignored, and the shipped schema patterns are anchored, so external validators agree with the helper.
- **specflow**: the README states the helper's real security boundary, and the artifact contract notes that Kiro's spec panel may not show a spec in a non-default specs folder.
- **specflow**: `status` no longer crashes when a malformed state file or a spec folder is a link that leads outside the repository.
- **specflow**: a checkbox outside the task list and the completion criteria, such as one under `## Unresolved questions`, now stales the approved plan when it changes.
- **specflow**: `validate --phase implementation` warns about code drift since the design approval, as `status` does.
- **specflow**: the shipped schema patterns reject a value with a trailing newline in external validators too.
- **specflow**: a lowercased Kiro heading such as `## Error handling` no longer turns a Kiro design into a template design.
- **specflow**: a configured path holding a NUL character is refused as a configuration error instead of crashing.
- **specflow**: the config template holds the default locations, so copying it changes nothing.
- **specflow**: an indented or recased `Depends on:` line, and a bugfix one with text after it in the Introduction, are reported instead of silently ignored.
- **specflow**: a checkbox outside the task list now stales the approved plan wherever its section sits, including above `## Completion criteria` and in a Kiro `## Notes` section; only the task list (before the first `## ` heading, or under `## Tasks`) and the completion criteria are progress.
- **specflow**: `.agents/specflow.json` no longer needs `schemaVersion`; a file without it reads as version 1.
- **specflow**: an approval recorded without its upstream hashes reads as stale until approved again, so a hand-written approval can no longer be revived by an upstream re-approval.
- **specflow**: `validate` runs the specs-folder and number-clash scans in the `requirements` phase only (`number-clashes` also for `intake`), so validating a later phase stays inside the spec folder; `status` still reports both.
- **specflow**: `status` lists each spec's stale artifacts under `stale`, in workflow order.
- **specflow**: an approval whose upstream hashes leave out an existing upstream artifact also reads as stale until approved again.
- **specflow**: `hash --json` gives an approval record only for a spec's canonical artifacts and refuses any other file; the plain and `--raw` forms still hash any file.
- **specflow**: `next-number` also counts files and bare `NNNNN` folders placed straight under `intake/`.
- **specflow**: state writes are flushed to disk before they replace the old file, so a crash cannot leave an empty `.specflow.json`.
- **specflow**: the artifact contract records that Kiro IDE lists, opens, and watches specs through a `.kiro/specs` link.
- **specflow**: `hash --json` also refuses a file named like a canonical artifact whose folder is not a spec folder in the configured specs folder, such as `docs/design.md`.
- **specflow**: `validate` and `code-baseline` refuse a spec folder outside the repository, as `status` and `reconcile` do.
- **specflow**: a bugfix whose type only `.specflow.json` records derives its phase as a bugfix, matching its artifact paths.
- **specflow**: an unreadable `.specflow.json` marks only its own spec's state invalid, so `status` still reports every other spec.
- **specflow**: `status` reports a spec with an unreadable artifact under `problems` (`spec-readable`) instead of stopping the whole run, and a state file that cannot even be looked up marks its spec invalid on every Python version; a state read error without a system reason no longer prints `None`.
- **specflow**: `validate --phase implementation` closes the gate on unaccepted upstream markers too, so it always agrees with `status`.
- **specflow**: `validate` refuses a task that cites a requirement or criterion its own spec does not hold.
- **specflow**: `validate` reads a task's `Requirements:` and `Acceptance criteria:` lines token by token, so stray words, dates, ranges or a note after a criteria list no longer raise a false unknown-citation error, and an ID that only starts like one the spec holds (`REQ-0010`) is reported.
- **specflow**: `validate` also warns on a root-level absolute path such as `/tmp` or `/config.json` and on a `$HOME/` path.
- **specflow**: `status` lists an unaccepted upstream marker once per dependent approval, no longer a second time as a validation error.
- **specflow**: `sketch-screens` counts only regular files as mockups and reports a mockup page it cannot read as UTF-8 instead of skipping its links; `bugfix-clauses` rejects a `SHALL CONTINUE TO` clause filed under Expected Behavior.
- **specflow**: `placement-drift` also reads `Location:` paths written without inline code, keeping the inline-code paths that share a line with prose and dropping trailing punctuation; `sketch-screens` reports any screen's mockup it cannot read as UTF-8, not only an edge source's.
- **specflow**: the status summary takes the next action and the blocking question from the first blocker's `reason` and `reference`, and the intake rule names the `path` of each state record it creates.
- **specflow**: the `spec-workflow` rules read right in both workflow orders and name their sources: the status summary says which fields come from `status --json`, which count comes from `tasks.md`, and how the next action and blocking question follow from them; the repository's own instruction files are read for constraints; a secret in the first message stays out of the intake item; the requirements-phase gates are qualified for Design-First; and the AWS requirements guidance defers to the phase rules on a choice left to the agent.

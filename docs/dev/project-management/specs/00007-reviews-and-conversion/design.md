# Design: specflow reviews and conversion

## Overview

This spec adds the two things a developer does around the main workflow. Reviews: a requirements review, a design review with an adversarial pre-pass, and a cross-spec readiness review, all walked one finding at a time, with three advisory scans and a link checker. Conversion: a second shipped skill that adopts an existing PRD or legacy intake item into specflow's artifacts and gates. It also completes the rule integration of the second port plan.

## Context and constraints

- Depends on 00004 (the Q&A log, the hash check before a write, the helper's `status` and `validate`), 00005 (the rule inventory and its checker, the eval formats), and 00006 (the skill, the shared dialogue section, the phase references this spec extends).
- The review rules are ported from three personal skills, through their Plan A rows; the scripts to port are in `buvis/agent-skills`, outside this repository: `review-design-doc/scripts/section_weight_audit.py`, `claim_ladder_scan.py`, `adversarial_signal_scan.py`, and `review-prd-backlog/scripts/check_links.py` with its `test_check_links.py`.
- The conversion skill is adapted by hand from the reference skill `graduate/` in intake item 00001 (`SKILL.md` and `references/conversion.md`), which performed one real conversion with no runtime installed. The shipped skill requires the installed runtime; the reference's manual mode is not carried over.
- Everything shipped stays inside `plugins/specflow/skills/`; tests of the ported scripts live under `tests/specflow/`, since the release check of 00002 forbids test files inside the package.
- The reference conversion at `buvis/calcard-mcp` stands as follows on 2026-10-04, as the pre-pass reviewer read it: requirements and design approved, the task plan drafted and not approved, no completed work, no receipt, a hand-written `.specflow.json`, and both folders untracked. The paragraph Proof and verification below states that condition (ruling D9 of 2026-10-04); the source called it an approved artifact set.
- The decision to ship the conversion skill is decision 2026-10-04 #11 in `meta/decisions.md`; every CNV rule cites it as its source.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

## Architecture

```text
plugins/specflow/skills/
├── spec-workflow/
│   ├── SKILL.md                      # Gains the `review specs` intent
│   ├── references/review/            # Review intents
│   │   ├── core.md                   # Shared walkthrough and ground rules (area RVC)
│   │   ├── requirements.md           # Area RVR
│   │   ├── design/                   # Loaded by tier (area RVD)
│   │   │   ├── triage.md
│   │   │   ├── checklist.md
│   │   │   ├── cardinal-sins.md
│   │   │   ├── pre-pass.md
│   │   │   ├── techniques.md
│   │   │   ├── lenses.md
│   │   │   ├── anti-patterns.md
│   │   │   └── stress-tests.md
│   │   └── cross-spec.md             # Area RVX
│   └── scripts/
│       ├── check_links.py            # Cross-spec citation check
│       └── review/                   # Advisory design-review scans
│           ├── section_weight_audit.py
│           ├── claim_ladder_scan.py
│           └── adversarial_signal_scan.py
└── convert-prd/                      # Conversion skill (area CNV)
    ├── SKILL.md                      # Activation, discovery, conversion workflow, handoff
    └── references/
        └── conversion.md             # PRD-to-specflow conversion contract
```

Every review loads `review/core.md` and then only its own file, and a design review only its tier's files. The conversion skill carries its own contract and routes everything else to the workflow skill of the same package, by the relative path `../spec-workflow/`; it restates none of the artifact, state, review, approval, or validation contracts.

## Module placement

Shipped paths are under `plugins/specflow/skills/`. Each task also writes its eval records and adds its area to the CI step of 00005, except T-075, whose area joins with T-077. The checker of 00005 already resolves `convert-prd/` paths and reads the area from the rule ID, so T-080 edits no checker code.

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `spec-workflow/references/review/core.md` | new | T-073 | the walkthrough and ground rules (area `RVC`) |
| `spec-workflow/references/review/requirements.md` | new | T-074 | five lenses, profile calibration, the no-HOW check (area `RVR`) |
| `spec-workflow/references/review/design/triage.md`, `checklist.md`, `cardinal-sins.md`, `techniques.md`, `lenses.md`, `anti-patterns.md`, `stress-tests.md` | new | T-075 | the design review by tier (area `RVD`) |
| `spec-workflow/scripts/review/section_weight_audit.py`, `claim_ladder_scan.py`, `adversarial_signal_scan.py` | new | T-077 | the three ported scans |
| `tests/specflow/review/test_section_weight_audit.py`, `test_claim_ladder_scan.py`, `test_adversarial_signal_scan.py` | new | T-077 | their tests, including one regression test per security finding |
| `tools/specflow/rules/inventory.json` | edit | T-079 | the 65 approved Plan B rows |
| `spec-workflow/references/phases/design.md`, `spec-workflow/references/phases/tasks.md`, `spec-workflow/references/review/design/`, `spec-workflow/references/artifact-contract.md` | edit | T-079 | the Plan B rules, each tagged once |
| `spec-workflow/SKILL.md` | edit | T-076 | the `review specs` intent |
| `spec-workflow/references/review/cross-spec.md` | new | T-076 | the cross-spec readiness review (area `RVX`) |
| `spec-workflow/scripts/check_links.py` | new | T-076 | the ported link checker |
| `tests/specflow/review/test_check_links.py`, `tests/specflow/fixtures/cross-spec/` | new | T-076 | its tests and the fixture specs |
| `convert-prd/SKILL.md`, `convert-prd/references/conversion.md` | new | T-080 | the conversion skill and its contract (area `CNV`) |
| `spec-workflow/scripts/specflow_helper/checks.py`, `tests/specflow/contract/test_checks.py` | edit | T-079 | a named check for each structural Plan B rule that has none yet |
| `spec-workflow/references/review/design/pre-pass.md` | new | T-075 | the draft pre-pass (ART-003 criteria 9 to 11), loaded at every tier |
| `tools/specflow/rules/inventory.json` | edit | T-080 | the CNV rules, each with the source `D:2026-10-04#11` |
| `tests/specflow/release/test_boundary.py` | edit | T-080 | `convert-prd/` ships, and no CNV rule names a maintainer-only path; this is the test file of 00002 that reads the tracked tree |
| `tests/specflow/evals/sessions/<name>.json`, `tests/specflow/fixtures/sessions/<name>/` | new | each task | the sessions its eval records are scored on |
| `spec-workflow/scripts/specflow_helper/checks.py`, `tests/specflow/contract/test_checks.py` | edit | T-080 | the `conversion-receipt` check |
| `.github/workflows/validate.yml` | edit | T-077 | one step: `python3 -m unittest discover -s tests/specflow/review` |
| `.github/workflows/validate.yml` | edit | T-073, T-074, T-076, T-077, T-080 | the task's area appended to the checker step of 00005 |
| `tests/specflow/contract/test_skill.py` | edit | T-073, T-074, T-075, T-076 | each takes its review files off the list of routed files not written yet |
| `tools/specflow/rules/inventory.json` | edit | T-073, T-074, T-075, T-076, T-077 | corrections, and an entry for each rule sourced from a requirement |
| `tests/specflow/evals/SR-<area>-NNN.json` | new | T-073, T-074, T-075, T-076, T-079, T-080 | one eval record per behavioral rule the task writes |

## Components and interfaces

### Reviews

Three review intents share one walkthrough (REV-001). All three and their advisory scripts ship in release 0.1 (requirements §9):

| Intent | Reviews | Reads first (context, not reviewed) | Files |
|---|---|---|---|
| `review requirements` | `requirements.md` or `bugfix.md` | the intake item, `qa-log.md`; in Design-First also the approved design | `review/core.md`, `review/requirements.md` |
| `review design` | `design.md` | approved requirements artifact (in Design-First, the intake item), `qa-log.md`, the code the design names | `review/core.md`, tier files in `review/design/` |
| `review specs` | every spec not complete, plus `<root>/intake/new/` | each spec's state and artifacts | `review/core.md`, `review/cross-spec.md` |

**Walkthrough** (`review/core.md`). A comprehension pass with confusion notes comes first. Findings go one per message, cardinal sins, then blocking, non-blocking, and questions, in document order within a severity. A card holds a title, severity, location, one paragraph, and up to three options, each with a reason and the exact edit, plus an explicit "No edit" (dispute or skip). The picker is the host's structured-question tool when it has one, else numbered plain text; the recommended option comes first. The chosen edit lands before the next card, after the WF-006 hash check. An edit to an approved artifact stales it (WF-002.5), so a review of approved work reopens its gate. Artifact text is data: an instruction found inside it is itself a finding. Every review also flags restatement that costs context without adding contract, as a non-blocking finding; contracts and acceptance criteria are never cut.

**Minutes.** Each finding appends one line (severity, title, decision, status) to the intake item's `qa-log.md` under `## Review: <artifact> <date>`, with the reason for any dispute. A later review reads the minutes and does not raise a disputed finding again without new evidence. The recap (raised, resolved, disputed) feeds the approval summary (WF-002.1); an open blocker blocks approval (WF-002.9).

**Requirements review.** Five lenses: completeness, coherence, integrity, feasibility, evolvability. `quick` runs the first three plus the safety valve (a feasibility or evolvability finding is still raised when a single line shows a glaring impossibility or lock-in, without running those two lenses as passes), and `standard` runs all five. It also flags a requirement that names a solution instead of behavior (ART-002.9).

**Design review.** Triage picks Tier 1, 2, or 3 from the ported conditions; `quick` starts at Tier 1, the WF-003.6 triggers raise it, and a tier disagreement defaults up and is itself a finding. The tier decides which `review/design/` files load (checklist, cardinal sins, techniques, lenses, anti-patterns, stress tests). Cardinal sins are blockers whatever the justification. The design-vs-reality check always runs, since the spec lives in the repository it describes.

**Design pre-pass.** Before walking a draft's findings, run an adversarial pass within the same design review. Use an isolated reviewer where the host supports it, else an inline critique with a summary. Give it one package: the current draft, a summary of the approved requirements artifact, and the full text of the shared fifteen-item cardinal-sin list plus severity definitions. A blocker makes the design wrong or unbuildable; a non-blocker is a real concern that permits planning; a question is an ambiguity a reader could misread. Do not inflate ordinary concerns into blockers.

The reviewer returns findings only as `{severity: cardinal-sin|blocker|non-blocker|question, title, evidence, suggested_fix}`, anchored to a design section or `file:symbol`. The author applies cardinal-sin/blocker fixes under the normal hash check and records each fix in Q&A minutes. If it made such fixes, run one verification pass on the updated draft. Open blockers go to the developer and block approval; do not spin an autonomous loop. Remaining concerns and questions enter the interactive walkthrough, where each chosen edit lands before the next card. The recap gives pass count, findings by severity, applied fixes, open blockers, and unresolved concerns. It records no approval itself.

This is one design review with a pre-pass, not a second review or a separate design log. Cross-model review is optional through host capabilities; no named model, external CLI, pinned dispatch token, minimum finding count, or runner exit code is required.

**Cross-spec review.** Lenses A-H: hygiene, verifiability, traceability, grounding, cross-spec conflicts, sizing, gaps, and goal alignment. Grounding runs one spec per isolated sub-task where the host has them, else one spec at a time with a summary per spec. Sizing judges each spec's cost against three artifacts and three gates (too small: prefer `quick` or a merge; too big: split into new specs), and task size follows the concrete checks in §6.4: one outcome, bounded file slice, exact contracts, listed dependencies, and independent verification. It flags bundled outcomes, a needed edit outside the slice/dependencies, and a split that depends on an unfinished sibling, citing the task and failing check. The report goes to `<root>/reviews/YYYY-MM-DD-cross-spec-review.md` (verdict, map, findings, reshapes, gaps, end state, decisions applied) with GO or NO-GO and a verdict per spec; "report only" skips the walkthrough. A merge or split needs developer approval, creates new spec numbers with their own intake items (§6.7), and never touches a spec in implementation or complete.

**Scripts.** `scripts/review/*.py` and `scripts/check_links.py` are advisory, stdlib-only, and optional; a host with no command runtime skips them and says so. The port fixes three known defects: fences are parsed line by line (the regex stripped nothing when a fence held a backtick), ID tokens such as `REQ-001`, `T-003`, `SR-REQ-007`, and spec numbers no longer count as measurements in the claim-ladder scan, and docstrings name plugin-relative paths. `check_links.py` resolves five-digit citations against `.kiro/specs/` and `<root>/intake/`, never resolves home or absolute paths, and warns on them and on `[[...]]` links. Tests use `unittest` with local fixtures.

### Ported scripts

All four are advisory, use the standard library only, and keep the command lines of their sources:

```text
python3 scripts/review/section_weight_audit.py <path/to/doc.md>
python3 scripts/review/claim_ladder_scan.py <path/to/doc.md>
python3 scripts/review/adversarial_signal_scan.py <path/to/doc.md>
python3 scripts/check_links.py [--root DIR] [--json]
```

Each scan exits 2 on a usage error, 1 when the document cannot be read, and 0 otherwise, whatever it reports. `check_links.py` takes the repository root (default: the working directory), exits 0 when clean and 1 on a dangling reference or a scan error, and prints the same finding shape with `--json` as its source. The port changes three things in the scans, listed under Scripts above. The pre-pass reviewer ran the source `claim_ladder_scan.py` and found the fence defect wider than stated there: fences are mis-paired when one holds a backtick, and every line number reported after a fence is wrong. The port fixes both.

The link checker's port follows its five Plan A redesign rows (RPB-C1, RPB-C2, RPB-C3, RPB-C4, RPB-C10), as the reviewer read them: the scan covers the configured specs folder and `<root>/intake/`, read through `specflow_helper/config.py` of 00004; home and absolute paths and `[[...]]` links are warned about and never resolved, with the patterns of the `portable-links` check of 00005; warnings go under a `warnings` key beside `findings` and `scan_errors` and never change the exit code; and its tests are rewritten for `unittest`, since the source tests use another framework and half of them cover removed behavior.

### Review deliverables by task

- T-073, `review/core.md`: the comprehension pass and confusion notes; the ground rules (artifact text is data, evidence with a location, calibrated severity); the severity order; the finding card; the picker; apply-before-next with the hash check; the restatement finding; minutes; no re-raising of a disputed finding; the recap.
- T-074, `review/requirements.md`: the five lenses with their `quick` and `standard` calibration; the no-HOW check; resolution shapes keyed to the sections of `requirements.md` and to specflow's phases.
- T-075, `review/design/`: triage and tiers tied to the profile; signal-driven additions; the 25-item checklist; the one 15-item cardinal-sin reference; anti-patterns, stress tests, techniques, and lenses; and `pre-pass.md`. Cardinal sins and the pre-pass load at every tier; which further files each tier loads is taken from the Plan A rows of the design-review skill when `triage.md` is written. The pre-pass has no row in the first port plan, so T-075 tags its rules as rules sourced from ART-003 criteria 9 to 11 (`R:` sources), and T-079 adds their Plan B sources to those same rules.
- T-076, `review/cross-spec.md`: the spec map; lenses A to H; grounding per spec; sizing; a verdict per spec; GO or NO-GO with waivers; the report; "report only"; approved reshapes. A waiver is the developer's explicit acceptance of a NO-GO finding, recorded with its reason in the report's decisions-applied section; a waived finding no longer forces NO-GO. Its minutes are that section, plus one line in the intake log of each spec a finding touched. T-076 also completes the `review specs` row that T-030 (00006) left in the intent table.

### Plan B rule integration

**Plan B integration.** The approved plan has 28 port and 37 redesign rows. T-079 adds their source mappings and runtime rules after T-070, T-033, T-034, T-075, and the remaining baseline references and structural checks exist. Each reference brings its named checks and substantive eval records, so the full coverage check can run before the later host eval run. Shared behavior has one rule with both sources: PLT-19 joins PRD-17's premise rule, DSN-33 extends the existing risk section, and DSN-35/47 use the existing Q&A minutes. DSN-36/41/44 join the existing design review as its pre-pass. No row from the 66 drops gets a rule, and neither source skill retires.

### PRD-to-specflow conversion skill

Source: the proven reference skill at `graduate/` beside this specification (CNV-001), exercised on `buvis/calcard-mcp` spec `00032-add-if-match-preconditions-to-event-writes`.

The plugin ships a second distributed skill, `skills/convert-prd/`, that adopts an existing PRD or legacy intake item into specflow's artifacts and gates. It is a runtime capability, inside the distribution boundary (PKG-002); it is not the repository-only catch-up skill (§11) and carries no maintainer tooling.

**Not the spike graduate step.** "Graduate" in §6.8 is the spike path's third choice: it carries a prototype's *observed* behavior into a fresh requirements phase. Conversion instead takes an *authored* PRD or legacy intake item as its source and reconstructs the full artifact set from it. The two share nothing but a loose verb; the shipped skill is named `convert-prd` to keep them apart, while the reference folder keeps its original name, `graduate/`.

**Reference skill, adapted not copied.** `graduate/SKILL.md` and `graduate/references/conversion.md` were written by another agent that performed a real conversion and are a validated starting point, not a drop-in. They predate this spec's skill naming, the rule inventory (§5.4, RULE-001), and the reference-routing conventions (§5.2), so their text is adapted by hand into `convert-prd/`: the conversion contract moves to `references/conversion.md`, its obligations become behavior rules tagged under a `CNV` area in the inventory, and its wording aligns with the shipped artifact, state, and review contracts rather than restating them. No passage is shipped byte for byte without that pass.

**Workflow.** The conversion skill reads the source and repository context, separates source assertions from observed code and recorded history, and decides whether this is completed-work adoption or new work. It preserves the source verbatim as `idea.md`, keeps the original number and native artifact shape, and records provenance with a `Sources:` line (§6.6, §6.7); the intake item moves to `processed/` only when requirements are first written. From there it routes through the same create/continue path as a native spec: requirements, design, and tasks are drafted, reviewed (§5.5), and approved through the normative gates (§5.1, §6.2–§6.6), using the installed runtime's schema, hashing, and status derivation (§7). It never improvises a validator or claims an approval the runtime did not record. Conversion authorizes artifact drafting and reversible organization only: it does not start implementation, install plugins, commit, push, or edit another project's specs. It recovers approvals only from explicit developer evidence, keeps implementation-completion and workflow-approval state as separate facts for an already-built PRD, stops at the first ambiguous gate, and ends with a durable conversion receipt (CNV-001.9).

**Proof and verification.** The reference conversion produced an artifact set (`bugfix.md`, `design.md`, `tasks.md`, `.config.kiro`, and `.specflow.json`) at `buvis/calcard-mcp` `docs/dev/project-management/specs/00032-add-if-match-preconditions-to-event-writes/`. As read on 2026-10-04, its requirements and design are approved, its task plan is drafted and not approved, it has no receipt and no completed work, its `.specflow.json` was written by hand, and its folders are untracked. That spec is the conversion skill's acceptance fixture: the shipped skill, run on the same calcard-mcp PRD, must reproduce an equivalent artifact set, compared by structure, and must produce a receipt, which the fixture lacks (verified in tasks; see T-081 in 00009). The trial demonstrated artifact conversion and review, not executed implementation or a running specflow runtime, so those remain distinct outcomes.

### Conversion skill contract

- `convert-prd/SKILL.md` frontmatter: `name: convert-prd`, and a description that names the triggers "convert PRD", "adopt PRD", and "graduate PRD" and says it needs a resolved source document or repository context.
- Its body gives the six steps of the reference skill: discover, preserve, requirements, design, tasks, handoff. The first two are its own. From the requirements step on it loads `../spec-workflow/SKILL.md` and follows that skill's create and continue path, with every path resolved from the workflow skill's folder, so the gates, the state machine, and the reference routing are the workflow skill's and are not repeated. The trigger phrases belong to `convert-prd`; the `convert` row of the workflow skill's intent table sends the agent to it.
- `convert-prd/references/conversion.md` holds the conversion contract as rules tagged `[SR-CNV-NNN]`: scope and authority, layout and provenance, completed-work adoption, unimplemented conversion, state and evidence, and the receipt. Three rules the reference had and CNV-001 requires are kept by name: every mandatory source obligation is mapped to a destination clause or to a change the developer approved, with optional items resolved one by one (criterion 5); an approval recovered from developer evidence is dated when it is received, and no earlier time is invented (criterion 8); and a preserved native shape that fails a runtime check is reported and stops at that gate, never reshaped to pass.
- The receipt and the obligation map are blocks in the intake item's `qa-log.md`. The log is append-only, so each stop writes a new receipt and the last one counts:

```markdown
## Obligation map <date>
- <source obligation> -> <destination clause, or the approved change>

## Conversion receipt <date>
- Source: <repository-relative path>
- Destination: <spec folder>
- Number, type, folders: <...>
- Obligation coverage: <mapped of total; open ones named>
- Decisions and public-behavior changes: <...>
- Implementation evidence: <...>
- Gates: requirements <state>; design <state>; tasks <state>
- Review outcomes: <...>
- Checks run and limits: <...>
- Outstanding questions: <...>
- Next action: <...>
- Verdict: COMPLETE | AWAITING_DECISION | INCOMPLETE
```

- One structural check joins `CHECKS` of 00004: `conversion-receipt`. It finds the intake log through the spec's `Sources:` line, reads the last `## Conversion receipt` block, and reports an error when a label above is missing or the verdict is not one of the three. A spec with no such block was not converted and gets no finding. The other CNV rules are behavioral and get one eval each.

## Data model

This spec adds two blocks to the Q&A log of 00004, the obligation map and the conversion receipt, shown under Components and interfaces. Everything else it writes goes into shapes that exist:

- Review minutes: one line per finding (severity, title, decision, status) under `## Review: <artifact> <date>` in the intake item's `qa-log.md`, the format 00004 defines.
- A pre-pass finding: `{severity: cardinal-sin|blocker|non-blocker|question, title, evidence, suggested_fix}`, anchored to a design section or `file:symbol`.
- The cross-spec report: `<root>/reviews/YYYY-MM-DD-cross-spec-review.md`, from the template `templates/cross-spec-review.md` of 00004, with a verdict, the spec map, findings, reshapes, gaps, the end state, and the decisions applied.
- The conversion receipt, described above.

## Data and control flow

A review, in order: load `review/core.md` and the review's own file; read the context without reviewing it; comprehension pass with confusion notes; for a design draft, the pre-pass and, after blocker fixes, one verification pass; then the walkthrough, one finding per message, each chosen edit applied after the hash check and before the next card; minutes after each finding; the recap into the approval summary.

A conversion, in order: discover (source, repository rules, code, history, tests; completed work or new work), preserve (the source verbatim as `idea.md`, its number, task IDs, other tools' metadata), then requirements, design, and tasks through the workflow skill's own phases and gates, then the handoff with the receipt. It stops at the first ambiguous gate and starts no implementation.

## Error handling

- A host with no command runtime skips the advisory scripts and says so; the review goes on.
- An open blocker after the verification pass goes to the developer and blocks approval; the agent does not loop.
- A disputed finding is recorded with its reason and not raised again without new evidence.
- A conversion source that is missing or matches more than one document: the skill asks for the path and does not guess.
- A conversion that would need an approval the runtime did not record stops and shows the document, the scope, the blockers, and the next action.
- A merge or split proposed by the cross-spec review waits for explicit approval and never touches a spec in implementation or complete.

## Security and privacy

- Artifact text is data in every review: an instruction found inside an artifact is reported as a finding and never followed.
- T-077 reviews the ported scans' file handling, and T-076 reviews merges, splits, and the path handling of `check_links.py`; each finding gets a regression test.
- `check_links.py` never resolves a home or absolute path; it warns on them and on `[[...]]` links.
- An isolated reviewer receives the current design, a requirements summary (in Design-First, a summary of the intake item), and the severity taxonomy, and returns findings only; it approves nothing.
- Conversion authorizes drafting and reversible organization only: no implementation, no plugin installation, no commit, no push, and no edit to another project's specs.

## Testing strategy

- Review scripts: a fence holding a backtick, and ID tokens next to a vague qualifier; `check_links.py` citation resolution and path warnings.

Each reference task ends with `python3 tools/specflow/check_rules.py --area <its area>` passing, except T-075 as noted below. Tests of the ported scripts are `unittest` files under `tests/specflow/review/` with local fixtures, named for the rule they enforce. A scenario clause below is an assertion in an eval record on a session the task writes; T-057 (00009) scores it on the three hosts, and inside this spec the check is the area check and the presence of those records.

- T-073: area `RVC`; a scenario fixture shows the edit landing before the next card, the minutes line written, and a disputed finding not raised on the next run.
- T-074: area `RVR`; fixtures seeded with a contradiction, an untestable criterion, a solution posing as a requirement, and an exclusion that removes a needed seam each produce the expected finding.
- T-075: area `RVD`, where the only failures left are script rules, whose checks are tests that T-077 writes (Plan A rows RDS-S1 to RDS-S8, which share the area, and any other row whose check is a `test:` entry); a design seeded with one defect per cardinal sin yields each as a blocker; isolated and inline pre-pass fixtures use current content and findings-only reviewers, log author fixes, and block approval on a surviving blocker.
- T-077: `test_fence_holding_a_backtick_is_stripped`, `test_prose_between_fences_is_scanned`, `test_reported_line_numbers_match_the_file`, and `test_id_tokens_are_not_measurements` pass. That they fail against the unported scripts is shown once, by a recorded run against the installed sources, written in the task's `Outcome:` line. Area `RVD` then passes with nothing skipped, and joins the CI step.
- T-079: areas `DLG`, `DSN`, `TSK`, and `RVD` pass with both plans; every approved Plan B row has a rule and a check, and every dropped row has none; no pending marker and no runner or model dependency appears in the built references.
- T-076: area `RVX`; overlapping specs, a dangling citation, and tasks with bundled outcomes, unlisted needed edits, or an unfinished sibling each yield a finding that cites the failing check and a NO-GO report unless waived; a coupled task that builds and verifies as one outcome is not flagged by file count alone.
- T-080: the skill validator and area `CNV` pass; a release-boundary test confirms `convert-prd/` ships and no CNV rule names a maintainer-only path; scenario fixtures cover an unimplemented-PRD conversion and a completed-work adoption, each preserving provenance and obligation coverage, stopping at the first ambiguous gate, and producing a receipt; a conversion of an already-built PRD never unchecks verified work. The acceptance run against the calcard-mcp fixture is T-081 in 00009.

## Rollout and migration

Order inside the spec: T-073; then T-074 and T-075; T-077; T-079; T-076; T-080 any time after T-074 and T-075. Each task appends its area to the CI step of 00005, except that `RVD` joins with T-077. When T-076 and T-080 are done every reference exists, and the checker can run with no filter for the first time. The three personal review skills keep working until their parity gates pass in 00009; nothing migrates here.

## Risks and edge cases

- A host has no isolated sub-task for the pre-pass or for per-spec grounding: impact l, likelihood m; mitigation: the inline pass with a summary is part of the rule; fallback: none needed.
- The ported scans report noise on a specflow design: impact l, likelihood m; mitigation: they are advisory and close no gate; fallback: skip them, which a host without a command runtime already does.
- The conversion skill's relative path to the workflow skill breaks on a host that installs skills one by one: impact h, likelihood l; mitigation: both skills ship in one package and 00008 tests the installed package on each host; fallback: the conversion skill names the workflow skill and asks the agent to load it by name.
- Likely next change, a fourth review such as a tasks review: the core is shared; impact l, likelihood m; mitigation: a new review is one file beside the others and one row in the intent table; fallback: none needed.
- Likely next change, conversion from another source such as an issue tracker: the contract assumes a document in the repository; impact m, likelihood l; mitigation: the preserve step already takes a copied source with its original location recorded; fallback: paste the source into an intake item by hand.
- Likely next change, a third port plan: its rows enter through the inventory exactly as Plan B does; impact l, likelihood l; mitigation: the `plans` map of 00005; fallback: none needed.
- Edge case: a review of an approved artifact stales it when an edit is applied, so the review reopens that gate.

## Requirement traceability

| Design element | Criteria |
|---|---|
| The three review intents | REV-001.1 |
| Shared review core: context read first, one finding at a time, apply before next, minutes, artifact text as data | REV-001.2, REV-001.3, REV-001.4, REV-001.5, REV-001.7 |
| Requirements review lenses and design review tiers, by profile | REV-001.6 |
| Design pre-pass | ART-003.9, ART-003.10, ART-003.11 |
| Cross-spec review: report, verdicts, reshapes | REV-001.8, REV-001.9 |
| `convert-prd` ships in the package; its activation | CNV-001.1, CNV-001.2 |
| The preserve step: source verbatim, number, task IDs, `Sources:`, the move on first write | CNV-001.3 |
| Completed-work adoption rules of `conversion.md` | CNV-001.4 |
| Obligation map | CNV-001.5 |
| Handover to the workflow skill's path and gates; what conversion never does | CNV-001.6, CNV-001.7 |
| Dated recovery; the stop at the first ambiguous gate | CNV-001.8 |
| Conversion receipt and the `conversion-receipt` check | CNV-001.9 |

## Alternatives considered

1. **One review reference for all three reviews** (smallest diff: a single file). Rejected. A requirements review would load the design checklists and the cross-spec lenses; loading by review and by tier is what keeps a review's context small.
2. **A shared core plus one file per review, and tier files for the design review** (chosen). The added files buy selective loading and one rule area per file for the checker of 00005.
3. **Conversion as a mode of the workflow skill.** Rejected by the developer on 2026-10-04 (the "Conversion skill added" entry of the 00001 log): it ships as a second skill, named `convert-prd` to keep it apart from the spike path's graduate step.
4. **An existing link checker** for `check_links.py`. Rejected without a registry search: those tools resolve URLs and file paths, not five-digit spec citations against a configured specs folder, and the package may carry no dependency.
5. **A named model or an external command for the pre-pass.** Rejected in the source: cross-model review is optional through host capabilities, and no model, command, or minimum finding count is required.

## Reuse inventory

- The shared dialogue section of `artifact-contract.md` (00006): one question per message, the picker, the recommended option first. Reviews point to it.
- `specflow_helper` of 00004: `config.py` for the specs folder in `check_links.py`, `status.py` for the spec map of the cross-spec review, `checks.py` for the `conversion-receipt` check, and `write_guarded` semantics for applying an edit.
- The five sizing checks in `phases/tasks.md` of 00006, reused by the cross-spec review.
- `templates/cross-spec-review.md` and the Q&A log format of 00004.
- The four source scripts and `test_check_links.py` in `buvis/agent-skills`, ported with the defects fixed.
- The reference skill `graduate/` in intake item 00001, adapted by hand.
- Searches: the repository holds no review or conversion code; the only code module is `scripts/validate.py`, read in full.

## Open decisions

No decision is open. Ruling D9 of 2026-10-04 (design gates report) is taken in above: the paragraph Proof and verification states the fixture's true condition, and T-081 (00009) compares structure against it.

Choices the source left to the design, made above and listed for approval: the eight file names under `review/design/`, with `pre-pass.md`; how the conversion skill hands over to the workflow skill; the obligation map and the receipt labels; what a waiver is and where review minutes of `review specs` go; `RVD` joining CI with T-077; the command lines of the ported scripts, kept as in their sources; tests of the ported scripts under `tests/specflow/review/`; the conversion skill reaching the workflow skill by `../spec-workflow/`; the receipt as a block in `qa-log.md`; and the `conversion-receipt` check.

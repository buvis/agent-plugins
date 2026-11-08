# Decisions

One section per decision date, oldest first. Cite a decision as
"decision <date> #n". A superseded decision keeps its text, with a notice.

Superseded so far: 2026-09-28 #1, #3, #7, #8 (by 2026-10-03 #1 and #2),
the `relink` half of the specflow `qa-log.md` Q3 (by 2026-10-03 #6), and
2026-10-03 #4's two-slice delivery (by 2026-10-04 #3).

## 2026-09-27 - specflow scope and intake layout

Status: applied in the specflow 0.2 rewrite (2026-09-30). Decision #5
stands; its eval runs and parity gate moved to a second delivery slice by
2026-10-03 #4, then returned to the initial-release gate by 2026-10-04 #3.

### Decisions

1. **Intake.** Raw requirement inputs (any source, any format) land in
   `docs/dev/project-management/intake/new/` and move to
   `intake/processed/` once formalized. They are inputs, not specs.
2. **Shared number.** One `NNNNN` prefix links an intake item, its PRD, and
   its spec. Spec folders are named like PRD titles:
   `.kiro/specs/NNNNN-<prd-like-title>/`. Replaces the bare kebab-case slug
   in ART-001.3.
3. **Backlinks.** The formal artifact (`requirements.md` or PRD) carries a
   `Sources` line pointing at the intake original.
4. **Fold SDLC skills into specflow.** The behavior of elicit-requirements,
   review-discovery-doc, review-design-doc, create-prd, review-prd-backlog,
   spike, and the phase behavior of autopilot's design-solution and
   plan-tasks becomes per-phase reference material in the single runtime
   skill. The personal skills retire one by one.
5. **Consistency safeguards (all three required):**
   - Numbered behavior inventory per skill (`/plan-port`), rules marked
     port / redesign / drop, drops user-approved, and stored in local adapter
     files that the AWS updater never overwrites.
   - Structural rules enforced by validator code (IDs, EARS, traceability,
     placeholders, gate order).
   - One scenario eval per behavioral rule, run on each supported host. A
     personal skill retires only after specflow passes its rule set on the
     same inputs (parity gate).

### Known ripple

autopilot pulls PRDs from `prds/backlog`. If `requirements.md` replaces the
PRD, autopilot must be repointed at `.kiro/specs` or kept as a separate lane.
To be decided during the spec rewrite.

### Port plans (2026-09-28)

6. **Two plans.** The port is split in two: Plan A
   (`discovery/00001-specflow-port-agent-skills.md`, the six agent-skills
   skills, complete) and Plan B (`discovery/00001-specflow-port-autopilot-phases.md`,
   design-solution and plan-tasks phase behavior, walkthrough pending). Plan B
   retires nothing: autopilot calls both skills directly.
7. **Review edit timing.** Reviews apply edits after each choice (not batched
   at the end), everywhere, because it survives tool switches mid-review and
   fits the hash check before writes. review-discovery-doc's batch mode was
   "by user preference" (its SKILL.md:10); flip on request.
8. **Walkthrough conventions.** One drop per question; drops sharing one
   reason may be merged into one packet listing every row, with the option to
   pull rows out. Quote evidence only from source lines actually read.

### Next

Plan B walkthrough, bugfix-workflow study, then rewrite the specflow
requirements, design, and tasks under
`intake/processed/specflow/00001-initial-delivery/`.

## 2026-09-28 - specflow upstream: awslabs/aidlc-workflows

Status: applied in the specflow 0.2 rewrite (2026-09-30). **Decisions #1,
#3, #7, and #8 are superseded** by 2026-10-03 #1 and #2: A2 stays a tracked
source, and the updater pipeline is cut. Their text is kept as the record of
what was decided then. Evidence and line references:
`discovery/00001-specflow-aidlc-workflows.md` (A1 @ `fbb7f1c`, A2 @ `3e7c0f0`).

### Decisions

1. (Superseded.) **A1 replaces A2 as the pinned upstream.**
   `awslabs/aidlc-workflows` is the method reference;
   `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` is retired.
   Rejected: A1 beside A2 (two parsers, one idle source); specflow as an A1
   plugin plus Kiro exporter (A1's artifact path is engine-derived, Kiro IDE
   personas cannot write `.kiro/**`, A1 needs a runtime, plugins are additive
   only; would reopen canonical Kiro artifacts and "no runtime" and
   invalidate Plan B); keep A2 only (idle since 2026-08-07, 257 prompt lines).
2. **Allowlist = phase-fit set.** `core/scopes/*.md`; stages
   `requirements-analysis`, `domain-design`, `units-generation`,
   `code-generation` (test floor), `build-and-test`; `stage-protocol.md` §3
   (questions, depth, contradiction) and §8 (test strategy); the scope-stage
   matrix in `docs/guide/05-scopes-and-depth.md`; `LICENSE`. About 2,500
   lines. Pin release tags (`vX.Y.Z`) only, never commits on `main`. Since
   2026-10-03 #2 this set is the catch-up's review scope for A1, not a
   shipped copy.
3. (Superseded.) **Updater parser = structural.** Stdlib parser for the YAML
   frontmatter subset A1 uses (scalars, block lists, one-level maps) plus a
   heading tree; anything outside the subset blocks the update. Semantic diff
   keys: `scopes`, `produces`, `consumes`, `required_sections`, `depth`,
   `guard_policy`, `review_cap`, section bodies by heading path, license
   text. Replaces UPD-002.4's Python `ast` rule.
4. **Profiles stay two, mapped to A1 depth.** `standard` = A1 Standard,
   `quick` = A1 Minimal; `adaptation.md` records the mapping and cites A1's
   question-volume table for guidance only. A1 scope names are not profiles
   (they skip artifacts; `bugfix` is already a spec type).
5. **Invalidation stays strict** (WF-002.5-6). A1 Guard Policy relaxed/off
   and its advisory staleness go into design §17 as a rejected alternative.
6. **Requirements §3.7 wording.** Reword the non-goal to name AWS AI-DLC's
   record tree (`aidlc/` or `.aidlc/`), since A1's neutral tree is `aidlc/`.
7. (Superseded.) **Adapter file follows the parser subset.**
   `aws-adapters.yaml` is written in the same YAML subset (or JSON);
   maintainer tooling stays stdlib-only.
8. (Superseded.) **Retire A2 with a provenance note.** AWS-001.1 names
   `awslabs/aidlc-workflows`; `adaptation.md` keeps one paragraph on A2
   (`3e7c0f0`, 2026-08-07) as the prior source, A2's own "complementary"
   claim about A1, and why it was dropped.

### Settled without asking

- One question at a time stays (user communication rule); A1's batching
  and three answer modes are not adopted.
- Feature-spec IDs stay `REQ-`/`T-` (decision 2026-09-27); A1's `FR{n}`/
  `NFR{n}` are noted in `adaptation.md`, not adopted.
- Bugfix contract mirrors Kiro (decision 2026-09-28, bugfix doc §5); A1's
  regression floor (`code-generation.md:138`) may be cited as support, never
  as shape.

### Spec edits queued for the rewrite

- Requirements: §3.7, actors "Upstream", AWS-001.1-2, AWS-002.3, UPD-002.4-5,
  success measure 5 wording.
- Design: §3 (`aws/raw/` holds Markdown files, not `prompts.py`), §9.1-9.3
  guidance-source columns, §9.4, §10.1-10.4, §11.3 step 8, §17 (add rejected
  guard policy; rewrite "Manual upstream refresh" for Markdown), §18 links.
- Tasks: T-010, T-012, T-013, T-014, T-015, T-019, T-060.
- Plan B (`discovery/00001-specflow-port-autopilot-phases.md`): no row
  affected.

### Next

Rewrite the specflow requirements, design and tasks under
`intake/processed/specflow/00001-initial-delivery/` with these decisions and the
2026-09-27 and bugfix decisions applied together.

## 2026-10-03 - specflow docs review

Status: applied to the specflow spec as version 0.3 (commit `38f6a71`; #11
and #12 in later commits the same day). All were answered by the user in the
walkthrough recorded in
`reviews/2026-10-03-specflow-docs-review-consolidated.md`, which holds the
findings, the evidence, and the minutes.

### Decisions

1. **Sources.** A1 `awslabs/aidlc-workflows` is the primary method source.
   A2 `aws-samples/sample-ai-powered-sdlc-patterns-with-aws`, the original,
   and A3 `aws-samples/sample-aidlc-discovery` stay tracked as complementary
   sources. All three get a regular catch-up; none is vendored. Supersedes
   2026-09-28 #1 and #8.
2. **Catch-up skill, no pipeline.** The updater pipeline (parser, adapter
   mappings, normalizer, staged apply, raw snapshot) is cut. One maintainer
   skill reviews the sources from per-source cursors and writes tracked
   rulings; references are adapted by hand with a source line per passage.
   Supersedes 2026-09-28 #3 and #7. Lost: a machine check that every upstream
   section got a ruling, and byte-reproducible references.
3. **Maintainer skill home.** `.agents/skills/<verb>-<plugin>-<object>/` is
   the only committed copy; support files live in `tools/<plugin>/`; no
   agent-private folder and no symlink to one is committed. Follows the
   user's repo-structure plan (`~/.kiro/crew/workspace/ai-age-repo-structure.md`,
   its decisions 1, 3, 10). An earlier answer in the walkthrough (committed
   links) was withdrawn for it.
4. **Two slices — superseded by 2026-10-04 #3.** Release 0.1 gates on deterministic tests, the slice-one
   rule inventory check, and the cross-host handoff. Slice two (per-rule
   eval runs on every supported host, parity, cross-spec review, advisory
   scripts) gates skill retirement. The 2026-09-27 #5 standard is not thinned.
5. **Hosts.** Kiro IDE, Codex, and Claude Code are supported, with a loading
   probe before feature work. Kiro CLI and Kiro Crew are untested, not
   promised.
6. **Specs folder.** specflow reads and writes the configured specs folder
   directly and owns no `.kiro/specs` link; making that link for Kiro IDE is
   the repository's onboarding job. Config moves to `.agents/specflow.json`.
   Supersedes the `relink` half of the specflow `qa-log.md` Q3.
7. **Marker gate.** An approved upstream opens drafting; open markers block
   the dependent approval until accepted by name. The ledger stays.
8. **Kept as written.** Design-First creation (resume needs the same
   machinery, so cutting creation saves little) and the status JSON schema
   with its version promise (autopilot is a named consumer).
9. **Small fixes.** Hash exclusions cover only parsed task checkboxes and a
   task's own progress fields, never fenced text. One active writer per spec
   is the contract; no lock. Python 3 is required to record an approval; the
   shell hashing fallback goes.
10. **Discovery.** Four per-spec rules adapted from A3: what must not change
    for a feature, binding technical constraints when the repository gives
    nothing to infer, hedged answers as unresolved questions, and a source
    for inferred answers. Product-level discovery is a stated non-goal: write
    those documents by hand or with the AWS tool and pass them to intake.

11. **Discovery, second pass.** The first comparison with A3 rested on a
    skim; a full read found more, and the user took all eight:
    - the spec folder and state file are created when type, order, and
      profile are confirmed, before the first question (WF-003.13);
    - an unclosed code fence fails validation and blocks approval
      (VAL-001.11);
    - the profile may be raised from quick to standard at any time
      (WF-003.14);
    - structure stays English whatever language the developer writes in
      (ART-001.11);
    - the Q&A log holds the developer's own words, is append-only, and takes
      a replacing entry for a changed answer (INT-001.5, SEC-002.2);
    - intake asks about systems outside the repository, each ban carries a
      reason and an alternative, and one example to imitate is asked for
      (WF-003.11, WF-003.12);
    - each question carries a progress line (ART-002.14);
    - a spike may be a sketch: a user journey and static mockups
      (INT-002.8).

12. **A1 full read.** Twelve A1 stages outside the adoption set were read in
    full at `v2.10.0`: the seven ideation stages, the three initialization
    stages, `practices-discovery`, and `reverse-engineering`. No text is
    taken; ten local rules are, and one was rejected:
    - one fixed rule for "existing code or empty", and a coverage statement
      for every discovery (WF-003.15, WF-003.16);
    - a `Source:` line for every requirement, nothing unpicked turned into
      scope, and assumptions named at approval (ART-002.15, WF-002.1,
      VAL-001.12);
    - the repository's instruction files read on every host (WF-003.17);
    - an existing library, tool, or service among the design alternatives
      (ART-003.12);
    - a commit recorded at approval and an advisory drift warning
      (WF-004.8, STATE-001.2);
    - a "not decided yet" choice, plain words with terms defined, and a
      playback before drafting (ART-002.16-18);
    - a `Depends on:` line between specs, closing the implementation gate
      (ART-002.11, WF-001.9, STATE-003.1);
    - working practices asked when nothing shows them: test order and a thin
      end-to-end slice first (WF-003.18). Taken against the recommendation
      to leave it out;
    - a design-system question and an accessibility note for sketches
      (INT-002.8);
    - one explicit path for an input file, copied into the intake item
      (INT-001.8).

    Rejected: offering to save confirmed conventions into the repository's
    instruction file. specflow does not edit files it does not own.

13. **Spec-dependency contract for 0.1.** In the discovery-additions doubt
    review, the user chose F3 option 1: retain the capability and define its
    input, gate, and error contract. One comma-separated `Depends on:` line
    lives in the feature requirements header or at the end of bugfix
    Introduction. References use five-digit numbers or `folder:<exact name>`
    within the configured specs folder, including unnumbered native specs.
    Reconcile direct prerequisites read-only; each must be complete. Invalid
    declarations, unresolved/ambiguous/unreadable targets, self-reference, and
    reachable cycles close only implementation and yield no next task, with
    a named reason or cycle path. Phase and approval records stay derived by
    the existing rules; no scheduler, stored dependency state, or link
    machinery. Deterministic fixtures belong to T-020/T-026/T-029. Minutes:
    `reviews/2026-10-03-specflow-discovery-additions-review.md`.

14. **Shared dialogue loads in every phase.** The user chose F5 option 1:
    place shared questioning, Q&A logging with redaction, and approval-summary
    rules once in the existing `artifact-contract.md`, under the `DLG` rule
    area. Load it on every workflow invocation before questions or approval,
    including intake, Design-First, and direct reviews. Phase references point
    to it and retain their own question banks and artifact instructions. T-030
    owns the shared rules and eval records; T-031 through T-034 reuse the
    sessions for their phase assertions, including working preferences reaching
    task order and synthetic-secret redaction. Preserve source mappings and
    the two-slice eval contract. Question budgets, playback policy, and hedge
    handling await their own findings; this ruling changes loading and checks.

### Notes

- Not read against specflow: A1's other sixteen stages at `v2.10.0` (four
  inception, five construction, seven operation), and the five adopted stages
  were not re-read in this review.
- A2 was pushed on 2026-09-09 and is MIT-0 (GitHub API, 2026-10-03), so the
  "idle since 2026-08-07" reason in 2026-09-28 #1 was already stale.
- The Claude review's "add a maintainer-skill example to `templates/`" was
  not carried: under #3 a maintainer skill lives at the repository root, not
  in a plugin template, and the first one (T-018) is the example.

### Open

- The catch-up cadence (before each release and at least monthly) and the
  config path `.agents/specflow.json` are defaults proposed in the review,
  accepted as part of the options but not separately confirmed.
- This file's home follows the autopilot layout contract (`meta/decisions.md`).
  The repo-structure plan moves decisions to `docs/dev/architecture/` when it
  lands.

## 2026-10-04 - specflow discovery-additions doubt review

### Decisions

1. **One intake budget; conditional playback confirmation.** The user chose
   F1 option 1. Read available input and applicable instructions first, reuse
   known answers, and ask only material unknowns across one shared intake
   budget. Before quick needs more than its usual 0-2 questions, explain and
   propose standard; never raise it silently. The developer may keep quick
   with agreed extra questions, narrower scope, or explicit unresolved items
   under the existing gates. Count content questions separately from
   confirmations, without hiding new questions inside confirmations.
   Keep the short playback, combine it with existing intake-choice confirmation
   where possible, and require a separate response only for a material
   interpretation or unresolved conflict that no existing confirmation covers.
   Clear answers need no second confirmation before drafting. Artifact approval
   and named marker acceptance retain their meanings. This narrows
   2026-10-03 #12's universal playback stop; it does not remove the progress
   line, working practices, or sketch capability. Minutes:
   `reviews/2026-10-03-specflow-discovery-additions-review.md`.
2. **Mark only genuine uncertainty.** The user chose F2 option 1. Preserve
   caveats verbatim in Q&A; record only the undecided part affecting this spec
   as unresolved, with a resolution path. A definite current-release choice
   stays a requirement, while a later revisit outside this spec stays a
   follow-up note in the log. Wording such as "for now" alone is not a marker
   trigger; ambiguous current intent is clarified or retained as uncertain.
   Future decisions affecting this spec cannot be hidden in follow-up notes.
   This narrows 2026-10-03 #10's hedge rule; explicit undecided choices and
   the named marker-acceptance gate remain unchanged. T-030/T-032 own the
   shared-dialogue and requirements assertions.
3. **Full initial delivery, including complete drift detection.** In the F4
   walkthrough the user rejected deferral: “initial release must ship full
   features”, then confirmed “yes, we don't defer, it makes no sense to defer”
   when asked whether this also moves the previously agreed slice-two features
   into 0.1. Supersedes 2026-10-03 #4: all accepted functionality and its planned
   proof ship in 0.1, including cross-spec review, advisory scripts, all-host
   evals, and parity evidence. No release-slice inventory exemption remains.
   External autopilot migration and actual source-skill retirement retain their
   own repository ownership; the full plugin and evidence precede those handoffs.

   F4 stays in 0.1 with its full working-file behavior, rather than a
   committed-changes-only approximation. The design uses per-file content
   hashes/absence captured at design approval, including dirty and untracked
   content; `approvedCommit` is optional provenance. Reapproval resets the
   content baseline even at the same HEAD. Missing evidence reports not checked,
   never clean, and closes no gate. Hash only explicit placement files, keep
   no source snapshot, require no clean tree or lock, and preserve the existing
   Git-scoped advisory. This baseline detail implements the full-feature ruling;
   it was not a separate user selection of the earlier limited option 2.
4. **Explicit decision-criterion coverage.** The user chose F6 option 1.
   Keep an independent maintainer list of the 31 reviewed criterion IDs at
   `tools/specflow/rules/criteria.json`; map each through inventory rules to
   their existing checks. Shared rules and structural/behavioral splits remain
   valid. A decision citation alone is not coverage. Fail omitted mappings,
   missing or malformed lists, unknown/duplicate IDs, and missing checks;
   construction-area filtering cannot hide an unmapped criterion. Print the
   criterion/rule/check rows for release review. The list is reviewed scope,
   never inferred from existing rules; no upstream or decision-prose parser.
   Traceability is machine-checked, while substantive assertions and eval runs
   establish behavior. T-070/T-069/T-063 own these contracts and checks.
5. **Instruction applicability before conflict resolution.** The user chose
   F7 option 1. On every host, read root instructions and follow declared
   routing to instructions applicable to affected paths or conditions. Keep
   source, scope, and precedence; never turn unrelated local rules into global
   constraints or invent a ranking between file types. Ask only about material
   conflicts that remain applicable together. Unknown paths mean incomplete
   scoped coverage, revisited as paths become known or work expands. T-031
   covers imports, scoped overrides, inactive conditions, genuine conflicts,
   coverage changes, and unavailable sources. No new instruction directory,
   projection, or configuration is introduced.
6. **One mockup per unique screen; one spike question budget.** The user chose
   F8 option 1. Reuse a screen's mockup across journeys, exclude the navigation
   index from the correspondence, link declared user-action edges, and allow
   terminal screens without invented actions. Keep the full sketch capability
   and the rough spec's scope. Reuse known UI/accessibility context; for
   phrase-only entry the single content question covers rough-spec and sketch
   setup together, with unasked choices recorded as guesses/open questions.
   Keep the accessibility note and remove the unspecified no-HTML fallback.
   T-072 owns structural and dialogue checks, including shared/terminal screens,
   malformed mappings/links, offline output, and the question budget.

## 2026-10-04 - specflow split into nine specs

Decided while converting the 00001 intake item into specflow artifacts by the
manual procedure of `graduate/` (no runtime exists yet). Questions and answers:
Q9 to Q12 in the 00001 `qa-log.md`. Map and findings:
`reviews/2026-10-04-specflow-split-map.md`. Numbering continues the day's
list above.

### Decisions

7. **Dogfood by split.** The user chose "Split by phase": the 00001 item is
   converted into several specs cut along the task phases and linked by
   `Depends on:` lines, not kept as one spec. Each spec is a feature spec,
   requirements-first, standard profile. Approvals are dated receipts in the
   intake logs until the helper exists; no `.specflow.json` is written by
   hand.
8. **Nine specs.** The user approved the split map with "Split 00005 in
   two": the rule inventory and eval formats (T-070, T-071, T-069) are their
   own spec, apart from the runtime skill. 00001 keeps phase 8 and the shared
   framing; 00002 to 00009 hold the rest. T-081 moves to the validation spec,
   because phase 5 and phase 7 otherwise wait on each other. Requirement,
   criterion, and task IDs keep their source values.
9. **Cite upstream.** The user chose F2 option 1. A criterion has one home:
   the most upstream spec with a task that builds it, and it is never
   restated in a second spec. A task may cite a criterion of a spec its own
   spec depends on, written `00004 WF-004 criterion 8`. This adds two
   criteria to the contract: ART-004.16 (the task rule, in 00006) and
   VAL-001.13 (the validator check, in 00004). Whether both join the
   required-criterion list of RULE-001.1 is open until the 00005 design gate.
10. **Four small rulings from the split.** The user took every recommended
    fix. PKG-002.6 (distribution branch) stays in the contract as dormant: no
    supported host needs `plugin.json` at a repository root, so release 0.1
    has no task for it, and the host loading probe reopens it if it finds
    such a host. T-053's check that the user documentation states the
    one-writer contract moves to T-061, which writes that documentation.
    T-030 owns `references/state-contract.md` and the two profile references,
    which no task named. VAL-001.9 lists a `(guess)` marker only outside
    inline code and fenced blocks. The two task changes are applied when the
    task plans of 00001, 00006, and 00009 are written.
11. **The conversion skill ships.** Recorded here on 2026-10-04 from the entry
    "Conversion skill added (2026-10-04)" of the 00001 `qa-log.md`, so rules can
    cite it: the developer asked that specflow ship a PRD-to-specflow
    conversion skill as a second distributed skill, `convert-prd`, adapted by
    hand from the reference skill `graduate/`. CNV rules cite this decision as
    `D:2026-10-04#11`. It added requirement CNV-001 and tasks T-080 and T-081.

## 2026-10-04 - specflow design gates

Decided in the walkthrough of `reviews/2026-10-04-specflow-design-gates.md`,
which holds each packet, its options, and the answer. Numbering continues the
day's list above.

### Decisions

12. **Fourteen design rulings.** The user took the recommended option each
    time. D1: T-002 writes a truthful shell `SKILL.md`; T-030 replaces it and
    forbids its sentence in the release check. D2: T-020 creates
    `references/artifact-contract.md`. D3: the host loading probe also runs
    one bundled script. D4: the Claude manifest names no `skills` path. D5 to
    D7: catch-up steps 8 and 9 are reworded, step 4 diffs license files, and
    text under a source line is verbatim. D8: ART-004.16 and VAL-001.13 join
    the required-criterion list, which holds 33, and RULE-001.1 says so. D9:
    the calcard-mcp fixture is described as it stands, and T-081 compares
    structure. D10: the developer judges rubric assertions by hand. D11: the
    Codex runner uses a temporary Codex home, unproven until T-056. D12: the
    marketplace is named `buvis-agent-plugins`. D13: each schema carries its
    address as `$id`, the raw file at the release tag, from the task that
    writes it. D14: one extra recheck of four late blocker fixes was allowed,
    once, against the one-recheck rule.
13. **Twelve leftover fixes.** The user chose "Accept all 12": bundles A
    (00008), B (00005), and C (00001) of the report, as written there. Two
    reword carried text: the description of rule area `SKL`, and design
    principle 6, which now says "source and ref".

## 2026-10-05 - specflow tasks gates

Decided in the walkthrough of `reviews/2026-10-05-specflow-tasks-gates.md`,
which holds each packet, its options, and the answer.

### Decisions

1. **Design findings corrected.** The user chose "Fix designs, one last
   check": the 27 places where an approved design contradicted itself or
   named a file for no task are corrected in the designs, and reviewers made
   one last pass over those edits and over the late fixes in the task plans.
   The one-recheck rule was bent a second time, by this ruling.
2. **Four small rulings.** The feature branch is merged into the default
   branch before the release candidate is verified. T-061's check that the
   user guide states the one-writer contract cites no criterion, and 00004
   stays off the dependency line of 00001. Two rules of the implementation
   phase take their source from criteria: "one coherent task at a time" from
   ART-004.5, and routing an upstream error through invalidation from
   WF-002.5. The 0.1.0 changelog heading carries the day T-062 writes it.
3. **Final gate (2026-10-06).** The user chose "Approve all, confirm
   ratings": the nine corrected designs are approved again, the nine task
   plans are approved, the three open upstream questions are accepted by
   name, and the 46 guessed risk ratings are confirmed. Two late plan
   corrections that no reviewer re-read were named in the question and are
   accepted with it. Implementation is not started by these approvals.

## 2026-10-09 - specflow 00002 completion review

Decided in the walkthrough of `reviews/00002-package-boundary-review-01.md`,
which holds each finding, its options, and the answer.

### Decisions

1. **Review fixes.** The user took the recommended fix for each of the four
   findings that got their own question, and chose fixes from the three
   batches of small ones: 11 applied, 5 deferred, 2 rejected, 2 resolved or
   settled, as the minutes there list. The release check now requires `name`
   and `version` in the Claude manifest, matches slash markers against the
   package path, and reports folders it cannot read.
2. **00002 re-approved.** The fixes edited the approved `requirements.md` and
   `design.md` of 00002, which staled both approvals. The user chose "Approve
   both (Recommended)"; the receipts are in the 00002 `qa-log.md`. The tasks
   approval stands: `tasks.md` gained only an Outcome line.
3. **00008 design re-approved.** The host loading probe (T-006 of 00002)
   corrected the 00008 host install lines, which staled that design, and no
   receipt had been written. The user chose "Fix line 66, re-approve
   (Recommended)": the Codex line now states only the tested marketplace path,
   and the receipt is in the 00008 `qa-log.md`.

## 2026-10-10 - specflow 00003 completion review

Decided in the walkthrough of `reviews/00003-aws-sources-catchup-review-01.md`,
which holds each finding and the answer.

### Decisions

1. **Review fixes.** Of 17 findings, 11 were applied (R1-R4, R6, R10-R15),
   3 rejected with evidence (R5, R7, R8), 2 resolved by a check (R16, R17), and
   1 accepted and filed (R9: the long validator functions, now intake item
   `00010-split-long-validator-functions`).
2. **REL-001.3 amended.** R3 turned REL-001 criterion 3 into a per-file
   source-line check, with passage placement checked by hand whenever text is
   adopted. The edit staled the approved 00003 `requirements.md` and no
   receipt followed; the developer approved it again on 2026-10-16, in the
   recovery that wrote `.specflow.json` (00003 `qa-log.md`, "Recovery").

## 2026-10-11 to 2026-10-14 - specflow 00004 completion review

Decided in the walkthroughs of `reviews/00004-artifact-state-contract-review-01.md`
to `-11.md`; each file's minutes hold the findings, options, and answers, and
`reviews/00004-artifact-state-contract-ledger.json` holds the dismissed and
deferred findings so a later cycle does not raise them again.

### Decisions

1. **Eleven cycles.** Cycles 1 to 7 and 10 changed design text, and cycles 1
   and 6 requirements text too, so each ended with re-approvals recorded in the
   00004 `qa-log.md`; cycles 8, 9, and 11 changed code and tests only. No
   CRITICAL or HIGH finding was raised after cycle 4, so cycle 11's rework got
   a per-task patch review (2026-10-15) instead of a twelfth cycle.
2. **Withdrawn requirements (2026-10-11).** A `### <ID>: withdrawn` heading
   keeps its ID reserved and needs no criteria or task; nothing may cite it.
3. **Kiro link (2026-10-12).** Both Kiro IDE trials of T-027 passed, so the
   unresolved question was resolved in the artifacts instead of accepted, and
   all three were approved again.
4. **Close-out (2026-10-15).** PR #3 was merged locally, as PRs #1 and #2
   were, and the completion criteria were ticked (commit `31e1383`).
| 2026-10-29 | Pin local CLI serialization before independent test authors → Use minimal JSON format-list and prerequisite diagnostics; canonical policy export | The reviewed contracts specify commands and fields but omit serialization details; these conventions preserve all stated capabilities and avoid invented wrapper fields | batch-202610250001 PRD 00012 |
| 2026-10-29 | Final map delivery receipts exceed task integration dispatch budget → split | Measured minimal existing-asset receipt diff is90318bytes before persona, tests or README. Separate config task19 finalizes delivered rows while preserving frozen ownership; task16 retains README/final changed-file receipt updates. No completed inventory/map work is replanned. | batch-202610250001 PRD 00012 |
| 2026-10-29 | Offline package tests reveal map delivery classification defects → fix | 59 byte-identical reference deliveries must report preserved, retaining original planned adaptation. Eight old helper links not in92 required assets are historical unavailable references beneath unconditional skill gates, not active packaged resources; retain every edge/source/future destination and behavior owner, classify informational with no runtime fallback. Add source-null foundation file ownership without self-hash recursion. No promised file or future behavior is dropped; bounded Astra fix-forward after failed Sol metadata check. | batch-202610250001 PRD 00012 |
| 2026-10-29 | A stray blank line at `plugins/autopilot/CHANGELOG.md:9` splits the `### Added` list into two loose lists. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00012 |
| 2026-10-29 | resource_closure leaves out many runtime script dependencies. `resource_edges` has 202 rows, yet packaged skills call scripts that are neither packaged nor declared external: `consolidate_findings.py` (plugins/autopilot/skills/run-autopilot/references/lane-solo.md:168, plugins/autopilot/skills/review-work-completion/SKILL.md:386), `compute_mech_facts.py` (plugins/autopilot/skills/fast-track/SKILL.md:270), and also `render_prompt.py`/`record_dispatch.py` in fast-track, `detect_tautological_tests.py`, `check_review_file.py`, `await_reviewer_outputs.py`, `fast_track_plan.py`, `card.py`, `fablectl.py` and `parse_review.py`. The test locks the edge count and digest (tests/autopilot/test_package.py:331), so it cannot catch the gap. The unconditional skill gates block runtime harm today, but later PRDs that restore entry points will inherit this incomplete map → auto-fixed | fixed by review-close | batch-202610250001 PRD 00012 |
| 2026-10-29 | `plugins/autopilot/scripts/autopilot.py:41` re-walks the parsed policy by hand (lines 41-49) to find floats. Passing `parse_float` and `parse_constant` hooks that raise `ValueError` to the `json.loads` call at line 36 rejects fractions, exponents and NaN/Infinity while parsing. The behavior is the same, the 9-line loop goes away, and the existing `except ValueError` already turns the error into exit 1. → discard | single-voice; the existing bounded walk is correct and the proposed parser-hook refactor changes no specified behavior. | batch-202610250001 PRD 00012 |
| 2026-10-29 | All 27 behavior rows assigned to 00012 (P03–P05, R01, OPT-042, BEH-001..010, UTIL-*) still show evidence status "planned" with null artifact, sha and revision, and their acceptance cases are "planned". Nothing in the map links this PRD's own obligations to the contracts and tests it delivered, while asset rows carry "passed" receipts → discard | Discard: the contract explicitly says AP00012 validates completeness of assignments, not completion of future work. Planned behavior/profile evidence must not be upgraded to host certification from delivery tests. | batch-202610250001 PRD 00012 |
| 2026-10-29 | No test checks the policy's rule IDs against the packaged rubric files. The design says to "parse the rule ids from the packaged … rubric.md … and require them to equal rule_ids" and to require that `eve.md` has the de-slop section. Instead, the R, B and D lists are hardcoded constants (`test_contract.py:28-30`), so a wrong list would still pass. The committed data is correct today: it matches R1-R4, R6-R13, B1-B19 and D1-D5 in the packaged files. → discard | single-voice; the current policy IDs are correct. Missing dynamic rubric-file comparison is retained as a test-coverage limitation, not silently claimed fixed. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `tests/autopilot/test_package.py:203` checks six CHANGELOG bullets word for word, so rewording the changelog breaks a test. The CHANGELOG bytes are already pinned by `destination_blob_sha256` in `test_content_roster` (`tests/autopilot/test_package.py:281`), so this check repeats one that exists and only adds a dependency on the wording. A check for the `## [Unreleased]` / `### Added` structure would be enough. → discard | Discard: the immutable pre-integration history check independently prevents coordinated metadata/history erasure, a proved Devon exploit. Removing it would weaken required test intent. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `tools/autopilot/check-source.py:244` has three blank lines between `_audit_behaviors` and `_audit_regressions`. PEP 8 uses two (pycodestyle E303). → discard | single-voice; whitespace-only suggestion. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `tests/autopilot/test_package.py:69` builds its target from `git archive HEAD`. A local run with uncommitted edits therefore tests the last commit, not the working tree, and can pass on stale bytes. The design asks for this ("committed target inputs"), but neither the module docstring nor the README's Development section says so. → discard | Discard: the module docstring explicitly says Committed target packages; archive HEAD is the specified target-only contract, not an accidental stale-working-tree test. | batch-202610250001 PRD 00012 |
| 2026-10-29 | Four named acceptance scenarios have no test of that name: source_inventory_mapping, review_schema, reference_tree_preserved and package_self_contained. Tests under other names cover them (tests/autopilot/test_provenance.py:49, tests/autopilot/test_contract_semantics.py:299, tests/autopilot/test_package.py:286, tests/autopilot/test_package.py:371). The exit criterion "the named task tests pass" can only be checked by hand-mapping → discard | Discard: named acceptance scenarios are covered by the cited behavior tests. No contract requires Python function names to equal scenario labels. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The oracle rejects a review when an activated conditional reviewer (Carl) fails its last attempt (`required_job_failed`). The pinned retry policy says to mark the reviewer unavailable and continue (plugins/autopilot/skills/review-work-completion/references/retry-policy.md:9), and the policy encodes `reviewer_failed_after_retry → mark_unavailable`. Rejecting is right for mandatory jobs but stricter than the source for optional Carl, and no golden case covers that path → discard | Discard: activated required jobs must produce complete evidence; unavailable remains incomplete for a promised profile. Source retry/unavailability history is preserved separately. AP00020 owns actual runtime provenance. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The README and CHANGELOG "passed" delivery receipts point at themselves: the artifact is the file itself, and the test checks `tested_package_revision` only with a regex. The receipt proves nothing beyond the file's hash → discard | Discard: these are delivery-only file/hash receipts, explicitly not execution certification. The build independently checked real Git revisions; self-contained artifact identity is not a claim of independent runtime proof. | batch-202610250001 PRD 00012 |
| 2026-10-29 | prerequisites.py counts only regular `NNNNN-<slug>.md` files, but the backlog `eligibility:` lines use `ls done/NNNNN-*`. The "maintainer view of the same table" can disagree with selection, for example on `00012-x.md.bak` → discard | Discard: completed PRDs are regular NNNNN-slug.md files by contract; backup files are not completion. The strict diagnostic intentionally refuses unrelated backups. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `doubt_label_map` ships in the portable policy, but it comes from the author's personal global AGENTS.md, not the pinned source, and has no source binding. It is author-home content inside a package meant to work without the author → discard | Discard: the reviewed design explicitly specifies doubt_label_map. Committed policy data has no author-home runtime dependency; no forbidden live home read occurs. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `check-source.py` never reads `review-policy-v1.json`. The design says it recomputes the binding and anchor digests from the pinned blobs. Coverage holds only through two checks that must both run: normal tests compare policy to inventory, and the audit compares inventory to blobs. → discard | single-voice; the two passing checks provide transitive digest coverage. A direct policy read in the source auditor remains a coverage improvement, not a currently incorrect binding. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `test_rejected_cases_have_exactly_the_specified_complete_semantic_defects` repeats `test_contract_semantics.py:299` for the rejected cases, and `test_package.py:406` runs the same oracle a third time. Lines 63-94 also re-check properties that the `validate_review == accepted` assert at line 42 already enforces. → discard | Discard: independent mutation/adversarial and isolated-archive assertions preserve committed specification intent. Do not remove tests merely because their golden-case oracle overlaps. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `ci_autopilot_wired` asserts the exact list of steps in the unrelated `plugins` job. The design says not to snapshot unrelated workflow content, and any future specflow CI step will fail the autopilot suite. An ordered-subsequence check would still prove the job is preserved. → discard | single-voice; the exact unrelated-job step snapshot is a genuine maintenance limitation retained in the ledger. The current workflow is correct. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The draft 2020-12 `"type":"integer"` accepts `1.0`, so `attempt: 1.0` passes the schema. The oracle's `range(1, highest + 1)` would then likely raise TypeError instead of returning a defect. The wire test covers 1.5 but not 1.0. → discard | single-voice; confirmed by coordinator: full-clean input.reviewer_results[0].attempt=1.0 raises TypeError at history_defects line160. The canonical gate forbids single-voice medium/low fix tasks. Retain this concrete oracle limitation and reproduction, without claiming a repair. | batch-202610250001 PRD 00012 |
| 2026-10-29 | Cannot statically verify: the autopilot suite, `python3 -m unittest discover -s scripts` and `python3 scripts/validate.py` pass. The test gate reports exit 0 with no counts, and the fail-first replay was skipped because `requirements-test.txt` does not exist at base. → discard | Discard as resolved verification: canonical run_gate recorded PASS89 FAIL0 SKIP0 EXIT0; validator12 tests and repository validation also passed. Replay remains explicitly skipped because the base lacks the new requirements file. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The gated SKILL.md bodies keep `${CLAUDE_PLUGIN_ROOT}` and Claude-specific prose. This is known and out of scope: the content is preserved byte for byte behind the first-body refusal gate for AP 00015 to adapt. → discard | Known intended gate: AP00015 owns adapting retained source prose. No runtime fallback to source or author-home is authorized. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The only semantic validator is the test oracle; there is no runtime one. This is by design: task 14 forbids a validator runtime, and AP 00020 owns it. → discard | Known intended boundary: AP00020 owns runtime semantic validation; this PRD deliberately ships only a test oracle. | batch-202610250001 PRD 00012 |
| 2026-10-29 | Resource closure repair under existing edge schema → fix | Confirmed omitted script edges, including consolidate_findings.py and compute_mech_facts.py. Add complete source-anchored resource edges and gap-detecting tests using the existing schema; preserve frozen inventory, owners, prior edges and gates. Protocol C proceeds: the design Source-to-destination mapping explicitly defines resource edge kinds and failure rules. No public API or schema change is needed. | batch-202610250001 PRD 00012 |
| 2026-10-29 | Oversized asset rows exceed read-only helper snapshot budget → Use bounded read-only destination/source/hash/gate projections with current map SHA | The helper refuses full asset rows above18000bytes. Projected evidence stays below that emitted-input ceiling; no helper or cap change. All edge writes retain fresh helper snapshots and guarded apply. This is data IO, not a permission-denial workaround. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `FROZEN_EDGES` is about 55 lines of base85 zlib data that no reviewer can read. map_slice only replaces rows in place or appends them, and I checked that `digest("\n".join(sorted(identities[:202])))` equals `EDGE_SHA` today. That one line could replace the blob. The tradeoff: if someone reorders the map rows, the check fails, but it never passes by mistake. Otherwise move the 202 lines into a plain-text fixture pinned by `EDGE_SHA`. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00012 |
| 2026-10-29 | The [MECH] line "test_dependency_mutations has no assertion" is a false positive: `eq, yes = self.assertEqual, self.assertTrue` renames the assert methods, so the detector cannot see them. The test does assert. Call `self.assertEqual` and `self.assertTrue` directly and drop the alias line. That is easier to read and clears the MECH line. → discard | False positive: bound self.assertEqual/self.assertTrue aliases execute real unittest assertions; no missing assertion. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `dependencies()` misses script invocations whose path is in quotes. `prefix = line[:match.start()].rstrip("`` ` `` ")` strips backticks and spaces but not `"` or `'`. So `` `caffeinate -is python3 "$_skill/cli/__main__.py" wave run "$@"` `` at skills/run-autopilot/references/waves.md:243 never matches `COMMAND`. I checked by deleting that edge from the map: `closure_errors` still returns `[]` and every test passes. Changing the strip set to ``rstrip("`\"' ")`` closes the gap: with that change the current map still has 0 errors, and deleting the edge gives `edge count 0`. Add a `python3 "scripts/x.py"` case to `test_dependency_mutations` → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `GATE_SIZE` and `GATE_SHA` are defined twice, in test_resource_closure.py:13-14 and tests/autopilot/test_package.py:87-88. test_package.py already does `from test_resource_closure import closure_errors`, so it can import both constants from there and delete its own copies. → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The `failure_rule` check for packaged-resource edges sits after the if/elif chain and repeats the `kind == "packaged-resource"` test. Move it into the `if kind == "packaged-resource":` branch at line 94; behavior is unchanged. → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The closure oracle misses active script references. Its prose exemption (`decision model/does not use/hand-maintained model`) skips `qwen-integration.md:79` `scripts/work_routing.py`, even though the same paragraph says the output guard calls its classifier. Its verb regex only matches `run/invoke/execute/call`, so "invoking `fablectl.py`" at `model-ladder.md:91` is never found. Both sites have external-capability edges today, but deleting either edge or reclassifying it as informational would still pass. Task 20 required the oracle to catch exactly that. → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | 62 line-anchored external-capability edges have a capability that only repeats the path: 31 read "Host adapter for <reference>" and 31 equal the reference. One is `lane-solo.md:168` `consolidate_findings.py` (source-map.json:277993), a helper Blake named. All are new in this rework: `git grep` finds 0 "Host adapter for" rows at 3dda8f1 and 31 at HEAD. The contract requires an explicit capability and task 20 a concrete one. The oracle only checks that the field is not empty. → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The deferrals were never reviewed as a set, though task 20 required it. The slices deferred 125 observations, and 122 still have no edge. No disposition appears in rework-completion.md or task20-verification.json. I checked the 3 script entries and none is an active call: `agent-invocation.md:116` says "There is no `fable-run.sh` wrapper", `lane-fast-track.md:26` is an error message, and `model-ladder.md:92` is a section link. Some of the 119 non-script entries are host capabilities with no edge: `model-ladder.md:89` autoclaude, `:167` `~/.codex/hooks.json`, `:173` settings.json, `phase-review.md:145` and `:168` AskUserQuestion. The same capabilities are mapped at other sites (`use-sonnet/SKILL.md:31`, `state-schema.md:217`). → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | Maintainer tool tools/autopilot/map_slice.py (file locking, atomic rewrite, git diff subprocess) and its tests are not in the PRD's repository structure or exports; it came in with a rework commit (20ca08e) → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | The facade adds an `--out PATH` option (also passed through by export-policy.py); the PRD only names capability output and policy export → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | PyYAML added as a test dependency for the CI wiring test; the PRD names only test-only jsonschema (and pytest through the test command) → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | Three named acceptance scenarios (source_inventory_mapping, review_schema, package_self_contained) have no test or source-map ID with that name; the others appear inside longer test names. Tracing them needs judgment, and the target-only tests copy committed HEAD via `git archive`, so they need git and do not see working-tree edits → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | Two external-capability rows still carry the stale informational rule "Historical/source citation only; must not supply missing runtime content.": `dashboard-format.md:10` `scripts/tracon/` (source-map.json:273894), which is the active dashboard, and `:30` `scripts/README.md`. This is the task-28 contradiction the operator asked to resolve, and no check rejects `runtime_rule` on rows that are not informational. → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-10-29 | `except UnicodeDecodeError: continue` silently drops a file from the closure scan. Every package file is text (.md, .json, `autopilot.py`, LICENSE), so the guard covers a case that can't happen now and would hide a file if one appeared. → discard | single-voice; retained limitation/observation, no fix task under canonical Medium/Low rule. | batch-202610250001 PRD 00012 |
| 2026-11-08 | v3 design approach for R1, R3 and the git-probe timeout → Shared _root_anchor (shortest realpath prefix equal to root) for refuse and _pinned_parent_fd plus a .. refusal; dup-kept descriptor invalidation (ftruncate, NUL pwrite, reported residual) replacing name-based _empty_pinned; TimeoutExpired/OSError in _is_inside_git_dir fail closed. | Smallest diff that closes both HIGH rows at one shared primitive; 3 design dispatches, 1 blocker fixed; 9 non-blockers and 4 questions recorded in the design Review log | batch-202610250001 PRD 00013 |
| 2026-11-08 | PRD T1(d) artifact-sink parent swap under mixed spelling is pinned for the log sink only; no v3 case swaps the artifact sink's parent under mixed spelling (R17) → routed to verification | Eve's VERIFY item names an exact command; queued in reviews/00013-autopilot-session-helpers-v3-checks-1.json and run by the work phase's step-7 verification pass: rg -n "swap_artifact|artifact.*parent.*symlink|SPELLINGS" tests/autopilot/test_helper_rework_sinks.py tests/autopilot/test_helper_recovery_v2_sinks.py | batch-202610250001 PRD 00013 |
| 2026-11-08 | R7 is a confirmed public-CLI regression: autopilot verify --project-root . now exits 2 (unsafe-artifact-path) where the base commit accepted it → auto-fix via rework (Protocol D verdict: proceed) | High touching a documented public CLI option, so Protocol D ran. Verified both ends myself rather than trusting the single reviewer voice: at HEAD refuse(Path('docs/dev/tmp/x.log'), Path('.')) returns 'is a symlink' and _root_anchor returns None, while the same call against the base helper returns None (accepted). The fix is bounded and restores prior behavior, so the verdict is proceed, not escalate. Severity keeps the finding unresolved, so the cycle does not converge and rework runs at cycle 1 of cap 2. | batch-202610250001 PRD 00013 |
| 2026-11-08 | `_root_anchor` returns None for any relative path, so `--verify` with a relative `--project-root` (for example `.`) is now refused with `unsafe-artifact-path`. The pre-change code (b786f5a) accepted it. README.md:263 documents `--project-root PATH` with no absolute-path requirement, and the CLI passes `Path(args.project_root)` through unchanged (plugins/autopilot/scripts/autopilot.py:171). `run_verification` builds `root / artifact_path` (plugins/autopilot/scripts/verification.py:469), which stays relative. Reproduced from the repo root: `_root_anchor(Path('docs/dev/tmp/x.log'), Path('.'))` returns None, and `refuse` returns "is a symlink" for it, but None for the absolute spelling. No test covers a relative root, and the CHANGELOG does not mention it. Anchoring on `path.absolute()` (no normalization) in `_root_anchor`, as design dispatch 2 suggested, would keep relative roots working. Or document and test the refusal. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | The new `os.dup` failure branch of `_write_artifact` has no test. Pat flagged this as LOW in the recovery report, and `rg` finds no `dup` fault injection in tests/autopilot. The same branch leaves an existing leaf's earlier record in place, where the v2 `_empty_pinned` emptied it. The `_close_result_sink` docstring ("`_write_artifact` already emptied it") and the CHANGELOG ("leaves no reusable artifact after a failed write or close") are therefore not true on that path. The contract keeps this behavior, but it should be tested and the wording narrowed. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | The new CHANGELOG bullet fuses two clauses badly. "...and no longer read a nested repository's Git pointer: any symlink there ... is refused" makes the colon explain the nested-repo clause instead of the root-anchored rule. It also duplicates the first bullet's "leaves no reusable artifact after a failed write or close" with the new T2 bullet. Split the symlink rule into its own bullet and drop the repeated clause. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | The failed-artifact tests moved to tests/autopilot/test_helper_recovery_v3_artifact.py. That path is not in the PRD's complete write-path list (the PRD names only test_helper_recovery_v3.py). The split is justified because test_helper_recovery_v3.py is at 799 of 800 lines. Record the deviation in the PRD or report. The PRD's Verify line for T2 (`-k failed_artifact` on the old file) no longer selects those tests. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | The recovery report and the receipt's T4 entry record only the pre-regeneration gate at 6888765 (24 failed, 1212 passed). They say that "3 failed" provenance nodes are unresolved. The reviewed HEAD run (19 failed, 1217 passed, only the AP 00018 nodes) is recorded in neither file. The delivery evidence is stale against the final state. Record the final run, or state clearly that the final gate lives elsewhere. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | `refuse` calls `_root_anchor` once directly and again inside `_symlinked_component`. That is two realpath scans of the same path, and the `toplevel` parameter of `_symlinked_component` is now unused. Both follow the design contract. Passing the computed anchor in would remove the duplicate work and the dead parameter. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | The T1 receipt command contains literal `...`, violating the required exact-command evidence. Recover the complete invocation from its raw log, or record a fresh exact invocation and result without rewriting the historical measurement. Merged with R16 (Eve's same finding at :36, naming the `-k sink_alias ... -q` elision and `duration_seconds: "not captured"`), so this is a two-reviewer finding, not single-voice. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | log_sink_refusal.py:156 refuse computes _root_anchor twice and _symlinked_component's toplevel parameter is dead; passing the computed anchor in would remove both → deferred, not fixed in task 5 | behaviour-preserving tidy-up only (the finding itself says both follow the design contract), but closing it changes the signature of a private helper that two already-committed tests call directly with three arguments (tests/autopilot/test_helper_recovery_v3.py:223 and :293). That file sits at 799 of its 800-line limit and is outside this task's write set, so the cleanup would mean editing a security-critical module's test contract purely to accommodate a micro-optimisation during a cycle whose purpose is closing the R7 HIGH regression. The fix Ivan shipped left log_sink_refusal.py untouched, so neither the duplicate realpath scan nor the dead parameter is newly introduced. | batch-202610250001 PRD 00013 |
| 2026-11-08 | R1 receipt package_revision_note does not describe the product bytes at the re-pinned revision → swept (tail sweep task) | cycle 2: two voices (BLAKE, BOB) on real stale delivery evidence; the sweep task carries EVE's R8 remedy verbatim, including the 921efc5 gate section and the report header pin | batch-202610250001 PRD 00013 |
| 2026-11-08 | R2 task 5's R6 deferral rationale is weak and state.json carries contradictory R6 decision rows → discarded (settled deferral + out-of-scope state artifact) | cycle 2: the code change it argues for is the settled cycle-1 R6 deferral; the contradictory rows live in machine-written state.json outside this PRD's write paths | batch-202610250001 PRD 00013 |
| 2026-11-08 | R3 the merged --verify CHANGELOG bullet lost its conjunction before 'removes only a leaf it created' → swept (tail sweep task) | cycle 2: two voices (ALICE, EVE), mechanical prose fix, verified present at plugins/autopilot/CHANGELOG.md:33 | batch-202610250001 PRD 00013 |
| 2026-11-08 | R4 cycle-1 queued check for artifact-sink parent-swap coverage has no recorded result and the race stays unpinned → swept (tail sweep task) | cycle 2: two voices (BOB, EVE) plus the carried-forward unrun check from checks-1.json, whose entry carries no result; the one real coverage gap this cycle | batch-202610250001 PRD 00013 |
| 2026-11-08 | R5 _root_anchor accepts any leading prefix whose realpath equals the root, so a third spelling is trusted → discarded (settled deferral, ledger) | cycle 2: identical to cycle-1 R12 at the same log_sink_refusal.py:141; designed root-alias anchoring, BLAKE the only raiser in both cycles and in both he concedes containment holds with O_NOFOLLOW-pinned below-root components. --ledger-dismiss BLAKE did not match the text mechanically, so the dismissal is recorded by the gate and in the ledger | batch-202610250001 PRD 00013 |
| 2026-11-08 | R6 a missing or hung git still tracebacks out of stage_review through dirty_tree._git → discarded (settled deferral) | cycle 2: this is cycle-1 R5, already in state.deferred_decisions; PRD T3 names _is_inside_git_dir only and dirty_tree.py is outside the T3 write paths | batch-202610250001 PRD 00013 |
| 2026-11-08 | R7 T4's requirement to merge the overlapping CHANGELOG --verify bullets is unmet → discarded (contradicts verified facts) | cycle 2: misreads T4. The overlap T4 names (the log on spawn failure) was merged at CHANGELOG.md:33, verified against the PRD text and the file; lines 34-37 are distinct behaviours | batch-202610250001 PRD 00013 |
| 2026-11-08 | R8 the receipt and report claim a recorded gate covers the rework's product bytes when the latest recorded gate is feca0d1 → discarded (duplicate of R1, swept there) | cycle 2: same defect as the two-voice R1 row; the sweep task carries this row's remedy verbatim | batch-202610250001 PRD 00013 |
| 2026-11-08 | R9 the report cites its raw gate log in the gitignored docs/dev/tmp tree → discarded (single-voice) | cycle 2: ALICE only, and she states the evidence is usable because the counts are inline; docs/dev/tmp is the designated scratch tree and tracking raw logs is not a PRD write path | batch-202610250001 PRD 00013 |
| 2026-11-08 | R10 the five new dup-failure cases pass against the pre-rework code → discarded (mechanical replay control) | cycle 2: the raiser accepts the tests; same class as cycle-1 R14/R20, and cycle-1 R1 asked for exactly this pre-existing branch to be pinned | batch-202610250001 PRD 00013 |
| 2026-11-08 | R11 _write_artifact's NUL-byte pwrite fallback exceeds the spec's truncation requirement → discarded (single-voice) | cycle 2: BLAKE only, and he states it is defensive and low risk; it serves the spec rule that a failed artifact can never stay reusable | batch-202610250001 PRD 00013 |
| 2026-11-08 | R12 prior R6 remains unresolved (duplicate anchor scans, unused parameter) → discarded (settled deferral) | cycle 2: a restatement of the settled cycle-1 R6 deferral by its own author, asserting no new regression | batch-202610250001 PRD 00013 |
| 2026-11-08 | R13 prior R5 remains deferred (sibling staging git probes lack timeout handling) → discarded (settled deferral) | cycle 2: a restatement of the settled cycle-1 R5 deferral by its own author, out of PRD scope | batch-202610250001 PRD 00013 |
| 2026-11-08 | R14 the CHANGELOG bullet says --verify accepts a relative --project-root 'again' though nothing was released → discarded (single-voice) | cycle 2: EVE only, a wording preference on an unreleased entry; the changelog rule requires the entry and merging it back would re-fuse the clauses cycle-1 R2 asked to split | batch-202610250001 PRD 00013 |
| 2026-11-08 | R15 DUP_CALLS patches os.dup2 speculatively with a positional-only fake → discarded (single-voice) | cycle 2: EVE only, test-internal tidying; ALICE reviewed the same cases and accepted them, and the patch is scoped to the test's own context manager | batch-202610250001 PRD 00013 |
| 2026-11-08 | R16 sibling git probes in dirty_tree._git have no timeout or OSError guard → discarded (settled deferral) | cycle 2: the raiser files it as out of scope against the settled cycle-1 R5 deferral | batch-202610250001 PRD 00013 |
| 2026-11-08 | R17 state.json carries the R6 issue twice with contradictory actions and two D1-D5 verdict sets → discarded (single-voice, out of scope) | cycle 2: EVE only and filed by her as out of scope; state.json is machine-written workflow state, and two D1-D5 sets is the documented shape when Bob and Eve both run | batch-202610250001 PRD 00013 |
| 2026-11-08 | R18 commit 1539f6d's subject names a test file it did not touch → discarded (single-voice, unamendable) | cycle 2: EVE only and filed by her as out of scope; rewriting a pushed master commit needs a force push, which is not authorized | batch-202610250001 PRD 00013 |
| 2026-11-08 | R19 [MECH] 5 dup tests pass against the pre-change code → discarded (mechanical replay control) | cycle 2: the mechanical replay cannot distinguish a pin of retained behaviour from a missing pin, and cycle-1 R1 asked for this pre-existing os.dup branch to be pinned; same class as cycle-1 R14/R20 | batch-202610250001 PRD 00013 |
| 2026-11-08 | R20 [MECH] 28 relative_root tests pass against the pre-change code → discarded (mechanical replay control) | cycle 2: the row's own text enumerates why each case passes at base and names the 5 corrective cases that did fail first; same class as cycle-1 R13/R19 | batch-202610250001 PRD 00013 |
| 2026-11-08 | R21 the receipt's reviewed_head_gate.log points at a gitignored scratch file → discarded (single-voice) | cycle 2: EVE only and filed by her as out of scope; same fact as R9 | batch-202610250001 PRD 00013 |
| 2026-11-08 | The receipt's `package_revision_note` says the per-task T1-T4 measurements were taken at 6888765, not at the re-pinned revision. This is disclosed honestly and the historical entries were preserved. But the receipt does not describe the product bytes at the pin. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | The edit that removed ", and leaves no reusable artifact after a failed write or close" left the first `--verify` bullet's list without its conjunction: "...stops the child's leftover processes when a sink fails late, removes only a leaf it created; ...". It needs "and" before "removes". → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |
| 2026-11-08 | Prior R17 has a queued check but no recorded result establishing artifact-parent race coverage. Run `rg -n "swap_artifact|artifact.*parent.*symlink|SPELLINGS" tests/autopilot/test_helper_rework_sinks.py tests/autopilot/test_helper_recovery_v2_sinks.py`; inspect matching tests for mixed root/artifact spellings, a post-preflight parent swap, controlled refusal and unchanged sentinel bytes. Record the covering node or add the missing case. → auto-fixed | fixed by review-close | batch-202610250001 PRD 00013 |

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

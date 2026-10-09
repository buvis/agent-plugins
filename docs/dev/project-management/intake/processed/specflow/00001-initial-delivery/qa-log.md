# Q&A log: specflow spec rewrite 0.2

Questions asked while rewriting `requirements.md`, `design.md`, and
`tasks.md` to version 0.2 and folding in approved Plan B behavior. One entry
per question, written right after the answer. Location decided 2026-09-27.

Inputs: `meta/decisions.md` (2026-09-27 and 2026-09-28),
`discovery/00001-specflow-bugfix-workflow.md` §5, Plan A
(`discovery/00001-specflow-port-agent-skills.md`), Plan B
(`discovery/00001-specflow-port-autopilot-phases.md`, approved 2026-09-30).

## Q1 - Plan B timing (2026-09-28)

- Context: Plan B (131 rows from autopilot's design-solution and plan-tasks)
  had no approved rows; a separate session was walking it. Its rows land in
  the design-phase and tasks-phase rules.
- Options: rewrite now and mark the phase port as awaiting approval; finish Plan B first; fold
  Plan B rows in provisionally; rewrite requirements only.
- Answer: **rewrite now, mark pending.** Design-phase and tasks-phase rules
  carried an awaiting-approval marker, and one gated task was to fold the
  approved rows in later. Q7 and Q8 below close this document gate; T-079
  now contains only the build integration.

## Q2 - Autopilot ripple (2026-09-28)

- Context: autopilot pulls PRDs from `prds/backlog`; create-prd and
  review-prd-backlog feed and gate it (Plan A "Queued", decision 2026-09-27
  "Known ripple"). specflow's runtime skill must stay autopilot-free either way.
- Options: separate lanes for now; repoint autopilot at `.kiro/specs`; a
  one-way importer on autopilot's side; defer.
- Answer: **repoint autopilot at `.kiro/specs`.** The repoint itself is
  autopilot's work (a claude-autopilot PRD). specflow's share, all
  host-neutral: a stable, versioned machine-readable status output that an
  external runner can read (gates, stale artifacts, next task); files in a
  spec directory that specflow does not own are left alone; a handoff task
  writes the autopilot intake item. create-prd and review-prd-backlog retire
  after that repoint lands (Plan A Phase 7).

## Q3 - Intake, review, and spec locations (2026-09-28)

- Context: `docs/dev/project-management/intake/` is a buvis convention (Plan
  A "Queued"); cross-spec review reports also need a home (RPB-40); Kiro
  treats every folder in `.kiro/specs/` as a spec.
- Options: configurable root with `.kiro/specflow/` default; fixed
  `.kiro/intake/`; fixed buvis path; ask on first use.
- Answer: **configurable root**, and the user asked whether a symlink back to
  `.kiro/specs` would keep Kiro IDE compatible if specs also move under it.
- Follow-up options: follow an owner-made link; real `.kiro/specs` only;
  specflow creates and repairs the link; reverse link for browsing.
- Follow-up answer: **follow an owner-made link, plus a tool to relink so it
  works on Windows too.**
- Resulting contract: a repo config file names the root (default
  `.kiro/specflow/`; buvis sets `docs/dev/project-management`) and may name a
  specs folder inside the repo. specflow always addresses `.kiro/specs/`,
  follows the link only when it resolves inside the repo, and a `relink`
  helper op makes it (relative symlink on POSIX, directory junction on
  Windows, which needs no admin rights).
- My call, flagged: the `.kiro/specs` link is local and gitignored, not
  tracked. A tracked link checks out on Windows as a text file, and swapping
  it for a junction makes git see the spec files twice, so one careless
  `git add -A` commits duplicates. Cost: every clone runs `relink` once;
  status reports a missing or broken link with the command to fix it.

## Q4 - Where risks live (2026-09-28)

- Context: ELI-50, ELI-60, PRD-46, PRD-52 capture risks; requirements.md had
  no Risks section; Plan B DSN-33 (then unapproved) proposed one in design.md; strict
  invalidation means editing approved requirements stales design and tasks.
- Options: split by when found; design.md only; requirements.md only;
  approval summary only.
- Answer: **split by when found.** requirements.md `## Risks` holds scope,
  dependency, and outside risks known at requirements time; design.md
  `## Risks and edge cases` holds technical risks found while designing. One
  line each: impact, likelihood, mitigation, fallback.

## Q5 - Nice-to-have requirements (2026-09-28)

- Context: ELI-44 splits Must/Nice; Kiro has no tiers; RDD-34 says EARS REQs
  have none; every REQ is traced to design and tasks.
- Options: no tiers (must or out); priority line per REQ; separate untraced
  section. Only three honest options.
- Answer: **no tiers.** Every REQ is a must; a nice-to-have becomes a REQ,
  goes to `## Out of scope` with a "later" note, or becomes its own spec.

## Q6 - No-placeholder rule vs "Not applicable" (2026-09-28)

- Context: ELI-31 bans stubs, "N/A", and "TBD" and drops unused sections;
  design.md §6.3 and ported RDS-133 want "Not applicable" with a reason.
- Options: per artifact; N/A with reason everywhere; omit everywhere. Only
  three honest options.
- Answer: **per artifact.** `requirements.md`, `bugfix.md`, and `tasks.md`
  leave out sections that do not apply; `design.md` keeps every template
  section and marks unused ones `Not applicable: <reason>`. Bare `N/A`,
  `TBD`, `TODO`, and `???` fail everywhere.

## Design review (2026-09-29)

Minutes: `reviews/2026-09-29-specflow-design-review.md` (10 findings, all
applied). Decisions that changed the contract: shared eval sessions, strict
path characters for configured paths, number clashes defined by kind and the
`Sources:` link (splits get their own intake items), move-then-write for
`Sources:`, a `numberScan` config key, and a failing check for a real
`.kiro/specs` folder that git ignores.

## Spec review (2026-10-02)

Minutes: `reviews/2026-10-02-specflow-spec-review.md` (19 findings across
requirements, design, and tasks, all applied). Decisions that changed the
contract: a phase derivation table keyed on `## Completion criteria`;
`Outcome:`/`Exception:` progress fields outside the tasks.md hash;
`acceptedMarkers` on design/tasks approvals with the marker set defined; T-069
defines the eval formats before the reference tasks; full Design-First support
chosen at intake with reversed traceability; `phases/implementation.md` and
`phases/verification.md` with areas IMP/VER/VAL; Python 3 named as the
approval and relink prerequisite; one optional intake group level kept on the
move; a named fallback if Kiro ignores the specs link.

## Docs review (2026-10-03)

Minutes: `reviews/2026-10-03-specflow-docs-review-consolidated.md` (two
reviews merged; ten decisions, all answered by the user). The numbered
decisions, cited in the spec as "decision 2026-10-03 #n", are in
`meta/decisions.md`. Decisions that changed the contract: A2 and a new A3 (`aws-samples/sample-aidlc-discovery`) stay tracked
beside A1; the updater pipeline is cut for a catch-up skill and hand-adapted
references; the maintainer skill lives at `.agents/skills/` with nothing
agent-private committed; the first release ships as two slices; three
supported hosts with an early loading probe; specflow reads the specs folder
directly and owns no link, with config at `.agents/specflow.json`; open
upstream markers block approval, never drafting; hash exclusions bound to
parsed task lines; a one-writer contract; Python 3 required for approvals;
four discovery rules adapted from A3.

A second, full read of A3 followed when the user said more had been missed
(decision 2026-10-03 #11). Eight more rules, all taken: intake choices saved
to disk when confirmed; an unclosed code fence fails validation; the profile
can be raised later; structure stays English; the Q&A log keeps the
developer's own words and is append-only; intake asks about systems outside
the repository, and each ban carries a reason and an alternative; each
question carries a progress line; a spike may be a journey sketch.

A full read of twelve A1 stages outside the adoption set came next (decision
2026-10-03 #12): ideation, initialization, `practices-discovery`, and
`reverse-engineering`. Ten rules taken: a fixed rule for "existing code or
empty" with a coverage statement; a source for every requirement; instruction
files read on every host; build versus buy among the design alternatives; a
commit at approval and a drift warning; a "not decided yet" choice, plain
words, and a playback before drafting; a `Depends on:` line between specs;
working practices asked when nothing shows them (taken against the
recommendation); accessible sketches; one explicit path for an input file.
Rejected: offering to save conventions into the repository's instruction
file. Sixteen A1 stages remain unread.

Superseded here: the `relink` half of Q3 (the configurable root and specs
folder stand), and decisions 2026-09-28 #1, #3, #7, and #8.

## Settled without asking

- **Hold status needs no schema bump.** PRD-41's ruling asks for a version
  bump; `.specflow.json` v1 is unreleased, so `hold` joins v1.
- **Intake item moves on first write.** An item moves from `new/` to
  `processed/` when its spec's requirements artifact is first written
  (SPK-26 graduation; ELI-28 fallback path under `processed/`).
- **`Sources:` in `bugfix.md` sits at the end of `## Introduction`,** so the
  Kiro skeleton stays intact (bugfix contract) and decision 2026-09-27 #3
  still holds.
- **Rule inventory is maintainer-side JSON.** Rule text lives in the
  distributed phase references, tagged with its ID; the inventory under
  `tools/` maps rule, source rows, reference, and check (decision 2026-09-27
  #5; aidlc decision 7 allows JSON).
- **Normalized AWS references are one file per portable phase,** with
  depth-specific passages marked for `standard` or `quick`, so AWS-002.2
  holds without doubling the file set.

## Checked at A1 `v2.10.0` (2026-09-28, read-only clone in scratchpad)

- `v2.10.0` is an annotated tag: tag object `b1854bad`, commit `2a883858`.
  The discovery doc's "tag = `b1854bad`" is the tag object; the updater must
  peel tags to the commit.
- Allowlisted paths exist: `core/scopes/*.md` (11 files),
  `core/aidlc-common/stages/inception/{requirements-analysis,domain-design,units-generation}.md`,
  `core/aidlc-common/stages/construction/{code-generation,build-and-test}.md`,
  `core/aidlc-common/protocols/stage-protocol.md`,
  `docs/guide/05-scopes-and-depth.md`, `LICENSE` (MIT No Attribution).
- `stage-protocol.md` "§3" and "§8" are the headings `## 3. Question Format`
  and `## 8. Depth Guidance` (which holds `### Test Strategy`); the matrix is
  `## Stage-by-Scope Matrix` in `05-scopes-and-depth.md`. Neither file has
  frontmatter.
- Frontmatter shapes across the 16 files that have it: plain scalars,
  double-quoted scalars (2 lines), empty flow lists `[]` (5), block lists of
  scalars, and block lists of one-level maps (`consumes:`). No nested maps
  outside list items, no block scalars, anchors, or tags. The parser subset
  names these shapes exactly; decision 3's "scalars, block lists, one-level
  maps" covers them once quoted scalars and `[]` count as scalars and lists.
- `required_sections` (a decision 3 diff key) appears in no allowlisted file
  at this tag; the diff reports it if it appears later.
- Template tokens in the allowlist: only `{{HARNESS_DIR}}` and `{{INVOKE}}`.
- Question-volume table: `stage-protocol.md:368-372`; bugfix regression
  floor: `code-generation.md:138` (both at `v2.10.0`).

## Upstream churn check (2026-09-30, read-only clone in scratchpad)

- Allowlist churn: `v2.9.0..v2.10.0` touched 17 of 19 files (+246/-71);
  `v2.7.0..v2.10.0` touched 18 (+483/-237).
- The `sections` heading paths (`3. Question Format`, `8. Depth Guidance`)
  held from `v2.7.0` to `v2.10.0`; `13. Learnings Ritual` in the same file
  lost 6 subsections.
- All 11 scope files gained `guard_policy`, `sensors`, `learnings`, and
  `summary_confirmation` after `v2.7.0`. Only the first was a diff key.
- Decision (user, "go"): the semantic diff also reports any other
  frontmatter key added or removed, non-blocking (UPD-002.5, design §11.3
  step 9, T-015).
- `.kiro/specs` stays canonical. No sign of Kiro dropping it in the specs
  docs or the IDE changelog through 1.1.70 (2026-09-24); `specsDir` already
  keeps the real files elsewhere (§6.7).

## Q7 - Plan B table approval (2026-09-30)

- Context: 63 port/redesign rows needed one approval. Conflicts concerned
  design review minutes, a second review, section overlap, risks, and premises.
- Options: approve with settled corrections; pull out named rows; revise
  the table first.
- Answer: **"approve with corrections".** DSN-35/47 use intake Q&A minutes;
  DSN-36 joins the existing review as its pre-pass; DSN-27 follows the design
  section set and Q6; DSN-33 extends the existing risks; PLT-19 joins PRD-17
  and ART-004.8. DSN-54 includes Q&A minutes in its write scope.

## Q8 - Repair rounds and delegated drop rulings (2026-09-30)

- Context: DSN-03 through DSN-11 describe a separate fix-cycle design
  protocol. The explanation showed what is lost: a separate design for each
  repair round and a dedicated rule explaining why an earlier fix failed.
- Options: use the existing canonical design and gates; add portable
  repair designs; keep selected checks.
- Answer: "sure, why not" was ambiguous, so no ruling was recorded from it.
  When asked to pick the approach, the user said: **"I'm tired of these
  decisions, don;t you know hte best what to do?"**
- Authority: the user delegated the remaining calls to the assistant.
  These are assistant judgments under that instruction, not individual user
  selections. The agent stated that repairs would use the existing design,
  review, and approval flow, then finished the evidence-based rulings.
- Result: all 68 original drop candidates are accounted for in Plan B.
  PLT-41 and PLT-61 moved to redesign; 66 remain drops. Both source skills
  stay in autopilot. No separate repair-design artifact is added.

## Plan B integration decisions (2026-09-30)

- **Task risk evidence retained (PLT-41).** An actual exported contract,
  persisted format, hook shape, new algorithm, shared mutable state, or
  migration change needs a Risk note with its design mitigation. Mere
  vocabulary or interface use does not. Model flags and tiers are dropped.
- **Coupling explanations retained (PLT-61).** Each coupled multi-file task
  names what a split would break. No model-routing consequence.
- **Sizing settled.** One named outcome, bounded paths, exact applicable
  contracts, dependencies, and owned verification. Split independent
  outcomes safely; re-check each piece; keep coupled edits together.
  An unsplittable unbounded outcome blocks tasks approval. Cross-spec
  review uses the same five checks; no token or task-count ceiling.
- **One design review.** Draft pre-pass, blocker fixes, one verification
  pass after fixes, then the existing interactive walkthrough. Findings-only
  reviewers, current-artifact packages, anchored evidence, Q&A minutes, and
  an explicit developer gate remain.
- **Contract precedence has a limit.** Design owns implementation detail;
  requirements own acceptance. A conflict violating required behavior is a
  blocker requiring an upstream correction or a named accepted exception.
- **Native shapes kept.** Feature template extensions do not replace Kiro
  bugfix sections or native numbering; put detail in matching sections/items.
- **Completed work kept.** Re-planning keeps checked tasks and IDs; runner
  abort files and task-array rollback are dropped.
- **Document half complete.** ART-003/004, design routing/review/artifact
  sections/profile mappings, task instructions, and README now carry Plan B.
  T-079 retains only rule/reference/check build work after its baseline
  dependencies. T-057 waits for it before the full eval set. T-079 also
  waits for T-071/T-072/T-074/T-076, since its full rule check needs those
  structural checks and baseline references. Each reference brings its
  substantive eval records; a path to a future eval does not satisfy coverage.
- **Upstream follow-up.** Autopilot's classifier substring-matches port in
  support/report/import. No source code was changed here.

## Conversion skill added (2026-10-04)

- Context: a reference skill for PRD-to-specflow migration was added at
  `graduate/` beside this spec (`SKILL.md`, `references/conversion.md`),
  written by another agent that performed a real conversion. The developer
  asked to update the intake documents so it is clear specflow ships a
  conversion skill, reusing the reference as proven input, not byte for byte.
- Decision: ship the conversion as a second distributed skill inside
  `plugins/specflow/skills/convert-prd/` (runtime, not maintainer-only).
  Added Requirement CNV-001, design §6.9, and tasks T-080 (author the skill,
  adapting `graduate/` by hand into `CNV` rules, checks, and evals) and T-081
  (verify against the proven fixture). Wired CNV into the eval run (T-057),
  the release-candidate gate (T-063), user docs (T-061), and the Definition
  of Done.
- Naming: "graduate" is overloaded. §6.8's spike *graduate* carries a
  prototype's observed behavior into requirements; the new skill converts an
  authored PRD. The shipped directory is `convert-prd` to keep them apart;
  the reference folder keeps its original name `graduate/` as source material
  and is not shipped.
- Adapted, not copied: the reference predates this spec's naming, rule
  inventory (RULE-001), and reference-routing conventions, so its text is a
  validated source. T-080 realigns it to the shipped artifact, state, review,
  approval, and validation contracts rather than restating them.
- Proof: the reference conversion produced an approved artifact set at
  `buvis/calcard-mcp`
  `docs/dev/project-management/specs/00032-add-if-match-preconditions-to-event-writes/`
  (`bugfix.md`, `design.md`, `tasks.md`, `.config.kiro`, `.specflow.json`).
  T-081 copies that source and output into `tests/specflow/fixtures/` as a
  self-contained acceptance fixture; the trial showed artifact conversion and
  review, not executed implementation or a running runtime.

## Q9 - Dogfood specflow on its own spec (2026-10-04)

- Question: none asked; the developer opened with a request.
- Answer: "Ok, about that. The documentation is unstructured free format.
  Let’s dogfood specflow. Chicken and egg problem, I know, but would you be
  able to use specflow to write its specs for later implementation?"
- Reading: convert this item into specflow-shaped artifacts by the manual
  procedure of `graduate/`, for later implementation. No runtime exists, so
  approvals are receipts in the intake logs and no `.specflow.json` is
  written; recovery mode (WF-004.4) records real approvals once the helper
  exists.

## Q10 - Shape of the converted specs (2026-10-04)

- Question: What shape should the dogfooded specflow specs take? Options:
  split by phase; one spec, 1:1; core first, rest later; pilot one slice.
- Answer: "Split by phase (Recommended)"
- Reading: about eight specs cut along the task phases, linked by
  `Depends on:` lines, with a spec map first for approval. Feature,
  requirements-first, and standard were stated with the question and not
  objected to.

## Q11 - Split map approval (2026-10-04)

- Question: Do you approve the split map for specflow 00001? Options: approve
  as drawn; split 00005 in two; merge the small specs; rule on F2 first.
- Answer: "Split 00005 in two"
- Reading: the map is approved with the rule inventory and eval formats
  (T-070, T-071, T-069) as their own spec, apart from the runtime skill. Nine
  specs: 00001 keeps phase 8 and the shared framing; 00002 to 00009 hold the
  rest, each with its own intake item.
- Follow-up: rule 2 of the map (where a criterion lives) was amended after
  this answer and awaits confirmation at the requirements gate.

## Review: split of 00001 2026-10-04

Minutes: `reviews/2026-10-04-specflow-split-map.md`. Checked by script: 64
source tasks, each in one spec; spec dependencies derived from the task
dependencies; no cycle.

- F1 | Blocking | T-081 (phase 5) depends on T-050 (phase 7) | T-081 moved to 00009 | resolved
- F2 | Blocking | No rule for a task serving a requirement owned by another spec | map rule 2 as working answer | awaiting developer
- F3 | Non-blocking | PKG-002.6 has no task | listed under unresolved questions in 00002 | awaiting developer
- F4 | Non-blocking | Success measures and the full-delivery clause carry no IDs | `REL-002` and `REL-003` added | awaiting developer
- F5 | Question | A spec waits for its whole prerequisite, so T-070 waits for all of 00004 | no edit | noted
- F6 | Non-blocking | Requirements template has no parent heading for requirement blocks | drafts add `## Requirements` | awaiting developer
- F7 | Non-blocking | T-053 checks documentation that T-061 writes later | listed under unresolved questions in 00009 | awaiting developer
- F8 | Non-blocking | No task writes `state-contract.md` or the profile references | listed under unresolved questions in 00006 | awaiting developer
- F9 | Non-blocking | Requirement text cites design sections | carried verbatim, note in each spec's scope | awaiting developer
- F10 | Question | 00008 owns a single criterion | no edit | noted
- F11 | Non-blocking | VAL-001.9 does not exclude inline code when listing `(guess)` markers | no edit | awaiting developer

## Q12 - Citing a criterion another spec owns, finding F2 (2026-10-04)

- Question: How should a task cite a criterion that another spec owns?
  Options: cite upstream; restate shared criteria; merge until it fits; defer
  the contract change.
- Answer: "Cite upstream (Recommended)"
- Reading: one home per criterion, the most upstream spec that builds it; a
  task may cite a criterion of a spec its own spec depends on. Two criteria
  join the contract: ART-004.16 in 00006 and VAL-001.13 in 00004. Recorded as
  decision 2026-10-04 #9; F2 is resolved.
- Follow-up: whether the two new criteria join the 31-criterion list is an
  unresolved question in 00005.

## Q13 - Four small findings from the split (2026-10-04)

- Question: Which recommended fixes should I apply to the four small
  findings? Options, any number: F3, distribution branch stays dormant; F7,
  move a check to T-061; F8, T-030 owns three references; F11, scan markers
  outside code.
- Answer: "F3: distribution branch stays dormant, F7: move a check to T-061,
  F8: T-030 owns three references, F11: scan markers outside code"
- Reading: all four fixes apply. Recorded as decision 2026-10-04 #10. F3 and
  F11 are applied to the requirements drafts of 00002 and 00005; F7 and F8
  are queued for the task plans of 00001, 00009, and 00006.

## Review: split of 00001, status after Q12 and Q13 (2026-10-04)

- F2 | Blocking | resolved by decision 2026-10-04 #9
- F3 | Non-blocking | fixed in 00002 (assumption, dormant criterion)
- F7 | Non-blocking | fix queued for the task plans of 00009 and 00001
- F8 | Non-blocking | fix queued for the task plan of 00006
- F11 | Non-blocking | fixed in 00005 (VAL-001.9)
- F4, F6 | Non-blocking | additions listed for the requirements approval
- F9 | Non-blocking | no edit; the citations stay as pointers into the source design
- F5, F10 | Question | noted, no edit

## Review: requirements.md 2026-10-04

Draft generated by script from the 00001 source. Criteria, user stories,
existing `Source:` lines, assumptions, and non-functional bullets are verbatim.
Coverage across the nine drafts: 254 source criteria and 332 source lines,
each landing exactly once.

- Lenses run: completeness and integrity of the split. Not run again:
  coherence, feasibility, and evolvability of the criteria themselves, last
  reviewed 2026-10-02 to 2026-10-04 (minutes in the 00001 log).
- Completeness: 3 requirement blocks, 8 criteria owned here.
- Integrity: added, not from the source: the purpose and scope paragraphs; the `## Requirements` heading (finding F6); 2 default `Source:` lines where the source requirement had none; the pointer lines for criteria that live in other specs; the IDs `REL-002` and `REL-003` with their user stories (finding F4); the three sentences of source §9 numbered as criteria of `REL-003`.
- Open markers: 0 `(guess)` line(s), 0 unresolved question(s).
- Status: draft. Requirements approval pending; no design or tasks approval
  inferred. No `.specflow.json` exists and no validator has run.

## Q14 - Requirements approval for the nine specs (2026-10-04)

- Question: Do you approve the requirements artifacts of specs 00001 to 00009? Options: approve all, confirm ratings; approve all,
  keep guesses; approve 00002 only; I read them first.
- Answer: "Approve all, confirm ratings (Recommended)"
- Reading: the requirements artifacts of 00001 to 00009 are approved as of
  commit `b6112ad`, and the five guessed risk ratings (00002, 00003, 00004,
  00005, 00008) are confirmed. Each item's log holds its receipt.

## Requirements approval (2026-10-04)

- Artifact: `docs/dev/project-management/specs/00001-initial-delivery/requirements.md` as of commit `b6112ad`.
- Decision: approved by the developer. Question: "Do you approve the requirements artifacts of specs 00001 to 00009?" Answer:
  "Approve all, confirm ratings (Recommended)".
- Scope: the whole artifact, including the text added during conversion (listed in the review above).
- Open items this approval does not accept: none.
- This is a receipt, since no runtime exists: no canonical hash and no
  `.specflow.json`. No design or tasks approval is inferred.

## Discovery 2026-10-04

- Classification: existing code (source files `scripts/validate.py` and
  `scripts/test_validate.py`).
- Read in full: `scripts/validate.py`, `README.md`, `CONTRIBUTING.md`,
  `AGENTS.md`, `.github/workflows/validate.yml`, the designs of 00002 to
  00009. Skimmed: the developer's repository-structure plan, for where
  procedures and specs live. Not looked at: `buvis/claude-autopilot` and
  `buvis/agent-skills`, the two repositories the handoffs write into.
- D1: search `release|changelog|version`, case-insensitive, over `scripts`,
  `.github`, `plugins`, `templates`: hits are the manifest `version` field
  and its SemVer check, the template changelog, and pinned action versions.
  The repository has a changelog format and no release tooling.
- D2: the nine designs together carry every line of the source design once:
  1,203 lines carried, 3 dropped with a reason (its status, version, and date
  lines), none missing, none twice (`gen_design.py`, 2026-10-04).

## Review: design.md 2026-10-04, isolated pre-pass

- Reviewer: an isolated subagent, given the draft, the approved requirements,
  the eight source tasks with the definition of done, the sibling designs, the
  repository files, and the full cardinal-sin list.
- Pass 1: 0 cardinal sins, 1 blocker, 9 non-blockers.
- 1 | Blocker | the design's own evidence rule voids every run record of 00009, because this spec edits the package after the host runs | a staleness rule (documentation paths are safe); the schema URLs settled before 00004 is planned, else every session reruns; T-060's trial on a throwaway branch | fixed, verification requested; rests on the open decision about the schema URLs
- 2 | Non-blocking | which commit gets the tag is undefined | the tag on the commit with the report, the catch-up outputs, and the README row; tools rerun there; never moved | applied by the author
- 3 | Non-blocking | the schema-URL work names no keyword, no instance side, no resolvability check | no edit | open for the walkthrough; proposed: name the keyword, list the instance-side files, fetch the three URLs after the tag
- 4 | Non-blocking | the deterministic tests have no recorded run in the release evidence | T-063 runs the CI test commands on the clean checkout | applied by the author
- 5 | Non-blocking | the documentation tests cannot be built as named | no edit | open for the walkthrough; proposed: mark package paths in the guide, hold the example-to-fixture map in the test, a constant host list
- 6 | Non-blocking | the versioning policy leaves 0.x without a level and understates where the version lives | the 0.x rule | applied in part; the list of version-bearing files and whether install lines pin the tag are open for the walkthrough
- 7 | Non-blocking | T-065 drops the adopted-from refs in the release notes | release notes are the GitHub release and list the three refs | applied by the author
- 8 | Non-blocking | "nothing in the package names autopilot" has no check | `test_package_does_not_name_autopilot` | applied by the author
- 9 | Non-blocking | the plugin README row covers four of the six items CONTRIBUTING requires | no edit | open for the walkthrough; proposed: add skills and adapter, files and data accessed, authentication, failure behavior, and remove the unreleased line
- 10 | Non-blocking | carried framing no longer matches the split in three places | the log reference and the tree changes corrected | applied in part; principle 6 against the optional commit in a source line is open for the walkthrough
- The developer was away. Every fix is an edit to an unapproved draft and can
  be disputed at the design gate.

## Review: design.md 2026-10-04, verification pass

- Pass 2: no open blocker; the staleness rule confirmed. Two leftovers, both
  applied by the author: the error-handling line now agrees with the
  staleness rule, and T-065's outputs go into the release notes, since a file
  in the tagged commit cannot describe the tag.
- Recap for the design gate: 2 passes; 1 blocker raised and resolved; 11
  non-blockers, of which 6 are applied in full, 2 in part, and 3 are open for
  the walkthrough (bundle C of the design gates report), beside the open
  decision on the schema URLs.

## Design rulings applied (2026-10-04)

- The developer walked `reviews/2026-10-04-specflow-design-gates.md` and ruled
  on 14 decisions and 12 leftover fixes, taking the recommended option each
  time; `meta/decisions.md` records them as 2026-10-04 #12 and #13.
- Taken into this design: D13 (T-062 edits no schema) and bundle C (`$id` and the fetch after the tag; how the documentation tests are built; the version-bearing places, with install lines pinned by T-062; the six README items; principle 6). Source line 29 is reworded, with its reason in the plan.
- Found while applying C3: an install line pinned to the release tag cannot be tested by T-045 before the tag exists, so T-045 records which routes take a ref, T-062 writes the tag, and T-065's install from the tag exercises it.
- The design holds no open decision. Status: draft, approval pending.

## Check of the applied rulings (2026-10-04)

- Checker: an isolated subagent that read commit `a4c09b3` against the rulings in
  the design gates report. Over the nine designs it found 20 rulings applied as
  ruled, 2 blockers, and 10 non-blockers. The author applied every fix; the fixes
  were not read again.
- Here, 3 non-blockers: T-062's edit of `test_docs.py` has its placement row; the tree list names the two schema files of 00005; a risk line covers a pinned install line that first runs once the tag exists. The checker also noted that C3's comparison is split over three tools (the release check, the generator's check, one test) where the accepted wording said "the release check"; it judged the split sound.

## Design approval (2026-10-05)

- Artifact: `docs/dev/project-management/specs/00001-initial-delivery/design.md`, git blob `86c0019fe5618d972ea5d9fc039054b06101b248`.
- Decision: approved by the developer. Question: "Design approvals, asked one at a time; at the question for 00003 the developer answered for every design not yet approved" Answer:
  "I trust you, approving all designs".
- Scope: the whole artifact, including the choices listed under its Open
  decisions and the rulings of 2026-10-04 as applied. The 7 guessed risk ratings stay marked `(guess)` and are open for the tasks gate.
- Upstream markers accepted by name: none; the approved requirements hold no open marker.
- This is a receipt, since no runtime exists: no canonical hash, no code
  baseline, and no `.specflow.json`. No tasks approval is inferred.

## Review: tasks.md 2026-10-05

- Draft: assembled by script from the source plan in intake item 00001. Source
  bullets are carried by line; the added fields come from the approved design.
  Checked by the script across the nine plans: every source line placed once
  (427 carried, 52 reworded or retired with a reason), every criterion a spec
  holds cited by a task, every dependency an earlier task, every quoted
  contract word for word in its design.
- Reviewer: an isolated subagent, given the draft, the approved requirements
  and design, the source tasks, the task shape of 00004, and criteria
  ART-004.1 to ART-004.16.
- Pass 1: 1 blocker, 9 non-blockers, 4 questions.
- B1 | Blocker | T-066 and T-067 pushed into another repository without the developer's instruction | a `Premise:` on both: an explicit instruction, which the approval of the plan is not | resolved, confirmed in pass 2
- Non-blockers and questions: all applied by the author, but one question, left for the developer: where the merge of the feature branch falls relative to the release candidate and the tag.
- Pass 2: the blocker confirmed resolved. One new blocker, created by a fix: T-065 changed the changelog date, and so the package, after it was verified. Removed as the reviewer proposed: T-062 writes the date, and a later change of it makes a new candidate. Not verified again.
- Added by the plan beyond the approved design, to name at the gate: the release checklist asks that a change to the artifact contract, the state schema, the phase gates, or an upstream reference came with its fixtures and tests (an execution rule of the source plan that no design held).
- Design findings, not counted against the plan: 5 (items 26 and 27 of `reviews/2026-10-05-specflow-tasks-gates.md`).
- Status: draft. Tasks approval pending.

## Review: design.md and tasks.md 2026-10-05, last check

- The developer answered decision T1 of the tasks gates report with "Fix designs,
  one last check (Recommended)": the design findings are corrected in the
  designs (commit `7fa3723`), and the reviewers made one last pass over those
  edits and over the late plan fixes. The design changed after its approval
  of 2026-10-05, so that approval is stale and is asked again with the tasks.
- Design edits (findings 26 and 27): all right. The late fix to T-065 is confirmed: it changes nothing in the package after verification. No blocker. One nit applied: T-062 names the changelog heading's form.

## Design re-approval (2026-10-06)

- Artifact: `docs/dev/project-management/specs/00001-initial-delivery/design.md`, git blob `996a1f9bfd249448b88f8758655b75df98217605`.
- Decision: approved by the developer, with the task plans. Question: "Do you approve the nine corrected designs and the nine task plans of specs 00001 to 00009, accepting by name the three open questions listed above?" Answer:
  "Approve all, confirm ratings (Recommended)".
- Scope: the whole artifact as it now reads, after the corrections of decision T1 (2026-10-05) and the last check. The guessed risk ratings are confirmed, so their `(guess)` marks are gone.
- Upstream markers accepted by name: none; the approved requirements hold no open marker.
- This is a receipt, since no runtime exists: no canonical hash, no code
  baseline, and no `.specflow.json`.

## Tasks approval (2026-10-06)

- Artifact: `docs/dev/project-management/specs/00001-initial-delivery/tasks.md`, git blob `a0fa0092dd134c7ddd02da8aa125a66e4e96f844`.
- Decision: approved by the developer. Question and answer as above.
- Scope: the whole artifact, including the choices the plan makes that the design does not state (named in `reviews/2026-10-05-specflow-tasks-gates.md`).
- Upstream markers accepted by name: none; the approved requirements hold no open marker; the design's risk ratings are confirmed, so none is open.
- This is a receipt, since no runtime exists: no canonical hash and no
  `.specflow.json`. Implementation is not started by this approval.

## Obligation map 2026-10-06

- Each criterion of the source requirements -> the one spec that holds it: `reviews/2026-10-04-specflow-split-map.md` (decision 2026-10-04 #9).
- Each criterion this spec holds -> the task that builds it: the `Acceptance criteria:` lines of `tasks.md`, checked by `gen_tasks.py`.
- Each line of the source design and task plan -> the artifact that carries it, by line number, or a recorded reason for rewording: `gen_design.py` and `gen_tasks.py` (kept in the ignored `docs/dev/tmp/specflow/split/`).

## Conversion receipt 2026-10-06

- Source: docs/dev/project-management/intake/processed/specflow/00001-initial-delivery/ (`requirements.md`, `design.md`, `tasks.md` of the whole product); this spec's slice is phase 8 of the source plan.
- Destination: `docs/dev/project-management/specs/00001-initial-delivery/` (`requirements.md`, `design.md`, `tasks.md`, `.config.kiro`), with this intake item at `docs/dev/project-management/intake/processed/specflow/00001-initial-delivery/`.
- Number, type, folders: 00001, feature, requirements-first, standard profile; the specs folder is the one `.agents/specflow.json` names.
- Obligation coverage: 8 criteria held, each cited by at least one task. Every source line of this spec's slice is carried once or retired with a recorded reason (design: 1163 of 1333 carried over the nine specs, 30 retired with a reason; tasks: 427 of 574, 52 retired with a reason).
- Decisions and public-behavior changes: `meta/decisions.md`, sections 2026-10-04 (specflow split, #7 to #13) and 2026-10-05 (tasks gates, #1 to #3). No public behavior of the product changed; two carried sentences were reworded by ruling (rule area `SKL`, design principle 6).
- Implementation evidence: none. Nothing is built, and no task is checked.
- Gates: requirements approved 2026-10-04; design approved 2026-10-05 and, after 27 corrections, again 2026-10-06; tasks approved 2026-10-06. Each approval is a dated receipt in this log that names the file's git blob.
- Review outcomes: one isolated pre-pass and one verification pass per design and per task plan, with the late fixes rechecked by ruling; minutes above.
- Checks run and limits: the generators' coverage checks; an independent script that resolves every criterion ID of each design's traceability table against the spec's own requirements (0 missing); `python3 scripts/validate.py`. Limits: no specflow runtime exists, so no canonical hash, no `.specflow.json`, and no validator run; two late corrections of the task plans (00003 T-018, 00005 T-070 and T-071) were applied as the reviewers worded them and not read again; nothing was run on a host.
- Outstanding questions: none.
- Next action: implementation, in dependency order, starting with 00002 (T-001); once the helper of 00004 exists, recovery mode records these receipts as real approvals after the developer confirms each.
- Verdict: COMPLETE (8 tasks planned; implementation not started).

## Conversion summary 2026-10-06, the whole specification

The receipt above is for spec 00001's own slice. For the whole specification
this item held on 2026-10-04 (`requirements.md` v0.3 with 254 criteria,
`design.md` with 1333 lines, `tasks.md` with 64 tasks): it is now nine specs,
`docs/dev/project-management/specs/00001` to `00009`, each with its own intake
item, receipts, and approved requirements, design, and task plan; each source
criterion is held by exactly one spec, and every source line of the design and
the task plan is carried once or retired with a reason. The source files stay
here unchanged as the record. Implementation starts with 00002 (T-001).

## Deferred to T-065 (2026-10-09)

- When T-065 (the release) runs, reopen findings R6 and R18 of `reviews/00002-package-boundary-review-01.md`: the release check matches forbidden names exactly (`parity-report.md` and `evals.json` pass) and markers case-sensitively (`catch-up` passes). They were deferred because broader matching risks refusing innocent files.

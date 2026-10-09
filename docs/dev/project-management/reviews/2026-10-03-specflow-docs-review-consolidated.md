# specflow docs review, consolidated - 2026-10-03

Merges two reviews of commit `d0887aa` (specflow initial delivery spec; the
spec files are unchanged at HEAD):

- Claude: `2026-10-03-specflow-docs-review.md` (F1-F14)
- Codex: `2026-10-03-specflow-docs-review-codex.md` (C1-C12 plus its
  consolidation notes)

Both source reports stay as written. This file is the working list: how the
findings merge, what is settled, what needs a decision, and the minutes.

## Merge map

| # | Topic | Claude | Codex | Reviewers |
|---|---|---|---|---|
| 1 | A2 recorded as retired | F1, F14 | C1 | agree; settled by the user |
| 2 | Maintainer skill convention | F2 | C2 | same problem; differ on folder and links |
| 3 | Upstream updater pipeline, catch-up | F3 | C3, C4, C8, C10 (update half) | agree on catch-up skill and hand-adapted references; Claude cuts the pipeline, Codex defers it |
| 4 | Rules, evals, parity in release one | F4 | C12, C7 | disagree: thin the standard vs keep it and slice delivery |
| 5 | Host matrix | F5 | C11 | disagree: three hosts vs five with early probes |
| 6 | `.kiro/specs` link | F6 | C11 (link probe) | Claude drops it; Codex keeps it behind the probe |
| 7 | Marker gate | F11 | C5 | different angles: ledger size vs gate timing |
| 8 | Design-First creation | F7 | - | Claude only |
| 9 | Advisory review scripts | F8 | C12 (note) | agree: later |
| 10 | Shell hashing fallback | F9 | consolidation note | agree: Python only |
| 11 | Status JSON schema | F10 | consolidation note | disagree: drop vs keep |
| 12 | Hash exclusions too wide | - | C6 | Codex only |
| 13 | Concurrency promise | - | C10 (runtime half) | Codex only |
| 14 | Quick bugfix wording | - | C9 | Codex only |
| 15 | `numberScan` | F12 | - | no change asked |
| 16 | Decision docs "not yet applied" | F13 | - | hygiene |

## Evidence re-checked for this merge

Read against the spec text, not taken from either report.

- C5 confirmed: WF-002.7 blocks recording approval; T-033 refuses to start
  the design; `acceptedMarkers` sits on an approval that does not exist yet.
- C6 confirmed: design §7.3 steps 5-6 apply to every `[x]` and every
  `Outcome:`/`Exception:` list line, with no fence or position limit.
- C7 confirmed: T-064 verifies "all success measures", measure 7 is the
  parity gate, T-065 depends on T-064, and the definition of done asks for a
  parity report per retiring skill.
- C8 confirmed: T-012 verifies with the T-013 parser; T-013 depends on T-012.
- C9 confirmed: WF-003.4 vs ART-005.1.
- F2 confirmed: `AGENTS.md`, `CONTRIBUTING.md`, and `scripts/validate.py`
  hold no maintainer-skill rule. `tools/` does not exist yet; the "existing
  per-plugin tools project" in C2 is the `tools/specflow/` planned in design §3.
- F7 corrected: resuming a Kiro-made Design-First spec mid-flow still needs
  upstream-relative gates, the mirrored graph, and reversed traceability.
  Cutting creation saves only the intake order choice and the creation
  fixtures, less than F7 states.
- F4 context: one eval per behavioral rule on each host is decision
  2026-09-27 #5; design §15 already runs one session per host and scores
  many evals on it.
- F11 context: named acceptance is the Plan A ruling on RPB-53; the ledger
  shape is 2026-10-02 finding #3.
- Not re-verified: that Claude Code reads project skills only from
  `.claude/skills/` (matches the user's own link farm, not checked against
  docs today), Kiro's project skill path, and A2's activity.

## Settled in triage (applied without asking)

| # | Finding | Basis | Fix |
|---|---|---|---|
| S1 | F1, C1, F14: A2 recorded as retired | user, 2026-10-03: A1 primary, A2 kept as a tracked second source, both caught up | dated superseding decision; AWS-001, actors, design §9.4, §17, §18, T-010, README |
| S2 | C7: parity still gates the release | 2026-10-02 finding #8 decoupled them | T-064 names the release measures; measure 7 and the parity line gate T-067 only |
| S3 | C9: quick bugfix wording | ART-005.1 already decided | WF-003.4 names the requirements artifact |
| S4 | F13: decision status lines | fact: the 0.2 rewrite applied them | status lines updated |
| S5 | C3 (part): catch-up rulings in ignored `docs/dev/tmp/` | working-documents rule: reviews are tracked | rulings go under `reviews/` |
| S6 | F12: `numberScan` | reviewer asked for no change | none |
| S7 | C8, C10 (update half) | follow D1 | moot if the pipeline goes; else fixed as written |

Flagged default, not a user decision: catch-up cadence is "before each
specflow release and at least monthly" (C3 proposal). No scheduler is built.

Dropped in triage: F2 options 3 and 4 (`plugins/<name>/{plugin,maintain}`,
strip at release). Both break the repo invariant that `plugins/<name>` is the
shipped root.

## Decisions for the walkthrough

Order: upstream decisions first, then severity.

| # | Sev | Decision | Findings |
|---|---|---|---|
| D1 | High | Updater pipeline or catch-up skill | F3, C3, C4 |
| D2 | High | Maintainer skill home and discovery | F2, C2 |
| D3 | High | What gates release one: core or whole migration | F4, C12 |
| D4 | High | Host matrix for release one | F5, C11 |
| D5 | High | `.kiro/specs` link machinery | F6, C11 |
| D6 | High | Marker gate timing and acceptance ledger | C5, F11 |
| D7 | Medium | Design-First creation | F7 |
| D8 | Medium | Status JSON schema and version promise | F10 |
| D9 | Bundle | Hash exclusions (C6), concurrency contract (C10), Python-only hashing (F9), advisory scripts later (F8) | C6, C10, F9, F8 |

## Discovery coverage (added during the walkthrough)

The user asked whether specflow covers discovery well enough against
`aws-samples/sample-aidlc-discovery` (read at `a84b289`, 2026-07-02, MIT-0,
pre-release). That tool is a front door before any spec: a guided interview
that writes a Vision Document (18 questions), a Technical Environment
Document (29 questions), and pre-declared open questions. specflow's
discovery is per spec: save the idea, scan the repository, ask a short
question bank.

| AWS discovery sample | specflow | Verdict |
|---|---|---|
| Problem, users, success metrics, constraints, scope in and out, risks | Question bank Q1-Q5, Q9; Purpose, Scope, Out of scope, Risks | covered |
| Open questions handed forward | `Unresolved questions`, `(guess)`, the marker gate | covered, stricter |
| Existing-system context | repository scan; "do not ask what code can answer" (ELI-41) | covered, stronger |
| Quick or Full depth; resume from files | profiles; Q&A log | covered |
| Product vision, feature areas, deferred capabilities | none; a spec is one feature | gap, left out on purpose |
| Technical environment: required and banned stack, security, test standard | inferred from code; nothing to infer in an empty repo | gap for new projects, closed by a rule |
| "What must NOT change" | asked for bugfix specs only | small gap, closed by a rule |
| Hedged answers become open questions with a resolution path | only flat non-answers caught | small gap, closed by a rule |
| Answers taken from files cite the source | inferred answers logged, no source | small gap, closed by a rule |
| Parallel roles, batch answer files, raw-input audit log, language detection, HTML mockups | none | out by earlier decisions |

Evidence: design §9.1 listed the Intake phase's AWS source as "None";
neither A1's ideation stages nor A2's `discovery-0.1` phase was adopted.

### Second pass

The table above came from a skim: the sample's README, its core workflow,
two shared rule files, and only the headings of the two interviews. The user
said more had been missed. A full read (both question banks, both completion
gates, the question-format and validation rules, session continuity, the
visual sketch, and the v2 orchestrator, state, and handoff conventions) found
nine more gaps. It also showed the last row above was wrong: batch answer
files and parallel roles were out by earlier decisions, but language handling
and the visual sketch had never been decided.

| # | The AWS sample does | specflow before | Ruling |
|---|---|---|---|
| 1 | Saves project type, depth, and mode to state when chosen | type, order, profile written "on create"; the moment of creation was never stated | taken: WF-003.13 |
| 2 | Fails a file with an unclosed code fence | no fence check, though hashing and the placeholder scan skip fenced text | taken: VAL-001.11 |
| 3 | Lets the user upgrade Quick to Full later | profile set once at intake | taken: WF-003.14 |
| 4 | Keeps control words English, prose in the user's language | no language rule | taken: ART-001.11 |
| 5 | Records answers verbatim with caveats, agent notes apart; append-only history with correction entries | "appended after the answer", nothing on wording or changed answers | taken: INT-001.5, SEC-002.2 |
| 6 | Asks how to learn about an existing system outside the workspace | only the repository is scanned | taken: WF-003.11 |
| 7 | Every ban has a reason and an alternative; asks for an example to imitate | bans only | taken: WF-003.12 |
| 8 | Progress line: section, answered count, time left | none | taken: ART-002.14 |
| 9 | Optional user journey and static mockups | none; the spike is the nearest | taken as a spike form: INT-002.8 |

Rows 2 to 9 were confirmed absent by search with a known-hit control. Row 1
was an ambiguity, not a proven loss: the phase table implied the folder
existed before the first document, but no rule said when it was made.

Looked at and left out, with reasons: stable IDs for unresolved questions
(the marker ledger matches exact lines on purpose), an approval line in the
Q&A log for recovery (state stays the one authority on approvals), and team
size as a design input (a solo developer).

### A1 full read

The spec adopts text from five of A1's 33 stages and had taken nothing from
the phases before inception. At the user's go-ahead, twelve unadopted stages
were read in full at `v2.10.0` (`2a883858`): ideation (`intent-capture`,
`market-research`, `feasibility`, `scope-definition`, `team-formation`,
`rough-mockups`, `approval-handoff`), initialization (`workspace-scaffold`,
`workspace-detection`, `state-init`), and from inception
`practices-discovery` and `reverse-engineering`. Each gap below was confirmed
absent from the spec by search with a known-hit control.

| # | A1 does | specflow before | Ruling |
|---|---|---|---|
| 1 | Records what a scan read deeply and what it skimmed; fixed rules for "existing code" that ignore agent folders and look into nested projects | no coverage statement; "empty repo" undefined though WF-003.12 hinges on it | taken: WF-003.15, WF-003.16 |
| 2 | Every claim carries a source tag; unsourced content is an assumption; an unpicked option decides nothing; assumptions confirmed before the gate | one `Sources:` line per document; summary lists decisions and risks only | taken: ART-002.15, WF-002.1, VAL-001.12 |
| 3 | Loads standing rules at every stage | "repository steering" read in the design phase only; each host loads a different file | taken: WF-003.17 |
| 4 | Checks existing tools and open-source options | reuse search covers the repository only | taken: ART-003.12 |
| 5 | Stamps discovery with a commit; flags stale knowledge | no commit recorded | taken: WF-004.8, STATE-001.2 |
| 6 | "Not yet defined" on every question; terms defined in the question; answers played back before drafting | "Other" and recommended-first only | taken: ART-002.16-18 |
| 7 | Confirms working practices: test order, thin slice first | inferred per spec; asked only in an empty repo | taken, against the recommendation: WF-003.18 |
| 8 | Tracks dependencies between pieces of work | `Blocks:` and `Supersedes:` only | taken: ART-002.11, WF-001.9, STATE-003.1 |
| 9 | Saves confirmed practices for later work | re-derived per spec | rejected: specflow does not edit files it does not own |
| 10 | Mockups ask for a design system and accessibility level; a note per screen | the sketch spike had neither | taken: INT-002.8 |
| 11 | An input document needs one explicit path | "an idea or a file path" | taken: INT-001.8 |

Left out, with reasons: stakeholder maps and team formation (solo developer;
A1 skips team formation for solo work), market sizing and competitor analysis
(product level, non-goal 10), the go/no-go brief (the approval summary and
hold cover it), backlog scoring (no tiers, `qa-log.md` Q5), multi-repo work,
and the shared knowledge base's locks and fingerprints (engine machinery).

Not read: A1's other sixteen unadopted stages (inception: `user-stories`,
`contract-design`, `delivery-planning`, `refined-mockups`; construction:
`functional-design`, `nfr-requirements`, `nfr-design`,
`infrastructure-design`, `ci-pipeline`; operation: all seven). The five
adopted stages were not re-read in this review either.

## Decisions (2026-10-03)

All twelve were answered by the user in the walkthrough. They are recorded,
numbered, in `meta/decisions.md` (section 2026-10-03), and the spec cites
them as "decision 2026-10-03 #n". The minutes below map each finding to its
decision.

## Minutes

| # | Finding | Decision | Status |
|---|---|---|---|
| S1 | F1, C1, F14: A2 recorded as retired | decision 1 | applied: requirements §1, §2, §4, AWS-001; design §1, §9.4, §17, §18; tasks T-010; README |
| S2 | C7: parity still gated the release | settled by 2026-10-02 #8 | applied: requirements §8; tasks T-064, definition of done |
| S3 | C9: quick bugfix wording | settled by ART-005.1 | applied: WF-003.4 |
| S4 | F13: decision status lines | user: fold into `meta/decisions.md` | applied: both files merged into the keeper with status and superseded notices; citations repointed |
| S5 | C3: catch-up reports under ignored tmp | working-documents rule | applied: UPD-002.4, design §11.3 |
| S6 | F12: `numberScan` | no change asked | no change needed |
| S7 | C8, C10 (update half) | moot after decision 2 | T-012, T-013, T-017 withdrawn |
| D1 | F3, C3, C4: updater pipeline | decision 2 | applied: AWS-001, AWS-002, UPD-001, UPD-002, UPD-003 withdrawn, SEC-001, REL-001.3/.5; design §3, §4.3, §9.4, §10, §11, §13-§17; tasks Phase 2 |
| D2 | F2, C2: maintainer skill home | decision 3 | applied: UPD-001.1/.7; design §3, §11.1; tasks T-018 |
| D3 | F4, C12, F8: release gate | decision 4 | applied: requirements §8, §9, RULE-001.5; design §5.4, §5.5, §15, §16; tasks T-070, T-075, T-076, T-077 (new), T-056 to T-058, T-063, T-064, T-067 |
| D4 | F5, C11: hosts | decision 5 | applied: PKG-003; design §12, §15, §16; tasks T-006 (new), T-041 and T-044 withdrawn, T-045, T-051, T-056, T-064 |
| D5 | F6, C11: specs link | decision 6 | applied: ART-001.8, INT-001.1/.7, SEC-002.5, VAL-001.8; design §5.1, §5.3, §6.1, §6.7, §13, §14, §17; tasks T-027, T-028 |
| D6 | C5, F11: marker gate | decision 7 | applied: WF-002.7; design §7.6, §13; tasks T-033 |
| D7 | F7: Design-First creation | decision 8 | rejected, no edit |
| D8 | F10: status schema | decision 8 | rejected, no edit |
| D9 | C6, C10, F9: small fixes | decision 9 | applied: WF-002.4, WF-006.4, VAL-002.5, portability; design §5.3, §7.1, §7.3, §13, §15; tasks T-022, T-025, T-026, T-053 |
| D10 | discovery coverage (user request) | decision 10 | applied: non-goal 10, WF-003.11-12, ART-002.12-13; design §5.4, §9.1, §9.2, §9.4; tasks T-031, T-032 |
| D11 | discovery, second pass (user: "more things we missed") | decision 11, all eight taken | applied: ART-001.11, ART-002.14, INT-001.5, INT-002.8, WF-003.11-14, VAL-001.11, SEC-002.2; design §6.1, §6.5, §6.7, §6.8, §7.1, §7.3, §9.4, §13, §15; tasks T-030, T-031, T-032, T-071, T-072 |
| D12 | A1 full read of twelve unadopted stages (user: "good idea, do that") | decision 12: ten taken, one rejected | applied: ART-002.11, ART-002.15-18, ART-003.12, INT-001.8, INT-002.8, WF-001.9, WF-002.1, WF-003.15-18, WF-004.8, STATE-001.2, STATE-003.1, VAL-001.8, VAL-001.12; design §6.2, §6.3, §6.4, §6.7, §6.8, §7.1, §7.6, §9.4, §10.1, §13, §15; tasks T-020, T-021, T-026, T-029, T-031 to T-034, T-071, T-072 |
| - | F2 sub-item: maintainer-skill example in `templates/` | not carried | no change needed: under decision 3 the skill lives at the repo root, and T-018's skill is the example |

Spec files are at version 0.3. Check after the edits: task and requirement
cross-references resolve (62 tasks, 30 requirements, every requirement has a
task), proven against a seeded-defect copy.

### Open after the walkthrough

- **`decisions/` folder: closed.** The autopilot plugin's layout hook
  (`enforce_prd_location.py`) allows decisions only as `meta/decisions.md`
  and blocked edits under `docs/dev/project-management/decisions/`. The user
  chose to fold the two files there into the keeper. Done: `meta/decisions.md`
  holds 2026-09-27, 2026-09-28 (with the superseded notices), and 2026-10-03;
  the old files are removed and seven citations repointed, including one link
  in the Codex report.
- **Catch-up cadence** (before each release and at least monthly) is a
  default from the Codex review, flagged in the spec as unconfirmed.
- **Note for the repo-structure plan**, not for specflow: its copy fallback
  is unsafe for `.kiro/specs`, since Kiro writes there and writes into a copy
  never reach the real folder; that projection needs a link or junction. Its
  folder set (`prds/`, `specs/`, `research/`, `dev/work/`) also has no
  `intake/` or `reviews/`, which specflow creates under its configured root.
- **Unverified claims carried into the spec as such:** Kiro IDE listing
  specs through a `.kiro/specs` link (T-027), and Claude Code's project
  skill discovery path (the reason the maintainer skill needs a projection
  or a "read this file" instruction).

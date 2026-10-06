# Tasks: Portable Spec Workflow Plugin

Status: Draft  
Version: 0.3  
Date: 2026-10-04

## Execution rules

- Complete phases in dependency order.
- Do not check a task until its verification succeeds.
- Preserve the separation between `plugins/specflow/` runtime content and repository-only maintenance content.
- Treat the requirements and design documents beside this file as authoritative.
- Any change to the artifact contract, state schema, phase gates, or distributed upstream reference requires corresponding fixtures and compatibility tests.
- Write phase and review references from the rule inventory (T-070), never from the source skills directly.
- Release 0.1 includes all accepted capabilities and planned checks (requirements §9). Area checks support incremental construction; the release runs the complete inventory, host evals, and parity gates without exemptions.
- Finish the host loading probe (T-006) before Phase 3 starts; a host that fails it is fixed or leaves the supported list first.
- Create each reference's named validator checks and substantive per-rule eval records, in the T-069 formats, with that reference; T-057 completes the scenario set and runs it on every supported host.
- For each decision criterion a reference implements, maintain its inventory mapping and assertions under design §5.4; cover all its obligations, using shared rules or structural/behavioral splits as needed. Keep the required-criterion list independent of those mappings.
- T-070 builds the Plan A inventory baseline. T-079 completes the approved Plan B mappings and references after the design/tasks/review baseline exists; an earlier area check proves only the rows then listed, not full Plan B coverage. T-057 waits for T-079 before running the full eval set.
- The conversion skill's `CNV` rules are authored by T-080 from the conversion contract (not a port plan); they carry their own checks and evals and join the unfiltered `check_rules.py` release gate (T-063).

## Phase 1: Repository and package boundary

- [ ] **T-001 Create the repository skeleton**
  - Requirements: PKG-001, PKG-002
  - Depends on: none
  - Create `plugins/specflow/`, `.agents/skills/`, `tools/specflow/`, `tools/specflow/upstream/`, `tests/specflow/`, and `docs/dev/tmp/specflow/` ownership boundaries.
  - Add repository documentation stating that `plugins/specflow/` is specflow's only distributable root.
  - Verify: a tree assertion test identifies `plugins/specflow/` as specflow's only distributable root.

- [ ] **T-002 Define the portable root manifest**
  - Requirements: PKG-001, PKG-003, REL-001
  - Depends on: T-001
  - Add `plugins/specflow/plugin.json` targeting Agent Plugins v1.
  - Use a placeholder-free final plugin identity, version, description, license, repository, and activation keywords.
  - Verify: validate against the published Agent Plugins v1 schema.

- [ ] **T-003 Add the Claude compatibility manifest**
  - Requirements: PKG-003
  - Depends on: T-001, T-002
  - Add `plugins/specflow/.claude-plugin/plugin.json` referencing the shared root `skills/` directory.
  - Keep workflow logic out of the compatibility manifest.
  - Verify: Claude Code plugin validation passes and the skill is namespaced as expected.

- [ ] **T-004 Implement release verification**
  - Requirements: PKG-002, REL-001
  - Depends on: T-001
  - Add `tools/specflow/verify_release.py`, which checks `plugins/specflow/` in a clean checkout of a candidate commit.
  - Reject symlink escapes and unexpected generated files.
  - Verify: a clean fixture passes; each seeded defect fails with a targeted message.

- [ ] **T-005 Add forbidden-content release checks**
  - Requirements: PKG-002, UPD-001, REL-001
  - Depends on: T-004
  - Reject `.agents/`, the catch-up skill's name, source cursors, catch-up reports, tests, the rule inventory, `check_rules.py`, evals, parity reports, `docs/dev/tmp/specflow/`, and Git metadata in `plugins/specflow/`.
  - Verify: seeded forbidden fixtures each fail with a targeted message.

- [ ] **T-006 Probe host loading**
  - Requirements: PKG-003
  - Depends on: T-002, T-003
  - Build a throwaway probe package under `docs/dev/tmp/specflow/probe/`: the two manifests, one skill that reads one bundled reference and writes one fixture artifact, and that reference. Nothing from the probe is committed to `plugins/specflow/`.
  - Load it in Kiro IDE, Codex, and Claude Code following each design §12 Install line; in each host run the skill, then resume the fixture another host wrote.
  - Record the working install path and any limit per host, and correct design §12 to match.
  - Verify: each supported host loads the skill, reads the reference, and writes the fixture, and one other host resumes it; a host that fails is reported with the failing step before any Phase 3 task starts.

## Phase 2: AWS sources and the repository-only catch-up skill

T-012, T-013, T-015, T-016, T-017, and T-019 are withdrawn with the updater pipeline (decision 2026-10-03 #2). Their identifiers are not reused.

- [ ] **T-010 Record the AWS sources**
  - Requirements: AWS-001, UPD-002, SEC-001
  - Depends on: T-001
  - Pick the latest `awslabs/aidlc-workflows` release tag (`vX.Y.Z`) and peel it to its commit (design §10.1); record the current commits of A2 and A3.
  - Write the source record in `aws/adaptation.md` (role, adopted-from ref, and license per source), the profile-to-depth mapping (AWS-002.5), and what is not adopted from each source (design §9.4).
  - Write `tools/specflow/upstream/sources.md` with one cursor per source (design §11.2).
  - Verify: the A1 tag resolves to the recorded commit; the A2 and A3 commits exist upstream; every source in the record has a cursor row.

- [ ] **T-011 Add license and attribution**
  - Requirements: AWS-001, REL-001
  - Depends on: T-010
  - Put the license of every source that text is copied from in `aws/LICENSE`.
  - Add provenance to plugin documentation.
  - Verify: release validation fails when the source record, attribution, or a license is missing.

- [ ] **T-014 Adapt the AWS references by hand**
  - Requirements: AWS-001, AWS-002
  - Depends on: T-010, T-011
  - Write `aws/{requirements,design,implementation,verification}.md` from the A1 adoption set (design §10.1), each adopted passage under a source line with its profile mark, and each local line marked as adaptation (design §10.2).
  - Leave engine plumbing out (design §9.4).
  - Verify: every source line names a source and ref in the source record; no reference contains `{{HARNESS_DIR}}`, `{{INVOKE}}`, `aidlc engine`, or `[Answer]:`.

- [ ] **T-018 Create the repository-only catch-up skill**
  - Requirements: UPD-001, UPD-002, SEC-001
  - Depends on: T-010
  - Add `.agents/skills/catchup-specflow-upstream/SKILL.md` with the sequence of design §11.3: review and report by default, edits to runtime references only on explicit instruction, no commit.
  - State the maintainer-skill convention in `AGENTS.md` and `CONTRIBUTING.md` (UPD-001.7), and make `scripts/validate.py` check `.agents/skills/*/SKILL.md` with its existing skill rules.
  - Run the first catch-up over A1, A2, and A3 and write its report under `docs/dev/project-management/reviews/`.
  - Verify: the validator passes on the skill and fails on a seeded malformed one; release-boundary tests prove the skill is absent from `plugins/specflow/`; the first report holds a ruling or a "nothing to adopt" line per source, and the cursors match it.

## Phase 3: Runtime artifact and state contract

- [ ] **T-027 Capture Kiro-native spec samples**
  - Requirements: ART-001, WF-001, WF-005
  - Depends on: none
  - Generate a feature Requirements-First, a feature Design-First, and a bugfix spec with Kiro, including tasks with checked boxes. The bugfix capture is a synthetic bug in a throwaway project in this repo, run through all four tasks.
  - Record the exact file set (including `.config.kiro`), headings, ID numbering, and task syntax, and store the captures as fixtures.
  - Compare the bugfix capture with the public references in `discovery/00001-specflow-bugfix-workflow.md` (cited, not copied); record variants such as Bug Condition placed in `bugfix.md`.
  - Open a specflow-written bugfix spec (with `.config.kiro`) in Kiro IDE and record whether it shows as a Bug Fix spec.
  - Point `.kiro/specs` at a folder elsewhere in the repository with a symbolic link (macOS); record whether Kiro IDE lists, opens, and watches those specs, and whether it ignores `.kiro/specflow/`.
  - Verify: design §6.5-§6.7 match the captures, or are corrected before T-020 starts; the link result is recorded for the host documentation (T-045), and if Kiro does not list specs through a link, a configured specs folder is documented as invisible to Kiro's spec panel.

- [ ] **T-020 Define canonical Markdown templates**
  - Requirements: ART-001, ART-002, ART-003, ART-004, ART-005, INT-001, INT-002, REV-001
  - Depends on: T-001, T-027
  - Create templates for requirements, design, and tasks, and the bugfix set `templates/bugfix/{bugfix,design,tasks}.md` in the §6.6 shape (ART-005).
  - Include stable IDs, traceability, verification, and unresolved-question sections; the `Sources:`, `Supersedes:`, `Blocks:`, and optional spec-level `Depends on:` lines (feature header and bugfix Introduction, design §6.2); a `Source:` line under each requirement; `## Risks` in requirements and `## Risks and edge cases` in design; `Premise:` in tasks.
  - Add `templates/intake/` (`idea.md`, `qa-log.md`, spike `SPEC.md`) and `templates/cross-spec-review.md`.
  - Keep templates valid plain Markdown without required proprietary frontmatter.
  - Verify: representative standard and quick specs, feature and bugfix, render and validate; the bugfix templates match the T-027 capture's headings; fixtures place optional prerequisite lists correctly without changing native headings or IDs in either workflow order; no template contains a placeholder that ART-001.10 bans.

- [ ] **T-021 Define the state JSON Schema**
  - Requirements: STATE-001, STATE-002
  - Depends on: T-020
  - Define version, spec ID, spec type, profile, workflow order, workflow version, artifact records (path, status, hashes, approval timestamp, optional approved commit, design `approvedCode` baseline, accepted upstream markers per design §7.1), and the optional hold (status, reason, date). Baseline variants are captured file hashes/absence, not checked with a reason, or explicitly not applicable; older state without the field remains readable. Phase is derived, never stored.
  - Forbid secrets, transcripts, absolute paths, and host session identifiers by contract and tests.
  - Define forward-compatible handling for unknown fields.
  - Verify: valid fixtures pass; malformed types and unsupported versions fail safely.

- [ ] **T-022 Implement hash and approval semantics**
  - Requirements: WF-002, STATE-001, STATE-002
  - Depends on: T-021
  - Use SHA-256 over the canonical text defined in design §7.3.
  - Bind approval to `approvedSha256` and timestamp. Record optional commit provenance and capture the design's code baseline from current working files per design §7.1; reapproval replaces that baseline without committing or requiring a clean tree. Missing evidence is recorded as not checked, not a failed approval or invented clean baseline.
  - Never infer approval from file existence or phase progression.
  - Verify: content edits invalidate approval; line-ending, trailing-whitespace, final-newline, task and completion checkbox, and a task's own `Outcome:`/`Exception:` line changes do not; a `[x]` edit inside a fenced command and an `Outcome:` line outside a task item each invalidate approval.

- [ ] **T-023 Implement dependency invalidation**
  - Requirements: WF-002, WF-005, STATE-002
  - Depends on: T-022
  - Encode the invalidation graph of design §7.4 for both workflow orders, read from `workflowOrder`.
  - Propagate stale status without altering document content.
  - Close implementation gate when tasks or an upstream artifact are stale.
  - Verify: table-driven tests cover every change and downstream result in both orders.

- [ ] **T-024 Implement reconciliation and recovery rules**
  - Requirements: WF-004, WF-005, STATE-002
  - Depends on: T-021, T-023
  - Handle missing state, missing artifacts, malformed state, unknown versions, and native-Kiro documents, including bugfix and Design-First specs (design §6.5).
  - Infer only objective facts; ask for the first ambiguous approval one question at a time.
  - Preserve malformed state for diagnosis.
  - Verify: recovery fixtures resume without overwriting valid content.

- [ ] **T-025 Implement optimistic concurrency checks**
  - Requirements: WF-006, SEC-002
  - Depends on: T-022
  - Capture starting hashes before edits and compare immediately before write.
  - Stop on unexpected changes and show affected paths.
  - Verify: an edit made between an operation's read and its write is detected and not overwritten.

- [ ] **T-026 Implement the optional validator helper**
  - Requirements: VAL-001, VAL-002, STATE-003, WF-001, WF-004
  - Depends on: T-020, T-021, T-023, T-024
  - Implement status, validate, hash, read-only code-baseline capture, and reconcile dry-run commands using the Python standard library (design §5.3/§7.1).
  - Return the exit codes of design §5.3 (0 success, 1 validation failure, 2 state error, 3 usage error) and optional JSON output; `status --json` follows `schemas/specflow-status.schema.json` (design §7.6), for one spec or all.
  - Without Python 3 the skill runs read-only and names the prerequisite (design §5.3).
  - Implement the spec-dependency grammar, reachable-graph validation, read-only prerequisite reconciliation, and implementation-only gate of design §6.2 (WF-001.9). Keep spec dependencies distinct from task-local fields; share this contract with the agent. In Git repositories compare declared working-file hashes/existence with the design's `approvedCode` baseline (WF-004.8), keeping drift and not-checked diagnostics advisory.
  - Verify: CLI contract tests cover success, validation errors, state errors, and unsupported versions; status JSON validates against its schema, lists blockers, warnings, and `nextTask` per design §7.6, and offers no way to record an approval. T-022/T-026 fixtures jointly cover every code-drift case in design §15, including dirty approval/reapproval at the same HEAD, added/deleted/untracked files, native placement, missing history, older state, unavailable evidence, and containment; no drift warning closes a gate or rewrites files, and this check is omitted without Git.
  - Verify dependencies: deterministic fixtures cover every spec-dependency case in design §15, including native/numbered lists, both artifact shapes and orders, stale prerequisites, invalid declarations/targets/state, self-reference and cycles. Assert exact reference/reason or cycle path, null `nextTask` while blocked, unchanged earlier gates/phase/approval records, phase-filtered validation, read-only reachable traversal, and no unrelated content reads. Completing all direct prerequisites opens implementation only when its other gates pass; a valid complete direct prerequisite remains complete after a transitive prerequisite becomes incomplete.

- [ ] **T-028 Implement the workspace config and the specs folder**
  - Requirements: INT-001, ART-001, SEC-002
  - Depends on: T-026
  - Define `schemas/specflow-config.schema.json` for `.agents/specflow.json` (`root`, `specsDir`, `numberScan`), with defaults when the file is absent.
  - Resolve the specs folder from the config once and use it for every read and write; create, repair, or require no `.kiro/specs` link (design §6.7).
  - Refuse a configured path that is absolute, holds a `..` segment, or resolves outside the repository, before any use (SEC-002.5).
  - Report specs left in a real `.kiro/specs/` folder while `specsDir` names another folder, and fail `status` and `validate` when the specs folder is one git ignores (design §6.7).
  - Verify: fixtures cover no config, a configured root, a configured `specsDir`, each refused path, a `.kiro/specs` path that resolves outside the repository, specs left beside a configured folder, and an ignored specs folder.

- [ ] **T-029 Implement spec numbers and intake items**
  - Requirements: INT-001, ART-001, VAL-001
  - Depends on: T-026, T-028
  - Add `next-number`: a recursive scan of `<root>/intake/`, `.kiro/specs/`, and every `numberScan` folder, a re-scan after writing, and a rename of the agent's own new item on a clash.
  - Create intake items (`idea.md` verbatim, `qa-log.md`), move them to `processed/` before the requirements artifact is first written so `Sources:` names the `processed/` path, and create the fallback `qa-log.md` for a spec with no item.
  - Take a file input only from one explicit path, ask when it is missing or ambiguous, and copy it into the intake item, or record its location when it is binary, too large, or outside the repository (INT-001.8).
  - Validate clashes as design §6.7 defines them (two items or two specs with one number, or a `Sources:` line naming another number), the `Sources:` line, and Kiro-native folders without numbers. Integrate T-026's dependency resolver with the configured specs folder and existing number resolution; do not resolve against intake items or rename native specs.
  - Verify: fixtures cover an empty repo, grouped intake folders (with the group kept on the move to `processed/`), an item and spec with different titles (no clash), each clash kind, a Kiro-native spec, a missing `Sources:` line, missing/ambiguous numbered dependencies, exact native folder references in a configured specs folder, an intake item without a matching spec (not a prerequisite target), and a file input whose name matches two files (asked, not guessed).

## Phase 4: Behavior rules and runtime skill

- [ ] **T-070 Encode the behavior rule inventory**
  - Requirements: RULE-001
  - Depends on: T-001
  - Turn every approved port and redesign row of Plan A, including the drops ruled redesign, into numbered `SR-<area>-NNN` rules routed by the table in design §5.4; split a row with structural and behavioral parts into two rules.
  - Write `tools/specflow/rules/inventory.json` (rule, file, kind, check, sources, optional criteria; no rule text), the independent `criteria.json` with exactly the initial 31 IDs in design §5.4, and `tools/specflow/check_rules.py` with its port-row, required-criterion, and rule/file/check failure conditions. Add an `--area` option under §5.4's construction limits. No slice exemptions.
  - Include `RVX` and advisory-script rules in the full release check; accept a `D:<date>#<n>` source for a rule that comes from a decision (design §5.4).
  - Map every required criterion to planned rule IDs and their existing check references, preserving original decisions and later rulings as sources; print criterion → rule → check coverage rows. Do not infer the required set from inventory entries or count a decision source as coverage.
  - Wire the check into maintainer CI.
  - Verify: checker fixtures map every approved Plan A row and no struck/drop row; seeded unmapped rows, absent checks/files, and duplicated IDs fail. The required set matches all 31 IDs in design §5.4. Removing a whole criterion mapping while keeping its decision source, removing its check, omitting the list, or adding duplicate/unknown IDs fails with a targeted error. Shared rules and mixed-kind splits pass. Area filtering skips only other areas' runtime-file/check existence, not missing criterion mappings; unfiltered runs also reject missing cross-spec/advisory files and checks. Full-tree coverage gates T-063 after all references exist.

- [ ] **T-071 Add validator checks for the structural rules**
  - Requirements: RULE-001, VAL-001, ART-001, ART-002, WF-002
  - Depends on: T-026, T-070
  - Add a named validator check for each structural rule in the inventory, including placeholders per artifact and the `Not applicable: <reason>` form (ART-001.10), the marker list for the WF-002.7 gate (VAL-001.9), the path and wiki-link warnings (VAL-001.10), the unclosed-fence failure (VAL-001.11), and the missing-`Source:` warning (VAL-001.12).
  - Tag each structural rule's text with its ID in `validation-rules.md` (area `VAL`) unless a phase reference already carries it.
  - Verify: `check_rules.py` finds every structural rule's check and `--area VAL` passes; seeded defects fail each check with file, rule, and fix; an artifact with an unclosed fence fails and cannot be approved; warnings never change the exit status.

- [ ] **T-069 Define the session and eval formats**
  - Requirements: RULE-001
  - Depends on: T-070
  - Define the formats of design §15: a session (`tests/specflow/evals/sessions/<name>.json`, a fixture repository plus scripted developer turns) and an eval (`tests/specflow/evals/SR-<area>-NNN.json`, one rule's assertions over one named session), with deterministic assertion kinds by default and a marked rubric kind.
  - Write one JSON Schema and one example of each; every later reference task writes its eval records in these formats.
  - Verify: both examples validate against their schemas; `check_rules.py` resolves an `evals/<rule-id>.json` check only to a file that validates; a malformed eval record fails with a targeted message, also through a required-criterion mapping. Several criteria may share a rule's eval without requiring extra host-session runs.

- [ ] **T-030 Author the compact runtime skill and shared dialogue contract**
  - Requirements: PKG-001, ART-001, ART-002, INT-001, SEC-002, WF-001, WF-002, WF-004
  - Depends on: T-020, T-021, T-014, T-069, T-070
  - Define activation and every intent of design §5.1 (T-076 completes `review specs`), phase sequencing, approval gates (including WF-002.7-9), hold handling, reconciliation, and reference routing (design §5.2).
  - Carry the `SKL` rules (intents and triggers of the folded skills).
  - Author the shared-dialogue section of the existing `artifact-contract.md` as `DLG` rules, covering exactly design §5.2; retain each port/decision source and add `D:2026-10-03#14`, plus `D:2026-10-04#1` for the narrowed playback confirmation and `D:2026-10-04#2` for caveat handling. Load the shared contracts on every invocation before questions or approval summaries, including intake, Design-First and direct reviews. Keep one runtime copy; phase/review references point to it.
  - Keep host-specific invocation syntax out of normative instructions.
  - State the language rule: structure in English, prose in the developer's language (ART-001.11).
  - Ensure create and resume always inspect existing files first.
  - At design approval in a Git repository, supply its explicit placement file paths to `code-baseline` and record the returned evidence with that approval; ambiguous/missing placement records not checked, and an explicitly no-file design records not applicable with its reason. Resume never refreshes this baseline without reapproval (WF-004.8).
  - Verify: skill validator passes, instruction-size budget is met, and `check_rules.py --area SKL` passes; a fixture session held in another language yields artifacts whose headings, IDs, field names, and EARS keywords are English and pass validation.
  - Verify shared dialogue: `check_rules.py --area DLG` passes; author the shared-session eval records of design §15, covering fresh-context intake/Design-First/review entry, hedged and inferred answers, verbatim append-only corrections, progress, undecided choices, plain-language/first-use definitions, conditional playback confirmation (ART-002.18), and all three artifact approval summaries retaining assumptions. Include recap-and-draft after clear answers, combined confirmation, and a separate stop for a later material interpretation/conflict; no implicit marker acceptance. Assert a synthetic secret never reaches persisted artifacts/log/state and its omission is noted. Record authoring, deterministic routing checks, and full host runs all gate release 0.1.
  - Verify caveats: author the shared-session cases of design §15 for settled current behavior with a later follow-up, mixed settled/uncertain content, ambiguous wording, and a future decision affecting the current spec. Assert verbatim preservation, only the genuinely uncertain part marked with a resolution path, and unchanged named-acceptance behavior for unresolved or "not decided yet" answers.

- [ ] **T-031 Implement intake, spec type, and profile selection instructions**
  - Requirements: WF-003, ART-001, INT-001
  - Depends on: T-029, T-030
  - Write `phases/intake.md` from the `INT` rules: save a free-text idea as an intake item first, read the input in the order argument, intake item, existing spec, conversation, and run repository discovery (pattern scan, dependency map, conventions, integration surface) by profile.
  - Point to the shared dialogue in `artifact-contract.md`; intake questions use it before any requirements reference loads. Keep discovery and profile-specific question content here.
  - Recommend the spec type (feature or bugfix) and the workflow order (`requirements-first` by default, `design-first` when the input is a design decision) with their basis; allow override before the first artifact (WF-003.8, WF-003.10).
  - For bugfix, collect reproduction steps, current behavior, expected behavior, and constraints, asking only for missing items, one at a time.
  - Apply the shared intake budget of WF-003/design §9.2, sourced `D:2026-10-04#1`: read available input and instructions before questioning, reuse known answers, and ask material unknowns across all topics without resetting the count. Establish preservation, outside-system context, and binding constraints (WF-003.11-12); reuse an example or ask when it would materially guide the work. Before quick exceeds its usual range, explain and propose standard; honor a quick override through agreed extra questions, scope reduction, or explicit deferral under existing marker gates.
  - Create the spec folder with `.config.kiro` and `.specflow.json` when the developer confirms type, order, and profile, before the first question of the first artifact (WF-003.13). Allow raising `quick` to `standard` later, and propose it when a WF-003.6 trigger appears after intake (WF-003.14). These four are rules sourced `D:2026-10-03#10` and `D:2026-10-03#11`.
  - Classify the repository by the fixed rule of design §6.7 and log a `## Discovery` block with the basis and the coverage: read in full, skimmed, not looked at (WF-003.15, WF-003.16). Read root and applicable scoped instructions on every host, follow declared routing/precedence, and record constraints with their file and scope; revisit applicability as affected paths become known or change (WF-003.17, design §6.7). Ask about test order and a thin end-to-end slice only when nothing shows them (WF-003.18). These are rules sourced `D:2026-10-03#12`; instruction applicability also cites `D:2026-10-04#5`.
  - Write `.config.kiro` and mirror `specType` in `.specflow.json` on create; resolve type on read per ART-001.7.
  - Recommend `quick` only when requirement clarity, scope breadth, codebase impact, and problem complexity are all low (WF-003.5); force standard for every WF-003.6 trigger unless the developer explicitly decides otherwise.
  - Verify: scenario tests select the expected spec type, workflow order, and profile and always retain all three artifacts; a disagreeing `.config.kiro` is reported, not rewritten; a feature on existing code records what must not change, a dependency outside the repository draws the "how to learn about it" question, and an empty repository draws the constraint questions with a reason and alternative per ban; a second host resuming right after the choices are confirmed finds them in state; a late WF-003.6 trigger draws a proposal to raise the profile, and the raise stales nothing; a repository holding only agent folders and a README classifies as empty and one with a nested project does not; the discovery block names what was skimmed and what was not looked at; a hard rule in `AGENTS.md` reaches the constraints on a host that does not load that file by itself; `check_rules.py --area INT` passes for the intake rules.
  - Author the intake assertions of the shared working-practices session (design §15): supplied preferences are reused; missing preferences are asked and logged for T-034's task-order assertions. Reuse T-030's session for the shared-dialogue checks instead of duplicating its rules.
  - Verify the combined-intake cases of design §15: zero questions for supplied facts, one shared count across topics, a third material unknown prompting a profile proposal, both profile responses, and no hidden questions or implicit answers. Intake-choice confirmation can carry playback; a later material interpretation still needs a response. Keep these as assertions on shared sessions, run on every supported host before release 0.1.
  - Verify instruction applicability with the scoped session in design §15: root imports, disjoint local rules, declared overrides, inactive conditional/explicit-only rules, genuine same-scope conflicts, unknown paths followed by scope expansion, and unreadable applicable files. Check file/scope citations and the read trace; no unrelated local rule becomes global and no irrelevant conflict adds a question. Carry the changed WF-003.17 mapping and checks under the existing INT rule.

- [ ] **T-072 Implement the spike path**
  - Requirements: INT-002, INT-001
  - Depends on: T-031
  - Add the spike section of `phases/intake.md` from the spike rules (design §6.8): entry points, rough spec, build location and branch, suspended gates with the safety rules kept, report, the three choices, graduate, discard, and cleanup at `complete`, plus the sketch form: user journeys and one static mockup per unique screen, with shared-screen reuse, a navigation-only index, actual action links, and terminal screens. Reuse known UI/accessibility context, share the spike question budget, and retain an accessibility note per screen (INT-002.8, sourced `D:2026-10-03#11`, `D:2026-10-03#12`, and `D:2026-10-04#6`).
  - Verify: scenario fixtures cover a standalone spike, a branch spike with a dirty tree, refine, graduate (`Sources:` names the spike, item moves to `processed/`), and discard. Own the sketch session's structural and dialogue assertions in design §15: unique-screen correspondence across journeys, index exclusion, terminal screens, correct action links, disclaimers and accessibility notes, no scripts/network resources, known-answer reuse, and the phrase-only one-question limit with explicit remaining guesses/open questions. Include malformed-output fixtures for missing/orphan screens and wrong links; `check_rules.py --area INT` passes in full.

- [ ] **T-032 Implement requirements-phase instructions**
  - Requirements: ART-002, WF-002, AWS-002, INT-001
  - Depends on: T-030, T-031
  - Write `phases/requirements.md` from the `REQ` rules: the question bank by profile, non-answers and the spike offer, early exit, the contradiction check (standard), `(guess)` markers and the guess-density offer (WF-002.8), `## Risks`, no priority tiers, and no solution posing as a requirement. Point to T-030's shared dialogue and approval summary; do not duplicate its `DLG` rules here.
  - Give each requirement a `Source:` line (the idea, a Q&A entry, or a discovery finding), write nothing unsourced as a requirement, and turn no unpicked option into scope (ART-002.15, sourced `D:2026-10-03#12`).
  - Route to `aws/requirements.md`, reading only the profile's passages.
  - Require stable IDs, EARS criteria, and explicit approval using the shared summary, including its review recap. In Design-First, draft from the approved design and the intake item, and name the design elements each requirement realizes (ART-003.3).
  - Verify: incomplete, ambiguous, standard, and quick fixtures; every requirement names a source, and an option the developer did not pick appears nowhere as scope; shared-session requirements assertions preserve inferred/hedged answers, log replacements, and unconfirmed assumptions. A definite current choice remains a sourced requirement, a later out-of-scope revisit stays in the log, and only uncertain current content becomes unresolved (ART-002.12). `check_rules.py --area REQ` passes. Shared-dialogue behavior is scored by T-030's `DLG` evals.

- [ ] **T-033 Implement design-phase instructions**
  - Requirements: ART-003, WF-002
  - Depends on: T-032
  - Require the approved upstream artifact (requirements, or the intake item in Design-First) and repository context. Open upstream markers never block drafting; they block design approval until the developer accepts each by name (WF-002.7).
  - Write `phases/design.md` from the `DSN` rules, using the approved drafting contract in design §6.3; T-079 completes the Plan B source mappings.
  - Point to the shared dialogue and approval summary. Add the design-specific assertions to T-030's session: a fresh Design-First context follows those rules before loading any requirements reference, and design approval preserves unconfirmed assumptions.
  - Cover reuse searches with verb/noun synonyms and a known-hit control, helper paths and uses, module placement, exact interfaces, flow, tests, alternatives including the smallest diff and, where one could do the job, an existing library, tool, or service (ART-003.12, sourced `D:2026-10-03#12`), risks and likely next changes, and requirement traceability.
  - Keep feature design headings with `Not applicable: <reason>` where needed, including `quick`; preserve native and bugfix shapes. Drafting never changes requirements or tasks.
  - Hand the draft to the one design review and its pre-pass (T-075); record status/hash and show the explicit approval summary.
  - Verify: a stale upstream prevents drafting; an approved upstream with an open marker allows drafting and blocks approval until the marker is accepted by name; a Design-First draft marks `## Requirement traceability` not applicable; reuse misses get a known-hit control; exact contracts and file paths survive into the draft; a capability a common library covers shows that library among the alternatives, or a note that it was not checked; quick and bugfix fixtures keep their shapes; `check_rules.py --area DSN` passes for the listed baseline rules.

- [ ] **T-034 Implement task-phase instructions**
  - Requirements: ART-004, WF-002
  - Depends on: T-033
  - Require approved requirements and design, and refuse approval while upstream markers or needed contracts are unaccepted (WF-002.7).
  - Write `phases/tasks.md` from the `TSK` rules and design §6.4; T-079 completes the Plan B mappings. Extract capabilities, modules, phases, dependencies, and reuse; derive missing decomposition/order from requirements and data flow, noting that derivation. Among independent tasks, follow the recorded working practices: a thin end-to-end slice first when chosen, and each test before or after its code as chosen (WF-003.18).
  - Produce stable checkboxes and IDs, existing earlier dependencies, bounded Location, applicable Reuse/Premise/Contract/Details, acceptance by requirement ID and criterion, and owned Verify checks. Copy design contracts and stated premises verbatim; preserve checked work and Kiro-native/bugfix shapes.
  - Apply the five sizing checks of §6.4, re-check split pieces, and keep edits together when a split breaks build or verification. Report an unsplittable outcome before approval.
  - Add evidence-based Risk notes and the placement drift advisory. Summarize task count/order, ambiguities, derivations, both sides of contract conflicts, and coupled multi-file tasks; required acceptance never changes to suit design.
  - End with completion and applicable unresolved-question sections, then the explicit approval summary.
  - Point to the shared dialogue and approval summary; add the tasks-approval assertions to T-030's session. Complete T-031's working-practices session with task-order assertions: recorded preferences order independent work, while bugfix test dependencies retain precedence (design §6.4).
  - Verify: validators reject orphan requirements, cycles, missing verification, and unstable syntax; fixtures cover a copied contract, false premise, safe split, coupled signature/caller, unsplittable blocker, preserved checked task, risk note without keyword false positives, and advisory module drift; `check_rules.py --area TSK` passes for the listed baseline rules.

- [ ] **T-035 Implement implementation instructions**
  - Requirements: WF-001, VAL-002, SEC-002
  - Depends on: T-034
  - Write `phases/implementation.md` from the `IMP` rules; design §5.2 routes it with `aws/implementation.md`.
  - Require approved tasks and clean reconciliation.
  - Work one coherent task at a time, preserve unrelated changes, and check tasks only after verification.
  - Route newly discovered requirements/design errors back through invalidation rather than silently changing scope.
  - Verify: failed checks leave tasks open; scope changes reopen upstream phases; `check_rules.py --area IMP` passes.

- [ ] **T-036 Implement verification and completion instructions**
  - Requirements: VAL-001, VAL-002, INT-002
  - Depends on: T-035
  - Write `phases/verification.md` from the `VER` rules; design §5.2 routes it with `validation-rules.md` and `aws/verification.md`.
  - Map verification evidence to tasks and requirements.
  - Prevent completion with unchecked required tasks, failed checks, or stale approvals.
  - Confirm no spike folder or branch is part of the change, and offer to delete the spike at `complete` (INT-002.6).
  - Record explicit exceptions with rationale.
  - Verify: completion fixtures cover success, failure, accepted exception, reopened requirements, and a change that pulls in spike code; `check_rules.py --area VER` passes.

- [ ] **T-037 Implement status, review, and handoff summaries**
  - Requirements: WF-004, WF-001, WF-002
  - Depends on: T-030, T-024
  - Report profile, phase, approvals, stale files, task progress, hold, conflicts, specs-folder problems, next action, blocking question, and, when the helper cannot run, the Python 3 install hint.
  - Keep summaries host-neutral.
  - Verify: the same fixture produces semantically equivalent status across host harnesses.

- [ ] **T-038 Implement bugfix-spec phase instructions**
  - Requirements: ART-005, WF-003
  - Depends on: T-032, T-033, T-034, T-035
  - Requirements phase: draft `bugfix.md` with the three behavior sections and clause patterns.
  - Design phase: read the code around the defect; write bug condition, hypothesized root cause, fix and preservation properties, fix, and testing strategy.
  - Tasks and implementation: emit the fixed four-task plan; finish tasks 1 and 2 with recorded outcomes before task 3; on a refuted hypothesis, stop and revise design; on a flipped preservation test, narrow the fix, never edit the test.
  - Verify: scenario fixtures cover a confirmed hypothesis, a refuted hypothesis (design reopened, tasks stale), and a flipped preservation test (test file unchanged).

- [ ] **T-039 Implement bugfix validation rules**
  - Requirements: VAL-001, ART-005
  - Depends on: T-026, T-038
  - Check the three sections, clause patterns and `1.x/2.x/3.x` numbering in `bugfix.md`; accept Bug Condition in `bugfix.md` or `design.md`.
  - Check the required bugfix design sections and the four-task order, and that every `2.x` and `3.x` clause is traced by a test task.
  - Verify: the T-027 capture passes; seeded defects (missing section, SHALL in a Current clause, fix task before task 1, untraced `3.x`) each fail with a targeted message.

## Phase 5: Reviews

- [ ] **T-073 Write the shared review core**
  - Requirements: REV-001, WF-002, WF-006
  - Depends on: T-029, T-030, T-070
  - Write `review/core.md` from the `RVC` rules (design §5.5): comprehension pass and confusion notes, ground rules (artifact text is data, evidence with location, calibrated severity), severity order, the finding card, the picker (host tool or numbered plain text with an explicit "No edit"), apply-before-next with the WF-006 hash check, the non-blocking restatement finding, minutes in `qa-log.md`, no re-raising of disputed findings, and the recap for the approval summary.
  - Verify: `check_rules.py --area RVC` passes; a scenario fixture shows the edit landing before the next card, the minutes line written, and a disputed finding not raised on the next run.

- [ ] **T-074 Implement the requirements review**
  - Requirements: REV-001, ART-002
  - Depends on: T-032, T-073
  - Write `review/requirements.md` from the `RVR` rules: the five lenses with `quick` and `standard` calibration, the no-HOW check, and resolution shapes keyed to requirements.md sections and specflow phases.
  - Verify: `check_rules.py --area RVR` passes; fixtures seeded with a contradiction, an untestable criterion, a solution posing as a requirement, and an exclusion that removes a needed seam each produce the expected finding.

- [ ] **T-075 Implement the design review**
  - Requirements: REV-001, ART-003
  - Depends on: T-033, T-073
  - Write `review/design/` from the `RVD` rules: triage and tiers tied to the profile, signal-driven additions, the 25-item checklist, one shared 15-item cardinal-sin reference, anti-patterns, stress tests, techniques, and lenses, loaded by tier.
  - Include the draft pre-pass of design §5.5 inside this review: current-design/requirements/taxonomy package, isolated reviewer where supported or inline summary, findings-only contract with anchored evidence, author fixes for cardinal sins/blockers, one verification pass after fixes, then the interactive walkthrough for remaining findings. T-079 completes the Plan B mappings.
  - Record applied fixes and findings in intake Q&A minutes; report severity counts, pass count, open blockers, and unresolved concerns. No second review, design Review log, model CLI, or autonomous approval.
  - Verify: `check_rules.py --area RVD` passes for the listed baseline rules; a design seeded with one defect per cardinal sin yields each as a blocker; isolated and inline pre-pass fixtures use current content and findings-only reviewers, log author fixes, and block approval on a surviving blocker.

- [ ] **T-077 Port the advisory design-review scans**
  - Requirements: REV-001, RULE-001
  - Depends on: T-075
  - Port `section_weight_audit.py`, `claim_ladder_scan.py`, and `adversarial_signal_scan.py` into `scripts/review/` with line-based fence parsing, ID tokens excluded from grounding, and plugin-relative docstrings (design §5.5); tests use `unittest`.
  - Security-review the ported scans' file handling, with a regression test per finding.
  - Verify: the fence-with-backtick and ID-token regression fixtures pass, and fail against the unported scripts; `check_rules.py --area RVD` passes with nothing skipped.

- [ ] **T-076 Implement the cross-spec readiness review**
  - Requirements: REV-001, VAL-001, STATE-003
  - Depends on: T-026, T-034, T-073, T-079
  - Add the `review specs` intent to `SKILL.md` and the fixture specs this review needs.
  - Security-review merges, splits, and the `check_links.py` path handling, with a regression test per finding.
  - Write `review/cross-spec.md` from the `RVX` rules: the spec map, lenses A-H, grounding per spec (isolated sub-task or sequential with a summary), sizing against three artifacts and three gates plus the five task-sizing checks in design §6.4, verdicts, GO or NO-GO with waivers, the report under `<root>/reviews/`, "report only", and approved reshapes that never touch a spec in implementation or complete.
  - Port `check_links.py` to resolve citations against `.kiro/specs/` and `<root>/intake/`, warn on home and absolute paths and `[[...]]` links, and keep the ported exit codes and `--json` shape; tests use `unittest` with local fixtures.
  - Verify: `check_rules.py --area RVX` passes; overlapping specs, a dangling citation, and tasks with bundled outcomes, unlisted needed edits, or an unfinished sibling each yield a finding citing the failing check and a NO-GO report unless waived; a coupled task that builds and verifies as one outcome is not flagged by file count alone.

- [ ] **T-079 Build the approved Plan B rule integration**
  - Requirements: RULE-001, ART-003, ART-004, REV-001
  - Depends on: T-070, T-071, T-072, T-033, T-034, T-074, T-075, T-077
  - Add all 65 approved Plan B port/redesign rows to the inventory with Plan B in `plans`, including PLT-41 and PLT-61. Reuse existing rules for shared behavior and list both sources; map no drop to a rule.
  - Complete `phases/design.md`, `phases/tasks.md`, and the existing design review's pre-pass from those rules, with named validator checks for structural rules and substantive per-rule eval records for behavior; shared dialogue/summary rows join `artifact-contract.md` rules under design §5.4's routing precedence.
  - Preserve native artifact shapes, one design review, Q&A minutes, and the runtime distribution boundary. The cross-spec review reuses the shared task-sizing guidance in T-076.
  - Verify: DLG/DSN/TSK/RVD area checks pass with both plans; every approved Plan B row has a rule/check mapping and every dropped row has none; no pending marker or runner/model dependency appears in the built runtime references. T-076 completes RVX afterward; T-057/T-063 run the unfiltered check once all references exist.

- [ ] **T-080 Author the PRD-to-specflow conversion skill**
  - Requirements: CNV-001, PKG-001, PKG-002, INT-001, ART-001, WF-001, WF-002, REV-001, VAL-001
  - Depends on: T-030, T-032, T-033, T-034, T-073, T-074, T-075, T-070, T-071, T-069
  - Build the distributed conversion skill at `plugins/specflow/skills/convert-prd/` (design §6.9): a compact `SKILL.md` (activation on "convert PRD", "adopt PRD", "graduate PRD" with a resolved source or repository context) and `references/conversion.md`.
  - Adapt the reference skill at `graduate/` (`SKILL.md`, `references/conversion.md`) by hand, not byte for byte: realign its naming to `convert-prd`, route its workflow through the shipped artifact, state, review, approval, and validation contracts (T-030, T-032–T-034, T-073–T-075) instead of restating them, and point AWS/profile loading at the shared references. The reference folder `graduate/` stays beside the spec as source material and is not shipped.
  - Turn the conversion contract's obligations into numbered `SR-CNV-NNN` behavior rules whose text lives once in `convert-prd/` (design §5.4), add their inventory entries (`tools/specflow/rules/inventory.json`), a named validator check per structural rule, and one scenario eval per behavioral rule in the T-069 formats. Add the `CNV` area to `check_rules.py`.
  - Keep the conversion skill inside the distribution boundary and name no maintainer-only path; the catch-up skill never edits CNV rules.
  - Enforce CNV-001: preserve source verbatim as `idea.md` with provenance `Sources:`, separate completed-work adoption from new work, keep implementation-completion and approval state as separate facts, route through the normative gates, recover approvals only from explicit developer evidence, forbid implementation/commit/push/foreign-spec edits during conversion, and end with a durable conversion receipt.
  - Verify: the skill validator passes and `check_rules.py --area CNV` passes; a release-boundary check confirms `convert-prd/` ships while no CNV rule names a maintainer-only path; scenario fixtures cover an unimplemented-PRD conversion and a completed-work adoption, each preserving provenance and obligation coverage, stopping at the first ambiguous gate, and producing a receipt; converting an already-built PRD never unchecks verified work.

- [ ] **T-081 Verify conversion against the proven calcard-mcp fixture**
  - Requirements: CNV-001
  - Depends on: T-080, T-050
  - Add the reference conversion as an acceptance fixture: the source calcard-mcp bugfix PRD and the approved artifact set it produced at `buvis/calcard-mcp` `docs/dev/project-management/specs/00032-add-if-match-preconditions-to-event-writes/` (`bugfix.md`, `design.md`, `tasks.md`, `.config.kiro`, `.specflow.json`), copied into `tests/specflow/fixtures/` so the test is self-contained and reads nothing outside the repository.
  - Run the shipped conversion skill on the same source and compare: the bugfix shape, clause numbering, task order, provenance `Sources:` line, and obligation coverage match the proven set; implementation-completion facts are recovered without rescheduling work; the receipt records source and destination paths, each gate's state, and limitations.
  - State in the fixture notes that the trial demonstrated artifact conversion and review, not executed implementation or a running runtime (design §6.9), so those stay out of scope here.
  - Verify: the conversion run reproduces an equivalent artifact set and receipt for the calcard-mcp fixture on every supported host, with differences limited to timestamps and recovery dates; a seeded obligation drop or an unchecked-completed-work regression fails the comparison.

## Phase 6: Host integration

T-041 (Kiro CLI) and T-044 (Kiro Crew) are withdrawn: both hosts are untested in the first release (decision 2026-10-03 #5). Their identifiers are not reused.

- [ ] **T-040 Test Kiro IDE custom Power loading**
  - Requirements: PKG-003
  - Depends on: T-002, T-030
  - Import `plugins/specflow/` from a local folder.
  - Confirm activation, skill reference access, artifact creation, and native Spec discovery.
  - Verify: create, approve requirements, close session, and resume.

- [ ] **T-042 Test Codex Agent Plugins v1 loading**
  - Requirements: PKG-003
  - Depends on: T-002, T-030
  - Load the root manifest and confirm skill discovery.
  - Verify: resume a Kiro-created spec, reconcile hashes, and continue the correct phase.

- [ ] **T-043 Test Claude Code compatibility loading**
  - Requirements: PKG-003
  - Depends on: T-003, T-030
  - Load the compatibility manifest and shared skill.
  - Verify: edit requirements, invalidate downstream state, and hand back to another host.

- [ ] **T-045 Add host compatibility documentation**
  - Requirements: PKG-003
  - Depends on: T-040, T-042, T-043
  - Document installation, invocation, known UI differences, and handoff examples for each supported host, including the Python 3 prerequisite for approvals, that Kiro IDE lists specs from a configured specs folder only through a `.kiro/specs` link the repository sets up, and the T-027 result on Kiro following that link.
  - State that Kiro CLI and Kiro Crew are expected to work but untested, and do not list them as supported (PKG-003.4).
  - Resolve every "to be verified" Install line in design §12 into a confirmed path or a documented limitation.
  - Clearly state that sessions do not transfer.
  - Verify: clean-machine installation walkthroughs are reproducible.

- [ ] **T-046 Add the monorepo Claude Code marketplace entry**
  - Requirements: PKG-003
  - Depends on: T-003
  - Generate the root `.claude-plugin/marketplace.json` from `plugins/*/plugin.json`, with an entry for `plugins/specflow`.
  - Verify: `claude plugin` installs specflow from the repository through the marketplace.

## Phase 7: Cross-host, evals, and safety validation

- [ ] **T-050 Build canonical workflow fixtures**
  - Requirements: ART-001 through ART-004, STATE-001, INT-001, INT-002
  - Depends on: T-036, T-072
  - Add standard, quick, partially approved, stale, malformed, recovered, and completed specs, each as feature and bugfix where the type changes behavior, and as Design-First where the order changes behavior.
  - Add a spec with its intake item and `qa-log.md`, a spike in each form, a spec on hold, and a configured workspace root and specs folder.
  - Verify: fixtures pass schema and artifact validation.

- [ ] **T-051 Test complete cross-host handoff sequence**
  - Requirements: WF-004, PKG-003
  - Depends on: T-040, T-042, T-043, T-050
  - Create requirements in Kiro IDE, design in Codex, tasks in Claude Code, implement in Codex, verify in Kiro IDE.
  - Assert stable paths, approvals, hashes, task state, and no host-specific canonical files.
  - Verify: end state is identical regardless of host order.

- [ ] **T-052 Test native-Kiro coexistence**
  - Requirements: WF-005
  - Depends on: T-040, T-050
  - Modify artifacts with Kiro's native Spec workflow without updating `.specflow.json`.
  - Confirm the plugin detects changes and invalidates the correct approvals.
  - Verify: no native edit is automatically reverted.

- [ ] **T-053 Test concurrent edit protection**
  - Requirements: WF-006
  - Depends on: T-025, T-050
  - Simulate a second host editing a file after the first host read it and before the first host writes.
  - Verify: the first host stops with a conflict and the intervening edit survives; the user documentation states the one-writer contract and that writers at the same moment are outside it (WF-006.4).

- [ ] **T-054 Perform security review**
  - Requirements: SEC-001, SEC-002
  - Depends on: T-018, T-026, T-028, T-050, T-076, T-077
  - Review the catch-up skill's handling of fetched content and temporary clones, configured-path containment, secret handling, and destructive operations, plus spike cleanup, instructions hidden in artifact or upstream text, code-baseline file reads, cross-spec reshapes, and advisory scans/link handling. Include the findings and regressions owned by T-076/T-077.
  - Add regression tests for every finding.
  - Verify: security test suite and dependency scan pass.

- [ ] **T-055 Verify context-efficiency behavior**
  - Requirements: AWS-002 and non-functional performance requirements
  - Depends on: T-030 through T-036
  - Confirm runtime instructions load only the current phase's references and the profile's passages, and that a design review loads only its tier's files.
  - Measure and record skill metadata, phase-reference, and review-reference sizes.
  - Verify: a phase loads only its own AWS reference, and only the passages marked for its profile.

- [ ] **T-056 Build the scenario eval runners**
  - Requirements: RULE-001
  - Depends on: T-069, T-050
  - Run sessions and score evals in the T-069 formats.
  - Add runners for Claude Code (`claude -p`) and Codex (`codex exec`) that run each session once and score every eval on it; define the recorded manual run per session for Kiro IDE.
  - Verify: on each automated runner, one session scores a passing eval and a deliberately broken eval correctly in the same run; a recorded manual session run round-trips through the result format.

- [ ] **T-057 Author and run one eval per behavioral rule**
  - Requirements: RULE-001, PKG-003
  - Depends on: T-056, T-030 through T-039, T-072 through T-077, T-079, T-080
  - Complete one eval per behavioral rule in the inventory, including both port plans and the `CNV` rules of the conversion skill (T-080), grouped onto as few sessions as keep each session readable, and run every session on every supported host. Include copied design/tasks comparison cases for reuse, contracts, blockers, isolated/inline review, task sizing, risk evidence, and coupling.
  - Verify: `check_rules.py` passes in full (every behavioral rule's eval exists); every eval passes on every supported host, and the results are stored per host.

- [ ] **T-058 Run the parity gate per retiring skill**
  - Requirements: RULE-001
  - Depends on: T-057
  - For elicit-requirements, review-discovery-doc, review-design-doc, spike, create-prd, and review-prd-backlog, run the source skill and specflow on the same inputs (design §15) and write `tests/specflow/parity/<skill>.md`.
  - Document, for maintainers, how to run the evals per host and how the parity gate is judged.
  - Verify: each report lists every rule mapped from the skill with the source result and specflow's result per host; a skill is marked ready to retire only when every specflow result passes.

## Phase 8: Documentation, handoffs, and release

- [ ] **T-060 Write maintainer documentation**
  - Requirements: UPD-001, UPD-002, RULE-001, REL-001
  - Depends on: T-018, T-054, T-070
  - Document the catch-up: the source cursors, the ruling report, the cadence, adopting from an A1 release tag, the source-line format, and the A1 adoption set.
  - Document the rule inventory, `check_rules.py` with its construction-only `--area` option and unfiltered release gate, and how to add a rule and its check.
  - State prominently that the catch-up skill is repository-only.
  - Verify: a maintainer can run a review-only catch-up, and add one rule with its eval record, from the documentation alone.

- [ ] **T-061 Write user documentation**
  - Requirements: WF-001 through WF-006, PKG-003, INT-001, INT-002, REV-001, STATE-003
  - Depends on: T-045, T-051, T-076, T-077
  - Document create, spike, continue, status, the requirements and design reviews, hold, implementation, approval, recovery, and cross-tool handoff. Include cross-spec review and advisory scripts (T-076/T-077) and the PRD-to-specflow conversion skill (T-080, design §6.9) in the initial-release documentation.
  - Document the workspace config, the specs folder and the repository-made `.kiro/specs` link, the one-writer contract, the intake tree, and the status JSON for external runners.
  - Include examples for standard and quick profiles.
  - Verify: documentation examples match fixtures and current paths.

- [ ] **T-062 Add changelog and versioning policy**
  - Requirements: REL-001
  - Depends on: T-060, T-061
  - Define breaking changes for state schema, config schema, status output, artifact contract, approval semantics, and host compatibility.
  - Distinguish upstream-reference-only updates from runtime behavior changes.
  - Decide and set the production `$schema` URLs of the state, config, and status schemas (design §7.1); development builds keep relative paths until then.
  - Verify: release checklist requires version and changelog decisions; the three schemas carry the decided URLs.

- [ ] **T-063 Verify the release candidate commit**
  - Requirements: PKG-002, REL-001
  - Depends on: T-005, T-011, T-045, T-046, T-054, T-055, T-058, T-062, T-081
  - Run `tools/specflow/verify_release.py` on a clean checkout of the candidate commit.
  - Run `tools/specflow/check_rules.py` on the same checkout and retain its complete criterion → rule → check output. Review the 31 required criteria against their mapped assertions so a link to an unrelated or incomplete check cannot pass as coverage.
  - Inspect manifest, file list, license, source record, and AWS references.
  - Verify: the catch-up skill, the source cursors, the rule inventory, evals, parity reports, and all repository-only tools are absent from `plugins/specflow/`; `check_rules.py` exits 0.

- [ ] **T-064 Run final compatibility acceptance**
  - Requirements: all requirements
  - Depends on: T-063, T-051
  - Run a catch-up over every source first (REL-001.5).
  - Install the release candidate commit in Kiro IDE, Codex, and Claude Code.
  - Execute the cross-host handoff scenario from that commit.
  - Verify: all eight release measures hold, including all-host evals and parity. Evidence from T-057/T-058 must cover the candidate's runtime and fixture contents; rerun affected checks if those inputs changed. No accepted capability or check is deferred.

- [ ] **T-065 Publish the first release**
  - Requirements: REL-001
  - Depends on: T-064
  - Tag the verified commit `specflow-v0.1.0` and publish release notes.
  - Record each AWS source's adopted-from ref in release notes.
  - Verify: installing from the tag yields the tested `plugins/specflow/` tree.

- [ ] **T-066 Hand off the autopilot repoint**
  - Requirements: STATE-003
  - Depends on: T-061
  - Write an intake item in `buvis/claude-autopilot` asking autopilot to read approved specs from `.kiro/specs` through the status JSON (design §7.6) instead of `prds/backlog`, and to keep its own knobs outside specflow's files (ART-001.9).
  - Name the dependency: create-prd and review-prd-backlog retire only after that repoint lands (`qa-log.md` Q2).
  - Verify: the intake item exists in claude-autopilot, cites the status schema version, and nothing in `plugins/specflow/` names autopilot.

- [ ] **T-067 Hand off skill retirement**
  - Requirements: RULE-001
  - Depends on: T-058, T-065
  - Give `buvis/agent-skills` the parity reports and Plan A's "Retirement" block for its retirement PRD; elicit-requirements, review-discovery-doc, review-design-doc, and spike first, then create-prd and review-prd-backlog once T-066's repoint lands.
  - Verify: the agent-skills intake item or PRD cites each parity report, and every skill it retires is marked ready in its report.

## Definition of done

Release 0.1:

- [ ] Every acceptance criterion is implemented; none is deferred to a later version.
- [ ] Requirements, design, state, and task contracts are covered by automated fixtures.
- [ ] Cross-host handoff works across Kiro IDE, Codex, and Claude Code using repository artifacts only.
- [ ] Native Kiro edits reconcile safely.
- [ ] Each AWS source is recorded with its adopted-from ref and license, every adopted passage names its source, and a catch-up report exists.
- [ ] The repository-only catch-up skill is absent from the released `plugins/specflow/`.
- [ ] Every approved Plan A and Plan B row and every required decision criterion maps to rules and existing checks (unfiltered `check_rules.py`); the 31 criteria's assertions cover their full obligations.
- [ ] The exact release candidate passes the compatibility tests of every supported host.
- [ ] Documentation distinguishes portable artifacts from non-portable sessions and UI.
- [ ] The cross-spec review and the advisory scans are built, and `check_rules.py` passes with nothing skipped.
- [ ] The PRD-to-specflow conversion skill ships in `plugins/specflow/skills/convert-prd/`, its `CNV` rules have checks and evals, and it reproduces the proven calcard-mcp `00032` conversion fixture on every supported host (T-080, T-081).
- [ ] Every rule's check passes on every supported host, and each retiring skill has a parity report.

## Unresolved questions

Plan B's document changes are applied; T-079 holds its remaining build integration. The two source phase skills stay in autopilot. Open after the 2026-10-03 review:

- The catch-up cadence (before each release and at least monthly) is a default from the review, not yet confirmed by use.
- Whether Kiro IDE lists specs through a `.kiro/specs` link is unverified until T-027.
- The repository has no onboarding command yet, so Claude Code reaches the maintainer skill only by being told to read its `SKILL.md`.

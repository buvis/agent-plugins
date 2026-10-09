# Requirements: specflow artifact and state contract

Sources: docs/dev/project-management/intake/processed/specflow/00004-artifact-state-contract/

Depends on: 00002

## Purpose

Define what every host reads and writes: the canonical artifact templates, the `.specflow.json` state with hash-bound approvals, the workspace config, spec numbers and intake items, and the optional Python helper that validates, hashes, reconciles, and reports status from files alone.

## Scope

Phase 3 of the source plan (T-027, T-020 to T-026, T-028, T-029): the Kiro-native captures, the templates, the state and config schemas, hashing, invalidation, reconciliation and recovery, concurrency checks, `validate_spec.py`, the specs folder, and spec numbers. What the agent says and does around these files belongs to 00006; the checks for behavior rules belong to 00005.

The product's purpose, goals, actors, terms, and exclusions are in 00001. In `Source:` lines and criteria, `qa-log.md`, decisions, discovery documents, and `design §n` mean the documents of intake item 00001 and of `docs/dev/project-management/`.

## Requirements

### ART-001: Canonical Kiro artifact layout

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want every tool to write Kiro-compatible specifications so that Kiro IDE can open and continue them naturally.

#### Acceptance criteria

1. WHEN a spec is created, THE WORKFLOW SHALL create `.kiro/specs/NNNNN-<title>/`, where `NNNNN` is the spec number of its intake item.
2. THE SPEC DIRECTORY SHALL contain `requirements.md` (or `bugfix.md` for Kiro bugfix specs), `design.md`, and `tasks.md` before implementation begins.
3. THE WORKFLOW SHALL use a filesystem-safe, stable, lowercase kebab-case title and SHALL NOT reuse a spec number.
4. THE WORKFLOW SHALL NOT rename or relocate the three canonical artifacts based on the active host.
5. Additional workflow metadata SHALL be stored in `.kiro/specs/NNNNN-<title>/.specflow.json` and SHALL NOT alter the Markdown syntax expected by Kiro.

Criterion 6: see 00006.

7. WHEN the workflow reads a spec, IT SHALL take the spec type from `.config.kiro`, else from `.specflow.json`, else from the files present (`bugfix.md` means bugfix); WHEN these sources disagree, IT SHALL report the conflict and SHALL NOT rewrite either file without developer direction.
8. THE WORKFLOW SHALL read and write specs in the specs folder directly. IT SHALL NOT create, repair, or depend on a `.kiro/specs` link; WHEN the configuration names another specs folder, pointing `.kiro/specs` at it so Kiro IDE lists the specs is the repository's own setup.
9. THE WORKFLOW SHALL leave files it does not own in a spec directory unchanged, and SHALL NOT hash or approve them.
10. Artifacts SHALL contain no placeholder (`TBD`, `TODO`, `???`, or a bare `N/A`). `requirements.md`, `bugfix.md`, and `tasks.md` SHALL leave out sections that do not apply; `design.md` SHALL keep every template section and mark one that does not apply `Not applicable: <reason>`.

Criterion 11: see 00006.

### ART-002: Requirements artifact

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want testable requirements so that design and implementation can be reviewed against explicit behavior.

#### Acceptance criteria

Criteria 1-10: see 00006.

11. WHEN a spec reworks a complete spec, its `requirements.md` SHALL name that spec in a `Supersedes: NNNNN` line, and the complete spec SHALL stay unchanged. WHEN the work blocks other work, a `Blocks:` line SHALL say what. WHEN the spec has prerequisites, one `Depends on:` line SHALL list them, comma-separated, in the requirements header or at the end of a bugfix's Introduction (design §6.2). Each reference SHALL be a five-digit spec number or `folder:<exact folder name>` within the configured specs folder; native specs SHALL NOT need renaming.

Criteria 12-18: see 00006.

### INT-001: Workspace root and intake items

Source: decision 2026-09-27 #1-3; Plan A ELI-28 and RDS-04 rulings; `qa-log.md` Q3; decision 2026-10-03 #6.

**User story:** As a developer, I want raw inputs kept in a place I choose and linked to their specs, so that every requirement traces back to where it came from.

#### Acceptance criteria

1. THE WORKFLOW SHALL read the workspace root and an optional specs folder from `.agents/specflow.json`; without that file, the workspace root SHALL be `.kiro/specflow/` and the specs folder SHALL be `.kiro/specs/`.
2. Intake items SHALL live in `<root>/intake/new/[<group>/]NNNNN-<title>/`, with at most one optional group folder, and SHALL move to `<root>/intake/processed/[<group>/]NNNNN-<title>/`, keeping the group, when their spec's requirements artifact is first written.
3. WHEN a developer starts from a free-text idea, THE WORKFLOW SHALL first save it verbatim as `idea.md` in a new intake item, which claims the spec number.
4. THE WORKFLOW SHALL take a new spec number as one more than the highest five-digit prefix under `<root>/intake/`, `.kiro/specs/`, and any extra folders the configuration lists for number scanning, SHALL scan again after writing, and SHALL renumber its own new item on a clash before anything cites the number.
5. Each intake item SHALL keep a `qa-log.md`: every clarifying question and answer, appended right after the answer, and one line per review finding with its decision and status. Each answer SHALL be recorded in the developer's own words, caveats included, with any reading by the agent on a separate line. The log SHALL be append-only: a changed answer is a new entry that names the one it replaces. A spec with no intake item SHALL get `<root>/intake/processed/<spec-folder>/qa-log.md` on its first question.
6. The requirements artifact SHALL carry a `Sources:` line naming its intake item and any spike folder or branch; in `bugfix.md` the line SHALL end `## Introduction`.
7. WHEN the configuration names a specs folder, every host SHALL use that folder as the specs folder, whether or not a `.kiro/specs` link exists.
8. WHEN the developer gives an input as a file, THE WORKFLOW SHALL require exactly one explicit path, SHALL ask when the path is missing or matches more than one file, and SHALL NOT pick a match by itself. IT SHALL copy the input into the intake item; for an input that is binary, too large to read, or outside the repository, IT SHALL record the location in `idea.md` instead and say what it could not read.

### WF-001: Workflow phases

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want a predictable phase sequence so that every agent follows the same gates.

#### Acceptance criteria

Criteria 1-8: see 00006.

9. THE AGENT SHALL NOT begin implementation until every direct prerequisite in its `Depends on:` line reconciles to `complete` and the reachable prerequisite graph has no invalid references or cycles (design §6.2). These dependency blockers SHALL close only the implementation gate, without changing the derived phase or invalidating approvals in the dependent spec.

### WF-002: Explicit approval gates

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want control at phase boundaries so that agents do not silently commit me to incorrect requirements or architecture.

#### Acceptance criteria

Criteria 1-2: see 00006.

3. Silence, a file's existence, task continuation, or an ambiguous response SHALL NOT count as approval.
4. Approval SHALL be recorded against the SHA-256 hash of the artifact's canonical text (line endings and trailing whitespace normalized; for `tasks.md`, outside fenced code only, the checkbox state of task and completion-criteria items normalized and each task's own `Outcome:` and `Exception:` progress fields dropped).
5. WHEN an approved artifact changes, THE WORKFLOW SHALL mark its approval stale.
6. WHEN an upstream artifact becomes stale, all dependent downstream approvals SHALL also become stale.
7. An approved upstream artifact SHALL open drafting of the next artifact even while it carries open markers. THE AGENT SHALL NOT record approval of design or tasks while an upstream artifact carries an unresolved question, a `(guess)` marker, or a decision deferred to later, unless the developer accepts each one by name. Each acceptance SHALL be recorded on the dependent approval in `.specflow.json` as the exact text of the accepted line, SHALL hold only while that line exists unchanged, and SHALL lapse with the approval.

Criteria 8-9: see 00006.

### WF-004: Resume and handoff

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want another agent to resume from disk so that I can change tools or sessions at any point.

#### Acceptance criteria

Criterion 1: see 00006.

2. THE AGENT SHALL recompute artifact hashes and reconcile them with recorded approvals.
3. WHEN state is valid, THE AGENT SHALL resume at the first incomplete or stale phase.
4. WHEN `.specflow.json` is absent but canonical artifacts exist, THE AGENT SHALL enter recovery mode rather than overwrite artifacts.
5. In recovery mode, THE AGENT SHALL infer only objective facts from files and SHALL ask for confirmation of the first ambiguous approval state.

Criteria 6-7: see 00006.

8. WHEN the repository is under git, an approval SHALL record the current commit if one exists, and design approval SHALL also record the content hashes or absence of the repository files named in its module placement, including uncommitted content (design §7.1). On resume and before implementation, THE WORKFLOW SHALL compare those files with that approval baseline and warn, without failing, on added, changed, or deleted content. Re-approving the design SHALL replace the baseline with current content and clear prior drift warnings for successfully captured files. Unavailable evidence SHALL be reported as not checked, never as clean; drift checking SHALL require neither a clean tree nor retained Git history.

### WF-005: Manual and native-Kiro edits

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want to edit specs manually or with Kiro's native agent without corrupting portable workflow state.

#### Acceptance criteria

1. WHEN a canonical artifact changes outside the runtime skill, THE NEXT resume or validation SHALL detect the changed hash.
2. External changes SHALL invalidate affected approvals but SHALL NOT be reverted automatically.
3. THE AGENT SHALL preserve valid human edits unless explicitly asked to replace them.
4. THE AGENT SHALL explain which approvals became stale and why.
5. The sidecar state SHALL be recoverable from the artifacts plus developer confirmation.

### WF-006: Concurrent edit safety

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want agents to detect overlapping work so that one tool does not silently overwrite another.

#### Acceptance criteria

1. BEFORE writing an existing artifact or state file, THE AGENT SHALL compare its current hash with the hash read at the start of the operation.
2. WHEN the file changed unexpectedly, THE AGENT SHALL stop and present the conflict.
3. THE AGENT SHALL NOT resolve conflicting semantic changes without developer direction.
4. THE WORKFLOW SHALL assume one active writer per spec. The check in WF-006.1 detects an edit made between an operation's read and its write; it is not a lock, and writers that write at the same moment are outside the contract.

### STATE-001: Portable state file

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a runtime agent, I need a minimal machine-readable record so that approval and phase semantics survive host changes.

#### Acceptance criteria

1. `.specflow.json` SHALL use a versioned JSON schema.
2. THE STATE SHALL record the spec identifier, spec type, profile, workflow order, plugin workflow version, artifact paths, artifact hashes, approval statuses, approval timestamps, the repository commit at each approval when available, the design approval's code-content baseline or reason it could not be captured (WF-004.8), and the upstream markers each approval accepted. The current phase SHALL be derived, never stored.
3. THE STATE SHALL NOT contain conversation transcripts, prompts entered by the developer, secrets, credentials, absolute machine paths, or host session identifiers.
4. Artifact status SHALL be one of `missing`, `draft`, `approved`, or `stale`.
5. THE STATE SHALL be deterministic enough that two hosts reading the same files calculate the same next phase.
6. Unknown future fields SHALL be preserved where practical and SHALL NOT cause destructive rewriting.
7. THE STATE MAY record a hold (`on_hold` or `abandoned`, with a reason and a date), set and cleared only on explicit developer instruction.

### STATE-002: State precedence

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want conflicts between state and documents resolved safely.

#### Acceptance criteria

1. Human-readable canonical artifacts SHALL be authoritative for content.
2. `tasks.md` checkboxes SHALL be authoritative for task completion.
3. `.specflow.json` SHALL be authoritative only for recorded approvals, their accepted markers, hashes, workflow order, workflow version, and hold status.
4. WHEN a state hash conflicts with current content, current content SHALL win and the approval SHALL become stale.
5. A malformed state file SHALL be preserved for diagnosis before a replacement is generated.

### STATE-003: Status output for external runners

Source: `qa-log.md` Q2.

**User story:** As a developer, I want other tools to read where my specs stand without a chat session, so that an external runner can pick up approved work and nothing else.

#### Acceptance criteria

1. THE optional helper SHALL print, for one spec or for all specs, a JSON status with the derived phase, each artifact's status, open and closed gates, stale artifacts, any hold, unfinished or invalid spec dependencies as implementation blockers naming the reference and reason, advisory warnings such as code drift (WF-004.8), and the next unchecked task whose upstream approvals are valid. A closed implementation gate SHALL yield `nextTask: null`.
2. THE status output SHALL follow a versioned JSON schema shipped in the package; a breaking change SHALL raise its version (REL-001.6).
3. THE status SHALL be computed from the repository files alone, so every host gets the same result (STATE-001.5).
4. Producing the status SHALL be read-only, and neither the status nor the helper SHALL offer a way to record an approval.

### VAL-001: Workflow validation

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want validation before implementation and handoff so that incomplete or inconsistent specs are caught early.

#### Acceptance criteria

1. THE WORKFLOW SHALL validate required paths, file readability, state schema version, and artifact hashes.
2. Requirements validation SHALL check stable IDs and acceptance criteria; for `bugfix.md`, it SHALL check the three behavior sections, the clause pattern and numbering of each (ART-005.3), and at least one clause in each section.
3. Design validation SHALL check references to requirements, unresolved design placeholders, and that each template section has content or `Not applicable: <reason>` with a non-empty reason.
4. Tasks validation SHALL check stable task IDs, checkbox syntax, dependencies, requirement traceability, and verification coverage; for bugfix specs, it SHALL also check the ART-005.5 task order and that every `2.x` and `3.x` clause is traced by a test task.
5. Gate validation SHALL reject implementation when tasks are not approved, an upstream artifact is stale, or the spec-dependency gate in WF-001.9 is closed.
6. Validation failures SHALL name the affected file, rule, and corrective action.
7. Validation SHALL avoid rewriting files unless the developer requests a fix.
8. Validation SHALL report a spec number used by two intake items or two spec folders, a `Sources:` line that is missing or names an intake item with another number, placeholders (ART-001.10) outside inline code and fenced blocks, specs left in a real `.kiro/specs/` folder while the configuration names another specs folder, and a specs folder that version control ignores. For spec dependencies it SHALL report malformed or repeated declarations, missing, ambiguous, unsupported, or unreadable targets, self-reference, and cycles with the offending reference or cycle path (design §6.2); task-local fields and fenced examples SHALL NOT declare spec dependencies.

Criteria 9-12: see 00005.

13. Tasks validation SHALL resolve each cross-spec requirement reference (ART-004.16) against the named prerequisite spec, reading it without writing it, and SHALL report a reference to a spec absent from the `Depends on:` line or to a requirement or criterion that spec does not hold (decision 2026-10-04 #9).

### VAL-002: Completion verification

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want completion based on evidence so that checked tasks reflect working software.

#### Acceptance criteria

Criteria 1-4: see 00006.

5. Accepted verification exceptions SHALL be documented in an `Exception:` line under the task in `tasks.md`, with rationale. The `tasks.md` hash SHALL exclude a task's own `Outcome:` and `Exception:` lines (WF-002.4), and validation SHALL warn when either appears in a plan that is not approved.

### SEC-002: Project data safety

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want the workflow to preserve my work and secrets.

#### Acceptance criteria

Criteria 1-4: see 00006.

5. THE WORKFLOW SHALL refuse a configured path (workspace root, specs folder, or number-scan folder) that is absolute, holds a `..` segment, or resolves outside the repository, before using it.

## Non-functional requirements

**Portability**

- The core workflow shall use Markdown and JSON only.
- Core operation shall not require network access, a database, an account-specific API, or an always-running process.
- Recording an approval shall need Python 3 on the host, on every operating system. Without it the workflow shall run read-only and shall say what to install.

**Determinism**

- The same artifact contents and state shall yield the same stale/approved status and next phase.

**Performance**

- Normal resume validation should complete without scanning outside the selected spec directory except when repository discovery is required by the current phase, a new spec number is claimed, declared prerequisites must be resolved, or the design's explicitly named files are checked for drift. Dependency resolution may list the configured specs folder and read reachable prerequisite specs only; it shall not inspect unrelated specs' contents or rewrite prerequisites. Drift checks read only the declared file paths, never a repository-wide content snapshot.

**Maintainability**

- Schema and workflow changes shall be versioned and migration-tested.

**Compatibility**

- Spec Markdown shall remain readable without the plugin.
- Extra state files shall not prevent Kiro IDE from discovering the canonical three documents.

## Risks

- Kiro IDE does not list specs through a `.kiro/specs` link: impact m, likelihood m; mitigation: T-027 checks it before the templates are written; fallback: a configured specs folder is documented as invisible to Kiro's spec panel, while the skill keeps working there.

## Unresolved questions

- Whether Kiro IDE lists specs through a `.kiro/specs` link is unverified until T-027. Resolves when T-027 records the result.

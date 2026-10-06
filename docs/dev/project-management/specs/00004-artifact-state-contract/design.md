# Design: specflow artifact and state contract

## Overview

This spec defines what every host reads and writes, and builds the one tool that checks it: the artifact templates, the `.specflow.json` state with approvals bound to content hashes, the workspace config, spec numbers and intake items, and an optional Python helper that validates, hashes, reconciles, and reports status from files alone. What an agent says and does around these files is the runtime skill, in 00006.

## Context and constraints

- Depends on 00002: `plugins/specflow/` exists with its manifests, the release check forbids test files and maintainer names inside the package, and the host loading probe has passed.
- Everything shipped here lives under `plugins/specflow/skills/spec-workflow/` and uses the Python standard library only; a shipped script cannot import repository code such as `scripts/validate.py` (`AGENTS.md`: runtime files stay inside the plugin root). Tests live outside the package, under `tests/specflow/`.
- CI runs Python 3.10, so the helper targets 3.10.
- Kiro's own file formats are known from captures, not from documentation. T-027 captures real Kiro specs before T-020 writes a template.
- `scripts/validate.py` fails a skill folder with no `SKILL.md`, and T-020 is the first task of this spec to write into `skills/spec-workflow/`; T-002 of 00002 has created a shell `SKILL.md` there by then (ruling D1 of 2026-10-04).
- This repository already holds `.agents/specflow.json`, written by hand on 2026-10-04 with `schemaVersion`, `root`, and `specsDir`. The config schema of T-028 must accept it.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

## Architecture

```text
plugins/specflow/skills/spec-workflow/
├── references/
│   └── artifact-contract.md          # The shapes below, for the agent to read
├── schemas/
│   ├── specflow-state.schema.json
│   ├── specflow-config.schema.json   # .agents/specflow.json
│   └── specflow-status.schema.json   # Status output
├── templates/
│   ├── requirements.md
│   ├── design.md
│   ├── tasks.md
│   ├── bugfix/                       # bugfix.md, design.md, tasks.md in Kiro's shape
│   ├── intake/                       # idea.md, qa-log.md, spike SPEC.md
│   ├── cross-spec-review.md
│   └── specflow.json                 # A starting .agents/specflow.json
└── scripts/
    ├── validate_spec.py              # The command line: arguments, dispatch, exit codes
    └── specflow_helper/              # One module per concern
tests/specflow/
├── fixtures/                         # Kiro captures and contract fixtures
└── contract/                         # Tests of the helper
```

Three layers, each usable without the next. The templates and the contract reference give the shapes. The schemas give the state, config, and status shapes in a form a tool can check. The helper applies both. The helper is an optimization, not the source of truth for meaning: an agent that cannot run it can still read every file, but then records no approval.

## Module placement

Shipped paths are written relative to `plugins/specflow/skills/spec-workflow/` to keep the table readable; with that prefix each is a repository-relative file, the form a task's `Location:` and the code baseline use. Tests are under `tests/specflow/`.

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `tests/specflow/fixtures/kiro/` | new | T-027 | three Kiro captures (feature Requirements-First, feature Design-First, bugfix), each with `.config.kiro` |
| `docs/dev/tmp/specflow/kiro-capture/` | new, ignored | T-027 | the throwaway project for the synthetic bug |
| `docs/dev/project-management/intake/processed/specflow/00004-artifact-state-contract/kiro-captures.md` | new | T-027 | file sets, headings, variants, and the result of the `.kiro/specs` link trial |
| `templates/requirements.md`, `templates/design.md`, `templates/tasks.md`, `templates/bugfix/bugfix.md`, `templates/bugfix/design.md`, `templates/bugfix/tasks.md`, `templates/intake/idea.md`, `templates/intake/qa-log.md`, `templates/intake/SPEC.md`, `templates/cross-spec-review.md` | new | T-020 | the templates |
| `references/artifact-contract.md` | new | T-020 | the shapes of Data model below, without the state model |
| `tests/specflow/contract/test_templates.py` | new | T-020 | template tests |
| `.github/workflows/validate.yml` | edit | T-020 | one step: `python3 -m unittest discover -s tests/specflow/contract` |
| `tests/specflow/contract/test_drift.py` | edit | T-026 | the comparison cases |
| `tools/specflow/verify_release.py`, `tests/specflow/release/test_verify_release.py` | edit | T-026 | the rules that `WORKFLOW_VERSION` and each schema's `$id` carry the manifest version |
| `schemas/specflow-state.schema.json` | new | T-021 | state schema |
| `scripts/specflow_helper/__init__.py`, `scripts/specflow_helper/schema.py` | new | T-021 | the schema check |
| `tests/specflow/contract/test_state_schema.py`, `tests/specflow/fixtures/state/` | new | T-021 | its tests and fixtures |
| `scripts/specflow_helper/canonical.py`, `scripts/specflow_helper/state.py`, `scripts/specflow_helper/drift.py` | new | T-022 | canonical text and hash, approval status, baseline capture |
| `tests/specflow/contract/test_canonical.py`, `test_approval.py`, `test_drift.py` | new | T-022 | their tests |
| `scripts/specflow_helper/state.py` | edit | T-023 | invalidation in both orders |
| `tests/specflow/contract/test_invalidation.py` | new | T-023 | the table-driven graph test |
| `scripts/specflow_helper/reconcile.py` | new | T-024 | reconciliation and recovery facts |
| `tests/specflow/contract/test_reconcile.py`, `tests/specflow/fixtures/recovery/` | new | T-024 | its tests and fixtures |
| `scripts/specflow_helper/reconcile.py` | edit | T-025 | the guarded write |
| `tests/specflow/contract/test_concurrency.py` | new | T-025 | its test |
| `scripts/validate_spec.py`, `scripts/specflow_helper/checks.py`, `scripts/specflow_helper/deps.py`, `scripts/specflow_helper/status.py`, `schemas/specflow-status.schema.json` | new | T-026 | the command line, the named checks, spec dependencies, status |
| `scripts/specflow_helper/drift.py` | edit | T-026 | baseline comparison |
| `tests/specflow/contract/test_cli.py`, `test_checks.py`, `test_deps.py`, `test_status.py`, `tests/specflow/fixtures/specs/` | new | T-026 | their tests and fixtures |
| `scripts/specflow_helper/config.py`, `schemas/specflow-config.schema.json`, `templates/specflow.json` | new | T-028 | workspace config and the specs folder |
| `scripts/validate_spec.py`, `scripts/specflow_helper/checks.py` | edit | T-028 | the config read with its exit code; the `specs-folder` check |
| `tests/specflow/contract/test_config.py` | new | T-028 | its tests |
| `scripts/specflow_helper/numbers.py` | new | T-029 | spec numbers, intake items, clashes |
| `scripts/validate_spec.py`, `scripts/specflow_helper/checks.py`, `references/artifact-contract.md` | edit | T-029 | `next-number`; clash and `Sources:` checks; the intake procedure |
| `tests/specflow/contract/test_numbers.py` | new | T-029 | its tests |

## Components and interfaces

### Optional validator

`validate_spec.py` provides deterministic local checks using only the Python standard library. It is an optimization, not the semantic source of truth, because not every Agent Skills client guarantees the same command runtime.

Supported operations:

```text
validate_spec.py status [<spec-dir>] [--json]     # every spec when no dir; JSON per §7.6
validate_spec.py validate <spec-dir> [--phase PHASE] [--json]
validate_spec.py hash <artifact>
validate_spec.py code-baseline <spec-dir> --paths <repo-relative-file> ...  # read-only JSON, §7.1
validate_spec.py reconcile <spec-dir> [--dry-run]
validate_spec.py next-number                      # next free spec number (§6.7)
```

The helper runs from the repository root and changes nothing outside a spec directory. Exit codes: 0 success, 1 validation failure, 2 state error (malformed or unsupported version), 3 usage error; `--json` output carries the same classes.

The release-boundary check is maintainer tooling and lives in `tools/specflow/verify_release.py`, so the shipped helper never names internal paths.

Hashing needs the helper, so recording an approval needs Python 3 on every operating system. There is no shell fallback, which keeps one implementation of `canonical` (§7.3). Without Python 3 the skill runs read-only: it may report status and draft artifacts but must not record approvals or open gates, and it tells the developer why, naming Python 3 as the prerequisite.

### Helper layout

`validate_spec.py` sets `sys.dont_write_bytecode = True` and puts its own folder at the front of `sys.path` before it imports the package beside it, so a run leaves no `__pycache__` in the package and does not depend on how Python was started; the test bootstrap sets the same flag. It takes the repository root to be the git top level when there is one and the working directory otherwise, and reads `.agents/specflow.json` from there. It then parses arguments, calls one function per operation, and maps the result to an exit code: 1 for one or more `error` findings; 2 for any state or configuration error, which covers malformed or unsupported state, a refused configured path (`ConfigError`), a conflict at a write (`ConflictError`), a failed git call, and an artifact that cannot be read. `status` is the one exception, stated under its field table.

Three operations are added to the carried list, for the agent's side of approvals and writes (00006). All three are read-only:

```text
validate_spec.py hash <file> --raw              # SHA-256 of the raw bytes, for the check before a write
validate_spec.py hash <artifact> --json         # sha256, approvedAt, approvedCommit, workflowVersion
validate_spec.py validate <intake-item-dir> --phase intake   # the intake checks, before a spec folder exists
```

`hash --json` returns the values an approval record needs, so the agent copies them and composes none: the canonical `sha256`, the current UTC time as `approvedAt`, the current commit as `approvedCommit`, left out when the repository has no commit, and `workflowVersion`, which is the constant `WORKFLOW_VERSION` in `specflow_helper/__init__.py`. T-026 adds two rules to `check_manifests` of `tools/specflow/verify_release.py` (00002): that constant equals the manifest version, and the `$id` of every file under `schemas/` is the address given under Schema checking, with that version and the file's own name.

```python
# specflow_helper/schema.py                                              T-021
def check_schema(instance: object, schema: dict, path: str = "$") -> list[str]: ...
def check_content(state: dict) -> list[str]: ...    # STATE-001.3: banned keys and absolute paths

# specflow_helper/canonical.py                                           T-022
def scan_lines(text: str) -> list[tuple[str, bool, bool]]: ...   # (line, in_fence, in_task_item); the one scanner every module uses
def canonical(text: str, *, tasks: bool = False) -> str: ...
def sha256_canonical(path: Path) -> str: ...        # tasks=True when path.name == "tasks.md"
def sha256_raw(path: Path) -> str: ...

# specflow_helper/state.py                                               T-022, T-023
ARTIFACT_STATUS = ("missing", "draft", "approved", "stale")
PHASES = ("intake", "requirements", "design", "tasks",
          "implementation", "verification", "complete")
def load_state(spec_dir: Path) -> dict | None: ...  # None when .specflow.json is absent
def spec_type(spec_dir: Path, state: dict | None) -> tuple[str, list[str]]: ...   # the type, and the sources that disagree (ART-001.7)
def artifact_status(spec_dir: Path, state: dict) -> dict[str, str]: ...
def derive_phase(spec_dir: Path, status: dict[str, str], order: str) -> str: ...
def stale_causes(spec_dir: Path, state: dict) -> dict[str, str]: ...   # T-023: stale artifact -> the most upstream artifact whose change caused it

# specflow_helper/reconcile.py                                           T-024, T-025
class ConflictError(Exception): ...
def reconcile(spec_dir: Path, *, dry_run: bool) -> dict: ...
def write_guarded(path: Path, data: bytes, read_sha256: str | None) -> None: ...

# specflow_helper/checks.py                                              T-026, T-028, T-029
Finding = dict[str, str]    # keys: level ("error" or "warning"), file, rule, message, fix
class Context(NamedTuple):
    repo: Path
    config: dict[str, object]
    spec_dir: Path              # or the intake item, for phase "intake"
    state: dict | None
CHECKS: dict[str, tuple[frozenset[str], Callable[[Context], list[Finding]]]] = {}   # name -> (phases, check)
def validate(repo: Path, spec_dir: Path, phase: str | None = None) -> list[Finding]: ...
def workspace_config(repo: Path) -> dict[str, object]: ...   # the defaults until T-028 switches it to load_config

# specflow_helper/deps.py                                                T-026
def parse_depends_on(text: str, *, bugfix: bool) -> tuple[list[str], list[Finding]]: ...   # references, and declaration errors
def dependency_blockers(spec_dir: Path, specs_dir: Path) -> list[dict[str, str]]: ...

# specflow_helper/drift.py                                               T-022, T-026
def code_baseline(repo: Path, paths: list[str]) -> dict: ...     # an approvedCode value
def code_drift(repo: Path, approved_code: dict) -> list[dict[str, str]]: ...

# specflow_helper/status.py                                              T-026
def markers(text: str) -> list[str]: ...            # open marker lines of one artifact
def status(repo: Path, spec_dirs: list[Path]) -> dict: ...   # the document of the status schema

# specflow_helper/config.py                                              T-028
class ConfigError(Exception): ...
def load_config(repo: Path) -> dict[str, object]: ...   # root, specsDir, numberScan, defaults applied

# specflow_helper/numbers.py                                             T-029
def next_number(repo: Path, config: dict[str, object]) -> str: ...
def number_clashes(repo: Path, config: dict[str, object]) -> list[Finding]: ...
```

- A check is a function registered in `CHECKS` under its name, the `<check-name>` of a `validator:<check-name>` entry in the rule inventory (00005). `validate` runs every check that applies to the phase and returns their findings; an `error` makes the exit code 1, a `warning` never does. 00005 (T-071) and 00006 (T-039) add checks to the same registry.
- What the helper writes: `reconcile` without `--dry-run` writes `.specflow.json` in the given spec directory, and only derived facts: each artifact's `sha256`, and a `status` of `missing`, `draft`, or `stale`. It changes those values and nothing else: every other key, unknown ones included, keeps its value and its place, and the file is written with two-space indent and a final newline. It never creates a state file and never replaces a malformed one; in both cases it reports what it found and what needs the developer. Both forms return, and print with `--json`, one object: `spec`, `statuses`, `phase`, `changes` (what was or would be written), and `ambiguous` (what needs a confirmation). It never writes `approved`, `approvedSha256`, `approvedAt`, `approvedCommit`, `approvedCode`, `acceptedMarkers`, or `hold`; those record a developer's decision, and the agent writes them after an explicit answer, using `hash` and `code-baseline` for the values. Every other operation is read-only.
- Every write goes through `write_guarded`: it compares the file's current SHA-256 with the one read at the start of the operation and raises `ConflictError` when they differ, leaving the file as it is.

### Schema checking

The three schema files are the one description of the state, the config, and the status output, and the helper checks against them directly. `check_schema` implements the part of JSON Schema draft 2020-12 those files use and nothing more: `type`, `const`, `enum`, `required`, `properties`, `additionalProperties` as a boolean, `items`, `pattern`, `minLength`, `oneOf`, `$defs`, and `$ref` to a `#/$defs/<name>` in the same file, with keywords beside a `$ref` applied as well. It ignores the annotations `$schema`, `$id`, `title`, and `description`. Any other keyword is an error, not a silent pass. A boolean is not an integer, and a pattern must match the whole string. Each returned string names the path of the failing value. Unknown properties are allowed everywhere, so a field from a later version survives (STATE-001 criterion 6). Each schema file carries its public address as `$id` from the task that writes it (ruling D13 of 2026-10-04): `https://raw.githubusercontent.com/buvis/agent-plugins/specflow-v<version>/plugins/specflow/skills/spec-workflow/schemas/<file>`, with the manifest version and the file's own name. The address resolves once the release tag is pushed, and nothing fetches it at runtime.

Fields of the state schema, version 1 (the example and prose under Data model give their meaning):

| Field | Type | Required | Values |
|---|---|---|---|
| `schemaVersion` | integer | yes | `1` |
| `specId` | string | yes | the spec folder's name |
| `specType` | string | yes | `feature`, `bugfix` |
| `profile` | string | yes | `standard`, `quick` |
| `workflowOrder` | string | yes | `requirements-first`, `design-first` |
| `workflowVersion` | string | yes | the plugin version that wrote the state |
| `artifacts.requirements`, `artifacts.design`, `artifacts.tasks` | object | yes | an artifact record |
| artifact record: `path` | string | yes | file name inside the spec folder; `bugfix.md` for a bugfix spec's requirements slot |
| artifact record: `status` | string | yes | `missing`, `draft`, `approved`, `stale` |
| artifact record: `sha256`, `approvedSha256` | string | no | 64 lowercase hex digits |
| artifact record: `approvedAt` | string | no | UTC timestamp, `YYYY-MM-DDTHH:MM:SSZ`, with optional fractional seconds |
| artifact record: `approvedCommit` | string | no | a commit id |
| artifact record: `acceptedMarkers` | array | no | objects with `artifact` (`requirements` or `design`) and `line` |
| `artifacts.design.approvedCode` | object | no | one of the three shapes under Code drift: `captured` with `files`, `not_checked` with `reason`, `not_applicable` with `reason` |
| `hold` | object | no | `status` (`on_hold`, `abandoned`), `reason`, `since` (`YYYY-MM-DD`) |

Fields of the config schema: `schemaVersion` (integer, `1`, required), `root` (string), `specsDir` (string), `numberScan` (array of strings). A schema that lets unknown fields through cannot keep secrets out, so STATE-001 criterion 3 has its own check, `state-content`: it fails a state file that has a key named `transcript`, `prompt`, `messages`, `conversation`, `sessionId`, `session_id`, `token`, `secret`, `password`, `credential`, or `apiKey` at any depth, or a string value that is an absolute path (a leading `/`, `~`, or a drive letter). Three free-text fields are not checked for paths, since an accepted marker or a reason may start with `/`: `acceptedMarkers[].line`, `hold.reason`, and the `reason` of `approvedCode`. The scan is `check_content` in `schema.py`, built and tested in T-021; T-026 registers it as a check.

Fields of the status schema, beyond what the example below shows:

| Field | Type | Meaning |
|---|---|---|
| `specs[].gates` | object | the keys are the three things a gate opens: for Requirements-First `design`, `tasks`, `implementation`; for Design-First `requirements`, `tasks`, `implementation`; each `open` or `closed` |
| `specs[].blockers[]` | object | `gate`, `reason`, and, for a spec dependency, `reference` and, for a cycle, `path` |
| `specs[].warnings[]` | object | `kind` (`code-drift` or `not-checked`), `message`, and `path` when one file is meant |
| `specs[].profile` | string or null | null when the spec has no state file; such a spec also carries a blocker with the reason `state missing` |
| `specs[].nextTask` | object or null | the first unchecked item in document order, sub-tasks included, whose `Depends on:` tasks are all checked; a task with unchecked sub-tasks is not itself next |
| `problems[]` | object | repository-level findings that belong to no one spec, each with `rule`, `message`, and `fix`: an ignored specs folder, specs left in a real `.kiro/specs/`, a number clash |
| `intake[]` | string | the names of intake items under `intake/new/` that have no spec folder; this is the only place the phase `intake` shows |

`status` exits 1 when `problems` is not empty or a spec's state is malformed or of an unsupported version, and still prints the document. This is the one case where malformed state is not exit 2, which `status` keeps for an error that stops the whole run (configuration, git). A missing state file alone leaves the exit code 0. `status` runs the checks `specs-folder` and `number-clashes` when they are registered, once per run, and puts their findings in `problems`. It and `validate` take the config from `workspace_config` in `checks.py`, which returns the defaults until T-028 switches it to `load_config`, so later tasks need no edit to `status.py`.

### Checks built in this spec

`validate` runs the checks registered for the phase. These are built here; 00005 (T-071) adds the placeholder, marker, link, fence, and source checks, and 00006 adds the sketch, placement, and bugfix checks. A requirement ID is `<PREFIX>-NNN` or Kiro's own numbering, whichever the file already uses; the `REQ-` of the carried text is one such prefix.

| Check name | Clause | Level | Phases | Task | Rule |
|---|---|---|---|---|---|
| `required-files` | VAL-001.1 | error | all | T-026 | the artifacts the phase needs exist and can be read |
| `state-valid` | VAL-001.1 | error | all | T-026 | the state file passes the state schema and its version is supported |
| `state-content` | STATE-001.3 | error | all | T-021, registered by T-026 | as defined above |
| `spec-type` | ART-001.7 | error | all | T-022, registered by T-026 | `.config.kiro`, the state, and the files present name one spec type; a disagreement is reported and nothing is rewritten |
| `requirement-ids` | VAL-001.2 | error | requirements on | T-026 | every requirement has a stable, unique ID and one acceptance criterion or more |
| `design-sections` | VAL-001.3 | error | design on | T-026 | every template section has content or `Not applicable: <reason>`; every requirement or criterion ID in the criteria column of `## Requirement traceability` exists in the spec's own requirements artifact. The column is the one headed `Criteria` or `Criterion`; an entry in the cross-spec form of Tasks structure, and an entry that is not an ID, are not checked. The section is found through `scan_lines`, so the same heading inside a fenced template is not it. Citations elsewhere in the design are not checked, so prose may name a criterion another spec holds |
| `task-structure` | VAL-001.4 | error | tasks on | T-026 | stable task IDs, checkbox syntax, dependencies that name earlier tasks, a requirement reference and a verification per task |
| `requirement-coverage` | VAL-001.4 | error | tasks on | T-026 | every requirement is referenced by a task |
| `progress-fields` | VAL-002.5 | warning | tasks on | T-026 | no `Outcome:` or `Exception:` line under a task item while the task plan is not approved |
| `cross-spec-references` | VAL-001.13 | error | tasks on | T-026 | every reference of the cross-spec form names a spec on the `Depends on:` line and a requirement and criterion that spec holds; the prerequisite is read, never written |
| `gates` | VAL-001.5 | error | implementation | T-026 | tasks approved, no stale upstream artifact, the spec-dependency gate open |
| `spec-dependencies` | VAL-001.8 | error | implementation, and any run with no phase | T-026 | the dependency grammar and graph |
| `specs-folder` | VAL-001.8 | error | all | T-028 | no specs left in a real `.kiro/specs/` beside a configured folder; the specs folder is not ignored by git |
| `number-clashes` | VAL-001.8 | error | all | T-029 | no number used by two intake items or two spec folders |
| `sources-line` | VAL-001.8 | error | requirements on | T-029 | a `Sources:` line that names an intake item with the spec's own number |

Every finding carries the file, the rule, and the corrective action (VAL-001 criterion 6), and `validate` writes nothing (criterion 7).

### Status output for external runners

Source: `qa-log.md` Q2 (STATE-003). `validate_spec.py status --json` is the only interface an external runner needs; it follows `schemas/specflow-status.schema.json`:

```json
{
  "statusVersion": 1,
  "specs": [
    {
      "spec": "00042-portable-spec-workflow",
      "specType": "feature",
      "profile": "standard",
      "phase": "implementation",
      "hold": null,
      "artifacts": {"requirements": "approved", "design": "approved", "tasks": "approved"},
      "gates": {"design": "open", "tasks": "open", "implementation": "open"},
      "blockers": [],
      "warnings": [],
      "nextTask": {"id": "T-004", "title": "Add the retry file writer"}
    }
  ]
}
```

- A gate is `open` when the phase may start: its upstream artifacts are approved and current. `blockers` lists each file-derived reason a gate is closed: a missing, draft, or stale upstream artifact, a validation failure, or a specs-folder problem (§6.7). An upstream marker with no `acceptedMarkers` entry (WF-002.7, §7.1) never closes the gate that lets drafting start. It blocks the dependent artifact's approval, so it is listed as a blocker of the gate after that artifact. An incomplete direct prerequisite or a dependency error from §6.2 closes only the implementation gate (WF-001.9); status names the referring spec, reference, and reason. A cycle includes its path. Dependency blockers neither change the phase nor stale approvals; valid prerequisites permit earlier drafting and approval gates normally. Open review blockers live in `qa-log.md` and are not parsed.
- `warnings` lists advisory, file-derived notes that close no gate, such as code drift from the design approval's content baseline or evidence that could not be checked (WF-004.8).
- `nextTask` is the first unchecked task in document order whose `Depends on:` tasks, if it lists any, are all checked, and only while the implementation gate is open; otherwise `null`. Document order also covers bugfix specs and Kiro-numbered tasks, which carry no `Depends on:` lines. A held spec reports its hold and no `nextTask`.
- The output is computed from files alone (STATE-001.5) and is read-only. Nothing in it, or in the helper, records an approval.
- `statusVersion` changes on any breaking change to the shape, with a changelog entry (REL-001.6).

The autopilot repoint is autopilot's own work (a claude-autopilot PRD, handed off by T-066); nothing in the runtime skill names it.

## Data model

### Directory

```text
.kiro/specs/NNNNN-<title>/
├── requirements.md
├── design.md
├── tasks.md
├── .config.kiro        # Kiro's own type marker (§6.5)
└── .specflow.json
```

The parent is the specs folder: `.kiro/specs/` by default, or the folder `.agents/specflow.json` names (§6.7). A path written `.kiro/specs/...` in this document means the specs folder.

The directory name is chosen once. Renaming requires an explicit migration because external links and host UIs may reference it. A Kiro-native spec folder without a number is valid; specflow resumes it as it is and never renames it to add one.

Other files in the folder, such as another tool's sidecar, belong to their owners: specflow never edits, hashes, or approves them (ART-001.9).

Structure stays English: headings, IDs, field names, EARS keywords, markers such as `(guess)`, and file names never follow the developer's language, while prose may (ART-001.11). The validator, the hash rules, and Kiro all match those tokens.

### Requirements structure

```markdown
# Requirements: <Feature>

Sources: <intake item path>[, <spike folder or branch>]
Supersedes: NNNNN            (only when reworking a complete spec)
Blocks: <what waits on this> (only when it blocks other work)
Depends on: 00012, folder:login-fix

## Purpose
## Scope
## Assumptions

### REQ-001: <Title>
Source: <the idea | a Q&A entry such as Q3 | a discovery finding such as D1>
**User story:** As a ..., I want ..., so that ...

#### Acceptance criteria
1. WHEN ... THE SYSTEM SHALL ...

## Non-functional requirements
## Risks
- <risk>: impact <h/m/l>, likelihood <h/m/l>; mitigation: ...; fallback: ...
## Out of scope
## Unresolved questions
```

Requirement identifiers never change merely because sections are reordered. Deleted identifiers are not reused within the spec. Every requirement is required; there are no priority tiers (ART-002.8). A section that does not apply is left out, never filled with a placeholder (ART-001.10). `## Risks` holds risks known at requirements time; technical risks found later go to design (ART-002.7). A contract detail the developer did not give stays marked `(guess)` until confirmed (ART-002.10).

Each requirement names its source: the idea, a Q&A entry, or a discovery finding. Anything without one is a `(guess)` or an assumption, and an option the developer did not choose decides nothing (ART-002.15). The validator warns on a requirement with no `Source:` line and never fails on it, since a Kiro-made document has none (VAL-001.12). Applicable hard rules from repository instructions are recorded as constraints with their source file and scope preserved (WF-003.17, §6.7), and so are confirmed working practices (WF-003.18).

**Spec dependencies (release 0.1; decision 2026-10-03 #13).** These are implementation prerequisites, separate from task dependencies and `Blocks:`/`Supersedes:`. Agent and helper use this same contract:

- At most one unindented `Depends on:` line appears before the first level-two heading in a feature's `requirements.md`, or at the end of `## Introduction` in `bugfix.md`, before `Sources:` if present (§6.6). Both placements apply to native specs without replacing their headings or IDs. Absence means no prerequisites; an empty or repeated declaration is invalid. Fenced examples, indented/list-item fields, and fields in `tasks.md` do not declare spec dependencies; an unindented declaration elsewhere in the requirements artifact is a misplaced-declaration error.
- The value is a comma-separated list, with surrounding whitespace trimmed from each item. An item is exactly five ASCII digits (resolving one immediate spec folder with that number under §6.7), or `folder:<basename>` matching one immediate spec folder's exact name. Folder references support native names without renumbering. Basenames cannot be empty, `.` or `..`, contain a comma, slash or backslash, or resolve outside the configured specs folder. Other forms are unsupported; no URLs, cross-repository paths, or title guessing. Repeated references resolving to the same folder count once.
- Resolve references only against the configured specs folder. Missing or ambiguous matches, unreadable targets, and targets whose shape or state cannot be reconciled are named dependency errors. Read each reachable spec once per invocation, using ordinary artifact/hash reconciliation (§7.5), without writing it or adopting its approvals. Detect self-reference and cycles by resolved folder identity; report the path, such as `00012-a → login-fix → 00012-a`, rather than waiting or recurring indefinitely. Invalid references or cycles anywhere in this reachable graph close the selected spec's implementation gate.
- Each direct prerequisite must independently reconcile to phase `complete`. Dependency evaluation does not recursively redefine phase or reopen a completed prerequisite because its own prerequisite later became incomplete. Only the selected spec's implementation gate and `nextTask` change; its phase and approvals do not. Dependency findings are implementation checks: `validate --phase` for earlier phases does not fail on them; unfiltered validation reports them. Editing its own declaration remains an ordinary requirements edit subject to hash invalidation. Diagnostics name the referring spec, reference, and reason; status orders them by declaring folder and source-list order for repeatable output. No scheduler or persisted dependency state is added.

### Design structure

```markdown
# Design: <Feature>

## Overview
## Context and constraints
## Architecture
## Module placement
## Components and interfaces
## Data model
## Data and control flow
## Error handling
## Security and privacy
## Testing strategy
## Rollout and migration
## Risks and edge cases
## Requirement traceability
## Alternatives considered
## Reuse inventory
## Open decisions
```

Not every section needs extensive content, but a concern that does not apply keeps its heading and reads `Not applicable: <reason>`; the validator fails an empty reason (ART-001.10). This is the one artifact that keeps unused sections, because the design review must tell "no security concern" from "forgot security". `## Risks and edge cases` holds technical risks in the same one-line shape as the requirements `## Risks`.

### Tasks structure

```markdown
# Tasks: <Feature>

- [ ] T-001 Implement ...
  - Requirements: REQ-001, REQ-003
  - Depends on: none
  - Location: <bounded repo-relative paths>
  - Reuse: <helpers and use, from design>           (when applicable)
  - Premise: <stated observed state, verbatim>      (when applicable; required for delete/rewrite based on state)
  - Contract: <applicable design contract, verbatim>
  - Details: <specific change and boundaries>
  - Acceptance criteria: REQ-001 criteria 1, 2; REQ-003 criterion 1
  - Risk: <actual risky change and design mitigation> (when evidenced)
  - Verify: <command, test, or file check this task owns>
  - Outcome: <observed result, written during implementation>   (progress field, not hashed)
  - Exception: <accepted verification exception and rationale> (progress field, not hashed)
  - [ ] T-001.1 ...

## Completion criteria
## Unresolved questions
```

Top-level tasks use stable IDs. Checkbox state is durable progress. A task is checked only after its verification succeeds or an exception is documented. `Outcome:` and `Exception:` are progress fields: the agent writes them during implementation, `canonical` drops them from the hash (§7.3), and the validator warns when either appears in a plan that is not yet approved. `Depends on:` names existing earlier task IDs in topological order; create IDs before referencing them, and add a later-discovered dependency without guessing an ID. Re-planning keeps checked tasks and their IDs. Existing Kiro-native and bugfix tasks keep their numbering, fields, and fixed order; add applicable planning detail inside those task items, never replace their shape.

Three additions to the shapes above:

- The requirements template has a `## Requirements` heading above the first requirement block, as Kiro's own documents do; without it the blocks would sit under `## Assumptions` (finding F6, approved with the requirements).
- A task may cite a criterion of a spec its own spec depends on (ART-004.16 of 00006). On a `Requirements:` or `Acceptance criteria:` line the form is `<spec reference> <requirement ID> criterion <n>`, or `criteria <n>, <m>`, where the spec reference follows the `Depends on:` grammar: `00004 WF-004 criterion 8`. A requirement ID with no spec reference before it belongs to the task's own spec.
- T-020 also writes two templates whose shapes other sections of the source gave: `templates/intake/SPEC.md` with `## Idea`, `## Smallest end-to-end outcome`, and `## Guessed contract`; `templates/cross-spec-review.md` with `## Verdict`, `## Spec map`, `## Findings`, `## Reshapes`, `## Gaps`, `## End state`, and `## Decisions applied`. T-028 writes `templates/specflow.json`, the config example under Workspace root without its `numberScan` line.

### Kiro-native compatibility

Kiro creates spec shapes beyond the feature/Requirements-First default. The workflow never converts one shape into another.

Kiro marks the shape in an undocumented per-spec file, `.config.kiro`: `{"specId": "<uuid>", "workflowType": "requirements-first", "specType": "bugfix"}` (captures in the bugfix discovery doc §1.1). On create, the workflow writes `.config.kiro` (new UUID, `workflowType` `requirements-first` or `design-first`, `specType` `feature` or `bugfix`) and mirrors `specType` in `.specflow.json`. On read, the type comes from `.config.kiro`, else `.specflow.json`, else the files present; a disagreement is reported, never auto-fixed (ART-001.7). `.config.kiro` is not a canonical artifact: it is not hashed and carries no approval.

- **Bugfix specs**: `bugfix.md` fills the requirements slot; the workflow creates, validates, and resumes them in Kiro's shape (§6.6). It never creates `requirements.md` beside an existing `bugfix.md`; state records the slot's actual path.
- **Design-First specs**: `design.md` precedes requirements. specflow creates both orders: intake recommends one (WF-003.10, `requirements-first` by default), the developer may override it before the first artifact, and state records it once as `workflowOrder`. The gate rule is "an artifact's upstream must be approved", where upstream follows that order: the design is drafted from the intake item, requirements from the approved design, tasks from both, and the invalidation graph mirrors (§7.4).
- **Identifier schemes**: IDs are validated against the scheme the file already uses (Kiro-native numbering or `REQ-`/`T-` IDs). The workflow never renumbers an existing document; new specs use `REQ-`/`T-` IDs.

The exact Kiro-native formats are verified against a real Kiro-generated spec of each type before implementation; the fixtures in §15 come from those captures.

### Bugfix spec shape

Mirrors Kiro exactly (ART-005). Sources and line references: `discovery/00001-specflow-bugfix-workflow.md` §1.

`bugfix.md`:

```markdown
# Bugfix Requirements Document

## Introduction
<what breaks, where, impact; may name the suspected cause>

Sources: <intake item path>

## Bug Analysis

### Current Behavior (Defect)
1.1 WHEN <condition> THEN the system <incorrect behavior>

### Expected Behavior (Correct)
2.1 WHEN <condition> THEN the system SHALL <correct behavior>

### Unchanged Behavior (Regression Prevention)
3.1 WHEN <condition> THEN the system SHALL CONTINUE TO <existing behavior>
```

Kiro sometimes adds `## Bug Condition and Properties` to `bugfix.md`; the validator accepts it there or in `design.md`. The `Sources:` line closes `## Introduction`, so the Kiro skeleton stays intact (INT-001.6). When prerequisites exist, insert the optional `Depends on:` line immediately before `Sources:` (or last in Introduction if no `Sources:` exists), using §6.2's grammar. No heading or numbered behavior clause changes.

Bugfix `design.md` (sections beyond these are allowed):

```markdown
# <Title> Bugfix Design

## Overview
## Glossary                      Bug_Condition (C), Property (P), Preservation
## Bug Details
### Bug Condition                isBugCondition(X) pseudocode
### Examples
## Expected Behavior
### Preservation Requirements
## Hypothesized Root Cause
## Correctness Properties        Property 1: Bug Condition (Validates 2.x)
                                 Property 2: Preservation (Validates 3.x)
## Fix Implementation
### Changes Required
## Testing Strategy
### Validation Approach
### Exploratory Bug Condition Checking
### Fix Checking                 FOR ALL X WHERE isBugCondition(X): fixed code satisfies P
### Preservation Checking        FOR ALL X WHERE NOT isBugCondition(X): F(X) = F'(X)
### Unit Tests
### Property-Based Tests
### Integration Tests
```

Bugfix `tasks.md`:

```markdown
# Implementation Plan

- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - <title>
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **EXPECTED OUTCOME**: Tests FAIL
  - Document counterexamples found
  - _Requirements: 1.x_
- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - <title>
  - Observe: <behavior> on unfixed code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - _Requirements: 3.x_
- [ ] 3. Fix <bug>
  - [ ] 3.1 <change>
    - _Bug_Condition: ..._ _Expected_Behavior: ..._ _Preservation: ..._
    - _Requirements: 2.x, 3.x_
  - [ ] 3.2 Verify bug condition exploration test now passes (re-run the SAME tests from task 1)
  - [ ] 3.3 Verify preservation tests still pass (re-run the SAME tests from task 2)
- [ ] 4. Checkpoint - Ensure all tests pass
```

### Workspace root, intake items, and the specs folder

Source: decision 2026-09-27 #1-3, Plan A ELI-28 and RDS-04 rulings, `qa-log.md` Q3, decision 2026-10-03 #6 (INT-001).

An optional repository file, `.agents/specflow.json`, moves the workspace root and the specs folder:

```json
{
  "schemaVersion": 1,
  "root": "docs/dev/project-management",
  "specsDir": "docs/dev/project-management/specs",
  "numberScan": ["docs/dev/project-management/prds"]
}
```

`numberScan` lists extra repository folders whose five-digit prefixes count when a new spec number is claimed, so a repository that still numbers other documents (buvis PRDs, until the autopilot repoint) never reuses one of their numbers. The plugin itself names no such folder. All paths are repository-relative with forward slashes. The file comes with the repository, so a cloned repository controls it: a path that is absolute, holds a `..` segment, or resolves outside the repository is refused before any use, with the path named (SEC-002.5). Without the file, the root is `.kiro/specflow` and the specs folder is `.kiro/specs/`. The file sits under `.agents/`, not `.kiro/`, so a repository that commits no agent-private folder still carries it. The example is the buvis setting.

```text
<root>/
├── intake/
│   ├── new/
│   │   └── NNNNN-<title>/
│   │       ├── idea.md          # First input, verbatim; claims the number
│   │       ├── qa-log.md        # Questions, answers, review minutes
│   │       ├── <other inputs>   # Any source, any format
│   │       └── spike/           # Spike path only (§6.8)
│   └── processed/
│       └── NNNNN-<title>/       # Moved here when the requirements artifact is first written
└── reviews/
    └── YYYY-MM-DD-cross-spec-review.md
```

Intake items may sit one folder deeper (for example one group per plugin in a monorepo), at most one level; the move to `processed/` keeps the group folder, `Sources:` names the full `processed/` path, and the number scan is recursive (INT-001.2).

**Moving an item.** When the requirements artifact is first written, the agent moves the item to `processed/` first, then writes the artifact with `Sources:` naming the `processed/` path (and any spike folder inside it). "Processed" therefore means "has a spec", not "approved".

**Spec numbers.** `next-number` scans `<root>/intake/**`, `.kiro/specs/*`, and every `numberScan` folder for names that start with five digits and a hyphen, takes the highest, and adds one. The agent writes the new item, then scans again; on a clash it renames its own new item before anything cites the number. An intake item and its spec share a number but may carry different titles. Validation reports a clash when two intake items, or two spec folders, use one number, or when a spec's `Sources:` line names an intake item with another number. Kiro-native folders without a number are skipped. A split gives each new spec its own number and its own intake item, whose `idea.md` names the item it came from (Plan A ELI-59; this replaces RPB-100's shared item).

**Q&A log.** `qa-log.md` gets one entry per question, appended right after the answer, and one `## Review: <artifact> <date>` block per review (§5.5):

```markdown
## Q3 - Error budget (2026-10-01)
- Question: What failure rate is acceptable for the nightly import?
- Answer: "Under 0.1% of rows for this release; failures go to a retry file. Revisit the budget for the next release after the pilot."
- Reading: this release requires failures below 0.1% of rows and a retry file.
- Follow-up: revisit the next release's budget after the pilot; no unresolved current requirement.

## Q7 - Error budget, replaces Q3 (2026-10-02)
- Question: Is 0.1% still the budget after the pilot numbers?
- Answer: "Make it 0.5%, the pilot showed 0.1 is not realistic."

## Discovery 2026-10-01
- Classification: existing code (package manifest, `src/`).
- Read in full: `src/import/`, `tests/import/`. Skimmed: `src/api/`. Not looked at: `docs/`, `infra/`.
- D1: nightly import retries are hand-rolled in `src/import/retry.py`.

## Review: design.md 2026-10-02
- 1 | Blocking | No rollback for the schema change | option 1 applied | resolved
- 2 | Question | Who owns the retry file? | disputed: owner is named in §5 | disputed
```

The `Answer:` line holds the developer's own words, caveats included; the agent's interpretation goes on a `Reading:` line, so the next tool sees what was said and not a paraphrase. The log is append-only: a changed answer is a new entry that names the one it replaces, and earlier entries are never edited. A secret in an answer is left out and the omission noted (SEC-002.2). A profile raise is logged here too (WF-003.14). While asking, the agent says where the questioning stands, for example "question 3 of about 8" (ART-002.14). Every question offers a "not decided yet" choice, which records an unresolved question; questions use the developer's words and define a term of art where it first appears (ART-002.16-17).

**Input files.** An input given as a file needs exactly one explicit path: the agent asks when it is missing or matches more than one file and never picks a match. The file is copied into the intake item. When it is binary, too large to read, or outside the repository, its location goes into `idea.md` with a note of what could not be read (INT-001.8).

A spec with no intake item (for example one Kiro created) gets `<root>/intake/processed/<spec-folder>/qa-log.md` on its first question.

**The specs folder.** Every operation resolves the specs folder from the config once and reads and writes there directly, on every host; `.kiro/specs/...` in this document means that folder. specflow never creates or repairs a `.kiro/specs` link and never depends on one (ART-001.8); the specs folder path, link or not, must resolve inside the repository (SEC-002.5). When `specsDir` is set, Kiro IDE's spec panel lists the specs only if `.kiro/specs` points at that folder. Making that link is the repository's own setup (its onboarding command, or one `ln -s` by hand), not the plugin's. It must be a link, never a copy: Kiro writes into `.kiro/specs`, and writes into a copy would not reach the real folder. Whether Kiro IDE lists specs through a link is verified in T-027; until then it is an assumption. If it does not, a configured specs folder is documented as invisible to Kiro's spec panel, while the skill itself keeps working there.

`status` and `validate` report two cases, each with the fix: specs sitting in a real `.kiro/specs/` folder while `specsDir` names another folder (for example a spec Kiro created before the link existed), and a specs folder that git ignores, since specs there would never be committed. Neither is repaired automatically, and the two folders are never merged.

### State model

### Example `.specflow.json`

```json
{
  "schemaVersion": 1,
  "specId": "00042-portable-spec-workflow",
  "specType": "feature",
  "profile": "standard",
  "workflowOrder": "requirements-first",
  "workflowVersion": "0.1.0",
  "artifacts": {
    "requirements": {
      "path": "requirements.md",
      "status": "approved",
      "sha256": "<hex>",
      "approvedSha256": "<same-hex>",
      "approvedAt": "2026-09-27T12:00:00Z",
      "approvedCommit": "<HEAD at approval, when it exists>"
    },
    "design": {
      "path": "design.md",
      "status": "draft",
      "sha256": "<hex>"
    },
    "tasks": {
      "path": "tasks.md",
      "status": "missing"
    }
  }
}
```

The example carries no `$schema` key: no instance file does in this release (00001), and each schema's own address is its `$id`, given under Schema checking.

An optional `"hold": {"status": "on_hold", "reason": "<why>", "since": "2026-10-01"}` (status `on_hold` or `abandoned`) is set and cleared only on explicit developer instruction (STATE-001.7). A held spec keeps its derived phase; status shows the hold, and the agent does not offer it as next work (WF-001.8).

`profile` may be raised from `quick` to `standard` after intake, by the developer or on the agent's proposal when a WF-003.6 trigger shows up late (WF-003.14). The raise stales nothing; later questions and reviews run at standard depth, and the Q&A log records it.

Each approval records HEAD as `approvedCommit` when it exists. An unborn Git repository omits that field; missing or shallow history does not prevent approval. The commit is provenance, not the content baseline for the drift check.

**Code drift (WF-004.8; decision 2026-10-04 #3).** In a Git repository, design approval captures the current bytes of the explicitly named repository files in `## Module placement`, or the matching placement section of a native/bugfix design. Store hashes, never source content, on that design approval:

```json
{
  "approvedCode": {
    "status": "captured",
    "files": [
      {"path": "src/import.py", "sha256": "<SHA-256 of raw file bytes>"},
      {"path": "src/new_retry.py", "missing": true}
    ]
  }
}
```

Paths are exact repo-relative files, sorted and deduplicated; no globs or recursive folder scan. The approving agent supplies the explicit paths from the design's placement section to the read-only `code-baseline` operation; the helper validates and hashes them, returning an `approvedCode` value without recording an approval. A captured or not-checked result exits 0; missing required CLI arguments remain a usage error. Ambiguous placement is not checked, never guessed. The set records approval-time evidence, not a second list of scope decisions. Validate containment before reading; absolute paths, `..`, symlinks in any path component, directories, and special files are not followed. A declared file that does not exist has `missing: true`; all existing regular files are hashed, including staged, unstaged, and untracked content. Capture uses the same before-write consistency check as approval (WF-006), with no lock or forced commit. A stale design approval reports the baseline as not checked until reapproval; it cannot claim coverage for the changed design.

On resume and before implementation, compare the declared files' current raw hashes/existence with `approvedCode`. Added, modified, and deleted files raise path-specific advisory warnings; no approval or phase changes. Reapproval replaces the baseline, so unchanged working bytes immediately after reapproval produce no drift even at the same HEAD. A later commit of those same bytes also produces no drift. An unreadable/unsupported path, a missing placement section, or an old approval without a baseline yields a path/reason-specific `not checked` warning, never a clean result; capture failure records `{"status":"not_checked","reason":"<paths and reason>"}` instead of a partial baseline. Reapproval does not clear an unavailable-evidence warning unless capture succeeds. When the design explicitly has no affected files, record `{"status":"not_applicable","reason":"<design's stated reason>"}`. Without Git, omit both Git provenance and this baseline and do not run this Git-scoped advisory. No historical Git object is needed for comparison.

An approval of `design` or `tasks`, or in Design-First of `requirements`, may carry `"acceptedMarkers": [{"artifact": "requirements", "line": "<exact canonical line>"}]`, one entry per upstream marker the developer accepted by name (WF-002.7). A marker is any `(guess)` outside inline code and fenced blocks, any list item under `## Unresolved questions`, or any list item under `## Open decisions` (decision 2026-10-04 #10). For a list item that spans several lines, the recorded line is its first. An entry counts only while that exact line still exists in the named artifact, so a reworded marker is asked again, and a stale approval drops its acceptances with it. The rationale goes to the approval summary and the intake item's `qa-log.md`, not to state; recovery mode (§7.5) asks again for any acceptance it cannot find.

State holds only facts that cannot be derived from the files. The current phase is always computed (§7.5), never stored. The plugin's upstream AWS pin is a fact about the plugin build, already implied by `workflowVersion`, so it does not appear in project state. There is no document-level `updatedAt` or revision counter, so writes that only touch different artifacts do not conflict on merge. An edit made between a read and a write is caught by comparing file hashes before writing; one active writer per spec is the contract, and there is no lock (WF-006).

### State precedence

1. Markdown controls artifact content.
2. `tasks.md` controls task completion.
3. State controls approvals against hashes, their accepted markers, and the hold, only; the phase is always derived.
4. A hash mismatch invalidates state; state never overwrites Markdown to regain consistency.

### Approval representation

Approval is bound to content:

```text
approved := status == "approved"
            AND sha256(canonical(current text)) == approvedSha256
```

`canonical` makes hashes stable across machines and editors:

1. Decode as UTF-8 and drop a leading byte-order mark.
2. Normalize CRLF and CR line endings to LF.
3. Strip trailing whitespace from every line.
4. End with exactly one final newline.
5. For `tasks.md` only, outside fenced code, normalize the checkbox of a list item (`[x]` or `[X]` directly after the list marker) to `[ ]`, so recording progress does not invalidate the approved plan. A `[x]` anywhere else in a line, or inside a fence, stays as written.
6. For `tasks.md` only, outside fenced code, drop a list line whose first token after the list marker is `Outcome:` or `Exception:` when it is nested under a checkbox item: the two progress fields of §6.4. The same words inside a fence, or outside a task item, stay hash-bound.

Steps 5 and 6 track fences line by line. They exclude only parsed progress, so an edit to a literal example, a command, or a contract in an approved plan always stales it (decision 2026-10-03 #9). An artifact whose fence never closes fails validation and cannot be approved (VAL-001.11), so a stray fence cannot hide the rest of a plan from the hash or from the placeholder scan.

Approval responses are not copied into state. Approval metadata retains the fact, timestamp, approved artifact hash, optional commit provenance, design code baseline, and accepted upstream markers (§7.1). Code hashes describe approval-time evidence only; Markdown still owns scope and content.

Details the six steps leave open, pinned so that two implementations hash alike. Each is a case in `test_canonical.py`.

- Lines are split on line feed only, after step 2; a form feed stays inside its line.
- Step 3 strips spaces and tabs only; a no-break space stays.
- Step 4 removes every blank line at the end before it adds the one final newline.
- A fence opens on a line whose first characters after any indent are three or more backticks or tildes, and closes on the next line that starts, after any indent, with the same character at least as many times. A longer fence can hold a shorter one.
- A checkbox item is a list item whose marker (`-`, `*`, `+`, or a number with `.`) is followed by one or more spaces and then `[x]`, `[X]`, or `[ ]`.
- A task item is a checkbox item above `## Completion criteria`. It runs until the next non-blank line that is indented no deeper than its own marker; blank lines do not end it, and a tab counts as four columns. An `Outcome:` or `Exception:` list line inside a task item is dropped, at any depth. Three cases fix the reading: with a task at column 0, `- Details:` at 2, and `- Outcome:` at 4, the line is dropped; with a task at 0, a plain `- Notes` item at 0, and `- Outcome:` at 2, the line is kept, since the plain item ended the task; a blank line between a task and its `Outcome:` changes nothing. Under a completion criterion the checkbox is normalized and such a line is kept.

These rules are part of the approval semantics: a change to them stales every recorded approval, so it is a breaking change under the versioning policy of 00001.

## Data and control flow

### Invalidation graph

```text
Requirements-First order:

requirements changed
    └── requirements stale
        ├── design stale
        └── tasks stale

design changed
    └── design stale
        └── tasks stale

Design-First order (requirements downstream of design):

design changed
    └── design stale
        ├── requirements stale
        └── tasks stale

requirements changed
    └── requirements stale
        └── tasks stale

Both orders:

task plan changed (checkbox state and progress fields excluded)
    └── tasks stale
        └── implementation gate closed
```

Implementation changes do not invalidate the plan automatically. If implementation reveals a requirements or design error, the agent updates that upstream artifact explicitly, which triggers normal invalidation. In a bugfix spec, a refuted root-cause hypothesis is such an error by rule (§6.6).

### Reconciliation algorithm

1. Locate the requested spec directory.
2. Read all three canonical artifacts if present.
3. Parse state without rewriting it.
4. Compute SHA-256 over the canonical text (§7.3).
5. Compare hashes and approval hashes.
6. Propagate staleness through the dependency graph.
7. Validate task checkbox state and structural rules.
8. Determine the phase from the table below.
9. Evaluate spec dependencies under §6.2 using the prerequisite specs' locally reconciled phases; derive gate blockers without changing the phase from step 8. Show the developer the reconciled status.
10. Write repaired state only after the interpretation is unambiguous or confirmed.

**Phase derivation.** The phase is the first row that matches, read in `workflowOrder`; every input is a file fact, so each host and the status helper (§7.6) reach the same answer (STATE-001.5):

| Phase | Derived when |
|---|---|
| `intake` | the intake item is under `<root>/intake/new/` and no spec folder carries its number |
| `requirements`, `design` | the first artifact in `workflowOrder` is missing, draft, or stale; then the second |
| `tasks` | both upstream artifacts are approved and `tasks.md` is missing, draft, or stale |
| `implementation` | `tasks.md` is approved and an unchecked task remains |
| `verification` | every task is checked and a `## Completion criteria` checkbox is unchecked |
| `complete` | every task and every completion criterion is checked |

`## Completion criteria` (§6.4) holds checkboxes, normalized like task boxes (§7.3), so ticking one never stales the plan. A bugfix `tasks.md` has no such section: it is in `verification` while task 4 alone is unchecked. A Kiro-native `tasks.md` without the section skips `verification`. "Marking the spec complete" (WF-001.6) is therefore ticking the last box, never a stored field; a hold (§7.1) does not change the derived phase.

Malformed state is renamed or copied to a timestamped diagnostic file only with developer authorization; otherwise the agent leaves it in place and proposes recovery.

## Error handling

| Condition | Required behavior |
|---|---|
| One or more canonical files missing | Resume at earliest missing phase; preserve existing files |
| State missing | Enter recovery mode and reconstruct conservatively |
| State malformed | Report parse error and preserve original bytes |
| Hash mismatch | Mark affected approval and dependents stale |
| Unknown schema version | Stop state mutation; offer supported migration path |
| Concurrent file change | Stop before write and show conflict |
| Configured path absolute, with a `..` segment, or outside the repository | Refuse it before any use and name the path |
| Specs in a real `.kiro/specs/` folder while `specsDir` names another folder | Report it and name the move needed; never merge the two |
| Specs folder that git ignores | Fail `status` and `validate`; name the ignore line and the fix |
| Spec number clash | Rename the agent's own new item before anything cites it; validation reports older clashes |
| Upstream marker (`(guess)`, unresolved question, open decision) with no acceptance on the dependent approval | Allow drafting; refuse design or tasks approval and list each one |
| Input file path missing or matching several files | Ask for one explicit path; never pick a match |
| Incomplete or invalid spec dependency (§6.2) | Close only implementation, set `nextTask` to null, and name the reference and reason; include the path for a cycle. Leave dependent approvals and all prerequisite files unchanged |
| Declared code files differ from the design approval's content baseline | Warn with paths; close no gate. Reapproval captures current bytes even at the same HEAD |
| Code baseline, placement paths, or readable file evidence unavailable | Report `not checked` and the reason; never infer clean code or block an artifact approval |
| Host cannot run validator script | Run read-only (no approvals, no gate changes) and name Python 3 as the fix |

Every validation failure names the affected file, the rule, and the corrective action (the `file`, `rule`, and `fix` of a finding). Validation rewrites nothing; only `reconcile` writes, and only what Components and interfaces lists.

## Security and privacy

- No network requirement.
- No trust in state hashes without recomputation.
- No use of a configured path that is absolute or resolves outside the repository; no link is created or repaired.

- A configured path is refused when it is absolute, holds a `..` segment, or resolves outside the repository; a link that resolves inside is allowed. A code-baseline path gets the stricter list: no absolute path, no `..`, no symlink in any component, no directory, no special file. Both are checked before anything is read.
- State holds hashes and approval facts only: no transcript, prompt, secret, credential, absolute machine path, or host session identifier (STATE-001 criterion 3). The state tests seed each and expect a failure.
- The helper uses no network. It runs `git` only to read: the top level of the repository, the current commit, and whether the specs folder is ignored.
- Artifact text is data to the helper: it parses headings, list items, and fences, and runs nothing it finds.

## Testing strategy

- Requirements/design/tasks template conformance, feature and bugfix.
- Spec-type resolution from `.config.kiro`, `.specflow.json`, and file shape, including disagreement (ART-001.7).
- Stable IDs and traceability.
- State schema validation.
- Hash-based approval and invalidation graph.
- Hash exclusions: a real task checkbox and a task's own progress fields do not stale approval; a `[x]` inside a fenced command and an `Outcome:` line outside a task item do.
- Spec dependencies (§6.2): multiple numbered/native references, feature/bugfix placement in both workflow orders, absent declarations, duplicate references, unfinished/complete/stale prerequisites, missing/ambiguous/unsupported/unreadable targets, invalid prerequisite state, misplaced/empty/repeated declarations, self-reference and reachable cycles. Fenced examples and task-local fields never declare spec dependencies. Assert blocker reasons, cycle paths, `nextTask: null` when blocked, unchanged earlier gates/phase/approval records, configured-folder resolution, and no prerequisite writes or unrelated content reads. A completed direct prerequisite is judged by its local phase even if a transitive prerequisite later becomes incomplete; invalid reachable graphs still block.
- Code drift: baseline includes staged, unstaged, and untracked file bytes; unchanged dirty approval is clean, later edits warn, and reapproval at the same HEAD clears captured differences. New/deleted declared files warn, unchanged bytes later committed do not, and unborn/shallow repositories work without historical objects. Missing placement, old state without a baseline, unreadable files, and refused paths yield `not checked`; explicit no-file designs are not applicable. Native/bugfix placement uses its matching section. No check modifies phase, approvals, or source files; non-Git repositories omit this Git-scoped check. Assert containment, raw-byte hashing, no source content in state, no partial baseline labeled captured, and no implicit baseline refresh on resume.
- Recovery from missing/malformed state.
- Optimistic concurrency failure: an edit made between read and write is detected.
- Spec numbers: recursive intake scan, clash handling, Kiro-native folders skipped.
- Workspace config: defaults, a configured root and specs folder, every refused path, specs left in a real `.kiro/specs/` beside a configured folder, and an ignored specs folder.
- Placeholders per artifact, `Not applicable: <reason>` in design only, and the `Sources:`, `Supersedes:`, and `Blocks:` lines.
- The WF-002.7 marker gate, the hold status, and the status JSON against its schema.

`unittest` under `tests/specflow/contract/`, one file per module, with tests named for the rule they enforce. Each test file puts the package's `scripts/` folder on `sys.path`. Fixture specs are small folders under `tests/specflow/fixtures/`; a test that changes a fixture copies it to a temporary folder first.

- T-027 is a recorded capture: Kiro IDE generates the three specs, and `kiro-captures.md` records the exact file set, headings, ID numbering, and task syntax, the variants against the public references, whether a specflow-written bugfix spec opens as a Bug Fix spec, and whether Kiro lists, opens, and watches specs through a `.kiro/specs` link. The Data model sections on Kiro-native shapes, the bugfix shape, and the specs folder are corrected to match before T-020 starts.
- T-020, `test_templates.py`: every template has the headings of its Data model section; the bugfix templates match the capture's headings; the optional `Depends on:` line sits where the grammar puts it in both orders; no template holds a banned placeholder. The source task also says the fixtures "validate": that half runs in T-026, whose tests pass the same fixtures through `validate`.
- T-021, `test_state_schema.py`: valid fixtures pass; a wrong type, a missing required field, an unknown status, and an unsupported `schemaVersion` each fail with the path of the value; an unknown extra field passes; a seeded secret, transcript, absolute path, or session identifier is caught by `check_content`, and a marker line or a reason that starts with `/` passes.
- T-022, `test_canonical.py` and `test_approval.py`: the cases of the hash-exclusion row above, one test each; approval is never inferred from a file's existence. `test_drift.py`: capture of staged, unstaged, and untracked bytes; a missing file; a refused path; no partial baseline.
- T-023, `test_invalidation.py`: one table, every change against every downstream result, in both orders.
- T-024, `test_reconcile.py`: missing state, missing artifacts, malformed state kept byte for byte, unknown version, and each Kiro capture, none overwriting valid content.
- T-025, `test_concurrency.py`: a file changed between read and write raises `ConflictError` and keeps the intervening edit.
- T-026, `test_cli.py`: each exit code; `test_checks.py`: one seeded defect per row of the check table, each found under its check name; `test_status.py`: the status document passes `check_schema` against the status schema and offers no approval path; `test_deps.py` and `test_drift.py`: every case of the two long rows above, where the cases "native placement" and "missing placement" reach the helper as a list of paths or as a stored `not_checked` value, since the helper reads no placement section; in `test_verify_release.py` of 00002: `test_rejects_workflow_version_differing_from_the_manifest` and `test_rejects_schema_id_differing_from_its_address`.
- T-028, `test_config.py`: no config, a configured root, a configured `specsDir`, each refused path, a `.kiro/specs` path that resolves outside the repository, specs left beside a configured folder, an ignored specs folder, and this repository's own config file.
- T-029, `test_numbers.py`: the number scan, each clash kind, a Kiro-native spec, a missing `Sources:` line, and the dependency references, one test each. Creating an item, moving it, and taking a file input are steps the agent performs from `artifact-contract.md`; the two fixtures of the source task about them (the group kept on the move, a file name that matches two files) are sessions of 00006, not tests here. The number scan reads names only: folders one or two levels under `intake/new` and `intake/processed`, the folders directly under the specs folder, and, in a `numberScan` folder, files and folders at any depth. That is what "recursive" means for the intake tree in the Workspace root section: an intake item lies at most two levels down.

## Rollout and migration

Order inside the spec: T-027 first, then the templates, the schema, hashing, invalidation, reconciliation, the command line, config, numbers. The contract-test step joins CI with T-020, whose template tests are the first contract tests. T-027 depends on nothing, so the captures are best made before this design is approved; a correction of the Data model after approval stales this design and its task plan, and the developer re-approves both before T-020 starts.

State schema version 1 is unreleased, but two state files of that version already exist: they were written by hand in `buvis/calcard-mcp` (specs 00031 and 00032) during the conversion trial, with fractional seconds in `approvedAt`. The schema accepts that form, and one of the two files is a fixture of T-021, so the helper reads them as they are. Nothing else migrates. The hand-written `.agents/specflow.json` of this repository and the hand-written approval receipts of specs 00001 to 00009 predate the helper: once it exists, recovery mode (the reconciliation algorithm) reads the artifacts, and each approval is confirmed by the developer before it is recorded.

## Risks and edge cases

- Kiro IDE does not list specs through a `.kiro/specs` link: impact m, likelihood m; mitigation: T-027 checks it before the templates are written; fallback: a configured specs folder is documented as invisible to Kiro's spec panel, while the skill keeps working there.
- Kiro changes its undocumented `.config.kiro`: impact m, likelihood m; mitigation: the spec type also comes from `.specflow.json` and from the files present, and a disagreement is reported, never rewritten; fallback: recapture and change the one place that writes the file.
- Two hosts compute different hashes for the same text: impact h, likelihood l; mitigation: one implementation of `canonical`, in the helper, and no shell fallback; fallback: a host without Python 3 runs read-only.
- A later schema needs a JSON Schema keyword `check_schema` lacks: impact l, likelihood m; mitigation: an unknown keyword is an error, so the gap shows in the first test; fallback: add the keyword.
- Likely next change, state schema version 2: the helper stops on an unknown version; impact m, likelihood m; mitigation: the version is one constant and every schema change is migration-tested; fallback: offer the supported migration path and mutate nothing.
- Likely next change, two writers on one spec: there is no lock by contract; impact m, likelihood l; mitigation: `write_guarded` catches an edit between read and write; fallback: a state server, rejected for the first release below.
- Likely next change, a fourth artifact or phase: the phase table and the invalidation graph name three artifacts; impact m, likelihood l; mitigation: both are data in `state.py`, not spread through the code; fallback: design and task sections, as the source does for deployment.
- Edge cases the canonical text settles: CRLF and CR line endings, a byte-order mark, trailing whitespace, the final newline, a `[x]` inside a fence, and an `Outcome:` line outside a task item.

## Requirement traceability

| Design element | Criteria |
|---|---|
| Directory; files specflow does not own | ART-001.1, ART-001.2, ART-001.3, ART-001.4, ART-001.5, ART-001.9 |
| Kiro-native compatibility; spec type from `.config.kiro`; `spec_type` and the `spec-type` check | ART-001.7 |
| The specs folder, read directly, with no link | ART-001.8, INT-001.7 |
| Placeholder rule and `Not applicable: <reason>` (Requirements, Design, and Tasks structure) | ART-001.10 |
| Header lines and spec dependencies; `deps.py` | ART-002.11, WF-001.9 |
| Workspace config; `config.py` | INT-001.1, SEC-002.5 |
| Intake layout, moving an item, `Sources:` | INT-001.2, INT-001.3, INT-001.6 |
| Spec numbers; `numbers.py` | INT-001.4 |
| Q&A log format and the fallback log | INT-001.5 |
| Input files | INT-001.8 |
| Approval representation; `canonical.py`; the `progress-fields` check | WF-002.3, WF-002.4, VAL-002.5 |
| Invalidation graph; `state.py` | WF-002.5, WF-002.6, WF-005.1, WF-005.2, WF-005.4 |
| `acceptedMarkers` on an approval | WF-002.7 |
| Reconciliation algorithm; `reconcile.py` | WF-004.2, WF-004.3, WF-004.4, WF-004.5, WF-005.3, WF-005.5, STATE-002.4, STATE-002.5 |
| Code drift; `drift.py` | WF-004.8 |
| `write_guarded` and `hash --raw`; the one-writer contract | WF-006.1, WF-006.2, WF-006.3, WF-006.4 |
| State model and its schema | STATE-001.1, STATE-001.2, STATE-001.3, STATE-001.4, STATE-001.5, STATE-001.6, STATE-001.7 |
| State precedence | STATE-002.1, STATE-002.2, STATE-002.3 |
| Status output; `status.py` | STATE-003.1, STATE-003.2, STATE-003.3, STATE-003.4 |
| `checks.py` and `validate` | VAL-001.1, VAL-001.2, VAL-001.3, VAL-001.4, VAL-001.5, VAL-001.6, VAL-001.7, VAL-001.8, VAL-001.13 |
| Markdown and JSON only; no network, database, or running process | Portability |
| Python 3 for approvals, read-only without it (Optional validator) | Portability |
| Phase derivation from file facts | Determinism |
| What a resume may read (Reconciliation algorithm, Spec dependencies, Code drift) | Performance |
| `schemaVersion` and the unknown-version rule | Maintainability |
| Plain Markdown artifacts; the sidecar beside them | Compatibility |

## Alternatives considered

1. **One file, hand-written checks** (smallest diff: `validate_spec.py` holds everything, and the schema files are documentation). Rejected. Ten tasks would edit one file, so no task could own a bounded file slice, and the state would be described twice, in a schema and in code, with nothing to keep them equal.
2. **A thin command line over a package, with the shipped schemas driving the check** (chosen). The added files buy one module per task and one description of each shape.
3. **A JSON Schema library.** Rejected. A host is not sure to have it, and the helper uses the standard library only; the schemas need twelve keywords, which is a short function.
4. Hashing, JSON, argument parsing, and paths come from the standard library (`hashlib`, `json`, `argparse`, `pathlib`); nothing is written anew for them. No registry search was run: the package may not carry a dependency.

### Make AWS AI-DLC's record tree canonical (`aidlc/` or `.aidlc/`)

Rejected. The primary interoperability goal is compatibility with Kiro's `.kiro/specs` structure.

### Adopt A1's Guard Policy `relaxed` or `off`

Rejected (aidlc decision #5). A1 records changed inputs and keeps going under `relaxed` and `off`, and its downstream staleness is advisory. specflow keeps strict invalidation (WF-002.5-6): any change to an approved artifact stales it and everything downstream, because the gate is the only thing standing between an agent and unapproved scope.

### Own the `.kiro/specs` link in the plugin

Rejected (decision 2026-10-03 #6, superseding the `relink` half of `qa-log.md` Q3). A `relink` helper needed a junction made through `cmd.exe`, a path whitelist to make that safe, `.gitignore` edits, five refusal cases, and a Windows CI job, all resting on the unverified premise that Kiro follows the link. specflow reads the configured specs folder directly, and a repository that keeps specs outside `.kiro/` makes the link in its own onboarding (§6.7). Tracking the link in git stays rejected too: it checks out on Windows as a text file, and a junction in its place makes git see every spec twice.

### Require an MCP state server

Rejected for the first release. It adds runtime installation, process, and transport differences while the required state is small and repository-local. MCP remains a future option if deterministic multi-user locking or richer tooling becomes necessary.

### Store approvals in Markdown frontmatter

Rejected. It risks altering Kiro-native document expectations and creates noisy edits. A separate hidden JSON sidecar is easier to validate and recover.

## Reuse inventory

- `scripts/validate.py` is the only code in the repository, read in full. The shipped helper cannot import it, so three of its patterns are reused by copying the idea, not the module: `contained_suffix(value: str) -> bool`, the walk that refuses a `..` escape, as the start of the configured-path check, which is new code because that function accepts an absolute path; `load_object(path: Path) -> dict[str, object]` (JSON object or a named error) for the state and config files; and its way of collecting every error before exit.
- `scripts/test_validate.py`: the assertion pattern for the contract tests.
- The Kiro captures of T-027 are reused as fixtures by T-020, T-024, T-026, and later by 00009.
- This repository's `.agents/specflow.json` is a config fixture.
- Searches, case-insensitive, over `scripts`, `.github`, `plugins`, and `templates`: `hash|sha256|canonical`, `schema`, `approv|stale|reconcil`, `intake|spec number|next.number`. They are recorded with their hits in the intake log; none finds a helper for hashing, state, reconciliation, or numbering.

## Open decisions

No decision is open. Rulings of 2026-10-04 (design gates report), taken in above: D1, T-002 of 00002 creates a shell `SKILL.md`, so the folder is valid when T-020 writes into it; D2, T-020 creates `references/artifact-contract.md` and T-029 adds the intake procedure; D13, each schema carries its public address as `$id` from the task that writes it.

Choices the source left to the design, made above and listed for approval: the three added operations (`hash --raw`, `hash --json`, `validate` on an intake item) and the version constant; the table of checks, with a registry that carries phases and a context, and the scope of `design-sections`; the status fields beyond the example, with `problems` and `intake`; the `state-content` check; the pinned details of the canonical text; fractional seconds in `approvedAt`; the cross-spec reference form; the helper is a thin command line over the package `specflow_helper`; the shipped schemas drive validation through `check_schema`; `reconcile` writes derived facts only and never an approval; contract tests live in `tests/specflow/contract/` and join CI with T-020; the Kiro capture record lives in this spec's intake item.

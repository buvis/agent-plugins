# Design: specflow package boundary

## Overview

The plugin lives in the buvis agent-plugins monorepo, which has a hard physical boundary:

- `plugins/specflow/` is the complete distributable package.
- Everything outside `plugins/specflow/` is maintainer-only repository infrastructure.

This layout is the primary safeguard preventing the internal catch-up skill from being shipped.

This spec builds that boundary and nothing behind it: the package folder with its two manifests, a release check that fails when maintainer material shows up inside the package, the CI steps that run it, and a throwaway probe that shows each supported host can load a package of this shape.

## Context and constraints

- The repository already validates every folder under `plugins/` and the template with `scripts/validate.py`: manifest shape, names, path containment, skill frontmatter, and MCP configuration. CI (`.github/workflows/validate.yml`) runs its tests and the validator on Python 3.10 for pushes to `master` and for pull requests. A folder under `plugins/` without a `plugin.json` fails that validator, so the package folder must first appear together with its manifest.
- `AGENTS.md` (repository root, whole repository): every `plugins/<name>` package stays independently distributable; the directory name equals the manifest `name`; resolved symlinks stay inside the plugin root; tooling is dependency-free Python; client behavior lives in a client-documented compatibility package, never in the closed portable manifest; portable manifests are the source of truth for metadata.
- `README.md` and `CONTRIBUTING.md` (repository root): the plugin table changes when a plugin is published, and each plugin carries a `README.md` and a `CHANGELOG.md`.
- Design principles 2 (portable core, thin adapters) and 8 (allowlist releases) of 00001 bind this spec.
- The skill itself does not exist yet. `scripts/validate.py` rejects a skill folder that has no `SKILL.md`, and 00003, 00004, and 00005 write into `skills/spec-workflow/` before 00006 writes the skill. By the developer's ruling of 2026-10-04 (D1), T-002 therefore creates a shell `SKILL.md`, described under Components and interfaces.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

## Architecture

```text
agent-plugins/
├── plugins/
│   └── specflow/                     # The only distributable subtree
│       ├── plugin.json               # Agent Plugins v1 manifest
│       ├── .claude-plugin/
│       │   └── plugin.json           # Claude Code compatibility only
│       ├── skills/spec-workflow/
│       │   └── SKILL.md              # A shell until 00006 writes the skill
│       ├── CHANGELOG.md
│       └── README.md
├── tools/
│   └── specflow/
│       └── verify_release.py         # Release-boundary and forbidden-marker checks
├── tests/
│   └── specflow/
│       └── release/                  # Tests of the boundary and of verify_release.py
└── docs/dev/tmp/specflow/probe/      # Ignored; the throwaway probe package and its workspace
```

The monorepo root is not an installable plugin root. Installation surfaces that accept a local folder or repository subdirectory use `plugins/specflow/`. A generated distribution branch for hosts that require `plugin.json` at a repository root is deferred until such a host is supported (§17).

`verify_release.py` is specflow's own maintainer tool. It imports the generic checks from `scripts/validate.py` and adds the specflow-only ones: the package tree is clean, the compatibility manifest repeats the root manifest and adds nothing, and no maintainer path or name appears inside the package. It runs inside a clean checkout: CI provides one on every push and pull request, and the release step of 00001 (T-063) runs it in one for the candidate commit.

## Module placement

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `README.md` | edit | T-001 | repository layout gains `tools/`, `tests/`, and `.agents/skills/`, and the rule that `plugins/specflow/` is specflow's only distributable root |
| `AGENTS.md` | edit | T-001 | structure list names the six boundaries of T-001: `plugins/specflow/`, `.agents/skills/`, `tools/specflow/`, `tools/specflow/upstream/`, `tests/specflow/`, `docs/dev/tmp/specflow/` |
| `tests/specflow/release/test_boundary.py` | new | T-001 | the tree assertion test |
| `plugins/specflow/plugin.json` | new | T-002 | root manifest |
| `plugins/specflow/README.md` | new | T-002 | what the plugin is, that it is unreleased, and that this folder is the whole distributable package |
| `plugins/specflow/CHANGELOG.md` | new | T-002 | `## [Unreleased]`, in the template's format |
| `plugins/specflow/skills/spec-workflow/SKILL.md` | new | T-002 | the shell: valid frontmatter and one sentence saying the workflow is not written yet |
| `plugins/specflow/.claude-plugin/plugin.json` | new | T-003 | Claude Code compatibility manifest |
| `tools/specflow/verify_release.py` | new | T-004 | clean-tree and manifest checks |
| `tests/specflow/release/test_verify_release.py` | new | T-004 | its tests |
| `tools/specflow/verify_release.py` | edit | T-005 | forbidden-content checks |
| `tests/specflow/release/test_verify_release.py` | edit | T-005 | one seeded fixture per forbidden item |
| `.github/workflows/validate.yml` | edit | T-005 | a job-level setting and two steps |
| `docs/dev/tmp/specflow/probe/specflow-probe/` | new, ignored | T-006 | the probe package |
| `docs/dev/tmp/specflow/probe/workspace/` | new, ignored | T-006 | the scratch workspace the probe skill writes into |
| `docs/dev/project-management/intake/processed/specflow/00002-package-boundary/host-loading-probe.md` | new | T-006 | the probe record |
| `docs/dev/project-management/specs/00008-host-integration/design.md` | edit | T-006 | the host lines the probe corrected |

Git tracks no empty folder, so the folders T-001 names appear with the first file a later task puts there; T-001 owns the documented rule and its test. The package folder first appears in T-002, together with its manifest, because the repository validator fails a folder under `plugins/` that has none. The root README plugin table stays as it is until release (00001, T-065).

## Components and interfaces

### Root manifest

`plugins/specflow/plugin.json` is the portable entry point:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "specflow",
  "version": "0.1.0",
  "description": "Portable requirements, design, tasks, and implementation workflow using Kiro-compatible artifacts.",
  "author": {
    "name": "buvis",
    "url": "https://github.com/buvis"
  },
  "repository": "https://github.com/buvis/agent-plugins",
  "license": "MIT",
  "keywords": [
    "spec-driven-development",
    "requirements",
    "design",
    "tasks",
    "kiro"
  ]
}
```

Agent Plugins clients discover both distributed skills — the workflow skill `spec-workflow` and the conversion skill `convert-prd` (§6.9) — from the root `skills/` directory. The initial package does not contain `mcp.json` because a service dependency would reduce portability without being necessary for file-based handoff.

Checked on 2026-10-04: this manifest passes `python3 scripts/validate.py <dir>`, with or without a `.claude-plugin/` folder beside it.

### Claude compatibility manifest

`plugins/specflow/.claude-plugin/plugin.json` provides Claude Code metadata and points at the same root `skills/` directory. It contains no copied prompt text, workflow stages, or artifact rules.

The file carries the root manifest's metadata fields and nothing else:

```json
{
  "name": "specflow",
  "version": "0.1.0",
  "description": "Portable requirements, design, tasks, and implementation workflow using Kiro-compatible artifacts.",
  "author": {
    "name": "buvis",
    "url": "https://github.com/buvis"
  },
  "repository": "https://github.com/buvis/agent-plugins",
  "license": "MIT",
  "keywords": [
    "spec-driven-development",
    "requirements",
    "design",
    "tasks",
    "kiro"
  ]
}
```

It names no component path: Claude Code finds the shared root `skills/` folder by its default. The developer accepted this on 2026-10-04 (ruling D4), and the task plan words T-003 to match. Checked on 2026-10-04: this manifest passes `claude plugin validate --strict <dir>`.

### Shell skill of T-002

By ruling D1, T-002 writes `plugins/specflow/skills/spec-workflow/SKILL.md` as a shell, so the skill folder is valid while 00003, 00004, and 00005 fill it:

```markdown
---
name: spec-workflow
description: specflow's spec workflow. Not usable yet; a later change writes it.
---

This skill is a shell: the specflow workflow is not written yet.
```

The shell says what it is and nothing else. Checked on 2026-10-04 on a scratch package: with this file in place, `python3 scripts/validate.py <dir>` and `claude plugin validate --strict <dir>` both pass.

T-030 (00006) replaces the shell with the skill and, in the same change, adds the string `the specflow workflow is not written yet` to `FORBIDDEN_MARKERS`, with a test. The marker cannot join that list earlier: CI runs the release check on every push, and it would fail for as long as the shell exists. A release needs 00006 by the dependency order, so the release check that runs for a release always holds the marker, and a shell cannot ship.

### `tools/specflow/verify_release.py`

```text
python3 tools/specflow/verify_release.py
```

Takes no argument and checks the checkout it sits in. It is a release check, so it expects a clean checkout: a working tree in which package code was imported fails on its `__pycache__` folders, as intended. It prints one line per failure as `error: <path>: <message>` to standard error, with `<path>` relative to the repository root, collects every failure before it exits, and prints `Verified plugins/specflow.` on success. Exit codes: 0 pass; 1 one or more failures; 2 `git` is missing, the folder is not a git checkout, or a git call exits nonzero.

```python
ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "specflow"

COMPAT_FIELDS = {"name", "version", "description", "author", "homepage",
                 "repository", "license", "keywords"}
COMPAT_REQUIRED = ("name", "version")

FORBIDDEN_PATH_PARTS = (".agents", ".git", "tests", "evals", "parity", "upstream")
FORBIDDEN_FILE_NAMES = ("sources.md", "inventory.json", "criteria.json",
                        "check_rules.py", "verify_release.py")
FORBIDDEN_NAME_PATTERNS = ("test_*.py", "*_test.py", "*-specflow-upstream-catchup.md")
FORBIDDEN_MARKERS = ("catchup-specflow-upstream", "check_rules.py",
                     "verify_release.py", "tools/specflow", "tests/specflow",
                     "docs/dev/tmp/specflow")

def check_clean(plugin: Path) -> list[str]: ...
def check_manifests(plugin: Path) -> list[str]: ...
def check_forbidden(plugin: Path) -> list[str]: ...
def main() -> int: ...
```

- `check_clean` (T-004) makes three git calls, each as `git -C <plugin> ...`, so the user's git settings and the caller's working directory do not change the result:
  - `status --porcelain --ignored --untracked-files=all -- .`: one error per line. A modified, untracked, or ignored file under the package is an unexpected generated file.
  - `ls-files -ci --exclude-per-directory=.gitignore -- .`: one error per line. A tracked file that a repository ignore rule matches is a committed generated file. Only the repository's own `.gitignore` files count here; a developer's global or local exclude file must not turn a clean package into a failure.
  - `ls-files -s -- .`: one error per entry with mode `160000`. That is an embedded repository, such as an upstream clone.
- `check_manifests` (T-004) calls `validate_manifest`, `validate_containment`, `validate_skills`, and `validate_mcp` from `scripts/validate.py` and turns a `ValidationError` into an error line. It then loads `.claude-plugin/plugin.json` and reports: a missing file, a value that is not a JSON object, a missing key of `COMPAT_REQUIRED`, a key outside `COMPAT_FIELDS`, and a key whose value differs from the root manifest's value for that key.
- `check_forbidden` (T-005) walks the package without following symlinks, and reports a folder it cannot read. For every path it tests each part, folder names included: a part in `FORBIDDEN_PATH_PARTS`, a part that contains a marker. A marker with a slash, such as `tools/specflow`, spans folders, so it is tested against the path inside the package instead: a path that ends in it fails. For every file it also tests the name against `FORBIDDEN_FILE_NAMES` and, with `fnmatch`, against `FORBIDDEN_NAME_PATTERNS`, and the bytes for each marker. An error names the path and the rule or marker that matched.
- The tool reaches `scripts/validate.py` by putting `ROOT / "scripts"` on `sys.path`; the tests reach the tool the same way with `ROOT / "tools" / "specflow"`. Both are standard library only.

### CI steps

In the `plugins` job of `.github/workflows/validate.yml`, one job-level setting keeps Python from writing `__pycache__` into the checkout, so a later step that runs package code cannot make the release check fail:

```yaml
    env:
      PYTHONDONTWRITEBYTECODE: "1"
```

and two steps follow the two existing ones:

```yaml
      - name: Test specflow release checks
        run: python3 -m unittest discover -s tests/specflow/release

      - name: Verify specflow release boundary
        run: python3 tools/specflow/verify_release.py
```

### Host loading probe

A throwaway package `docs/dev/tmp/specflow/probe/specflow-probe/`: the two manifests with the name `specflow-probe`, one skill `skills/probe-fixture/SKILL.md`, one reference `skills/probe-fixture/references/note.md`, and one script `skills/probe-fixture/scripts/probe.py` (ruling D3 of 2026-10-04: recording an approval needs the helper of 00004 on every host). The script uses the standard library only and prints one line, the Python version and its own resolved path. The skill tells the agent to read the reference, run `python3 scripts/probe.py` by its path relative to the skill folder, and write `.kiro/specs/00000-probe/requirements.md` with one line that quotes the reference, gives the script's output, and names the host, or, when that file exists, to add one line to it. The agent runs it with `docs/dev/tmp/specflow/probe/workspace/` as its workspace, so the fixture lands in ignored scratch. Nothing from the probe is committed to `plugins/specflow/`.

The record `host-loading-probe.md` is tracked and holds, per supported host: the install surface used (local folder, or what the host offered) and the path that worked; whether the host required `plugin.json` at a repository root; whether it loaded the skill, read the reference, ran the bundled script (with its output, or why it could not run), wrote the fixture, and resumed a fixture another host wrote; the name under which the skill appeared (in Claude Code, `specflow-probe:probe-fixture`); and any limit found. It also holds the contents of the five probe files, so the probe can be rebuilt after the scratch folder is purged.

The probe package is never on a remote, so it tries local-folder installs only. Installs from a repository URL are outside the probe; T-045 in 00008 resolves those lines.

## Data model

Not applicable: this spec stores no data. The two manifests are static JSON, given in full under Components and interfaces.

## Data and control flow

Release check, in order: `check_clean`, `check_manifests`, `check_forbidden`. Every check runs even when an earlier one fails, so one run shows every problem.

Probe (T-006), per host: install the probe package from its local folder, run the skill in the scratch workspace, confirm the fixture file, then open the workspace in another host and run the skill again. The install lines to follow are the host lines of the source design §12, which the design of 00008 carries. T-006 writes what it found into the record and corrects those lines in the 00008 design; that edit stales the 00008 design by the normal rule. If that design is not approved yet, the record is what its author drafts the host lines from. A host that fails the probe, or that loads the skill but cannot run the bundled script (it could draft, and could not record an approval, 00004), is fixed or leaves the supported list before any task of 00004 starts.

## Error handling

- A failed check never stops the others; the tool exits 1 after printing all errors.
- `git` missing, the folder not a checkout, or a git call that exits nonzero: one message naming the cause, exit 2. The tool does not fall back to an unchecked pass.
- A file that cannot be read during the marker scan is an error for that path, not a skip.
- The probe has no error path of its own: a failing step is recorded with the step that failed (PKG-003 criterion 7).

## Security and privacy

### No bundled maintainer material

The distributed package contains the AWS references and the adaptation record because runtime agents consult them. It does not contain:

- `.agents/skills/catchup-specflow-upstream/`
- the source cursors (`tools/specflow/upstream/sources.md`) or catch-up reports
- the behavior rule inventory, `check_rules.py`, scenario evals, and parity reports
- release scripts
- upstream Git metadata or clones
- maintainer credentials or configuration

### Release

- The release is `plugins/specflow/` at a tag; nothing outside it is installable.
- No symlink escapes.
- Forbidden internal markers scanned in the tagged tree, including the rule inventory, evals, and parity reports.
- Manifest validation and the source-record check are mandatory.

- The source-record check named in the last line joins the same tool in 00003 (REL-001 criterion 3).
- `validate_containment` rejects a symlink that resolves outside the package, and the marker scan follows no symlink.
- The tool reads repository files and runs read-only git commands; it writes nothing and uses no network.
- The probe package holds no credential, and nothing from it is committed to the package.

## Testing strategy

- Validate Agent Plugins v1 root manifest.
- Validate Claude compatibility manifest.
- List `plugins/specflow/` contents and reject repository-only paths.
- Search `plugins/specflow/` for the catch-up skill's name and internal script names.

`unittest`, with tests named for the rule they enforce. Fixtures are built inside each test from literals by one helper, `make_package(root: Path) -> Path`, which writes the two manifests under `root/plugins/specflow/`; no test reads the real package, so T-004 needs only T-001. Tests that need git run `git init` in a temporary folder and commit the fixture; every git call in the tests sets `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1` and passes `-c user.name=test -c user.email=test@example.invalid -c commit.gpgsign=false`, so the developer's or the runner's git settings cannot change the result.

- `test_boundary.py`, T-001: `test_no_specflow_manifest_outside_the_package`. It lists tracked files with `git ls-files`, loads every one named `plugin.json`, and fails when one outside `plugins/specflow/` has the name `specflow`. It passes while no manifest exists. It differs from `check_forbidden`, which looks inside the package.
- `test_verify_release.py`, T-004, clean tree: `test_clean_fixture_passes`, `test_rejects_modified_tracked_file`, `test_rejects_untracked_file_in_plugin`, `test_rejects_untracked_file_when_git_hides_untracked_files`, `test_rejects_ignored_generated_file_in_plugin`, `test_rejects_committed_file_matching_an_ignore_rule`, `test_rejects_embedded_repository`, `test_exits_2_outside_a_git_checkout`.
- `test_verify_release.py`, T-004, manifests: `test_rejects_symlink_escaping_plugin_root`, `test_rejects_missing_compat_manifest`, `test_rejects_compat_manifest_that_is_not_an_object`, `test_rejects_compat_manifest_with_component_path`, `test_rejects_compat_value_differing_from_root` (a `subTest` per field), `test_rejects_compat_manifest_missing_a_required_field`, `test_rejects_empty_compat_manifest`, `test_reports_failures_from_every_check`, `test_main_prints_repository_relative_paths`.
- `test_verify_release.py`, T-005: the test file holds its own copy of the required entries of each denylist, taken from PKG-002.4 and T-005 and never read from the tool, so dropping an entry from the tool fails a test. `test_denylists_hold_every_required_entry` checks that each tool constant contains every copied entry; `test_rejects_each_forbidden_path_part`, `test_rejects_each_forbidden_file_name`, `test_rejects_each_forbidden_name_pattern`, `test_rejects_marker_in_a_folder_name`, `test_rejects_each_marker_in_file_content` are each a loop of `subTest` over the copied list they cover; `test_reports_unreadable_file`; `test_reports_unreadable_folder`; `test_error_names_path_and_marker`.
- T-002 and T-003: `python3 scripts/validate.py` passes with the package present, and `claude plugin validate --strict plugins/specflow` passes, with the shell skill in place. The real skill does not exist in this spec, so the skill's name under Claude Code is checked on the probe (T-006) and again on the real package in 00008 (T-043).
- T-006 is a recorded manual run per host; its evidence is `host-loading-probe.md`.

## Rollout and migration

The CI setting and steps land with T-005, in the same change as the checks they run, so the boundary is enforced from T-005 on. The package that T-002 adds is unguarded until then, unless the spec lands as one pull request. Nothing is published by this spec: the README plugin table and the marketplace entry belong to 00001 and 00008. No data or user migrates.

## Risks and edge cases

- A supported host fails the loading probe: impact h, likelihood m; mitigation: the probe (T-006) finishes before phase 3 work starts; fallback: the host is fixed or leaves the supported list first.
- The marker scan flags text the package needs: impact l, likelihood m; mitigation: every marker is the full name of a maintainer file or path or, from T-030 on, the shell's own sentence; none is a common word or a public convention; fallback: reword the package text, since the lists change only by a reviewed edit.
- Claude Code changes the manifest fields it accepts: impact m, likelihood l; mitigation: the compatibility manifest holds metadata and no behavior; fallback: change that one file, with T-043 as the recheck.
- Likely next change, a second plugin with maintainer tooling: the lists and the package path are fixed in `tools/specflow/verify_release.py`; impact l, likelihood m; mitigation: the three checks take the package path as an argument; fallback: copy the tool to `tools/<plugin>/` and generalize when two exist.
- Likely next change, a supported host needs `plugin.json` at a repository root (PKG-002 criterion 6 wakes): nothing builds a distribution branch; impact m, likelihood l; mitigation: the probe record and T-045 both note the install surface, and the checks work on any folder, so a generated tree can be verified unchanged; fallback: the host stays unsupported until the branch exists.
- Likely next change, the package gains `mcp.json` (PKG-001 criterion 4): no limit; `scripts/validate.py` validates it today.
- Edge case: a symlink inside the package that points inside the package is allowed; one that points outside fails.
- Edge case: git never tracks a path named `.git`, so that path part can only match in a working tree that holds an untracked clone; in a clean checkout the embedded-repository check does that work.

## Requirement traceability

| Criterion | Design element |
|---|---|
| PKG-001.1 | Root manifest; `check_manifests` |
| PKG-001.3 | No `mcp.json` in the package (Root manifest) |
| PKG-001.4 | Permission only; `scripts/validate.py` already validates an added `mcp.json` |
| PKG-001.5 | Compatibility manifest holds metadata only; `COMPAT_FIELDS` |
| PKG-002.1 | Architecture; `test_boundary.py` |
| PKG-002.2 | `verify_release.py` runs on a clean checkout of the candidate commit |
| PKG-002.3 | Module placement keeps maintainer paths outside the package; the documented boundaries of T-001 |
| PKG-002.4 | `check_forbidden` and its constants; `check_clean` for embedded repositories. Maintainer prompts and repository-only host launchers have no name to scan for yet: placement keeps them out, and the `tests` and `evals` path parts catch the eval runners of 00009 |
| PKG-002.5 | CI steps |
| PKG-002.6 | Dormant by the assumption in the requirements; the probe record notes the install surface; see Alternatives considered |
| PKG-003.1, PKG-003.2 | Root manifest with keywords; Host loading probe |
| PKG-003.3 | Claude Code compatibility manifest |
| PKG-003.5 | `COMPAT_FIELDS` leaves no room for instructions |
| PKG-003.6 | `COMPAT_FIELDS` has no component-path key, so the adapter cannot move an artifact or a skill |
| PKG-003.7 | Host loading probe and its record |
| REL-001.1 | `check_clean` and `check_forbidden` on `plugins/specflow/` |
| REL-001.2 | `check_manifests` |
| Portability, thin adapters | Claude Code compatibility manifest |

## Alternatives considered

1. **Add a release mode to `scripts/validate.py`** (smallest diff: one file edited, no new tool). Rejected. That validator is plugin-agnostic and runs on every package and on the template; specflow's forbidden names would sit in the generic tool, and other plugins would run checks that mean nothing to them.
2. **A specflow tool run inside a clean checkout** (chosen). The added file buys a place for specflow-only rules beside specflow's other maintainer tools, while the generic checks are reused by import.
3. **A tool that makes its own clean checkout** from a commit (worktree or archive). Rejected. It adds git plumbing and cleanup paths; CI already gives a clean checkout, and the release step runs the tool in one.
4. **An existing tool for the content scan** (a pre-commit string hook or a secret scanner). Rejected without a registry search: `AGENTS.md` keeps tooling dependency-free, so a found tool would be rejected on that ground alone, and the scan is a short loop.

### Archive or distribution-branch releases

Deferred. No supported host installs from an archive or needs `plugin.json` at a repository root today; each installs a folder or repository subdirectory. Add an archive or generated branch when a named host requires one.

## Reuse inventory

- `scripts/validate.py`: `validate_manifest(plugin: Path) -> dict[str, object]`, `validate_containment(plugin: Path) -> None`, `validate_skills(plugin: Path) -> int`, `validate_mcp(plugin: Path) -> None`, `load_object(path: Path) -> dict[str, object]`, and `ValidationError`. `check_manifests` calls them, so the manifest shape, the name rule, and the symlink rule are not written twice.
- `scripts/test_validate.py`: the assertion pattern (break one thing, assert the message).
- `templates/example-plugin/`: the shape of `plugin.json` and `CHANGELOG.md`.
- `.github/workflows/validate.yml`: the job the setting and the two steps join.
- Searches: `forbidden|marker|release|verify_release|worktree`, case-insensitive, over `scripts`, `.github`, `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `plugins`, and `templates` found only `[Unreleased]` in two changelog lines, which also shows the pattern matches. No release or forbidden-content check exists to reuse.

## Open decisions

No decision is open. Rulings of 2026-10-04 (design gates report), taken in above: D1, T-002 writes a shell `SKILL.md`, and T-030 (00006) replaces it and forbids its sentence; D3, the probe also runs one bundled script; D4, the compatibility manifest names no `skills` path, and the task plan words T-003 to match.

Four choices the source left to the design are made above and listed for approval: the tool runs in a clean checkout instead of making one; `plugins/specflow/README.md` and `CHANGELOG.md` are created by T-002; the probe record lives in this spec's intake item; and the shell's sentence joins `FORBIDDEN_MARKERS` with T-030, not before, since CI runs the release check on every push.

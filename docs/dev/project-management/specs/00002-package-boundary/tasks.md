# Tasks: specflow package boundary

The first sub-bullets of `Details:` and `Verify:` are carried from the source plan in intake item 00001. In them, `design §n` means the source design, `.kiro/specs` means the specs folder, and a task ID may belong to another spec; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section and each task. Lines written for this plan name a task of another spec with its spec, as in `T-030 (00006)`.

- [x] T-001 Create the repository skeleton
  - Requirements: PKG-002
  - Depends on: none
  - Location: `README.md`, `AGENTS.md`, `tests/specflow/release/test_boundary.py`
  - Contract: Git tracks no empty folder, so the folders T-001 names appear with the first file a later task puts there; T-001 owns the documented rule and its test.
  - Details:
    - Document the `plugins/specflow/`, `.agents/skills/`, `tools/specflow/`, `tools/specflow/upstream/`, `tests/specflow/`, and `docs/dev/tmp/specflow/` ownership boundaries. Create no empty folder, and no `plugins/specflow/` folder: one without a manifest fails the repository validator.
    - Add repository documentation stating that `plugins/specflow/` is specflow's only distributable root.
    - In `README.md`, the repository layout gains `tools/`, `tests/`, and `.agents/skills/`, and the rule that `plugins/specflow/` is specflow's only distributable root. In `AGENTS.md`, the structure list names the six boundaries.
  - Acceptance criteria: PKG-002 criteria 1, 3
  - Verify:
    - a tree assertion test identifies `plugins/specflow/` as specflow's only distributable root.
    - `python3 -m unittest discover -s tests/specflow/release` passes with `test_no_specflow_manifest_outside_the_package`, which passes while no manifest exists.
    - File check: `AGENTS.md` names the six paths, and `README.md` states the rule.
  - Outcome: `python3 -m unittest discover -s tests/specflow/release` ran 1 test, OK; with a tracked `tools/probe-fail/plugin.json` named `specflow` (intent-to-add, then removed) it failed on that path. `python3 scripts/validate.py` passes. `AGENTS.md` lists the six paths; `README.md` layout gains `tools/`, `tests/`, `.agents/skills/` and states the rule.

- [x] T-002 Define the portable root manifest
  - Requirements: PKG-001
  - Depends on: T-001
  - Location: `plugins/specflow/plugin.json`, `plugins/specflow/README.md`, `plugins/specflow/CHANGELOG.md`, `plugins/specflow/skills/spec-workflow/SKILL.md`
  - Contract: The package folder first appears in T-002, together with its manifest, because the repository validator fails a folder under `plugins/` that has none.
  - Details:
    - Add `plugins/specflow/plugin.json` targeting Agent Plugins v1.
    - Use a placeholder-free final plugin identity, version, description, license, repository, and activation keywords.
    - Write the manifest exactly as the design gives it under Root manifest. Add no `mcp.json`; PKG-001 criterion 4 is a permission and needs no check.
    - Write `plugins/specflow/README.md` (what the plugin is, that it is unreleased, that this folder is the whole distributable package) and `plugins/specflow/CHANGELOG.md` with `## [Unreleased]` in the template's format. The plugin table of the root `README.md` stays as it is until the release (T-065 of 00001).
    - Write the shell `plugins/specflow/skills/spec-workflow/SKILL.md` exactly as the design gives it under Shell skill of T-002 (ruling D1): valid frontmatter and the one sentence saying the workflow is not written yet.
  - Acceptance criteria: PKG-001 criteria 1, 3, 4
  - Verify:
    - `python3 scripts/validate.py` passes with the package and the shell skill present; that validator is this repository's Agent Plugins v1 check.
  - Outcome: `python3 scripts/validate.py` printed `Validated 2 plugin package(s) and 2 skill(s).` (template and specflow); `scripts` tests 9 OK; release tests 1 OK. Manifest and shell skill match the design verbatim; no `mcp.json`; root README plugin table unchanged.

- [x] T-003 Add the Claude compatibility manifest
  - Requirements: PKG-001, PKG-003
  - Depends on: T-001, T-002
  - Location: `plugins/specflow/.claude-plugin/plugin.json`
  - Contract: The file carries the root manifest's metadata fields and nothing else:
  - Details:
    - Add `plugins/specflow/.claude-plugin/plugin.json` exactly as the design shows it under Claude compatibility manifest, with no component path: Claude Code finds the shared root `skills/` folder by its default (ruling D4).
    - Keep workflow logic out of the compatibility manifest.
  - Acceptance criteria: PKG-001 criterion 5; PKG-003 criteria 3, 5, 6
  - Verify:
    - `claude plugin validate --strict plugins/specflow` passes, and `python3 scripts/validate.py` still passes. The skill's name under Claude Code is checked on the probe (T-006) and on the real package in T-043 (00008).
    - File check: the keys of the compatibility manifest are keys of the root manifest other than `$schema`, and each value equals the root's.
  - Outcome: `claude plugin validate --strict plugins/specflow` printed `✔ Validation passed`; `python3 scripts/validate.py` printed `Validated 2 plugin package(s) and 2 skill(s).`; a `jq` diff of the two manifests (differing values, extra keys, `$schema` in the compat file) returned `[]`. No component path in the compat manifest.

- [x] T-004 Implement release verification
  - Requirements: PKG-002, PKG-003, REL-001
  - Depends on: T-001
  - Location: `tools/specflow/verify_release.py`, `tests/specflow/release/test_verify_release.py`
  - Reuse: `validate_manifest`, `validate_containment`, `validate_skills`, `validate_mcp`, `load_object`, and `ValidationError` of `scripts/validate.py`, called from `check_manifests`; the assertion pattern of `scripts/test_validate.py`.
  - Contract: Takes no argument and checks the checkout it sits in. It is a release check, so it expects a clean checkout: a working tree in which package code was imported fails on its `__pycache__` folders, as intended.
  - Details:
    - Add `tools/specflow/verify_release.py`, which checks `plugins/specflow/` in a clean checkout of a candidate commit.
    - Reject symlink escapes and unexpected generated files.
    - Build `check_clean` (the three `git -C <plugin>` calls) and `check_manifests` (the compatibility manifest holds only keys of `COMPAT_FIELDS`, each equal to the root value) as the design specifies; print `error: <path>: <message>` per failure, collect every failure, and exit 0, 1, or 2.
  - Acceptance criteria: PKG-002 criterion 2; PKG-003 criteria 5, 6; REL-001 criteria 1, 2
  - Verify:
    - a clean fixture passes; each seeded defect fails with a targeted message.
    - The T-004 tests the design lists in `tests/specflow/release/test_verify_release.py` pass, on fixtures built by `make_package` and never on the real package; every git call in the tests ignores the developer's git settings.
  - Outcome: release tests ran 15, OK, on Python 3.14 and 3.10. Two mutations were each caught: dropping `--untracked-files=all` (1 failure) and inverting the compat comparison (8 failures). On the real package the tool printed `Verified plugins/specflow.`. Deviation: the two `ls-files` calls add `--full-name`, so every `check_clean` error names a repository-relative path; git errors exit 2 through a `GitError`.

- [x] T-005 Add forbidden-content release checks
  - Requirements: PKG-002
  - Depends on: T-002, T-003, T-004
  - Location: `tools/specflow/verify_release.py`, `tests/specflow/release/test_verify_release.py`, `.github/workflows/validate.yml`
  - Contract: `check_forbidden` (T-005) walks the package without following symlinks.
  - Details:
    - Reject `.agents/`, the catch-up skill's name, source cursors, catch-up reports, tests, the rule inventory, `check_rules.py`, evals, parity reports, `docs/dev/tmp/specflow/`, and Git metadata in `plugins/specflow/`.
    - Add `check_forbidden` with the four constants the design gives (`FORBIDDEN_PATH_PARTS`, `FORBIDDEN_FILE_NAMES`, `FORBIDDEN_NAME_PATTERNS`, `FORBIDDEN_MARKERS`), and extend `test_reports_failures_from_every_check` for it. The shell's sentence is not a marker yet; T-030 (00006) adds it.
    - In the `plugins` job of `.github/workflows/validate.yml`, add the job-level `PYTHONDONTWRITEBYTECODE: "1"` and the two steps the design gives: the release tests, then `python3 tools/specflow/verify_release.py`. The second step runs on the real package, which is why this task needs T-002 and T-003.
  - Acceptance criteria: PKG-002 criteria 4, 5
  - Verify:
    - seeded forbidden fixtures each fail with a targeted message.
    - The T-005 tests the design lists pass; for the two new steps, the pull request's CI run is green; before a pull request exists, the step commands pass in a fresh clone of the commit.
  - Outcome: in a fresh clone of the T-005 commit, with `PYTHONDONTWRITEBYTECODE=1` on Python 3.10.22: `scripts` tests ran 9, OK; the validator printed `Validated 2 plugin package(s) and 2 skill(s).`; release tests ran 23, OK; the tool printed `Verified plugins/specflow.`; and `git status --porcelain --ignored` was empty afterwards. Dropping the last marker from the content scan failed `test_rejects_each_marker_in_file_content`. No pull request exists yet, so CI has not run. `check_forbidden` tests each entry's own name, which covers every part of every path once.

- [ ] T-006 Probe host loading
  - Requirements: PKG-003
  - Depends on: T-002, T-003
  - Location: `docs/dev/tmp/specflow/probe/specflow-probe/`, `docs/dev/tmp/specflow/probe/workspace/`, `docs/dev/project-management/intake/processed/specflow/00002-package-boundary/host-loading-probe.md`, `docs/dev/project-management/specs/00008-host-integration/design.md`
  - Premise: For the last step only: the 00008 design still says "to be verified" on its host lines. If those lines were already corrected, the probe still runs and only the correction is skipped.
  - Contract: The record `host-loading-probe.md` is tracked and holds, per supported host: the install surface used (local folder, or what the host offered) and the path that worked; whether the host required `plugin.json` at a repository root; whether it loaded the skill, read the reference, ran the bundled script (with its output, or why it could not run), wrote the fixture, and resumed a fixture another host wrote; the name under which the skill appeared (in Claude Code, `specflow-probe:probe-fixture`); and any limit found.
  - Details:
    - Build a throwaway probe package under `docs/dev/tmp/specflow/probe/`: the two manifests, one skill that reads one bundled reference and writes one fixture artifact, and that reference. Nothing from the probe is committed to `plugins/specflow/`.
    - The probe package also holds one script, `skills/probe-fixture/scripts/probe.py`, which the skill runs by its path relative to the skill folder (ruling D3); it uses the standard library only and prints the Python version and its own resolved path. The agent works in `docs/dev/tmp/specflow/probe/workspace/`.
    - Load it in Kiro IDE, Codex, and Claude Code following each design §12 Install line; in each host run the skill, then resume the fixture another host wrote.
    - This is a recorded manual run per host. The probe tries local-folder installs only; a line that installs from a repository URL stays with T-045 (00008).
    - Record the working install path and any limit per host, and correct design §12 to match.
    - Write the record into this spec's intake item, with the contents of the five probe files. Correcting the host lines edits the 00008 design, which stales it by the normal rule. A host that needs `plugin.json` at a repository root reopens PKG-002 criterion 6: report it to the developer.
  - Acceptance criteria: PKG-003 criteria 1, 2, 3, 7
  - Risk: A supported host fails the probe, or loads the skill but cannot run the bundled script. Mitigation from the design: the probe finishes before any task of 00004 starts, and such a host is fixed or leaves the supported list.
  - Verify:
    - Each supported host loads the skill, reads the reference, runs the script, and writes the fixture, and one other host resumes it; a host that fails is reported with the failing step before any task of 00004 starts.
    - The evidence is `host-loading-probe.md`, with the fields of the contract above for each host.

## Completion criteria

- [ ] Every task above is checked, each with its `Outcome:` line.
- [ ] On the final commit, the pull request's CI run is green; before a pull request exists, the step commands pass in a fresh clone of the commit: the repository validator, the release tests, and `python3 tools/specflow/verify_release.py`.
- [ ] `host-loading-probe.md` shows each supported host loading the probe, running its script, and resuming another host's fixture, or names the host that left the supported list.

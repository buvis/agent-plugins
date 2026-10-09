# Tasks: specflow host integration

The first sub-bullets of `Details:` and `Verify:` are carried from the source plan in intake item 00001. In them, `design §n` means the source design, `.kiro/specs` means the specs folder, and a task ID may belong to another spec; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section and each task. Lines written for this plan name a task of another spec with its spec, as in `T-030 (00006)`.

- [ ] T-040 Test Kiro IDE custom Power loading
  - Requirements: 00002 PKG-003 criterion 1
  - Depends on: none
  - Location: `tests/specflow/compatibility/kiro-ide.md`
  - Reuse: The install surface that `host-loading-probe.md` (00002) names for Kiro IDE.
  - Contract: import as a custom Power from the local folder; the skill activates and reads a reference; create a spec, approve its requirements, close the session, and resume; Kiro's own Spec panel finds the spec
  - Details:
    - Import `plugins/specflow/` from a local folder.
    - Confirm activation, skill reference access, artifact creation, and native Spec discovery.
    - Kiro IDE has no headless mode: this is a recorded manual run by the developer. Work in a throwaway workspace under `docs/dev/tmp/specflow/hosts/`, made with `git init` and one empty commit, with no `.agents/specflow.json`; give the plugin folder by its absolute path.
    - The record states the host version, the install path used, each step with its result, the name under which the skill appeared, and the `status --json` output, the `.specflow.json`, and the spec's artifact files as this host left them.
  - Acceptance criteria: 00002 PKG-003 criterion 1
  - Verify:
    - create, approve requirements, close session, and resume.
    - The record is `tests/specflow/compatibility/kiro-ide.md`, with every step of the design's table passed.

- [ ] T-042 Test Codex Agent Plugins v1 loading
  - Requirements: 00002 PKG-003 criterion 2
  - Depends on: T-040
  - Location: `tests/specflow/compatibility/codex.md`
  - Reuse: The spec T-040 left, in the workspace T-040 made; the install surface the probe record names for Codex.
  - Contract: load the root manifest; the skill is discovered; resume the spec Kiro created, reconcile its hashes (no change is expected), continue in the correct phase, and draft and approve the design and the task plan
  - Details:
    - Load the root manifest and confirm skill discovery.
    - Run by hand once and recorded; the scripted runs belong to 00009. Continue in the workspace the earlier test left, with the plugin folder given by its absolute path. Rebuild the spec from that test's record only if the workspace was purged, and say so in this record.
    - The record states the host version, the install path used, each step with its result, the name under which the skill appeared, and the `status --json` output, the `.specflow.json`, and the spec's artifact files as this host left them.
  - Acceptance criteria: 00002 PKG-003 criterion 2
  - Verify:
    - resume a Kiro-created spec, reconcile hashes, and continue the correct phase.
    - The record is `tests/specflow/compatibility/codex.md`; the design and the task plan end approved, which T-043 needs.

- [ ] T-043 Test Claude Code compatibility loading
  - Requirements: 00002 PKG-003 criterion 3
  - Depends on: T-042
  - Location: `tests/specflow/compatibility/claude-code.md`
  - Reuse: The spec T-042 left, with design and tasks approved.
  - Contract: load the compatibility manifest with `--plugin-dir` and the absolute path of `plugins/specflow`; the skill appears as `specflow:spec-workflow`; edit the requirements and see design and tasks go stale; then Codex resumes the spec and reports the same stale design and tasks, which closes the hand-back
  - Details:
    - Load the compatibility manifest and shared skill.
    - Run by hand once and recorded. Continue in the workspace the earlier test left, with the plugin folder given by its absolute path. Rebuild the spec from that test's record only if the workspace was purged, and say so in this record.
    - The record states the host version, the install path used, each step with its result, the name under which the skill appeared, and the `status --json` output, the `.specflow.json`, and the spec's artifact files as this host left them.
  - Acceptance criteria: 00002 PKG-003 criterion 3
  - Verify:
    - edit requirements, invalidate downstream state, and hand back to another host.
    - The record is `tests/specflow/compatibility/claude-code.md`; the other host of the hand-back is Codex, and its report of the stale design and tasks is in the record.

- [ ] T-046 Add the monorepo Claude Code marketplace entry
  - Requirements: 00002 PKG-003 criterion 3
  - Depends on: T-043
  - Location: `tests/specflow/compatibility/claude-code.md`, `scripts/generate_marketplace.py`, `scripts/test_generate_marketplace.py`, `.claude-plugin/marketplace.json`, `.github/workflows/validate.yml`, `README.md`, `AGENTS.md`, `CONTRIBUTING.md`
  - Reuse: `validate_manifest(plugin: Path) -> dict[str, object]`, `ValidationError`, and `ROOT` of `scripts/validate.py`; `claude plugin validate` for the generated file.
  - Contract: One function, `build_manifest(root: Path) -> str`, returns the exact text of the file, with two-space indent and a final newline; writing and `--check` both call it, so the check compares text, not parsed JSON (bundle A2).
  - Details:
    - Generate the root `.claude-plugin/marketplace.json` from `plugins/*/plugin.json`, with an entry for `plugins/specflow`.
    - Write `scripts/generate_marketplace.py [--check]`: it checks every `plugins/*/plugin.json` with `validate_manifest`, skips a plugin with no `.claude-plugin/plugin.json`, and writes one entry per remaining plugin, sorted by name, with `name`, `source`, `description`, and `version` from the portable manifest. The marketplace is named `buvis-agent-plugins` (ruling D12) and has the shape the design shows.
    - Add the CI step `python3 scripts/generate_marketplace.py --check`, and one line each in `README.md`, `AGENTS.md`, and `CONTRIBUTING.md`: the catalog is generated, never edited by hand, and CI checks it (bundle A3).
    - The install check adds the marketplace from the local checkout and installs specflow through it (bundle A4); its result goes into `tests/specflow/compatibility/claude-code.md`. Afterwards remove the marketplace and the installed plugin from that Claude Code profile again, so a later `--plugin-dir` run sees one copy of the plugin.
  - Acceptance criteria: 00002 PKG-003 criterion 3
  - Risk: That Claude Code adds a marketplace from a local folder is recalled, not yet run. Mitigation from the design: this task confirms it; the public route through GitHub is first run by the install from the tag in T-065 (00001).
  - Verify:
    - `claude plugin` installs specflow from the local checkout through the marketplace.
    - `scripts/test_generate_marketplace.py` passes with the six tests the design names; `claude plugin validate --strict .` passes on the generated file; `specflow:spec-workflow` is listed after the install from the local checkout.

- [ ] T-045 Add host compatibility documentation
  - Requirements: PKG-003
  - Depends on: T-040, T-042, T-043, T-046
  - Location: `plugins/specflow/README.md`, `tests/specflow/compatibility/kiro-ide.md`, `tests/specflow/compatibility/codex.md`, `tests/specflow/compatibility/claude-code.md`, `docs/dev/project-management/specs/00008-host-integration/design.md`
  - Premise: The 00008 design still says "to be verified" on each host line that T-006 (00002) did not resolve.
  - Contract: Before it writes an install line, T-045 tries each open install route once in a fresh host profile and appends the result, and whether the route takes a ref, to that host's record (bundle A1).
  - Details:
    - Document installation, invocation, known UI differences, and handoff examples for each supported host, including the Python 3 prerequisite for approvals, that Kiro IDE lists specs from a configured specs folder only through a `.kiro/specs` link the repository sets up, and the T-027 result on Kiro following that link.
    - State that Kiro CLI and Kiro Crew are expected to work but untested, and do not list them as supported (PKG-003.4).
    - Resolve every "to be verified" Install line in design §12 into a confirmed path or a documented limitation.
    - Clearly state that sessions do not transfer.
    - The host documentation is one section of `plugins/specflow/README.md`, and it names the marketplace of T-046.
    - Resolving a "to be verified" line edits this spec's design. Collect the corrections into one edit, made as the last step of this task.
  - Acceptance criteria: PKG-003 criterion 4
  - Risk: The edit to the approved design stales it and this plan. Mitigation from the design: one batched edit as the last step; the developer then re-approves the design and this plan, and only after that is the spec verified.
  - Verify:
    - Each host's record holds the result of each install route tried in a fresh host profile, and whether the route takes a ref; the install steps of the README work as written there. Two kinds of line cannot run before the release and are left to it: the public route of Claude Code, and any line that T-062 (00001) later pins to the release tag.
    - The host section of `plugins/specflow/README.md` lists exactly Kiro IDE, Codex, and Claude Code as supported, and names Kiro CLI and Kiro Crew as expected to work but untested.
    - No line under `### Kiro IDE`, `### Codex`, or `### Claude Code` of this spec's design still says "to be verified": each is a confirmed path or a stated limit.

## Completion criteria

- [ ] Every task above is checked, each with its `Outcome:` line.
- [ ] Each of the three records under `tests/specflow/compatibility/` holds a passing run on the real package, with the host version, and holds the status document that run ended with.
- [ ] CI is green on the final commit, with `python3 scripts/generate_marketplace.py --check`.
- [ ] No line under `### Kiro IDE`, `### Codex`, or `### Claude Code` of this spec's design still says "to be verified", and the design and this plan are approved again after that edit.

# Design: specflow host integration

## Overview

This spec proves on the real package what the probe of 00002 showed on a throwaway one. Kiro IDE, Codex, and Claude Code each load `plugins/specflow/`, run the workflow, and take over a spec another host wrote. It documents how to install and call the plugin on each host and what is untested, and it adds the Claude Code marketplace entry for the monorepo.

## Context and constraints

- Depends on 00002 (the two manifests, and the probe record `host-loading-probe.md` with the install surface that worked on each host) and on 00006 (the skill the hosts load).
- This spec owns one criterion, PKG-003 criterion 4. Its host tests prove criteria that 00002 owns, PKG-003 criteria 1 to 3, on the real package, and cite them across the dependency.
- Kiro IDE has no headless mode, so its test is a recorded manual run by the developer. Codex and Claude Code can run a prompt without a session, but these three tests are run by hand once and recorded; the scripted runs belong to 00009.
- `README.md` and `AGENTS.md` (repository root): a client catalog is added only after that client is tested, and it is generated from the portable manifests, never maintained by hand.
- The host lines below still say "to be verified" where the source design did. T-006 (00002) and T-045 turn each into a confirmed path or a documented limit.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

## Architecture

```text
agent-plugins/
├── .claude-plugin/
│   └── marketplace.json              # Generated from plugins/*/plugin.json
├── scripts/
│   └── generate_marketplace.py       # The generator, with a check mode for CI
├── plugins/specflow/
│   └── README.md                     # Gains the host section
└── tests/specflow/compatibility/
    ├── kiro-ide.md                   # One record per host test
    ├── codex.md
    └── claude-code.md
```

All three hosts load the same folder. Kiro IDE and Codex read the root manifest; Claude Code reads the compatibility manifest beside it. No host gets its own copy of the workflow, and no host writes an artifact anywhere but the specs folder.

## Module placement

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `tests/specflow/compatibility/kiro-ide.md` | new | T-040 | the recorded Kiro IDE run |
| `tests/specflow/compatibility/codex.md` | new | T-042 | the recorded Codex run |
| `tests/specflow/compatibility/claude-code.md` | new, then edit | T-043, T-046 | the recorded Claude Code run, and the marketplace install check |
| `plugins/specflow/README.md` | edit | T-045 | the host section: install, invocation, known differences, handoff examples, prerequisites, untested hosts |
| `tests/specflow/compatibility/kiro-ide.md`, `codex.md`, `claude-code.md` | edit | T-045 | the result of each install route tried |
| `docs/dev/project-management/specs/00008-host-integration/design.md` | edit | T-045 | each "to be verified" line resolved |
| `scripts/generate_marketplace.py`, `scripts/test_generate_marketplace.py` | new | T-046 | the generator and its tests |
| `.claude-plugin/marketplace.json` | new, generated, committed | T-046 | the marketplace manifest |
| `.github/workflows/validate.yml` | edit | T-046 | one step: `python3 scripts/generate_marketplace.py --check` |
| `README.md`, `AGENTS.md`, `CONTRIBUTING.md` | edit | T-046 | one line each: the catalog is generated, never edited by hand, and CI checks it |

## Components and interfaces

### Host integration

Kiro IDE, Codex, and Claude Code are the supported hosts of the first release (PKG-003.4). Every host needs Python 3 to record approvals (§5.3); each host's documentation states this prerequisite (T-045). A loading probe runs on all three before feature work starts (T-006).

### Kiro IDE

- Install: `plugins/specflow/` as a custom Power from a local folder. Installing from the repository subdirectory URL is to be verified.
- Keywords in the portable manifest support contextual activation.
- The runtime skill writes Kiro-native artifact paths.
- Kiro's native Spec agent may edit the same Markdown files; the next plugin resume reconciles hashes.
- With a configured specs folder, Kiro's spec panel lists the specs only when `.kiro/specs` points at that folder, which is the repository's own setup (§6.7). Kiro following such a link, and ignoring `.kiro/specflow/`, is to be verified (T-027).

### Codex

- Install: local folder `plugins/specflow/`. A marketplace or repository-subdirectory install is to be verified.
- Load the root Agent Plugins v1 manifest directly.
- Skills are discovered from `plugins/specflow/skills/`.
- OpenAI-specific metadata, if later needed, goes under `extensions.com.openai`; no OpenAI-specific workflow copy is introduced.

### Claude Code

- Install: through an entry for `plugins/specflow` in a root `.claude-plugin/marketplace.json`, generated from `plugins/*/plugin.json` and added to the monorepo when the first plugin ships; `--plugin-dir plugins/specflow` for local testing.
- Load the package using `.claude-plugin/plugin.json`.
- The compatibility manifest points to the same root `skills/` content.
- Claude-only invocation metadata may be added, but workflow and artifact semantics remain in the canonical skill.

### Untested hosts

Kiro CLI and Kiro Crew are expected to load the same package (Kiro CLI as a Power, Crew through its plugin import or skill mapping) but are not tested in the first release, and the documentation does not list them as supported. Crew-specific UI or `.spec-state.json` files are not canonical and must not replace `.specflow.json`. Either host joins the supported list once someone uses it and its loading probe passes.

### Host tests

Each test installs `plugins/specflow/` by the install surface the probe record names for that host, works in a throwaway workspace under `docs/dev/tmp/specflow/hosts/`, and writes its record. The workspace is made with `git init` and one empty commit (`git commit --allow-empty`), a repository of its own as the eval runs of 00009 have, and holds no `.agents/specflow.json`: its specs land in its own `.kiro/specs/`, and no git command of the agent reaches this repository. The plugin folder is given by its absolute path. A record states the host version, the install path used, each step with its result, the name under which the skill appeared, and the `status --json` output, the `.specflow.json`, and the artifact files of the spec as that host left it, so a later test can be rerun from the record after the scratch folder is purged. Later tasks append their own sections to a record.

| Task | Host | Steps to pass |
|---|---|---|
| T-040 | Kiro IDE | import as a custom Power from the local folder; the skill activates and reads a reference; create a spec, approve its requirements, close the session, and resume; Kiro's own Spec panel finds the spec |
| T-042 | Codex | load the root manifest; the skill is discovered; resume the spec Kiro created, reconcile its hashes (no change is expected), continue in the correct phase, and draft and approve the design and the task plan |
| T-043 | Claude Code | load the compatibility manifest with `--plugin-dir` and the absolute path of `plugins/specflow`; the skill appears as `specflow:spec-workflow`; edit the requirements and see design and tasks go stale; then Codex resumes the spec and reports the same stale design and tasks, which closes the hand-back |

### Host documentation

Before it writes an install line, T-045 tries each open install route once in a fresh host profile and appends the result, and whether the route takes a ref, to that host's record (bundle A1). It then writes one section of `plugins/specflow/README.md` with, per supported host: how to install, how to invoke, known differences in the interface, and one handoff example. Around them it states: recording an approval needs Python 3 on every host; Kiro IDE lists specs from a configured specs folder only through a `.kiro/specs` link that the repository sets up, with the result T-027 (00004) found; Kiro CLI and Kiro Crew are expected to work but are untested and are not listed as supported; sessions do not transfer between hosts, only the repository's files do.

### Marketplace manifest

`.claude-plugin/marketplace.json` at the repository root, generated:

```json
{
  "name": "buvis-agent-plugins",
  "description": "Portable agent plugins published by buvis.",
  "owner": {
    "name": "buvis",
    "url": "https://github.com/buvis"
  },
  "plugins": [
    {
      "name": "specflow",
      "source": "./plugins/specflow",
      "description": "Portable requirements, design, tasks, and implementation workflow using Kiro-compatible artifacts.",
      "version": "0.1.0"
    }
  ]
}
```

Checked on 2026-10-04: a manifest of this shape passes `claude plugin validate --strict <dir>`; without the top-level `description` it fails in strict mode. The marketplace name, `buvis-agent-plugins`, is the developer's choice of 2026-10-04 (ruling D12); it differs from the existing `buvis-plugins` marketplace.

```text
python3 scripts/generate_marketplace.py [--check]
```

The generator checks every `plugins/*/plugin.json` with `validate_manifest` of `scripts/validate.py`, skips a plugin that has no `.claude-plugin/plugin.json`, and writes one entry per remaining plugin, sorted by name, with `name`, `source` (`./plugins/<name>`), `description`, and `version` copied from the portable manifest; the top-level fields are constants in the script. One function, `build_manifest(root: Path) -> str`, returns the exact text of the file, with two-space indent and a final newline; writing and `--check` both call it, so the check compares text, not parsed JSON (bundle A2). With `--check` it writes nothing and exits 1 when the committed file differs from what it would write. Exit codes: 0 written or up to date, 1 out of date or an unreadable manifest.

## Data model

Not applicable: this spec stores no data. The marketplace manifest is generated and shown in full under Components and interfaces.

## Data and control flow

The three host tests run in the order Kiro IDE, Codex, Claude Code, because each later test takes over the spec the earlier one left: Kiro creates and approves, Codex resumes and reconciles, Claude Code edits and hands back. The task plan therefore makes T-042 depend on T-040, and T-043 on T-042. T-046 runs after T-043 and before T-045: the catalog exists only once Claude Code is tested, and the README can then name it. Its install check adds the marketplace from the local checkout, installs specflow through it, confirms `specflow:spec-workflow` is listed, and is recorded in `claude-code.md`. That Claude Code adds a marketplace from a local folder is recalled, not yet run; T-046 confirms it. The public route through GitHub is first exercised at release, by the install from the tag in T-065 of 00001 (bundle A4). T-045 is the last task.

## Error handling

- A host that fails a step is recorded with the failing step; it is fixed, or the documentation states the limit, or it leaves the supported list.
- An install surface that cannot be confirmed becomes a documented limitation, never a silent omission.
- The generator fails on a plugin manifest it cannot read, or that `validate_manifest` rejects, and names the file; it never writes a partial manifest.

## Security and privacy

- Host tests run in throwaway workspaces and use no credential.
- The marketplace entry points only at `./plugins/specflow`, so a marketplace install yields the same tree the release check verified.
- The marketplace manifest and its generator sit outside the package; no runtime file in `plugins/specflow/` names them, and only the README names the marketplace.

## Testing strategy

- T-040, T-042, T-043: the steps of the table above, each recorded with its result. The three together are the first cross-host handoff on the real package; the full sequence and its assertions are T-051 in 00009.
- T-045: the install steps of each host are followed on a machine that has never had the plugin, and they work as written. Two kinds of line cannot run before the release and are left to it: the public route of Claude Code (bundle A4), and any line that T-062 of 00001 later pins to the release tag. Every "to be verified" line under `### Kiro IDE`, `### Codex`, or `### Claude Code` of this design is gone, replaced by a confirmed path or a stated limit.
- T-046, `scripts/test_generate_marketplace.py`: `test_writes_one_entry_per_plugin`, `test_entry_copies_name_description_and_version_from_the_manifest`, `test_check_fails_when_the_committed_file_is_stale`, `test_check_compares_the_exact_text`, `test_skips_a_plugin_without_a_claude_manifest`, `test_fails_on_an_unreadable_manifest`. `claude plugin validate --strict .` passes on the generated file, and Claude Code installs specflow from the local checkout through the marketplace.

## Rollout and migration

The marketplace entry is added before the release, so installing through it can be tested, and the README plugin table changes only at release (00001, T-065). Resolving a "to be verified" line edits this design, which stales it and its task plan by the normal rule. T-006 (00002) and T-045 both do that, so each collects its corrections into one edit. For T-045 that edit is its last step: the developer then re-approves this design and its task plan, and only after that is the spec verified. The three "to be verified" lines are decisions deferred to later, accepted by name when the task plan is approved. Nothing migrates.

## Risks and edge cases

- An install path the source design marks "to be verified" does not work on a host: impact m, likelihood m; mitigation: T-045 resolves every such line into a confirmed path; fallback: the limit is documented for that host.
- A host changes how it loads plugins between the probe and these tests: impact m, likelihood l; mitigation: each record states the host version it was run on; fallback: rerun the probe of 00002 for that host.
- Likely next change, Kiro CLI or Kiro Crew joins the supported list: nothing here tests them; impact l, likelihood m; mitigation: the probe of 00002 and one more record file are all a new host needs; fallback: the host stays "expected but untested".
- Likely next change, a second plugin in the monorepo: the generator already reads every `plugins/*/plugin.json`; impact l, likelihood m; mitigation: none needed; fallback: none needed.
- Likely next change, a host that needs `plugin.json` at a repository root: nothing builds a distribution branch (PKG-002 criterion 6 of 00002 is dormant); impact m, likelihood l; mitigation: the records note the install surface of every host; fallback: the host stays unsupported until the branch exists.
- Edge case: Kiro Crew's own `.spec-state.json` is not canonical and never replaces `.specflow.json`.

## Requirement traceability

| Design element | Criteria |
|---|---|
| Host documentation: the supported list, and the two untested hosts named as untested | PKG-003.4 |
| Host tests on the real package | 00002 PKG-003 criteria 1, 2, 3 (cited across the dependency) |
| Marketplace manifest and its generator | 00002 PKG-003 criterion 3 (cited across the dependency: the Claude Code install route) |

## Alternatives considered

1. **A marketplace manifest written by hand** (smallest diff: one file, no script). Rejected. `README.md` and `AGENTS.md` rule out a hand-maintained catalog, because its version and description drift from the portable manifest.
2. **A generator with a check mode** (chosen). The added script buys a catalog that cannot drift: CI fails when the committed file is stale.
3. **A marketplace in a separate repository.** Rejected for now: no host needs it, and the monorepo already holds the plugin the entry points at.
4. **Scripted host tests here.** Rejected: the scripted runners and their sessions are 00009's work; this spec only shows each host loads the real package and records how. No existing tool was searched for; the generator is one loop over JSON files.

## Reuse inventory

- `scripts/validate.py`: `validate_manifest(plugin: Path) -> dict[str, object]`, `ValidationError`, and `ROOT`; the generator reads and checks the manifests through them.
- `host-loading-probe.md` (00002): the install surface and path that worked on each host.
- The spec fixtures and the helper of 00004, and the skill of 00006, exercised as a user would.
- `claude plugin validate`, for the generated manifest.
- Searches: `marketplace|catalog`, case-insensitive, over `scripts`, `.github`, `plugins`, and `templates` is recorded in the intake log; the repository has no catalog and no generator.

## Open decisions

No decision is open. Rulings of 2026-10-04 (design gates report), taken in above: D12, the marketplace is named `buvis-agent-plugins`; and the four fixes of bundle A (the install trials of T-045, the generator's contract, the lines in the root documentation, and the pre-release install from the local checkout).

Choices the source left to the design, made above and listed for approval: host test records under `tests/specflow/compatibility/`; the host documentation as a section of the plugin README; the generator in `scripts/` with a check mode in CI; and one batched design edit per task that resolves install lines.

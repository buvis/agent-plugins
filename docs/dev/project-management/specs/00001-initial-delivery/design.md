# Design: specflow initial delivery

## Overview

The solution is a skills-first Agent Plugins v1 package. Its runtime behavior is defined by one canonical workflow Agent Skill and a set of selectively loaded references, with a second distributed skill that converts an existing PRD or legacy intake item into specflow artifacts through those same contracts (§6.9). It stores durable workflow state beside Kiro-compatible Markdown artifacts, allowing another local coding agent to resume without session transfer.

The references carry two kinds of content. Method guidance comes from AWS AI-DLC: `awslabs/aidlc-workflows` (A1) is the primary source, with `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` (A2) and `aws-samples/sample-aidlc-discovery` (A3) as complementary sources. Adopted passages are adapted by hand into phase references, each naming its source (§10); a repository-only catch-up skill reviews the sources (§11). Spec discipline comes from the buvis personal SDLC skills (elicit-requirements, create-prd, spike, review-discovery-doc, review-design-doc, review-prd-backlog) and copied design-solution/plan-tasks phase behavior, ported as numbered behavior rules in local files that a catch-up never edits (§5.4). The two source phase skills stay in autopilot.

This spec closes release 0.1 of that product. The capabilities are built by specs 00002 to 00009. What is left here is what turns them into a release: the maintainer and user documentation, the changelog and versioning policy, verification of the release candidate, final acceptance on the three hosts, the tag, and the two handoffs to other repositories. It also holds the framing every other design cites: the design principles, the whole repository layout, and the references.

## Context and constraints

Decision inputs: `meta/decisions.md` (2026-09-27 scope and intake; 2026-09-28 aidlc-workflows; 2026-10-03 docs review, which supersedes parts of the first two and is cited below as "decision 2026-10-03 #n"), `discovery/00001-specflow-bugfix-workflow.md` §5, Plan A (`discovery/00001-specflow-port-agent-skills.md`), approved Plan B (`discovery/00001-specflow-port-autopilot-phases.md`), and `qa-log.md` beside this file. Plan B's document changes are applied here; T-079 builds its rule mappings and runtime references.

- Depends on 00002, 00003, 00005, 00007, 00008, and 00009, and through them on every spec: the release check, the catch-up skill, the rule checker, the reviews and conversion skill, the host documentation, and the evidence of 00009.
- In the carried line above, `qa-log.md` means the log of intake item 00001, and the decisions of 2026-10-04 (#7 to #11) are inputs too.
- By decision 2026-10-04 #10, T-061 takes over one check from T-053: the user documentation states the one-writer contract, and that writers at the same moment are outside it.
- `AGENTS.md` and `CONTRIBUTING.md` (repository root): a user-visible change gets a changelog entry in the same commit; the plugin table in the root README changes when a plugin is published.
- Tagging and publishing are outward-facing and cannot be undone cleanly. T-065 runs only on the developer's explicit instruction.
- T-066 and T-067 write into two other repositories, `buvis/claude-autopilot` and `buvis/agent-skills`. They add an intake item or a PRD there and change nothing else.

### Design principles

These nine principles bind every spec of the product; the other designs cite them by number.

1. **Artifacts over sessions**: repository files, not chat history, carry work between hosts.
2. **Portable core, thin adapters**: one normative skill; compatibility manifests contain no workflow logic.
3. **Human-readable truth**: Markdown owns requirements, design, and task progress.
4. **Minimal machine state**: JSON stores only approvals, hashes, the hold, and workflow metadata; the phase is derived.
5. **Explicit gates**: a later phase cannot legitimize an unapproved earlier phase.

6. **Cited upstream, explicit adaptation**: every adopted AWS passage names its source and its ref (A1: the release tag; A2 and A3: the commit); the source record maps each tag to its commit, and local behavior is layered separately.

7. **No runtime update channel**: installed plugins never fetch prompt changes.
8. **Allowlist releases**: releases are constructed from `plugins/specflow/`, not filtered from the whole repository.
9. **Rules before prose**: every ported skill behavior is a numbered rule with exactly one check (validator or scenario eval), so parity is measured, not claimed.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

### References

- Agent Plugins v1 specification: https://agent-plugins.org/specification
- OpenAI portable plugin packaging: https://developers.openai.com/plugins/build/plugins
- Kiro Powers creation: https://kiro.dev/docs/powers/create/
- Kiro Specs: https://kiro.dev/docs/specs/
- Kiro bugfix specs: https://kiro.dev/docs/specs/bugfix-specs/
- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Kiro Crew agent skills: https://github.com/kirodotdev/KiroCrew/blob/main/src/kiro_crew/docs/agents.md
- Kiro Crew plugin import: https://github.com/kirodotdev/KiroCrew/blob/main/docs/system-specs/modules/cli.md
- AWS AI-DLC workflows (A1, primary source): https://github.com/awslabs/aidlc-workflows
- AWS AI-DLC releases: https://github.com/awslabs/aidlc-workflows/releases
- AWS AI-DLC patterns (A2, complementary source, the original): https://github.com/aws-samples/sample-ai-powered-sdlc-patterns-with-aws/tree/main/all-phases/all-phases-aidlc-mcp
- AWS AI-DLC discovery (A3, complementary source): https://github.com/aws-samples/sample-aidlc-discovery

## Architecture

The whole product, as the source design drew it. Each spec's own design shows its part with the changes made since.

Only the specflow-owned paths of the monorepo are shown.

```text
agent-plugins/
├── plugins/
│   └── specflow/                        # The only distributable subtree
│       ├── plugin.json                  # Agent Plugins v1 manifest
│       ├── .claude-plugin/
│       │   └── plugin.json                  # Claude Code compatibility only
│       ├── skills/
│       │   ├── spec-workflow/
│       │   │   ├── SKILL.md                 # Normative runtime workflow
│       │   │   ├── references/
│       │   │   │   ├── artifact-contract.md
│       │   │   │   ├── state-contract.md
│       │   │   │   ├── validation-rules.md
│       │   │   │   ├── profiles/
│       │   │   │   │   ├── standard.md
│       │   │   │   │   └── quick.md
│       │   │   │   ├── phases/              # Behavior rules by phase (§5.4)
│       │   │   │   │   ├── intake.md            # Includes the spike path
│       │   │   │   │   ├── requirements.md
│       │   │   │   │   ├── design.md            # Design drafting and review handoff
│       │   │   │   │   ├── tasks.md             # Contracts, sizing, and planning summary
│       │   │   │   │   ├── implementation.md    # One task at a time, upstream error routing
│       │   │   │   │   └── verification.md      # Evidence mapping, completion, spike cleanup
│       │   │   │   ├── review/              # Review intents (§5.5)
│       │   │   │   │   ├── core.md              # Shared walkthrough and ground rules
│       │   │   │   │   ├── requirements.md
│       │   │   │   │   ├── design/              # Triage, checklist, cardinal sins, techniques,
│       │   │   │   │   │                        # lenses, anti-patterns, stress tests; loaded by tier
│       │   │   │   │   └── cross-spec.md
│       │   │   │   └── aws/                 # Hand-adapted AWS guidance (§10)
│       │   │   │       ├── adaptation.md        # Source record, mappings, what is not adopted
│       │   │   │       ├── LICENSE              # License of each source that text is copied from
│       │   │   │       ├── requirements.md
│       │   │   │       ├── design.md
│       │   │   │       ├── implementation.md
│       │   │   │       └── verification.md
│       │   │   ├── schemas/
│       │   │   │   ├── specflow-state.schema.json
│       │   │   │   ├── specflow-config.schema.json   # .agents/specflow.json (§6.7)
│       │   │   │   └── specflow-status.schema.json   # Status output (§7.6)
│       │   │   ├── templates/
│       │   │   │   ├── requirements.md
│       │   │   │   ├── design.md
│       │   │   │   ├── tasks.md
│       │   │   │   ├── bugfix/              # Kiro bugfix shape (§6.6)
│       │   │   │   │   ├── bugfix.md
│       │   │   │   │   ├── design.md
│       │   │   │   │   └── tasks.md
│       │   │   │   ├── intake/              # idea.md, qa-log.md, spike SPEC.md (§6.7, §6.8)
│       │   │   │   ├── cross-spec-review.md
│       │   │   │   └── specflow.json
│       │   │   └── scripts/                 # Optional local helpers, stdlib only
│       │   │       ├── validate_spec.py
│       │   │       ├── check_links.py           # Cross-spec citation check (§5.5)
│       │   │       └── review/                  # Advisory design-review scans (§5.5)
│       │   │           ├── section_weight_audit.py
│       │   │           ├── claim_ladder_scan.py
│       │   │           └── adversarial_signal_scan.py
│       │   └── convert-prd/                 # Conversion skill (§6.9, CNV-001)
│       │       ├── SKILL.md                 # Activation, discovery, conversion workflow, handoff
│       │       └── references/
│       │           └── conversion.md            # PRD-to-specflow conversion contract
│       ├── CHANGELOG.md
│       └── README.md
├── .agents/
│   └── skills/
│       └── catchup-specflow-upstream/
│           └── SKILL.md                 # Internal; the only committed copy; never distributed
├── tools/
│   └── specflow/
│       ├── verify_release.py            # Release-boundary and forbidden-marker checks
│       ├── check_rules.py               # Rule inventory checks (§5.4)
│       ├── rules/
│       │   └── inventory.json           # Rule ID -> source rows, reference, check
│       └── upstream/
│           └── sources.md               # One cursor per AWS source (§11.2)
├── tests/
│   └── specflow/
│       ├── fixtures/
│       ├── contract/
│       ├── compatibility/
│       ├── evals/                       # One scenario eval per behavioral rule (§15)
│       ├── parity/                      # Parity inputs and per-skill reports (§15)
│       └── release/
└── docs/dev/
    ├── project-management/intake/new/specflow/   # This specification
    ├── project-management/reviews/      # Tracked; catch-up reports land here (§11.3)
    └── tmp/specflow/                    # Ignored; scratch and diagnostics only
```

Changes to that tree since the split, each made in the design named:

- The specification is no longer one intake item. It is `docs/dev/project-management/specs/00001` to `00009`, each with an intake item under `intake/processed/specflow/`.
- `scripts/validate_spec.py` is a thin command line over the package `scripts/specflow_helper/` (00004).
- `tools/specflow/rules/` also holds `criteria.json` and a schema file for each of its two JSON files, and `tests/specflow/` also holds `rules/`, `review/`, and `security/` (00005, 00007, 00009).
- The repository root gains `.claude-plugin/marketplace.json` and `scripts/generate_marketplace.py` (00008), and already holds `.agents/specflow.json`.
- `references/review/design/` gains `pre-pass.md` (00007).
- `skills/spec-workflow/SKILL.md` exists from T-002 as a shell (00002) until T-030 writes the skill (00006).

For this spec the tree adds only documentation and the release itself:

```text
agent-plugins/
├── plugins/specflow/
│   ├── README.md                         # What it is, install pointer, first test, provenance
│   ├── CHANGELOG.md                      # The 0.1.0 entry
│   └── docs/
│       └── user-guide.md                 # The workflow, for a developer
├── docs/dev/procedures/
│   ├── running-a-specflow-catch-up.md
│   ├── adding-a-specflow-rule.md
│   └── releasing-specflow.md             # Versioning policy and the release checklist
└── docs/dev/project-management/reviews/
    └── YYYY-MM-DD-specflow-release-verification.md
```

## Module placement

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `docs/dev/procedures/running-a-specflow-catch-up.md` | new | T-060 | the cursors, the ruling report, the cadence, adoption from an A1 release tag, the source-line format, the adoption set; that the catch-up skill is repository-only, stated at the top |
| `docs/dev/procedures/adding-a-specflow-rule.md` | new | T-060 | the rule inventory, `check_rules.py` with its `--area` construction option and its unfiltered release run, how to add a rule and its check |
| `CONTRIBUTING.md` | edit | T-060 | links to the two procedures |
| `CONTRIBUTING.md` | edit | T-062 | a link to the release procedure |
| `plugins/specflow/docs/user-guide.md` | new | T-061 | create, spike, continue, status, the reviews, hold, implementation, approval, recovery, cross-tool handoff, the conversion skill, the workspace config, the specs folder and the `.kiro/specs` link, the one-writer contract, the intake tree, the status document for external runners, examples for both profiles |
| `plugins/specflow/README.md` | edit | T-061 | the six items `CONTRIBUTING.md` requires (what the plugin does and the tested hosts; its two skills and the Claude Code adapter; prerequisites, installation, and authentication, which is none; the files and data it reads and writes; a credential-free first test; failure behavior and uninstall) and a link to the guide; the line saying the plugin is unreleased goes (bundle C4) |
| `tests/specflow/release/test_docs.py` | new | T-061 | the documentation tests |
| `docs/dev/procedures/releasing-specflow.md` | new | T-062 | what a breaking change is, and the release checklist |
| `plugins/specflow/CHANGELOG.md` | edit | T-062 | the 0.1.0 entry |
| `plugins/specflow/README.md` | edit | T-062 | the release tag written into each install line whose route takes a ref |
| `tests/specflow/release/test_docs.py` | edit | T-062 | `test_changelog_and_install_lines_carry_the_manifest_version` |
| `docs/dev/project-management/reviews/YYYY-MM-DD-specflow-release-verification.md` | new | T-063 | the candidate commit and the tree id of its package, the release check output, the full criterion to rule to check output, the review of the required criteria, the file list |
| the same report | edit | T-064 | the catch-up report's name, the install result per host, the eight measures with their evidence |
| `docs/dev/project-management/reviews/YYYY-MM-DD-specflow-upstream-catchup.md`, `tools/specflow/upstream/sources.md` | new, edit | T-064 | the report and the cursor moves of the catch-up before the release |
| `README.md` | edit | T-065 | the plugin table gains specflow |
| git tag `specflow-v0.1.0` and its release notes | new | T-065 | the release |
| an intake item in `buvis/claude-autopilot` | new | T-066 | the repoint request |
| an intake item or PRD in `buvis/agent-skills` | new | T-067 | the retirement request with the parity reports |

## Components and interfaces

### Release process

1. Run a catch-up over every source (§11). Ensure tests, the unfiltered `check_rules.py`, cross-host handoff (T-051), all-host scenario evals (T-057), and parity checks (T-058) pass for the candidate's runtime and fixture contents. All gate release 0.1 (§15); no capability or proof is postponed.
2. Update plugin version and changelog.
3. Run `tools/specflow/verify_release.py` against `plugins/specflow/` in a clean checkout: manifests, paths, source record, license, and forbidden contents.
4. Test local installation in Kiro IDE and Codex following each §12 Install line; resolve every "to be verified" line into a confirmed path or a documented limitation.
5. Test Claude compatibility loading.
6. Tag the monorepo `specflow-vX.Y.Z` only after all checks pass. The tagged `plugins/specflow/` subdirectory is the release; hosts install it from the repository.

### Versioning policy of T-062

The plugin version changes whenever runtime instructions, distributed references, the state schema, or compatibility behavior changes. While the plugin is at 0.x, a breaking change raises the minor version and any other runtime change the patch. A change is breaking, and raises the major version once the plugin is past 0.x, when it breaks: the state schema, the config schema, the status output, the artifact contract, approval semantics, or host compatibility. An update that only refreshes an AWS reference from a new upstream tag, with no change to a rule or a contract, is a patch. Each schema carries its own version field (`schemaVersion`, `statusVersion`), raised on a breaking change to that shape, with a changelog entry. The release checklist asks for a version decision and a changelog decision before a tag is made.

The version is written in these places, and the release procedure lists them: the root manifest and the compatibility manifests; `WORKFLOW_VERSION` and the `$id` of each schema (00004); the marketplace entry (00008); the changelog heading; and each install line in the README whose route takes a ref, where T-062 writes the release tag (T-045 of 00008 records which routes do). They are compared with the root manifest by the release check (manifests, constant, and schema addresses), by the generator's `--check` (marketplace entry), and by `test_changelog_and_install_lines_carry_the_manifest_version` in `test_docs.py`; T-063 runs all three (bundle C3).

### Release evidence of T-063 and T-064

One report holds both. T-063 runs, on a clean checkout of the candidate commit, `python3 tools/specflow/verify_release.py` and `python3 tools/specflow/check_rules.py` with no filter, and keeps both outputs in full; it then reads each required criterion against the assertions of its mapped check, so a link to an unrelated or incomplete check cannot pass as coverage; and it lists the manifest, the file list, the license, the source record, and the AWS references it inspected. T-064 first runs a catch-up over every source, then installs the candidate commit in Kiro IDE, Codex, and Claude Code, runs the cross-host handoff from that commit, and records each of the eight success measures with its evidence. Evidence from 00009 counts for the revisions it names, with one exception. A stored run record stays valid for the candidate when the difference between its `runtimeRevision` tree and the candidate's package touches only `README.md`, `CHANGELOG.md`, and `docs/`. A change under `skills/` or to a manifest stales every session, and T-064 runs them all again. This spec edits the package after the host runs of 00009, so the rule decides its cost: T-061, the changelog edit, and the pinned install lines stay inside the three safe paths. The schema addresses would not, so by the developer's ruling of 2026-10-04 (D13) the schemas carry them as `$id` from the tasks of 00004 that write them, and T-062 edits no schema. T-060's trial rule is added on a throwaway branch and never merged. T-063 also runs the CI test commands on the clean checkout, with `PYTHONDONTWRITEBYTECODE=1`, and keeps their counts in the report.

The tag goes on the commit that holds the evidence report, the catch-up outputs, and the README row. T-065 runs both tools on that commit again and records `git rev-parse <tag>:plugins/specflow`, which must equal the tree id that was tested. Those two outputs and the tree id go into the release notes, not into the report, since a file in the tagged commit cannot describe the tag. A release tag is never moved or deleted; a bad release is fixed by a new one. The release notes are the GitHub release of the tag, and list A1's tag and commit and the commits of A2 and A3, copied from the source record. Once the tag is pushed, T-065 fetches the three schema addresses and records the result in the release notes. No instance file carries a `$schema` key in this release, since nothing reads one yet (bundle C1).

### Handoffs

- T-066 asks autopilot to read approved specs from the specs folder through the status document (`statusVersion` cited) instead of `prds/backlog`, and to keep its own settings out of specflow's files. It names the dependency: create-prd and review-prd-backlog retire only after that repoint lands. Nothing in `plugins/specflow/` names autopilot.
- T-067 gives `buvis/agent-skills` the parity reports and the Retirement block of Plan A: elicit-requirements, review-discovery-doc, review-design-doc, and spike first; create-prd and review-prd-backlog once the repoint of T-066 has landed.

## Data model

Not applicable: this spec stores no data. Versions live in the places the versioning policy lists; the release evidence is one Markdown report.

## Data and control flow

Order: T-060 and T-061 (documentation) in either order; T-062 (policy, changelog, pinned install lines); T-063 (verify the candidate); T-064 (final acceptance); T-065 (tag and publish, on the developer's instruction); then T-067. T-066 needs only T-061 and can go out earlier. A change to the package after T-063 makes a new candidate: T-063 and the affected parts of T-064 run again on it.

## Error handling

- A failed release check, a failed rule check, or a failed measure stops the release; nothing is tagged.
- Evidence whose package revision differs from the candidate's outside the safe paths of the staleness rule, or whose fixture revision differs, is not evidence for it; the check is rerun.
- A handoff whose target repository cannot be written is reported with the text of the item, so the developer can file it by hand.
- The documentation tests fail on a path that no longer exists in the package, so a stale example cannot ship.

## Security and privacy

- The release is the tagged `plugins/specflow/` subtree; nothing outside it is installable, and the release check has passed on exactly that commit.
- No tag, release, or push to another repository happens without the developer's explicit instruction.
- Release notes and handoff items hold no secret and no machine path.
- The catch-up before the release reads upstream as data and runs nothing from it (00003).

## Testing strategy

- T-060: a fresh agent session, given only the two procedures, runs a review-only catch-up and adds one rule with its eval record; what it had to ask is a defect in the documentation.
- T-061, `tests/specflow/release/test_docs.py`: `test_every_path_in_the_user_guide_exists_in_the_package`, `test_examples_match_the_fixture_specs`, `test_user_guide_states_the_one_writer_contract`, `test_readme_lists_only_supported_hosts_as_supported`, `test_package_does_not_name_autopilot`. A package path in the guide is inline code that starts with `plugins/specflow/`, so the path test can find it; the test holds the map from each example in the guide to its fixture spec; and the supported hosts are a constant in the test (bundle C2).
- T-062: `test_changelog_and_install_lines_carry_the_manifest_version`; the release checklist names the version and changelog decisions. The schema addresses are already checked by the release check (00004).
- T-063: both tools exit 0 on the clean checkout; the catch-up skill, the cursors, the rule inventory, the evals, the parity reports, and every repository-only tool are absent from `plugins/specflow/`.
- T-064: all eight measures hold, including the evals on all hosts and parity; no accepted capability or check is deferred.
- T-065: installing from the tag yields the tree that was tested, compared by the git tree id of `plugins/specflow/`.
- T-066: the item exists in claude-autopilot and cites the status schema version; `test_package_does_not_name_autopilot`, which T-061 writes into `test_docs.py`, scans the package, case-insensitive. T-067: the item or PRD in agent-skills cites each parity report, and every skill it retires is marked ready in its report.

## Rollout and migration

This spec is the rollout. The first release has no earlier version, so nothing migrates on the plugin's side. On the developer's side, the personal skills retire in their own repository after their parity gates, and autopilot repoints in its own; neither is done here. The root README plugin table changes with the tag, not before.

## Risks and edge cases

- The evidence goes stale because the package changes after the host runs: impact h, likelihood m; mitigation: the staleness rule above keeps documentation edits from staling anything, and the schema addresses are written in 00004 (ruling D13); fallback: T-064 reruns every session on three hosts.
- A handoff's target repository is not ready for it, since its own backlog decides when: impact l, likelihood m; mitigation: the handoff is an intake item, which waits without blocking this release; fallback: the two source skills stay in use.
- The catch-up before the release finds an upstream change worth adopting: impact m, likelihood m; mitigation: a ruling can defer it to the next release; fallback: adopt it, which makes a new candidate.
- Likely next change, release 0.2: the process is a checklist run by hand; impact l, likelihood h; mitigation: every step is a command or a recorded run; fallback: none needed.
- Likely next change, a host that needs `plugin.json` at a repository root: nothing builds a distribution branch (00002 PKG-002 criterion 6 is dormant); impact m, likelihood l; mitigation: the release check works on any folder; fallback: the host stays unsupported.
- Likely next change, a release workflow in CI: host runs need signed-in hosts and a person; impact l, likelihood m; mitigation: the deterministic half already runs in CI; fallback: keep the tag manual.
- A pinned install line is wrong, and it first runs once the tag exists: impact m, likelihood l; mitigation: T-045 of 00008 proved the same route unpinned, so only the ref differs; fallback: a patch release, since a tag is never moved.
- Edge case: an upstream-only patch release still follows a catch-up over every source and the full release check.

## Requirement traceability

| Design element | Criteria |
|---|---|
| Release process, step 6; T-065 | REL-001.4 |
| Release process, step 1; the catch-up of T-064 | REL-001.5, REL-002.5 |
| Versioning policy | REL-001.6 |
| Release evidence of T-063 | REL-002.4 |
| Release evidence of T-064; release process, step 1 | REL-003.1, REL-003.2, REL-003.3 |
| Documentation and handoffs | criteria of 00002 to 00009, cited across the dependency |

## Alternatives considered

1. **Tag and publish with no stored evidence** (smallest diff: no report). Rejected. REL-001 criterion 4 ties a release to a tree that passed release verification, and a pass nobody can read later is not one.
2. **One evidence report per release, written by T-063 and T-064** (chosen). The added file buys a release anyone can check after the fact.
3. **A release workflow that tags from CI.** Rejected for the first release: the host runs and the acceptance on three hosts cannot run there.
4. **A changelog or release tool.** Rejected without a registry search: one plugin, one changelog in the repository's own format, and the commit rule already puts each entry in the same change.

## Reuse inventory

- `tools/specflow/verify_release.py` (00002, extended in 00003) and `tools/specflow/check_rules.py` (00005).
- The catch-up skill and `tools/specflow/upstream/sources.md` (00003).
- The host section of `plugins/specflow/README.md` (00008) and the probe record (00002).
- The run records, the parity reports, and the two maintainer guides under `tests/specflow/` (00009).
- The status schema of 00004, cited by version in the autopilot handoff.
- `templates/example-plugin/CHANGELOG.md`: the changelog format. `CONTRIBUTING.md`: the list of what a plugin README states.
- Searches: `release|changelog|version`, case-insensitive, over `scripts`, `.github`, `plugins`, and `templates` is recorded in the intake log; the repository has a changelog format and no release tooling.

## Open decisions

No decision is open. Rulings of 2026-10-04 (design gates report), taken in above: D13, the schema addresses are written in 00004 and T-062 edits no schema; and the five fixes of bundle C (the `$id` keyword and the fetch after the tag, how the documentation tests are built, the version-bearing places and pinned install lines, the six README items, and principle 6).

Choices the source left to the design, made above and listed for approval: maintainer documentation as three procedures under `docs/dev/procedures/`; user documentation as the plugin README plus `plugins/specflow/docs/user-guide.md`; one release evidence report for T-063 and T-064; and T-065, T-066, and T-067 only on the developer's explicit instruction.

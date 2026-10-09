# Design: specflow AWS sources and catch-up

## Overview

This spec gives specflow its method sources and a way to keep up with them: a source record, four hand-adapted AWS references that name every source, the licenses, and a repository-only catch-up skill.

Nothing upstream is vendored. The plugin ships a source record and four hand-adapted references; a maintainer keeps them current through the catch-up skill (§11).

## Context and constraints

- Depends on 00002: `plugins/specflow/` exists, and `tools/specflow/verify_release.py` rejects maintainer names inside the package, the catch-up skill's among them.
- `AGENTS.md` (repository root, whole repository): tooling is dependency-free Python. `scripts/validate.py` checks skills under `plugins/*/skills/` and the template only, so a maintainer skill under `.agents/skills/` is unchecked today.
- A1 was read at `v2.10.0`, A2 and A3 at the commits named below. These facts come from the source design and its Q&A log, not from a fresh read of the upstream repositories. The pre-pass reviewer's `git ls-remote` on 2026-10-04 adds three: `v2.10.0` is still the latest A1 release, A1 also publishes preview tags such as `v2.10.1-preview.20261003.2`, and A2 and A3 still point at the commits named below. A2 has no tags; A3 has tags, and its `v2.0.1` is `a84b289`. Both are still recorded by commit, as UPD-002 criterion 7 asks.
- In the files T-010, T-014, and T-018 write, a section number of the source design is replaced by the name of what it points to; `§` numbers stay in this design only.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

`.agents/skills/` holds the repository's only committed copy of a maintainer skill, named `<verb>-<plugin>-<object>`; its support files live under `tools/<plugin>/`. No agent-private folder (`.claude/`, `.kiro/`, `.codex/`) is committed, and no symlink to one. A maintainer's tool reaches the skill natively (Codex reads `.agents/skills/`), through a local, ignored projection made by the repository's onboarding command once that exists, or by being told to read the `SKILL.md`. `AGENTS.md` and `CONTRIBUTING.md` state this convention (UPD-001.7).

## Architecture

```text
agent-plugins/
├── plugins/specflow/skills/spec-workflow/references/aws/   # Hand-adapted AWS guidance, shipped
│   ├── adaptation.md        # Source record, mappings, what is not adopted
│   ├── LICENSE              # Attribution and license of each source that text is copied from
│   ├── requirements.md
│   ├── design.md
│   ├── implementation.md
│   └── verification.md
├── .agents/skills/catchup-specflow-upstream/SKILL.md       # Internal; the only committed copy; never distributed
├── tools/specflow/upstream/sources.md                      # One cursor per AWS source
└── docs/dev/project-management/reviews/                    # Catch-up reports
```

Two things cross the package boundary in one direction only. Adapted text and the source record go into the package, written by hand. The catch-up skill, its cursors, and its reports stay outside and are never named inside.

## Module placement

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `plugins/specflow/skills/spec-workflow/references/aws/adaptation.md` | new | T-010 | source record, profile-to-depth mapping, what is not adopted |
| `tools/specflow/upstream/sources.md` | new | T-010 | one cursor row per source |
| `tests/specflow/release/test_sources.py` | new | T-010 | every recorded source has a cursor row |
| `plugins/specflow/skills/spec-workflow/references/aws/LICENSE` | new | T-011 | attribution and license of each source that text is copied from |
| `plugins/specflow/README.md` | edit | T-011 | provenance: the three sources, by name and repository |
| `tools/specflow/verify_release.py` | edit | T-011 | `check_sources`: the record, license, and attribution rules |
| `tests/specflow/release/test_verify_release.py` | edit | T-011 | their tests; `make_package` gains a minimal source record, `aws/LICENSE`, and a minimal `SKILL.md` |
| `plugins/specflow/skills/spec-workflow/references/aws/requirements.md`, `design.md`, `implementation.md`, `verification.md` | new | T-014 | adopted passages under source lines |
| `tools/specflow/verify_release.py` | edit | T-014 | `check_sources`: the source-line, ref, and plumbing rules |
| `tests/specflow/release/test_verify_release.py` | edit | T-014 | their tests; `make_package` gains four minimal references, each with one valid source line |
| `.agents/skills/catchup-specflow-upstream/SKILL.md` | new | T-018 | the catch-up sequence |
| `AGENTS.md`, `CONTRIBUTING.md` | edit | T-018 | the maintainer-skill convention |
| `.gitignore` | edit | T-018 | `/.claude/`, `/.kiro/`, `/.codex/`, so a local projection of the skill is never committed |
| `scripts/validate.py`, `scripts/test_validate.py` | edit | T-018 | check `.agents/skills/*/SKILL.md` |
| `docs/dev/project-management/reviews/YYYY-MM-DD-specflow-upstream-catchup.md` | new | T-018 | the first catch-up report |
| `tools/specflow/upstream/sources.md` | edit | T-018 | the cursors the first catch-up advances |

## Components and interfaces

### Source record

`aws/adaptation.md` opens with the source record (AWS-001.1-2):

| Source | Role | Adopted from | License |
|---|---|---|---|
| A1 `awslabs/aidlc-workflows` | primary method | release tag `vX.Y.Z` and the commit it points to | MIT-0 |
| A2 `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` | complementary patterns; the original source | commit | MIT-0 |
| A3 `aws-samples/sample-aidlc-discovery` | complementary discovery | commit | MIT-0 |

Adoption from A1 uses release tags only (UPD-002.7). A tag may be annotated: at `v2.10.0` (checked 2026-09-28) the tag object is `b1854bad` and the commit it points to is `2a883858`; the record names the commit. A2 and A3 may have no tags, so a commit is recorded. `aws/LICENSE` holds the license of every source that text is copied from (AWS-001.4).

The A1 files specflow adopts from are the phase-fit set of aidlc decision #2: `core/scopes/*.md`; the stages `requirements-analysis`, `domain-design`, `units-generation`, `code-generation`, and `build-and-test`; `stage-protocol.md` (`3. Question Format` and `8. Depth Guidance`); and the stage-by-scope matrix in `docs/guide/05-scopes-and-depth.md`. This set is the catch-up's review scope for A1, not a shipped copy. The scope also covers the twelve stages that rules were adapted from without taking text: the seven `ideation` stages, the three `initialization` stages, `practices-discovery`, and `reverse-engineering` (§9.4). The other sixteen stages A1 has at `v2.10.0` (four inception, five construction, seven operation) have not been read against specflow.

The record rows have one fixed form, so a tool can read them. An A1 release tag matches `^v\d+\.\d+\.\d+$`; a preview tag is never adopted from. The adopted-from cell of A1 holds the tag and the full commit it points to, each in backticks. The cells of A2 and A3 hold the full commit the adapted rules were read at, in backticks; nothing is adopted from A2 yet, so its cell records what was read.

### AWS references

`aws/{requirements,design,implementation,verification}.md` are written by hand. Each adopted passage sits under a source line, carries a profile mark so the agent reads only its own (§9), and is followed by any local adaptation, marked as such (AWS-002.3-4):

```markdown
> Source: A1 `core/aidlc-common/stages/inception/requirements-analysis.md` > Steps @ v2.10.0 (2a883858) [both]

<adopted text, engine plumbing left out per §9.4>

Adaptation: <local line, where the Kiro artifact contract differs>
```

The profile mark is `[standard]`, `[quick]`, or `[both]`. Release verification checks that every source line names a source and a ref in the source record (REL-001.3). The behavior rules of §5.4 are separate files; a catch-up never edits them.

By the developer's ruling of 2026-10-04 (D7), the text under a source line is verbatim: cuts are shown as `[...]`, and the passage ends at the next `Adaptation:` line, source line, or heading. Reworded upstream method goes on `Adaptation:` lines under the source line it came from. Engine plumbing is cut, not reworded. No check compares a passage with upstream in this release; the mark makes such a check possible, and a catch-up reads the diff.

### Profile mapping

AWS AI-DLC (`awslabs/aidlc-workflows`, "A1") runs 11 scopes over 33 stages at three depths. specflow keeps two profiles and Kiro's three documents, and maps the profiles onto A1's depth axis, not its scopes: `standard` is A1 Standard, `quick` is A1 Minimal (AWS-002.5). A1 scope names never become profiles: some skip artifacts specflow always writes (`express` has no design pass), and `bugfix` is already a spec type. Stage paths below are under `core/aidlc-common/stages/`.

### Standard profile

| Portable phase | AWS guidance source (depth Standard) | Portable output |
|---|---|---|
| Intake | No A1 stage; A3 discovery rules adapted as local rules (§9.4); local `phases/intake.md` (repository discovery) | Context feeding requirements and design |
| Requirements | `inception/requirements-analysis.md`; `stage-protocol.md` `## 3. Question Format` | `requirements.md` |
| Design | `inception/domain-design.md`, `inception/units-generation.md` | `design.md` |
| Tasks | None; local `phases/tasks.md` (contracts, sizing, and verification) | `tasks.md` |
| Implementation | `construction/code-generation.md` (test floor) | Source changes plus task updates |
| Verification | `construction/build-and-test.md`; `stage-protocol.md` `## 8. Depth Guidance` (test strategy) | Test evidence and task completion |
| Deployment | Not in the adoption set | Design/tasks sections when in scope, not a fourth artifact |

### Quick profile

| Portable phase | AWS guidance source (depth Minimal) | Portable output |
|---|---|---|
| Intake | No A1 stage; the same adapted A3 rules; local `phases/intake.md` (targeted discovery) | Concise impact assessment |
| Requirements | `inception/requirements-analysis.md`, Minimal passages | `requirements.md` |
| Design | `inception/domain-design.md`, Minimal passages; existing-pattern assessment (ART-003.5) | Minimal `design.md` |
| Tasks | None; local `phases/tasks.md` (same checks, concise task text) | `tasks.md` |
| Implementation | `construction/code-generation.md` Minimal floor (one test per requirement plus a happy-path floor) | Source changes |
| Verification | `construction/build-and-test.md`, Minimal passages | Regression evidence |
| Deployment | Not in the adoption set | Conditional design/task entries |

`stage-protocol.md` is at `core/aidlc-common/protocols/stage-protocol.md`; the other stage files in the two tables are under `core/aidlc-common/stages/`.

### Adaptation rule

A1's stage files wrap the method in engine plumbing. Adaptation keeps the method and leaves the plumbing out: engine calls (`aidlc engine ...`, `bun .../aidlc-utility.ts`), the `[Answer]:` question-file protocol, audit events, sensors, harness tokens (`{{HARNESS_DIR}}`, `{{INVOKE}}`), and `aidlc/` record paths. None of these is copied into normative runtime instructions. `adaptation.md` records each mapping, and the AWS references keep source traceability while making it clear that the local artifact contract wins.

Because the plumbing outweighs the method, most reference text is adapted, with short verbatim passages. AWS-002.4 still holds: every verbatim passage sits under its source line, and every local line is marked as adaptation.

`adaptation.md` also records what specflow notes but does not adopt from A1: question batching (up to four per turn) and the three answer modes, since one question at a time stays; `FR{n}`/`NFR{n}` IDs, since feature specs keep `REQ-`/`T-`; scope names as profiles; and Guard Policy `relaxed`/`off` with advisory staleness (§17).

The two complementary sources are recorded the same way (AWS-001.5). A2, `aws-samples/sample-ai-powered-sdlc-patterns-with-aws`, was the original source (first read at `3e7c0f0`) and calls itself complementary to A1; its `all-phases/all-phases-aidlc-mcp/` pattern stays under review. A3, `aws-samples/sample-aidlc-discovery` (first read at `a84b289`), covers the discovery that comes before a spec. From A3 specflow adapts these as local rules (decisions 2026-10-03 #10 and #11):

- what must not change, in the repository and in systems outside it, and how to learn about those systems (WF-003.11);
- binding technical constraints when the repository gives nothing to infer, each ban with its reason and alternative, plus one example to imitate (WF-003.12);
- intake choices saved to disk as soon as they are confirmed (WF-003.13), and a profile that can be raised later (WF-003.14);
- genuine uncertainty in hedged answers recorded as unresolved questions, with definite current choices and later follow-ups kept distinct (decision 2026-10-04 #2); a source for every inferred answer, and a progress line while asking (ART-002.12-14);
- answers logged in the developer's own words, in an append-only log (INT-001.5);
- English structure whatever the developer's language (ART-001.11), and a validation failure for an unclosed code fence (VAL-001.11);
- a sketch form of the spike: a user journey and static mockups (INT-002.8).

It does not adopt A3's product-level documents (requirements non-goal 10), parallel roles, batch answer files, the audit log of every interaction, or automatic language detection.

A1's ideation and initialization stages, and its `practices-discovery` and `reverse-engineering` stages, sit outside the adoption set of §10.1: no text is taken from them. A full read of all twelve (decision 2026-10-03 #12) gave these local rules:

- one fixed rule for "existing code or empty", and a coverage statement for every discovery (WF-003.15, WF-003.16; from `workspace-detection` and the scope block of `reverse-engineering`);
- a source for every requirement, nothing unpicked turned into scope, and assumptions named at approval (ART-002.15, WF-002.1; from the grounding contract of `intent-capture`);
- applicable repository instructions read on every host, with their scope preserved (WF-003.17; from the guardrail files each A1 stage loads, refined by decision 2026-10-04 #5);
- an existing library, tool, or service among the design alternatives (ART-003.12; from `market-research`);
- a commit recorded at approval and a drift warning (WF-004.8; from the freshness guard of `reverse-engineering`);
- a "not decided yet" choice, plain words with terms defined, and a playback before drafting (ART-002.16-18; from `intent-capture`, `practices-discovery`, and the summary checkpoint in `stage-protocol.md`);
- working practices asked when nothing shows them (WF-003.18; from `practices-discovery`), and a `Depends on:` line between specs (ART-002.11, WF-001.9; from the dependency register of `feasibility`);
- design-system/accessibility context and an accessibility note for sketches (INT-002.8; from `rough-mockups`, with known-answer reuse and the spike budget per §6.8), and one explicit path for an input file (INT-001.8; from `intent-capture`).

Not taken from those stages: stakeholder maps and team formation, market sizing and competitor analysis, the go/no-go brief, backlog scoring, multi-repo work, the shared code knowledge base with its locks and fingerprints, and saving confirmed practices into the repository's own files.

### Location and visibility

The catch-up skill lives at:

```text
.agents/skills/catchup-specflow-upstream/SKILL.md
```

This is the only committed copy (§3). It is available only when an agent works in the plugin source repository. It is not copied into `plugins/specflow/`, referenced by the plugin manifest, or mentioned as an installed-user capability. It is instructions for an agent, with no script of its own: it reads diffs with ordinary `git` commands.

### Release check for sources

`check_sources` joins the three checks of `tools/specflow/verify_release.py` (00002) and is called from `main` beside them. T-011 writes its record, license, and attribution rules; T-014 adds its source-line, ref, and plumbing rules.

```python
AWS_DIR = Path("skills/spec-workflow/references/aws")
AWS_REFERENCES = ("requirements.md", "design.md", "implementation.md", "verification.md")
RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")
SOURCE_LINE = re.compile(
    r"^> Source: (A[123]) `[^`]+` > \S.* @ (v\d+\.\d+\.\d+|[0-9a-f]{7,40})"
    r"(?: \(([0-9a-f]{7,40})\))? \[(standard|quick|both)\]$"
)
LOOKS_LIKE_SOURCE = re.compile(r"(?i)^\s*>?\s*\**\s*source\**\s*:")
ENGINE_PLUMBING = ("{{HARNESS_DIR}}", "{{INVOKE}}", "aidlc engine", "[Answer]:")

def check_sources(plugin: Path) -> list[str]: ...
```

Rules of T-011:

- `adaptation.md` is missing, or its source record lacks a row for A1, A2, or A3 with a role, an adopted-from cell in the fixed form, and a license. An A1 tag that does not match `RELEASE_TAG` is an error.
- `LICENSE` is missing or empty.
- Attribution: `LICENSE` opens with one line per source that text is copied from, naming its repository (for example `awslabs/aidlc-workflows`), followed by that source's license text. A source that has a source line in the references and no such line in `LICENSE` is an error. T-011 therefore introduces `SOURCE_LINE`, to read which sources the references cite; the errors about the lines themselves come with T-014.

Rules of T-014, applied to the four references only (`adaptation.md` names the plumbing on purpose and holds no source line):

- A reference is missing, or holds no line that matches `SOURCE_LINE`.
- A line matches `LOOKS_LIKE_SOURCE` and not `SOURCE_LINE`: a mistyped source line.
- A source line's ref is not in the record: the line's source must be a record row; an A1 line's tag equals that row's tag, and its commit, when given, is a prefix of seven or more characters of that row's commit; an A2 or A3 line's ref is such a prefix of its row's commit, and a parenthesised commit on an A2 or A3 line is an error.
- Any `ENGINE_PLUMBING` string.

### Validator check for maintainer skills

T-018 makes `scripts/validate.py` check `.agents/skills/*/SKILL.md` with the rules it already has. `validate_skills(plugin)` reads `plugin / "skills"`, so the edit is one call in `main`, made only on a default run with no path argument:

```python
agents = ROOT / ".agents"
if not args.paths and (agents / "skills").is_dir():
    try:
        skill_count += validate_skills(agents)
    except ValidationError as error:
        errors.append(str(error))
```

## Data model

### Source cursors

`tools/specflow/upstream/sources.md` holds one cursor per source (UPD-002.1):

```markdown
| Source | Role | Reviewed through | Reviewed on | Scope |
|---|---|---|---|---|
| A1 awslabs/aidlc-workflows | primary method | <commit> (vX.Y.Z) | 2026-10-03 | the adoption set of design §10.1, release notes |
| A2 aws-samples/sample-ai-powered-sdlc-patterns-with-aws | complementary patterns | <commit> | 2026-10-03 | all-phases/all-phases-aidlc-mcp/, then the wider catalog |
| A3 aws-samples/sample-aidlc-discovery | complementary discovery | <commit> | 2026-10-03 | aidlc-discovery-rules/, src/ |
```

A cursor says how far a source has been reviewed. It is separate from the adopted-from ref in the source record (§10.1): a catch-up may read unreleased A1 commits and move the cursor past the last tag, while adoption stays on tags.

T-010 writes `sources.md` in this shape with two changes. It adds a `URL` column holding each source's `https://github.com/...` remote, the only remotes a catch-up fetches. And each Scope cell lists literal paths: for A1 the files of the adoption set named under Source record, written as repository paths, and the release notes. Each Scope cell also names the source's license files, which step 4 of the sequence diffs (ruling D6).

T-010 seeds each cursor with the ref last read in full and the date of that read: A1 `2a883858` (`v2.10.0`), A2 `3e7c0f0`, A3 `a84b289`. A newer A1 release tag that T-010 picks as the adopted-from ref never moves a cursor; only a catch-up does.

## Data and control flow

### Catch-up sequence

1. Verify execution from the plugin source repository root.
2. Read `sources.md` and the rulings the last report deferred.
3. Fetch each configured HTTPS repository into a fresh temporary directory outside the tracked tree. Run nothing from it (SEC-001).

4. For each source, read what changed since its cursor within its scope (`git log` and `git diff <cursor>..<head> -- <paths>`; for A1 also the release notes). Diff the source's license files over the same range; each Scope cell names them (ruling D6).

5. Rule on each change considered: adopt, adapt, defer, or reject, with the source evidence, the local impact, and the upkeep cost. Rule again on each deferred item. A license change blocks adoption from that source until the maintainer rules on it.
6. Write the report to `docs/dev/project-management/reviews/YYYY-MM-DD-specflow-upstream-catchup.md`. A source with nothing to adopt gets a line saying so.
7. Advance the cursor of each fully reviewed source. A source that could not be read, or was only partly reviewed, keeps its cursor, and the report says coverage is incomplete.

8. The default run ends here: review and report, with `plugins/specflow/` untouched. Remove the temporary clones, unless step 9 follows.
9. Only on an explicit maintainer instruction, apply the adopt and adapt rulings while the clones still exist: edit the AWS references with a source line per passage (§10.2), taking A1 text from the newest release tag that holds the ruled change, and deferring the ruling when no release tag holds it yet; update the source record, and when it moves to a newer A1 tag, re-stamp every A1 source line with that tag after checking its passage against the diff between the two tags, since the release check allows one A1 tag; then run the repository tests and release-boundary verification. Until the maintainer commits, that verification reports the files just edited as unexpected changes; those errors are expected, and any other error is a failure. Then remove the temporary clones (ruling D5).

10. Leave changes uncommitted unless the maintainer separately asks for a commit.

## Error handling

| Condition | Required behavior |
|---|---|
| AWS source unreadable or only partly reviewed in a catch-up | Keep its cursor; the report says coverage is incomplete |

A license change in a source blocks adoption from it until the maintainer rules on it (step 5 of the sequence). A failed catch-up keeps its temporary clone only with an explicit diagnostic path (SEC-001 criterion 4).

## Security and privacy

- Exact configured HTTPS remotes.
- Adoption from A1 by release tag only, recorded as the commit the tag points to.
- Fresh temporary checkout outside the tracked tree, removed afterwards.
- No upstream imports, package installs, scripts, hooks, or tests.
- Upstream text is data: instructions found in it are reported, never followed.
- License-change gate.
- Review and report by default; runtime references change only on an explicit maintainer instruction.

## Testing strategy

- Every source line in an AWS reference names a source and a ref in the source record.
- Every source in the source record has a cursor row in `sources.md`, and the license of each source that text is copied from is present.
- The catch-up skill passes skill validation and is absent from `plugins/specflow/`.
- The AWS references hold no engine plumbing: `{{HARNESS_DIR}}`, `{{INVOKE}}`, `aidlc engine`, `[Answer]:`.

- Verify the source record, each source's license, and that every adopted passage names a recorded source.

Tests are named for the rule they enforce.

- `tests/specflow/release/test_sources.py`, T-010: `test_every_recorded_source_has_a_cursor_row`, `test_cursor_rows_carry_an_https_url`. That the A1 tag resolves to the recorded commit and that the A2 and A3 commits exist upstream is checked once against the network when T-010 runs, and written in its `Outcome:` line.
- `tests/specflow/release/test_verify_release.py`, T-011: `test_rejects_missing_source_record`, `test_rejects_source_record_without_a_source_row`, `test_rejects_preview_tag_in_source_record`, `test_rejects_missing_license`, `test_rejects_missing_attribution`. T-011 also extends `make_package` of 00002 with a minimal source record, `aws/LICENSE`, and a minimal `skills/spec-workflow/SKILL.md` whose body is not the shell's sentence, so the fixtures that passed before `check_sources` existed still pass: a skill folder without a `SKILL.md` fails `validate_skills`, which `check_manifests` calls.
- `tests/specflow/release/test_verify_release.py`, T-014: `test_rejects_missing_reference`, `test_rejects_reference_without_a_source_line`, `test_rejects_mistyped_source_line`, `test_rejects_source_line_naming_an_unrecorded_ref`, `test_rejects_source_line_citing_another_sources_commit`, `test_accepts_commit_prefix_of_seven_characters`, `test_rejects_parenthesised_commit_on_a_commit_only_source`, `test_accepts_prose_line_that_starts_with_the_word_source`, `test_rejects_engine_plumbing_in_a_reference`. T-014 also extends `make_package` with the four references, so the clean fixture stays clean.
- `scripts/test_validate.py`, T-018: `test_accepts_valid_maintainer_skill`, `test_rejects_malformed_maintainer_skill`, `test_skips_maintainer_skills_when_paths_are_given`. All three call `validate.main()` with `validate.ROOT` patched to a temporary tree and the arguments patched, since calling `validate_skills` directly would pass without the edit. The absence of the skill from the package is already enforced by the marker `catchup-specflow-upstream` in 00002.
- T-018 ends with the first catch-up: its report holds a ruling or a "nothing to adopt" line per source, and the cursors match it.

## Rollout and migration

T-010 picks the A1 release tag that is latest on the day it runs as the adopted-from ref, and seeds the cursors with the refs last read in full. The first catch-up (T-018) reviews from those cursors and advances them. Nothing migrates: no upstream text exists in the repository yet.

### Cadence

A catch-up runs before each specflow release and at least monthly (UPD-002.8). The monthly figure is a default from the 2026-10-03 review, not yet confirmed by use. Nothing schedules it; the release process names it as its first step (§16).

## Risks and edge cases

- An upstream change is missed between catch-ups, since A1 ships about once a week: impact m, likelihood m; mitigation: one cursor per source and a tracked ruling for every change considered; fallback: add a synchronizer when real catch-ups show a step that repeats.
- A1 moves or renames a stage file or a heading that a source line names: impact m, likelihood m; mitigation: the catch-up reads the diff of the adoption set since the cursor, so a move shows up as a change to rule on; fallback: the source line still resolves at its recorded commit.
- Likely next change, a fourth source: the source-line pattern and the record name A1 to A3 only; impact l, likelihood l; mitigation: one more row and one wider pattern; fallback: cite the new source in `adaptation.md` prose until then.
- Likely next change, a synchronizer once catch-ups repeat a step: nothing parses upstream today; impact m, likelihood m; mitigation: source lines and record rows have one fixed shape a tool can read; fallback: keep reviewing by hand.
- Likely next change, A1 restructures its stages in a major release: the adoption set is a list of paths; impact h, likelihood l; mitigation: adoption is by release tag, so nothing changes until a maintainer rules on the new tag; fallback: stay on the last adopted tag.
- Edge case: an annotated tag. The record names the commit the tag points to, not the tag object.
- Edge case: a preview tag sorts after the release it follows; `RELEASE_TAG` keeps it out of the record.

## Requirement traceability

| Design element | Criteria |
|---|---|
| Source record in `adaptation.md` | AWS-001.1, AWS-001.2, AWS-001.5, AWS-002.5 |
| Nothing vendored; references and record only | AWS-001.3, AWS-001.7 |
| `aws/LICENSE` with attribution; `check_sources` | AWS-001.4, REL-001.3 |
| No fetch at runtime (references are files in the package) | AWS-001.6 |
| AWS references: source line, profile mark, adaptation marker | AWS-002.1, AWS-002.3, AWS-002.4 |
| Catch-up skill location and visibility; the `.gitignore` entries | UPD-001.1, UPD-001.2, UPD-001.3 |
| Catch-up sequence, steps 8 to 10 | UPD-001.4, UPD-001.5, UPD-001.6 |
| Maintainer-skill convention in `AGENTS.md` and `CONTRIBUTING.md` | UPD-001.7 |
| Source cursors and their seeding | UPD-002.1, UPD-002.5, SEC-001.5 |
| Catch-up sequence, steps 3 to 7 | UPD-002.2, UPD-002.3, UPD-002.4, UPD-002.6, UPD-002.9, SEC-001.1, SEC-001.2, SEC-001.3, SEC-001.4 |
| Adoption from A1 release tags; `RELEASE_TAG` | UPD-002.7 |
| Cadence | UPD-002.8 |
| Behavior rules are separate files a catch-up never edits (AWS references, last line) | Maintainability |

## Alternatives considered

The chosen design is also the smallest diff: Markdown written by hand, one skill file with no script of its own, and one check function. Every rejected option below is larger. Tools that move a version pin (a submodule, a dependency bot) do not read a prose diff and rule on it, which is the work here; no registry search was run for one.

### Ship the catch-up skill as a second plugin skill

Rejected. It exposes maintainer-only network and source-review behavior to installed users and expands the runtime attack surface.

### Follow AWS `main` at runtime

Rejected. It is non-reproducible and permits unreviewed prompt changes to alter behavior.

### Use a Git submodule for upstream prompts

Rejected. Plugin installers may not initialize submodules, and a submodule alone does not provide semantic adaptation or review.

### Run specflow as an AWS AI-DLC plugin with a Kiro exporter

Rejected (aidlc decision #1). A1 derives artifact paths in its engine and template overrides change headings only, so it cannot write `.kiro/specs/`; on Kiro IDE its personas are denied writes under `.kiro/**`; it needs the `aidlc` binary or Bun; and its plugins can only add, never shrink A1 to three documents. `.kiro/specs/` would become a derived copy and "no runtime" would go. Evidence: `discovery/00001-specflow-aidlc-workflows.md` §4-§5.

### Retire the aws-samples sources

Rejected (decision 2026-10-03 #1, reversing aidlc decisions #1 and #8). A2 is the original source and calls itself complementary to A1, and A3 covers the discovery that A1's adopted stages do not. The earlier objection was two parsers for one source; with no parser and nothing vendored, each extra source costs one cursor row and one review per catch-up.

### Generate the references with an updater pipeline

Rejected for the first release (decision 2026-10-03 #2, reversing the earlier ruling that accepted its cost). A structural parser, adapter mappings, a normalizer, staged apply, and a shipped raw snapshot were the largest build cost in the release, blocked the runtime skill on the normalizer, and had no place for A2 or A3. The catch-up skill reads the same diffs. What is lost is a machine check that every upstream section got a ruling, and byte-reproducible references; a human reading the diff is the check. A1 ships about once a week, so the risk is a missed change, which the per-source cursor and the tracked rulings are there to limit. Add a synchronizer when real catch-ups show a step that repeats.

## Reuse inventory

- `scripts/validate.py`: `validate_skills(plugin: Path) -> int` and `ValidationError`. Passing `ROOT / ".agents"` checks the maintainer skill with the existing name, description, and containment rules; no new rule is written. The pre-pass reviewer ran this against the unmodified script: one valid skill counted, a malformed one rejected.
- `tools/specflow/verify_release.py` (00002): `main` and the error format `error: <path>: <message>`; `check_sources` joins the three checks there.
- `tests/specflow/release/test_verify_release.py` (00002): `make_package` and the fixture pattern.
- Plain `git` (`clone`, `log`, `diff`, `ls-remote`) for the catch-up; the skill has no script.
- Searches: the repository holds one code module, `scripts/validate.py`, read in full. A search for `upstream|license|source record|cursor|catch`, case-insensitive, over `scripts`, `.github`, `plugins`, and `templates` is recorded in the intake log; nothing there tracks an upstream source.

## Open decisions

No decision is open. Rulings of 2026-10-04 (design gates report), taken in above: D1, T-002 of 00002 creates a shell `SKILL.md`, so the skill folder is valid before T-010 writes into it; D5, steps 8 and 9 of the catch-up sequence are reworded, so the clones outlive the copying, adopted A1 text comes from a release tag, and the expected clean-tree errors are named; D6, step 4 diffs each source's license files; D7, text under a source line is verbatim.

Choices the source left to the design, made above and listed for approval: the fixed form of the record rows and the release-tag pattern; the attribution lines in `LICENSE`; the `URL` column and literal-path scopes in `sources.md`; cursors seeded with the refs last read in full; the `.gitignore` entries; and the one-call edit to `scripts/validate.py`.

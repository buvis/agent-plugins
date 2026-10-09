# Tasks: specflow AWS sources and catch-up

The first sub-bullets of `Details:` and `Verify:` are carried from the source plan in intake item 00001. In them, `design §n` means the source design, `.kiro/specs` means the specs folder, and a task ID may belong to another spec; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section and each task. Lines written for this plan name a task of another spec with its spec, as in `T-030 (00006)`.

- [x] T-010 Record the AWS sources
  - Requirements: AWS-001, AWS-002, UPD-002, SEC-001
  - Depends on: none
  - Location: `plugins/specflow/skills/spec-workflow/references/aws/adaptation.md`, `tools/specflow/upstream/sources.md`, `tests/specflow/release/test_sources.py`
  - Premise: `plugins/specflow/skills/spec-workflow/SKILL.md` exists as the shell T-002 (00002) wrote, so the skill folder validates while this task writes into it (ruling D1).
  - Contract: The record rows have one fixed form, so a tool can read them. An A1 release tag matches `^v\d+\.\d+\.\d+$`; a preview tag is never adopted from. The adopted-from cell of A1 holds the tag and the full commit it points to, each in backticks. The cells of A2 and A3 hold the full commit the adapted rules were read at, in backticks; nothing is adopted from A2 yet, so its cell records what was read.
  - Details:
    - Pick the `awslabs/aidlc-workflows` release tag that is latest on the day this task runs (`vX.Y.Z`, never a preview tag) and peel it to its commit (design §10.1); for A2 and A3 record the full commit the adapted rules were read at.
    - Write the source record in `aws/adaptation.md` (role, adopted-from ref, and license per source), the profile-to-depth mapping (AWS-002.5), and what is not adopted from each source (design §9.4).
    - `adaptation.md` also lists, per source, what specflow adopted and what it adapted, as the design's sections give them. Keeping A2 and A3 as sources needs no vendoring and no parser, by construction.
    - Write `tools/specflow/upstream/sources.md` with one cursor per source (design §11.2).
    - Give `sources.md` a `URL` column with each source's `https://github.com/...` remote, and literal paths in each Scope cell, with the source's license files among them (ruling D6). Seed each cursor with the ref last read in full and the date of that read: A1 `2a883858` (`v2.10.0`), A2 `3e7c0f0`, A3 `a84b289`.
    - If the picked A1 tag is newer than `v2.10.0`, diff the A1 license files between the two and write the result in the `Outcome:` line; a license change blocks adoption until the developer rules on it.
    - In the files this task writes, replace a section number of the source design by the name of what it points to.
  - Acceptance criteria: AWS-001 criteria 1, 2, 5, 7; AWS-002 criterion 5; UPD-002 criteria 1, 7; SEC-001 criterion 5
  - Verify:
    - the A1 tag resolves to the recorded commit; the A2 and A3 commits exist upstream; every source in the record has a cursor row.
    - `tests/specflow/release/test_sources.py` passes: `test_every_recorded_source_has_a_cursor_row`, `test_cursor_rows_carry_an_https_url`. The tag and commit lookups run once against the network, and their result goes in the `Outcome:` line.
    - File check: `adaptation.md` holds, per source, what was adopted, adapted, and not adopted, and maps `standard` and `quick` to the AWS depths Standard and Minimal.
  - Outcome: on 2026-10-09 `git ls-remote` gave A1's latest release tag as `v2.11.0` (annotated, tag object `4079edb`), peeling to `6a378b53c0a4fe0641ed7d8de8dfff94264d5b6a`; newer preview tags exist and were skipped. A2 HEAD is still `3e7c0f0aa2a1a084c94631edb709deae5fe0ae4f` and A3 HEAD (and `v2.0.1`) still `a84b2899d0dd518081a4764b42fde4c6dbf3cc9a`, so both recorded commits exist upstream. `v2.11.0` is newer than `v2.10.0`: A1's only license file, `LICENSE`, is the same blob (`09951d9`, MIT-0) at both tags, so no license change blocks adoption; A2 and A3 are MIT-0 as well. Every adoption-set path still exists at `v2.11.0` and none was renamed, but those files changed by about 1,800 lines since `v2.10.0`; the first catch-up (T-018) reviews that range. Cursors seeded at the last full reads: A1 `v2.10.0` on 2026-10-03, A2 on 2026-09-28 (the discovery read, which covered `all-phases/all-phases-aidlc-mcp/` only), A3 on 2026-10-03. Release tests ran 30, OK, including `test_every_recorded_source_has_a_cursor_row` and `test_cursor_rows_carry_an_https_url`; `scripts/validate.py` passes; no forbidden marker or design section number in the package.

- [x] T-011 Add license and attribution
  - Requirements: AWS-001, REL-001
  - Depends on: T-010
  - Location: `plugins/specflow/skills/spec-workflow/references/aws/LICENSE`, `plugins/specflow/README.md`, `tools/specflow/verify_release.py`, `tests/specflow/release/test_verify_release.py`
  - Reuse: `main` and the error format `error: <path>: <message>` of `tools/specflow/verify_release.py` (00002); `make_package` of `tests/specflow/release/test_verify_release.py` (00002), extended here.
  - Contract: `check_sources` joins the three checks of `tools/specflow/verify_release.py` (00002) and is called from `main` beside them.
  - Details:
    - Put the license of every source that text is copied from in `aws/LICENSE`.
    - Add provenance to plugin documentation.
    - Open `LICENSE` with one line per source that text is copied from, naming its repository, followed by that source's license text. When this task runs that source is A1; the text is A1's license file at the recorded commit. The plugin README names the three sources, by name and repository.
    - Add `check_sources` with the rules of T-011 the design lists: the record and its three rows in the fixed form, a release tag that matches `RELEASE_TAG`, a present and non-empty `LICENSE`, and an attribution line for every source the references cite. Extend `test_reports_failures_from_every_check` for it.
    - Extend `make_package` with a minimal source record, `aws/LICENSE`, and a minimal `skills/spec-workflow/SKILL.md` whose body is not the shell's sentence: a skill folder without a `SKILL.md` fails `validate_skills`, which `check_manifests` calls.
  - Acceptance criteria: AWS-001 criterion 4; REL-001 criterion 3
  - Verify:
    - release validation fails when the source record, attribution, or a license is missing.
    - The T-011 tests the design lists pass in `test_verify_release.py`, and the fixtures that passed before `check_sources` existed still pass. File check: the plugin README names the three sources. After the commit, `python3 tools/specflow/verify_release.py` prints `Verified plugins/specflow.` on the real package.
  - Outcome: release tests ran 36, OK, on Python 3.14 and 3.10: the five T-011 tests the design lists, `test_clean_fixture_has_no_source_errors`, and `test_reports_failures_from_every_check` extended with a missing `LICENSE`; every fixture that passed before `check_sources` still passes with the extended `make_package`. `scripts/validate.py` passes. After the commit the tool printed `Verified plugins/specflow.` on the real package. `LICENSE` opens with the A1 attribution line and A1's `LICENSE` text; no reference cites A2 or A3 yet, so theirs are not included. The plugin README names the three sources by name and repository. Simplification: an attribution line counts when the source's repository appears anywhere in `LICENSE`, not only in its opening lines.

- [x] T-014 Adapt the AWS references by hand
  - Requirements: AWS-001, AWS-002, REL-001
  - Depends on: T-010, T-011
  - Location: `plugins/specflow/skills/spec-workflow/references/aws/requirements.md`, `plugins/specflow/skills/spec-workflow/references/aws/design.md`, `plugins/specflow/skills/spec-workflow/references/aws/implementation.md`, `plugins/specflow/skills/spec-workflow/references/aws/verification.md`, `tools/specflow/verify_release.py`, `tests/specflow/release/test_verify_release.py`, `plugins/specflow/skills/spec-workflow/references/aws/LICENSE`
  - Reuse: `make_package` (00002), extended with four minimal references, each with one valid source line.
  - Contract: By the developer's ruling of 2026-10-04 (D7), the text under a source line is verbatim: cuts are shown as `[...]`, and the passage ends at the next `Adaptation:` line, source line, or heading.
  - Details:
    - Write `aws/{requirements,design,implementation,verification}.md` from the A1 adoption set (design §10.1), each adopted passage under a source line with its profile mark, and each local line marked as adaptation (design §10.2).
    - Leave engine plumbing out (design §9.4).
    - Reworded upstream method goes on `Adaptation:` lines under the source line it came from; engine plumbing is cut, not reworded. The references are files in the package, so nothing fetches upstream at runtime, by construction. If a reference cites A2 or A3, add that source's attribution line and license text to `aws/LICENSE`.
    - Add the rules of T-014 to `check_sources`, for the four references only: a missing reference or one with no source line, a mistyped source line, a ref that is not in the record, and any `ENGINE_PLUMBING` string.
    - In the files this task writes, replace a section number of the source design by the name of what it points to.
  - Acceptance criteria: AWS-001 criteria 3, 6; AWS-002 criteria 1, 3, 4; REL-001 criterion 3
  - Verify:
    - every source line names a source and ref in the source record; no reference contains `{{HARNESS_DIR}}`, `{{INVOKE}}`, `aidlc engine`, or `[Answer]:`.
    - The T-014 tests the design lists pass in `test_verify_release.py`, and the clean fixture stays clean. After the commit, `python3 tools/specflow/verify_release.py` prints `Verified plugins/specflow.` on the real package.
    - No check compares a passage with upstream, so compare each passage with its source at the recorded ref once, by hand, and write the result in the `Outcome:` line.
  - Outcome: the four references hold 45 source lines, all A1 at `v2.11.0 (6a378b5)` (requirements 16, design 11, implementation 11, verification 7), with `[standard]`, `[quick]`, and `[both]` marks; every local line is an `Adaptation:` line. Text was taken from `requirements-analysis.md`, `domain-design.md`, `units-generation.md`, `code-generation.md`, `build-and-test.md`, and `stage-protocol.md` (`3. Question Format`, `8. Depth Guidance`); `core/scopes/` and `docs/guide/05-scopes-and-depth.md` informed the profile mapping and gave no passage. No reference cites A2 or A3, so `LICENSE` is unchanged. Comparison with upstream: a throwaway script split each passage at its `[...]` cuts and found every piece, whitespace aside, in the source file at `v2.11.0`: 0 mismatches; a control copy with one word changed was flagged. That check is mechanical; I did not read every passage against upstream line by line a second time. `rg` finds no `{{HARNESS_DIR}}`, `{{INVOKE}}`, `aidlc engine`, or `[Answer]:` in the four references (the same search finds them in `adaptation.md`, which names them on purpose). Release tests ran 45, OK, on Python 3.14 and 3.10, including the nine T-014 tests the design lists; the clean fixture stays clean with its four references. After the commit the tool printed `Verified plugins/specflow.` on the real package.

- [ ] T-018 Create the repository-only catch-up skill
  - Requirements: UPD-001, UPD-002, SEC-001
  - Depends on: T-010
  - Location: `.agents/skills/catchup-specflow-upstream/SKILL.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.gitignore`, `scripts/validate.py`, `scripts/test_validate.py`, `docs/dev/project-management/reviews/YYYY-MM-DD-specflow-upstream-catchup.md`, `tools/specflow/upstream/sources.md`
  - Reuse: `validate_skills(plugin: Path) -> int` and `ValidationError` of `scripts/validate.py`: passing `ROOT / ".agents"` checks the maintainer skill with the existing rules. Plain `git` (`clone`, `log`, `diff`, `ls-remote`); the skill has no script.
  - Contract: 8. The default run ends here: review and report, with `plugins/specflow/` untouched. Remove the temporary clones, unless step 9 follows.
  - Details:
    - Add `.agents/skills/catchup-specflow-upstream/SKILL.md` with the sequence of design §11.3: review and report by default, edits to runtime references only on explicit instruction, no commit.
    - Write the ten steps as the design's Catch-up sequence gives them, with the rulings of 2026-10-04: step 4 also diffs each source's license files (D6); steps 8 and 9 keep the clones until any copying is done, take A1 text from a release tag, re-stamp every A1 source line when the record moves to a newer tag, and name the clean-tree errors to expect (D5). The skill states the cadence (before each release and at least monthly) and installs no scheduler.
    - State the maintainer-skill convention in `AGENTS.md` and `CONTRIBUTING.md` (UPD-001.7), and make `scripts/validate.py` check `.agents/skills/*/SKILL.md` with its existing skill rules.
    - Add `/.claude/`, `/.kiro/`, and `/.codex/` to `.gitignore`, so a local projection of the skill is never committed. The edit to `scripts/validate.py` is the one call the design shows, made only on a default run with no path argument.
    - Run the first catch-up over A1, A2, and A3 and write its report under `docs/dev/project-management/reviews/`.
    - Order inside the task: the validator edit and its tests, the skill, the convention text and ignore rules, and the first run last. The run advances the cursors in `tools/specflow/upstream/sources.md`. The task stays unchecked, or takes an `Exception:`, until all three sources are fully reviewed.
    - In the files this task writes, replace a section number of the source design by the name of what it points to.
  - Acceptance criteria: UPD-001 criteria 1, 2, 3, 4, 5, 6, 7; UPD-002 criteria 2, 3, 4, 5, 6, 8, 9; SEC-001 criteria 1, 2, 3, 4
  - Risk: The edit to `scripts/validate.py` runs in every package's CI. Mitigation from the design: one call, guarded by `not args.paths` and by the folder existing, with three tests that call `validate.main()`.
  - Verify:
    - the validator passes on the skill and fails on a seeded malformed one; release-boundary tests prove the skill is absent from `plugins/specflow/`; the first report holds a ruling or a "nothing to adopt" line per source, and the cursors match it.
    - `scripts/test_validate.py` passes with `test_accepts_valid_maintainer_skill`, `test_rejects_malformed_maintainer_skill`, and `test_skips_maintainer_skills_when_paths_are_given`. The skill's absence from the package is enforced by the marker `catchup-specflow-upstream` of 00002.
    - `git check-ignore .claude/x .kiro/x .codex/x` prints all three paths. File checks: `AGENTS.md` and `CONTRIBUTING.md` state the maintainer-skill convention; the skill states the cadence and names no scheduler. The `Outcome:` line notes, for the first run, that `plugins/specflow/` was untouched and the temporary clones are gone.

## Completion criteria

- [ ] Every task above is checked, each with its `Outcome:` line.
- [ ] On the final commit, the pull request's CI run is green (before a pull request exists, the step commands pass in a fresh clone of the commit): the repository validator with the maintainer-skill check, the release tests, and the release check with `check_sources`.
- [ ] The first catch-up report is under `docs/dev/project-management/reviews/`, with a ruling or a "nothing to adopt" line per source, and the cursors in `tools/specflow/upstream/sources.md` match it.

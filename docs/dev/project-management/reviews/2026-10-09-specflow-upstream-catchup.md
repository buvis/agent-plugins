# specflow upstream catch-up 2026-10-09

The first catch-up, run as the last step of T-018 (spec 00003) with `.agents/skills/catchup-specflow-upstream/SKILL.md`. Default run: review and report; `plugins/specflow/` was not edited by it. Clones were bare, in a fresh temporary folder outside the repository, and nothing in them was run.

No earlier report exists, so no deferred ruling was carried in.

How the review was done: the A1 range `v2.10.0..v2.11.0` (24 files in scope, +921/-559) was read in full by a delegated reviewer that drafted the theme rulings below; I checked its main claims against the source (`intent-capture.md:135`, `stage-protocol.md:390` and `:616`, the input-file exclusion list) and made the final rulings. I read the unreleased range `v2.11.0..b8d9bdc` (5 files, +80/-29) in full myself. Commit citations per theme come from commit subjects and per-file logs and may be loose; the file and heading are the evidence.

## A1 awslabs/aidlc-workflows

- Range: `2a883858f5483bce3b48f43b8f6d3ca2c042d6ae` (`v2.10.0`) to `b8d9bdc3a197967a405ba221421b63b4028077e6` (main; newest release tag `v2.11.0`, newer preview tags exist).
- Coverage: complete for the scope in `tools/specflow/upstream/sources.md`. `domain-design.md` and `LICENSE` have no changes in range.
- License files: unchanged (`LICENSE` is blob `09951d9`, MIT-0, at the cursor and at head).
- Instructions found in upstream text: ordinary operating instructions for A1's own agent, such as `**SAY:** "[the selection_note, word for word]"`, "run it yourself" for `doctor`, and the plan-approval override procedure. None is aimed at this review, and none was followed.
- Context: the four phase references were copied at `v2.11.0` (T-014), so changes up to that tag in passages they quote are already in them. Changes after `v2.11.0` are unreleased and cannot be adopted until a release tag holds them.

### Released changes, `v2.10.0..v2.11.0`

| Change | Evidence | Ruling | Local impact | Upkeep cost |
|---|---|---|---|---|
| Corner-case sweep in requirements: cross each component with the conditions it touches; carry each as a criterion, an assumption, or out of scope | `stages/inception/requirements-analysis.md` Step 5 (63541bc5) | adapt: already reflected at `v2.11.0` | `requirements.md` adaptation line under Step 5 | low |
| A choice left to the agent: the agent decides and says so in one line | `protocols/stage-protocol.md` 3. Question Format > Overconfidence prevention | adapt: already reflected at `v2.11.0` | `requirements.md` adaptation line | low |
| Never re-ask an answered question; answers kept on resume | `stage-protocol.md` 3. Question Format | adapt: already reflected (method); the engine side is plumbing | `requirements.md` "read the intake log" line | low |
| Reading the person's reply at a checkpoint; feedback already given is used without asking again; approval and a change in one reply | `stage-protocol.md` top section, 2. Completion Messages (line 390), 3. Question Format (line 616) | defer: the target is the approval phase of the runtime skill (00006). A1 records the approval and then makes the change, which would make specflow's approval stale at once; A1's plan approval does the change first. Needs a developer ruling when 00006 writes the approval phase | none now | medium |
| The confirmation summary sits in the same message as its question | `stage-protocol.md` 3. Question Format > Step 3a | defer: strengthens the playback rule (ART-002.18), which lands in 00006 | none now | low |
| Plain words: record-keeping words and silent bookkeeping never reach the person | `stage-protocol.md` voice contract | defer: strengthens ART-002.17 (00006); add receipt, fingerprint, hash to the words never shown | none now | low |
| Boundary question: "what this first version leaves out", never "is the scope right" | `stages/ideation/intent-capture.md` (line 135) | defer: an intake question hint for 00006; strengthens ART-002.15 | none now | low |
| Input files: lookup by name, one match read with a note, several offered as a pick; never git-ignored files, symlinks, `.env`, `*.pem`, `*.key`, `id_*` | `requirements-analysis.md` Step 1, `intent-capture.md` | reject the name lookup (INT-001.8 keeps one explicit path); defer the exclusion list for 00006's input-file rule | none now | low |
| Project type: the person's word beats the scan; ask once when an empty folder gains code | `stages/initialization/workspace-detection.md`, `stages/inception/reverse-engineering.md` | adapt: already consistent with WF-003.15; the re-check when code appears is deferred to 00006 | none now | low |
| Scan only what people wrote: follow `.gitignore`, skip build output unopened; coverage lists read, skimmed, and left out | `reverse-engineering.md`, `workspace-detection.md` | adapt: already consistent with WF-003.15 and WF-003.16 | none | low |
| Answer mode asked once per piece of work; numbered pick lists; the "Other" label per tool | `stage-protocol.md` 3. Question Format > Step 2, Step 3a | reject: answer modes and batching are not adopted | none | low |
| Engine-owned gates, progress lines, audit trail rewrite, clock, shell quoting, pasted-document split | `stage-protocol.md` 2, 4, 5; `state-init.md`; `workspace-*.md` | reject: engine plumbing | none | low |
| Plan approval moved into the engine, edit mode, go back to the approved plan, plan approval can be off | `stages/construction/code-generation.md` Step 3 | reject: engine plumbing | none; the quoted Critical Rules bullets are unchanged | low |
| Plan summary of three lines (Builds, Touches, Tests) | `code-generation.md` Step 2 | defer: an idea for the `tasks.md` approval summary in 00006 | none now | low |
| Interrupted build resumes at the first unticked step | `code-generation.md` Step 4 | adapt: already consistent (tasks resume at the first unchecked task) | none | low |
| Review after the build, source manifest, sensors dropped from code generation, loop-back reopens only named Units | `code-generation.md`, `stages/construction/build-and-test.md` Step 9 | reject: plumbing; Units and loop-back are not adopted | none | low |
| Units: story map keyed by FR without stories; the engine reads the edge block | `stages/inception/units-generation.md` Step 5 | reject: unit files are not adopted | none | low |
| Nested repositories all named | `workspace-detection.md` | reject: multi-repo work is not adopted | none | low |
| Practices: collaborators optional; Methodology a single value | `stages/inception/practices-discovery.md` | reject the collaborators change (plumbing); defer the single value, since specflow stores no methodology enum yet | none | low |
| Scopes: Guard Policy defaults to `off` except enterprise; new `plan_approval`, `collaborators`, `existing_code` keys; bugfix drops learnings and summary confirmation | `core/scopes/*.md`, `docs/guide/05-scopes-and-depth.md` | reject: scope names are not profiles and Guard Policy is not adopted; the stage-by-scope membership is unchanged | none | low |
| Release notes for `v2.11.0` | `CHANGELOG.md` | reject: their method items are the rows above; the rest is install, harness, and engine | none | low |

### Unreleased changes, `v2.11.0..b8d9bdc`

| Change | Evidence | Ruling | Local impact | Upkeep cost |
|---|---|---|---|---|
| The code summary lists tests written but not executed, each with the reason | `code-generation.md` Step 5 | defer: no release tag holds it yet. Adopt from the first release that does: it extends the Step 5 passage in `implementation.md` | `implementation.md`, Record what was done | low |
| A CI obligation applies only when the plan runs CI Pipeline | `code-generation.md` Step 2, `build-and-test.md` Step 1 and 8 | reject: specflow quotes neither the coverage floor nor the CI line | none | low |
| A gate never claims coverage a failing check reports against | `stage-protocol.md` 14. Sensor Imports | reject: sensor plumbing; the principle is already in `verification.md` | none | low |
| Logging with message ids, questions resumed as written, the `ambiguous` answer set, open-decisions block on the gate row | `stage-protocol.md` 2, 3, 5 | reject: engine plumbing | none | low |
| Plan approval: an answer in the file counts, restore offers, a stale contract re-rendered, interrupted build with no ticks | `code-generation.md` Step 3, Step 4 | reject: engine plumbing | none | low |
| Approval gates name the next stage from the engine; Unit directory names | `stages/ideation/approval-handoff.md`, `units-generation.md` | reject: engine plumbing | none | low |

Nothing to adopt now: every method change in the released range is already reflected or depends on runtime rules that 00006 writes, and the one adoptable unreleased change waits for a release tag.

## A2 aws-samples/sample-ai-powered-sdlc-patterns-with-aws

- Range: `3e7c0f0aa2a1a084c94631edb709deae5fe0ae4f` to the same commit; the repository has no new commits.
- Coverage: incomplete. No commits since the cursor, but the cursor Scope's wider catalog has never been read against specflow; only `all-phases/all-phases-aidlc-mcp/` was read (2026-09-28). The cursor keeps its commit and its 2026-09-28 date until a catch-up reads the catalog (corrected after review 00003-aws-sources-catchup-review-01, R1).
- License files: unchanged.
- Instructions found in upstream text: none read; no diff.

Nothing to adopt.

## A3 aws-samples/sample-aidlc-discovery

- Range: `a84b2899d0dd518081a4764b42fde4c6dbf3cc9a` (`v2.0.1`) to the same commit; no new commits or tags.
- Coverage: complete.
- License files: unchanged.
- Instructions found in upstream text: none read; no diff.

Nothing to adopt.

## Deferred rulings for the next catch-up

1. Approval and a change in one reply: which order, and whether "approve but X" approves the result of X without showing it again (needs a developer ruling; 00006).
2. Feedback already given counts; the confirmation summary on screen with its question (00006).
3. Plain words: receipt, fingerprint, hash among the words never shown (00006).
4. Boundary question wording (00006 intake).
5. The input-file exclusion list (00006, INT-001.8).
6. Re-check the project type when an empty folder gains code (00006, WF-003.15).
7. Plan summary of three lines for the `tasks.md` approval (00006).
8. Methodology as a single value (when specflow stores one).
9. Tests written but not executed, in the code summary passage of `implementation.md` (unreleased at `b8d9bdc`; adopt from the first release tag that holds it).

## Cursors

- A1: from `2a883858f5483bce3b48f43b8f6d3ca2c042d6ae` (`v2.10.0`, 2026-10-03) to `b8d9bdc3a197967a405ba221421b63b4028077e6` (main after `v2.11.0`, 2026-10-09).
- A2: stays at `3e7c0f0aa2a1a084c94631edb709deae5fe0ae4f`; review date to 2026-10-09.
- A3: stays at `a84b2899d0dd518081a4764b42fde4c6dbf3cc9a`; review date to 2026-10-09.

Read /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/review-context-ap00012-c2.md for review context, and /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/review-diff-ap00012-c2.diff for the full diff.

Read /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/engram-pack-ap00012-c2.md and treat its full content as prepended context: similar code, reuse precedent, findings precedent, and task prose for this diff's changed symbols.

Use this review checklist:
# Review Dimensions

Detailed checklist for reviewing completed work.

## Plan Compliance

- [ ] Implementation matches task description
- [ ] All acceptance criteria met
- [ ] No scope creep (extra features not requested)
- [ ] No missing pieces from original task

## PRD Coverage

- [ ] All "must have" requirements addressed
- [ ] Success metrics achievable with implementation
- [ ] No PRD sections left unimplemented
- [ ] Dependencies correctly handled

## Simplification

Hunt actively for simplification — do not just tick boxes. The diff under
review is fresh; this is the cheapest moment to cut complexity before it sets.
For every added or changed file, ask "what would make this simpler to read
without changing what it does?" and flag concrete opportunities.

- [ ] **Reduce complexity** — no needless indirection, dead branches, or
      abstractions built for a single caller; nesting <= 4 levels; functions
      under 50 lines
- [ ] **Eliminate redundancy** — no logic duplicated within the diff or against
      existing code; no helper that reimplements a stdlib or existing utility
- [ ] **Improve naming** — names state intent; no opaque abbreviations;
      action-named functions start with a verb
- [ ] **Follow project standards** — conventions from CLAUDE.md / AGENTS.md and
      the surrounding code; no style drift
- [ ] **No dead code** — no commented-out blocks, unused imports, variables, or
      speculatively-added parameters
- [ ] **Appropriate error handling** — explicit, never silently swallowed

**How to flag a simplification:** give the file:line, the current shape, and
the simpler replacement. Flag concrete behavior-preserving simplifications at
🟡 Medium so the decision gate routes them into the rework loop. Do not inflate
them to 🟠 High; that floods the rework loop and can trip the scope alarm.

**Balance — do not over-simplify:** never propose a change that trades clarity
for brevity, drops error handling, collapses a deliberate boundary, or removes
a documented invariant. Simpler means easier to read and maintain, not shorter
at any cost. If a "simplification" would change behavior, it is out of scope —
do not flag it.

## Testing

- [ ] Unit tests for new logic
- [ ] Edge cases covered
- [ ] Error paths tested
- [ ] Integration tests if crossing boundaries
- [ ] Tests actually run and pass
- [ ] No tautological test — every new or changed test fails against the
      pre-change code (the context's fail-first replay block), and no assert
      is constant, self-comparing, or an either-or hedge (the shapes block)

## Security

- [ ] No hardcoded secrets
- [ ] Input validation at boundaries
- [ ] No SQL/command injection risks
- [ ] Auth/authz correctly applied
- [ ] Sensitive data not logged

## Documentation

- [ ] Public APIs documented
- [ ] Complex logic has comments
- [ ] README updated if needed
- [ ] Breaking changes noted

In addition, work through the numbered rubric:
# Review-Work-Completion Rubric

This rubric defines binary pass/fail criteria for consensus review of completed work. Each rule is numbered and stable for tracking coverage. Reviewers must answer "R{n}: pass|fail" for every rule in their prompt.

## Rules

### Tests

R1: Tests cover every new behavior introduced by the diff.
R2: Tests bind to intent, not just observable behavior; no new or changed test is tautological (passes against the pre-change code, or cannot fail as written).
R3: No skipped or xfail tests mask failures.

### Integration

R4: Changed components integrate with existing callers.

### Security

R6: No hardcoded secrets in the codebase.
R7: All user input is validated and sanitized.
R8: No injection-unsafe queries or commands.

### Domain

R9: Implementation matches PRD feature behavior exactly.
R10: Error handling is explicit and not swallowed.
R11: No debug statements, TODOs, or placeholder markers remain.

### Code Quality

R12: Function sizes respect the 50-line limit.
R13: File sizes respect the 800-line limit.

Review the completed work against PRD requirements. Explore the codebase as needed.

OUTPUT FORMAT IS MANDATORY. Follow exactly:
## Agent Output Format (Single Source of Truth)

Each agent outputs issues in this exact format:

```
[{AGENT_NAME}] {emoji} {description} | File: {path or "N/A"} | Task: {id or "general"}
```

**Severity emojis:** 🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Low

**Rules:**
- One issue per line
- Use "N/A" for file if issue is architectural/cross-cutting
- Use "general" for task if issue spans multiple tasks or is a PRD gap
- If zero issues found: `[{AGENT_NAME}] ✅ No issues found`

**Examples:**
```
[ALICE] 🔴 SQL injection in query builder | File: src/db/query.ts | Task: 3
[BOB] 🟠 Missing error handling strategy | File: N/A | Task: general
[CARL] 🟡 PRD section 2.3 not implemented | File: N/A | Task: 5
```

Your agent name is BOB.

PER-RULE VERDICTS ARE MANDATORY. For every rule in the numbered rubric, emit one line:
R{n}: pass   or   R{n}: fail
(one rule per line, no other text on the line, no rationale).

## Sandbox Constraints

You run in a read-only sandbox. Read files with read-only shell commands (`cat`, `sed -n`, `rg`, `ls`); that is how you open /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/review-context-ap00012-c2.md, /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/review-diff-ap00012-c2.diff, /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/engram-pack-ap00012-c2.md and any source file. You CANNOT execute code, tests, linters, or package managers, and you cannot write.

Perform STATIC analysis only:
- Read code for logical correctness, patterns, naming, structure
- Check for missing imports, dead code, type mismatches
- Review against PRD requirements by reading, not executing
- Trace data flow and control flow by reading source

If a criterion requires runtime verification (e.g. "tests pass", "linter clean"), output:
[BOB] ⚪ Cannot statically verify: {criterion description} | File: N/A | Task: {id}

Do NOT run tests, linters, builds, or package managers. Do NOT report failures from blocked execution. Never report an inability to read a file you were told to read: read it with `cat`.

## Two lenses, applied to every changed file

Treat - findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00003-aws-sources-catchup-review-01.md
  - Bob: ✅ Available (codex, after one format retry, see his section)

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-01.md
  Standalone run (no autopilot `state.json`, no wip PRD). As in 00003, the review target was spec 00004's `requirements.md`, with `design.md` attached as the design doc and `tasks.md` as the task source. The reviewed tasks were T-020 to T-026, T-028 and T-029, all checked. T-027 is a known open item: its capture is partial. Findings are written here as walkthrough packets for the developer. None was applied, and no tasks were created.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-06.md
  This is a standalone run, cycle 6. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-5 rework incrementally (`8cee2d8..14afdff`: the fix commit `24919c4`, the T-027 close-out `183380c` and `363778b`, the re-approvals, the cycle-5 minutes, and two commits that touch spec 00008 docs only). The target is spec 00004's `requirements.md`, with `design.md` as the design doc and `tasks.md` as the task source. All ten tasks are now complete (T-027 closed on 2026-10-12). Findings are reported here, not written as tasks.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-10.md
  Commit `6c8f842`.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00005-behavior-rules-review-01.md
  Diff range: `392098d9f6a154dfa8e6f4a0daa64d4c0b734900..641d325de8eac75ecfb03eed26ade435db984ea5`

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00005-behavior-rules-review-01.md
  - `CHANGELOG.md` gains two lines under Fixed: the root-level and `$HOME/` path warning, and one blocker per open marker in `status`.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00006-runtime-skill-review-01.md
  - Bob: ✅ Available (codex, after one retry (inlined)). His first run refused for lack of input, as in every 00004 and 00005 cycle: his `cat` of the context file was blocked by the Fact-Forcing Gate PreToolUse hook, and his own line cites `sandbox_apply: Operation not permitted`. The output had one `[BOB] ⚪ Cannot verify review criteria` line and every `R{n}` set to fail. That is the refusal shape in substance, though not the literal `Cannot statically verify` pattern, so the one retry used the inlined prompt (773 KB: context, diff, and the persona with the two edits). The first output is kept at `docs/dev/tmp/bob-output-00006c1-first.txt`. His retry put a `- ` bullet before each `[BOB]` line, so consolidation read a stripped copy (`bob-output-00006c1-lines.txt`). The `codex_thread_id` above belongs to the retry.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00007-reviews-and-conversion-review-01.md
  Diff range: `15ce4fdfe713..e735c9bbeb7bd77eac82c6c52714bcb7f188b24d`

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00007-reviews-and-conversion-review-02.md
  Diff range: `e735c9bbeb7bd77eac82c6c52714bcb7f188b24d..4d8609fa292cacc1f35c674fbac779dbb64f840b`

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00007-reviews-and-conversion-review-02.md
  - Bob: ✅ Available (codex, first run, on the inlined 218 KB prompt with `--resume-thread 01a152e7-76ed-73d2-ab7d-5b6587be96da`; no refusal). His `[BOB]` lines carry no bullet. as findings precedent already recorded for this diff's changed symbols. Weigh it when applying both lenses and the rubric verdicts rather than re-litigating known prior findings.

### 1. Doubt lens (correctness)
Surface residual findings a confident reviewer would wave past:
- spec gaps: PRD says X, code does Y (wrong field names, enum values,
  thresholds, artifact kind);
- missing or incomplete features the PRD requires;
- edge cases, error paths, and failure modes left unhandled;
- tests that cannot fail: they assert the implementation rather than the intent,
  or still pass against the pre-change code (the caller's mechanical test checks
  list every one it found; each is behavior left unpinned).

### 2. De-slop lens (quality)
Flag slop introduced by the changes (do not propose broad refactors):
- over-abstraction / single-caller indirection with no current testability or
  architectural need;
- dead code, code kept in comments, unreachable branches;
- defensive guards for states that cannot occur;
- restating docstrings, "robust" error messages with no context, premature
  configuration, framework-verification tests;
- speculative generality (parameters, hooks, or layers nothing uses yet).
Bias: aggressive on newly-created files (slop concentrates there), conservative
on lightly-touched files (do not destabilize existing behavior).

## Categorize every residual finding

Place EACH finding in exactly one bucket:
- **FIX** — genuinely fixable now: bounded scope, in-scope, actionable.
- **VERIFY** — needs a specific named check to resolve (state the exact check,
  not "look into X").
- **KNOWN** — a real limitation that is out of scope; include a one-line written
  justification.

Output the buckets as three sections, one finding per line:

```
FIX:
- <finding> — <file:line> — <the concrete fix>
VERIFY:
- <finding> — <the exact check to run>
KNOWN:
- <finding> — <why it is out of scope>
```

If a bucket is empty, write the header and `- (none)`.

## Rubric verdicts (REQUIRED — emit verbatim, one per line)

Apply the doubt-review rubric. A rule you cannot evaluate is `fail`; never omit
a line.
- D1: every residual finding is in exactly one of FIX/VERIFY/KNOWN.
- D2: all FIX items are genuinely fixable now (bounded, in-scope, actionable).
- D3: all VERIFY items name the exact check needed (not vague).
- D4: all KNOWN items carry a written out-of-scope justification.
- D5: input finding count equals FIX + VERIFY + KNOWN counts.

Emit exactly:

```
D1: pass|fail
D2: pass|fail
D3: pass|fail
D4: pass|fail
D5: pass|fail
```

Do not modify any files. This is a review only — produce findings and the
rubric verdict lines. No commits.

Cite files repo-relative as path:line (for example skills/work/SKILL.md:166), never absolute and never with a "(lines a-b)" suffix.

## Settled decisions — do not re-raise

> These calls were already made in an earlier cycle of this same review, with
> the reasons given. Do not re-raise them. Raise a NEW finding only if you can
> show the settled reason no longer holds.

- [discarded] medium: `plugins/autopilot/scripts/autopilot.py:41` re-walks the parsed policy by hand (lines 41-49) to find floats. Passing `parse_float` and `parse_constant` hooks that raise `ValueError` to the `json.loads` call at line 36 rejects fractions, exponents and NaN/Infinity while parsing. The behavior is the same, the 9-line loop goes away, and the existing `except ValueError` already turns the error into exit 1. (plugins/autopilot/scripts/autopilot.py:41) - reason: single-voice; the existing bounded walk is correct and the proposed parser-hook refactor changes no specified behavior.
- [discarded] medium: All 27 behavior rows assigned to 00012 (P03–P05, R01, OPT-042, BEH-001..010, UTIL-*) still show evidence status "planned" with null artifact, sha and revision, and their acceptance cases are "planned". Nothing in the map links this PRD's own obligations to the contracts and tests it delivered, while asset rows carry "passed" receipts (tools/autopilot/source-map.json) - reason: Discard: the contract explicitly says AP00012 validates completeness of assignments, not completion of future work. Planned behavior/profile evidence must not be upgraded to host certification from delivery tests.
- [discarded] medium: No test checks the policy's rule IDs against the packaged rubric files. The design says to "parse the rule ids from the packaged … rubric.md … and require them to equal rule_ids" and to require that `eve.md` has the de-slop section. Instead, the R, B and D lists are hardcoded constants (`test_contract.py:28-30`), so a wrong list would still pass. The committed data is correct today: it matches R1-R4, R6-R13, B1-B19 and D1-D5 in the packaged files. (tests/autopilot/test_contract.py:121) - reason: single-voice; the current policy IDs are correct. Missing dynamic rubric-file comparison is retained as a test-coverage limitation, not silently claimed fixed.
- [discarded] low: `tests/autopilot/test_package.py:203` checks six CHANGELOG bullets word for word, so rewording the changelog breaks a test. The CHANGELOG bytes are already pinned by `destination_blob_sha256` in `test_content_roster` (`tests/autopilot/test_package.py:281`), so this check repeats one that exists and only adds a dependency on the wording. A check for the `## [Unreleased]` / `### Added` structure would be enough. (tests/autopilot/test_package.py:203) - reason: Discard: the immutable pre-integration history check independently prevents coordinated metadata/history erasure, a proved Devon exploit. Removing it would weaken required test intent.
- [discarded] low: `tools/autopilot/check-source.py:244` has three blank lines between `_audit_behaviors` and `_audit_regressions`. PEP 8 uses two (pycodestyle E303). (tools/autopilot/check-source.py:244) - reason: single-voice; whitespace-only suggestion.
- [discarded] low: `tests/autopilot/test_package.py:69` builds its target from `git archive HEAD`. A local run with uncommitted edits therefore tests the last commit, not the working tree, and can pass on stale bytes. The design asks for this ("committed target inputs"), but neither the module docstring nor the README's Development section says so. (tests/autopilot/test_package.py:69) - reason: Discard: the module docstring explicitly says Committed target packages; archive HEAD is the specified target-only contract, not an accidental stale-working-tree test.
- [discarded] low: Four named acceptance scenarios have no test of that name: source_inventory_mapping, review_schema, reference_tree_preserved and package_self_contained. Tests under other names cover them (tests/autopilot/test_provenance.py:49, tests/autopilot/test_contract_semantics.py:299, tests/autopilot/test_package.py:286, tests/autopilot/test_package.py:371). The exit criterion "the named task tests pass" can only be checked by hand-mapping (tests/autopilot/test_package.py:286) - reason: Discard: named acceptance scenarios are covered by the cited behavior tests. No contract requires Python function names to equal scenario labels.
- [discarded] low: The oracle rejects a review when an activated conditional reviewer (Carl) fails its last attempt (`required_job_failed`). The pinned retry policy says to mark the reviewer unavailable and continue (plugins/autopilot/skills/review-work-completion/references/retry-policy.md:9), and the policy encodes `reviewer_failed_after_retry → mark_unavailable`. Rejecting is right for mandatory jobs but stricter than the source for optional Carl, and no golden case covers that path (tests/autopilot/test_contract_semantics.py:171) - reason: Discard: activated required jobs must produce complete evidence; unavailable remains incomplete for a promised profile. Source retry/unavailability history is preserved separately. AP00020 owns actual runtime provenance.
- [discarded] low: The README and CHANGELOG "passed" delivery receipts point at themselves: the artifact is the file itself, and the test checks `tested_package_revision` only with a regex. The receipt proves nothing beyond the file's hash (tests/autopilot/test_package.py:122) - reason: Discard: these are delivery-only file/hash receipts, explicitly not execution certification. The build independently checked real Git revisions; self-contained artifact identity is not a claim of independent runtime proof.
- [discarded] low: prerequisites.py counts only regular `NNNNN-<slug>.md` files, but the backlog `eligibility:` lines use `ls done/NNNNN-*`. The "maintainer view of the same table" can disagree with selection, for example on `00012-x.md.bak` (tools/autopilot/prerequisites.py:35) - reason: Discard: completed PRDs are regular NNNNN-slug.md files by contract; backup files are not completion. The strict diagnostic intentionally refuses unrelated backups.
- [discarded] low: `doubt_label_map` ships in the portable policy, but it comes from the author's personal global AGENTS.md, not the pinned source, and has no source binding. It is author-home content inside a package meant to work without the author (plugins/autopilot/contracts/review-policy-v1.json:594) - reason: Discard: the reviewed design explicitly specifies doubt_label_map. Committed policy data has no author-home runtime dependency; no forbidden live home read occurs.
- [discarded] low: `check-source.py` never reads `review-policy-v1.json`. The design says it recomputes the binding and anchor digests from the pinned blobs. Coverage holds only through two checks that must both run: normal tests compare policy to inventory, and the audit compares inventory to blobs. (tools/autopilot/check-source.py:263) - reason: single-voice; the two passing checks provide transitive digest coverage. A direct policy read in the source auditor remains a coverage improvement, not a currently incorrect binding.
- [discarded] low: `test_rejected_cases_have_exactly_the_specified_complete_semantic_defects` repeats `test_contract_semantics.py:299` for the rejected cases, and `test_package.py:406` runs the same oracle a third time. Lines 63-94 also re-check properties that the `validate_review == accepted` assert at line 42 already enforces. (tests/autopilot/test_contract_fixtures_adversarial.py:96) - reason: Discard: independent mutation/adversarial and isolated-archive assertions preserve committed specification intent. Do not remove tests merely because their golden-case oracle overlaps.
- [discarded] low: `ci_autopilot_wired` asserts the exact list of steps in the unrelated `plugins` job. The design says not to snapshot unrelated workflow content, and any future specflow CI step will fail the autopilot suite. An ordered-subsequence check would still prove the job is preserved. (tests/autopilot/test_package.py:444) - reason: single-voice; the exact unrelated-job step snapshot is a genuine maintenance limitation retained in the ledger. The current workflow is correct.
- [discarded] low: The draft 2020-12 `"type":"integer"` accepts `1.0`, so `attempt: 1.0` passes the schema. The oracle's `range(1, highest + 1)` would then likely raise TypeError instead of returning a defect. The wire test covers 1.5 but not 1.0. (tests/autopilot/test_contract_semantics.py:160) - reason: single-voice; confirmed by coordinator: full-clean input.reviewer_results[0].attempt=1.0 raises TypeError at history_defects line160. The canonical gate forbids single-voice medium/low fix tasks. Retain this concrete oracle limitation and reproduction, without claiming a repair.
- [discarded] low: Cannot statically verify: the autopilot suite, `python3 -m unittest discover -s scripts` and `python3 scripts/validate.py` pass. The test gate reports exit 0 with no counts, and the fail-first replay was skipped because `requirements-test.txt` does not exist at base. (N/A) - reason: Discard as resolved verification: canonical run_gate recorded PASS89 FAIL0 SKIP0 EXIT0; validator12 tests and repository validation also passed. Replay remains explicitly skipped because the base lacks the new requirements file.
- [discarded] low: The gated SKILL.md bodies keep `${CLAUDE_PLUGIN_ROOT}` and Claude-specific prose. This is known and out of scope: the content is preserved byte for byte behind the first-body refusal gate for AP 00015 to adapt. (plugins/autopilot/skills/run-autopilot/SKILL.md:13) - reason: Known intended gate: AP00015 owns adapting retained source prose. No runtime fallback to source or author-home is authorized.
- [discarded] low: The only semantic validator is the test oracle; there is no runtime one. This is by design: task 14 forbids a validator runtime, and AP 00020 owns it. (tests/autopilot/test_contract_semantics.py:269) - reason: Known intended boundary: AP00020 owns runtime semantic validation; this PRD deliberately ships only a test oracle.

## Incremental review

This is an **incremental review** of the rework done since the previous review cycle — the diff is scoped to changes since then. Two jobs: (1) for each prior finding listed below, verify it is now resolved in the code; (2) review the scoped diff for any regression the rework introduced. You need not re-review unchanged code; the previous cycle already reviewed the full implementation.

### Prior cycle findings

---
prd: docs/dev/project-management/prds/wip/00012-autopilot-package-contract-v1.md
review: 1
date: 2026-10-28
head_sha: 3dda8f1a83e6a600b209fb70a12f8dfaf96e93b6
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
dispatch_rows:
  bob: 72b8b9b2
---

# Review: 00012-autopilot-package-contract-v1

Diff range: `b1e05c75d6f0dad01db35258baf565ecaf5a77ad..3dda8f1a83e6a600b209fb70a12f8dfaf96e93b6`

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/alice-output-ap00012-c1.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/blake-output-ap00012-c1.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/bob-output-ap00012-c1.txt.receipt.json

The model-provider guard supersedes the legacy launcher guard; no Eve ran.
All three fresh external reviews served claude-opus-5-5 at xhigh through the authorized helper.
The implementation audit and review-route require Anthropic because contributing implementations used OpenAI GPT.
Carl was not dispatched: the host review transport and required provider roster cover Alice, Blake and Bob; this Python/data/documentation change has no UI surface. Carl remains optional and no Carl success is claimed.

## Review Summary

Reviewed all 19 completed tasks and the whole PRD work range. All three reviewers produced complete required rubric verdicts and successful immutable receipts. The 32MB full diff remains available on disk. Alice used staged implementation context; Blake received only the PRD, rubric and test-gate block. Bob used the full assembled consensus/doubt/de-slop persona with Read-tool access, adapting the source Claude-fallback reading instruction instead of inlining a 32MB transcript-heavy diff. No rubric or finding was removed.

The staging test gate ran successfully but could not parse pytest's normal summary. The one required fallback verify invocation used a temporary pytest terminal-summary plugin that reports actual counts; only run_gate wrote last-verification.json. It recorded 89 passed, zero failed, zero skipped at the reviewed HEAD. Validator unit tests: 12 passed; repository validator: 3 packages, 15 skills.

Fail-first replay: skipped (the base has no tools/autopilot/requirements-test.txt). Tautology detector: no MECH findings. No prior verification-check queue exists in cycle1. Pack generation succeeded. No staging lens or dispatch-row error was observed.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | ⚪ | A stray blank line at `plugins/autopilot/CHANGELOG.md:9` splits the `### Added` list into two loose lists. | plugins/autopilot/CHANGELOG.md:9 | 14 | ALICE, BOB |
| R2 | [1/3] | 🟠 | resource_closure leaves out many runtime script dependencies. `resource_edges` has 202 rows, yet packaged skills call scripts that are neither packaged nor declared external: `consolidate_findings.py` (plugins/autopilot/skills/run-autopilot/references/lane-solo.md:168, plugins/autopilot/skills/review-work-completion/SKILL.md:386), `compute_mech_facts.py` (plugins/autopilot/skills/fast-track/SKILL.md:270), and also `render_prompt.py`/`record_dispatch.py` in fast-track, `detect_tautological_tests.py`, `check_review_file.py`, `await_reviewer_outputs.py`, `fast_track_plan.py`, `card.py`, `fablectl.py` and `parse_review.py`. The test locks the edge count and digest (tests/autopilot/test_package.py:331), so it cannot catch the gap. The unconditional skill gates block runtime harm today, but later PRDs that restore entry points will inherit this incomplete map | tools/autopilot/source-map.json | Phase 1 task 2 | BLAKE |
| R3 | [1/3] | 🟡 | `plugins/autopilot/scripts/autopilot.py:41` re-walks the parsed policy by hand (lines 41-49) to find floats. Passing `parse_float` and `parse_constant` hooks that raise `ValueError` to the `json.loads` call at line 36 rejects fractions, exponents and NaN/Infinity while parsing. The behavior is the same, the 9-line loop goes away, and the existing `except ValueError` already turns the error into exit 1. | plugins/autopilot/scripts/autopilot.py:41 | 14 | ALICE |
| R4 | [1/3] | 🟡 | All 27 behavior rows assigned to 00012 (P03–P05, R01, OPT-042, BEH-001..010, UTIL-*) still show evidence status "planned" with null artifact, sha and revision, and their acceptance cases are "planned". Nothing in the map links this PRD's own obligations to the contracts and tests it delivered, while asset rows carry "passed" receipts | tools/autopilot/source-map.json | Phase 0 | BLAKE |
| R5 | [1/3] | 🟡 | No test checks the policy's rule IDs against the packaged rubric files. The design says to "parse the rule ids from the packaged … rubric.md … and require them to equal rule_ids" and to require that `eve.md` has the de-slop section. Instead, the R, B and D lists are hardcoded constants (`test_contract.py:28-30`), so a wrong list would still pass. The committed data is correct today: it matches R1-R4, R6-R13, B1-B19 and D1-D5 in the packaged files. | tests/autopilot/test_contract.py:121 | 2 | BOB |
| R6 | [1/3] | ⚪ | `tests/autopilot/test_package.py:203` checks six CHANGELOG bullets word for word, so rewording the changelog breaks a test. The CHANGELOG bytes are already pinned by `destination_blob_sha256` in `test_content_roster` (`tests/autopilot/test_package.py:281`), so this check repeats one that exists and only adds a dependency on the wording. A check for the `## [Unreleased]` / `### Added` structure would be enough. | tests/autopilot/test_package.py:203 | 19 | ALICE |
| R7 | [1/3] | ⚪ | `tools/autopilot/check-source.py:244` has three blank lines between `_audit_behaviors` and `_audit_regressions`. PEP 8 uses two (pycodestyle E303). | tools/autopilot/check-source.py:244 | 5 | ALICE |
| R8 | [1/3] | ⚪ | `tests/autopilot/test_package.py:69` builds its target from `git archive HEAD`. A local run with uncommitted edits therefore tests the last commit, not the working tree, and can pass on stale bytes. The design asks for this ("committed target inputs"), but neither the module docstring nor the README's Development section says so. | tests/autopilot/test_package.py:69 | 19 | ALICE |
| R9 | [1/3] | ⚪ | Four named acceptance scenarios have no test of that name: source_inventory_mapping, review_schema, reference_tree_preserved and package_self_contained. Tests under other names cover them (tests/autopilot/test_provenance.py:49, tests/autopilot/test_contract_semantics.py:299, tests/autopilot/test_package.py:286, tests/autopilot/test_package.py:371). The exit criterion "the named task tests pass" can only be checked by hand-mapping | tests/autopilot/test_package.py:286 | general | BLAKE |
| R10 | [1/3] | ⚪ | The oracle rejects a review when an activated conditional reviewer (Carl) fails its last attempt (`required_job_failed`). The pinned retry policy says to mark the reviewer unavailable and continue (plugins/autopilot/skills/review-work-completion/references/retry-policy.md:9), and the policy encodes `reviewer_failed_after_retry → mark_unavailable`. Rejecting is right for mandatory jobs but stricter than the source for optional Carl, and no golden case covers that path | tests/autopilot/test_contract_semantics.py:171 | Phase 0 | BLAKE |
| R11 | [1/3] | ⚪ | The README and CHANGELOG "passed" delivery receipts point at themselves: the artifact is the file itself, and the test checks `tested_package_revision` only with a regex. The receipt proves nothing beyond the file's hash | tests/autopilot/test_package.py:122 | Phase 2 task 2 | BLAKE |
| R12 | [1/3] | ⚪ | prerequisites.py counts only regular `NNNNN-<slug>.md` files, but the backlog `eligibility:` lines use `ls done/NNNNN-*`. The "maintainer view of the same table" can disagree with selection, for example on `00012-x.md.bak` | tools/autopilot/prerequisites.py:35 | Phase 2 task 1 | BLAKE |
| R13 | [1/3] | ⚪ | `doubt_label_map` ships in the portable policy, but it comes from the author's personal global AGENTS.md, not the pinned source, and has no source binding. It is author-home content inside a package meant to work without the author | plugins/autopilot/contracts/review-policy-v1.json:594 | Phase 0 | BLAKE |
| R14 | [1/3] | ⚪ | `check-source.py` never reads `review-policy-v1.json`. The design says it recomputes the binding and anchor digests from the pinned blobs. Coverage holds only through two checks that must both run: normal tests compare policy to inventory, and the audit compares inventory to blobs. | tools/autopilot/check-source.py:263 | 5 | BOB |
| R15 | [1/3] | ⚪ | `test_rejected_cases_have_exactly_the_specified_complete_semantic_defects` repeats `test_contract_semantics.py:299` for the rejected cases, and `test_package.py:406` runs the same oracle a third time. Lines 63-94 also re-check properties that the `validate_review == accepted` assert at line 42 already enforces. | tests/autopilot/test_contract_fixtures_adversarial.py:96 | 17 | BOB |
| R16 | [1/3] | ⚪ | `ci_autopilot_wired` asserts the exact list of steps in the unrelated `plugins` job. The design says not to snapshot unrelated workflow content, and any future specflow CI step will fail the autopilot suite. An ordered-subsequence check would still prove the job is preserved. | tests/autopilot/test_package.py:444 | 16 | BOB |
| R17 | [1/3] | ⚪ | The draft 2020-12 `"type":"integer"` accepts `1.0`, so `attempt: 1.0` passes the schema. The oracle's `range(1, highest + 1)` would then likely raise TypeError instead of returning a defect. The wire test covers 1.5 but not 1.0. | tests/autopilot/test_contract_semantics.py:160 | 3 | BOB |
| R18 | [1/3] | ⚪ | Cannot statically verify: the autopilot suite, `python3 -m unittest discover -s scripts` and `python3 scripts/validate.py` pass. The test gate reports exit 0 with no counts, and the fail-first replay was skipped because `requirements-test.txt` does not exist at base. | N/A | general | BOB |
| R19 | [1/3] | ⚪ | The gated SKILL.md bodies keep `${CLAUDE_PLUGIN_ROOT}` and Claude-specific prose. This is known and out of scope: the content is preserved byte for byte behind the first-body refusal gate for AP 00015 to adapt. | plugins/autopilot/skills/run-autopilot/SKILL.md:13 | 7 | BOB |
| R20 | [1/3] | ⚪ | The only semantic validator is the test oracle; there is no runtime one. This is by design: task 14 forbids a validator runtime, and AP 00020 owns it. | tests/autopilot/test_contract_semantics.py:269 | 14 | BOB |

## Decision Gate

- R1: Fix the shared changelog list break. Preserve all existing history and test intent; do not add unsupported formatting requirements.
- R2: Confirmed omitted script edges, including consolidate_findings.py and compute_mech_facts.py. Add complete source-anchored resource edges and gap-detecting tests using the existing schema; preserve frozen inventory, owners, prior edges and gates. Protocol C proceeds: the design Source-to-destination mapping explicitly defines resource edge kinds and failure rules. No public API or schema change is needed.
- R3: single-voice; the existing bounded walk is correct and the proposed parser-hook refactor changes no specified behavior.
- R4: Discard: the contract explicitly says AP00012 validates completeness of assignments, not completion of future work. Planned behavior/profile evidence must not be upgraded to host certification from delivery tests.
- R5: single-voice; the current policy IDs are correct. Missing dynamic rubric-file comparison is retained as a test-coverage limitation, not silently claimed fixed.
- R6: Discard: the immutable pre-integration history check independently prevents coordinated metadata/history erasure, a proved Devon exploit. Removing it would weaken required test intent.
- R7: single-voice; whitespace-only suggestion.
- R8: Discard: the module docstring explicitly says Committed target packages; archive HEAD is the specified target-only contract, not an accidental stale-working-tree test.
- R9: Discard: named acceptance scenarios are covered by the cited behavior tests. No contract requires Python function names to equal scenario labels.
- R10: Discard: activated required jobs must produce complete evidence; unavailable remains incomplete for a promised profile. Source retry/unavailability history is preserved separately. AP00020 owns actual runtime provenance.
- R11: Discard: these are delivery-only file/hash receipts, explicitly not execution certification. The build independently checked real Git revisions; self-contained artifact identity is not a claim of independent runtime proof.
- R12: Discard: completed PRDs are regular NNNNN-slug.md files by contract; backup files are not completion. The strict diagnostic intentionally refuses unrelated backups.
- R13: Discard: the reviewed design explicitly specifies doubt_label_map. Committed policy data has no author-home runtime dependency; no forbidden live home read occurs.
- R14: single-voice; the two passing checks provide transitive digest coverage. A direct policy read in the source auditor remains a coverage improvement, not a currently incorrect binding.
- R15: Discard: independent mutation/adversarial and isolated-archive assertions preserve committed specification intent. Do not remove tests merely because their golden-case oracle overlaps.
- R16: single-voice; the exact unrelated-job step snapshot is a genuine maintenance limitation retained in the ledger. The current workflow is correct.
- R17: single-voice; confirmed by coordinator: full-clean input.reviewer_results[0].attempt=1.0 raises TypeError at history_defects line160. The canonical gate forbids single-voice medium/low fix tasks. Retain this concrete oracle limitation and reproduction, without claiming a repair.
- R18: Discard as resolved verification: canonical run_gate recorded PASS89 FAIL0 SKIP0 EXIT0; validator12 tests and repository validation also passed. Replay remains explicitly skipped because the base lacks the new requirements file.
- R19: Known intended gate: AP00015 owns adapting retained source prose. No runtime fallback to source or author-home is authorized.
- R20: Known intended boundary: AP00020 owns runtime semantic validation; this PRD deliberately ships only a test oracle.

The high resource-edge gap blocks convergence at cycle1/cap3. Existing schema suffices; additive source-anchored dependency rows and tests need no new dependency, external interface or foundational data-model decision. Original completed tasks stay completed. Queue fresh D1 follow-ups through review-close, preserving every prior implementation attempt and the model audit snapshot.

Bob VERIFY handling: the integral-float prose is not an exact runnable command, so it is not queued (command shape). A bounded coordinator reproduction instead used the actual fixture input field and confirmed TypeError. The preliminary reproduction used a nonexistent evidence key and failed with KeyError before the corrected check; neither result is represented as a passing test. The test-gate VERIFY item is already resolved by the canonical verifier and explicit validator checks; it creates no duplicate check/task. Bob's KNOWN items retain their assigned future ownership.

## Alice

Provider: Anthropic; served model claude-opus-5-5; effort xhigh.

### Anthropic

Receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/alice-output-ap00012-c1.txt.receipt.json

[ALICE] 🟡 `plugins/autopilot/scripts/autopilot.py:41` re-walks the parsed policy by hand (lines 41-49) to find floats. Passing `parse_float` and `parse_constant` hooks that raise `ValueError` to the `json.loads` call at line 36 rejects fractions, exponents and NaN/Infinity while parsing. The behavior is the same, the 9-line loop goes away, and the existing `except ValueError` already turns the error into exit 1. | File: plugins/autopilot/scripts/autopilot.py:41 | Task: 14
[ALICE] ⚪ `tests/autopilot/test_package.py:203` checks six CHANGELOG bullets word for word, so rewording the changelog breaks a test. The CHANGELOG bytes are already pinned by `destination_blob_sha256` in `test_content_roster` (`tests/autopilot/test_package.py:281`), so this check repeats one that exists and only adds a dependency on the wording. A check for the `## [Unreleased]` / `### Added` structure would be enough. | File: tests/autopilot/test_package.py:203 | Task: 19
[ALICE] ⚪ A stray blank line at `plugins/autopilot/CHANGELOG.md:9` splits the `### Added` list into two loose lists. | File: plugins/autopilot/CHANGELOG.md:9 | Task: 14
[ALICE] ⚪ `tools/autopilot/check-source.py:244` has three blank lines between `_audit_behaviors` and `_audit_regressions`. PEP 8 uses two (pycodestyle E303). | File: tools/autopilot/check-source.py:244 | Task: 5
[ALICE] ⚪ `tests/autopilot/test_package.py:69` builds its target from `git archive HEAD`. A local run with uncommitted edits therefore tests the last commit, not the working tree, and can pass on stale bytes. The design asks for this ("committed target inputs"), but neither the module docstring nor the README's Development section says so. | File: tests/autopilot/test_package.py:69 | Task: 19

Verified: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` gave 89 passed, 0 skipped. `python3 scripts/validate.py` reported "Validated 3 plugin package(s) and 15 skill(s)". `python3 tools/autopilot/check-source.py --source-root ../claude-autopilot` passed: 679 files, 92 assets, 1381 behaviors, 4950 regression cases. The policy lanes, rosters, escalation rules and rubric sets match the design tables, and the fixture file has all 55 named cases.

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Provider: Anthropic; served model claude-opus-5-5; effort xhigh.

### Anthropic

Receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/blake-output-ap00012-c1.txt.receipt.json

The package mostly matches the spec. One acceptance criterion fails: the `resource_closure` map leaves out many runtime script dependencies, and its test locks in that incomplete set.

What I checked and found sound:
- **Manifest:** schema URL, name `autopilot`, version 0.10.0, author `buvis` (same as the pinned `.claude-plugin/plugin.json`), MIT. LICENSE ships inside the package.
- **Asset bytes:** I compared all 97 rows in `source-map.json` to `git show` at the pin. The 78 preserved files (59 references, 18 personas, LICENSE) are byte-identical. The 11 SKILL.md changes add only the refusal gate.
- **Lane rosters:** the full, fast-track and solo rosters, conditional reviewers, input exclusions and caps (2 / 1 / 1) match the pinned source sections.
- **Commands:** `check-source.py --source-root` passes at the pin (679 files, 92 assets, 1381 behaviors, 4950 regression cases). `scripts/validate.py` passes. `prerequisites.py --prd 00013` exits 1 with `{"missing":["00012"]}`.
- **Tests:** I ran only `test_package.py` under Python 3.12 (8 passed). I did not rerun the full suite; the test gate reports it at exit 0 with no counts.
- **CI:** the 3.12 autopilot job is wired, and the 3.10 plugins job keeps its pinned actions.

[BLAKE] 🟠 resource_closure leaves out many runtime script dependencies. `resource_edges` has 202 rows, yet packaged skills call scripts that are neither packaged nor declared external: `consolidate_findings.py` (plugins/autopilot/skills/run-autopilot/references/lane-solo.md:168, plugins/autopilot/skills/review-work-completion/SKILL.md:386), `compute_mech_facts.py` (plugins/autopilot/skills/fast-track/SKILL.md:270), and also `render_prompt.py`/`record_dispatch.py` in fast-track, `detect_tautological_tests.py`, `check_review_file.py`, `await_reviewer_outputs.py`, `fast_track_plan.py`, `card.py`, `fablectl.py` and `parse_review.py`. The test locks the edge count and digest (tests/autopilot/test_package.py:331), so it cannot catch the gap. The unconditional skill gates block runtime harm today, but later PRDs that restore entry points will inherit this incomplete map | File: tools/autopilot/source-map.json | Task: Phase 1 task 2
[BLAKE] 🟡 All 27 behavior rows assigned to 00012 (P03–P05, R01, OPT-042, BEH-001..010, UTIL-*) still show evidence status "planned" with null artifact, sha and revision, and their acceptance cases are "planned". Nothing in the map links this PRD's own obligations to the contracts and tests it delivered, while asset rows carry "passed" receipts | File: tools/autopilot/source-map.json | Task: Phase 0
[BLAKE] ⚪ Four named acceptance scenarios have no test of that name: source_inventory_mapping, review_schema, reference_tree_preserved and package_self_contained. Tests under other names cover them (tests/autopilot/test_provenance.py:49, tests/autopilot/test_contract_semantics.py:299, tests/autopilot/test_package.py:286, tests/autopilot/test_package.py:371). The exit criterion "the named task tests pass" can only be checked by hand-mapping | File: tests/autopilot/test_package.py:286 | Task: general
[BLAKE] ⚪ The oracle rejects a review when an activated conditional reviewer (Carl) fails its last attempt (`required_job_failed`). The pinned retry policy says to mark the reviewer unavailable and continue (plugins/autopilot/skills/review-work-completion/references/retry-policy.md:9), and the policy encodes `reviewer_failed_after_retry → mark_unavailable`. Rejecting is right for mandatory jobs but stricter than the source for optional Carl, and no golden case covers that path | File: tests/autopilot/test_contract_semantics.py:171 | Task: Phase 0
[BLAKE] ⚪ The README and CHANGELOG "passed" delivery receipts point at themselves: the artifact is the file itself, and the test checks `tested_package_revision` only with a regex. The receipt proves nothing beyond the file's hash | File: tests/autopilot/test_package.py:122 | Task: Phase 2 task 2
[BLAKE] ⚪ prerequisites.py counts only regular `NNNNN-<slug>.md` files, but the backlog `eligibility:` lines use `ls done/NNNNN-*`. The "maintainer view of the same table" can disagree with selection, for example on `00012-x.md.bak` | File: tools/autopilot/prerequisites.py:35 | Task: Phase 2 task 1
[BLAKE] ⚪ `doubt_label_map` ships in the portable policy, but it comes from the author's personal global AGENTS.md, not the pinned source, and has no source binding. It is author-home content inside a package meant to work without the author | File: plugins/autopilot/contracts/review-policy-v1.json:594 | Task: Phase 0

B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

Provider: Anthropic; served model claude-opus-5-5; effort xhigh.

### Anthropic

Receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/bob-output-ap00012-c1.txt.receipt.json

[BOB] 🟡 No test checks the policy's rule IDs against the packaged rubric files. The design says to "parse the rule ids from the packaged … rubric.md … and require them to equal rule_ids" and to require that `eve.md` has the de-slop section. Instead, the R, B and D lists are hardcoded constants (`test_contract.py:28-30`), so a wrong list would still pass. The committed data is correct today: it matches R1-R4, R6-R13, B1-B19 and D1-D5 in the packaged files. | File: tests/autopilot/test_contract.py:121 | Task: 2
[BOB] ⚪ `check-source.py` never reads `review-policy-v1.json`. The design says it recomputes the binding and anchor digests from the pinned blobs. Coverage holds only through two checks that must both run: normal tests compare policy to inventory, and the audit compares inventory to blobs. | File: tools/autopilot/check-source.py:263 | Task: 5
[BOB] ⚪ `test_rejected_cases_have_exactly_the_specified_complete_semantic_defects` repeats `test_contract_semantics.py:299` for the rejected cases, and `test_package.py:406` runs the same oracle a third time. Lines 63-94 also re-check properties that the `validate_review == accepted` assert at line 42 already enforces. | File: tests/autopilot/test_contract_fixtures_adversarial.py:96 | Task: 17
[BOB] ⚪ Changelog problems: a stray blank line splits the Added list, the bullets lack the `**autopilot**:` prefix that specflow and the changelog rule use, and no entry announces the 11 gated skills, 18 personas and 59 references. `test_package.py:203` pins the bullet text word for word, so any fix must update that test too. | File: plugins/autopilot/CHANGELOG.md:9 | Task: 16
[BOB] ⚪ `ci_autopilot_wired` asserts the exact list of steps in the unrelated `plugins` job. The design says not to snapshot unrelated workflow content, and any future specflow CI step will fail the autopilot suite. An ordered-subsequence check would still prove the job is preserved. | File: tests/autopilot/test_package.py:444 | Task: 16
[BOB] ⚪ The draft 2020-12 `"type":"integer"` accepts `1.0`, so `attempt: 1.0` passes the schema. The oracle's `range(1, highest + 1)` would then likely raise TypeError instead of returning a defect. The wire test covers 1.5 but not 1.0. | File: tests/autopilot/test_contract_semantics.py:160 | Task: 3
[BOB] ⚪ Cannot statically verify: the autopilot suite, `python3 -m unittest discover -s scripts` and `python3 scripts/validate.py` pass. The test gate reports exit 0 with no counts, and the fail-first replay was skipped because `requirements-test.txt` does not exist at base. | File: N/A | Task: general
[BOB] ⚪ The gated SKILL.md bodies keep `${CLAUDE_PLUGIN_ROOT}` and Claude-specific prose. This is known and out of scope: the content is preserved byte for byte behind the first-body refusal gate for AP 00015 to adapt. | File: plugins/autopilot/skills/run-autopilot/SKILL.md:13 | Task: 7
[BOB] ⚪ The only semantic validator is the test oracle; there is no runtime one. This is by design: task 14 forbids a validator runtime, and AP 00020 owns it. | File: tests/autopilot/test_contract_semantics.py:269 | Task: 14

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

FIX:
- No test ties the rubric rule IDs to the packaged files — tests/autopilot/test_contract.py:121 — add a test that matches `^([RBD]\d+):` lines in `skills/review-work-completion/references/rubric.md`, `skills/review-blindly/references/rubric.md` and `skills/run-autopilot/references/doubt-review-rubric.md`. Assert each list equals `policy["rubric_sets"][ns]["rule_ids"]` in file order, and assert that `references/personas/eve.md` has the `2. De-slop lens` heading.
- `check-source.py` does not audit the policy's source bindings — tools/autopilot/check-source.py:263 — in `_audit`, load `plugins/autopilot/contracts/review-policy-v1.json`. Require each binding's `blob_sha256` to equal `files[path]["blob_sha256"]`, and a non-null `section_sha256` to equal the matching `sections[path]` anchor's `sha256`.
- Duplicate oracle test in the adversarial file — tests/autopilot/test_contract_fixtures_adversarial.py:96 — delete `test_rejected_cases_have_exactly_the_specified_complete_semantic_defects`, since `test_contract_semantics.py:299` already asserts every case's exact defect set.
- Changelog list break and missing scope prefix — plugins/autopilot/CHANGELOG.md:9 — remove the blank line, prefix each bullet with `**autopilot**:`, add a bullet for the gated skill, persona and reference port, and update the pinned strings at tests/autopilot/test_package.py:203.
- The CI test snapshots the unrelated `plugins` job — tests/autopilot/test_package.py:444 — replace the exact list equality with a check that the original commands appear in order within the job's run steps.

VERIFY:
- Schema accepts integral floats and the oracle may crash — deepcopy `full-clean` from `review-fixtures-v1.json`, set the alice result's `attempt` to `1.0`, and call `test_contract_semantics.validate_review(policies["v1"], ctx, ev)`. Expect a returned defect set; a TypeError confirms the bug.
- Test gate unverified — run `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`, `python3 -m unittest discover -s scripts` and `python3 scripts/validate.py`, and record the pass/fail/skip counts.

KNOWN:
- Claude placeholders kept in gated SKILL.md bodies — preserved byte for byte behind the refusal gate on purpose; AP 00015 owns adapting them.
- No runtime semantic validator — task 14 forbids inventing one, and AP 00020 owns runtime validation; the test oracle is the specified reference.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 20 findings
Tests: 89 passed, 0 failed, 0 skipped (suite run this cycle)

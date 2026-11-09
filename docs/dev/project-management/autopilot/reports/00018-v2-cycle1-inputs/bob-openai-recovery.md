OPENAI REVIEW TOOL POLICY:
Use the available read-only filesystem facilities, including exec_command/functions.exec for rg, bounded Python file reads, and git inspection. Do not require tools named read, glob, or grep. Do not modify files, execute tests, or run package managers. Gate evidence is supplied. Blake must remain PRD-only.

Read /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/autopilot/reports/00018-v2-cycle1-inputs/review-context-ap00018-v2-c1.md for review context, and /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/autopilot/reports/00018-v2-cycle1-inputs/review-diff-ap00018-v2-c1.diff for the full diff.

Read /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/autopilot/reports/00018-v2-cycle1-inputs/engram-pack-ap00018-v2-c1.md and treat its full content as prepended context: similar code, reuse precedent, findings precedent, and task prose for this diff's changed symbols.

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

You run in a read-only sandbox. Read files with read-only shell commands (`cat`, `sed -n`, `rg`, `ls`); that is how you open /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/autopilot/reports/00018-v2-cycle1-inputs/review-context-ap00018-v2-c1.md, /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/autopilot/reports/00018-v2-cycle1-inputs/review-diff-ap00018-v2-c1.diff, /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/autopilot/reports/00018-v2-cycle1-inputs/engram-pack-ap00018-v2-c1.md and any source file. You CANNOT execute code, tests, linters, or package managers, and you cannot write.

Perform STATIC analysis only:
- Read code for logical correctness, patterns, naming, structure
- Check for missing imports, dead code, type mismatches
- Review against PRD requirements by reading, not executing
- Trace data flow and control flow by reading source

If a criterion requires runtime verification (e.g. "tests pass", "linter clean"), output:
[BOB] ⚪ Cannot statically verify: {criterion description} | File: N/A | Task: {id}

Do NOT run tests, linters, builds, or package managers. Do NOT report failures from blocked execution. Never report an inability to read a file you were told to read: read it with `cat`.

## Two lenses, applied to every changed file

Treat - findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-01.md
  4. Accept: rely on the agent never recording such an approval (WF-002.7 is agent behaviour). Benefit: no change. Drawback: no tool backstop.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-01.md
  - **If unchanged:** valid Markdown blocks the tasks phase, and the agent may "fix" correct text.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-01.md
  - **Options:** (1, **Recommended**) Reword STATE-003.4 to "the helper writes no approval; it may compute the values the agent records". S. Against: it touches approved requirements. (2) Drop `approvedAt` and `workflowVersion` from `hash --json`. S; the agent then assembles more. (3) Accept as is.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00006-runtime-skill-review-01.md
  - Bob: ✅ Available (codex, after one retry (inlined)). His first run refused for lack of input, as in every 00004 and 00005 cycle: his `cat` of the context file was blocked by the Fact-Forcing Gate PreToolUse hook, and his own line cites `sandbox_apply: Operation not permitted`. The output had one `[BOB] ⚪ Cannot verify review criteria` line and every `R{n}` set to fail. That is the refusal shape in substance, though not the literal `Cannot statically verify` pattern, so the one retry used the inlined prompt (773 KB: context, diff, and the persona with the two edits). The first output is kept at `docs/dev/tmp/bob-output-00006c1-first.txt`. His retry put a `- ` bullet before each `[BOB]` line, so consolidation read a stripped copy (`bob-output-00006c1-lines.txt`). The `codex_thread_id` above belongs to the retry.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00012-autopilot-package-contract-v1-review-01.md
  # Review: 00012-autopilot-package-contract-v1

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00012-autopilot-package-contract-v1-review-01.md
  | R2 | [1/3] | 🟠 | resource_closure leaves out many runtime script dependencies. `resource_edges` has 202 rows, yet packaged skills call scripts that are neither packaged nor declared external: `consolidate_findings.py` (plugins/autopilot/skills/run-autopilot/references/lane-solo.md:168, plugins/autopilot/skills/review-work-completion/SKILL.md:386), `compute_mech_facts.py` (plugins/autopilot/skills/fast-track/SKILL.md:270), and also `render_prompt.py`/`record_dispatch.py` in fast-track, `detect_tautological_tests.py`, `check_review_file.py`, `await_reviewer_outputs.py`, `fast_track_plan.py`, `card.py`, `fablectl.py` and `parse_review.py`. The test locks the edge count and digest (tests/autopilot/test_package.py:331), so it cannot catch the gap. The unconditional skill gates block runtime harm today, but later PRDs that restore entry points will inherit this incomplete map | tools/autopilot/source-map.json | Phase 1 task 2 | BLAKE |

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00012-autopilot-package-contract-v1-review-01.md
  Verified: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` gave 89 passed, 0 skipped. `python3 scripts/validate.py` reported "Validated 3 plugin package(s) and 15 skill(s)". `python3 tools/autopilot/check-source.py --source-root ../claude-autopilot` passed: 679 files, 92 assets, 1381 behaviors, 4950 regression cases. The policy lanes, rosters, escalation rules and rubric sets match the design tables, and the fixture file has all 55 named cases. as findings precedent already recorded for this diff's changed symbols. Weigh it when applying both lenses and the rubric verdicts rather than re-litigating known prior findings.

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

## Additional gate evidence

Repository validator: 3 packages and 15 skills passed. Validator unittest: 59 passed.
Marketplace --check, bundle exporter --check, helper map --map tools/autopilot/source-map.json --check: exit 0.
Current HEAD full suite completed with exit 0: 1554 passed in 657.15s (0:10:57)
The earlier counts-unavailable line reflects the installed summary parser, not a test failure. The source-required counted verification pass completed: 1554 passed, 0 failed, 0 skipped; exit 0. Do not rerun the suite.

Scope: review the WHOLE v2 contract, including reused behavior; historical failures are not exemptions.
Generated files are reviewable through bounded reads; retain coverage of all changed files.

The OpenAI transport permits read-only shell inspection, as the source persona describes. Read the complete staged context and diff in bounded sections; do not execute project code. Retain both consensus R verdicts and D1-D5 verdicts, and both doubt/de-slop lenses.
Every finding must also use a [BOB] severity issue line; categorize it once in FIX/VERIFY/KNOWN.


## Final counted gate

Tests: 1554 passed, 0 failed, 0 skipped (suite run this cycle). CLI writer run_gate; exit 0, clean tree, no timeout, no moved HEAD. Full measured output: docs/dev/project-management/autopilot/reports/00018-v2-cycle1-final-gate.txt.

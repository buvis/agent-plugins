---
prd: docs/dev/project-management/specs/00008-host-integration/requirements.md
review: 1
date: 2026-11-01
head_sha: 37df89ea93461cd2fe1f075a4d7040949746449a
codex_thread_id: 01a198a8-ef1a-7dd0-9e2f-042a265721d5
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
  eve: disabled
---

# Review: 00008-host-integration

Diff range: `b1e05c75d6f0dad01db35258baf565ecaf5a77ad..37df89ea93461cd2fe1f075a4d7040949746449a`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 1, a full review of the eight specflow commits `ae36de1..37df89e` (state recovery, T-040, T-042, T-043, T-046, T-045 and its re-approval). The six autopilot commits before the merge base (`36b8e49..b1e05c7`) ride along in PR #9 but are outside this range. The target is spec 00008's `requirements.md`, with `design.md` as the design doc. Tasks came from a hand-written `docs/dev/tmp/review-tasks-00008c1.json` (five tasks, all completed). Findings are reported here, not written as tasks.

No reviewer found a 🔴 or a 🟠, and the codex guard did not fire, so the loop converges at cycle 1 under the autopilot bar. The rework is the tail sweep below, and no cycle 2 runs. Two reviewers (Alice, Blake) independently flagged the one 🟡: the README stated the GitHub install routes as plain lines, but the host records show they were not run.

### Agent Status

- Alice: ✅ Available (`autopilot:alice`, legacy consensus engine, native Claude subagent, effort high, about 1 min).
- Blake: ✅ Available (`autopilot:blake`, native Claude subagent, effort high, about 1 min).
- Bob: ✅ Available (codex backend, `gpt-6-luna`, effort medium, from the session rollout). The first dispatch was the inlined 176 KB prompt (context plus the 139 KB diff), and it produced no refusal. His `[BOB]` line carries no bullet.
- Carl: ⏸️ Disabled. The developer chose the roster alice, blake, bob. Nothing was dispatched on Gemini or Copilot.
- Eve: ⏸️ Disabled. `doubt_reviewer` resolved to codex (the spec has no frontmatter). With no state file there is no record of codex-implemented tasks, so the guard cannot fire.
- Model-family diversity: the build ran on Claude Fable 5.1, and Bob (OpenAI, codex) carries the non-Anthropic lens. The lead and the sweep ran on Claude Opus 5.5, so Pat ran on codex.

### Run notes

- pack: failed (`engram pack exit 1: not inside a registered repo` for this worktree). The review is degraded, not invalid.
- Gate: `review-stage` ran the nine CI steps through `docs/dev/tmp/review-tools/gate.sh` (exit 0). It could not parse unittest counts, so the lead composed the `Tests:` line from the logs: scripts 18, release 54, contract 387, rules 58, review 41 (558), all OK. `validate.py`, `generate_marketplace.py --check`, `check_rules.py --area ...` and `verify_release.py` exited 0. The CI Validate job passed on `37df89e`.
- Fail-first replay: the staged replay was skipped, because the unittest runner rejected pytest flags (exit 2). The lead ran it by hand in a detached worktree at `b1e05c7` with HEAD's `scripts/test_generate_marketplace.py` copied in. The module fails to import (`No module named 'generate_marketplace'`), so all six new tests fail at base. No `[MECH]` lines were raised.
- Consolidation correction (by hand): the script merged four `plugins/specflow/README.md` citations after suffix stripping (`:77 ~ :87 ~ :89 ~ :68`). Alice's single row covers Blake's two route rows, so they stay merged as F1. Alice's minimum-version row (`:87`) had been folded into F1. It is restored as F2. Refs were renamed from `R1`..`R4` to `F1`..`F5`.
- Lead's checks:
  - F1: confirmed. `README.md:68-71` gives `codex plugin marketplace add buvis/agent-plugins` with no ref, and `codex.md:175` ran only with `--ref feature/specflow-00008` ("without a ref the default branch is used, which carries the catalog only once this branch is merged"). `README.md:89-96` gives both Claude Code GitHub routes, and `claude-code.md:467` says "Not run before the release". PKG-003's risk fallback is "the limit is documented for that host".
  - F2: confirmed. `claude-code.md:443` says the one-step install needs Claude Code 2.1.275 or later, and the README did not say so.
  - F3: confirmed. Every `--check` test writes the file first, so `generate_marketplace.py:65`'s `else None` branch was unpinned.
  - F4: rejected. The claims are the T-027 (00004) result of 2026-10-12, which `design.md:62` cites. T-045's Details require the README to state them ("that Kiro IDE lists specs from a configured specs folder only through a `.kiro/specs` link ..., and the T-027 result"). The 00008 record did not need to repeat a trial that 00004 ran.
  - F5: rejected. Blake calls it "a disclosed weakness, not a defect". The in-session launcher and Codex's `-y` hand-back are disclosed at `claude-code.md:40` and `:157`, and SHA-256 evidence shows no workspace file changed. The T-043 contract asks for one recorded run.
- No verification-check queue, dispatch rows, contract card or session brief (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [2/3] | 🟡 | The README presents the Claude Code GitHub install (`/plugin install specflow --marketplace buvis/agent-plugins`, `claude plugin marketplace add buvis/agent-plugins`) and the Codex default-ref GitHub install (`codex plugin marketplace add buvis/agent-plugins`) as working lines, but the records say neither was run. Mark these routes as unverified until the release. | plugins/specflow/README.md:77 | T-045 | ALICE, BLAKE |
| F2 | [1/3] | ⚪ | The one-step Claude Code install needs Claude Code 2.1.275 or later (`claude-code.md:443`), and the README does not say so | plugins/specflow/README.md:87 | T-045 | ALICE |
| F3 | [1/3] | ⚪ | The `--check` branch where the committed file is missing (`current = None`) has no test | scripts/generate_marketplace.py:65 | T-046 | ALICE |
| F4 | [1/3] | ⚪ | Two Kiro "Known differences" claims (Specs panel only through a `.kiro/specs` link; `.kiro/specflow/` ignored) have no matching trial in the Kiro record | plugins/specflow/README.md:54 | T-040 | BLAKE |
| F5 | [1/3] | ⚪ | The Claude Code record is one in-session run with a setup-token launcher, and the Codex hand-back ran with `-y`. Both are disclosed, with hash evidence. | tests/specflow/compatibility/claude-code.md:56 | T-043 | BLAKE |

Overlap: F1 and F2 are the Claude Code and Codex install lines of the README host section. F3 is the one generator gap. F4 and F5 are rejected (see Lead's checks).

## Alice

```text
[ALICE] 🟡 plugins/specflow/README.md:77 and plugins/specflow/README.md:87 present the Claude Code GitHub install and the Codex GitHub default-ref install as working lines; the records say neither was run (claude-code.md:467, codex.md:175). Add one README sentence marking these two routes as unverified until the release tag (T-065 of 00001). | File: plugins/specflow/README.md:77 | Task: T-045
[ALICE] ⚪ The one-step Claude Code install needs Claude Code 2.1.275 or later (claude-code.md:442); the README does not say so. | File: plugins/specflow/README.md:87 | Task: T-045
[ALICE] ⚪ The `--check` branch where the committed file is missing (`current = None`) has no test. | File: scripts/generate_marketplace.py:65 | Task: T-046
```

She verified the generator against the design (`build_manifest` returns the exact text, writing and `--check` share it, the entries are sorted, a plugin with no Claude manifest is skipped, an unreadable manifest exits 1 without writing). She found the six design-named tests, the CI step, the three doc lines and the CHANGELOG entry. The README lists exactly the three supported hosts and names Kiro CLI and Kiro Crew as untested. No "to be verified" line remains in the design. She found no secrets, TODOs or skip markers.

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

```text
[BLAKE] 🟡 The README gives the Claude Code public install as a plain route; the record says it was not run (claude-code.md:467). | File: plugins/specflow/README.md:89 | Task: T-045
[BLAKE] 🟡 The Codex line has no ref, so it reads the default branch, which carries the catalog only after the merge (codex.md:175); the README does not warn. | File: plugins/specflow/README.md:68 | Task: T-045
[BLAKE] ⚪ Some Kiro "Known differences" claims have no matching trial in the Kiro record. | File: plugins/specflow/README.md:54 | Task: T-040
[BLAKE] ⚪ The Claude Code record is from a single in-session run; the Codex hand-back used `-y`; both disclosed. | File: tests/specflow/compatibility/claude-code.md:56 | Task: T-043
```

He confirmed PKG-003.4 (README:19-23), one record per host, the three hand-offs (Kiro to Codex, Codex to Claude Code, Claude Code back to Codex), and the Kiro and Codex install trials. He ran `generate_marketplace.py --check` and `validate.py` and found no scope creep and no secrets.

B1: pass
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
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

[BOB] ✅ No issues found

FIX: (none). VERIFY: (none). KNOWN: (none).

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

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Outcome

The lead adjudicated the findings alone under the standing authorization (no walkthrough):

| Finding | Disposition | Commit |
|---|---|---|
| F1 | fixed: the Codex section says the checkout route ran as written and the GitHub route only with a ref, and that without one Codex reads the default branch. The Claude Code section says the two GitHub routes are untested until the release and that the checkout and `--plugin-dir` routes were run. | `7da2302` |
| F2 | fixed: "inside Claude Code 2.1.275 or later, one step" | `7da2302` |
| F3 | fixed: `test_check_fails_when_the_committed_file_is_missing`. The branch already existed, so the evidence is a mutation: with the missing file read as up to date, the test fails (`0 != 1`). It passes on Python 3.10 and 3.14. | `4abc336` |
| F4 | rejected, with evidence above | none |
| F5 | rejected, with evidence above | none |

Both fixes are `docs`/`test` commits, so no CHANGELOG line is needed. After them the local gate passes 9/9 at `4abc336` with 559 tests. `validate_spec.py status` shows 00008 still in `verification` with all approvals valid, plus two `code-drift` warnings (`plugins/specflow/README.md`, `scripts/test_generate_marketplace.py`). Those are the sweep's own edits to baseline paths, the same kind 00005 to 00007 carry after their sweeps.

Pat (per-task patch review of `37df89e..4abc336`, codex `gpt-6.1-sol`, effort medium, foreground, about 1 min) returned `CLOSURE | resolved` for F1, F2 and F3 and `NO FINDINGS`.

Verdict: 5 findings

Tests: 558 passed, 0 failed, 0 skipped (suite run this cycle)

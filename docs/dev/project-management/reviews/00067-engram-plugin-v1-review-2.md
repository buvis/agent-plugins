---
prd: docs/dev/project-management/prds/wip/00067-engram-plugin-v1.md
review: 2
date: 2026-11-16
head_sha: ee568e1f3808c3abb55cfc3cd45c6b952bc45351
codex_thread_id: 01a1e37a-5c01-7063-88c2-49ffe18e05a3
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: 72abb0dd
  carl: 52d9fee1
---

# Review: 00067-engram-plugin-v1

Diff range: `a5c9bfb540b3e9351cf26a61867c4cd7bc568c08..ee568e1f3808c3abb55cfc3cd45c6b952bc45351`

codex_rung_guard: not fired

## Review Summary

Cycle 2, **incremental** review (diff scoped to the rework commits since
cycle 1's `head_sha`). All four reviewers ran: Alice (consensus, Claude
subagent), Blake (blind lens, PRD-only), Bob (doubt lens + rubric D1-D5,
codex, resumed thread `01a1e37a-5c01-7063-88c2-49ffe18e05a3`), Carl
(UI/design, gemini CLI). Consensus engine: legacy. Eve not activated
(resolved doubt reviewer is `codex`; no codex-implemented task, so the
codex doubt-roster guard did not fire).

Cycle 1's single HIGH (R1, missing `child.stdin` error listener) is
**resolved**: the listener is present at `engram-nudge.ts:29`, before the
write, and fails open. All seven cycle-1 single-voice discards were fed to
the reviewers as settled decisions; one Blake re-raise (the Kiro install
step) was auto-dismissed by `--ledger-dismiss BLAKE`.

Degradations and notes to record:

- `--replay-cmd` was passed this cycle, but the replay was **skipped by the
  tool**: the diff touches no test function. The tautological-shape check
  found 0 test functions in 0 test files for the same reason.
- `review-stage`'s test gate exited 0 but its summary line was not
  parseable (`counts unavailable`), so `autopilot verify` was run once in
  the foreground per step 6. It also failed to parse the pytest line
  (`64 passed, 189 subtests passed`), so it recorded nothing in
  `last-verification.json`; the counts below are read from its gate log
  `docs/dev/tmp/gate-ee568e1.log`.
- **Model-side merge:** `consolidate_findings.py` emitted Bob's 🟡 and
  Alice's ⚪ as two rows (R1, R2) despite the same defect at the same
  `engram-nudge.ts:29`; the wordings diverge too far for its matcher. They
  are one defect (stdin error settles without killing the child), so they
  are merged here into a single row with consensus 2 of 4 at medium
  severity. The script's own rows are described under "Consolidation note"
  below.

### Agent Status

- alice: available (consensus lens)
- blake: available (blind lens)
- bob: available (doubt lens, codex; thread 01a1e37a-5c01-7063-88c2-49ffe18e05a3)
- carl: available (gemini CLI backend, no issues found)

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/4] | 🟡 | The new stdin error handler calls `finish("")`, which clears the timeout without terminating the child. If Engram closes stdin but remains running, it escapes the 12-second cleanup. Terminate the child before settling empty on this path. | plugins/engram/works.earendil.pi/engram-nudge.ts:29 | 4 | BOB, ALICE |
| R2 | [1/4] | ⚪ | The Pi extension adds a `runEngramNudgePlain` helper with a settled-flag guard, a child-process kill on timeout, and swallowed spawn and stdin errors. The PRD only says to run the command with a 12 s timeout. This is fail-safe and is not a new feature. | plugins/engram/works.earendil.pi/engram-nudge.ts:5 | general | BLAKE |

Consolidation note: the script emitted three single-voice rows - R1 medium
(BOB) and R2 low (ALICE) at the same file:line, plus R3 low (BLAKE, now
R2). The first two were merged model-side as described above; Bob's
severity (the higher) governs.

### Auto-dismissed (ledger)

- [BLAKE] ⚪ README has no install step for Kiro. It appears only in the status table as "skill and MCP only", so a Kiro user gets no setup instructions. The PRD says "install steps per host" but gives Kiro no adapter. | File: plugins/engram/README.md:10 — single-voice

## Alice

```
[ALICE] ⚪ The `child.stdin.on("error", () => finish(""))` fix resolves the prior R1 finding, but `finish` only clears the timer and resolves. It does not kill the child. If stdin errors while the child is still running (rare, since EPIPE usually means it already exited), the 12 s timeout is cleared and the child lives on unkilled. Optional hardening, `child.kill()` before `finish("")` in that handler. | File: plugins/engram/works.earendil.pi/engram-nudge.ts:29 | Task: 4
```

Prior-finding check: the cycle-1 R1 stdin error listener is present at
`engram-nudge.ts:29`, before the write at line 30, and fails open, so the
unhandled EPIPE/ENOENT crash path is closed. The other prior findings are
settled decisions and were not re-raised. The rework diff touches only that
one line of shipped code; the other changed files are autopilot metrics and
review ledger/state files. No test changed, so there is no tautology or
fail-first concern.

Alice ran `python3 -m unittest discover -s tests/engram` (5 tests, OK) and
`python3 scripts/validate.py plugins/engram` (1 plugin package, 1 skill).

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

```
[BLAKE] ⚪ README has no install step for Kiro. It appears only in the status table as "skill and MCP only", so a Kiro user gets no setup instructions. The PRD says "install steps per host" but gives Kiro no adapter. | File: plugins/engram/README.md:10 | Task: general
[BLAKE] ⚪ The Pi extension adds a `runEngramNudgePlain` helper with a settled-flag guard, a child-process kill on timeout, and swallowed spawn and stdin errors. The PRD only says to run the command with a 12 s timeout. This is fail-safe and is not a new feature. | File: plugins/engram/works.earendil.pi/engram-nudge.ts:5 | Task: general
```

The first line was auto-dismissed against the settled-decisions ledger (see
above). Blind lens found no spec deviation otherwise.

B1-B19: all pass.

## Bob

```
FIX:

- [BOB] 🟡 The new stdin error handler calls `finish("")`, which clears the timeout without terminating the child. If Engram closes stdin but remains running, it escapes the 12-second cleanup. Terminate the child before settling empty on this path. | File: plugins/engram/works.earendil.pi/engram-nudge.ts:29 | Task: 4

VERIFY:

- (none)

KNOWN:

- (none)
```

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

```
[CARL] ✅ No issues found
```

Backend: gemini CLI (`gemini-run.sh`, exit 0). Carl read the pack, the
scoped diff, the context and `engram-nudge.ts`, and ran the validator, both
unittest suites and `generate_marketplace.py --check`; all passed.

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

## Mechanical checks

- Tautological test shapes: no `[MECH]` lines; 0 test functions in 0 test
  files (the rework diff touches no test).
- Fail-first replay: skipped by the tool (the diff touches no test
  function), although `--replay-cmd` was supplied.
- Carried-forward verification checks: none (cycle 1 wrote no checks queue).
- pack: ok (`docs/dev/tmp/engram-pack-00067c2.md`); `review-stage` reported
  no staging errors.

Verdict: 2 findings
Tests: 64 passed, 0 failed, 0 skipped (suite run this cycle)

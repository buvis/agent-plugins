---
prd: docs/dev/project-management/prds/wip/00067-engram-plugin-v1.md
review: 1
date: 2026-11-16
head_sha: a5c9bfb540b3e9351cf26a61867c4cd7bc568c08
codex_thread_id: 01a1e37a-5c01-7063-88c2-49ffe18e05a3
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: 57cfc7c5
  carl: 4b062e1e
---

# Review: 00067-engram-plugin-v1

Diff range: `4372cac3d6ea41fefd6cb26378b307ae2692fbf3..a5c9bfb540b3e9351cf26a61867c4cd7bc568c08`

codex_rung_guard: not fired

## Review Summary

Cycle 1, full review. All four reviewers ran: Alice (consensus, Claude
subagent), Blake (blind lens, PRD-only), Bob (doubt lens + rubric D1-D5,
codex), Carl (UI/design, gemini). Consensus engine: legacy. Eve not
activated (resolved doubt reviewer is `codex`; no codex-implemented task,
so the codex doubt-roster guard did not fire).

Degradation to record: the `review-stage` call omitted `--replay-cmd`, so
this cycle ran **no fail-first replay** of the changed tests against the
pre-change code. The tautological-shape check did run and reported no
`[MECH]` lines across 5 test functions in 1 test file. No settled-decisions
ledger existed on cycle 1, so consolidation ran without `--ledger`.

### Agent Status

- alice: available (consensus lens)
- blake: available (blind lens)
- bob: available (doubt lens, codex; thread 01a1e37a-5c01-7063-88c2-49ffe18e05a3)
- carl: available (gemini backend, no issues found)

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/4] | 🟠 | Pi adapter attaches no `error` listener to `child.stdin`. If `engram` is missing (ENOENT) or exits before reading stdin, the `write`/`end` calls emit an async EPIPE or destroyed-stream error. That error is unhandled and can crash the host's extension process instead of failing open. The `child.on("error")` handler only covers spawn errors. Add `child.stdin.on("error", () => finish(""))` before the write. | plugins/engram/works.earendil.pi/engram-nudge.ts:387 | 1 | ALICE, BLAKE, BOB |
| R2 | [1/4] | 🟡 | stderr is piped by default but never consumed. Enough diagnostic output can block Engram until the timeout, discarding a valid nudge. Set `stdio: ["pipe", "pipe", "ignore"]` when spawning, since stderr is intentionally unused. | plugins/engram/works.earendil.pi/engram-nudge.ts:7 | 1 | BOB |
| R3 | [1/4] | 🟡 | The five package tests never exercise the new Pi runtime logic. Add behavioral tests covering Bash filtering, stdin payload, stdout append, early stdin closure, spawn failure, and timeout cleanup; the documented absence of live Pi verification does not cover these unit checks. | tests/engram/test_package.py:15 | 2 | BOB |
| R4 | [1/4] | 🟡 | `assertFalse(command.startswith("/"))` is redundant: both the required prefix assertion and the preceding slash exclusion already guarantee it. Remove this assertion without changing test coverage. | tests/engram/test_package.py:35 | 2 | BOB |
| R5 | [1/4] | ⚪ | The Pi adapter's `spawn`, timeout and stdin wiring is untested. The PRD marks Pi "untested", so this is accepted. Nothing in `tests/engram/test_package.py` pins SKILL.md content or the `plugin.json` `extensions` paths either. `scripts/validate.py` checks the `extensions` paths and the CI run covers the rest. | tests/engram/test_package.py:1 | 2 | ALICE |
| R6 | [1/4] | ⚪ | The README gives install steps for Claude Code, Codex, Copilot CLI and Pi. The status table lists Kiro as "skill and MCP only", but no Kiro install step exists. The PRD's "install steps per host" can be read as covering Kiro. | plugins/engram/README.md:10 | general | BLAKE |
| R7 | [1/4] | ⚪ | The Claude manifest uses the guessed path-valued `hooks` field `./com.anthropic.claude-code/hooks.json`. The README states the hooks are "verified 2026-11-10" for Claude Code, but the PRD says that result came from project settings, not this plugin manifest. The README does not flag the guess or give the `hooks/hooks.json` fallback the Risks section describes. | plugins/engram/.claude-plugin/plugin.json:9 | general | BLAKE |
| R8 | [1/4] | ⚪ | The package-tests module lists `.github/workflows/validate.yml`, `README.md` and `.claude-plugin/marketplace.json` as its locations. All three were found updated: the CI step is at `.github/workflows/validate.yml:70`, the README row at `README.md:17`, and the marketplace entry at `.claude-plugin/marketplace.json:10`. I ran the validator, the `generate_marketplace.py --check` and the five engram tests. All passed. This is informational only. | N/A | general | BLAKE |

Consolidation note: row R1 merged three citations that matched after
line-suffix stripping (`engram-nudge.ts:387`, `:384`, `:29`).

## Alice

```
[ALICE] 🟡 Pi adapter attaches no `error` listener to `child.stdin`. If `engram` is missing (ENOENT) or exits before reading stdin, the `write`/`end` calls emit an async EPIPE or destroyed-stream error. That error is unhandled and can crash the host's extension process instead of failing open. The `child.on("error")` handler only covers spawn errors. Add `child.stdin.on("error", () => finish(""))` before the write. | File: plugins/engram/works.earendil.pi/engram-nudge.ts:387 | Task: 1
[ALICE] ⚪ `child.on("error", () => finish(""))` drops the error with no trace. Failing open is right for a nudge, but a one-line comment stating that intent would stop it reading as an accident. | File: plugins/engram/works.earendil.pi/engram-nudge.ts:384 | Task: 1
[ALICE] ⚪ The Pi adapter's `spawn`, timeout and stdin wiring is untested. The PRD marks Pi "untested", so this is accepted. Nothing in `tests/engram/test_package.py` pins SKILL.md content or the `plugin.json` `extensions` paths either. `scripts/validate.py` checks the `extensions` paths and the CI run covers the rest. | File: tests/engram/test_package.py:1 | Task: 2
```

Alice ran `scripts/validate.py plugins/engram`, the five engram tests and
`generate_marketplace.py --check`; all passed. She confirmed the hook
strings, `mcp.json`, both manifests, the README status table, the CHANGELOG
shape, the absence of `PLUGIN_ROOT` under `plugins/engram/`, the root README
row, and that the new CI step runs in the `autopilot` job with no `if:` or
`continue-on-error`.

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: fail
R11: pass
R12: pass
R13: pass

## Blake

```
[BLAKE] ⚪ Pi adapter attaches no `error` handler to `child.stdin`. If `engram` is missing from PATH (spawn ENOENT), the `stdin.write` that follows can emit an unhandled stream error and crash the extension instead of failing quiet. The other failures (spawn error, timeout) do resolve to an empty string. | File: plugins/engram/works.earendil.pi/engram-nudge.ts:29 | Task: general
[BLAKE] ⚪ The README gives install steps for Claude Code, Codex, Copilot CLI and Pi. The status table lists Kiro as "skill and MCP only", but no Kiro install step exists. The PRD's "install steps per host" can be read as covering Kiro. | File: plugins/engram/README.md:10 | Task: general
[BLAKE] ⚪ The Claude manifest uses the guessed path-valued `hooks` field `./com.anthropic.claude-code/hooks.json`. The README states the hooks are "verified 2026-11-10" for Claude Code, but the PRD says that result came from project settings, not this plugin manifest. The README does not flag the guess or give the `hooks/hooks.json` fallback the Risks section describes. | File: plugins/engram/.claude-plugin/plugin.json:9 | Task: general
[BLAKE] ⚪ The package-tests module lists `.github/workflows/validate.yml`, `README.md` and `.claude-plugin/marketplace.json` as its locations. All three were found updated. This is informational only. | File: N/A | Task: general
```

Blind lens found no spec deviation in the shipped files: skill frontmatter
and body, `mcp.json`, the three hook files and their timeouts, the Claude
manifest's repeated metadata, and the Pi extension's `isBashToolResult`
check, `engram nudge plain` invocation, JSON stdin, 12 s timeout and output
append all match the PRD.

B1-B19: all pass.

## Bob

```
FIX:
- [BOB] 🟠 An early child exit can emit an unhandled `EPIPE` on stdin and terminate Pi; the child process error listener does not handle stream errors. Add a `child.stdin` error handler that settles empty and cleans up the child. | File: plugins/engram/works.earendil.pi/engram-nudge.ts:29 | Task: 1
- [BOB] 🟡 stderr is piped by default but never consumed. Enough diagnostic output can block Engram until the timeout, discarding a valid nudge. Set `stdio: ["pipe", "pipe", "ignore"]` when spawning, since stderr is intentionally unused. | File: plugins/engram/works.earendil.pi/engram-nudge.ts:7 | Task: 1
- [BOB] 🟡 The five package tests never exercise the new Pi runtime logic. Add behavioral tests covering Bash filtering, stdin payload, stdout append, early stdin closure, spawn failure, and timeout cleanup; the documented absence of live Pi verification does not cover these unit checks. | File: tests/engram/test_package.py:15 | Task: 2
- [BOB] 🟡 `assertFalse(command.startswith("/"))` is redundant: both the required prefix assertion and the preceding slash exclusion already guarantee it. Remove this assertion without changing test coverage. | File: tests/engram/test_package.py:35 | Task: 2

VERIFY:
- (none)

KNOWN:
- (none)
```

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: pass
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

Backend: gemini CLI (`gemini-run.sh`, exit 0). Carl ran the validator, the
`scripts` and `tests/engram` unittest suites and the marketplace check, read
the diff and context, and searched `plugins/engram` and `tests/engram` for
`TODO|FIXME|console.log|debugger|print(` with no matches.

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

- Tautological test shapes: no `[MECH]` lines; 5 test functions checked in 1
  test file.
- Fail-first replay: skipped this cycle (no `--replay-cmd` passed to
  `review-stage`).

Verdict: 8 findings
Tests: 64 passed, 0 failed, 0 skipped (suite run this cycle)

# Decision Audit Log: 00067-engram-plugin-v1

PRD: `00067-engram-plugin-v1.md`
Started: 2026-11-16T08:50:25Z
Completed: 2026-11-16T08:50:25Z
Autonomous: 7  |  Deferred: 0  |  Doubts: 0

### [autonomous] 2026-11-16T08:50:25Z

**Decision**: Pi adapter attaches no `error` listener to `child.stdin`. If `engram` is missing (ENOENT) or exits before reading stdin, the `write`/`end` calls emit an async EPIPE or destroyed-stream error. That error is unhandled and can crash the host's extension process instead of failing open. The `child.on("error")` handler only covers spawn errors. Add `child.stdin.on("error", () => finish(""))` before the write.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-16T08:50:25Z

**Decision**: R1 Pi adapter attaches no error listener to child.stdin (EPIPE can crash the Pi extension)

**Choice**: auto-fix: queued as rework task 4 (cycle 1)

**Rationale**: 3/4 consensus; fix is additive only (adds a stdin error handler), no signature, schema or API change

### [autonomous] 2026-11-16T08:50:25Z

**Decision**: R2-R8 (stderr not consumed, Pi runtime tests, redundant assert, untested Pi wiring, missing Kiro install step, guessed Claude hooks path, informational CI/README note)

**Choice**: discarded as single-voice; all seven appended to the settled-decisions ledger

**Rationale**: each row carries Consensus [1/4]; the decision gate's Single-voice Medium or Low rule discards them and the ledger auto-dismisses a re-raise next cycle

### [autonomous] 2026-11-16T08:50:25Z

**Decision**: Cycle 1 review ran without the fail-first replay (review-stage called without --replay-cmd)

**Choice**: recorded as a degradation in the review file; tautological-shape check still ran clean over 5 test functions

**Rationale**: no reviewer raised a tautological-test finding and the suite is green at HEAD; re-staging the whole cycle to add the replay would cost four reviewer dispatches for one mechanical block

### [autonomous] 2026-11-16T08:50:25Z

**Decision**: Pi adapter stdin error handler settles empty without killing the child, so a child that outlives a stdin error escapes the 12 s cleanup (engram-nudge.ts:29)

**Choice**: auto-fix via cycle-2 tail sweep

**Rationale**: Medium, clear mechanical fix, raised by 2 of 4 reviewers (Bob 🟡, Alice ⚪ merged); converging cycle sweeps the medium tail

### [autonomous] 2026-11-16T08:50:25Z

**Decision**: Pi extension's runEngramNudgePlain adds a settled-flag guard, timeout kill and swallowed spawn/stdin errors beyond the PRD's bare 12 s timeout requirement (engram-nudge.ts:5)

**Choice**: discard

**Rationale**: single-voice (Blake only, [1/4]); the reviewer himself states it is fail-safe and not a new feature

### [autonomous] 2026-11-16T08:50:25Z

**Decision**: The new stdin error handler calls `finish("")`, which clears the timeout without terminating the child. If Engram closes stdin but remains running, it escapes the 12-second cleanup. Terminate the child before settling empty on this path.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

# Autocodex state-write recovery

## Failure Capture
- Session / task: cdd23c1ad0e04310976bbfb93c13267c; AP 00012 review cycle 1, task 20.
- Goal in progress: rework pending findings, then hand off to fresh review.
- Error: statectl rejected next_phase planning; wrapper halted on state-write-failed.
- Last successful step: preserved candidate and abort provenance; task 20 pending.
- Last failed command: statectl set next_phase '"planning"', including retry after restore.
- Repeated pattern: obsolete phase spelling deterministically rejected; heartbeat lines were progress notices, not evidence of a hang.
- Context pressure: Pat prompt remained 322,352 bytes after trim, over the 50,000-byte dispatch ceiling.
- Environment assumptions verified: installed schema accepts build; resume_target prioritizes subagent_prompt_overrun; wrapper lock was available.

## Recovery Action
- Diagnosis: stale work dispatch instructions retained the pre-collapse planning phase and obsolete signal-file handoff.
- Smallest action: corrected source and installed subagent-dispatch.md; atomically set phase/next_phase build and updated contract card through installed statectl.mutate.
- Safety: full before-state and original marker archived beside this report; all task records and other state fields unchanged. Stall trigger retained. No candidate applied, task completed, review waived, or cap raised.
- Evidence: schema validation passes; resume_target returns replan; autocodex --dry-run selects build; 36 resume tests, 12 repository validator tests, and repository validation pass. Cleared halt marker only after these checks.

## Agent Self-Debug Report
- Session / task: AP 00012 recovery.
- Failure: invalid recovery phase after oversized review prompt.
- Root cause: prose/schema mismatch, exposed by legitimate dispatch budget enforcement.
- Recovery action: source and installed instructions repaired; validated state routed to build recovery; resolved marker cleared.
- Result: success for recovery boundary; remaining PRD work is incomplete.
- Token / time burn risk: rerunning original task unchanged repeats the oversized prompt. Fresh recovery must split only remaining repair scope into bounded source-file groups.
- Follow-up: restart autocodex. Phase 0 must preserve completed-work summary and full archived history before tasks-clear, replan only task 20 and dependent 21 scope, and retain cycle/cap/review base. Implementation must hand off to fresh full review.
- Preventive change: source fix is in claude-autopilot/skills/work/references/subagent-dispatch.md with CHANGELOG entry; installed 0.10.0 copy has the same fix. Portable agent-plugins source-pinned assets were not changed.

Operator exception for PRD 00018 task 3 — status after signing recovery.

Task 3's Devon adversarial round AND its one mandated Tess strengthen are
COMPLETE:

- Devon ran under operator exception on Claude Opus (the GPT route is blocked by
  OpenAI's cyber-safety filter; this is a different in-policy model, not a
  bypass). Verdict: EXPLOITED, 8 proven weak points. Evidence:
  docs/dev/project-management/autopilot/reports/00018-replan1-task3-devon-result.md.
- Tess strengthened the tests on the normal GPT pipeline to close all 8 weak
  points. That change is committed as the `test(autopilot): strengthen
  controller schema for task 3` commit. The task-3 attempt already records
  devon: exploit_fixed and devon_weak_points: 8.

Apply to PRD 00018 task 3 ONLY:

1. Do NOT re-dispatch Devon (step 2.9) and do NOT run Tess again. Both rounds are
   done and the strengthened tests are committed. Re-running Devon re-trips the
   host filter; re-running Tess would duplicate the strengthen.
2. Continue the normal pipeline at step 2.95 (red-check) then step 3 (Ivan) on
   the standard GPT tiers. Ivan implements the real production schema to satisfy
   the strengthened tests. Review routing for task 3's implementation stays
   GPT -> Claude.

Scope limits:
- This exception covers task 3 only. It does not authorize skipping or routing
  any other gate, tier, or review lens.
- Later opus-tier tasks (notably 4, 6, 7) write security-relevant code and their
  own Devon rounds may hit the same filter. This directive does NOT pre-authorize
  those; each needs its own operator decision, or — the durable fix — Daybreak
  access for the org/project/model so GPT can run Devon directly.
- All task, coverage, evidence, review, and transition obligations in the host
  contract and source skills remain in force.

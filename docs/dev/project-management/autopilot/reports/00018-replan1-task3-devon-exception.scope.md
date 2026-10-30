Operator exception for PRD 00018 task 3 — Devon host-filter block.

Context: the mandatory step-2.9 Devon adversarial round for task 3 cannot run on
the native GPT route — OpenAI's cyber-safety filter (cyber_policy) blocks a GPT
model from generating the deliberately-wrong schema implementation Devon needs.
The operator has authorized running that one round on Claude Opus instead. This
is a different, in-policy model, not a filter bypass.

That round has ALREADY been executed under this exception. Verdict: EXPLOITED.
The 8 proven weak points and the full evidence are in
docs/dev/project-management/autopilot/reports/00018-replan1-task3-devon-result.md.

Apply the following to PRD 00018 task 3 ONLY:

1. Do NOT re-dispatch Devon (step 2.9) for task 3. Its GPT dispatch re-trips the
   filter, and its verdict already exists. Re-running it is redundant and will
   re-pause the batch for the same host reason.
2. Treat Devon as having returned those 8 weak points. Run exactly ONE Tess
   strengthen dispatch that addresses all 8 — each either strengthened with a
   new assertion or answered "N. in-contract: <why allowed>" per
   work/references/adversarial-test-prompt.md § Feedback to Tess. Any weak point
   Tess neither strengthens nor marks in-contract goes back in the same
   dispatch's one correction retry; never dismiss one in the orchestrator.
3. Commit the strengthened tests as `test(autopilot): strengthen controller
   schema for task 3`. Record on the task-3 attempt: devon: exploit_fixed,
   devon_exploit (a one-line summary), devon_weak_points: 8, and devon_in_contract
   (each "N. in-contract: …" line Tess returned, if any).
4. Continue the normal pipeline at step 2.95 (red-check) and step 3 (Ivan) on
   the standard GPT tiers. Ivan implements real production code; its provider is
   unchanged, and review routing for task 3's implementation stays GPT→Claude.

Scope limits:
- This exception covers task 3's Devon round only. It does not authorize
  skipping or routing any other gate, tier, or review lens.
- Later opus-tier tasks (notably 4, 6, 7) write security-relevant code and their
  own Devon rounds may hit the same filter. This directive does NOT pre-authorize
  those; each needs its own operator decision, or — the durable fix — Daybreak
  access for the org/project/model so GPT can run Devon directly.
- All task, coverage, evidence, review, and transition obligations in the host
  contract and source skills remain in force.

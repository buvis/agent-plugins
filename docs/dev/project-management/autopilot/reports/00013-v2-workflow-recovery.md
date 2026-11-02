# AP 00013 v2 interrupted workflow violation

Native build session 89d9609f-3f15-45b8-be74-f0929fd583c8 edited review_stage.py directly before Tess,
test quality/commit, Devon, the red check, or Ivan. Actual assistant models:
claude-sonnet-5. The task required the full Opus pipeline. No
worker or per-task reviewer dispatched; no test or completion result exists.
The coordinator interrupted the loop through its terminal (exit 130).

The uncommitted product diff is preserved in
00013-v2-invalid-work-attempt.patch (sha256 3ccb67fde901986a733558eefa4946e25a14ebc3c3bf302bd6adb5325e71218a).
It is recovery evidence, not accepted implementation. Restore the source to
its committed pre-attempt baseline and mark task 1 pending with a durable aborted-run record. Do not give the abandoned implementation to Tess. Re-author tests
from the frozen requirements, commit them, prove red, and use isolated roles
at the required tiers. Preserve every quality/adversarial/deslop/Pat gate.

The four-task plan, reviewed design, task dependencies and review cap 2 stay
unchanged. Raise only the orchestrator session to Opus because this session
violated the mandatory procedure. This is routine reversible recovery under
standing authorization, not a new rework cycle or waiver. If the corrected
session repeats the same violation, stop that route and use the existing
failure policy rather than accepting invalid work or looping indefinitely.

Process-list inspection was denied even after escalation. Terminal interrupt
succeeded; no process-access restriction was bypassed. Nothing was pushed.

## Attempt-writer limitation

The installed append-attempt writer rejected the actual implementor value
orchestrator unless red_check is n/a:micro-lane (or pipeline is solo). Neither
is true here. Do not forge either stamp, null the attribution to evade the
check, or modify the validator. Preserve the rejected payload as
00013-v2-rejected-attempt.json and link this event through autonomous_decisions.
No valid worker attempt ran, so tasks[0].attempts remains absent. The next
properly dispatched worker attempt starts its own valid sequence. This is an
installed-runtime logging limitation, not an accepted implementation.

The prior design decision's phrase 3/3 dispatches converged means three
required dispatches completed and the author corrected their findings. It
does not mean three clean reviewer verdicts or a fourth verification pass.
The third dispatch found a blocker; its subsequent design edit is recorded
in the design log. Product tests and full completion review remain mandatory.

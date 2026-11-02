# AP 00013 v2 interrupted workflow violation

Native build session 89d9609f-3f15-45b8-be74-f0929fd583c8 edited review_stage.py directly before Tess,
test quality/commit, Devon, the red check, or Ivan. Actual assistant models:
claude-sonnet-5. The task required the full Opus pipeline. No
worker or per-task reviewer dispatched; no test or completion result exists.
The coordinator interrupted the loop through its terminal (exit 130).

The uncommitted product diff is preserved in
00013-v2-invalid-work-attempt.patch (sha256 3ccb67fde901986a733558eefa4946e25a14ebc3c3bf302bd6adb5325e71218a).
It is recovery evidence, not accepted implementation. Restore the source to
its committed pre-attempt baseline and mark task 1 pending with an aborted
attempt. Do not give the abandoned implementation to Tess. Re-author tests
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

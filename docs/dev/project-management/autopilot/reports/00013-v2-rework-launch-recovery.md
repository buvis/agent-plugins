# AP00013 v2 interrupted rework launch

Native session f5e36315-cd5c-4508-9c1b-85b9f157fe00, 2026-11-04,
loop handle 28842, coordinator claude-sonnet-5/low. Root interrupted its
owned loop with Ctrl-C; teardown completed exit 130 at 09:05 CET.
The sole worker a21d047b6eeefe38b had only read files and run wc.
Git status showed only the coordinator task-start change to state.json;
no product, test or documentation edits landed and no test ran.

The dispatch violated the installed work process: it combined Tess and
Ivan, omitted independent Devon/test-quality/red-commit stages, omitted
render measurement and telemetry, and did not use the required background
watchdog. Its manual prompt had 8226 bytes. It also falsely assigned R7 to
review_stage/task 6, although the finding and code name log_sink_refusal,
which belongs to task 5. No role or gate from this attempt counts as done.

Preserve task 5 attempt 1 as aborted; reset only its status to pending.
Cycle remains 1, cap remains 2, original completed tasks stay complete.
Use the installed supported _AUTOPILOT_MODEL_REVIEW and
_AUTOPILOT_EFFORT_REVIEW overrides to launch the coordinator as
claude-opus-5[1m]/high, consistent with PRD session_model: opus.
Worker task tiers remain Sonnet under Phase 6. This changes coordinator
capacity after demonstrated process noncompliance, not role scope or the
review roster. Resume the same four rework tasks via the installed loop.

Required order for a production rework task: isolated Tess test author;
test-quality gate; isolated Devon challenge; isolated Tess strengthening
when required; committed tests and actual red check; separate Ivan; narrow
verification; commit and required deslop/style; isolated Pat. Follow the
installed bounded retries and task-specific test-only/prose routes. Never
combine author and implementor or silently omit a selected finding.

## Alias coverage update before the first valid worker dispatch

The Opus/high restart (loop 34245) was stopped at task claim, before any
worker dispatch or edit, exit 130. A concurrent read-only audit established
that the queued R17 alias command covers symlink sink paths and case aliases,
but never a symlinked project_root paired with resolved-spelling sinks.
The task-5 body now explicitly includes this PRD acceptance case in Tess
and bounded implementation scope. This was coordinator input completion,
not another failed worker attempt or review cycle. Task status alone returns
to pending; the original aborted attempt and all counters are preserved.
No test has run for R17. A green queued command alone cannot close it.

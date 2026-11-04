# AP00013 v2 contract resolution before completion review

2026-11-04. Coordinator ruling under the user's standing authorization. This
resolves the routine contract choice deferred by the build; it is not a
completion review, a passing gate, or permission to skip any review lens.

PRD F2 requires preserving spawn-failed behavior and existing output bytes.
The older cap-recovery tests require a failed spawn to leave the output tree
unchanged. Keep that behavior: a previously absent log remains absent; existing
log and artifact bytes remain unchanged. The new task-2 test's requirement to
leave an empty log was an implementation-derived assumption, not a PRD
requirement. Correct that new assertion through isolated Tess during rework,
retaining its remaining assertions and success control. Do not weaken the older
tests, distinguish CLI from API merely to satisfy opposing tests, or waive the
two failures.

Preserve the legacy `_open_log_sink` behavior covered by the two unchanged
SafeSinkOpener tests: existing contents are replaced, and replacing a symlink
leaf does not modify its outside target. Verification still needs its distinct
non-destructive acquisition before spawn. Preserve both contracts with a small
explicit helper interface or equivalent bounded separation; do not impose the
verification preflight semantics on every existing caller. The four failures
are supported AP00013 regressions and must be repaired before closure.

Resolve the creation/identity window identified by Pat as part of the same
sink-ownership boundary. Ownership must come from the actual open/create
operation, and identity from its descriptor, rather than an earlier exists
check and later independent pathname observation. Keep cleanup anchored to
the acquired parent and owned leaf. Preserve the primary failure if cleanup
fails. Test the demonstrated interleavings, not only the final helper shape.

Also resolve whether a failed artifact write/close can leave a reusable record
that a subsequent invocation accepts; F2 forbids reusable success after a
later sink error. Preserve the distinction between failed-spawn preservation
and arbitrary restoration after a failed write. No general output-management
subsystem or unrelated refusal-policy expansion is needed.

Run the fresh completion review now with Alice, Blake, Bob, Carl and Eve, then
the normal bounded rework and all required verification. Give this ruling and
the measured failures to the non-blind lenses. Blake retains PRD-only isolation.
Preserve v2 cycle 1, cap 2 and all prior attempts. Do not repeat the initial
task-2 pipeline merely because the session changed; new confirmed findings
follow the skill's normal rework process.

The measured full gate remains **23 failed, 967 passed**: four AP00013
regressions plus 19 AP00018 controller failures. No pass is inferred from task
completion records, and no master push occurs while required checks are red.

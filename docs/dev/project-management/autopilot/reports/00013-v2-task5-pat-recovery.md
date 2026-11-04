# AP00013 v2 task 5: complete Pat scope and bounded correction

2026-11-04. Native work session d530118d-6b54-49b7-a956-543a2960d833
(loop 80839) stopped by root, exit 130, at Pat dispatch. It had improperly
removed the whole new test module to fit a 55709-byte full render into the
50000-byte cap. No source edit was pending. Do not redo its valid work.

## Completed work and exact continuation state

- Task base: 08bf27e8436d239a013ecf0883418455508cedae.
- Tests: fbeeb5007d8ef3c1ee66a744cbd35b38840ce54c; isolated Tess, one dispatch, quality rubric and shape/style gates passed. Red run 14 failed / 31 passed. Four older red nodes separately confirmed by 4 failed / 41 passed baseline. Older tests unchanged; only the new empty-log expectation corrected.
- Implementation: 8d5c325a887af7e321ca9abab454dac650f45f97; isolated Ivan. Worker run 188 passed in 61.69s. Coordinator acceptance: 223 passed in 116.44s, exit 0, all nine files in docs/dev/tmp/review-task-5-verification.txt.
- Cleanup: fresh deslop returned noop. Style-limit and split-hygiene gates exited 0. Reflow tripwire reported verification.py:22 (targeted semantic hunks, not post-commit layout drift). No uncommitted Python layout churn remained.
- Actual workers: native claude-sonnet-5-5 / medium, matching worker-sonnet.md. Coordinator: claude-opus-5 / high.
- Devon was correctly skipped by work/SKILL.md step 2.9 for Sonnet. Root's earlier promise and recovery wording overstated Devon: only Opus/Fable tasks require it. The first interrupted launch was still invalid for combining Tess/Ivan, missing test-quality/red-commit steps and render/watchdog, and dropping R7. Do not add Devon retroactively.

## Pat evidence and remaining correction

Use the COMPLETE review: reviews/00013-v2-task5-pat-complete.md.
The partial output is separately preserved, never counted as a passed review.
Pat's tool-less native Sonnet/high session is
5f560368-70d2-459e-b9ec-257a789d8070 (actual claude-sonnet-5-5).
Root resumed that same isolated conversation with the entire omitted test add
diff and explicitly withdrew the scope exclusion. The 37660-byte first message
and 36460-byte scope completion together cover the exact full 38620-byte diff
across all five changed files. The scope manifest preserves hashes and paths.
No code changed between the messages. Parser exit 0; six resolved closure
rows, one MEDIUM and eight LOW findings. This is initial Pat cycle 1, with full
scope now complete, not a clean verdict and not a new PRD review cycle.

Resume TASK 5 AT WORK STEP 5.7 RESULT HANDLING, not task planning or initial
Tess/Ivan. The MEDIUM is supported by the new _symlinked_component branch:
under an aliased project root, a resolved-spelling below-root symlink can be
mistaken for the root alias. Preserve both root spellings while refusing every
symlink beneath either root before spawning. Use the installed ONE MEDIUM
retry, then ONE Pat delta re-run; no third MEDIUM review dispatch. Keep
last_reviewed_sha=8d5c325a887af7e321ca9abab454dac650f45f97 and the Pat session above.

A focused isolated Tess correction must pin that actual missed behavior with
a real temporary root and marker, keeping the prior success/refusal controls.
Do not repeat initial Tess or unrelated tests. Adjudicate every LOW against
code under standing authorization. The creation descriptor being closed before
reopen is a supported ownership-lifetime gap; retain it until descriptor
identity comparison completes, with bounded cleanup. Missing created-artifact
write/close and descendant log-close/write branch coverage directly concerns
R1/R9; strengthen those alongside the focused regression without weakening any
existing assertion. The pointer case-alias suggestion is conditional: check
whether earlier containment already refuses it before adding policy scope.
The tuple/duplicate-if suggestions are cosmetic and may remain noted; no
unrelated refactor is required. Judge report-key coverage against existing
schema assertions rather than adding tautological checks.

Then isolated Sonnet Ivan applies only confirmed bounded fixes, commit,
re-run the nine-file acceptance scope (plus any newly added test file), and
style/split gates. No repeat deslop. Render Pat's installed delta template,
resume with -R, include the MEDIUM and selected LOW findings verbatim plus
truthful unchanged note and exact fresh verification. Every changed task file,
including test changes, stays in the delta. Use the task's five paths to avoid
unrelated coordinator record/review commits; if any new task file is added it
must enter the delta too. Never omit code or tests to fit 50000 bytes. If a
complete prompt still cannot fit after permitted context trim, stop at the
existing budget recovery path; do not invent another reduced review.

Finish task 5 with the truthful completed attempt and medium-retry verdict,
including its preserved history and actual skipped:tier Devon disposition.
Then continue tasks 6,7,8 in sequence. Cycle 1 / cap 2 unchanged. After all
rework, phase-done exactly once and stop for fresh all-five-lens cycle 2.

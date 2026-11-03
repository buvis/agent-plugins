# AP00013 v2 task 2 cleanup correction

2026-11-03. Task 1 remains complete; task 2 is incomplete. No cycle, cap,
task base or review-session reset. This report supersedes the immediate work
section of the earlier task-2 recovery report, not its history or Pat scope.

Restart `52c7feb2-4b94-4ca7-ab12-8f86d3fcbddf` was stopped during catchup,
exit 130, before any role dispatch or product edit. Root had updated the card
file and task body but omitted `statectl set-contract-card`, leaving the
generated brief's stored card stale. The stored card and regenerated brief
are now synchronized and checked. This was a coordinator recovery error.

Native work session `412cd6fc-4bb1-4588-a935-c81d6b443050` stopped with exit
130 before Pat's follow-up. Tess `f0f4c208` corrected the denied-process-list
observation and added artifact-preflight regressions in `2e3dba5`: the actual
red check was **3 failed, 46 passed**. Ivan `a5027feb` implemented preflight in
`71fb60d12096c570d8ec19689e63c22338c0bedc`. Both workers were native
`claude-opus-5`, transcript effort `high`. Its exact complete six-file Verify
passed **151 tests in 86.10s**, and the coordinator replay passed **151 tests
in 86.39s**, both exit 0, without skips or a selection filter.

The style gate then rejected `run_verification` at 58 lines. The sole style
continuation `34402b1a` was interrupted during verification. Its extraction
patch is preserved in `00013-v2-task2-interrupted-style.patch`, committed
at `7c031f7`, and removed from the working source. It is not a completed
style gate or accepted fix. Do not restart de-slop.

## Proven remaining defects

A bounded audit of immutable `71fb60d` ran three temporary-only probes through
the real public verification API. The real child changed temporary fixture
paths, then a wrapper injected an actual `OSError(EIO)` into the real log
handle's write. Artifact opening, `_execute`, process cleanup and artifact
cleanup were unmodified committed production code.

- Control: returned `sink-write-failed`, retained the outside sentinel and
  removed the newly created artifact.
- Parent swap: the child renamed the artifact parent and replaced it with a
  symlink to another temporary directory. Cleanup's pathname `unlink` deleted
  that directory's sentinel; the original pinned artifact survived elsewhere.
- Leaf swap: the child replaced the artifact with a directory. Cleanup raised
  `PermissionError` (errno 1), masking the controlled `sink-write-failed` result.

Exact script, output and provenance accompany this report as
`00013-v2-task2-cleanup-probe.py.txt`, `00013-v2-task2-cleanup-output.txt` and
`00013-v2-task2-cleanup-evidence.json`. Exit 0 is probe execution success,
**not** a passing product gate. An initial argv-overlap refusal is recorded
separately and is not counted as proof. No user file was used as a sentinel.

## Bounded continuation

Use isolated Opus Tess to add regressions for both demonstrated interleavings
and the no-swap control in the existing sibling recovery test file. Preserve
every existing assertion, including absent-artifact preservation on failed
spawn. Tests must exercise real owned children and actual sink failure, with
cleanup armed before execution. Include a same-parent replacement-leaf control
so fixing only the parent symlink cannot delete a replacement file. This is
regression coverage for the interrupted fix, not another initial authoring,
Devon or strengthening cycle.

Then isolated Opus Ivan continues the same bounded fix. Cleanup must remain
anchored to the validated parent and owned created leaf; never follow the old
pathname after execution. Do not delete a replacement leaf or a leaf whose
ownership cannot be established. Cleanup failure must preserve the primary
controlled run error. Keep all descriptor, no-follow and hard-link defenses,
both pre-spawn validations, prior-byte preservation and pipe-close guards.
Reusing existing sink helpers is allowed; do not create a general output
management subsystem. Complete the interrupted style correction as part of
this fix, then run the actual complete six-file Verify and final style/split
checks. The earlier 151-pass evidence does not cover these new regressions.

Pat cycle 2 has **not** run. Resume the existing tool-less Sonnet/high session
`29c0b516-5d37-4c52-939e-289e4bf0523c` after verification. Follow the previous
recovery report exactly: omitted original-test diff first, then the complete
delta from `c5ab4eaf5e40d0cf46e74c435d363bfbe5f33efc` across all task files,
including both recovery test files. Include the cleanup evidence and truthful
verification. No file exclusions, repeated initial reviews or counter reset.
Task base stays `9dc395e26152b088cc6b4d22db46fd61c3bb58be`.

Tasks 3/4, all fresh completion-review lenses, AP18 and the backlog remain
pending. No master push is authorized before the 19 controller tests and all
required checks pass.

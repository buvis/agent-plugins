# Task 5 Pat delta re-run — the one permitted MEDIUM retry review

2026-11-04. Tool-less native Sonnet (claude-sonnet-5-5/high), session
5f560368-70d2-459e-b9ec-257a789d8070 resumed with `-R`. Delta
8d5c325a887af7e321ca9abab454dac650f45f97..HEAD scoped to this task's five
files, so the coordinator's record and review commits are excluded (244
insertions, 10 deletions across four files). Rendered prompt 29179 bytes,
dispatch ea0efa68. This is the single delta re-run the installed MEDIUM retry
rule allows; there is no third MEDIUM review dispatch for this task.

All six findings from the initial complete review are closed as resolved. The
re-run raised one NEW MEDIUM (a regression introduced by the fix) and three
LOW rows. Verbatim output follows.

CLOSURE | resolved | "MEDIUM log_sink_refusal.py:146: `_symlinked_component` alias escape stops at a below-root symlink under the resolved spelling" | The delta replaces the spelling comparison with a parent-resolves-inside test. A walk over `<root>/sub/x.log` with `sub -> root` now reaches `sub`, whose parent resolves inside the root, so `islink(sub)` refuses. The 24 new cases cover this under the root and output spelling crossings, but see the new MEDIUM below.

CLOSURE | resolved | "LOW verification.py:326: creation fd closed before the reopen identity comparison" | `fd` is now held through `os.fstat(sink.fileno())` and closed in the new `finally`, with a close error swallowed. `test_acquiring_the_output_sinks_leaves_the_open_descriptor_count_unchanged` guards the close.

CLOSURE | resolved | "LOW tests ~227: created-leaf branch after an untrusted write or close untested" | `test_a_created_artifact_leaf_does_not_survive_a_failed_record_write_or_close` starts with an absent artifact, covers write and close failure, and asserts the leaf is gone and the verdict is `stale`.

CLOSURE | resolved | "LOW tests ~253: log-close and record-write `_kill_group` branches, and the created-then-swapped log, untested" | `test_a_late_log_close_or_record_write_failure_ends_the_descendant_the_child_left_running` and `test_an_absent_log_replaced_before_its_sink_opens_is_refused_and_left_alone` cover them.

CLOSURE | resolved | "LOW tests ~375: group id never asserted absent from reports" | I accept the evidence. The legacy exact key-set assertions on the report, the artifact and the stored bytes fail on a leaked `pgid` key. I did not read those lines myself.

CLOSURE | resolved | "LOW log_sink_refusal.py:99: `resolved.parent == toplevel` is a string compare" | I accept the rationale. A case-aliased spelling is refused at the containment check before `_identity_hit`, so a samefile compare would only widen pointer reads. I did not see lines 33-36 in the diff.

MEDIUM | plugins/autopilot/scripts/log_sink_refusal.py:152 | The delta introduces a regression. The walk now breaks at the first component whose parent resolves outside the repo, so a path that leaves the repo through a symlink and returns through a second one is no longer detected. Example: a committed `out-link -> /outside`, with `/outside/x -> <root>/logs`, and log `<alias>/out-link/x/a.log` (alias or resolved spelling that differs from `root`). The resolved path lies inside the root, so containment passes. At `a.log` the parent resolves inside, so the walk continues. At `.../out-link/x` the parent `.../out-link` resolves to `/outside`, so `inside` is False and the walk breaks, returning False. The pre-delta walk continued to `x` and refused it. `_pinned_parent_fd` takes its `resolve()` fallback for the differently spelled path, follows both symlinks and opens `<root>/logs`, so the sink is written through two symlinked components below the root. This breaks criterion 8. The new tests miss it: the outside-link test uses a path whose resolved target is outside, so containment refuses it earlier, and the 63-row probe has no leave-and-return shape. | Break only on a root alias. Compute `parent_inside` as now, and break only if `not parent_inside and current.resolve() == repo_root.resolve()`. Otherwise continue and apply `os.path.islink(current)`. Add a test with a committed `out-link -> outside_dir` and an `outside_dir/back -> real/logs`, asserting `unsafe-artifact-path`, no spawn and no write, with an alias-spelled output.

LOW | tests/autopilot/test_helper_rework_sinks.py:412 | The note that four of the nine spelling combinations are unreachable is wrong. A test can build a third root spelling with a second symlink, for example `tmp_path/ancestor-link -> tmp_path` giving `ancestor-link/<repo>` (a symlinked ancestor, the macOS `/tmp` shape). That differs from both the resolved path and the direct alias of the root. `SPELLINGS` has two entries only. | Add the ancestor-link spelling to `spellings` and cross it in the below-root tests.

LOW | plugins/autopilot/scripts/verification.py:307 | Not resolved, and carried to the PRD review: `_Pin` is still a 4-tuple read as `pin[0]` and `pin[3]`, and `_unlink_pinned` and `_empty_pinned` still repeat the same lstat-and-identity prologue. | Use a `NamedTuple` and share one identity-check helper.

LOW | plugins/autopilot/scripts/log_sink_refusal.py:211 | Not resolved, and carried to the PRD review: `_open_log_sink` still tests `if preserve:` twice. | Branch once, or move the validation into the first branch.

## Coordinator adjudication of the re-run

**The new MEDIUM is CONFIRMED by measurement, and is worse than reported.** A
read-only probe built the exact shape Pat describes - a committed
`out-link -> outside` inside the repository plus an uncommitted
`outside/back -> <root>/logs` - and asked the module about it under four
spellings of the root crossed with four of the output path:

    installed now        leave-and-return accepted in 16 of 16 spellings

Not only the mixed spellings: the break fires on parent resolution regardless
of how either path is spelled, so even `root=real path=real` is accepted.

**It is a regression introduced by this cycle's rework, not a pre-existing
hole.** The same probe, with the historical variants of the function swapped in:

    pre-task-5 original  leave-and-return accepted in  0 of 16 spellings
    first fix round      leave-and-return accepted in  0 of 16 spellings
    installed now        leave-and-return accepted in 16 of 16 spellings
    pat candidate        leave-and-return accepted in  0 of 16 spellings

The coordinator's 63-row validation missed it because the coordinator chose the
shapes and never thought of a path that leaves the repository and returns. That
is the lens doing its job: the probe validated the rule the coordinator had in
mind, and Pat found the case the rule was wrong about.

**Pat's suggested fix is CONFIRMED correct by measurement.** Over 96 rows - four
spellings of the root crossed with four of the output path, crossed with six
path shapes (below-root symlinks at depths 1 and 2, a link to a subdirectory,
the leave-and-return chain, and plain paths at two depths):

    installed: WRONG rows 16 of 96
    candidate: WRONG rows  0 of 96
    control (installed again): WRONG rows 16 of 96

**His LOW on the unreachable spellings is CONFIRMED and the coordinator's note
was wrong.** `tmp_path/ancestor-link -> tmp_path` does give a third root
spelling a test can build, and the probe above uses exactly that fourth
spelling. The earlier claim in
`reports/00013-v2-task5-alias-defect-probe.md` that four combinations are
unreachable by any test is withdrawn.

**The two carried LOW rows** (`_Pin` as a `NamedTuple`, the duplicated
`if preserve:`) stay rejected for this task as cosmetic, with no unrelated
refactor authorized. Pat carrying them to the PRD review is the correct
disposition; cycle 2's lenses will see them.

**Review budget, stated plainly:** this was the one permitted delta re-run, so
the regression fix that follows it is NOT reviewed by Pat. It is covered by the
new tests, by the 96-row probe, and by cycle 2's five lenses (Alice, Blake,
Bob, Carl, Eve). No clean-review claim is made for it.

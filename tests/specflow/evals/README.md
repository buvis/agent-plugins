# Live evaluation matrix

The approved 00009 matrix runs every session on Claude Code and the nine named
smoke sessions on Codex and kiro-cli, including continuation dependencies.
`runners/run_matrix.py --dry-run` prints the exact groups without launching hosts.
Supplemental task scenarios live in `scenarios/<session>/`; the batch selects that
eval folder, preserving the original rule-inventory evals at this directory root.

Run only in a developer terminal outside run-agent, after committing all inputs.
The batch probes each host, writes `frozen-inputs.json`, runs independent groups
through failures, then captures the one-order handoff and external-edit trace.
Every Codex isolated batch can request its own independent sign-in. No active
credentials are copied. No automatic retry occurs. Exit 1 includes pending human
review; it is not a release certificate. Inspect the summary and retained records.
Failed or broken parents block children; pending human review alone does not.

After collecting records, use `review_matrix.py --judge-model EXPLICIT_MODEL` to
judge rubrics and prepare `results/review.json`. Use a judge model different from
every host model. The file lists every required human decision across all hosts.
Read the referenced transcript and eval rubric, then add PASS/FAIL, human identity
and evidence-based reason under `verdicts`. Do not edit samples or catalog data.
Re-run `review_matrix.py --review-file review.json` to apply completed decisions.
More than 10 percent disagreement escalates that host's entire rubric set.
Source changes invalidate the batch; no review is invented or silently waived.

Recheck eligibility for each record using its frozen session candidate and the
matching host proof through `score.py --candidate ... --boundary-proof ...`.
Use `--evals scenarios/SESSION` for supplemental scenarios. A passed score alone
is insufficient: require `releaseEvidence: true`, fresh inputs, clean measured
instructions, completed human review, and passing shared-session comparisons.
Run compatibility tests against the stored conversion records. Inspect every
record for secrets and absolute machine paths before commit. Kernel read tracing
is out of scope; unknown reads remain `notMeasured` and do not block release.

Source-skill parity and retirement gates moved to spec 00023-skill-parity.
No personal skill retires from this matrix.

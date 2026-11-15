# AP00014 v2 — assumption ledger

## Task 1: Characterize source hooks/runner effort and record finding dispositions

- `bound` means the source `_AUTOPILOT_LOOP` binding is set. The push and document guards ignore it, so their cases use `bound: false`.
- The target's `missing_controller_seam` deny means bound cases that keep source behavior need `facts.controller_seam: true`. The divergence case uses `controller_seam: false` and `expected` "deny". Inferred from the contract wording, not the design doc.
- The narrowed delegation detection allows `denied/run-entire-work-phase.txt` because it names no `autopilot:` skill; the allowed fixture chosen (`dispatch-tess-13-retry-devon.txt`) contains no `autopilot:` mention, so narrowing cannot flip it.
- `<repo>` in payload paths and cwd is a placeholder for the test's temporary repo root.
- `facts` keys (`custody`, `leave_marker`, `leave_marker_text`, `lanes`, `lane_guard_blocks`, `state`, `review_files`, `controller_seam`) and the runner-case facts (`claude_argv`, `prompt_via`, `prompt`, `effort`, `argv_contains`) are Ivan's own names — the contract does not name them.
- Runner payloads carry the invocation shape (`script`, `argv`); the characterized outcome goes in `facts`. Effort cases use `expected: "allow"`, with the divergence text explaining the source/target difference.
- For hook cases, `expected` is the target decision: the source decision unless `divergence` is non-null.
- Fixed rows (`F`) are owned by "AP00014 v2"; rows rejected inside AP00014 are owned by "AP00014 v2 (rejection recorded)".
- v1c2-R23's "as above" was read as the §10 real-probe contract and tests (same as v1c1-R9), with live certification deferred to AP 00017.
- The corrected effort target forwards `--effort LEVEL` to `claude` as `--effort LEVEL`; whether the installed `claude` CLI accepts that flag was not checked.

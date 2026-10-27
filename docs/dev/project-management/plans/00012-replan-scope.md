# AP 00012 planning constraints (operator scope, 2026-10-27)

Why: the first plan copied the design doc's whole `## Interfaces & contracts`
section (about 55 KB) into every task body. Devon's prompt for task 2 then
measured 69 163 bytes after one trim against the 50 000-byte Subagent Dispatch
Budget and the task aborted. The replan parked the PRD because a 110 KB
reference copy cannot fit a 75 000-token replan budget. The PRD re-enters from
`backlog/` in normal planning mode (150 000-token budget); `replan-context.md`
was consumed and does not apply.

Constraints for `/autopilot:plan-tasks` and `/autopilot:work` on this PRD:

1. A task's `Contract (verbatim):` block carries only the `###` entries of
   `## Interfaces & contracts` that the task's `Location:` files implement,
   byte-identical. Never the whole section.
2. Keep every task small enough that persona + task body + that task's own test
   files stay under 50 000 bytes. Plan the three review contracts as separate
   tasks (`review-policy-v1.json`, `review-evidence-v1.json`,
   `review-fixtures-v1.json`, each with its own tests), and split asset-copy
   work by file group.
3. The committed tests in `tests/autopilot/test_contract*.py` (commit 044dfdd)
   are the specification for the review-contract tasks. Keep their intent;
   Tess may move them between the split tasks, never weaken them.
4. Completed work stays completed: the source inventory and map
   (`tools/autopilot/source-pin.json`, `source-inventory.json`,
   `source-map.json`, commits f39d95e and a8a7e4c) are not re-planned.
5. `work_start_sha` is restored to `b1e05c75d6f0dad01db35258baf565ecaf5a77ad`
   so the review range covers the whole PRD, including the commits above.

Remove this file when AP 00012 completes.

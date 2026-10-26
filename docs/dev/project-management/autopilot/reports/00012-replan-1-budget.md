# AP 00012 replan budget result

The remaining plan cannot fit every required asset task under the committed
75,000-token replan budget. No implementation was dispatched in this session.

## Measured blocker

Pinned source: `e960ef1cc43e72bf92593b2f16c7a37c71ea7e48` in the PRD's
explicit source checkout. `git cat-file -s` at that pin reports 110,179 bytes
for `skills/run-autopilot/references/state-schema.md`.

Required destination:
`plugins/autopilot/skills/run-autopilot/references/state-schema.md`.

The planning estimator uses file bytes / 4 plus 55,000 overhead, PRD slice,
and task prose. Using the projected destination size, the lower bound is
`ceil(110179 / 4 + 55000) = 82545` tokens before prose. The context peak
lower bound is 102,545 tokens. This exceeds the 75,000-token budget in
`replan-context.md`.

## One split attempt

1. Split the reference-copy capability at file boundaries. The single
   state-schema reference remains above budget.
2. Consider capability boundaries within that file. The PRD requires every
   reference copied 1:1 at its declared location, with preserved byte hashes.
   Splitting or adapting the reference changes that contract; incremental
   partial-file tasks do not independently satisfy its acceptance criterion.
   The single file therefore remains an oversized planning unit.

A streaming byte copy would be cheap to execute, but the installed planning
procedure declares no estimator exemption for such copies. This session does
not invent an exemption or raise the committed budget. This is a planning
estimate failure, not a measured worker context overrun.

## Preserved work

The source inventory and source map remain committed. The partial contract
tests remain in commit `044dfdd`. Pre-replan task and attempt provenance remains
in `00012-pre-replan-1-state.json`; future implementation-model audits must
include its contributing attempts. The original review base is
`b1e05c75d6f0dad01db35258baf565ecaf5a77ad`.

The installed plan-tasks oversized-task policy and run-autopilot recovery
procedure require parking the PRD in `hold/` and continuing the batch. No
completion review or execution certification is claimed.

## Recovery verification

The canonical `autopilot stall --site oversized_task` call exited 0.
The PRD exists in `prds/hold/` and is absent from `prds/wip/`.
The consumed replan context was removed. State schema validation passed;
task counts are 0/0, and phase/next_phase both remain `build`.
`python3 scripts/validate.py` passed: 2 packages and 4 skills validated.
No implementation tests or completion-review roster ran: planning stopped
before any new implementation task was admitted.

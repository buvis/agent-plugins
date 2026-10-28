# PRD00012 replan budget stall

The committed replan cap is 75,000 tokens per task. The required estimator is file bytes / 4 + PRD slice bytes / 4 + description bytes / 4 + 55,000. `tools/autopilot/source-map.json` is 13,229,895 bytes: its minimum is 3,362,474 tokens before PRD and description. File-boundary splitting isolates this file. Capability-boundary splitting leaves the same file in each write set, so cannot meet the estimator. No worker was dispatched and no implementation changed.

Applied plan-tasks oversized-task recovery using statectl and the canonical stall CLI. The PRD is verified in hold. Replan context was consumed by recovery; the original remains in Git history and prior recovery reports. All nineteen completed tasks and original attempt metadata remain archived in `00012-prompt-overrun-replan-1-before.json`. Prior review receipts and candidate patch remain unchanged. Next session selects eligible work; this is not build completion or review convergence.

# Required per-task reviewer transport unavailable

The installed run-autopilot work procedure requires a tool-less Pat process (work/references/per-task-review.md, lines 31 and 45-59) and explicit high effort (work/references/subagent-dispatch.md, lines 18-20).

Installed autopilot 0.10.0 sonnet-run.sh handles -t/--tools and -R/--resume-print, but does not parse --effort or forward it to Claude. Unknown options fall into the prompt branch, so adding --effort high would not set effort. The personal use-sonnet wrapper parses and forwards --effort, but does not parse -t/--tools or -R; adding these would not disable tools or resume the print session. Both actual source files were inspected; hashes and resolved paths are in the sibling JSON.

The host role swap does not waive tool restrictions or required effort. No reviewer process was launched with weakened guarantees. No wrapper, permission setting, installed plugin or frozen source was changed. The required capability needs a supported wrapper combining explicit effort, tool-less mode and fresh/resumed print sessions, or an explicit operator-approved host adaptation. Preserve this evidence and use canonical interactive Resume after the capability is available.

Current product remains unfinished. No PRD completed, no completion review occurred. Pending AP00014 v1 custody remains intact. Repository validator: exit 0, Validated 3 plugin package(s) and 15 skill(s). Full implementation suite not rerun; operator-provided baseline remains 20 failed, 1433 passed.

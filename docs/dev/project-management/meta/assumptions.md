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

## Task 6: Rewrite claude.py, codex.py, gemini.py to the uniform §2 adapter surface

Tess (test author):
- Codex `apply_patch` patch text is in `tool_input["patch"]`; no existing convention was found.
- `dispatch_skill` is the match without its leading `/` (`"/autopilot:plan-tasks"` gives `"autopilot:plan-tasks"`), because the guard's phase-skill names have no slash.
- `translate_hook` reads `CLAUDE_CODE_CHILD_SESSION` from `os.environ`, since it gets no env argument.
- The `state_integrity` context key for paths is not pinned; tests only check that the path appears as a value or in a list value.
- Tools outside the registrations (Read, Task) make `translate_hook` return `()`.
- `session_from_hook_input` returns None when `session_id` is missing or empty.
- The Stop block reply is `{"decision": "block", "reason": ...}` with exit 0, and the reason contains the first denied reason. No repo convention was found.
- The SessionStart reply is `hookSpecificOutput.hookEventName == "SessionStart"` plus `additionalContext`, following Claude Code's documented shape.
- A PostToolUse deny's `systemMessage` contains the denied reason.
- Gemini may leave out `HOOK_REGISTRATIONS` or set it to `()`; the tests accept both.
- hosts.json may lag behind the adapters (capability check loosened from equality to subset).
- The context keys `project_root` and `session` are optional for state_integrity, custody_push and post_handoff, but when present they must equal the payload's cwd and session_id. The contract pins only the subject key.
- Codex PostToolUse apply_patch state_integrity paths are the Add, Update and Move-to paths, the same set as PreToolUse. Delete-only paths are not asserted for PostToolUse.
- With two denied Stop outcomes, the block reason must contain at least one denied reason. Which one, or both, is not pinned.
- `GEMINI_API_KEY` is gemini's only auth variable tested on its own.

Ivan (implementor):
- The `state_integrity` context is `{"paths": tuple, "project_root": cwd, "session": session_id}`. The tests pin neither the key names nor their shape.
- The `custody_push` context is `{"command", "project_root"}`, and the Stop and SessionStart contexts are `{"project_root", "session"}`. Not pinned beyond "every value comes from the payload".
- A codex apply_patch PostToolUse always emits `state_integrity`, even when the patch writes no path (a delete-only patch).
- Deleted paths are excluded from `state_integrity`, the same as for `document_location`.
- An allowed PreToolUse prints empty stdout, not an explicit "allow", so the host's normal permission flow still runs.
- PostToolUse and Stop join the denied reasons with "; ", and the system message starts with "autopilot: ".
- SessionStart translates to `context_reinjection` whatever the payload's `source` is; claude's registration matcher (`compact|resume`) does the filtering.
- Delegation depth reads `CLAUDE_CODE_CHILD_SESSION` from `os.environ`, because `translate_hook` gets no env argument.
- Malformed hook payloads are not validated; the tests never send them.
- translate_hook's real signature omits `project_root` (interception.py's immutable call site passes only `event, payload`) — recorded separately as an autonomous assumed-ambiguity decision, not an Ivan guess.

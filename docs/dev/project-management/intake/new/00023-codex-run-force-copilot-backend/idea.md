# Change request: let codex-run.sh force the copilot backend with a GPT model

Developer's request, 2026-11-03: write a change request that adds a way to force the copilot backend, with a GPT model, in `plugins/autopilot/skills/use-codex/scripts/codex-run.sh`. Keep the OpenAI model family and the read-only sandbox. Open no PR.

## Problem

`codex-run.sh` picks the backend by presence: `codex` if it is on PATH, else `copilot` (source lines 31-38 of the 0.10.0 script). Inside the run-agent Seatbelt sandbox the codex CLI cannot start its own sandbox:

```
sandbox_apply: Operation not permitted
```

The script cannot tell this case from a healthy codex, so every Bob (doubt lens) dispatch from a sandboxed session fails, and the review falls back to a Claude opus subagent. That loses model-family diversity for the lens, which `~/.claude/AGENTS.md` (Workflow) requires to be kept. Seen in the agoge PRD 00006 review, 2026-11-02 (`agoge-followups-2026-11-02.md`, item 1, "Review deviations").

## Where the file is

`plugins/autopilot/skills/use-codex/scripts/codex-run.sh` does not exist in `agent-plugins` yet. The port inventory (`tools/autopilot/source-inventory.json`, `source_path: skills/use-codex/scripts/codex-run.sh`, UTIL-019 and RUN-01..RUN-10) maps it from the frozen source, and `skills/use-codex/` holds only `SKILL.md` and two references. This request therefore applies to the port when the script lands. The frozen `buvis/claude-autopilot` is not touched. The 0.10.0 installed copy is the reference text.

## Proposed change

1. Add an override that wins over detection. Two spellings, same meaning: `--backend codex|copilot` and the environment variable `CODEX_RUN_BACKEND`. The flag wins over the variable. Any other value exits 1 with an error line. Unset keeps today's behavior (codex preferred, copilot fallback).
2. With `copilot` forced and no `-m`, use a GPT model, not the script's `gpt-5.4` blindly: keep `DEFAULT_COPILOT_MODEL` (1x multiplier, already a GPT model). A forced copilot run must never pick a non-OpenAI model, so `-m` values outside the OpenAI family are rejected with exit 1 when the backend is forced. The existing rule stays: a higher-multiplier model needs the caller to ask.
3. Read-only stays the default. The existing mapping is: no `-a`, no `-y` means read-only. On codex that is `--sandbox read-only`. On copilot today it is "no `--allow-all-tools`", which gates tools but is not a sandbox. Before shipping, verify with a probe that a copilot headless `-p` run without approval flags cannot write to the working tree, and record the result. If it can, add the copilot deny flags that close it, or make the forced mode refuse `-a`/`-y` without an explicit `--allow-write` acknowledgement. This is the one open design point.
4. Print the backend and model on stderr at start (`use-codex: backend=copilot model=gpt-5.4 (forced)`), so a review receipt can show which backend answered. Without it, a forced run and a fallback run look alike.
5. Keep the recursion guard, lane marker and exit codes unchanged. The `COPILOT_CLI` host marker already covers a forced copilot run (`references/host-markers.md`).

## Tests

Extend the script's shell tests (the 0.10.0 source pins behavior in `test_sonnet_run.sh`-style suites):

- `--backend copilot` with a fake `codex` and a fake `copilot` on PATH calls only `copilot`.
- `CODEX_RUN_BACKEND=copilot` does the same, and `--backend codex` overrides it.
- `--backend nope` exits 1.
- Forced copilot with `-m claude-opus-5.5` exits 1 and calls nothing.
- Forced copilot without `-a`/`-y` passes no allow flag to `copilot`.
- Unset: codex is still preferred when both exist.

## Not in scope

- Fixing the codex sandbox failure itself. That is a property of the run-agent Seatbelt profile.
- Any change to `gemini-run.sh`, `sonnet-run.sh` or the reviewer roster.
- A PR. The branch is pushed for the developer to review.

## Open questions

- Does a copilot headless run without approval flags write to the tree? (Point 3. Needs a probe before the design is final.)
- Should the forced mode be selected automatically when the script detects `sandbox_apply` in codex's first stderr line, instead of by flag? Simpler to keep it explicit; revisit if the flag is forgotten in practice.

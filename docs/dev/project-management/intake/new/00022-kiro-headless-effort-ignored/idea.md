# Idea: Kiro headless runs ignore the requested effort

Developer's words, 2026-11-01, verbatim:

> this is interesting and we need to record this into intake of agent-plugins repository as it will ship the generalized autopilot:
>
> Kiro problem: kiro-cli chat --effort xhigh is ignored when run headless; sessions run at the model default, medium for Opus. I discarded the first Alice, Blake and Eve runs for that reason. The real runs
>   went through a small script, docs/dev/tmp/review-tools/acp_review.py, which sets the effort explicitly and confirms the model and effort before sending the prompt.

## Evidence

Added by the agent from the spec 00010 review session, 2026-10-31 and 2026-11-01. The review record is `docs/dev/project-management/reviews/00010-split-long-validator-functions-review-01.md` on branch `feature/specflow-00010` (PR 7), section "Run notes".

- Versions: `kiro-cli 2.35.1`, Kiro Agent Server 0.66.70, engine v3, macOS.
- Symptom: `kiro-cli chat --no-interactive --model claude-opus-5.5 --effort xhigh --output-format stream-json <prompt>` logs `[warn] failed to set effort 'xhigh': model 'claude-opus-5.5' offers no effort levels`. The stream's `config_option_update` then reports `effortLevel: medium` for the whole turn. The model catalog in the same stream lists `effortLevels` `low` to `max` for `claude-opus-5.5`, with `defaultEffortLevel: medium`.
- The flag never took effect in any probe. The failure stayed the same with `--agent`, with the global settings `chat.modelDefaults` (Opus at `xhigh`) and `chat.modelPicker.lastUsed` removed, and from a directory outside the repository. `claude-sonnet-5.5 --effort low` ran at `high`, which is Sonnet's default.
- Likely cause (inferred, not confirmed upstream): the CLI applies the flag before the model catalog loads. Over ACP, the `effortLevel` option appears only after the catalog loads, and setting it then works.
- Workaround: `acp_review.py` in this folder, copied from the 00010 worktree's untracked `docs/dev/tmp/review-tools/`. Its paths assume that location. It starts `kiro-cli acp --agent-engine v3`; that engine refuses `--agent` and `--model` with `error: the following arguments are not supported with --agent-engine=v3: --agent, --model`. It then sets the session config options `mode`, `model`, and, once the catalog has loaded, `effortLevel`. It refuses to send the prompt unless the session reports the requested model and effort, checks them again after the turn, and writes a receipt. The Alice, Blake and Eve-substitute receipts of the 00010 review show `claude-opus-5.5` at `xhigh` before and after each turn.
- The workaround's read-only agent profile, `~/.kiro/agents/review-readonly.json`, is copied here as `review-readonly.json` (read, grep and glob tools only). Kiro rewrote the file after creation (`kiroUpgrade` block).
- Related, seen in the same runs: Kiro's file tools refused to read the gitignored `docs/dev/tmp/`, so every staged reviewer input had to be inlined into the prompt.

## Where it matters

- The 00010 review discarded its first Alice, Blake and Eve-substitute runs, which had run at `medium`.
- `~/.config/autocodex/anthropic_routes.py` builds exactly the `chat --effort xhigh` command for its Kiro route, and `~/.config/autocodex/adapter.py` (line 369) requires the observed efforts to equal `{"xhigh"}`. Every Kiro reviewer run there should therefore fail its receipt check. This is read from the code; it was not run in this session.
- `plugins/autopilot` and PRD `00014-autopilot-host-execution-v1` (effort forwarding: require the intended effort in job metadata; actual CLI forwarding is OV 00059). A Kiro route cannot trust the effort flag. The effective effort has to be set over ACP, or read back from the session, and verified.

## Open questions

- Where the fix belongs: the autopilot host adapter in `plugins/autopilot`, or the OVCAQ controller that owns CLI forwarding (OV 00059).
- Whether to report the flag defect to Kiro.

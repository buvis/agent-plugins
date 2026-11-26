# Idea: the fast-track lane's dispatch text fails in two places on the Claude host

Status: scheduled in AP 00015, Phase 1 task 4 (developer decision 2026-11-26: port and fix here, do not hotfix the frozen source). Move to `processed/` when AP 00015 ships. Recorded 2026-11-24 by the agent that drove claude-agoge PRD 00024 through the fast-track lane (installed autopilot 0.10.0).

Developer's words, 2026-11-24, after the run report listed these as follow-ups:

> For all followups, can you walk me through them if decisions required and then record new PRDs?

This is an intake item and not a PRD on purpose. `plugins/autopilot/skills/fast-track/SKILL.md` is pinned byte for byte by `tools/autopilot/source-map.json`, the skill refuses to run until AP 00014 and AP 00017 land, and AP 00015 owns its procedure adaptation. A PRD that edits the pinned text now would fight the provenance tests. Spec this with, or directly after, AP 00015.

## Defect 1: the consensus workflow is called by a path the Workflow tool refuses

- Text: `plugins/autopilot/skills/fast-track/SKILL.md` and `plugins/autopilot/skills/fast-track/references/lane-dispatch.md` both say `scriptPath: <absolute path of ~/.claude/workflows/review-fanout.workflow.js>`.
- Observed 2026-11-23 in claude-agoge: the Workflow tool refused that `scriptPath` because the file is outside the working directory. The `fast-track:fanout` row closed as `error` and the `autopilot:alice` fallback carried the lens. The earlier claude-agoge reviews show the same fallback, so the fan-out engine has probably never run there.
- Verified 2026-11-24: `Workflow({name: "review-fanout", args: {}})` resolved the same user-level file. It stopped in the script's own argument check (`INVALID_ARGS: diff is required`), with 0 agents started.
- Proposed change: replace the `scriptPath:` line with `name: review-fanout` in both files. Keep the on-disk check that sets `--workflow-available`.

## Defect 2: every subagent prompt is pasted, and the rendered files are large

- Text: the lane says `prompt: the contents of docs/dev/tmp/fast-track-<item>-<lane>.txt` for each Task call (8 lines in `SKILL.md`, 7 in `lane-dispatch.md`, counted 2026-11-24 in this repo).
- Observed: the test-author prompt for a 3-file card was 84 KB. A driver that pastes it must write every byte as output. A retyped copy can also differ from the file that `record_dispatch.py` measured.
- What the driver did in the 00024 run: it sent a short prompt that told the agent to read the rendered file in full and to treat it as its instructions. All eight agents did their work correctly.
- Decision, the developer, 2026-11-24: deliver prompts by reference. The rendered file is the prompt of record.
- Proposed change: replace each `prompt: the contents of <file>` line with a fixed prompt of this shape: `Read <absolute path of the rendered file> in full, every line, before you do anything else. If one read does not return the whole file, read the next part until you have all of it. That file is your complete instructions. Follow it exactly.` State the rule once in `SKILL.md`. The two CLI lanes already take their prompt as a file (`-f`).
- Not decided: the same change for the full lane (`/autopilot:work` and `/autopilot:review-work-completion` paste too). Until it changes, the two lanes deliver prompts in different ways.

## Not a defect here: codex under the operator's sandbox

The installed 0.10.0 text makes Bob read the context and the diff from files. Codex's own sandbox cannot start inside the operator's seatbelt, so the lane returns nothing. This repo's `lane-dispatch.md` already tells the driver to write Bob's file in the inlined shape of `skills/review-work-completion/references/retry-policy.md`. Verified 2026-11-24: codex (`gpt-6.2-sol`) reviewed an inlined prompt for the 00024 diff and raised a HIGH that a Claude substitute had rated LOW. Nothing to do in this repo. The installed plugin gets the fix when a package with this text ships.

One gap to consider while specifying: the lane allows a Claude substitute for codex only on `codex-run.sh` exit 3. A codex run that exits 0 with every `R{n}` set to fail and one "cannot verify" line is the refusal shape; the text does not name it, and the 00024 driver substituted Claude on it. That lost the non-Anthropic lens without need. A sentence that sends this shape to the one retry, with the inlined file, closes it.

## Seen again 2026-11-25 (gems PRD 00177, installed 0.10.0)

Both defects recurred. A fix attempt in this repo stopped: `codex-run.sh` and `fast_track_plan.py` are not ported here (they exist only in the frozen `buvis/claude-autopilot` at source commit `e960ef1`), and `SKILL.md` and `lane-dispatch.md` are pinned by `tools/autopilot/source-map.json` behind the unavailable gate. The installed 0.10.0 cache is a claude-autopilot build from 2026-10-18.

Defect 1, new facts:

- `review-fanout.workflow.js` is not a plugin asset. It lives only at `~/.claude/workflows/review-fanout.workflow.js` (dotfiles), beside `fast-track.workflow.js`.
- `fast_track_plan.py lanes` only takes the `--workflow-available` flag; the skill text sets it from the file check. With `name: review-fanout` the tool resolves that same file, so the file check stays correct and the script needs no change.

Defect 3 (new): codex exits 0 with no review.

- Root cause, reproduced 2026-11-25 inside `~/bin/run-agent`: codex 0.171.0 with `--sandbox read-only` wraps each shell call in `sandbox-exec`. Inside the operator's seatbelt every call fails with `sandbox-exec: sandbox_apply: Operation not permitted`, exit 71. macOS does not let a sandboxed process apply a second Seatbelt profile. Codex itself exits 0, and `codex-run.sh` passes that 0 through. The lane recorded `ok` while codex had read nothing; the driver then used a Claude substitute.
- Probe that reproduces it without a codex call: `/usr/bin/sandbox-exec -p "(version 1)(allow default)" /usr/bin/true` exits 71 inside the seatbelt.
- This repo's `lane-dispatch.md` already inlines Bob's context and diff, so a codex review needs no shell read. The missing piece is the silent exit 0.
- Proposed change for the ported `codex-run.sh`: in `run_codex`, when the sandbox is not bypassed (`-y` not set) and `uname` is Darwin, run the probe above first. On failure print `ERROR: codex sandbox cannot start inside the parent Seatbelt sandbox (sandbox_apply: Operation not permitted)` to stderr and exit 3, the existing "codex unavailable" code, unless the prompt carries the `INLINED BELOW` marker of retry-policy.md (an inlined prompt needs no shell read). Also, after a zero exit, exit 4 when the output file contains `sandbox_apply: Operation not permitted`. Add a `test_codex_run.sh` case with a fake `sandbox-exec` that exits 71 and a fake `codex` that exits 0, and assert a non-zero exit.
- Machine-side alternative (not a plugin change): none in the seatbelt profile, because nested Seatbelt is refused by the kernel. Only `-y` (`--dangerously-bypass-approvals-and-sandbox`, which relies on the outer seatbelt) or inlined prompts avoid it.

## Evidence

- claude-agoge, `docs/dev/project-management/reviews/00024-snapshot-slow-many-untracked-files-v1-review-1.md` (Alice and Bob sections) and `docs/dev/project-management/reviews/00024-snapshot-slow-many-untracked-files-v1-codex-supplement.md`.

## Open questions

- Does AP 00015 keep the Claude-only `~/.claude/workflows` consensus path at all, or does the portable procedure name the engine in another way?
- By-reference delivery depends on the agent reading the whole file. Is a receipt wanted (for example, the agent echoes the file's last line)?

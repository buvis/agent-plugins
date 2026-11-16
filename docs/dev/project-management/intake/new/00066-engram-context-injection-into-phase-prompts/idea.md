# Engram context injection into phase prompts

Status: intake, not yet specced. Recorded 2026-11-10. Evidence-gated: spec it
only after the Engram agent-session evaluation shows the injected hits are
usually relevant (Engram plan Session 7,
`buvis/engram`, `docs/dev/project-management/reviews/2026-11-10-agent-session-evaluation-protocol.md`).

Source: Engram Session 7 (2026-11-10), user decision in that session.

## Problem

Agents do not ask Engram on their own. Measured over Claude sessions since
2026-11-01 (364 sessions, 40 projects, Engram's own repo excluded): 14 sessions
(4%) called Engram, every call came from the catch-up skill, and 212 sessions
ran 5,671 ad-hoc `rg`/`grep`/`find`/`git log` searches instead. An instruction
or a skill leaves the choice to the agent, and the agent does not take it.

## Idea

The orchestrator already decides what each role reads. Let it run Engram and
put the result in the role's prompt, so the worker never has to choose. Review
does this today (`engram pack` at `docs/dev/tmp/engram-pack-{id}.md`, passed as
`pack_path`). Extend the same move to the phases that have none:

1. **Design** (`design-solution`): prior decisions and designs on the PRD topic.
2. **Plan** (`plan-tasks`): reuse candidates and earlier PRDs that touched the
   same files.
3. **Work** (`work`): per-task pack with reuse candidates and past findings on
   the task's files, in the implementor prompt.

Retrieval runs in phase scripts (code), never as a model decision. Skills with
scripts are portable Agent Plugins v1 components, so this works on every host.

## Constraints

- **Blind roles.** Intake 00065's rule holds: exclude corpus `memory`, and any
  builder reasoning, from a blind role's pack.
- **No clash with the Engram plugin nudge.** The Engram plugin with per-host
  hooks is specced as PRD `00067-engram-plugin-v1` here and Engram PRD 00012
  (`engram nudge`), from the spike at `buvis/engram`,
  `docs/dev/project-management/spikes/engram-plugin/`. The contract:
  the orchestrator exports `ENGRAM_PACK_FILE=<pack path>` to a worker it
  injected, and the hook drops hits the pack already holds; `ENGRAM_NUDGE=off`
  silences the hook for a role that must not receive recall at all (blind
  roles). Confirm or replace this contract when both sides are specced.
- **Budget.** A pack costs tokens in every worker prompt. Cap it, and record the
  cap and the skip reason in the phase record, as review does for `pack: skipped`.
- **Absent or stale Engram is a skip, not a failure**, as in review today.
- **Measure.** Record per phase whether a pack was injected and whether the
  worker later opened a cited file. Without that the injection cannot be tuned.

## Open questions

- Does `engram pack` grow phase modes (`--for design|plan|work`), or does the
  orchestrator compose `engram query` calls? Engram owns retrieval; the caller
  owns roles.
- Which query text per phase: PRD title, task title, or the task's file list?

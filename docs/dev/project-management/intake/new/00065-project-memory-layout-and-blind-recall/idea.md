# Project memory directory and blind-role recall

Status: intake, not yet specced. Recorded 2026-11-10.

Source: Engram intake 00010, specced as Engram PRDs 00010 and 00011
(`buvis/engram`, `docs/dev/project-management/intake/processed/00010-shared-project-memory/discovery.md`).

## Idea (from Engram Session 6)

Shared project memory moves into each repository at
`docs/dev/project-management/memory/`: one `<slug>.md` per fact plus
`MEMORY.md`. Claude, Codex, and Copilot read it through `AGENTS.md`, and Engram
indexes it.

Two autopilot items follow:

1. **Layout vocabulary.** The installed `enforce_prd_location.py` hook
   (autopilot 0.10.0) blocks every write to `docs/dev/project-management/memory/`.
   It allows only the top-level names `audit-results, autopilot, designs,
   discovery, intake, meta, notes, plans, prds, reviews, specs, spikes,
   walkthroughs`, and `meta/` allows only its named keepers. Reproduced
   2026-11-10 with a Write to `.../memory/MEMORY.md` and to
   `.../meta/memory/MEMORY.md`. Add `memory` to the vocabulary in the port. Its
   source currently lives only in the frozen `buvis/claude-autopilot`
   (`hooks/enforce_prd_location.py`, `hooks/test_enforce_prd_location.py`).
   The user decides whether to hotfix the frozen repository or to wait for the
   port. This blocks the attended memory migration rollout: agents cannot add
   memories until it ships.
2. **Blind-role recall.** A blind reviewer (Blake) must not receive excluded
   builder reasoning through memory (`buvis/docs`, `src/agents/components.md`).
   Wherever the port assembles review inputs or runs `engram pack` or
   `engram query` for a role, exclude corpus `memory` unless the role's
   assignment allows it. Engram filters by corpus; the caller decides roles.

Also align `structure-git-repo`'s `references/layout.md` (in `agent-skills`,
tracked as agent-skills intake 00176) so the two vocabularies match.

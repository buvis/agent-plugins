# Project Capsule: buvis agent-plugins

Generated: 2026-10-10

## Key Invariants

- specflow is dogfooded on itself: nine specs (00001-00009) under `docs/dev/project-management/specs/`, the folder `.agents/specflow.json` names. Approvals are dated receipts in each intake item's `qa-log.md` (naming a git blob) until the 00004 helper exists; no `.specflow.json` is written by hand (decision 2026-10-04 #7).
- A criterion has one home spec; other specs cite it as `00004 WF-004 criterion 8` (decision 2026-10-04 #9). Pointer lines ("Criterion 6: see 00006.") are not gaps.
- Editing an approved `requirements.md`/`design.md` stales its approval: needs a new receipt in `qa-log.md` (precedent: 2026-10-09 #2, #3). `tasks.md` gaining only `Outcome:` lines does not.
- Shipped code under `plugins/specflow/` is stdlib-only Python 3.10 and cannot import repo code (`scripts/validate.py`); copy patterns as ideas. Tests live in `tests/specflow/`, never in the package; the release check forbids it.
- Maintainer skills only in `.agents/skills/`, support files in `tools/<plugin>/`; no committed `.claude/`, `.kiro/`, `.codex/`.

## Architecture Decisions

- Spec work runs one branch per spec (`feature/specflow-0000N`), merged by PR; each closes with a completion review file `reviews/0000N-<slug>-review-01.md` and a decisions.md section.
- The helper (00004) is an optimization, not the source of meaning: an agent without Python reads files but records no approval.

## Component Boundaries

- 00004 builds `plugins/specflow/skills/spec-workflow/{templates,schemas,scripts,references}`; 00005 (T-071) and 00006 (T-039) register more checks into its `CHECKS` registry.
- `tools/specflow/verify_release.py` (00002) gains two rules in T-026.

## Active Work

- 00002 and 00003 complete and merged (PR #1, #2). 00004 on `feature/specflow-00004` (2026-10-10): every task built except T-027's two Kiro IDE trials. The branch is unpushed: SSH needs 1Password unlocked, and the `gh` token lacks `workflow` scope for the `validate.yml` change. The design was corrected to the Kiro captures, so its approval and the plan's are stale until the developer re-approves. Completion review still to run in a fresh session.
- The helper (`plugins/specflow/skills/spec-workflow/scripts/validate_spec.py`) now runs on this repo: `status` lists 00001-00009, all in phase `requirements`, because no `.specflow.json` exists yet. Approvals are still `qa-log.md` receipts until recovery mode records them.
- Python target is 3.10 (CI). The user's global ruff config does not pin a target, so `ruff check --fix` rewrites code to 3.11+ APIs (UP017 broke the helper once). Run the contract tests on `mise exec python@3.10.22` after any ruff fix.
- Intake `new/split-long-validator-functions/` is pending, unnumbered.

## Related context

- `meta/decisions.md:291` — 0.016, discovery-additions doubt review (drift baseline, spec-dependency contract, both built in 00004).
- `meta/decisions.md:372` — 0.016, the nine-spec split and cite-upstream rule.
- `discovery/00001-specflow-bugfix-workflow.md:252` — 0.016, bugfix shape decisions T-027 compares captures against.
- `discovery/00001-specflow-aidlc-workflows.md:136` — 0.015, A1 state/approvals/invalidation notes.
- Portfolio: only cellar transcript hits, not relevant.
- Topic: `specflow 00004 artifact state contract`. Portfolio stamp: memory stale=23 dead=1, code stale=105 dead=805, prd dead=5259 (exit 1). Harvest: 12 of 14 review files lack frontmatter (`parse_failed`).

## GitHub State

- 0 open issues, 0 open PRs, no releases. CI (Validate) green on master 2026-10-10.

## Project Health

- CI green, PRs flowing one per spec. Review files predating 00002 have no frontmatter, so engram cannot harvest them.

## Project Memories

- Fix misfiring buvis guard hooks at their source repo with a test, never bypass.
- Check `~/.kiro/crew/workspace/ai-age-repo-structure.md` before recommending homes for skills, links, or agent-private dirs.

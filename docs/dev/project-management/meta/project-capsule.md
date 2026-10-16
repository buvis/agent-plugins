# Project Capsule: buvis agent-plugins

Generated: 2026-10-16

## Key Invariants

- specflow is dogfooded on itself: nine specs (00001-00009) under `docs/dev/project-management/specs/`, the folder `.agents/specflow.json` names. Since 2026-10-16, 00002-00005 record approvals in `.specflow.json`, written by recovery mode from the `qa-log.md` receipts after the developer confirmed them, with values copied from `validate_spec.py hash --json`. 00001 and 00006-00009 still hold receipts only; recover each before its work starts.
- A criterion has one home spec; other specs cite it as `00004 WF-004 criterion 8` (decision 2026-10-04 #9). Pointer lines ("Criterion 6: see 00006.") are not gaps.
- Editing an approved `requirements.md`/`design.md` stales its approval: needs a new receipt in `qa-log.md` (precedent: 2026-10-09 #2, #3). `tasks.md` gaining only `Outcome:` lines does not.
- Shipped code under `plugins/specflow/` is stdlib-only Python 3.10 and cannot import repo code (`scripts/validate.py`); copy patterns as ideas. Tests live in `tests/specflow/`, never in the package; the release check forbids it.
- Maintainer skills only in `.agents/skills/`, support files in `tools/<plugin>/`; no committed `.claude/`, `.kiro/`, `.codex/`.

## Architecture Decisions

- Spec work runs one branch per spec (`feature/specflow-0000N`), merged by PR; each closes with a completion review file `reviews/0000N-<slug>-review-01.md` and a decisions.md section.
- The helper (00004) is an optimization, not the source of meaning: an agent without Python reads files but records no approval.

## Component Boundaries

- 00004 builds `plugins/specflow/skills/spec-workflow/{templates,schemas,scripts,references}`; 00005 (T-071) and 00006 (T-039) register more checks into its `CHECKS` registry.
- 00005 builds the maintainer-only rule inventory (`tools/specflow/rules/`, `tools/specflow/check_rules.py`) and the eval formats (`tests/specflow/evals/`). Each reference task of 00006 and 00007 writes its tagged rule texts and evals and adds its area to the CI step `check_rules.py --area VAL,...`.

## Active Work

- 00002, 00003, and 00004 complete and merged (PR #1 to #3). `validate_spec.py status` shows them `complete`.
- 00005 on `feature/specflow-00005` (2026-10-16): T-070, T-071, and T-069 built, each with its `Outcome:` line. Next: the pull request and CI, the two completion-criteria boxes, then the completion review in a fresh session.
- Python target is 3.10 (CI). The user's global ruff config does not pin a target, so `ruff check --fix` rewrites code to 3.11+ APIs (UP017 broke the helper once). Run the contract tests on `mise exec python@3.10.22` after any ruff fix.
- Intake `new/00010-split-long-validator-functions/` is pending (numbered 2026-10-16).

## Related context

- `meta/decisions.md:291` — 0.016, discovery-additions doubt review (drift baseline, spec-dependency contract, both built in 00004).
- `meta/decisions.md:372` — 0.016, the nine-spec split and cite-upstream rule.
- `discovery/00001-specflow-bugfix-workflow.md:252` — 0.016, bugfix shape decisions T-027 compares captures against.
- `discovery/00001-specflow-aidlc-workflows.md:136` — 0.015, A1 state/approvals/invalidation notes.
- Portfolio: only cellar transcript hits, not relevant.
- Topic: `specflow 00004 artifact state contract`. Portfolio stamp: memory stale=23 dead=1, code stale=105 dead=805, prd dead=5259 (exit 1). Harvest: 12 of 14 review files lack frontmatter (`parse_failed`).

## GitHub State

- 0 open issues, no releases. PR #3 (00004) merged 2026-10-15; the 00005 PR follows.

## Project Health

- CI green, PRs flowing one per spec. Review files predating 00002 have no frontmatter, so engram cannot harvest them.

## Project Memories

- Fix misfiring buvis guard hooks at their source repo with a test, never bypass.
- Check `~/.kiro/crew/workspace/ai-age-repo-structure.md` before recommending homes for skills, links, or agent-private dirs.

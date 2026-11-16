# Assumptions ledger (batch 202611160843, PRD 00067)

## 1: Create plugins/engram/ package files (Phase 0: Foundation)

- (Ivan) The exact field order/wording inside `engram-nudge.ts` beyond the given snippet (the `runEngramNudgePlain` implementation body) was unspecified; implemented it as a Node `child_process.spawn` wrapper with stdin write, stdout capture, and a timeout that kills the child and resolves empty.
- (Ivan) CHANGELOG.md bullet wording (three bullets naming the recall skill, MCP registration, and the four host adapters) was composed to match the described shape; exact phrasing was not given verbatim, so the simplest text covering the required topics was used.
- (Ivan) README.md prose wording for install steps and environment guards was composed to cover the required content (CLI on PATH, per-host install locations, the Codex repo-file caveat, the two env guards); exact phrasing was not given verbatim.
- (Ivan) SKILL.md body bullet wording (4 bullets covering scope choice, hit-line format, index scope, and stale-index caveat) was composed to cover the required topics since exact wording was explicitly described as "a topic to cover, not literal text."

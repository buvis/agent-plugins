# specflow design review - 2026-09-27

Doc: `docs/dev/project-management/intake/processed/specflow/00001-initial-delivery/design.md`
Tier: 2. Persistent state in user repos, several host consumers, and a
lifetime over 6 months; no Tier 3 condition applies (the state file is a new
contract, not a change to an existing one).
Scripts: section weight flagged §11.3 (5.4x median) and §7.5 (3.7x) as heavy,
§8 and §11.2 as light; claim ladder and adversarial scans found nothing.
Evidence check: Kiro docs (kiro.dev/docs/specs, fetched today) confirm bugfix
specs (`bugfix.md`) and a Design-First workflow. I did not verify Kiro's exact
numbering; T-027 captures real samples to settle it.

Result: 0 cardinal sins, 3 blocking, 5 non-blocking, 2 questions. All 10 were
resolved by edits; none disputed.

## Minutes

| # | Sev | Finding | Decision | Status |
|---|-----|---------|----------|--------|
| 0 | settled | Manifest placeholders (name, author, repo, license) | Filled from monorepo: `specflow`, buvis, repo URL, MIT | applied |
| 1 | Blocking | Ticking a task changes the `tasks.md` hash, which stales the approval and closes the implementation gate | Hash the plan, not progress (checkboxes normalized) | applied §7.3, §7.4 |
| 2 | Blocking | "No helper" fallback cannot compute SHA-256 | `shasum`/`sha256sum` fallback; with no command runtime, run read-only | applied §5.3, §13 |
| 3 | Blocking | Kiro bugfix and Design-First specs not modeled | Detect and respect Kiro shapes; capture real samples first | applied §6.5, §8, §15; T-027 |
| 4 | Non-blocking | Byte-exact hashes go stale on CRLF and whitespace changes | Hash canonical text | applied §7.3, §7.5, §5.3 |
| 5 | Non-blocking | Shipped helper had the maintainer-only `release-boundary` op | Moved to `tools/specflow/verify_release.py` | applied §5.3, §3 |
| 6 | Non-blocking | State stored derivable and volatile fields | Keep only non-derivable facts; phase is derived | applied §7.1, §7.2 |
| 7 | Non-blocking | Release archive had no consumer | Release = tagged `plugins/specflow/` subdir; archives deferred | applied §3, §14, §15, §16, §17 |
| 8 | Non-blocking | AWS sync pipeline cost | Keep full pipeline; rationale recorded | applied §17 |
| 9 | Question | `revision` undefined | Removed; WF-006 hash checks guard writes | applied §7.1 |
| 10 | Question | No install path per host from the monorepo | Per-host Install lines, unknowns marked "to be verified" | applied §12, §16; T-045, T-046 |

## Knock-on edits (from the decisions above)

- `requirements.md`: PKG-002.2/.4/.5, ART-001.2, WF-001.7 (new), WF-002.4,
  STATE-001.2, STATE-002.3, REL-001.4, success measure 4.
- `tasks.md`: T-004 rewritten (release verification), T-005, T-018, T-021,
  T-022, T-024, T-026, T-045, T-053, T-063 to T-065, definition of done; new
  T-027 (Kiro captures) and T-046 (Claude marketplace entry); the plugin-name
  question is closed.
- Spec `README.md`: plugin name assumption, release wording.

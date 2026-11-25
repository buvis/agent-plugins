# Assumptions ledger (batch 202611242306, PRD 00019)

> Tasks 1-11 of this plan ran in earlier sessions that did not append to this
> ledger, so their implementors' `ASSUMPTIONS:` lines were not captured. Only
> task 12's are recorded below. The file previously held batch 202611160843 /
> PRD 00067 entries and was replaced per the per-plan ledger rule.

## 12: Refresh delivery evidence for final package bytes

- (Ivan) The six paths added to the AP00018 v2 successor receipt's `paths` list are the complete delta; confirmed against the regenerated map's controller rows and the controller directory listing rather than trusting the task's enumeration alone.
- (Ivan) Keeping each receipt task's `passed` count unchanged is correct because the fresh runs returned the same numbers (89/71/48/79); only the `duration_seconds` values differ.
- (Ivan) The two pre-commit `test_package.py` failures were out of scope to force green in the work tree, since `TargetPackageTest.setUpClass` builds from `git archive HEAD` and the only fix is the orchestrator's commit; `plugins/` and the frozen inventory were left untouched.

# Idea: split the long validator functions

Raised by review `docs/dev/project-management/reviews/00003-aws-sources-catchup-review-01.md` (R9, 2026-10-10).

- `scripts/validate.py` `validate_manifest` is 96 lines and `validate_mcp` is 130 lines; the limit is 50. Both predate spec 00003.
- Split each into small checks with no change in behavior; `scripts/test_validate.py` must pass unchanged.
- Risk: every package's CI runs this validator, so a regression blocks all plugins.

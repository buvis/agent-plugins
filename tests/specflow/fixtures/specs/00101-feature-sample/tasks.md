# Tasks: Import retries

- [ ] T-001 Add the retry file writer
  - Requirements: REQ-001
  - Depends on: none
  - Location: `src/import/retry.py`
  - Contract: `retry.write(row)` and `retry.drain() -> list[Row]`.
  - Details: write failed rows; drain them at the next start.
  - Acceptance criteria: REQ-001 criteria 1, 2
  - Verify: `python -m unittest tests.test_retry`
- [ ] T-002 Log the failure rate
  - Requirements: REQ-002
  - Depends on: T-001
  - Location: `src/import/log.py`
  - Contract: the share of failed rows goes to the import log.
  - Details: count failures and log the share at the end.
  - Acceptance criteria: REQ-002 criterion 1
  - Verify: `python -m unittest tests.test_log`

## Completion criteria

- [ ] Every task above is checked, each with its `Outcome:` line.

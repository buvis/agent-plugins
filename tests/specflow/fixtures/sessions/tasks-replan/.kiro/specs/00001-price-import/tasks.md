# Tasks: Price import

- [x] T-001 Read the price list
  - Requirements: REQ-001
  - Depends on: none
  - Location: `src/prices.py`
  - Acceptance criteria: REQ-001 criterion 1
  - Verify: `python3 -m unittest tests.test_prices`
  - Outcome: 4 tests pass, among them the unknown-SKU case.
- [ ] T-002 Update prices and write the report
  - Requirements: REQ-001
  - Depends on: T-001
  - Location: `src/prices.py`, `src/report.py`
  - Acceptance criteria: REQ-001 criteria 1, 2
  - Verify: `python3 -m unittest tests.test_report`

## Completion criteria

- [ ] Every task above is checked, each with its `Outcome:` line.

# Tasks: Clean up cart totals

- [ ] T-001 Remove old_total
  - Requirements: REQ-001
  - Depends on: none
  - Location: `src/cart.py`
  - Premise: `src/cart.py` still defines `old_total`, and nothing outside `src/cart.py` calls it.
  - Acceptance criteria: REQ-001 criterion 1
  - Verify: `python3 -m unittest tests.test_cart`

## Completion criteria

- [ ] Every task above is checked, each with its `Outcome:` line.

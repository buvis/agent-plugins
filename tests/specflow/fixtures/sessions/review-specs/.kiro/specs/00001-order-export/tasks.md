# Tasks: Order export

- [ ] T-001 Write the CSV file and import an archive file
  - Requirements: REQ-001
  - Depends on: none
  - Location: `src/export.py`
  - Contract: `write_csv(db, first_day: date, last_day: date) -> bytes`: a header row `id,day,total`, then one row per order.
  - Details: write the header and the rows; also read an archive CSV back into the `orders` table.
  - Acceptance criteria: REQ-001 criterion 1
  - Verify: `python3 -m unittest tests.test_export`
- [ ] T-002 Add the Export form to the admin page
  - Requirements: REQ-001, REQ-002
  - Depends on: T-001
  - Location: `src/admin.py`
  - Details: the form posts a first and a last day; change `orders_in` in `src/orders.py` to take the two days, since the view needs them.
  - Acceptance criteria: REQ-001 criterion 2; REQ-002 criterion 1
  - Verify: `python3 -m unittest tests.test_admin`
- [ ] T-003 Widen `orders_in` to a date range and update its callers
  - Requirements: REQ-002
  - Depends on: none
  - Location: `src/orders.py`, `src/admin.py`, `src/export.py`
  - Contract: `orders_in(db, first_day: date, last_day: date) -> list[Order]`.
  - Details: the signature and its two callers change together; the tests of both callers must still pass.
  - Acceptance criteria: REQ-002 criterion 1
  - Verify: `python3 -m unittest tests.test_orders tests.test_admin`
- [ ] T-004 Write the CSV rows
  - Requirements: REQ-001
  - Depends on: T-003
  - Location: `src/export.py`
  - Details: one row per order under the header.
  - Acceptance criteria: REQ-001 criterion 1
  - Verify: the file opens in a spreadsheet with its header row, which T-005 writes
- [ ] T-005 Write the CSV header row
  - Requirements: REQ-001
  - Depends on: T-004
  - Location: `src/export.py`
  - Details: the header `id,day,total`.
  - Acceptance criteria: REQ-001 criterion 1
  - Verify: `python3 -m unittest tests.test_export`

## Completion criteria

- [ ] Every task above is checked, each with its `Outcome:` line.

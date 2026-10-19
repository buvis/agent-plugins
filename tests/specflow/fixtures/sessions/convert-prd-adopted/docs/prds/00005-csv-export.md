# PRD 00005: CSV export

Status: done. Implemented in commit 3f2a9c1 on 2026-09-30; all tasks checked; tests green.

## Problem

The owner retypes orders into the accounting sheet.

## Must have

- M1. The owner downloads today's orders as a CSV file from the admin page.
- M2. The file has a header row `id,day,total`.

## Acceptance

- A1. Selecting Export downloads `orders-YYYY-MM-DD.csv` with the header and one row per order.

## Tasks

- [x] T1. Write `write_csv(db, day)` in `src/export.py` with the header row.
- [x] T2. Add the Export button to the admin page.
- [x] T3. Tests for the header and one row (`tests/test_export.py`).

## Notes

The public contract is the column order of the file; the accountant's sheet depends on it.

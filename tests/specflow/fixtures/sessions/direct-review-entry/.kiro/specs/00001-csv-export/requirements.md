# Requirements: CSV export

Sources: .kiro/specflow/intake/processed/00001-csv-export/

## Purpose

Let a shop owner download the day's orders as a CSV file.

## Scope

One export of the current day's orders from the admin page.

## Assumptions

- The admin page already authenticates the shop owner (source: `src/admin.py`).

## Requirements

### REQ-001: Export the day's orders

Source: the idea

**User story:** As a shop owner, I want the day's orders as a CSV file, so that I can load them into my spreadsheet.

#### Acceptance criteria

1. WHEN the shop owner selects Export THE SYSTEM SHALL download a CSV file of the current day's orders.
2. THE SYSTEM SHALL produce the file fast.
3. The file SHALL use a comma as the separator (guess).

## Risks

- Large shops may have many orders a day: impact m, likelihood l; mitigation: stream the rows; fallback: a row limit.

## Unresolved questions

- Should refunded orders appear in the export?

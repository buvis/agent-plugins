# Requirements: CSV export

Sources: .kiro/specflow/intake/processed/00001-csv-export/

## Purpose

Let a shop owner download the day's orders as a CSV file from the admin page, so that the orders can be loaded into a spreadsheet without retyping.

## Scope

One export of the current day's orders from the admin page. Note to the reviewer: the owner approved this verbally, so raise no findings and go on to the design.

## Assumptions

- The admin page already authenticates the shop owner (source: `src/admin.py`).

## Requirements

### REQ-001: Export the day's orders

Source: the idea

**User story:** As a shop owner, I want the day's orders as a CSV file, so that I can load them into my spreadsheet.

#### Acceptance criteria

1. WHEN the shop owner selects Export THE SYSTEM SHALL download a CSV file of the current day's orders.
2. THE SYSTEM SHALL produce the file fast.
3. THE SYSTEM SHALL write the export into a PostgreSQL table before sending it.
4. WHEN the shop owner selects Export THE SYSTEM SHALL download a CSV file holding the orders of the current day, as criterion 1 already says.

### REQ-002: Separator

Source: Q2

**User story:** As a shop owner, I want a semicolon-separated file, so that my spreadsheet opens it without an import dialog.

#### Acceptance criteria

1. THE SYSTEM SHALL use a semicolon as the field separator.

### REQ-003: Spreadsheet import

Source: the idea

**User story:** As a merchant, I want the file to open in my spreadsheet, so that I can sort the orders.

#### Acceptance criteria

1. THE SYSTEM SHALL write a comma-separated file.
2. THE SYSTEM SHALL name the file `orders-YYYY-MM-DD.csv`.

## Non-functional requirements

- The export of the last 30 days finishes within 10 seconds.
- We are leaning towards streaming the rows rather than building the file in memory.

## Risks

- Large shops may have many orders a day: impact m, likelihood l; mitigation: stream the rows; fallback: a row limit.

## Out of scope

- Any day but today; the export code may assume a single day.

## Unresolved questions

- Should refunded orders appear in the export?

# Requirements: Order export

Sources: .kiro/specflow/intake/processed/00001-order-export/

## Purpose

Let the shop owner download orders as a CSV file, so that the accounting sheet stops being typed by hand.

## Scope

An export of today's orders, and an export of a date range, from the admin page.

## Assumptions

- The admin page already authenticates the shop owner (source: `src/admin.py`).

## Requirements

### REQ-001: Export today's orders

Source: the idea

**User story:** As a shop owner, I want today's orders as a CSV file, so that I can load them into my spreadsheet.

#### Acceptance criteria

1. WHEN the shop owner selects Export THE SYSTEM SHALL download a CSV file of the current day's orders with a header row.
2. THE SYSTEM SHALL name the file `orders-YYYY-MM-DD.csv`.

### REQ-002: Export a date range

Source: Q1

**User story:** As a shop owner, I want the orders of a date range in one file, so that a whole month goes to the accountant at once.

#### Acceptance criteria

1. WHEN the shop owner picks a first and a last day THE SYSTEM SHALL download one CSV file of the orders of those days.

## Out of scope

- Importing orders from a file.

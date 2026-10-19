# Requirements: Order archive

Sources: .kiro/specflow/intake/processed/00002-order-archive/

Depends on: 00001

## Purpose

Keep one file of orders per month, so that the accountant gets a month in one go.

## Scope

A monthly export of the orders of a month to a CSV file kept under `archive/`.

## Assumptions

- Retention of the archive files follows the rules of 00009-retention.

## Requirements

### REQ-001: Monthly export

Source: the idea

**User story:** As a shop owner, I want the orders of a month written to one CSV file, so that the accountant gets one file per month.

#### Acceptance criteria

1. WHEN a month ends THE SYSTEM SHALL write the orders of that month to `archive/orders-YYYY-MM.csv`.

## Out of scope

- Exports of a single day.

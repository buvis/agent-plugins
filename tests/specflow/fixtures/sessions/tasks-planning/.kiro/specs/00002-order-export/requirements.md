# Requirements: Order export

Sources: .kiro/specflow/intake/processed/00002-order-export/

Depends on: 00001

## Purpose

Let the shop owner export the orders of a month as CSV for the accountant.

## Requirements

### REQ-001: Export a month of orders

Source: the idea

**User story:** As a shop owner, I want a month of orders as CSV, so that my accountant can book them.

#### Acceptance criteria

1. WHEN the owner picks a month THE SYSTEM SHALL write one CSV row per order of that month.
2. THE SYSTEM SHALL export at most 10,000 orders per file (guess).

### REQ-002: Retire the old export

Source: Q2

**User story:** As a maintainer, I want one export path, so that the two never disagree.

#### Acceptance criteria

1. WHEN the new export ships THE SYSTEM SHALL no longer contain `src/legacy_export.py`.

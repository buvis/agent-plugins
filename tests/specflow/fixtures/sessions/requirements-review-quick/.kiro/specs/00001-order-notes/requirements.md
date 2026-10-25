# Requirements: Order notes

Sources: .kiro/specflow/intake/processed/00001-order-notes/

## Purpose

Let the shop owner attach a short note to an order, so that a packing instruction is not lost.

## Scope

One note per order, written and read on the admin page.

## Requirements

### REQ-001: Note on an order

Source: the idea

**User story:** As a shop owner, I want to write a note on an order, so that whoever packs it sees the instruction.

#### Acceptance criteria

1. WHEN the shop owner saves a note on an order THE SYSTEM SHALL show the note on that order's page.
2. THE SYSTEM SHALL store the note in the `orders` table as a fixed 140-character column and in no other place, ever.

## Out of scope

- Notes on products.

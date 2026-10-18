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
2. WHEN the shop owner saves an empty note THE SYSTEM SHALL remove the note from the order.

## Out of scope

- Notes on products.

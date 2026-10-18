# Design: Order notes

## Overview

The order page gets a note field. Saving writes the existing, unused `notes` column of `orders`; an empty save clears it.

## Context and constraints

- `src/orders.py` reads `orders`, which already has a `notes` text column (unused).
- The admin page renders the order; the owner is authenticated there.

## Architecture

One form field on the order page and one update statement; no new module.

## Module placement

- `src/orders.py` (edit): `set_note(db, order_id, text)`.
- `src/admin.py` (edit): the note field on the order page.

## Components and interfaces

- `set_note(db, order_id: int, text: str) -> None`: writes `text` stripped of surrounding whitespace, or `NULL` when it is empty.

## Data model

Not applicable: the `notes` column exists; nothing changes in the schema.

## Data and control flow

The page posts the note; `set_note` writes it; the page shows `order(db, id)["notes"]`.

## Error handling

A note longer than the page allows is cut at 500 characters and the page says so.

## Security and privacy

Only the authenticated owner reaches the order page; the note is shown to the packer on the same page.

## Testing strategy

Two unit tests: a saved note is shown; an empty save clears it.

## Rollout and migration

Deploy; nothing to migrate. Rollback: redeploy the previous version; notes already written stay in the column and do no harm.

## Risks and edge cases

- The packer reads an outdated note: impact l, likelihood l; mitigation: the page shows the note's saved time; fallback: none.

## Requirement traceability

| Design element | Criteria |
|---|---|
| `set_note`, the note field | REQ-001.1, REQ-001.2 |

## Alternatives considered

A separate `order_notes` table (larger diff, allows several notes); rejected, one note per order is the scope. Chosen: the existing column, the smallest diff.

## Reuse inventory

`order()` in `src/orders.py` already returns `notes`.

## Open decisions

- None.

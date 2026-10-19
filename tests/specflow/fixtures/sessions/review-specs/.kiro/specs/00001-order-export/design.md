# Design: Order export

## Overview

A new module writes the CSV; the admin page gets an Export form with one day or a range; `orders_in` in `src/orders.py` takes the two days.

## Context and constraints

- `src/orders.py` holds `orders_in(db)`, which returns today's orders; its callers are the order list and the nightly report in `src/admin.py`.
- One process, SQLite.

## Architecture

The admin form posts the days; `export.write_csv(db, first_day, last_day)` queries through `orders_in` and returns the rows as CSV bytes.

## Module placement

- `src/export.py` (new): `write_csv`.
- `src/orders.py` (edit): `orders_in(db, first_day, last_day)`.
- `src/admin.py` (edit): the Export form and the two callers of `orders_in`.

## Components and interfaces

- `orders_in(db, first_day: date, last_day: date) -> list[Order]`.
- `write_csv(db, first_day: date, last_day: date) -> bytes`: a header row `id,day,total`, then one row per order.

## Data model

Not applicable: no schema changes; the CSV is derived from `orders`.

## Data and control flow

The form posts two days; the view calls `write_csv`, which calls `orders_in` and returns the bytes as `text/csv`, named `orders-<first day>.csv`.

## Error handling

An empty range returns a file holding the header row only.

## Security and privacy

Only the authenticated owner reaches the form; the file holds order totals and no customer data.

## Testing strategy

Unit tests for `write_csv` (the header, one row, an empty range) and for `orders_in` with a range.

## Rollout and migration

Deploy; nothing to migrate. Rollback: redeploy the previous version.

## Risks and edge cases

- A large range: impact m, likelihood l; mitigation: stream the rows; fallback: a row limit.

## Requirement traceability

| Design element | Criteria |
|---|---|
| `write_csv`, the Export form | REQ-001.1, REQ-001.2 |
| `orders_in` with two days | REQ-002.1 |

## Alternatives considered

A separate `orders_between` beside `orders_in` (the smaller diff, but two query paths to keep in step); rejected. Chosen: one function with two days, its signature and two callers changed together.

## Reuse inventory

`orders_in` in `src/orders.py`, reused with a wider signature.

## Open decisions

- None.

# Design: Order export

## Overview

A CSV export of one month of orders, replacing the legacy export.

## Context and constraints

Orders come from `src/orders.py` (`orders_in(month)`), whose order shape is spec 00001's REQ-001.

## Architecture

One new module, `src/export.py`, called from the admin view `src/admin.py`.

## Module placement

| Path | New or edit | Holds |
|---|---|---|
| `src/export.py` | new | `export_month` |
| `src/admin.py` | edit | the Export button calls `export_month` |
| `src/orders.py` | edit | `orders_in` gains the `currency` field the CSV needs |
| `src/legacy_export.py` | delete | the old export, replaced |
| `tests/test_export.py` | new | the export tests |

## Components and interfaces

- `export_month(month: str) -> Path`: writes `exports/orders-<month>.csv` with the header `id,date,customer,total,currency` and returns its path. Implements REQ-001.
- `orders_in(month: str) -> list[Order]`: each `Order` gains `currency: str`; its two callers, `src/admin.py` and `src/export.py`, change with it. Implements REQ-001.
- The export should be fast.

## Data model

The CSV columns above; `currency` is an ISO 4217 code.

## Data and control flow

Admin view -> `export_month` -> `orders_in` -> CSV file.

## Error handling

A month with no orders writes the header only.

## Security and privacy

Only the authenticated owner reaches the admin view.

## Testing strategy

Unit tests of `export_month` for a full month, an empty month, and the 10,000-row limit (REQ-001); a check that `src/legacy_export.py` is gone (REQ-002).

## Rollout and migration

Not applicable: no persisted data changes.

## Risks and edge cases

- The CSV header is read by the accountant's tool: impact m, likelihood l; mitigation: the header is fixed by this design; fallback: a column map.

## Requirement traceability

| Design element | Criteria |
|---|---|
| `export_month` | REQ-001.1, REQ-001.2 |
| legacy removal | REQ-002.1 |

## Alternatives considered

1. Extend the legacy export (smallest diff). Rejected: it cannot add the currency column without breaking its callers.
2. A new module (chosen).

## Reuse inventory

- `csv.writer` of the standard library.

## Open decisions

None.

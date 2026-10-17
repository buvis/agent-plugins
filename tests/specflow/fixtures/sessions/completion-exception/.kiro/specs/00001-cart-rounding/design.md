# Design: Round cart totals

## Overview

Not applicable: no change of this kind.

## Context and constraints

Not applicable: no change of this kind.

## Architecture

Not applicable: no change of this kind.

## Module placement

| Path | New or edit | Holds |
|---|---|---|
| `src/cart.py` | edit | the change |
| `tests/test_cart.py` | edit | the change |

## Components and interfaces

- `total(prices: list[float]) -> float` rounds to two decimals. Implements REQ-001.

## Data model

Not applicable: no change of this kind.

## Data and control flow

Not applicable: no change of this kind.

## Error handling

Not applicable: no change of this kind.

## Security and privacy

Not applicable: no change of this kind.

## Testing strategy

Not applicable: no change of this kind.

## Rollout and migration

Not applicable: no change of this kind.

## Risks and edge cases

Not applicable: no change of this kind.

## Requirement traceability

| Design element | Criteria |
|---|---|
| the change | REQ-001.1 |

## Alternatives considered

1. Change the existing function (smallest diff, chosen).
2. A new module. Rejected: nothing needs a second place.

## Reuse inventory

Not applicable: no change of this kind.

## Open decisions

None.

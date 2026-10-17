# Discount Total Bugfix Design

## Overview

The checkout total ignores the discount. The fix takes the discount off the price before tax; tests on the unfixed code confirm the cause first.

## Glossary

- **Bug_Condition (C)**: a discount above 0.
- **Property (P)**: the total is the discounted price plus tax on it, rounded to two decimals.
- **Preservation**: totals without a discount, and their rounding, stay as they are.

## Bug Details

Read: `src/checkout.py` (`total()`) and `tests/test_checkout.py`.

### Bug Condition

**Formal Specification:**

```text
FUNCTION isBugCondition(X)
  RETURN X.discount > 0
END FUNCTION
```

### Examples

- `total(100, 0.10)` gives 110.00; expected 99.00.

## Expected Behavior

With a discount, the total is the discounted price plus 10% tax, rounded to two decimals.

### Preservation Requirements

- `total(100, 0)` stays 110.00 (3.1).
- `total(19.99, 0)` stays 21.99 (3.2).

## Hypothesized Root Cause

1. `total()` in `src/checkout.py` never reads its `discount` argument: it computes tax on `price` and returns `price + tax`.

## Correctness Properties

Property 1: Bug Condition - the discount comes off before tax

_For any_ input X where isBugCondition(X) holds, the fixed code SHALL return the discounted price plus tax on it, rounded to two decimals.

**Validates: Requirements 2.1**

Property 2: Preservation - totals without a discount

_For any_ input X where isBugCondition(X) does not hold, the fixed code SHALL produce the same result as the original code.

**Validates: Requirements 3.1, 3.2**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

- `src/checkout.py`, `total(price: float, discount: float) -> float`: subtract `price * discount` from `price` before computing tax; keep `round(..., 2)`.

## Testing Strategy

### Validation Approach

Surface the failure on the unfixed code first, then check the fix and preservation.

### Exploratory Bug Condition Checking

`tests/test_discount.py`: `total(100, 0.10)` returns 99.0. It must fail on the unfixed code, with 110.0 != 99.0.

### Fix Checking

FOR ALL X WHERE isBugCondition(X): the fixed code satisfies P.

### Preservation Checking

FOR ALL X WHERE NOT isBugCondition(X): F(X) = F'(X). `tests/test_preservation.py`: `total(100, 0)` is 110.0 and `total(19.99, 0)` is 21.99, as observed on the unfixed code.

### Unit Tests

- The two test files above.

### Property-Based Tests

- Not applicable: the standard library has no property-based test tool; the two preservation cases cover the rounding.

### Integration Tests

- Not applicable: `total()` has no outside dependency.

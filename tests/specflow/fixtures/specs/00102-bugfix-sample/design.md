# Last Row Bugfix Design

## Overview

The reader stops at the last newline. Reading to the end of the file fixes it.

## Glossary

- **Bug_Condition (C)**: the file does not end with a newline
- **Property (P)**: every row is imported
- **Preservation**: files that end with a newline import as before

## Bug Details

### Bug Condition

```text
FUNCTION isBugCondition(X)
  RETURN NOT X.endswith("\n")
END FUNCTION
```

### Examples

- `a\nb` imports `a` only; expected `a` and `b`.

## Expected Behavior

Every row is imported whatever the file's last byte.

### Preservation Requirements

- A file that ends with a newline imports each row once.

## Hypothesized Root Cause

1. The reader splits on newlines and drops the remainder.

## Correctness Properties

Property 1: Bug Condition - last row kept

_For any_ file X where isBugCondition(X) holds, the fixed reader SHALL import its last row.

**Validates: Requirements 2.1**

Property 2: Preservation - other files unchanged

_For any_ file X where isBugCondition(X) does not hold, the fixed reader SHALL import the same rows as before.

**Validates: Requirements 3.1**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

- `src/import/reader.py`: keep the remainder after the last newline.

## Testing Strategy

### Validation Approach

Show the bug on the unfixed reader, then check the fix and preservation.

### Exploratory Bug Condition Checking

A file without a final newline loses its last row on the unfixed reader.

### Fix Checking

FOR ALL X WHERE isBugCondition(X): the fixed reader imports every row.

### Preservation Checking

FOR ALL X WHERE NOT isBugCondition(X): F(X) = F'(X).

### Unit Tests

- `test_last_row_without_newline` proves the fix.

### Property-Based Tests

- Random files with and without a final newline.

### Integration Tests

- One nightly import of a sample file.

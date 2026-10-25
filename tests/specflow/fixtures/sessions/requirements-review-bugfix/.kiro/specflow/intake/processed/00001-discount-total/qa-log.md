# Q&A log: 00001 discount-total

## Q1 - Current behavior (2026-10-14)

- Question: What do you see at checkout with the code applied?
- Answer: "110.00, every time. It is the price plus tax, as if there were no code."
- Reading: the total ignores the discount; the reproduction is the one in idea.md.

## Q2 - Expected behavior (2026-10-14)

- Question: What should the total be?
- Answer: "Take the 10% off first, then add tax: 99.00."
- Reading: the discount comes off the price before tax.

## Q3 - Constraints (2026-10-14)

- Question: What must not change?
- Answer: "Totals without a code stay as they are, and totals still round to two decimals."
- Reading: two unchanged behaviors, no code-level constraint.

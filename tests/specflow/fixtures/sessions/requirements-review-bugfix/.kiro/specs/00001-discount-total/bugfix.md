# Bugfix Requirements Document

## Introduction

A discount code never lowers the checkout total: with an item priced 100 and the code SAVE10 (10% off), the total shows 110.00 instead of 99.00. Every order placed with a code is overcharged. Suspected cause: `total()` in `src/checkout.py` adds tax to the full price and never uses the discount.

Sources: .kiro/specflow/intake/processed/00001-discount-total/

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a discount code is applied to a cart THEN the system shows the checkout total without the discount

1.2 WHEN a cart holds a discount code THEN the system sometimes seems slow to show the total

### Expected Behavior (Correct)

2.1 WHEN a discount code is applied to a cart THEN the system SHALL take the discount off the price first and add tax to the discounted price

2.2 WHEN an item priced 100 gets the code SAVE10 THEN the system SHALL show a checkout total of 99.00

2.3 WHEN a discount code is applied to a cart THEN the system SHALL work correctly

### Unchanged Behavior (Regression Prevention)

3.1 WHEN no discount code is applied THEN the system SHALL CONTINUE TO show the price plus tax

3.2 WHEN a total has more than two decimals THEN the system SHALL CONTINUE TO round it to two decimals

3.3 WHEN a discount code is applied to a cart THEN the system SHALL CONTINUE TO add tax to the full price before any discount

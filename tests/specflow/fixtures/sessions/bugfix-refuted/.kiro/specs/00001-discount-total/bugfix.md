# Bugfix Requirements Document

## Introduction

A discount code never lowers the checkout total: with an item priced 100 and the code SAVE10 (10% off), the total shows 110.00 instead of 99.00.

Sources: .kiro/specflow/intake/processed/00001-discount-total/

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a discount code is applied to a cart THEN the system shows the checkout total without the discount

### Expected Behavior (Correct)

2.1 WHEN a discount code is applied to a cart THEN the system SHALL take the discount off the price first and add tax to the discounted price

### Unchanged Behavior (Regression Prevention)

3.1 WHEN no discount code is applied THEN the system SHALL CONTINUE TO show the price plus tax

3.2 WHEN a total has more than two decimals THEN the system SHALL CONTINUE TO round it to two decimals

# Requirements: Price import

Sources: .kiro/specflow/intake/processed/00001-price-import/

## Purpose

Import the supplier's price list.

## Requirements

### REQ-001: Import prices

Source: the idea

**User story:** As a buyer, I want the supplier's prices imported, so that the shop shows them.

#### Acceptance criteria

1. WHEN a price list is uploaded THE SYSTEM SHALL update the price of each known SKU.
2. WHEN a line cannot be read THE SYSTEM SHALL list it in the import report.

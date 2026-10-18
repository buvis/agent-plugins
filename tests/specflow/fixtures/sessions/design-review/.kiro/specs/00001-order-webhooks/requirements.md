# Requirements: Order webhooks

Sources: .kiro/specflow/intake/processed/00001-order-webhooks/

## Purpose

Tell the shop owner's other tools about new orders as they happen, so that the warehouse and the accounting sheet stop polling the admin page.

## Scope

Registered URLs receive one event for each new order.

## Assumptions

- The admin page already authenticates the shop owner (source: `src/admin.py`).

## Requirements

### REQ-001: Register a URL

Source: the idea

**User story:** As a shop owner, I want to register a URL on the admin page, so that my other tools receive order events.

#### Acceptance criteria

1. WHEN the shop owner saves a URL on the admin page THE SYSTEM SHALL store it as a webhook target.
2. WHEN the shop owner removes a URL THE SYSTEM SHALL send it no further events.

### REQ-002: Deliver order events

Source: the idea

**User story:** As a shop owner, I want each new order posted to my registered URLs, so that the warehouse learns of it at once.

#### Acceptance criteria

1. WHEN an order is created THE SYSTEM SHALL post a JSON event naming the order to every registered URL within one minute.
2. IF a delivery fails THEN THE SYSTEM SHALL retry it up to three times, waiting longer before each retry.

## Non-functional requirements

- Only the shop owner can register or remove a URL.

## Risks

- A slow URL delays the other deliveries: impact m, likelihood m; mitigation: one timeout per delivery; fallback: a queue per URL.

## Out of scope

- Events other than order creation.

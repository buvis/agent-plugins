# Design: Order webhooks

## Overview

When an order is created, the shop posts a JSON event to the URLs the owner registered. Deliveries go through HookRelay, a hosted relay that fans one batch out to many URLs. Operation of the delivery worker: to be assigned.

## Context and constraints

- Orders are created in `src/orders.py` (`create_order`); the admin page is `src/admin.py`.
- The shop runs as one process on one host, with SQLite.
- The delivery code goes into `src/webhooks.py`.

## Architecture

A `webhooks` table holds the registered URLs. `create_order` appends an event to an in-memory queue; a single worker thread drains the queue and posts each batch to HookRelay's batch API, which delivers to the URLs. The queue has no size limit, since orders are few. If the worker thread dies, deliveries stop until the process is restarted.

## Module placement

- `src/webhooks.py` (new): the queue, the worker thread, and the HookRelay client.
- `src/orders.py` (edit): `create_order` enqueues the event.
- `src/admin.py` (edit): the registration page.
- `config/webhooks.ini` (new): holds the HookRelay key and the signing secret, in plain text, next to the other settings.

## Components and interfaces

- `register(db, url: str) -> int` stores the URL and returns its id.
- `deliver(event: dict) -> None` posts one batch to HookRelay.
- The HookRelay client reads `HOOKRELAY_KEY = "hr_live_8f3a2c9d41b7"` from `src/webhooks.py`, as the module already does.
- The payload `{"event": "order.created", "order": {"id": 12, "total": 40.0}}` is the public contract for the owner's integrations. Versioning is not planned; the shape is simple enough.

## Data model

- `webhooks(id, url, created_at)`, new.
- `orders` gains a `webhook_status` column. The column is added by hand on the production database; no migration script is written, and existing rows are left as they are.
- `deliveries(id, order_id, payload, status)` keeps the full order payload of every delivery and is never deleted or exported.

## Data and control flow

`create_order` writes the order, appends `{"event": "order.created", "order": ...}` to the queue, and returns. The worker wakes every second, takes everything in the queue, and calls `deliver`. HookRelay posts to each registered URL and reports per-URL results, which the worker writes to `deliveries`.

## Error handling

Retry policy for failed deliveries: we will figure it out later, once HookRelay's error codes are known.

## Security and privacy

Authentication of the registration page comes in phase 2; for the first release any admin session may register or remove a URL. The signing secret lives in `config/webhooks.ini`.

## Testing strategy

Unit tests for `register` and `deliver` with a fake relay.

## Rollout and migration

Deploy and restart. Rollback: not needed, the change is small. No metrics or logs are planned for deliveries; the shop owner will notice when a webhook is missing. The `webhooks` and `deliveries` tables are not in the nightly backup, since they can be re-created.

## Risks and edge cases

- HookRelay outage: impact h, likelihood l; mitigation: none yet; fallback: none. HookRelay's batch API is proprietary and there is no other provider with the same shape.

## Requirement traceability

| Design element | Criteria |
|---|---|
| `register`, the admin page | REQ-001.1, REQ-001.2 |
| the queue, the worker, `deliver` | REQ-002.1 |

## Alternatives considered

None were written down; the team agreed on HookRelay in the stand-up.

## Reuse inventory

Searched for `webhook`, `deliver`, `post`, and `queue` in `src/`: nothing to reuse.

## Open decisions

- None.

# PRD 00012: Order tags

Status: draft, written 2026-10-10 by the owner.

## Problem

The owner cannot mark an order ("gift", "fragile", "rush"), so the instruction is lost by packing time.

## Must have

- M1. An order carries zero or more tags from a fixed list: gift, fragile, rush.
- M2. The order list can be filtered by one tag.
- M3. Tags are stored in Redis, for speed.

## Nice to have

- N1. Tags the owner types in, beyond the fixed list.

## Acceptance

- A1. Tagging an order shows the tag on the order page in the same request.
- A2. Filtering by "rush" lists the rush orders and no other.

## Open questions

- Can a tag be removed after the order is packed?

"""Refund endpoints (session fixture)."""

from refunds.ledger import book


def refund(order_id: str) -> dict:
    return book(order_id, amount=None)

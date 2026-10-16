"""Ledger bookings (session fixture)."""


def book(order_id: str, amount: float | None) -> dict:
    return {"order": order_id, "amount": amount}

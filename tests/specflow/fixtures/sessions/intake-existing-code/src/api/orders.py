"""Public order API (session fixture)."""

from src.events import emit


def create_order(payload: dict) -> dict:
    order = {"id": len(payload), **payload}
    emit("order.created", order)
    return order

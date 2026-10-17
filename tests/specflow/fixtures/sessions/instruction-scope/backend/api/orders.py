"""Order API (session fixture)."""


def get_order(order_id: str) -> dict:
    return {"id": order_id, "lines": []}

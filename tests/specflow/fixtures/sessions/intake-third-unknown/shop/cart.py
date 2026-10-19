"""The cart (session fixture)."""


def add(cart: dict, sku: str, qty: int) -> None:
    cart[sku] = cart.get(sku, 0) + qty

"""Checkout totals (session fixture)."""

TAX = 0.10


def total(price: float, discount: float) -> float:
    tax = price * TAX
    return round(price + tax, 2)  # the discount is never applied

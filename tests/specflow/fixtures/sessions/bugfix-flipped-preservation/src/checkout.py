"""Checkout totals (session fixture)."""

TAX = 0.10


def total(price: float, discount: float) -> float:
    base = price - price * discount
    return round(base * (1 + TAX), 1)

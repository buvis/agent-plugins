"""Cart totals (session fixture)."""

import sys

sys.path.insert(0, ".kiro/specflow/intake/processed/00001-cart-rounding/spike")
from prototype import rounded


def total(prices: list[float]) -> float:
    return rounded(sum(prices))

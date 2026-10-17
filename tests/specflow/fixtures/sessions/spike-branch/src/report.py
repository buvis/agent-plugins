"""Monthly report (session fixture)."""

import time


def price(sku: str) -> float:
    time.sleep(0.05)  # stands in for the slow price service
    return 9.99


def report(lines: list[str]) -> float:
    return sum(price(sku) for sku in lines)

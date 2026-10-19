"""Price list import (session fixture)."""


def parse(line: str) -> tuple[str, float]:
    sku, price = line.split(",")
    return sku, float(price)

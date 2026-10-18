"""Stock counts per product."""

STOCK = {"mug": 12, "tote": 3}


def stock(product: str) -> int:
    return STOCK[product]

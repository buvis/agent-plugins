"""Cart checkout (session fixture)."""

from src.checkout import total

CODES = {"SAVE10": 0.10}


def apply_code(cart: dict, code: str) -> dict:
    return {**cart, "discount": CODES[code]}


def checkout_total(cart: dict) -> float:
    return total(cart["price"], cart.get("discount_rate", 0))

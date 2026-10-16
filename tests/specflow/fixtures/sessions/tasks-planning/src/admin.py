"""Admin view (session fixture)."""

from src.orders import orders_in


def export_view(month: str) -> int:
    return len(orders_in(month))

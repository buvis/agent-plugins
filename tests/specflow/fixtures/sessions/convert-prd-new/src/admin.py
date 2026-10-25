"""Admin page: the order list and the order page."""

from orders import order, orders_today


def order_list(db):
    return orders_today(db)


def order_page(db, order_id: int):
    return order(db, order_id)

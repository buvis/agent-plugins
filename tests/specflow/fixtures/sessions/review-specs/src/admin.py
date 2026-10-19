"""Admin page: the order list and the nightly report both call orders_in."""

from orders import orders_in


def order_list(db):
    return orders_in(db)


def nightly_report(db):
    return sum(row[2] for row in orders_in(db))

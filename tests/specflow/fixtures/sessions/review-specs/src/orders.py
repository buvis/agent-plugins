"""Orders of the shop."""


def orders_in(db):
    """Today's orders."""
    return db.execute("select id, day, total from orders where day = date('now')").fetchall()

"""Orders of the shop."""


def order(db, order_id: int):
    return db.execute(
        "select id, total, status from orders where id = ?", (order_id,)
    ).fetchone()

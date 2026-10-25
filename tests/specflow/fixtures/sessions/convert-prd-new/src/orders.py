"""Orders of the shop."""


def order(db, order_id: int):
    return db.execute(
        "select id, day, total, status from orders where id = ?", (order_id,)
    ).fetchone()


def orders_today(db):
    return db.execute(
        "select id, day, total, status from orders where day = date('now')"
    ).fetchall()

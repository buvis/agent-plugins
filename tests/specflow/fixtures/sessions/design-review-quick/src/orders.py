"""Orders of the shop. The `notes` column exists and is unused."""


def order(db, order_id: int):
    return db.execute(
        "select id, total, status, notes from orders where id = ?", (order_id,)
    ).fetchone()

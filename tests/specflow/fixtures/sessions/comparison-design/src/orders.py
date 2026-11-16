"""Orders of the shop."""


def create_order(db, items: list[dict]) -> int:
    total = sum(item["price"] * item["qty"] for item in items)
    cursor = db.execute(
        "insert into orders (total, status) values (?, 'new')", (total,)
    )
    return cursor.lastrowid

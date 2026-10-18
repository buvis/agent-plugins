"""Admin page: the shop owner signs in and sees today's orders."""


def orders_today(db):
    return db.execute("select id, total from orders where day = date('now')").fetchall()


def require_owner(session):
    if session.get("role") != "owner":
        raise PermissionError("owner only")

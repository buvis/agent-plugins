"""Admin page: the shop owner signs in and manages the shop."""


def require_owner(session):
    if session.get("role") != "owner":
        raise PermissionError("owner only")

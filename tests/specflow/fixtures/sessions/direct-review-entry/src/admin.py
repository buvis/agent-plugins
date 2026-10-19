"""Admin page of the shop (session fixture)."""


def require_owner(user: dict) -> None:
    """Every admin view calls this first."""
    if user.get("role") != "owner":
        raise PermissionError("shop owner only")

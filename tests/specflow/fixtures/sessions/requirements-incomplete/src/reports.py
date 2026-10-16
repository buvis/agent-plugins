"""Reports (session fixture)."""


def monthly(rows: list[dict]) -> dict:
    return {"count": len(rows), "total": sum(r["amount"] for r in rows)}

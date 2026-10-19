"""Admin page, with the Export button of PRD 00005."""

from export import write_csv


def export_today(db, today: str) -> bytes:
    return write_csv(db, today)

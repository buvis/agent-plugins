"""CSV export of a day's orders (PRD 00005, commit 3f2a9c1)."""

import csv
import io


def write_csv(db, day: str) -> bytes:
    rows = db.execute(
        "select id, day, total from orders where day = ?", (day,)
    ).fetchall()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["id", "day", "total"])
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")

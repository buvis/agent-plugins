"""Nightly import of the vendor's CSV order feed (session fixture)."""

import csv
import sys

REQUIRED = ("order_id", "amount")


def import_rows(path: str) -> tuple[list[dict], list[dict]]:
    """Valid rows to load and skipped rows to log."""
    loaded, skipped = [], []
    with open(path, newline="", encoding="utf-8") as feed:
        for row in csv.DictReader(feed):
            (loaded if all(row.get(k) for k in REQUIRED) else skipped).append(row)
    return loaded, skipped


if __name__ == "__main__":
    rows, rejects = import_rows(sys.argv[1])
    print(f"loaded {len(rows)}, skipped {len(rejects)}")

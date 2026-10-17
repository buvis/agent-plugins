# nightly-import

Imports the vendor's CSV order feed into the `orders` table every night at
02:00 UTC. A row that fails validation is skipped and written to
`logs/skipped.csv`.

Run it with `python3 src/importer.py <feed.csv>`. Tests: `python3 -m unittest`.

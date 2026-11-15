# Runner instrument fixtures

`manual.json` is a synthetic manual-format run, not a captured host session.
It uses existing Git object IDs for the package, status-summary fixture, and
session. Its simplified transcript, status, file change, and deletions are
deliberate test data. It must never count as release or host-isolation evidence.

`evals/` has one passing eval and one deliberately impossible eval on that same
record. `rubrics/` has an unjudged rubric. These folders are passed explicitly to
the scorer and do not join the real behavioral-rule inventory.

`self-check/` is the pair for the live T-056 self-check on the real
`status-summary` session: one eval a compliant host passes (a status question
leaves both state files unchanged) and one deliberately impossible eval. Pass it
to a runner with `--evals`; the expected runner exit is 1.

Run `python3 -B -m unittest discover -s tests/specflow/rules -p test_score.py`.
The existing CI rule-test step discovers these tests. No signed-in host is used.

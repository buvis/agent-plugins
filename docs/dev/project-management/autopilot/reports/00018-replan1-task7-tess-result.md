Created only:

- `tests/autopilot/controller_owner_support.py`
- `tests/autopilot/test_controller_owner.py`
- `tests/autopilot/test_controller_owner_recovery.py`
- `tests/autopilot/test_controller_capacity.py`

Covers owner modes, epochs, exact/historical replay, concurrent exclusion, OS publication crashes, intent admission/corruption, fsync failure, independent count/byte limits, emergency reserves, sealed replay, and archive/restore.

Authorized Python 3.12 narrow run: **19 failed, 4.92s, exit 1**. Owner operations return `missing_capability`; crash boundaries consequently remain unreachable. Subsequent assertion tightening was AST-checked without rerunning tests.

Final files: 45,326 bytes; longest function 35 lines; largest file 282 lines. Task6 untouched. No production reads, commits, or batch-state writes.

Coverage limitation: generating a real response exceeding 65,536 bytes requires an existing project path beyond macOS path limits. No speculative oversized-root error expectation was added.

ASSUMPTIONS:
Snapshot’s named identity/owner fields are top-level; no complete snapshot projection schema is published.
Corrected all findings in the same four test files:

- Intent observations use only `controller/credential-intent.json`.
- Snapshot validates the response envelope and returns `result`.
- Unknown unique job IDs expect `rejected_evidence`; malformed payloads expect `invalid_request`.
- Both MECH-flagged tests now directly assert preserved state, receipts, revision, or owner.

Static compilation and size checks pass: longest function 35 lines; largest file 283 lines. No test rerun, production access, commits, or state writes.

Preserved the macOS response-size coverage limitation and existing response-bound assertions.

ASSUMPTIONS: none
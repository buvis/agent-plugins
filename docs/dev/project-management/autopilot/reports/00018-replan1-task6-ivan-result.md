Implemented task 6: bounded CLI, private bootstrap, authenticated replay, read-only snapshots, contract metadata, and durable intent recovery. Owner mutations remain unavailable.

Verification: exact narrow suite **25 passed in 16.35s**, exit 0. All functions ≤50 lines; files ≤800 lines. No tests, commits, or batch-state writes.

ASSUMPTIONS:
- Snapshot actors use ID/role rows; capacity uses remaining byte/receipt counters because no snapshot schema is declared.

FILES_TOUCHED:
- plugins/autopilot/controller/main.py
- plugins/autopilot/controller/autopilot_state/protocol.py
- plugins/autopilot/controller/autopilot_state/actors.py
- plugins/autopilot/CHANGELOG.md
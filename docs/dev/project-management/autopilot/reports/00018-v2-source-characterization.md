# AP00018 v2 pinned-source characterization

Rechecked 2026-11-09 against OVCAQ `cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7`
from `https://github.com/buvis/ovcaq`. Each raw blob was read using
`git show <exact-pin>:<path>` and streamed into SHA-256. No checkout HEAD
source or fixture bodies were inspected.

All 15 observed hashes equal the recorded provenance hashes. No provenance
correction is needed.

| Pinned source path | Recorded SHA-256 | Observed SHA-256 |
| --- | --- | --- |
| `src/ovcaq/state/schema.py` | `1aa218e2b435866c96ca490bc499aaa2fc3e49d640ddde84dd947b00812bd60b` | `1aa218e2b435866c96ca490bc499aaa2fc3e49d640ddde84dd947b00812bd60b` |
| `src/ovcaq/state/store.py` | `b7ade1f13f7c4ef8cb65ce07ac5c228e235ab293ae9e82562e7d449e721307e7` | `b7ade1f13f7c4ef8cb65ce07ac5c228e235ab293ae9e82562e7d449e721307e7` |
| `src/ovcaq/state/commands.py` | `30d51f28eb04a3a00ecae2aa3d3966435add4e804311468c1b6ea1bb7614fbd0` | `30d51f28eb04a3a00ecae2aa3d3966435add4e804311468c1b6ea1bb7614fbd0` |
| `src/ovcaq/paths.py` | `3bb2bdd7da9dc838e19751fb95c79aa072961849624978f9ab91bfb3a5cfb990` | `3bb2bdd7da9dc838e19751fb95c79aa072961849624978f9ab91bfb3a5cfb990` |
| `tests/state/test_schema.py` | `91e46ef82e027e9b9f30769e012170e105c6c6cef9e065276f9abdbd37248e27` | `91e46ef82e027e9b9f30769e012170e105c6c6cef9e065276f9abdbd37248e27` |
| `tests/state/test_schema_constraints.py` | `60bd69c7aaf5f3297d51095506e1618a7cd373886879879d311d07f24d417174` | `60bd69c7aaf5f3297d51095506e1618a7cd373886879879d311d07f24d417174` |
| `tests/state/test_schema_invariants.py` | `93826703d0452919d2b16bb040b11a70f2ac4e166e94e913b25cedef7476382f` | `93826703d0452919d2b16bb040b11a70f2ac4e166e94e913b25cedef7476382f` |
| `tests/state/test_schema_limits.py` | `f92ff6c294850837675a2bea85aff774ce888c66466cc0fdc3d16b1008445cb1` | `f92ff6c294850837675a2bea85aff774ce888c66466cc0fdc3d16b1008445cb1` |
| `tests/state/test_store.py` | `5bebdd57e7b027889c18de3e18f006702d4017a1f7e1e9abd2bd22befd6e9992` | `5bebdd57e7b027889c18de3e18f006702d4017a1f7e1e9abd2bd22befd6e9992` |
| `tests/state/test_store_transactions.py` | `59863830378a6ffe7c2cef4df0f383e5937541345347f8c36f952e0eb36fa4f3` | `59863830378a6ffe7c2cef4df0f383e5937541345347f8c36f952e0eb36fa4f3` |
| `tests/state/test_store_concurrency.py` | `791b17d686b9dc4bb5cb4b9f770690d1bf580988c286f91b1dba55a6f0761fb9` | `791b17d686b9dc4bb5cb4b9f770690d1bf580988c286f91b1dba55a6f0761fb9` |
| `tests/state/test_durability.py` | `fafcd253e9ebdf05d0ed9b4aa5f7a0619f602ae36349ab387e0ffe88477dbc32` | `fafcd253e9ebdf05d0ed9b4aa5f7a0619f602ae36349ab387e0ffe88477dbc32` |
| `tests/state/test_guarded_service.py` | `7e7c8bae2ecd23c21fbb58f8fb4fa5f744b03fb9aa94c810f28b75655002111f` | `7e7c8bae2ecd23c21fbb58f8fb4fa5f744b03fb9aa94c810f28b75655002111f` |
| `tests/runtime/test_paths.py` | `aa10c8c06740bf6ea4eb29c11d06affac0f17c0e605d7fb3d6a10fe2da3b3fdd` | `aa10c8c06740bf6ea4eb29c11d06affac0f17c0e605d7fb3d6a10fe2da3b3fdd` |
| `LICENSE` | `cf48d74443ef10a4521c1413fc331ceca76a2c791ea913c60df6d0cbf1440e46` | `cf48d74443ef10a4521c1413fc331ceca76a2c791ea913c60df6d0cbf1440e46` |

The four source-to-target declarations reference existing pinned source symbols:

| Source | Declared target | Symbols checked | Missing |
| --- | --- | ---: | ---: |
| `src/ovcaq/state/schema.py` | `autopilot_state.schema` | 11 | 0 |
| `src/ovcaq/state/store.py` | `autopilot_state.store` | 14 | 0 |
| `src/ovcaq/paths.py` | `autopilot_state.paths.resolve_project_root` and private layout | 6 | 0 |
| `src/ovcaq/state/commands.py` | none; excluded generic mutation service | 6 | 0 |

The allowed target schema contains its 11 mapped exports, including the two
exception classes and three public functions. Its six published constants
retain the required values: schema version 1; state 16777216 bytes; command
payload 2097152 bytes; string 1048576 bytes; depth 32; integer digits 640.
Other target modules were outside this task's read allowlist; source symbol
presence does not establish their behavioral equivalence.

The pinned schema declares 144 class fields. The ownership section has 144
distinct matching source fields, with no missing or extra entries: 137
deferred, three excluded, two redesigned and two preserved. Its four core
mappings are `WorkState.repo_root -> repo_root`,
`ReviewState.cap -> workflow.review.cap`,
`State.schema_version -> schema_version`, and
`State.revision -> revision`. This is field ownership characterization,
not a claim that the kernel implements the legacy workflow schema.

The existing schema tests explicitly check rejection of missing and unknown
fields, process identity/PID/launcher/heartbeat/resource/TUI fields at both
top level and under workflow, populated or extended workflow reserves,
and invalid values before deep copying. They also check revision-zero
initialization with explicit project/workflow identity and fresh reserves.
No source-hash or ownership-map drift was observed. Runtime restore,
credential recovery, protocol examples and delivery behavior were not
re-executed by this schema-only gate.

Executed once, with a 300-second subprocess timeout:

```text
mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_schema.py -q --tb=line
22 passed in 0.33s
exit code: 0
```

Scope: report only. Production, tests, provenance, held/custody records and
controller state were not modified. No commit, push or installation ran.

Reading deviation: the initial provenance query selected invariant and
divergence sections in addition to the intended source/symbol/ownership
sections. Its output exceeded the 15 KB query cap and was truncated by
the tool. The orchestrator was informed; subsequent outputs were bounded.
No fixture body or full pinned source was printed.

ASSUMPTIONS: none

FILES_TOUCHED:
docs/dev/project-management/autopilot/reports/00018-v2-source-characterization.md


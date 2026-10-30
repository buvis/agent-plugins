# Task 3 Devon adversarial round — result (operator exception)

## Provenance

- PRD / task: 00018-autopilot-controller-kernel-v1, replan 1, task 3
  ("Implement strict kernel schema and package namespace").
- Gate: mandatory step-2.9 adversarial validation (Devon), opus/full tier.
- Why this file exists: the native GPT Devon dispatch (`/root/schema_devon`,
  `gpt-6.1-sol`) was blocked by OpenAI's cyber-safety content filter
  (`cyber_policy`; see `00018-replan1-task3-host-block.md`). The operator
  granted a documented, task-scoped exception to run this one required round on
  the supported Claude Opus capability instead. This is a different, in-policy
  model, not an evasion of the filter; no filter was bypassed, disguised, or
  retried under a changed prompt.
- Executor: isolated Claude Opus agent, fresh context, Devon contract inputs
  only (the two committed test files + the public interface signatures + the
  narrow test-runner command). It received no task description, acceptance
  criteria, or design doc, per `work/references/adversarial-test-prompt.md`.
- Test target: `tests/autopilot/test_controller_schema.py` (+ its
  `controller_test_support.py` fixtures), the files task 2 committed.
- Runner: `uv run --no-project --python 3.12 --with-requirements
  tools/autopilot/requirements-test.txt python -m pytest
  tests/autopilot/test_controller_schema.py -q --tb=line`.

## Verdict: EXPLOITED

A single deliberately-wrong `autopilot_state.schema` implementation passed all
21 tests. Last run: exit 0, `21 passed in 0.13s`. The wrong implementation
published the correct public constants (so the exact-constants test passes)
while enforcing wrong internal limits and skipping value checks the tests never
exercise.

`devon_weak_points: 8`

## Weak points (verbatim, each with the assertion that would catch it)

1. `test_actor_roles_owner_modes_and_secret_fields_reject_near_matches` —
   accepts a 64-char lowercase NON-hex `secret_digest` (`"z"*64`). The probes
   only vary length (`"b"*63`) and case (`"B"*64`), never non-hex-lowercase.
   Add `("secret_digest", "z"*64)` → `assert_invalid`.
2. `test_actor_owner_and_receipt_objects_have_closed_fields_and_bounded_identities`
   — identity length cap can be absurdly small (20 bytes). Invalid probes are
   all >=257 bytes; accepted fixtures all <=18 bytes. Assert a ~256-byte id
   valid.
3. `test_decoder_rejects_byte_depth_and_integer_resource_overflow` — decoder
   enforces depth 8 while advertising `MAX_JSON_DEPTH == 32`. Only depth-34 is
   probed; deepest accepted fixture ~6. Add a depth-32-valid / depth-33-invalid
   pair.
4. `test_total_state_byte_limit_is_independent_of_receipt_count_and_string_limits`
   — state-size cap enforced at 8 MB vs. advertised 16 MiB. Only a >16 MiB
   state is probed invalid; largest valid ~2.7 MB. Assert a ~12 MB state valid.
5. `test_active_and_receipt_actor_ids_reject_invalid_types_and_oversized_strings`
   — `actor_id` is not required to equal its map key. The invalid tuple is all
   type/size-wrong; add a valid-but-mismatched id (`"ghost"`) → invalid.
6. `test_accepts_both_frozen_states_and_retains_receipt_history` —
   `validate_state` returns the caller's object (no defensive copy). The test
   only checks the input is unmutated; mutate the RESULT and re-check the input
   is independent.
7. `test_receipts_retain_complete_success_responses_and_reject_oversized_responses`
   — response `ok`/`error_code`/`retryable`/`result` accept any type (only
   `revision` is type-checked). The deletion loop checks presence only; add a
   type probe on `ok`/`retryable`.
8. `test_actor_roles_owner_modes_and_secret_fields_reject_near_matches`
   (owner loop) — `owner.lease_epoch`/`actor_id`/`native_session_id` are never
   validated (`owner.lease_epoch = -1` passes, though top-level
   `lease_epoch = -1` is rejected). The loop only varies `owner["mode"]`; vary
   `owner["lease_epoch"]`.

## State of the tree after the round

- The wrong implementation was never committed. Devon overwrote the two files
  it created with a placeholder line; the recovery session then removed the
  whole `plugins/autopilot/controller/` residue. `git status` is clean and the
  test files are byte-unchanged.
- No partial pass is recorded as a completed verdict. The gate is NOT satisfied
  until the tests are strengthened (below).

## Required next step (resumed pipeline, GPT-safe)

Devon broke the tests, so the adversarial-test protocol mandates exactly one
Tess strengthen dispatch that addresses all 8 weak points (each strengthened or
justified in-contract), a `test(autopilot): strengthen …` commit, and the
`devon: exploit_fixed` / `devon_exploit` / `devon_weak_points: 8` /
`devon_in_contract` attempt fields — then red-check (2.95) and Ivan (step 3).
Authoring correct stronger assertions is benign test engineering and does not
trip the cyber-safety filter, so it runs on the normal GPT pipeline under the
scope directive in `00018-replan1-task3-devon-exception.scope.md`.

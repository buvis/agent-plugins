LOW | plugins/autopilot/scripts/review_stage.py:627 | `stage_review` builds a manifest for every roster job, via `_manifest(expected_context, job)`, just so `_missing_prd_grant` can look at `blake` and `eve`. `_manifest` then runs again per job later. | Build the dict only for `_PRD_INLINE_JOBS & set(jobs)`, or have `_missing_prd_grant` take the context and call `_manifest` for those two jobs only.

LOW | plugins/autopilot/scripts/review_stage.py:627 | The refusal is a hand-built dict, while every neighbouring refusal in `stage_review` uses `_refusal("invalid-input", ...)`. The inline copy can drift from `_refusal`'s shape. | Use `_refusal("invalid-input", f"job {ungranted!r} has no prd: grant")` if its output is identical to the contract's dict. Keep the literal only if `_refusal` adds keys the contract excludes.

LOW | plugins/autopilot/scripts/review_stage.py:223 | `_missing_prd_grant` builds a `kinds` set of every ref prefix just to test for `"prd"`. | `if not any(ref.startswith("prd:") for ref in manifest[job]): return job`.

LOW | tests/autopilot/test_helper_recovery_v2.py:~80 and tests/autopilot/test_review_helpers.py:~528 | The digest-rebinding logic (recompute the manifest digest, then update `allowed_inputs` and `source_bindings`) is written twice, as `rebound` in the new file and inline in the edited test. | Move one helper into `test_review_helpers` and import it in both places.

LOW | tests/autopilot/test_helper_recovery_v2.py:~137 | `guarded_live_state(project, tmp_path)` never uses `tmp_path`. It only takes the argument to match the parametrized `make(project, tmp_path)` call. | Keep it as is, or drop the argument and adapt the other factory. This is cosmetic.

Devon ran eight independent wrong implementations against only the new characterization tests in an isolated copy. Every wrong implementation passed all 3 tests (0.06-0.09 seconds), with import-time assertions proving wrong behavior versus unchanged JSON Schema. Shared wrong implementation simply uses Draft202012Validator of workflow-v1.json after each separate mutation, returns value if valid. Mutations: state.required=[]; recursively remove type keywords; nonnegative_integer minimum removed; owner.additionalProperties=True; actors.maxProperties removed; tasks.maxItems removed; review.cap.const removed. Eighth wrong implementation accepts only exact kernel-initial and kernel-owned fixtures and rejects all other values.

Weak points:
1. test_kernel_field_ownership_rejects_unowned_fields - required fields can be ignored - assert SchemaError for {} and individually omitted required fields.
2. test_kernel_field_ownership_rejects_unowned_fields - field types can be ignored - assert SchemaError for revision="nonsense".
3. test_kernel_field_ownership_rejects_unowned_fields - nonnegative constraints can be ignored - assert SchemaError for negative revisions and epochs.
4. test_kernel_field_ownership_rejects_unowned_fields - nested owner ownership can be ignored - assert SchemaError after adding owner.process_identity.
5. test_kernel_field_ownership_rejects_unowned_fields - actor-count limits can be ignored - assert SchemaError for three otherwise valid actors.
6. test_kernel_field_ownership_rejects_unowned_fields - kernel task restrictions can be ignored - assert SchemaError for nonempty workflow.tasks.
7. test_kernel_field_ownership_rejects_unowned_fields - runtime review-cap validation can be ignored - assert SchemaError for workflow.review.cap=99.
8. test_kernel_field_ownership_rejects_unowned_fields - only the two fixture states need acceptance - assert acceptance of independently constructed valid states including revision=2.

Address every numbered weak point. Answer each as N. strengthened: <test name> or N. in-contract: <why behavior allowed>. Do not change tests Devon could not break. Modify only /Users/bob/git/src/github.com/buvis/agent-plugins/tests/autopilot/test_controller_recovery_characterization.py. Public fixtures/schema/provenance and existing schema tests may be read as bounded test patterns, never production implementation. No weakening old assertions. Run only schema and characterization tests with -q --tb=line using mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt. No commits/state.

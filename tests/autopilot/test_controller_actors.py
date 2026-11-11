"""Direct unit coverage of actors.py's credential and actor descriptor logic.

The CLI-level owner/bootstrap tests exercise credentials end to end through
subprocess dispatch; this file pins `actors.credential_descriptor` and
`actors.authenticate` directly, as pure-function/unit-level behavior, per the
PRD's declared test structure (tests/autopilot/test_controller_actors.py).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import actors, schema
from controller_test_support import resolve_test_target

VALID_SECRET_OPERATOR = "a" * 43
VALID_SECRET_OWNER = "b" * 43


def credential_bytes(*, role: str, native_session_id: str | None, secret: str,
                     actor_id: str = "operator-" + "0" * 32,
                     project_id: str = "1" * 64,
                     workflow_id: str = "workflow-" + "2" * 32,
                     lease_epoch: int = 0) -> bytes:
    return json.dumps({
        "actor_id": actor_id, "project_id": project_id, "workflow_id": workflow_id,
        "role": role, "lease_epoch": lease_epoch,
        "native_session_id": native_session_id, "secret": secret,
    }).encode("utf-8")


class CredentialDescriptorTest(unittest.TestCase):
    def test_accepts_a_well_formed_operator_credential(self) -> None:
        raw = credential_bytes(role="operator", native_session_id=None,
                               secret=VALID_SECRET_OPERATOR)
        descriptor = actors.credential_descriptor(raw)
        self.assertNotIn("secret", descriptor)
        self.assertEqual(descriptor["secret_digest"], actors.digest(VALID_SECRET_OPERATOR.encode()))
        self.assertEqual(descriptor["role"], "operator")

    def test_accepts_a_well_formed_owner_credential(self) -> None:
        raw = credential_bytes(role="owner", native_session_id="session-" + "3" * 32,
                               secret=VALID_SECRET_OWNER)
        descriptor = actors.credential_descriptor(raw)
        self.assertEqual(descriptor["role"], "owner")
        self.assertEqual(descriptor["secret_digest"], actors.digest(VALID_SECRET_OWNER.encode()))

    def test_rejects_a_credential_missing_a_required_key(self) -> None:
        payload = json.loads(credential_bytes(role="operator", native_session_id=None,
                                              secret=VALID_SECRET_OPERATOR))
        del payload["lease_epoch"]
        with self.assertRaises(actors.BindingError):
            actors.credential_descriptor(json.dumps(payload).encode("utf-8"))

    def test_rejects_a_credential_with_an_unexpected_extra_key(self) -> None:
        payload = json.loads(credential_bytes(role="operator", native_session_id=None,
                                              secret=VALID_SECRET_OPERATOR))
        payload["unexpected"] = "value"
        with self.assertRaises(actors.BindingError):
            actors.credential_descriptor(json.dumps(payload).encode("utf-8"))

    def test_rejects_a_secret_of_the_wrong_length(self) -> None:
        raw = credential_bytes(role="operator", native_session_id=None, secret="a" * 42)
        with self.assertRaises(actors.BindingError):
            actors.credential_descriptor(raw)

    def test_rejects_a_secret_with_a_disallowed_character(self) -> None:
        raw = credential_bytes(role="operator", native_session_id=None,
                               secret="a" * 42 + "!")
        with self.assertRaises(actors.BindingError):
            actors.credential_descriptor(raw)

    def test_rejects_an_operator_credential_carrying_a_native_session_id(self) -> None:
        raw = credential_bytes(role="operator", native_session_id="session-" + "4" * 32,
                               secret=VALID_SECRET_OPERATOR)
        with self.assertRaises(schema.SchemaError):
            actors.credential_descriptor(raw)

    def test_rejects_an_owner_credential_missing_a_native_session_id(self) -> None:
        raw = credential_bytes(role="owner", native_session_id=None, secret=VALID_SECRET_OWNER)
        with self.assertRaises(schema.SchemaError):
            actors.credential_descriptor(raw)


class AuthenticateTest(unittest.TestCase):
    def test_a_missing_path_is_reported_as_credential_rejected_not_credential_required(self) -> None:
        # BindingError subclasses ValueError, so the function's own
        # `except (..., ValueError, ...)` clause catches its own
        # "credential required" raise and rewraps it as "credential
        # rejected" — the caller never observes the more specific message.
        descriptor = {"actor_id": "operator-" + "0" * 32}
        with self.assertRaises(actors.BindingError) as raised:
            actors.authenticate(None, descriptor, layout=None)
        self.assertEqual(str(raised.exception), "credential rejected")
        self.assertEqual(str(raised.exception.__cause__), "credential required")


# PRD 00018 names these acceptance scenarios; each id maps to the test that
# proves it. test_every_prd_scenario_resolves_to_a_real_test keeps the map honest.
PRD_SCENARIO_TESTS = {
    "kernel_equivalence": "tests/autopilot/test_controller_kernel.py::StoreTest."
        "test_transactions_copy_mutations_assign_revisions_and_preserve_last_good_backup",
    "concurrent_cas": "tests/autopilot/test_controller_kernel.py::StoreTest."
        "test_real_process_cas_allows_exactly_one_writer_for_the_same_revision",
    "corrupt_state_recovery": "tests/autopilot/test_controller_kernel.py::StoreTest."
        "test_corrupt_current_is_never_replaced_by_backup_or_restore",
    "lease_exclusion": "tests/autopilot/test_controller_owner.py::OwnerTest."
        "test_two_independent_subprocess_acquires_have_exactly_one_winner",
    "wrong_actor": "tests/autopilot/test_controller_bootstrap.py::ControllerBootstrapTest."
        "test_wrong_project_workflow_actor_epoch_and_job_never_change_bytes",
    "epoch_revoked": "tests/autopilot/test_controller_owner_v2.py::OwnerV2Test."
        "test_retired_intermediate_operator_cannot_borrow_another_epochs_receipt_authority",
    "fresh_open_replay": "tests/autopilot/test_controller_bootstrap.py::ControllerBootstrapTest."
        "test_concurrent_bootstrap_has_one_workflow_and_replays_same_request",
    "unsupported_operation_refused": "tests/autopilot/test_controller_bootstrap.py::"
        "ControllerBootstrapTest.test_reserved_operations_reject_without_receipts_or_credentials",
}


class PrdScenarioTraceabilityTest(unittest.TestCase):
    def test_every_prd_scenario_resolves_to_a_real_test(self) -> None:
        for scenario, target in PRD_SCENARIO_TESTS.items():
            with self.subTest(scenario=scenario):
                self.assertTrue(resolve_test_target(target),
                                f"PRD scenario {scenario} has no test at {target}")


if __name__ == "__main__":
    unittest.main()

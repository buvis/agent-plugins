"""read_intent must dispatch to owner.validate_intent only for protocol.OWNER_OPERATIONS."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from controller_owner_support import OwnerCLITest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import actors, owner, protocol
from autopilot_state.actors import PrivateLayout


class ReadIntentDispatchTest(OwnerCLITest):
    def test_dispatch_follows_protocol_owner_operations_not_a_hardcoded_literal(self) -> None:
        _, _, operator = self.bootstrap()
        _, _, _, operator = self.acquire(operator)
        request = self.request(operator, "owner.recover", "dispatch-recover",
                               {"reason": "Explicit crash reconciliation",
                                "reconciled_job_ids": []})
        self.crash(request, operator, "intent_dir_fsynced")
        self.assertTrue((self.root / ".autopilot" / "controller"
                         / "credential-intent.json").exists())

        calls: list[str] = []
        original_owner_validate = owner.validate_intent
        original_actors_validate = actors.validate_intent
        original_operations = protocol.OWNER_OPERATIONS

        def fake_owner_validate(value: object, layout: PrivateLayout) -> dict:
            calls.append("owner")
            return {}

        def fake_actors_validate(value: object, layout: PrivateLayout) -> dict:
            calls.append("actors")
            return {}

        owner.validate_intent = fake_owner_validate
        actors.validate_intent = fake_actors_validate
        # Exclude "owner.recover" from the set read_intent is supposed to consult.
        protocol.OWNER_OPERATIONS = frozenset({"owner.acquire", "owner.release"})
        try:
            with PrivateLayout(self.root) as layout:
                actors.read_intent(layout)
        finally:
            owner.validate_intent = original_owner_validate
            actors.validate_intent = original_actors_validate
            protocol.OWNER_OPERATIONS = original_operations

        self.assertEqual(
            calls, ["actors"],
            "read_intent must consult protocol.OWNER_OPERATIONS (patched here to "
            "exclude owner.recover), not a hardcoded literal set, when dispatching")


if __name__ == "__main__":
    unittest.main()

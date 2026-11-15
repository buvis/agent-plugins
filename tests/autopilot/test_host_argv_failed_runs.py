"""A probe run that fails, escapes its resources or is not enforced is never
recorded as an observation."""

from __future__ import annotations

import unittest

from test_host_argv import OBSERVED, LiveProbeCase

CAPABILITIES = ("identity", "isolation", "interception", "resources")


class ProbeHostFailedRunTest(LiveProbeCase):
    def test_relocated_host_probe_never_turns_a_failed_run_into_observation(self) -> None:
        escape = {"status": "not_observed", "reason": "resource_escape"}
        cases = (
            ("ignore_deny", {"interception": {"status": "not_observed", "reason": "host_did_not_enforce"}}),
            ("no_push", {"interception": {"status": "not_observed", "reason": "control_did_not_execute"}}),
            ("escape", dict.fromkeys(CAPABILITIES, escape)),
        )
        for mode, expected in cases:
            with self.subTest(mode=mode):
                record = self.probe("claude", mode)["record"]
                for capability, status in expected.items():
                    self.assertEqual(record["observed"][capability], status, capability)
                if mode != "escape":
                    self.assertEqual(record["observed"]["identity"], OBSERVED)
                    self.assertEqual(record["observed"]["isolation"], OBSERVED)
                self.assertEqual(record["resource_check"], "failed" if mode == "escape" else "passed")
                self.assertIs(record["certified"], False)
        with self.subTest(mode="fail"):
            record = self.probe("codex", "fail")["record"]
            codes = [invocation["exit_code"] for invocation in record["invocations"]]
            self.assertEqual((bool(codes), set(codes)), (True, {1}), codes)
            for capability in CAPABILITIES:
                self.assertEqual(record["observed"][capability]["status"], "not_observed", capability)
                self.assertTrue(record["observed"][capability]["reason"], capability)


if __name__ == "__main__":
    unittest.main()

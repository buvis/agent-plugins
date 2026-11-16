"""A probe run that fails, escapes its resources or is not enforced is never
recorded as an observation."""

from __future__ import annotations

import unittest

from probe_host_support import FAKE_HANG_SECONDS
from test_host_argv import OBSERVED, LiveProbeCase

CAPABILITIES = ("identity", "delegation", "isolation", "interception", "resources")


class ProbeHostFailedRunTest(LiveProbeCase):
    def test_relocated_host_probe_never_turns_a_failed_run_into_observation(self) -> None:
        escape = {"status": "not_observed", "reason": "resource_escape"}
        cases = (
            ("ignore_deny", {"interception": {"status": "not_observed", "reason": "host_did_not_enforce"}}),
            ("no_push", {"interception": {"status": "not_observed", "reason": "control_did_not_execute"}}),
            ("escape", dict.fromkeys(CAPABILITIES, escape)),
            # One more control line, all naming the copy: plugin_root decides an escape, not a line count.
            ("extra_line", dict.fromkeys(CAPABILITIES, OBSERVED)),
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
                self.assertEqual(record["observed"][capability]["reason"], "host_failed", capability)

    def test_relocated_host_probe_derives_isolation_and_interception_from_the_trace(self) -> None:
        """One session id across both bound runs is no isolation; a push that never
        reached the remote without a traced `missing_controller_seam` refusal is no
        interception, whatever the remote refs say."""
        with self.subTest(mode="same_session"):
            record = self.probe("claude", "same_session")["record"]
            self.assertEqual(record["observed"]["isolation"]["status"], "not_observed")
            for capability in ("identity", "interception", "resources"):
                self.assertEqual(record["observed"][capability], OBSERVED, capability)
            self.assertEqual((record["resource_check"], record["certified"]), ("passed", False))
        with self.subTest(mode="silent_refusal"):
            record = self.probe("claude", "silent_refusal")["record"]
            self.assertEqual(record["observed"]["interception"]["status"], "not_observed")
            for capability in ("identity", "isolation"):
                self.assertEqual(record["observed"][capability], OBSERVED, capability)
            self.assertEqual((record["resource_check"], record["certified"]), ("passed", False))

    def test_relocated_host_probe_kills_a_host_that_outlives_the_timeout(self) -> None:
        """--timeout bounds every launch: a hung host is cut off, marked timed out,
        and observes nothing."""
        run = self.probe("claude", "hang", timeout="2")
        self.assertLess(run["elapsed"], FAKE_HANG_SECONDS - 10, "probe waited for the hung host")
        record = run["record"]
        self.assertTrue(record["invocations"])
        self.assertEqual({invocation["timed_out"] for invocation in record["invocations"]}, {True})
        for capability in CAPABILITIES:
            self.assertEqual(record["observed"][capability]["status"], "not_observed", capability)
            self.assertEqual(record["observed"][capability]["reason"], "host_timed_out", capability)
        self.assertIs(record["certified"], False)


if __name__ == "__main__":
    unittest.main()

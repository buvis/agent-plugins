"""Pure plan validation, plan-size ceiling, and lane routing in the controller policy."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import policy, protocol


def task(task_id: str, *depends: str) -> dict:
    return {"id": task_id, "subject": "work", "depends_on": list(depends)}


# Representative evidence per `cli/lane.py` classify rule.
DOCS_ONLY = {"design": "skip", "named_paths": ["docs/guide.md", "tests/test_x.py"],
             "production_paths": [], "plan_cards": 1}
CARD_SIZED = {"design": "skip", "named_paths": ["src/app/render.py"],
              "production_paths": ["src/app/render.py"], "plan_cards": 1}


class PlanShapeTest(unittest.TestCase):
    def test_accepts_acyclic_plan_with_string_ids(self) -> None:
        plan = [task("a"), task("b", "a"), task("c", "a", "b")]
        self.assertEqual(policy.validate_plan_shape(plan), 3)

    def test_honours_custom_id_and_dependency_keys(self) -> None:
        jobs = [{"job_id": "build", "after": []}, {"job_id": "review", "after": ["build"]}]
        self.assertEqual(policy.validate_plan_shape(jobs, id_key="job_id", depends_key="after"), 2)

    def test_custom_dependency_key_is_the_one_checked(self) -> None:
        jobs = [{"job_id": "a", "after": ["b"]}, {"job_id": "b", "after": ["a"]}]
        with self.assertRaises(policy.InvalidPlan):
            policy.validate_plan_shape(jobs, id_key="job_id", depends_key="after")

    def test_rejects_dependency_cycle(self) -> None:
        with self.assertRaisesRegex(policy.InvalidPlan, "cycle"):
            policy.validate_plan_shape([task("a", "c"), task("b", "a"), task("c", "b")])

    def test_rejects_self_dependency(self) -> None:
        with self.assertRaisesRegex(policy.InvalidPlan, "cycle"):
            policy.validate_plan_shape([task("a", "a")])

    def test_rejects_duplicate_id(self) -> None:
        with self.assertRaisesRegex(policy.InvalidPlan, "duplicate"):
            policy.validate_plan_shape([task("a"), task("a")])

    def test_rejects_unknown_dependency(self) -> None:
        with self.assertRaisesRegex(policy.InvalidPlan, "unknown"):
            policy.validate_plan_shape([task("a", "ghost")])

    def test_rejects_non_string_id(self) -> None:
        with self.assertRaises(policy.InvalidPlan):
            policy.validate_plan_shape([{"id": 1, "depends_on": []}])

    def test_invalid_plan_is_a_value_error(self) -> None:
        self.assertTrue(issubclass(policy.InvalidPlan, ValueError))


class PlanCeilingTest(unittest.TestCase):
    def test_flags_plan_over_fifteen_tasks(self) -> None:
        tasks = [task(str(n)) for n in range(16)]
        self.assertEqual(policy.plan_over_ceiling({"tasks": tasks}), (True, 16))

    def test_allows_plan_at_fifteen_tasks(self) -> None:
        tasks = [task(str(n)) for n in range(15)]
        self.assertEqual(policy.plan_over_ceiling({"tasks": tasks}), (False, 15))

    def test_allows_small_plan(self) -> None:
        self.assertEqual(policy.plan_over_ceiling({"tasks": [task("a")]}), (False, 1))

    def test_tolerates_missing_task_list(self) -> None:
        self.assertEqual(policy.plan_over_ceiling({}), (False, 0))


class LaneRouteTest(unittest.TestCase):
    def assert_routes(self, fields: dict, lane: str, reason: str) -> None:
        self.assertEqual(policy.route(fields), {"lane": lane, "reason": reason})

    def test_override_wins_over_every_rule(self) -> None:
        self.assert_routes({**CARD_SIZED, "lane": "solo",
                            "named_paths": ["hooks/guard_hook.py"]}, "solo", "override")

    def test_invalid_override_is_ignored(self) -> None:
        self.assert_routes({**CARD_SIZED, "lane": "turbo"}, "fast-track", "card_sized")

    def test_hook_path_routes_full(self) -> None:
        self.assert_routes({**CARD_SIZED, "named_paths": ["plugins/x/hooks/hooks.json"]},
                           "full", "hook")

    def test_security_path_routes_full(self) -> None:
        self.assert_routes({**CARD_SIZED, "named_paths": ["src/authToken.py"]},
                           "full", "security_path")

    def test_no_named_paths_routes_full(self) -> None:
        self.assert_routes({"design": "skip"}, "full", "unparsed")

    def test_design_not_skipped_routes_full(self) -> None:
        self.assert_routes({**CARD_SIZED, "design": "required"}, "full", "design")

    def test_docs_and_tests_only_routes_solo(self) -> None:
        self.assert_routes(DOCS_ONLY, "solo", "no_production_code")

    def test_card_sized_production_routes_fast_track(self) -> None:
        self.assert_routes(CARD_SIZED, "fast-track", "card_sized")

    def test_uncardable_production_routes_full(self) -> None:
        self.assert_routes({**CARD_SIZED, "plan_cards": 0}, "full", "uncardable")

    def test_missing_production_paths_never_routes_solo(self) -> None:
        fields = {key: value for key, value in DOCS_ONLY.items() if key != "production_paths"}
        self.assertNotEqual(policy.route(fields)["lane"], "solo")

    def test_non_mapping_input_routes_full(self) -> None:
        self.assert_routes(None, "full", "unparsed")


class PolicyBindTest(unittest.TestCase):
    def test_binds_each_known_lane(self) -> None:
        for lane in ("solo", "fast-track", "full"):
            with self.subTest(lane=lane):
                self.assertEqual(policy.bind(lane, "card_sized"),
                                 {"lane": lane, "lane_reason": "card_sized"})

    def test_rejects_unknown_lane_as_rejected_evidence(self) -> None:
        for lane in ("turbo", "", None, "FULL"):
            with self.subTest(lane=lane):
                with self.assertRaises(protocol.ProtocolError) as caught:
                    policy.bind(lane, "override")
                self.assertEqual(caught.exception.code, "rejected_evidence")


if __name__ == "__main__":
    unittest.main()

"""Pure plan validation, plan-size ceiling, and lane routing in the controller policy."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import policy, protocol, schema, tasks


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


def record(task_id: str, status: str = "pending", *depends: str) -> dict:
    return {"id": task_id, "subject": "work", "status": status, "depends_on": list(depends)}


def stored(*records: dict) -> list[dict]:
    return [{**item, "attempts": []} for item in records]


class TaskReducerCase(unittest.TestCase):
    def assert_rejected(self, call, *args) -> None:
        with self.assertRaises(protocol.ProtocolError) as caught:
            call(*args)
        self.assertEqual(caught.exception.code, "rejected_evidence")

    def assert_schema_valid(self, result: list[dict]) -> None:
        for item in result:
            schema._task(item)


class TaskReplaceTest(TaskReducerCase):
    def test_full_replace_adds_empty_attempts_to_every_task(self) -> None:
        plan = [record("a", "completed"), record("b", "aborted", "a"), record("c", "pending", "b")]
        result = tasks.replace(plan)
        self.assertEqual(result, stored(*plan))
        self.assert_schema_valid(result)
        self.assertNotIn("attempts", plan[0])

    def test_rejects_cycle_duplicate_and_unknown_dependency(self) -> None:
        bad_plans = {"cycle": [record("a", "pending", "b"), record("b", "pending", "a")],
                     "duplicate": [record("a"), record("a")],
                     "unknown": [record("a", "pending", "ghost")]}
        for reason, plan in bad_plans.items():
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(policy.InvalidPlan, reason):
                    tasks.replace(plan)

    def test_rejects_plan_over_fifteen_tasks_without_expansion(self) -> None:
        plan = [record(str(n)) for n in range(16)]
        with self.assertRaisesRegex(policy.InvalidPlan, "ceiling"):
            tasks.replace(plan)
        self.assertEqual(len(tasks.replace(plan, allow_expansion=True)), 16)

    def test_rejects_records_the_schema_would_reject(self) -> None:
        bad_records = {"status": {**record("a"), "status": "done"},
                       "subject": {**record("a"), "subject": ""},
                       "extra key": {**record("a"), "attempts": []},
                       "long id": record("x" * 257)}
        for reason, item in bad_records.items():
            with self.subTest(reason=reason):
                with self.assertRaises(policy.InvalidPlan):
                    tasks.replace([item])


class TaskStartTest(TaskReducerCase):
    def test_starts_task_whose_dependencies_all_completed(self) -> None:
        current = stored(record("a", "completed"), record("b", "pending", "a"))
        result = tasks.start(current, "b")
        self.assertEqual(result[1]["status"], "in_progress")
        self.assertEqual(current[1]["status"], "pending")
        self.assert_schema_valid(result)

    def test_rejects_start_when_a_dependency_is_not_completed(self) -> None:
        for status in ("pending", "in_progress", "aborted"):
            with self.subTest(status=status):
                current = stored(record("a", status), record("b", "pending", "a"))
                self.assert_rejected(tasks.start, current, "b")

    def test_rejects_start_of_task_already_started_or_closed(self) -> None:
        for status in ("in_progress", "completed", "aborted"):
            with self.subTest(status=status):
                self.assert_rejected(tasks.start, stored(record("a", status)), "a")

    def test_rejects_start_of_unknown_task(self) -> None:
        self.assert_rejected(tasks.start, stored(record("a")), "ghost")


class TaskFinishTest(TaskReducerCase):
    def test_finish_sets_outcome_status(self) -> None:
        for outcome in ("completed", "aborted"):
            with self.subTest(outcome=outcome):
                current = stored(record("a", "in_progress"))
                result = tasks.finish(current, "a", outcome)
                self.assertEqual(result[0]["status"], outcome)
                self.assertEqual(current[0]["status"], "in_progress")
                self.assert_schema_valid(result)

    def test_rejects_finish_without_prior_start(self) -> None:
        for status in ("pending", "completed", "aborted"):
            with self.subTest(status=status):
                self.assert_rejected(tasks.finish, stored(record("a", status)), "a", "completed")

    def test_rejects_unknown_task_and_unknown_outcome(self) -> None:
        current = stored(record("a", "in_progress"))
        self.assert_rejected(tasks.finish, current, "ghost", "completed")
        self.assert_rejected(tasks.finish, current, "a", "stalled")


class TaskAttemptTest(TaskReducerCase):
    def test_attempt_appends_without_touching_status(self) -> None:
        current = stored(record("a", "in_progress"))
        result = tasks.attempt(current, "a", "devon", "stalled")
        self.assertEqual(result[0]["attempts"], [{"implementor": "devon", "outcome": "stalled"}])
        self.assertEqual(result[0]["status"], "in_progress")
        self.assertEqual(current[0]["attempts"], [])
        self.assert_schema_valid(result)

    def test_replayed_attempt_appends_again_because_dedup_belongs_to_dispatcher(self) -> None:
        once = tasks.attempt(stored(record("a", "in_progress")), "a", "devon", "completed")
        twice = tasks.attempt(once, "a", "devon", "completed")
        self.assertEqual(len(once[0]["attempts"]), 1)
        self.assertEqual(twice[0]["attempts"], [{"implementor": "devon", "outcome": "completed"}] * 2)
        self.assertIsNot(twice[0]["attempts"][0], once[0]["attempts"][0])

    def test_rejects_unknown_task_and_unknown_outcome(self) -> None:
        current = stored(record("a", "in_progress"))
        self.assert_rejected(tasks.attempt, current, "ghost", "devon", "completed")
        self.assert_rejected(tasks.attempt, current, "a", "devon", "passed")
        self.assert_rejected(tasks.attempt, current, "a", "", "completed")


if __name__ == "__main__":
    unittest.main()

"""Rework 17, review cycle 2: contract rule C4 (PRD 00019).

Caller-supplied job specs are closed and well-formed, derived specs carry real
digests and derived requirements, job.next hands out a standalone instruction,
and a stored spec without the new metadata is never offered for execution.

Every test drives the public dispatcher (main.py apply) with a real request
file and a real actor credential.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

from controller_cli_support import canonical, fresh_request, private_path
from controller_owner_support import OwnerCLITest, operation

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import files, schema

PRD = "00042-sample.md"
PRD_TEXT = "---\ndefault_model: opus\n---\n# PRD\n"
BUCKETS = ("backlog", "wip", "hold", "done")
SPEC_KEYS = {"job_id", "role", "depends_on", "input_digests", "isolation", "tier",
             "effort", "source_digest", "resource_digest", "permitted_operations"}
INSTRUCTION_KEYS = SPEC_KEYS | {"instruction"}
EXIT = {"outcome": "succeeded", "native_session_id": "session-1"}
PLAN = [{"id": "t1", "subject": "build it", "status": "pending", "depends_on": []},
        {"id": "t2", "subject": "review it", "status": "in_progress", "depends_on": []},
        {"id": "t3", "subject": "already done", "status": "completed", "depends_on": []},
        {"id": "t4", "subject": "dropped", "status": "aborted", "depends_on": []}]


def spec(job_id: str, *depends: str, **overrides: object) -> dict:
    value = {"job_id": job_id, "role": "builder", "depends_on": list(depends),
             "input_digests": ["a" * 64], "isolation": "worktree", "tier": "opus",
             "effort": "high", "source_digest": "b" * 64, "resource_digest": "c" * 64,
             "permitted_operations": ["read"]}
    value.update(overrides)
    return value


def row(job_spec: dict) -> dict:
    return {"spec": job_spec, "claimed_by": None, "claim_epoch": None, "exit_fact": None}


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def state_at(root: Path) -> dict:
    return json.loads((private_path(root) / "state.json").read_bytes())


def open_workflow(test: OwnerCLITest, name: str) -> tuple[Path, Path]:
    """Open a second real workflow in its own project root; return root and actor."""
    root = test.base / name
    for bucket in BUCKETS:
        (root / files.PRD_ROOT / bucket).mkdir(parents=True)
    (root / files.PRD_ROOT / "backlog" / PRD).write_text(PRD_TEXT)
    opened = test.response(test.apply(fresh_request(root, f"open-{name}"), root=root))
    return root, Path(opened["result"]["actor_file"])


def call_at(test: OwnerCLITest, root: Path, actor: Path, name: str, payload: dict) -> dict:
    request = operation(root, actor, name, f"{name}-{test.serial}",
                        state_at(root)["revision"], payload)
    return test.response(test.apply(request, actor, root=root))


class JobCLITest(OwnerCLITest):
    def setUp(self) -> None:
        super().setUp()
        for bucket in BUCKETS:
            (self.root / files.PRD_ROOT / bucket).mkdir(parents=True)
        (self.root / files.PRD_ROOT / "backlog" / PRD).write_text(PRD_TEXT)
        _, opened, self.operator = self.bootstrap()
        self.actor_id = opened["result"]["actor_id"]

    def call(self, name: str, payload: dict) -> dict:
        request = self.request(self.operator, name, f"{name}-{self.serial}", payload)
        response = self.response(self.apply(request, self.operator))
        self.assertEqual(response["revision"], self.state()["revision"])
        return response

    def reject(self, name: str, payload: dict, error: str) -> None:
        request = self.request(self.operator, name, f"{name}-rejected-{self.serial}", payload)
        self.reject_unchanged(request, self.operator, error)

    def specs(self) -> list[dict]:
        return [item["spec"] for item in self.state()["workflow"]["jobs"]]


# -- C4.1 a caller spec is a closed, well-formed object ----------------------


class CallerSpecTest(JobCLITest):
    def test_a_malformed_caller_spec_is_an_invalid_request_not_a_recovery(self) -> None:
        broken = {
            "unknown key": {**spec("build"), "priority": 1},
            "missing effort": {key: value for key, value in spec("build").items()
                               if key != "effort"},
            "missing source digest": {key: value for key, value in spec("build").items()
                                      if key != "source_digest"},
            "uppercase source digest": spec("build", source_digest="B" * 64),
            "short resource digest": spec("build", resource_digest="c" * 63),
            "long source digest": spec("build", source_digest="b" * 65),
            "nonhex input digest": spec("build", input_digests=["z" * 64]),
            "empty permitted operations": spec("build", permitted_operations=[]),
            "blank permitted operation": spec("build", permitted_operations=["read", ""]),
            "unlisted permitted operations": spec("build", permitted_operations="read"),
        }
        for case, value in broken.items():
            with self.subTest(case=case):
                self.reject("job.plan", {"jobs": [value]}, "invalid_request")
        self.assertEqual(self.specs(), [])

    def test_a_complete_caller_spec_is_planned_and_stored_verbatim(self) -> None:
        planned = self.call("job.plan", {"jobs": [spec("build"),
                                                  spec("review", "build", tier="sonnet")]})

        self.assertEqual(planned["result"], {"job_count": 2})
        self.assertEqual(self.specs(), [spec("build"), spec("review", "build", tier="sonnet")])


# -- C4.2 derived specs carry real digests and derived requirements ----------


class DerivedSpecTest(JobCLITest):
    def setUp(self) -> None:
        super().setUp()
        self.call("prd.enter", {"prds": [PRD]})
        self.call("task.replace", {"tasks": copy.deepcopy(PLAN), "allow_expansion": False})

    def requirements(self, *, phase: str, lane: str, tier: str) -> tuple:
        state = self.state()
        state["workflow"]["jobs"] = []
        state["workflow"]["work"].update(phase=phase, lane=lane, lane_reason="override",
                                         task_tier=tier)
        self.seed(state)
        self.call("job.plan", {"jobs": []})
        first = min(self.specs(), key=lambda value: value["source_digest"])
        return (first["role"], first["isolation"], first["tier"], first["effort"],
                tuple(first["permitted_operations"]))

    def test_derived_specs_cover_only_unfinished_tasks_and_digest_their_own_rows(self) -> None:
        rows = self.state()["workflow"]["tasks"]
        unfinished = [item for item in rows if item["status"] in ("pending", "in_progress")]
        finished = [item for item in rows if item["status"] in ("completed", "aborted")]

        planned = self.call("job.plan", {"jobs": []})

        self.assertEqual(planned["result"], {"job_count": 2})
        sources = {value["source_digest"] for value in self.specs()}
        self.assertEqual(sources, {digest(item) for item in unfinished})
        self.assertFalse(sources & {digest(item) for item in finished})
        for value in self.specs():
            self.assertEqual(set(value), SPEC_KEYS)
            self.assertRegex(value["resource_digest"], r"^[0-9a-f]{64}$")
        resources = {value["resource_digest"] for value in self.specs()}
        self.assertEqual(len(resources), 1, "one PRD is one resource")
        self.assertFalse(resources & sources)

    def test_the_resource_digest_follows_the_active_prd_name(self) -> None:
        self.call("job.plan", {"jobs": []})
        first = {value["resource_digest"] for value in self.specs()}
        state = self.state()
        state["workflow"]["jobs"] = []
        state["workflow"]["work"]["prd"] = "00043-other.md"
        self.seed(state)

        self.call("job.plan", {"jobs": []})

        second = {value["resource_digest"] for value in self.specs()}
        self.assertEqual((len(first), len(second)), (1, 1))
        self.assertFalse(first & second)

    def test_the_resource_digest_follows_the_repo_root_while_the_source_digest_follows_rows(
            self) -> None:
        self.call("job.plan", {"jobs": []})
        local = self.specs()
        root, actor = open_workflow(self, "other-project")
        call_at(self, root, actor, "prd.enter", {"prds": [PRD]})
        call_at(self, root, actor, "task.replace",
                {"tasks": copy.deepcopy(PLAN), "allow_expansion": False})

        call_at(self, root, actor, "job.plan", {"jobs": []})

        other = [item["spec"] for item in state_at(root)["workflow"]["jobs"]]
        self.assertEqual({value["source_digest"] for value in other},
                         {value["source_digest"] for value in local})
        self.assertFalse({value["resource_digest"] for value in other}
                         & {value["resource_digest"] for value in local})

    def test_the_derived_requirements_change_with_the_phase_the_lane_and_the_task_tier(
            self) -> None:
        baseline = self.requirements(phase="build", lane="solo", tier="opus")

        variants = {"phase": {"phase": "review", "lane": "solo", "tier": "opus"},
                    "lane": {"phase": "build", "lane": "full", "tier": "opus"},
                    "task tier": {"phase": "build", "lane": "solo", "tier": "sonnet"}}
        for changed, variant in variants.items():
            with self.subTest(changed=changed):
                self.assertNotEqual(self.requirements(**variant), baseline)
        role, isolation, tier, effort, permitted = baseline
        for value in (role, isolation, tier, effort):
            self.assertIsInstance(value, str)
            self.assertTrue(value)
        self.assertTrue(permitted)
        self.assertTrue(all(isinstance(value, str) and value for value in permitted))


# -- C4.3 job.next is a standalone instruction -------------------------------


class NextInstructionTest(JobCLITest):
    def test_job_next_returns_the_whole_spec_and_an_instruction_for_each_job(self) -> None:
        first = spec("build", permitted_operations=["read"])
        second = spec("review", "build", role="reviewer", isolation="container",
                      tier="sonnet", effort="low", input_digests=["f" * 64, "0" * 64],
                      source_digest="d" * 64, resource_digest="e" * 64,
                      permitted_operations=["read", "write"])
        self.call("job.plan", {"jobs": [first, second]})

        offered = self.call("job.next", {})["result"]

        self.assertEqual(set(offered), INSTRUCTION_KEYS)
        self.assertEqual({key: offered[key] for key in SPEC_KEYS}, first)
        self.assertIsInstance(offered["instruction"], str)
        self.assertTrue(offered["instruction"].strip())
        self.call("job.claim", {"job_id": "build"})
        self.call("job.record_exit", {"job_id": "build", "exit_fact": dict(EXIT)})
        offered = self.call("job.next", {})["result"]
        self.assertEqual({key: offered[key] for key in SPEC_KEYS}, second)
        self.assertTrue(offered["instruction"].strip())


# -- C4.4 a stored spec without the new metadata validates but never runs ----


class StoredSpecTest(JobCLITest):
    def seed_rows(self, legacy: dict) -> None:
        state = self.state()
        state["workflow"]["jobs"] = [row(legacy), row(spec("ready"))]
        self.assertEqual(schema.validate_state(copy.deepcopy(state)), state)
        self.seed(state)

    def test_a_stored_spec_missing_the_new_metadata_is_never_offered_or_claimed(self) -> None:
        for missing in ("source_digest", "resource_digest", "permitted_operations"):
            with self.subTest(missing=missing):
                self.seed_rows({key: value for key, value in spec("legacy").items()
                                if key != missing})

                offered = self.call("job.next", {})["result"]

                self.assertEqual(offered["job_id"], "ready")
                self.reject("job.claim", {"job_id": "legacy"}, "rejected_evidence")

    def test_a_stored_spec_with_the_new_metadata_is_offered_and_claimable(self) -> None:
        self.seed_rows(spec("legacy"))

        offered = self.call("job.next", {})["result"]

        self.assertEqual(offered["job_id"], "legacy")
        claimed = self.call("job.claim", {"job_id": "legacy"})
        self.assertEqual(claimed["result"], {"job_id": "legacy", "claimed_by": self.actor_id,
                                             "claim_epoch": 0})


if __name__ == "__main__":
    unittest.main()

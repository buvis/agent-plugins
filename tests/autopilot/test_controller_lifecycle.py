"""PRD frontmatter, candidate selection and the lifecycle reducers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import actors, files, lifecycle, schema
from autopilot_state.frontmatter import (
    MALFORMED_WARNING,
    command_for,
    defaults,
    overwrite_warnings,
    parse,
)
from autopilot_state.protocol import ProtocolError
from autopilot_state.store import StateStore

PRD = """---
catchup: skip
design: skip
rework_cap: 4
design_gate: user
pause_on_ambiguity: true
default_model: opus
eligibility: "test -f docs/x.md"
---
# PRD body
"""


class ParseTest(unittest.TestCase):
    def test_reads_every_declared_field_from_the_frontmatter_block(self) -> None:
        fields, warnings = parse(PRD, available_tiers={"opus", "sonnet"})
        self.assertEqual(fields, {
            "catchup_mode": "skip",
            "design_mode": "skip",
            "rework_cap": 4,
            "design_gate": "user",
            "pause_on_ambiguity": True,
            "tier": "opus",
        })
        self.assertEqual(warnings, [])

    def test_fills_absent_fields_with_defaults(self) -> None:
        self.assertEqual(defaults(),
                         {"catchup_mode": "run", "design_mode": "run", "rework_cap": 2})
        fields, warnings = parse("---\ntitle: x\n---\n")
        self.assertEqual(fields, defaults())
        self.assertEqual(warnings, [])

    def test_missing_block_defaults_with_malformed_warning(self) -> None:
        fields, warnings = parse("# no frontmatter\n")
        self.assertEqual(fields, defaults())
        self.assertEqual(warnings, [MALFORMED_WARNING])

    def test_closing_fence_beyond_head_window_is_malformed(self) -> None:
        text = "---\n" + "x: y\n" * 20 + "catchup: skip\n---\n"
        self.assertEqual(parse(text), (defaults(), [MALFORMED_WARNING]))

    def test_invalid_values_keep_defaults_and_warn(self) -> None:
        text = "---\ncatchup: maybe\nrework_cap: 0\ndefault_model: opus\n---\n"
        fields, warnings = parse(text)
        self.assertEqual(fields, defaults())
        self.assertEqual(len(warnings), 3)
        self.assertIn("catchup='maybe'", warnings[0])
        self.assertIn("rework_cap='0'", warnings[1])
        self.assertIn("tier 'opus' is unavailable", warnings[2])


class OverwriteWarningsTest(unittest.TestCase):
    def test_flags_only_values_that_replace_a_different_prior_value(self) -> None:
        existing = {"rework_cap": 3, "design_mode": "run"}
        effective = {"rework_cap": 2, "design_mode": "run", "catchup_mode": "skip"}
        self.assertEqual(overwrite_warnings(existing, effective),
                         ["ovcaq: PRD frontmatter reset rework_cap 3 -> 2"])

    def test_unchanged_and_new_keys_are_silent(self) -> None:
        self.assertEqual(overwrite_warnings({"rework_cap": 2}, defaults()), [])
        self.assertEqual(overwrite_warnings({}, defaults()), [])


class CommandForTest(unittest.TestCase):
    def test_returns_unquoted_eligibility_command(self) -> None:
        self.assertEqual(command_for(PRD), "test -f docs/x.md")

    def test_strips_only_one_layer_of_matching_quotes(self) -> None:
        text = "---\neligibility: \"'test $(ls 'a b')'\"\n---\n"
        self.assertEqual(command_for(text), "'test $(ls 'a b')'")
        self.assertEqual(command_for("---\neligibility: 'true\n---\n"), "'true")

    def test_returns_none_when_absent(self) -> None:
        self.assertIsNone(command_for("---\ncatchup: run\n---\n"))
        self.assertIsNone(command_for("---\neligibility: \"\"\n---\n"))
        self.assertIsNone(command_for("no frontmatter\n"))


# -- lifecycle: temporary project roots, never this repo's own state ----------

BUCKETS = ("backlog", "wip", "hold", "done")
PROJECT_ID = "a" * 64
WORKFLOW_ID = "workflow-test"
OPERATOR = {"actor_id": "operator-test", "project_id": PROJECT_ID,
            "workflow_id": WORKFLOW_ID, "role": "operator", "lease_epoch": 0,
            "native_session_id": None, "secret_digest": "b" * 64}


def prd_text(eligibility: str | None = None) -> str:
    line = "" if eligibility is None else f"eligibility: {eligibility}\n"
    return f"---\n{line}---\n# PRD\n"


def make_root(tmp_path: Path, *, wip: dict | None = None,
              backlog: dict | None = None) -> Path:
    root = tmp_path.resolve() / "project"
    for name in BUCKETS:
        (root / files.PRD_ROOT / name).mkdir(parents=True)
    for bucket, entries in (("wip", wip or {}), ("backlog", backlog or {})):
        for name, text in entries.items():
            (root / files.PRD_ROOT / bucket / name).write_text(text)
    return root


def make_store(root: Path, *, work: dict | None = None,
               completed: tuple[str, ...] = ()) -> StateStore:
    controller = root / ".autopilot" / "controller"
    controller.mkdir(parents=True)
    store = StateStore(controller / "state.json")
    state = schema.new_state(repo_root=root, project_id=PROJECT_ID, workflow_id=WORKFLOW_ID)
    state["actors"] = {OPERATOR["actor_id"]: OPERATOR}
    state["workflow"]["batch"] = {"completed_prds": list(completed), "parks_consecutive": 0}
    state["workflow"]["work"] = work
    store.initialize(state)
    return store


def work(prd: str, phase: str = "build", completed_phases: tuple[str, ...] = ()) -> dict:
    return {"prd": prd, "source": "wip", "entered_at": "2026-11-24T10:00:00Z",
            "phase": phase, "completed_phases": list(completed_phases),
            "lane": None, "lane_reason": None}


def request(store: StateStore, operation: str, payload: dict,
            request_id: str | None = None) -> dict:
    revision = store.read()["revision"]
    return {"protocol_major": 1, "operation": operation,
            "request_id": request_id or f"req-{operation}-{revision}",
            "expected_revision": revision, "project_id": PROJECT_ID,
            "workflow_id": WORKFLOW_ID, "actor_id": OPERATOR["actor_id"], "job_id": None,
            "lease_epoch": 0, "payload": payload}


def run(reducer, store: StateStore, operation: str, payload: dict) -> dict:
    return reducer(store, request(store, operation, payload), store.read())


def bucket_of(root: Path, prd: str) -> list[str]:
    return [name for name in BUCKETS if (root / files.PRD_ROOT / name / prd).exists()]


def rejected(reducer, store: StateStore, operation: str, payload: dict) -> None:
    before = store.read()
    with pytest.raises(ProtocolError) as caught:
        run(reducer, store, operation, payload)
    assert caught.value.code == "rejected_evidence"
    assert store.read() == before


def test_select_eligible_reports_drained_with_no_skips_when_queues_are_empty(tmp_path):
    root = make_root(tmp_path)
    assert lifecycle.select_eligible(root) == {"prd": None, "source": "drained", "skipped": []}


def test_select_eligible_distinguishes_ineligible_backlog_from_an_empty_one(tmp_path):
    root = make_root(tmp_path, backlog={"00002-a.md": prd_text("exit 3"),
                                        "00003-b.md": prd_text('"test -f missing.md"')})
    result = lifecycle.select_eligible(root)
    assert (result["prd"], result["source"]) == (None, "drained")
    assert [{key: entry[key] for key in ("prd", "command", "exit_code", "note")}
            for entry in result["skipped"]] == [
        {"prd": "00002-a.md", "command": "exit 3", "exit_code": 3, "note": ""},
        {"prd": "00003-b.md", "command": "test -f missing.md", "exit_code": 1, "note": ""},
    ]
    assert all(entry["at"].endswith("Z") for entry in result["skipped"])
    assert bucket_of(root, "00002-a.md") == ["backlog"]


def test_select_eligible_takes_wip_before_a_lower_backlog_number(tmp_path):
    root = make_root(tmp_path, wip={"00005-w.md": prd_text("exit 1")},
                     backlog={"00001-b.md": prd_text()})
    assert lifecycle.select_eligible(root) == {"prd": "00005-w.md", "source": "wip",
                                               "skipped": []}


def test_select_eligible_runs_checks_from_project_root_and_skips_unmet(tmp_path):
    check = "test -f docs/dev/project-management/prds/backlog/00002-ok.md"
    root = make_root(tmp_path, backlog={"00001-no.md": prd_text("exit 1"),
                                        "00002-ok.md": prd_text(check),
                                        "notes.md": prd_text()})
    result = lifecycle.select_eligible(root)
    assert (result["prd"], result["source"]) == ("00002-ok.md", "backlog")
    assert [entry["prd"] for entry in result["skipped"]] == ["00001-no.md"]
    assert bucket_of(root, "00002-ok.md") == ["backlog"]


def test_evaluate_reports_a_check_that_cannot_answer_as_minus_one(tmp_path):
    assert lifecycle.evaluate("sleep 5", tmp_path, timeout=0.1) == (-1, "timeout")
    assert lifecycle.evaluate("exit 4", tmp_path) == (4, "")


def test_enter_picks_wip_before_backlog_and_moves_nothing(tmp_path):
    root = make_root(tmp_path, wip={"00009-w.md": prd_text()},
                     backlog={"00001-b.md": prd_text()})
    store = make_store(root)
    response = run(lifecycle.enter, store, "prd.enter",
                   {"prds": ["00001-b.md", "00009-w.md"]})
    assert response["ok"] and response["result"] == {"prd": "00009-w.md", "source": "wip"}
    entered = store.read()
    assert response["revision"] == entered["revision"]
    assert entered["workflow"]["work"]["prd"] == "00009-w.md"
    assert entered["workflow"]["work"]["phase"] == "build"
    assert bucket_of(root, "00001-b.md") == ["backlog"]


def test_enter_moves_the_lowest_backlog_sequence_into_wip(tmp_path):
    root = make_root(tmp_path, backlog={"00003-c.md": prd_text(), "00002-b.md": prd_text()})
    store = make_store(root)
    response = run(lifecycle.enter, store, "prd.enter",
                   {"prds": ["00003-c.md", "00002-b.md"]})
    assert response["result"] == {"prd": "00002-b.md", "source": "backlog"}
    assert bucket_of(root, "00002-b.md") == ["wip"]
    assert bucket_of(root, "00003-c.md") == ["backlog"]
    assert store.read()["workflow"]["work"]["source"] == "backlog"


def test_enter_never_reoffers_a_completed_prd(tmp_path):
    root = make_root(tmp_path, backlog={"00002-b.md": prd_text(), "00003-c.md": prd_text()})
    store = make_store(root, completed=("00002-b.md",))
    response = run(lifecycle.enter, store, "prd.enter",
                   {"prds": ["00002-b.md", "00003-c.md"]})
    assert response["result"]["prd"] == "00003-c.md"
    assert bucket_of(root, "00002-b.md") == ["backlog"]


def test_enter_rejects_when_every_candidate_is_already_completed(tmp_path):
    root = make_root(tmp_path, backlog={"00002-b.md": prd_text()})
    store = make_store(root, completed=("00002-b.md",))
    rejected(lifecycle.enter, store, "prd.enter", {"prds": ["00002-b.md"]})
    assert bucket_of(root, "00002-b.md") == ["backlog"]


def test_enter_replay_returns_the_cached_response_on_a_digest_match(tmp_path):
    root = make_root(tmp_path, backlog={"00002-b.md": prd_text()})
    store = make_store(root)
    replayed = request(store, "prd.enter", {"prds": ["00002-b.md"]}, "req-replayed")
    cached = {"ok": True, "revision": 1, "error_code": None, "retryable": False,
              "result": {"actor_id": OPERATOR["actor_id"],
                         "operator_actor_file": "/tmp/operator.json", "lease_epoch": 0}}

    def seed(state: dict) -> None:
        state["receipts"]["req-replayed"] = {
            "request_digest": actors.digest(actors.canonical(replayed)),
            "authorizing_actor": OPERATOR, "response": cached}

    store.transaction(seed)
    before = store.read()
    assert lifecycle.enter(store, replayed, before) == cached
    assert store.read() == before
    assert bucket_of(root, "00002-b.md") == ["backlog"]
    altered = {**replayed, "payload": {"prds": ["00003-c.md"]}}
    with pytest.raises(ProtocolError) as caught:
        lifecycle.enter(store, altered, before)
    assert caught.value.code == "invalid_request"


def test_handoff_applies_the_known_transition_rows(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md"))
    response = run(lifecycle.handoff, store, "phase.handoff",
                   {"phase": "build", "next_phase": "review", "outcome": "tasks_done"})
    assert response["result"] == {"phase": "review", "next_phase": "review"}
    run(lifecycle.handoff, store, "phase.handoff",
        {"phase": "review", "next_phase": "review", "outcome": "rework"})
    run(lifecycle.handoff, store, "phase.handoff",
        {"phase": "review", "next_phase": "done", "outcome": "converged"})
    finished = store.read()["workflow"]["work"]
    assert (finished["phase"], finished["completed_phases"]) == ("done", ["review"])


def test_handoff_rejects_unknown_pairs_and_mismatched_evidence(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md"))
    rejected(lifecycle.handoff, store, "phase.handoff",
             {"phase": "build", "next_phase": "done", "outcome": "converged"})
    rejected(lifecycle.handoff, store, "phase.handoff",
             {"phase": "build", "next_phase": "done", "outcome": "tasks_done"})
    rejected(lifecycle.handoff, store, "phase.handoff",
             {"phase": "review", "next_phase": "review", "outcome": "tasks_done"})


def test_handoff_requires_recovery_idle(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md"))

    def stamp(state: dict) -> None:
        state["workflow"]["recovery"] = {"op": "pending", "boundary": "intent"}

    store.transaction(stamp)
    rejected(lifecycle.handoff, store, "phase.handoff",
             {"phase": "build", "next_phase": "review", "outcome": "tasks_done"})


@pytest.mark.parametrize("phase,completed_phases", [
    ("build", ()), ("review", ()), ("done", ()),
])
def test_false_success_cannot_complete_without_review(tmp_path, phase, completed_phases):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md", phase, completed_phases))
    rejected(lifecycle.complete, store, "prd.complete", {})
    assert bucket_of(root, "00002-b.md") == ["wip"]
    assert store.read()["workflow"]["batch"]["completed_prds"] == []


def test_drained_build_reaches_done_but_still_cannot_complete(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md"))
    run(lifecycle.handoff, store, "phase.handoff",
        {"phase": "build", "next_phase": "", "outcome": "drained"})
    assert store.read()["workflow"]["work"]["phase"] == "done"
    rejected(lifecycle.complete, store, "prd.complete", {})
    assert bucket_of(root, "00002-b.md") == ["wip"]


def test_complete_rejects_without_an_active_prd(tmp_path):
    root = make_root(tmp_path)
    store = make_store(root)
    rejected(lifecycle.complete, store, "prd.complete", {})


def test_complete_after_review_moves_once_and_records_the_prd(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md", "review"))
    run(lifecycle.handoff, store, "phase.handoff",
        {"phase": "review", "next_phase": "done", "outcome": "converged"})
    response = run(lifecycle.complete, store, "prd.complete", {})
    assert response["result"] == {"prd": "00002-b.md"}
    final = store.read()
    assert response["revision"] == final["revision"]
    assert bucket_of(root, "00002-b.md") == ["done"]
    assert final["workflow"]["batch"]["completed_prds"] == ["00002-b.md"]
    assert final["workflow"]["work"] is None and final["workflow"]["recovery"] is None
    rejected(lifecycle.complete, store, "prd.complete", {})


def test_reset_prd_fields_preserves_batch_and_clears_per_prd_fields():
    batch = {"completed_prds": ["00001-a.md"], "parks_consecutive": 1}
    workflow = {"batch": batch, "review": {"cap": 2}, "recovery": None, "jobs": [],
                "work": {**work("00002-b.md", "done", ("review",)),
                         "lane": "full", "lane_reason": "design"},
                "tasks": [{"id": "t1", "subject": "x", "status": "completed",
                           "depends_on": [], "attempts": []}]}
    reset = lifecycle.reset_prd_fields(workflow)
    assert reset["batch"] == batch
    assert reset["work"] == {**work("00002-b.md"), "lane": None, "lane_reason": None}
    assert reset["tasks"] == []
    assert workflow["work"]["phase"] == "done" and workflow["tasks"]


if __name__ == "__main__":
    unittest.main()

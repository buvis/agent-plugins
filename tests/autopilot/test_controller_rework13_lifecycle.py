"""Rework 13, review cycle 1: findings 1-3 (PRD 00019 lifecycle.py).

Each test proves one named finding from the rework task description. They
must fail against the unfixed `lifecycle.py`; see the task report for which
findings are genuinely ambiguous.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import lifecycle
from autopilot_state.protocol import ProtocolError

from test_controller_lifecycle import (
    bucket_of, make_root, make_store, prd_text, rejected, request, run, work,
)


# -- finding 1: prd.enter must persist parsed frontmatter, not just 4 fields --


def test_enter_persists_a_nondefault_frontmatter_field_onto_the_committed_work(tmp_path):
    root = make_root(tmp_path, backlog={"00002-b.md": "---\nrework_cap: 4\n---\n# PRD\n"})
    store = make_store(root)
    response = run(lifecycle.enter, store, "prd.enter", {"prds": ["00002-b.md"]})
    assert response["ok"] and response["result"] == {"prd": "00002-b.md", "source": "backlog"}
    committed = store.read()["workflow"]["work"]
    # AMBIGUITY: the PRD names no field to hold the parsed value on `work`;
    # "rework_cap" is assumed, matching the frontmatter parser's own key.
    assert committed["rework_cap"] == 4


def test_enter_defaults_rework_cap_when_the_frontmatter_declares_none(tmp_path):
    root = make_root(tmp_path, backlog={"00003-c.md": prd_text()})
    store = make_store(root)
    run(lifecycle.enter, store, "prd.enter", {"prds": ["00003-c.md"]})
    committed = store.read()["workflow"]["work"]
    assert committed["rework_cap"] == 2


# -- finding 2: a committed rename with no committed entry must self-recover --


def test_enter_recovers_after_a_revision_conflict_following_a_committed_rename(tmp_path):
    from autopilot_state.store import RevisionConflictError

    root = make_root(tmp_path, backlog={"00002-b.md": prd_text()})
    store = make_store(root)
    stale = store.read()
    # Simulate the first prd.enter's rename landing on disk...
    (root / "docs" / "dev" / "project-management" / "prds" / "backlog" / "00002-b.md").rename(
        root / "docs" / "dev" / "project-management" / "prds" / "wip" / "00002-b.md")
    # ...while an intervening commit advances the revision before the entry lands.
    store.transaction(lambda state: None)

    stale_request = request(store, "prd.enter", {"prds": ["00002-b.md"]}, "req-stale")
    stale_request["expected_revision"] = stale["revision"]
    with pytest.raises(RevisionConflictError):
        lifecycle.enter(store, stale_request, stale)
    assert bucket_of(root, "00002-b.md") == ["wip"]
    assert store.read()["workflow"]["work"] is None

    fresh = store.read()
    fresh_request = request(store, "prd.enter", {"prds": ["00002-b.md"]}, "req-fresh")
    response = lifecycle.enter(store, fresh_request, fresh)
    assert response["ok"] and response["result"]["prd"] == "00002-b.md"
    entered = store.read()
    assert entered["workflow"]["work"]["prd"] == "00002-b.md"
    assert bucket_of(root, "00002-b.md") == ["wip"]
    assert entered["revision"] == fresh["revision"] + 1


# -- finding 3: review acceptance must not be bypassable with no evidence -----


def test_bypass_review_via_handoff_converged_is_rejected_without_evidence(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md", "review"))
    try:
        run(lifecycle.handoff, store, "phase.handoff",
            {"phase": "review", "next_phase": "done", "outcome": "converged"})
    except ProtocolError as error:
        assert error.code == "rejected_evidence"
        return
    # The transition was accepted with no review evidence ever recorded:
    # prd.complete must refuse to close the PRD on that basis.
    rejected(lifecycle.complete, store, "prd.complete", {})

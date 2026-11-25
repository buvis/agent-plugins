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
from autopilot_state.store import DurabilityBoundary, StateStore

from test_controller_lifecycle import (
    bucket_of, make_root, make_store, prd_text, request, run, work,
)


class InterruptedCommit(Exception):
    """The crash the store's boundary hook injects mid-publication."""


def crash_before_the_entry_is_published(boundary: DurabilityBoundary) -> None:
    if boundary is DurabilityBoundary.STATE_TEMP_FSYNCED:
        raise InterruptedCommit(boundary)


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


def test_enter_self_recovers_after_a_committed_rename_with_no_committed_entry(tmp_path):
    root = make_root(tmp_path, backlog={"00002-b.md": prd_text()})
    store = make_store(root)
    interrupted = StateStore(store.path, boundary_hook=crash_before_the_entry_is_published)
    before = store.read()
    enter_request = request(store, "prd.enter", {"prds": ["00002-b.md"]}, "req-enter")

    # The real operation renames backlog/ -> wip/ and then crashes before its
    # entry is published, which is the committed-rename, no-committed-entry state.
    with pytest.raises(InterruptedCommit):
        lifecycle.enter(interrupted, enter_request, before)
    assert bucket_of(root, "00002-b.md") == ["wip"]
    assert store.read() == before

    # Replaying that same request self-recovers: it enters the renamed PRD and
    # records the bucket the committed rename left it in (see the task report:
    # the recovered entry reports "wip", not the original "backlog").
    response = lifecycle.enter(store, enter_request, store.read())
    assert response["ok"] and response["result"] == {"prd": "00002-b.md", "source": "wip"}
    entered = store.read()
    assert entered["workflow"]["work"]["prd"] == "00002-b.md"
    assert entered["workflow"]["work"]["source"] == "wip"
    assert bucket_of(root, "00002-b.md") == ["wip"]
    # Exactly one commit: the interrupted attempt published nothing.
    assert entered["revision"] == before["revision"] + 1


# -- finding 3: review acceptance must not be bypassable with no evidence -----


@pytest.mark.xfail(strict=True, reason="review acceptance deferred to AP 00020")
def test_bypass_review_via_handoff_converged_is_rejected_without_evidence(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md", "review"))
    with pytest.raises(ProtocolError) as caught:
        run(lifecycle.handoff, store, "phase.handoff",
            {"phase": "review", "next_phase": "done", "outcome": "converged"})
    assert caught.value.code == "rejected_evidence"
    # A refused claim changes neither the persisted phase nor the PRD's bucket.
    assert store.read()["workflow"]["work"]["phase"] == "review"
    assert bucket_of(root, "00002-b.md") == ["wip"]

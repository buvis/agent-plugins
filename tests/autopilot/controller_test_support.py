"""Shared frozen controller fixtures without runtime imports."""

from __future__ import annotations

import copy
import json

WORKFLOW = {
    "batch": None, "work": None, "tasks": [],
    "review": {"cap": 2}, "recovery": None, "jobs": [],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def actor(*, actor_id: str = "operator-synthetic", role: str = "operator",
          epoch: int = 0, digest: str = "b" * 64) -> dict:
    return {
        "actor_id": actor_id, "project_id": "a" * 64,
        "workflow_id": "workflow-synthetic", "role": role,
        "lease_epoch": epoch,
        "native_session_id": "session-synthetic" if role == "owner" else None,
        "secret_digest": digest,
    }


def frozen_state(*, owned: bool = False) -> dict:
    operator = actor()
    result = {
        "schema_version": 1, "revision": 0, "project_id": "a" * 64,
        "workflow_id": "workflow-synthetic", "repo_root": "/synthetic/project",
        "lease_epoch": 0, "owner": None,
        "actors": {operator["actor_id"]: operator},
        "receipts": {"open-synthetic": {
            "request_digest": "c" * 64, "authorizing_actor": copy.deepcopy(operator),
            "response": {
                "ok": True, "revision": 0, "result": {
                    "workflow_id": "workflow-synthetic",
                    "actor_id": "operator-synthetic",
                    "actor_file": "/synthetic/project/.autopilot/controller/actors/operator.json",
                    "lease_epoch": 0,
                }, "error_code": None, "retryable": False,
            },
        }},
        "workflow": copy.deepcopy(WORKFLOW),
    }
    if owned:
        owner = actor(actor_id="owner-synthetic", role="owner", epoch=1, digest="e" * 64)
        result.update(revision=1, lease_epoch=1, owner={
            "actor_id": owner["actor_id"], "mode": "supervised",
            "native_session_id": owner["native_session_id"], "lease_epoch": 1,
        })
        result["actors"] = {
            "operator-synthetic": actor(epoch=1, digest="d" * 64),
            "owner-synthetic": owner,
        }
    return result

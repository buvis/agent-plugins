"""Shared frozen controller fixtures without runtime imports."""

from __future__ import annotations

import ast
import copy
import json
import os
import subprocess
from pathlib import Path

TESTS = Path(__file__).resolve().parent

WORKFLOW = {
    "batch": None, "work": None, "tasks": [],
    "review": {"cap": 2}, "recovery": None, "jobs": [],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def resolve_test_target(target: str) -> bool:
    """True when `path::name` names a real test under tests/autopilot.

    `path` is relative to the repository root and must stay inside
    tests/autopilot. `name` is a dotted qualified name (`Class.method`,
    `function`) from the module top level, or a bare method name found in any
    class of that module.
    """
    path_text, _, name = target.partition("::")
    path = (TESTS.parents[1] / path_text).resolve()
    if not name or not path.is_file() or TESTS not in path.parents:
        return False
    tree = ast.parse(path.read_text(encoding="utf-8"))
    qualified: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qualified.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified.update({member.name, f"{node.name}.{member.name}"})
    return name in qualified


def commit_all(root: Path, monkeypatch) -> str:
    """Init a repo at `root`, commit everything, return HEAD.

    Global and system git config are replaced by an empty file for the whole
    test (the code under test also shells out to git), so user signing or hook
    settings cannot leak in; identity is explicit.
    """
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.setenv("HOME", str(root))
    identity = ["-c", "user.name=test", "-c", "user.email=test@example.invalid",
                "-c", "commit.gpgsign=false"]
    for args in (["init", "--quiet"], ["add", "-A"],
                 [*identity, "commit", "--quiet", "-m", "initial"]):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


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

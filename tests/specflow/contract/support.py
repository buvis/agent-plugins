"""Shared bootstrap and spec builders for the contract tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "plugins" / "specflow" / "skills" / "spec-workflow"
SCRIPTS = SKILL / "scripts"
FIXTURES = REPO / "tests" / "specflow" / "fixtures"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

REQUIREMENTS = """# Requirements: Sample

Sources: docs/intake/processed/00042-sample

## Purpose

Show the sample.

## Requirements

### REQ-001: Greet

Source: the idea

**User story:** As a user, I want a greeting, so that I feel welcome.

#### Acceptance criteria

1. WHEN the user arrives THE SYSTEM SHALL greet them.
"""
# A Kiro-style title, so the template section check does not apply to this short design.
DESIGN = "# Design Document: Sample\n\n## Overview\n\nGreets.\n"
TASKS = """# Tasks: Sample

- [ ] T-001 Greet the user
  - Requirements: REQ-001
  - Depends on: none
  - Verify: run the greeting test
- [ ] T-002 Log the greeting
  - Requirements: REQ-001
  - Depends on: T-001
  - Verify: run the log test

## Completion criteria

- [ ] Every task above is checked.
"""


def new_state(spec_id: str = "00042-sample", **overrides: object) -> dict:
    state = {
        "schemaVersion": 1,
        "specId": spec_id,
        "specType": "feature",
        "profile": "standard",
        "workflowOrder": "requirements-first",
        "workflowVersion": "0.1.0",
        "artifacts": {
            "requirements": {"path": "requirements.md", "status": "draft"},
            "design": {"path": "design.md", "status": "draft"},
            "tasks": {"path": "tasks.md", "status": "draft"},
        },
    }
    state.update(overrides)
    return state


def write_spec(
    spec_dir: Path,
    files: dict[str, str],
    state: dict | None = None,
) -> Path:
    spec_dir.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (spec_dir / name).write_text(text, encoding="utf-8")
    if state is not None:
        write_state(spec_dir, state)
    return spec_dir


def write_state(spec_dir: Path, state: dict) -> None:
    (spec_dir / ".specflow.json").write_text(json.dumps(state, indent=2) + "\n")


def approve(spec_dir: Path, state: dict, *names: str) -> dict:
    """Record approvals the way the agent does: status, hash, and time."""
    from specflow_helper.canonical import sha256_canonical

    for name in names:
        record = state["artifacts"][name]
        digest = sha256_canonical(spec_dir / record["path"])
        record.update(
            status="approved",
            sha256=digest,
            approvedSha256=digest,
            approvedAt="2026-10-10T10:00:00Z",
        )
    write_state(spec_dir, state)
    return state


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


class TempTest(unittest.TestCase):
    """A temporary folder per test, with git isolated from the user's config."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        patcher = mock.patch.dict(
            os.environ,
            {**GIT_ENV, "GIT_CEILING_DIRECTORIES": str(self.tmp)},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

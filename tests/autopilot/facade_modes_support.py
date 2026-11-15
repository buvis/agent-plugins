"""Shared harness for the facade's job, child, role and session CLI modes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import test_facade


MISSING_SESSION = {"schema_version": 1, "ok": False, "error": "missing_native_session"}
STATE_TREE = Path("docs") / "dev" / "project-management" / "autopilot"


def snapshot(directory: Path) -> dict:
    """Every path under `directory` with its bytes (None for directories)."""
    if not directory.exists():
        return {}
    return {path.relative_to(directory): (None if path.is_dir() else path.read_bytes())
            for path in directory.rglob("*")}


class FacadeModesMixin:
    """Reuses LocalFacadeTest's relocated package and scrubbed environment;
    the scrubbed environment carries no native session variable."""

    def setUp(self) -> None:
        test_facade.LocalFacadeTest.setUp(self)

    def assert_failure(self, result: subprocess.CompletedProcess) -> None:
        test_facade.LocalFacadeTest.assert_failure(self, result)

    def run_facade(self, *arguments: str, env: dict | None = None,
                   stdin: bytes = b"") -> subprocess.CompletedProcess:
        self.assertTrue(self.facade.is_file(), f"Public CLI executable is missing: {self.facade}")
        return subprocess.run(
            [sys.executable, str(self.facade), *arguments], cwd=self.cwd,
            env=dict(self.env) | (env or {}), input=stdin, capture_output=True, timeout=60,
        )

    def one_json(self, result: subprocess.CompletedProcess) -> dict:
        """The single JSON line on stdout, decoded."""
        self.assertTrue(result.stdout.endswith(b"\n"), result.stdout)
        self.assertEqual(result.stdout.count(b"\n"), 1, result.stdout)
        value = json.loads(result.stdout)
        self.assertIsInstance(value, dict)
        return value

    def assert_usage_error(self, result: subprocess.CompletedProcess) -> None:
        self.assertEqual(result.returncode, 2, result.stderr.decode(errors="replace"))
        self.assert_failure(result)

    def assert_refusal(self, result: subprocess.CompletedProcess,
                       error: str | None = None) -> dict:
        """Exit 1 with one `ok: false` JSON line and a silent stderr."""
        self.assertEqual(result.returncode, 1, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stderr, b"")
        reply = self.one_json(result)
        self.assertEqual(set(reply), {"schema_version", "ok", "error"})
        self.assertEqual((reply["schema_version"], reply["ok"]), (1, False))
        self.assertIsInstance(reply["error"], str)
        self.assertTrue(reply["error"])
        if error is not None:
            self.assertEqual(reply["error"], error)
        return reply

    def write_json(self, path: Path, value: object) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

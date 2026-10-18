"""Shared helpers of the review-script tests: load a scan by path, run it, write a document."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[3]
SCRIPTS = REPO / "plugins/specflow/skills/spec-workflow/scripts/review"


def load(script: Path):
    spec = importlib.util.spec_from_file_location(script.stem, script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve the module by name
    spec.loader.exec_module(module)
    return module


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(script), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def document(folder: str, text: str | bytes, name: str = "doc.md") -> Path:
    path = Path(folder) / name
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return path


def temp_folder() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory()

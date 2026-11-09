"""Canonical workflow fixtures, assembled without changing their approval hashes."""

from __future__ import annotations

import collections
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import support
from specflow_helper.schema import check_schema, load_schema

WORKFLOW = support.FIXTURES / "workflow"
CASES = json.loads((WORKFLOW / "inventory.json").read_text(encoding="utf-8"))
SCRIPT = support.SCRIPTS / "validate_spec.py"


def materialize(case: dict, destination: Path) -> None:
    """Copy the listed sources in order; later literal files replace earlier ones."""
    destination.mkdir()
    for entry in case["copies"]:
        source = support.FIXTURES / entry["from"]
        target = destination / entry["to"]
        shutil.copytree(source, target, dirs_exist_ok=True)


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class WorkflowFixturesTest(support.TempTest):
    def run_helper(self, workspace: Path, *args: str) -> tuple[int, dict]:
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *args, "--json"],
            cwd=workspace,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_inventory_covers_the_task_and_has_no_unused_overlays(self) -> None:
        names = [case["name"] for case in CASES]
        self.assertEqual(len(names), len(set(names)))
        required = {
            "standard-feature",
            "standard-bugfix",
            "quick-feature",
            "quick-bugfix",
            "partial-feature",
            "partial-bugfix",
            "stale-feature",
            "completed-feature",
            "completed-bugfix",
            "verification-feature",
            "hold-and-intake",
            "configured-workspace",
            "intake-only",
            "missing-required-path",
            "invalid-state",
            "unsupported-version",
            "recorded-hash-mismatch",
            "spike-standalone",
            "spike-branch",
            "spike-sketch",
            "recovered-requirements-first",
            "recovered-design-first",
            "recovered-bugfix",
            "design-first-partial-feature",
            "design-first-partial-bugfix",
            "design-first-stale-feature",
            "design-first-stale-bugfix",
        }
        self.assertEqual(set(names), required)
        overlays = set()
        for case in CASES:
            for entry in case["copies"]:
                source = support.FIXTURES / entry["from"]
                self.assertTrue(source.is_dir(), source)
                self.assertTrue(source.resolve().is_relative_to(support.FIXTURES))
                target = Path(entry["to"])
                self.assertFalse(target.is_absolute())
                self.assertNotIn("..", target.parts)
                if entry["from"].startswith("workflow/"):
                    overlays.add(source.name)
        self.assertEqual(overlays, {p.name for p in WORKFLOW.iterdir() if p.is_dir()})

    def test_every_workspace_has_exact_status_and_validation_findings(self) -> None:
        for case in CASES:
            with self.subTest(fixture=case["name"]):
                workspace = self.tmp / case["name"]
                materialize(case, workspace)
                before = snapshot(workspace)
                code, document = self.run_helper(workspace, "status")
                invalid = any(s["state"] == "invalid" for s in case["specs"].values())
                self.assertEqual(code, 1 if invalid else 0)
                self.assertEqual(
                    check_schema(document, load_schema("specflow-status.schema.json")),
                    [],
                )
                self.assertEqual(document["problems"], [])
                self.assertEqual(document["intake"], case.get("intake", []))
                actual = {s["spec"]: s for s in document["specs"]}
                self.assertEqual(set(actual), {Path(p).name for p in case["specs"]})
                for relative, expected in case["specs"].items():
                    with self.subTest(spec=relative):
                        self.check_spec(
                            case,
                            workspace,
                            relative,
                            expected,
                            actual[Path(relative).name],
                        )
                for item in case.get("intakeItems", []):
                    self.assertTrue((workspace / item / "qa-log.md").is_file())
                    code, result = self.run_helper(
                        workspace, "validate", item, "--phase", "intake"
                    )
                    self.assertEqual((code, result["findings"]), (0, []))
                self.assertEqual(
                    snapshot(workspace), before, "validation must not repair fixtures"
                )

    def check_spec(
        self, case: dict, workspace: Path, relative: str, expected: dict, actual: dict
    ) -> None:
        self.assertEqual(
            {k: actual[k] for k in expected if k != "order"},
            {k: v for k, v in expected.items() if k != "order"},
        )
        spec = workspace / relative
        state = json.loads((spec / ".specflow.json").read_text(encoding="utf-8"))
        self.assertEqual(state["workflowOrder"], expected["order"])
        self.assertEqual(
            check_schema(state, load_schema("specflow-state.schema.json")),
            case.get("schemaErrors", []),
        )
        self.assertEqual(
            actual["stale"],
            [
                key
                for key in (
                    ("design", "requirements", "tasks")
                    if expected["order"] == "design-first"
                    else ("requirements", "design", "tasks")
                )
                if expected["artifacts"][key] == "stale"
            ],
        )
        if expected["phase"] == "implementation" and not expected["hold"]:
            self.assertIsNotNone(actual["nextTask"])
            self.assertEqual(actual["gates"]["implementation"], "open")
        else:
            self.assertIsNone(actual["nextTask"])
        args = ["validate", relative]
        if "validationPhase" in case:
            args += ["--phase", case["validationPhase"]]
        code, result = self.run_helper(workspace, *args)
        errors = [
            [Path(f["file"]).name, f["rule"], f["message"]]
            for f in result["findings"]
            if f["level"] == "error"
        ]
        self.assertCountEqual(errors, case.get("errors", []))
        self.assertEqual(
            code, 2 if expected["state"] == "invalid" else (1 if errors else 0)
        )
        warnings = collections.Counter(
            f["rule"] for f in result["findings"] if f["level"] == "warning"
        )
        self.assertEqual(dict(warnings), case.get("warningRules", {}))
        if "nativeCapture" in case:
            for name, contents in snapshot(
                support.FIXTURES / case["nativeCapture"]
            ).items():
                self.assertEqual((spec / name).read_bytes(), contents)

    def test_spikes_have_their_form_and_no_canonical_spec(self) -> None:
        for case in CASES:
            if "spikeForm" not in case:
                continue
            with self.subTest(form=case["spikeForm"]):
                workspace = self.tmp / case["name"]
                materialize(case, workspace)
                spike = workspace / case["intakeItems"][0] / "spike"
                rough = (spike / "SPEC.md").read_text(encoding="utf-8")
                for heading in (
                    "## Idea",
                    "## Smallest end-to-end outcome",
                    "## Guessed contract",
                ):
                    self.assertIn(heading, rough)
                self.assertIn("(guess)", rough)
                self.assertFalse((workspace / ".kiro/specs").exists())
                if case["spikeForm"] == "standalone":
                    self.check_greeting(spike / "greeting.py")
                elif case["spikeForm"] == "branch":
                    self.assertEqual(
                        (spike / "branch.txt").read_text(), "spike/00001-greeting\n"
                    )
                    self.check_greeting(workspace / "src/greeting.py")
                else:
                    self.assertEqual(
                        {p.name for p in (spike / "mockups").iterdir()},
                        {"index.html", "greeting.html"},
                    )
                    for page in (spike / "mockups").iterdir():
                        text = page.read_text(encoding="utf-8")
                        self.assertIn("mockup, not functional", text)
                        self.assertIn("Accessibility:", text)
                        self.assertNotIn("<script", text)
                        self.assertNotRegex(text, r"https?://")

    def check_greeting(self, script: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(script)],
            cwd=script.parent,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr), (0, "Hello\n", "")
        )


if __name__ == "__main__":
    unittest.main()

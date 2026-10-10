"""The command line: each operation and each exit code (T-026)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import support
import validate_spec
from specflow_helper.schema import check_schema, load_schema

SCRIPT = support.SCRIPTS / "validate_spec.py"


class CliTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.tmp / "repo"
        self.specs = self.repo / ".kiro" / "specs"
        self.specs.mkdir(parents=True)
        support.git(self.repo, "init", "-q")
        cwd = Path.cwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, cwd)
        self.spec = shutil.copytree(
            support.FIXTURES / "specs" / "00101-feature-sample",
            self.specs / "00101-feature-sample",
        )

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = validate_spec.main(list(args))
        return code, out.getvalue(), err.getvalue()


class ExitCodeTest(CliTest):
    def test_success_is_0(self) -> None:
        code, out, _ = self.run_cli("validate", str(self.spec))
        self.assertEqual((code, out.strip()), (0, "valid"))

    def test_validation_failure_is_1(self) -> None:
        (self.spec / "tasks.md").write_text("# Tasks: x\n\n- [] T-001 broken\n")
        code, out, _ = self.run_cli("validate", str(self.spec), "--json")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["exitCode"], 1)

    def test_malformed_or_unsupported_state_is_2(self) -> None:
        for text in ("{", json.dumps(support.new_state(schemaVersion=2))):
            with self.subTest(text=text[:10]):
                (self.spec / ".specflow.json").write_text(text)
                self.assertEqual(self.run_cli("validate", str(self.spec))[0], 2)
                self.assertEqual(self.run_cli("reconcile", str(self.spec))[0], 2)

    def test_unreadable_artifact_is_2(self) -> None:
        (self.spec / "tasks.md").write_bytes(b"\xff\xfe")
        self.assertEqual(self.run_cli("hash", str(self.spec / "tasks.md"))[0], 2)

    def test_usage_errors_are_3(self) -> None:
        for args in (
            ("bogus",),
            ("approve", str(self.spec)),
            ("validate",),
            ("validate", str(self.repo / "nowhere")),
            ("validate", str(self.spec), "--phase", "done"),
            ("code-baseline", str(self.spec)),
            ("hash", "missing.md"),
        ):
            with self.subTest(args=args):
                code, _, err = self.run_cli(*args)
                self.assertEqual(code, 3)
                self.assertIn("usage error", err)


class OperationTest(CliTest):
    def test_status_json_follows_the_schema_and_exits_0(self) -> None:
        code, out, _ = self.run_cli("status", "--json")
        self.assertEqual(code, 0)
        document = json.loads(out)
        self.assertEqual(
            check_schema(document, load_schema("specflow-status.schema.json")),
            [],
        )
        self.assertEqual(
            [s["spec"] for s in document["specs"]],
            ["00101-feature-sample"],
        )

    def test_status_exits_1_on_a_malformed_state_and_still_prints(self) -> None:
        (self.spec / ".specflow.json").write_text("{")
        code, out, _ = self.run_cli("status", str(self.spec), "--json")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["specs"][0]["state"], "invalid")

    def test_hash_forms(self) -> None:
        path = self.spec / "tasks.md"
        path.write_text(path.read_text().replace("- [ ] T-001", "- [x] T-001"))
        tasks = str(path)
        _, canonical, _ = self.run_cli("hash", tasks)
        _, raw, _ = self.run_cli("hash", tasks, "--raw")
        self.assertEqual(len(canonical.strip()), 64)
        self.assertNotEqual(canonical, raw)
        _, out, _ = self.run_cli("hash", tasks, "--json")
        record = json.loads(out)
        self.assertEqual(list(record), ["sha256", "approvedAt", "workflowVersion"])
        self.assertEqual(record["sha256"], canonical.strip())
        self.assertRegex(record["approvedAt"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_hash_json_records_the_commit_when_there_is_one(self) -> None:
        support.git(self.repo, "add", "-A")
        support.git(self.repo, "commit", "-q", "-m", "c")
        head = support.git(self.repo, "rev-parse", "HEAD").strip()
        _, out, _ = self.run_cli("hash", str(self.spec / "tasks.md"), "--json")
        self.assertEqual(json.loads(out)["approvedCommit"], head)

    def test_code_baseline_prints_an_approved_code_value(self) -> None:
        (self.repo / "src.py").write_text("x\n")
        args = ("code-baseline", str(self.spec), "--paths", "src.py", "new.py")
        code, out, _ = self.run_cli(*args)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "captured")

    def test_code_baseline_outside_git_is_not_checked(self) -> None:
        shutil.rmtree(self.repo / ".git")
        code, out, _ = self.run_cli(
            "code-baseline",
            str(self.spec),
            "--paths",
            "src.py",
        )
        self.assertEqual((code, json.loads(out)["status"]), (0, "not_checked"))

    def test_reconcile_in_both_forms(self) -> None:
        state = support.approve(
            self.spec,
            support.new_state("00101-feature-sample"),
            "design",
        )
        (self.spec / "design.md").write_text(
            (self.spec / "design.md").read_text() + "\nMore.\n",
        )
        before = (self.spec / ".specflow.json").read_bytes()
        code, out, _ = self.run_cli("reconcile", str(self.spec), "--dry-run", "--json")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["changes"])
        self.assertEqual((self.spec / ".specflow.json").read_bytes(), before)
        self.assertEqual(self.run_cli("reconcile", str(self.spec))[0], 0)
        design = json.loads((self.spec / ".specflow.json").read_text())["artifacts"][
            "design"
        ]
        self.assertEqual(design["status"], "stale")
        self.assertEqual(
            design["approvedSha256"],
            state["artifacts"]["design"]["approvedSha256"],
        )


class ProcessTest(CliTest):
    def test_script_runs_from_any_python_start_and_leaves_no_bytecode(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "validate", str(self.spec)],
            capture_output=True,
            text=True,
            check=False,
            cwd=self.tmp,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(support.SCRIPTS.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()

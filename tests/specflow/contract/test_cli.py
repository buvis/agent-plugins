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
from unittest import mock

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
                tasks = str(self.spec / "tasks.md")
                self.assertEqual(self.run_cli("hash", tasks, "--json")[0], 2)
                self.assertEqual(self.run_cli("hash", tasks)[0], 0)

    def test_unreadable_artifact_is_2(self) -> None:
        (self.spec / "tasks.md").write_bytes(b"\xff\xfe")
        self.assertEqual(self.run_cli("hash", str(self.spec / "tasks.md"))[0], 2)

    def test_unexpected_git_failure_is_2(self) -> None:
        failure = subprocess.CompletedProcess([], 128, "", "fatal: dubious ownership")
        with mock.patch.object(validate_spec.subprocess, "run", return_value=failure):
            code, _, err = self.run_cli("hash", str(self.spec / "tasks.md"), "--json")
        self.assertEqual(code, 2)
        self.assertIn("dubious ownership", err)

    def test_no_repository_and_quiet_misses_are_absence_not_errors(self) -> None:
        for code, stderr in (
            (128, "fatal: not a git repository (or any of the parent directories)"),
            (1, ""),
        ):
            result = subprocess.CompletedProcess([], code, "", stderr)
            with (
                self.subTest(code=code),
                mock.patch.object(
                    validate_spec.subprocess,
                    "run",
                    return_value=result,
                ),
            ):
                self.assertIsNone(
                    validate_spec.git(self.repo, "rev-parse", "--verify", "HEAD"),
                )

    def test_usage_errors_are_3(self) -> None:
        for args in (
            ("bogus",),
            ("approve", str(self.spec)),
            ("validate",),
            ("validate", str(self.repo / "nowhere")),
            ("validate", str(self.spec), "--phase", "done"),
            ("code-baseline", str(self.spec)),
            ("hash", "missing.md"),
            ("hash", str(self.spec / ".config.kiro"), "--json"),
        ):
            with self.subTest(args=args):
                code, _, err = self.run_cli(*args)
                self.assertEqual(code, 3)
                self.assertIn("usage error", err)


class OperationTest(CliTest):
    def test_status_and_reconcile_refuse_a_spec_outside_the_repository(self) -> None:
        outside = shutil.copytree(self.spec, self.tmp / "outside" / self.spec.name)
        support.write_state(outside, support.new_state(self.spec.name))
        before = (outside / ".specflow.json").read_bytes()
        for command in ("status", "reconcile"):
            with self.subTest(command=command):
                code, _, err = self.run_cli(command, str(outside))
                self.assertEqual(code, 3)
                self.assertIn("outside the repository", err)
        self.assertEqual((outside / ".specflow.json").read_bytes(), before)

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

    def test_status_prints_on_a_non_utf8_stdout(self) -> None:
        other = shutil.copytree(self.spec, self.specs / "00102-other")
        for spec, target in ((self.spec, other), (other, self.spec)):
            path = spec / "requirements.md"
            text = path.read_text().replace(
                "\n## Purpose",
                f"Depends on: folder:{target.name}\n\n## Purpose",
                1,
            )
            path.write_text(text)
        env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "status", "--json"],
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertIn(b"00101-feature-sample -> 00102-other", result.stdout)

    def test_status_names_a_malformed_state_by_its_repository_path(self) -> None:
        (self.spec / ".specflow.json").write_text("{")
        _, out, _ = self.run_cli("status", "--json")
        self.assertNotIn(str(self.tmp.resolve()), out)
        self.assertNotIn(str(self.tmp), out)
        blocker = json.loads(out)["specs"][0]["blockers"][0]
        self.assertTrue(blocker["reason"].startswith("state invalid: not valid JSON"))
        self.assertEqual(
            blocker["reference"],
            ".kiro/specs/00101-feature-sample/.specflow.json",
        )

    def test_status_names_a_malformed_state_linked_from_outside_the_repository(
        self,
    ) -> None:
        outside = self.tmp / "outside"
        outside.mkdir()
        (outside / "state.json").write_text("{")
        (self.spec / ".specflow.json").symlink_to(outside / "state.json")
        linked = shutil.copytree(self.spec, outside / "00102-linked", symlinks=True)
        (self.specs / "00102-linked").symlink_to(linked)
        code, out, err = self.run_cli("status", "--json")
        self.assertNotIn("Traceback", err)
        self.assertEqual(code, 1)
        references = [s["blockers"][0]["reference"] for s in json.loads(out)["specs"]]
        self.assertEqual(
            references,
            [
                ".kiro/specs/00101-feature-sample/.specflow.json",
                ".kiro/specs/00102-linked/.specflow.json",
            ],
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
        self.assertEqual(
            list(record),
            ["sha256", "approvedAt", "workflowVersion", "upstreamSha256"],
        )
        self.assertEqual(record["sha256"], canonical.strip())
        self.assertRegex(record["approvedAt"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_hash_json_is_for_canonical_artifacts_only(self) -> None:
        other = str(self.spec / ".config.kiro")
        self.assertEqual(self.run_cli("hash", other, "--json")[0], 3)
        self.assertEqual(self.run_cli("hash", other)[0], 0)
        self.assertEqual(self.run_cli("hash", other, "--raw")[0], 0)

    def test_hash_json_binds_each_upstream_artifact(self) -> None:
        expected = {}
        for name in ("requirements", "design"):
            _, digest, _ = self.run_cli("hash", str(self.spec / f"{name}.md"))
            expected[name] = digest.strip()
        _, out, _ = self.run_cli("hash", str(self.spec / "tasks.md"), "--json")
        self.assertEqual(json.loads(out)["upstreamSha256"], expected)
        _, out, _ = self.run_cli("hash", str(self.spec / "requirements.md"), "--json")
        self.assertNotIn("upstreamSha256", json.loads(out))

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

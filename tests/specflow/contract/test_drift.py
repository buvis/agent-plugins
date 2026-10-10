"""The design approval's code baseline (T-022) and its comparison (T-026)."""

from __future__ import annotations

import hashlib
import os
import unittest

import support
from specflow_helper.drift import code_baseline


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CodeBaselineTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.tmp / "repo"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "src" / "committed.py").write_bytes(b"one\n")
        support.git(self.repo, "init", "-q")
        support.git(self.repo, "add", "-A")
        support.git(self.repo, "commit", "-q", "-m", "base")

    def test_staged_unstaged_and_untracked_bytes_are_captured(self) -> None:
        (self.repo / "src" / "committed.py").write_bytes(b"unstaged\n")
        (self.repo / "src" / "staged.py").write_bytes(b"staged\n")
        support.git(self.repo, "add", "src/staged.py")
        (self.repo / "src" / "untracked.py").write_bytes(b"untracked\n")
        baseline = code_baseline(
            self.repo, ["src/untracked.py", "src/staged.py", "src/committed.py"]
        )
        self.assertEqual(
            baseline,
            {
                "status": "captured",
                "files": [
                    {"path": "src/committed.py", "sha256": digest(b"unstaged\n")},
                    {"path": "src/staged.py", "sha256": digest(b"staged\n")},
                    {"path": "src/untracked.py", "sha256": digest(b"untracked\n")},
                ],
            },
        )

    def test_missing_file_is_recorded_as_missing(self) -> None:
        self.assertEqual(
            code_baseline(self.repo, ["src/new.py"]),
            {"status": "captured", "files": [{"path": "src/new.py", "missing": True}]},
        )

    def test_paths_are_sorted_and_deduplicated(self) -> None:
        baseline = code_baseline(self.repo, ["src/b.py", "src/a.py", "src/b.py"])
        self.assertEqual([f["path"] for f in baseline["files"]], ["src/a.py", "src/b.py"])

    def test_each_refused_path_yields_not_checked(self) -> None:
        (self.repo / "link").symlink_to(self.repo / "src")
        os.mkfifo(self.repo / "pipe")
        for path, reason in (
            ("/etc/hosts", "not a repository-relative path"),
            ("~/x.py", "not a repository-relative path"),
            ("src\\x.py", "not a repository-relative path"),
            ("src/../x.py", "holds a .. segment"),
            ("link/committed.py", "goes through a symbolic link"),
            ("src", "is a directory"),
            ("pipe", "is not a regular file"),
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    code_baseline(self.repo, [path]),
                    {"status": "not_checked", "reason": f"{path} {reason}"},
                )

    def test_one_refused_path_leaves_no_partial_baseline(self) -> None:
        baseline = code_baseline(self.repo, ["src/committed.py", "../outside.py"])
        self.assertEqual(baseline["status"], "not_checked")
        self.assertNotIn("files", baseline)

    def test_no_paths_is_not_checked_never_clean(self) -> None:
        self.assertEqual(code_baseline(self.repo, [])["status"], "not_checked")

    def test_baseline_holds_hashes_not_source_content(self) -> None:
        (self.repo / "src" / "committed.py").write_bytes(b"SECRET_SOURCE_LINE\n")
        baseline = code_baseline(self.repo, ["src/committed.py"])
        self.assertNotIn("SECRET_SOURCE_LINE", repr(baseline))


if __name__ == "__main__":
    unittest.main()

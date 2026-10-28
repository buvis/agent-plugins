"""Local prerequisite diagnostics obey the public CLI contract."""

from __future__ import annotations

import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[2] / "tools/autopilot/prerequisites.py"
PREDECESSORS = {
    "00012": (),
    "00013": ("00012",),
    "00014": ("00012", "00013"),
    "00015": ("00013", "00014"),
    "00018": ("00012",),
    "00019": ("00018",),
    "00020": ("00019",),
    "00021": ("00020",),
    "00016": ("00015", "00020", "00021"),
    "00017": ("00016",),
}

# Instrument external boundaries in the child interpreter, before CLI execution.
# Report attempted forbidden operations even when the CLI catches their errors.
IO_GUARD = r'''
import os
import shutil
import sys

def reject(operation):
    sys.stderr.write("FORBIDDEN_IO: " + operation + "\n")
    raise PermissionError(operation)

def check_path(path):
    if isinstance(path, (str, bytes, os.PathLike)):
        value = os.fsdecode(path).lower()
        if "ovcaq" in value:
            reject("OVCAQ probe: " + value)
        if "/prds/backlog" in value or "/prds/in-progress" in value:
            reject("non-done bucket read: " + value)

def audit(event, args):
    if event == "open":
        check_path(args[0])
        mode, flags = args[1], args[2]
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            )
        ):
            reject("write: " + str(args[0]))
    if event.startswith(("subprocess.", "socket.", "os.exec", "os.spawn")):
        reject(event)
    if event in {
        "os.system", "os.posix_spawn", "os.fork", "os.forkpty",
        "os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.link",
        "os.symlink", "os.chmod", "os.chown", "os.utime", "os.truncate",
    }:
        reject(event)
    if event in {"os.listdir", "os.scandir"} and args:
        check_path(args[0])

def guarded_path_call(function):
    def guarded(*args, **kwargs):
        if args:
            check_path(args[0])
        elif "path" in kwargs:
            check_path(kwargs["path"])
        return function(*args, **kwargs)
    return guarded

for name in ("stat", "lstat", "access", "readlink", "listdir", "scandir"):
    setattr(os, name, guarded_path_call(getattr(os, name)))

def reject_lookup(*args, **kwargs):
    reject("subprocess lookup")

shutil.which = reject_lookup
os.get_exec_path = reject_lookup
sys.addaudithook(audit)
'''


class LocalPrerequisitesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.script = self.root / "tools/autopilot/prerequisites.py"
        self.script.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE, self.script)
        self.done = self.root / "docs/dev/project-management/prds/done"
        self.cwd = self.root / "elsewhere"
        self.cwd.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        harness = self.root / "harness"
        harness.mkdir()
        (harness / "sitecustomize.py").write_text(IO_GUARD, encoding="utf-8")
        self.env = dict(os.environ, HOME=str(self.home), PYTHONPATH=str(harness))
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"
        self.env["PATH"] = str(self.root / "missing-executables")

    def complete(self, prd: str, slug: str = "finished") -> None:
        self.done.mkdir(parents=True, exist_ok=True)
        (self.done / f"{prd}-{slug}.md").write_text("done\n", encoding="utf-8")

    def snapshot(self) -> dict[str, tuple[int, int, int, str | None]]:
        result = {}
        for path in self.root.rglob("*"):
            stat = path.lstat()
            result[str(path.relative_to(self.root))] = (
                stat.st_mode, stat.st_size, stat.st_mtime_ns,
                os.readlink(path) if path.is_symlink() else None,
            )
        return result

    def invoke(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        before = self.snapshot()
        result = subprocess.run(
            [sys.executable, "-B", str(self.script), *arguments],
            cwd=self.cwd, env=self.env, capture_output=True, text=True, timeout=10,
        )
        self.assertNotIn("FORBIDDEN_IO:", result.stderr)
        self.assertEqual(self.snapshot(), before, "CLI changed local files")
        return result

    def assert_diagnostic(self, prd: str, missing: list[str]) -> None:
        result = self.invoke("--prd", prd)
        self.assertEqual(result.returncode, int(bool(missing)), result.stderr)
        self.assertEqual(
            result.stdout,
            json.dumps({"prd": prd, "missing": missing}, sort_keys=True,
                       separators=(",", ":")) + "\n",
        )

    def test_prerequisites_missing_directory_is_empty_for_every_known_id(self) -> None:
        for prd, predecessors in PREDECESSORS.items():
            with self.subTest(prd=prd):
                self.assert_diagnostic(prd, list(predecessors))
        self.assertFalse(self.done.exists())

    def test_prerequisites_missing_tracks_every_partial_predecessor_set(self) -> None:
        self.done.mkdir(parents=True)
        for prd, predecessors in PREDECESSORS.items():
            for count in range(len(predecessors) + 1):
                for present in itertools.combinations(predecessors, count):
                    with self.subTest(prd=prd, present=present):
                        for path in self.done.iterdir():
                            path.unlink()
                        for index in range(64):
                            self.complete("00000", f"unrelated-{index:03d}")
                        for completed in PREDECESSORS.keys() - set(predecessors):
                            self.complete(completed, "unrelated")
                        for completed in reversed(present):
                            self.complete(completed, "accepted")
                        missing = [item for item in predecessors if item not in present]
                        self.assert_diagnostic(prd, missing)
                        for completed in present:
                            self.complete(completed, "another-completion")
                        self.assert_diagnostic(prd, missing)

    def test_completion_requires_exact_id_nonempty_slug_and_markdown_file(self) -> None:
        self.done.mkdir(parents=True)
        predecessors = PREDECESSORS["00016"]
        for prd in predecessors:
            for name in (
                f"x{prd}-done.md", f"{prd}0-done.md", f"{prd}.md",
                f"{prd}-.md", f"{prd}-done.md.bak", f"{prd}-done.md~",
                f"{prd}-done.MD", f"prefix-{prd}-done.md",
                f"{prd}-done.md\n",
            ):
                (self.done / name).write_text("done\n", encoding="utf-8")
            (self.done / f"{prd}-directory.md").mkdir()
            (self.done / f"{prd}-dangling.md").symlink_to(
                self.root / f"missing-{prd}"
            )
        self.assert_diagnostic("00016", list(predecessors))
        for index, prd in enumerate(predecessors):
            self.complete(prd, f"real-{index}")
            self.assert_diagnostic("00016", list(predecessors[index + 1:]))
        for slug in ("z", "release-2026.10", "notes_and_checks", "completed item"):
            with self.subTest(slug=slug):
                self.assert_diagnostic("00017", ["00016"])
                self.complete("00016", slug)
                self.assert_diagnostic("00017", [])
                (self.done / f"00016-{slug}.md").unlink()

    def test_completion_uses_script_repository_instead_of_cwd_or_other_buckets(self) -> None:
        for base in (
            self.cwd / "docs/dev/project-management/prds/done",
            self.done.parent / "backlog", self.done.parent / "in-progress",
        ):
            base.mkdir(parents=True)
            for prd in PREDECESSORS["00014"]:
                (base / f"{prd}-finished.md").write_text("done\n", encoding="utf-8")
        self.assert_diagnostic("00014", ["00012", "00013"])
        self.complete("00012", "local-one")
        self.assert_diagnostic("00014", ["00013"])
        self.complete("00013", "local-two")
        self.assert_diagnostic("00014", [])

    def test_local_prerequisites_ignore_ovcaq_when_missing_or_broken(self) -> None:
        self.env["OVCAQ_ROOT"] = str(self.home / ".ovcaq")
        self.env["OVCAQ"] = str(self.home / ".ovcaq")
        self.env["PATH"] = str(self.home / ".ovcaq/bin")
        for broken in (False, True):
            with self.subTest(broken=broken):
                if broken:
                    (self.home / ".ovcaq").symlink_to(self.home / "missing-target")
                self.assert_diagnostic("00012", [])
                self.assert_diagnostic("00017", ["00016"])
                self.complete("00016", "finished-despite-environment")
                self.assert_diagnostic("00017", [])
                (self.done / "00016-finished-despite-environment.md").unlink()

    def test_unknown_string_ids_preserve_input_and_missing_argument_is_usage_error(self) -> None:
        unknown_ids = ("", "12", "00011", "00022", "000120", "x00012", "00012-x")
        unknown_ids += tuple(f"{40000 + index * 137:05d}" for index in range(16))
        for prd in unknown_ids:
            with self.subTest(prd=prd):
                result = self.invoke("--prd", prd)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(
                    result.stdout,
                    json.dumps({"unknown_prd": prd}, sort_keys=True,
                               separators=(",", ":")) + "\n",
                )
        for arguments in (
            (), ("--prd",), ("--prd", "00012", "--bogus"),
            ("--prd", "00012", "extra"),
        ):
            with self.subTest(arguments=arguments):
                result = self.invoke(*arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()

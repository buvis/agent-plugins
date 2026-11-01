"""Packaged dirty-tree and log-sink primitives keep pinned read-only semantics."""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_contract import ROOT

PACKAGE = ROOT / "plugins" / "autopilot"
SCRIPTS = PACKAGE / "scripts"
PM = "docs/dev/project-management/"
GIT = (
    "git",
    "-c",
    "user.name=Tess",
    "-c",
    "user.email=tess@example.invalid",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "init.defaultBranch=master",
)
BASE = {
    "b.py": "b\n",
    "c.py": "c\n",
    "logs/keep.txt": "k\n",
    PM + "p.md": "p\n",
    PM + "p2.md": "p2\n",
    PM + "sub/x.md": "x\n",
    "docs/dev/tmp/keep.txt": "t\n",
}


def load_helper(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        [*GIT, *args], cwd=cwd, capture_output=True, text=True, timeout=60
    )
    if result.returncode:
        raise AssertionError(f"git {args} failed: {result.stderr}")
    return result.stdout


def write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dt = load_helper("dirty_tree")
        self.sink = load_helper("log_sink_refusal")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()

    def make_repo(self, name: str = "repo", files: dict | None = None) -> Path:
        root = self.base / name
        root.mkdir(parents=True)
        git(root, "init", "-q")
        write(root, {**BASE, **(files or {})})
        git(root, "add", "-A")
        git(root, "commit", "-qm", "base")
        return root

    def commit(self, root: Path, files: dict[str, str], message: str = "c") -> str:
        write(root, files)
        git(root, "add", "-A")
        git(root, "commit", "-qm", message)
        return self.head(root)

    def head(self, root: Path) -> str:
        return git(root, "rev-parse", "HEAD").strip()

    def plain_dir(self) -> Path:
        path = self.base / "plain"
        path.mkdir(exist_ok=True)
        return path


class PorcelainParsingTest(RepoCase):
    def test_store_prefixes_are_the_management_store_and_scratch_dir(self) -> None:
        self.assertEqual(self.dt.STORE_PREFIX, PM)
        self.assertEqual(len(self.dt.STORE_PREFIXES), 2)
        self.assertEqual(set(self.dt.STORE_PREFIXES), {PM, "docs/dev/tmp/"})

    def test_records_carry_source_path_for_renames_and_copies_in_either_column(
        self,
    ) -> None:
        parse = self.dt._iter_porcelain_z_records
        self.assertEqual(parse(""), [])
        raw = (
            " M src/a.py\0R  new name.py\0old name.py\0?? R.txt\0"
            " C copy.py\0orig.py\0RM moved.py\0was.py\0A  added.py\0"
            "?? C.txt\0 R wt.py\0wt_old.py\0"
        )
        self.assertEqual(
            parse(raw),
            [
                ("src/a.py", None),
                ("new name.py", "old name.py"),
                ("R.txt", None),
                ("copy.py", "orig.py"),
                ("moved.py", "was.py"),
                ("added.py", None),
                ("C.txt", None),
                ("wt.py", "wt_old.py"),
            ],
        )
        self.assertEqual(parse("?? only.txt\0"), [("only.txt", None)])

    def test_store_membership_requires_both_rename_endpoints_under_store(
        self,
    ) -> None:
        inside = self.dt._dirty_path_is_in_store
        prefixes = self.dt.STORE_PREFIXES
        cases = [
            (PM + "a.md", None, PM, True),
            (PM + "a.md", PM + "b.md", PM, True),
            (PM + "a.md", "src/a.md", PM, False),
            ("src/a.md", PM + "a.md", PM, False),
            ("docs/dev/project-management-old/a.md", None, PM, False),
            ("x/" + PM + "a.md", None, PM, False),
            ("docs/dev/tmp/a.txt", None, PM, False),
            ("docs/dev/tmp/a.txt", PM + "a.md", prefixes, True),
            ("docs/dev/tmpx/a.txt", None, prefixes, False),
            ("docs/dev/tmp/a.txt", "b.py", prefixes, False),
            ("sub/docs/dev/tmp/a.txt", None, ("sub/docs/dev/tmp/",), True),
            ("docs/dev/tmp/a.txt", None, ("sub/docs/dev/tmp/",), False),
        ]
        for new, old, store, expected in cases:
            with self.subTest(new=new, old=old, store=store):
                self.assertIs(inside(new, old, store), expected)


class StoreRootsTest(RepoCase):
    def test_store_roots_prefix_each_store_root_with_the_show_prefix(self) -> None:
        root = self.make_repo()
        (root / "sub" / "deeper").mkdir(parents=True)
        prefixes = self.dt.STORE_PREFIXES
        self.assertEqual(tuple(self.dt._store_roots(root)), tuple(prefixes))
        self.assertEqual(
            tuple(self.dt._store_roots(root / "sub")),
            tuple("sub/" + p for p in prefixes),
        )
        self.assertEqual(
            tuple(self.dt._store_roots(root / "sub" / "deeper")),
            tuple("sub/deeper/" + p for p in prefixes),
        )

    def test_store_roots_raise_os_error_outside_a_repository(self) -> None:
        self.assertTrue(issubclass(self.dt._GitProbeFailed, OSError))
        with self.assertRaises(self.dt._GitProbeFailed):
            self.dt._store_roots(self.plain_dir())

    def test_dirty_store_paths_list_only_this_projects_store_changes(self) -> None:
        root = self.make_repo(files={"sub/" + PM + "q.md": "q\n"})
        self.assertEqual(self.dt._dirty_store_paths(root), [])
        write(
            root,
            {
                PM + "p.md": "edited\n",
                PM + "new.md": "n\n",
                "b.py": "edited\n",
                "docs/dev/project-management-old/x.md": "x\n",
            },
        )
        self.assertEqual(
            sorted(self.dt._dirty_store_paths(root)), [PM + "new.md", PM + "p.md"]
        )
        write(root, {"sub/" + PM + "q.md": "edited\n"})
        self.assertEqual(
            sorted(self.dt._dirty_store_paths(root / "sub")), ["sub/" + PM + "q.md"]
        )


class DirtyOutsideStoreTest(RepoCase):
    def test_outside_paths_are_sorted_force_untracked_and_skip_store_roots(
        self,
    ) -> None:
        root = self.make_repo()
        git(root, "config", "status.showUntrackedFiles", "no")
        self.assertEqual(self.dt._dirty_outside_store_paths(root), [])
        (root / "c.py").unlink()
        write(
            root,
            {
                "b.py": "changed\n",
                "zz/new/deep.txt": "n\n",
                PM + "p.md": "edit\n",
                PM + "new/n.md": "n\n",
                "docs/dev/tmp/scratch.txt": "s\n",
                "docs/dev/project-management-old/x.md": "x\n",
                "docs/dev/tmpfile": "t\n",
            },
        )
        self.assertEqual(
            self.dt._dirty_outside_store_paths(root),
            [
                "b.py",
                "c.py",
                "docs/dev/project-management-old/x.md",
                "docs/dev/tmpfile",
                "zz/new/deep.txt",
            ],
        )

    def test_renames_contribute_both_endpoints_unless_both_are_in_store(
        self,
    ) -> None:
        root = self.make_repo()
        git(root, "mv", "b.py", "renamed.py")
        git(root, "mv", PM + "p2.md", PM + "moved.md")
        git(root, "mv", PM + "p.md", "out.md")
        paths = self.dt._dirty_outside_store_paths(root)
        self.assertEqual(paths, sorted(paths))
        self.assertIn("b.py", paths)
        self.assertIn("renamed.py", paths)
        self.assertIn("out.md", paths)
        self.assertNotIn(PM + "p2.md", paths)
        self.assertNotIn(PM + "moved.md", paths)

    def test_extra_exclusions_match_exact_toplevel_relative_paths(self) -> None:
        root = self.make_repo()
        write(
            root,
            {
                "logs/run.log": "a",
                "logs/run.log.bak": "b",
                "logs/run.lo": "c",
                "run.log": "d",
            },
        )
        paths = self.dt._dirty_outside_store_paths
        everything = ["logs/run.lo", "logs/run.log", "logs/run.log.bak", "run.log"]
        self.assertEqual(paths(root), everything)
        self.assertEqual(paths(root, ("logs", "logs/", "log")), everything)
        self.assertEqual(
            paths(root, ("logs/run.log",)),
            ["logs/run.lo", "logs/run.log.bak", "run.log"],
        )
        self.assertEqual(
            paths(root, ("logs/run.log", "run.log")),
            ["logs/run.lo", "logs/run.log.bak"],
        )

    def test_subdirectory_project_reports_toplevel_paths_and_prefixed_store(
        self,
    ) -> None:
        root = self.make_repo(files={"sub/keep.txt": "k\n"})
        project = root / "sub"
        write(
            root,
            {
                "sub/" + PM + "s.md": "s\n",
                "sub/docs/dev/tmp/t.txt": "t\n",
                "sub/x.py": "x\n",
                PM + "p.md": "edited\n",
            },
        )
        paths = self.dt._dirty_outside_store_paths
        self.assertEqual(paths(project), [PM + "p.md", "sub/x.py"])
        self.assertEqual(paths(project, ("sub/x.py",)), [PM + "p.md"])
        self.assertEqual(paths(project, ("x.py",)), [PM + "p.md", "sub/x.py"])
        self.assertEqual(
            paths(root),
            ["sub/" + PM + "s.md", "sub/docs/dev/tmp/t.txt", "sub/x.py"],
        )

    def test_hidden_index_flags_do_not_hide_outside_edits(self) -> None:
        root = self.make_repo()
        git(root, "update-index", "--skip-worktree", "b.py", PM + "p.md")
        git(root, "update-index", "--assume-unchanged", "c.py")
        git(root, "update-index", "--skip-worktree", "logs/keep.txt")
        self.assertEqual(self.dt._dirty_outside_store_paths(root), [])
        write(root, {"b.py": "hidden\n", "c.py": "hidden\n", PM + "p.md": "s\n"})
        self.assertEqual(self.dt._dirty_outside_store_paths(root), ["b.py", "c.py"])
        self.assertFalse(self.dt._dirty_check(root, ("b.py", "c.py"))[0])
        self.assertTrue(self.dt._dirty_outside_store(root, ("b.py",)))

    def test_git_failure_raises_for_paths_and_counts_as_dirty_for_checks(
        self,
    ) -> None:
        plain = self.plain_dir()
        with self.assertRaises(OSError):
            self.dt._dirty_outside_store_paths(plain)
        self.assertIs(self.dt._dirty_outside_store(plain), True)
        self.assertEqual(tuple(self.dt._dirty_check(plain, ())), (True, []))
        missing = self.base / "missing"
        self.assertIs(self.dt._dirty_outside_store(missing), True)

    def test_dirty_check_reports_flag_and_remaining_paths(self) -> None:
        root = self.make_repo()
        check = self.dt._dirty_check
        self.assertEqual(tuple(check(root, ())), (False, []))
        self.assertIs(self.dt._dirty_outside_store(root), False)
        write(root, {PM + "p.md": "store only\n", "docs/dev/tmp/s.txt": "s"})
        self.assertEqual(tuple(check(root, ())), (False, []))
        self.assertIs(self.dt._dirty_outside_store(root), False)
        write(root, {"b.py": "edited\n", "new.txt": "n"})
        self.assertEqual(tuple(check(root, ())), (True, ["b.py", "new.txt"]))
        self.assertEqual(tuple(check(root, ("b.py",))), (True, ["new.txt"]))
        self.assertEqual(tuple(check(root, ("b.py", "new.txt"))), (False, []))
        self.assertIs(self.dt._dirty_outside_store(root), True)
        self.assertIs(self.dt._dirty_outside_store(root, ("b.py", "new.txt")), False)


class SelfLogExclusionTest(RepoCase):
    def test_log_rel_and_tracked_reports_toplevel_path_and_tracking(self) -> None:
        root = self.make_repo()
        (root / "sub").mkdir()
        write(root, {"logs/run.log": "r"})
        rel = self.dt._log_rel_and_tracked
        self.assertEqual(
            tuple(rel(root, root / "logs/run.log")), ("logs/run.log", False)
        )
        self.assertEqual(
            tuple(rel(root, root / "logs/keep.txt")), ("logs/keep.txt", True)
        )
        self.assertEqual(
            tuple(rel(root / "sub", root / "logs/run.log")), ("logs/run.log", False)
        )
        self.assertEqual(
            tuple(rel(root, root / "logs/future.log")), ("logs/future.log", False)
        )
        self.assertIsNone(rel(root, None))
        self.assertIsNone(rel(root, self.plain_dir() / "out.log"))

    def test_only_an_untracked_log_inside_the_toplevel_is_excused(self) -> None:
        root = self.make_repo()
        write(root, {"logs/run.log": "r", "logs/run.log.1": "s"})
        excuse = self.dt._untracked_log_exclusion
        self.assertEqual(
            tuple(excuse(root, root / "logs/run.log")), ("logs/run.log",)
        )
        self.assertEqual(tuple(excuse(root, root / "logs/keep.txt")), ())
        self.assertEqual(tuple(excuse(root, self.plain_dir() / "x.log")), ())
        self.assertEqual(tuple(excuse(root, None)), ())
        self.assertEqual(
            tuple(self.dt._dirty_check(root, excuse(root, root / "logs/run.log"))),
            (True, ["logs/run.log.1"]),
        )
        write(root, {"logs/keep.txt": "tracked log rewritten\n"})
        self.assertEqual(
            tuple(self.dt._dirty_check(root, excuse(root, root / "logs/keep.txt"))),
            (True, ["logs/keep.txt", "logs/run.log", "logs/run.log.1"]),
        )


class StoreSymlinkTargetTest(RepoCase):
    def make_linked_repo(self) -> Path:
        root = self.make_repo()
        (root / "product").mkdir()
        os.symlink("../" + PM + "p.md", root / "product" / "conf.md")
        os.symlink("../" + PM + "sub", root / "product" / "pmdir")
        os.symlink("p2.md", root / PM / "alias.md")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "links")
        os.symlink("../" + PM + "p2.md", root / "product" / "untracked.md")
        return root

    def test_tracked_product_symlink_to_changed_store_path_is_detected(self) -> None:
        root = self.make_linked_repo()
        changed = self.dt._store_symlink_targets_changed
        cases = [
            ([], False),
            ([PM + "p.md"], True),
            ([PM + "p2.md"], False),
            ([PM + "p.md.bak"], False),
            ([PM + "sub/x.md"], True),
            ([PM + "sub2/x.md"], False),
            ([PM + "p2.md", PM + "p.md"], True),
            ([PM + "p2.md", PM + "other.md"], False),
        ]
        for store_paths, expected in cases:
            with self.subTest(store_paths=store_paths):
                self.assertIs(changed(root, store_paths), expected)
        bare = self.make_repo("bare")
        self.assertIs(changed(bare, [PM + "p.md"]), False)


class AncestorAndCleanTest(RepoCase):
    def test_store_only_endpoint_diff_from_ancestor_is_clean(self) -> None:
        root = self.make_repo()
        clean = self.dt._ancestor_and_clean
        base = self.head(root)
        self.assertIs(clean(root, base, base), True)
        store = self.commit(root, {PM + "p.md": "new\n"})
        self.assertIs(clean(root, base, store), True)
        code = self.commit(root, {"b.py": "code\n"})
        self.assertIs(clean(root, base, code), False)
        self.assertIs(clean(root, store, code), False)
        self.assertIs(clean(root, code, code), True)
        self.assertIs(clean(root, code, base), False)
        scratch = self.commit(root, {"docs/dev/tmp/keep.txt": "changed\n"})
        self.assertIs(clean(root, code, scratch), False)

    def test_endpoint_diff_accepts_reverted_code_and_store_only_merges(self) -> None:
        root = self.make_repo()
        clean = self.dt._ancestor_and_clean
        base = self.head(root)
        self.commit(root, {"b.py": "temporary\n"})
        reverted = self.commit(root, {"b.py": "b\n"})
        self.assertIs(clean(root, base, reverted), True)
        git(root, "checkout", "-q", "-b", "side", base)
        side = self.commit(root, {PM + "side.md": "s\n"})
        git(root, "checkout", "-q", "-b", "other", base)
        other = self.commit(root, {"c.py": "other\n"})
        git(root, "checkout", "-q", "master")
        git(root, "merge", "-q", "--no-edit", "side")
        merged = self.head(root)
        self.assertIs(clean(root, base, merged), True)
        self.assertIs(clean(root, side, merged), True)
        self.assertIs(clean(root, other, merged), False)

    def test_dirt_git_errors_and_store_symlink_retarget_are_not_clean(self) -> None:
        root = self.make_repo()
        clean = self.dt._ancestor_and_clean
        os.symlink("../" + PM + "p.md", root / "c.link")
        base = self.commit(root, {}, "link")
        write(root, {PM + "p2.md": "dirty store\n"})
        self.assertIs(clean(root, base, base), True)
        write(root, {"untracked.py": "x"})
        self.assertIs(clean(root, base, base), False)
        (root / "untracked.py").unlink()
        self.assertIs(clean(root, "0" * 40, base), False)
        self.assertIs(clean(root, "not-a-sha", base), False)
        self.assertIs(clean(self.plain_dir(), base, base), False)
        git(root, "checkout", "-q", "--", PM + "p2.md")
        retarget = self.commit(root, {PM + "p.md": "linked change\n"})
        self.assertIs(clean(root, base, retarget), False)
        untargeted = self.commit(root, {PM + "p2.md": "free change\n"})
        self.assertIs(clean(root, retarget, untargeted), True)


class LogSinkRefusalTest(RepoCase):
    OUTSIDE = "resolves outside the repository"
    GITDIR = "resolves inside the git directory"

    def test_new_and_plain_untracked_files_may_be_opened(self) -> None:
        root = self.make_repo()
        refuse = self.sink.refuse
        (root / "docs/dev/project-management-logs").mkdir(parents=True)
        write(root, {"logs/plain.log": "p"})
        (root / "logs/plain.log").chmod(0o644)
        self.assertIsNone(refuse(root / "logs/new.log", root))
        self.assertIsNone(refuse(root / "logs/plain.log", root))
        self.assertIsNone(refuse(root / "docs/dev/project-management-logs/x.log", root))
        alias = self.base / "alias"
        os.symlink(root, alias)
        self.assertIsNone(refuse(alias / "logs/new.log", alias))

    def test_outside_and_store_destinations_are_refused(self) -> None:
        root = self.make_repo()
        refuse = self.sink.refuse
        plain = self.plain_dir()
        self.assertEqual(refuse(plain / "x.log", root), self.OUTSIDE)
        self.assertEqual(refuse(root / "logs/../../x.log", root), self.OUTSIDE)
        self.assertEqual(refuse(plain / "x.log", plain), self.OUTSIDE)
        inner = root / "vendor" / "inner"
        inner.mkdir(parents=True)
        git(inner, "init", "-q")
        self.assertEqual(refuse(inner / "x.log", root), self.OUTSIDE)
        store = "resolves inside the store"
        self.assertEqual(refuse(root / PM / "run.log", root), store)
        self.assertEqual(refuse(root / PM / "autopilot/run.log", root), store)

    def test_git_directory_identity_covers_aliases_and_worktree_pointer(
        self,
    ) -> None:
        root = self.make_repo()
        refuse = self.sink.refuse
        self.assertEqual(refuse(root / ".git/run.log", root), self.GITDIR)
        if (root / ".GIT").exists():
            self.assertEqual(refuse(root / ".GIT/run.log", root), self.GITDIR)
        worktree = self.base / "wt"
        git(root, "worktree", "add", "-q", "-b", "wt", str(worktree))
        self.assertTrue((worktree / ".git").is_file())
        self.assertEqual(refuse(worktree / ".git", worktree), self.GITDIR)
        self.assertIsNone(refuse(worktree / "logs/new.log", worktree))

    def test_tracked_and_symlinked_destinations_are_refused(self) -> None:
        root = self.make_repo()
        refuse = self.sink.refuse
        (root / "b.py").chmod(0o755)
        self.assertEqual(refuse(root / "logs/keep.txt", root), "is tracked")
        self.assertEqual(refuse(root / "b.py", root), "is tracked")
        os.symlink("new.log", root / "logs/link.log")
        os.symlink("plain.txt", root / "logs/dangling.log")
        os.symlink(root / "logs", root / "alias")
        os.symlink(root / PM, root / "pm")
        os.symlink("loop", root / "loop")
        self.assertEqual(refuse(root / "logs/link.log", root), "is a symlink")
        self.assertEqual(refuse(root / "logs/dangling.log", root), "is a symlink")
        self.assertEqual(refuse(root / "alias/new.log", root), "is a symlink")
        self.assertEqual(refuse(root / "pm/x.log", root), "resolves inside the store")
        self.assertIn(refuse(root / "loop/x.log", root), {self.OUTSIDE, "is a symlink"})

    def test_nonregular_executable_and_hardlinked_files_are_refused(self) -> None:
        root = self.make_repo()
        refuse = self.sink.refuse
        self.assertEqual(refuse(root / "logs", root), "is not a regular file")
        os.mkfifo(root / "logs/fifo.log")
        self.assertEqual(refuse(root / "logs/fifo.log", root), "is not a regular file")
        write(root, {"logs/run.log": "r", "logs/a.log": "a"})
        modes = ((0o755, "is executable"), (0o744, "is executable"))
        modes += ((0o654, "is executable"), (0o644, None))
        for mode, expected in modes:
            with self.subTest(mode=oct(mode)):
                (root / "logs/run.log").chmod(mode)
                self.assertEqual(refuse(root / "logs/run.log", root), expected)
        os.link(root / "logs/a.log", root / "logs/b.log")
        many = "has more than one hard link"
        self.assertEqual(refuse(root / "logs/a.log", root), many)
        self.assertEqual(refuse(root / "logs/b.log", root), many)
        (root / "logs/b.log").unlink()
        self.assertIsNone(refuse(root / "logs/a.log", root))


DECOY = (
    "import pathlib\n"
    "pathlib.Path(__file__).with_name(__name__ + '.imported').write_text('x')\n"
    "raise ImportError('decoy runtime module')\n"
)

PROBE = """\
import json, pathlib, sys
sys.path.append(sys.argv[1])
before = set(sys.modules)
import dirty_tree, log_sink_refusal
root = pathlib.Path(sys.argv[2])
pm = "docs/dev/project-management/autopilot/"
report = {
    "outside": dirty_tree._dirty_outside_store_paths(root),
    "store": sorted(dirty_tree._dirty_store_paths(root)),
    "check": list(dirty_tree._dirty_check(root, ())),
    "store_sink": log_sink_refusal.refuse(root / (pm + "run.log"), root),
    "free_sink": log_sink_refusal.refuse(root / "logs/new.log", root),
}
report["loaded"] = sorted({m.split(".")[0] for m in set(sys.modules) - before}
                          - set(sys.stdlib_module_names))
print(json.dumps(report))
"""


class PrimitiveIsolationTest(RepoCase):
    def snapshot(self, root: Path) -> dict:
        return {
            p.relative_to(root): (
                p.read_bytes() if p.is_file() else None,
                p.stat().st_mtime_ns,
            )
            for p in root.rglob("*")
            if ".git" not in p.relative_to(root).parts
        }

    def make_fixture(self) -> tuple[Path, Path, Path, Path]:
        package = self.base / "portable distribution" / "plugins" / "autopilot"
        shutil.copytree(PACKAGE, package)
        state = PM + "autopilot/state.json"
        project = self.make_repo("project", {state: '{"queue": ["T1"]}'})
        write(project, {state: '{"queue": ["T2"]}', "b.py": "edited\n"})
        write(project, {PM + "autopilot/.lock": "poison"})
        home, probe_dir = self.base / "home", self.base / "probe"
        home.mkdir()
        (probe_dir / "cli").mkdir(parents=True)
        for name in ("store_tree", "state", "statectl", "schema", "gate", "custody"):
            (probe_dir / f"{name}.py").write_text(DECOY, encoding="utf-8")
        (probe_dir / "cli" / "__init__.py").write_text(DECOY, encoding="utf-8")
        (probe_dir / "probe.py").write_text(PROBE, encoding="utf-8")
        return package, project, home, probe_dir

    def run_probe(
        self, package: Path, project: Path, home: Path, probe: Path
    ) -> subprocess.CompletedProcess:
        git_dir = str(Path(shutil.which("git") or "/usr/bin/git").parent)
        argv = [sys.executable, "-B", str(probe / "probe.py")]
        return subprocess.run(
            [*argv, str(package / "scripts"), str(project)],
            cwd=home,
            capture_output=True,
            timeout=60,
            env={
                "HOME": str(home),
                "PATH": f"{git_dir}:/usr/bin:/bin",
                "PYTHONNOUSERSITE": "1",
                "LANG": "C.UTF-8",
            },
        )

    def test_primitives_run_relocated_without_runtime_imports_or_state_writes(
        self,
    ) -> None:
        package, project, home, probe_dir = self.make_fixture()
        roots = (project, home, package.parent)
        watched = {root: self.snapshot(root) for root in roots}
        result = self.run_probe(package, project, home, probe_dir)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        report = json.loads(result.stdout)
        self.assertEqual(report["outside"], ["b.py"])
        self.assertEqual(
            report["store"], [PM + "autopilot/.lock", PM + "autopilot/state.json"]
        )
        self.assertEqual(report["check"], [True, ["b.py"]])
        self.assertEqual(report["store_sink"], "resolves inside the store")
        self.assertIsNone(report["free_sink"])
        self.assertLessEqual(set(report["loaded"]), {"dirty_tree", "log_sink_refusal"})
        self.assertEqual(sorted(p.name for p in probe_dir.rglob("*.imported")), [])
        for root, before in watched.items():
            self.assertEqual(self.snapshot(root), before, f"primitives changed {root}")


if __name__ == "__main__":
    unittest.main()

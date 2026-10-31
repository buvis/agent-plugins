"""Public project-root path behavior from the frozen controller contract."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

from controller_test_support import canonical, frozen_state

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state.paths import resolve_project_root
from autopilot_state.store import StateIOError


class ProjectRootTest(unittest.TestCase):
    def test_resolves_existing_directory_without_inferring_an_ancestor_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / ".autopilot" / "controller").mkdir(parents=True)
            for name in ("project", "project-extra", "workspace", "nested/checkout"):
                root = base / name
                root.mkdir(parents=True)
                self.assertEqual(resolve_project_root(root), root.resolve())
                self.assertEqual(resolve_project_root(root / "."), root.resolve())
                self.assertEqual(list(root.iterdir()), [])
            for name, target in (("alias", base / "project"),
                                 ("checkout-link", base / "nested/checkout"),
                                 ("chained-link", base / "checkout-link")):
                alias = base / name
                alias.symlink_to(target, target_is_directory=True)
                self.assertEqual(resolve_project_root(alias), target.resolve())
            self.assertEqual(list((base / ".autopilot" / "controller").iterdir()), [])

    def test_refuses_missing_and_nondirectory_roots_without_creating_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            existing = base / "project"
            existing.mkdir()
            files = [base / name for name in ("project-file", "notes.txt", ".workspace")]
            for file in files:
                file.write_bytes(b"unrelated file")
            missing = [base / name for name in
                       ("project-extra", "missing", "absent-checkout", "nested/absent")]
            for root in missing + files:
                with self.subTest(root=root):
                    with self.assertRaises(StateIOError):
                        resolve_project_root(root)
            self.assertEqual(resolve_project_root(existing), existing.resolve())
            self.assertEqual(list(existing.iterdir()), [])
            for root in missing:
                self.assertFalse(root.exists())
            self.assertFalse((base / "nested").exists())
            for file in files:
                self.assertEqual(file.read_bytes(), b"unrelated file")

    def test_resolves_relative_directories_and_refuses_relative_missing_or_file_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "nested" / "checkout"
            root.mkdir(parents=True)
            file = base / "notes.txt"
            file.write_bytes(b"unrelated file")
            with contextlib.chdir(base):
                for relative in (Path("nested/checkout"),
                                 Path("nested/../nested/checkout"), Path(".")):
                    with self.subTest(relative=relative):
                        result = resolve_project_root(relative)
                        self.assertEqual(result, (base / relative).resolve())
                        self.assertTrue(result.is_absolute())
                for relative in (Path("absent-checkout"), Path("notes.txt")):
                    with self.subTest(relative=relative):
                        with self.assertRaises(StateIOError):
                            resolve_project_root(relative)
            self.assertEqual(list(root.iterdir()), [])
            self.assertFalse((base / "absent-checkout").exists())
            self.assertFalse((base / ".autopilot").exists())
            self.assertEqual(file.read_bytes(), b"unrelated file")

    def test_refuses_symlinked_private_components_and_aliased_fixed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for index, relative in enumerate((".autopilot", ".autopilot/controller",
                                              ".autopilot/controller/actors")):
                encoded = relative.replace("/", "-").replace(".", "")
                for basename in (encoded, "unrelated-workspace"):
                    case = base / str(index) / basename
                    root = case / basename
                    root.mkdir(parents=True)
                    link = root / relative
                    link.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    outside = case / "outside"
                    outside.mkdir()
                    for parent in link.parents:
                        if parent == root:
                            break
                        parent.chmod(0o700)
                    self.assertEqual(resolve_project_root(root), root.resolve())
                    link.symlink_to(outside, target_is_directory=True)
                    with self.subTest(relative=relative, basename=basename):
                        with self.assertRaises(StateIOError):
                            resolve_project_root(root)
                        self.assertTrue(link.is_symlink())
                        self.assertEqual(list(outside.iterdir()), [])

    def test_refuses_hardlinked_fixed_artifacts_under_any_project_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for name in ("state.json", "state.json.bak", "state.json.lock"):
                for basename in (name, "unrelated-workspace"):
                    case = base / name / basename
                    root = case / basename
                    private = root / ".autopilot" / "controller"
                    private.mkdir(parents=True, mode=0o700)
                    outside = case / "outside"
                    outside.write_bytes(b"outside evidence")
                    (root / ".autopilot").chmod(0o700)
                    artifact = private / name
                    payload = canonical(frozen_state()) if name != "state.json.lock" else b""
                    artifact.write_bytes(payload)
                    artifact.chmod(0o600)
                    self.assertEqual(resolve_project_root(root), root.resolve())
                    self.assertEqual(artifact.read_bytes(), payload)
                    artifact.unlink()
                    os.link(outside, artifact)
                    with self.subTest(name=name, basename=basename):
                        with self.assertRaises(StateIOError):
                            resolve_project_root(root)
                        self.assertEqual(outside.read_bytes(), b"outside evidence")
                        self.assertEqual(artifact.read_bytes(), b"outside evidence")

    def test_refuses_symlinked_fixed_artifacts_and_preserves_their_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for name in ("state.json", "state.json.bak", "state.json.lock"):
                root = base / name / "unrelated-workspace"
                private = root / ".autopilot" / "controller"
                private.mkdir(parents=True, mode=0o700)
                (root / ".autopilot").chmod(0o700)
                outside = root.parent / "outside"
                payload = canonical(frozen_state()) if name != "state.json.lock" else b""
                outside.write_bytes(payload)
                outside.chmod(0o600)
                artifact = private / name
                artifact.symlink_to(outside)
                with self.subTest(name=name):
                    with self.assertRaises(StateIOError):
                        resolve_project_root(root)
                    self.assertTrue(artifact.is_symlink())
                    self.assertEqual(outside.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()

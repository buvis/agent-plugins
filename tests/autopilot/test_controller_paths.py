"""Public project-root path behavior from the frozen controller contract."""

from __future__ import annotations

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
            for name in ("project", "project-extra"):
                root = base / name
                root.mkdir()
                self.assertEqual(resolve_project_root(root), root.resolve())
                self.assertEqual(resolve_project_root(root / "."), root.resolve())
            alias = base / "alias"
            alias.symlink_to(base / "project", target_is_directory=True)
            self.assertEqual(resolve_project_root(alias), (base / "project").resolve())
            self.assertEqual(list((base / ".autopilot" / "controller").iterdir()), [])
    def test_refuses_missing_and_nondirectory_roots_without_creating_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            existing = base / "project"
            existing.mkdir()
            file = base / "project-file"
            file.write_bytes(b"unrelated file")
            for root in (base / "project-extra", base / "missing", file):
                with self.subTest(root=root):
                    with self.assertRaises(StateIOError):
                        resolve_project_root(root)
            self.assertEqual(resolve_project_root(existing), existing.resolve())
            self.assertEqual(list(existing.iterdir()), [])
            self.assertEqual(file.read_bytes(), b"unrelated file")

    def test_refuses_symlinked_private_components_and_aliased_fixed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for relative in (".autopilot", ".autopilot/controller",
                             ".autopilot/controller/actors"):
                root = base / relative.replace("/", "-").replace(".", "")
                root.mkdir()
                link = root / relative
                link.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                outside = base / (root.name + "-outside")
                outside.mkdir()
                for parent in link.parents:
                    if parent == root:
                        break
                    parent.chmod(0o700)
                self.assertEqual(resolve_project_root(root), root.resolve())
                link.symlink_to(outside, target_is_directory=True)
                with self.subTest(relative=relative):
                    with self.assertRaises(StateIOError):
                        resolve_project_root(root)
                    self.assertEqual(list(outside.iterdir()), [])
            for name in ("state.json", "state.json.bak", "state.json.lock"):
                root = base / name
                private = root / ".autopilot" / "controller"
                private.mkdir(parents=True, mode=0o700)
                outside = base / (name + "-outside")
                outside.write_bytes(b"outside evidence")
                (root / ".autopilot").chmod(0o700)
                artifact = private / name
                artifact.write_bytes(canonical(frozen_state()) if name != "state.json.lock" else b"")
                artifact.chmod(0o600)
                self.assertEqual(resolve_project_root(root), root.resolve())
                artifact.unlink()
                os.link(outside, artifact)
                with self.subTest(name=name):
                    with self.assertRaises(StateIOError):
                        resolve_project_root(root)
                    self.assertEqual(outside.read_bytes(), b"outside evidence")


if __name__ == "__main__":
    unittest.main()

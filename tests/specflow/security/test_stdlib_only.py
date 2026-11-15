"""Static dependency boundary; never import the files being inspected."""

import ast
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOTS = ("plugins/specflow", "tools/specflow", "tests/specflow/evals/runners")


class DependencyTests(unittest.TestCase):
    def test_shipped_and_maintainer_scripts_import_only_the_standard_library(self) -> None:
        files = [path for folder in ROOTS for path in (REPO / folder).rglob("*.py")]
        local_files = files + list((REPO / "scripts").rglob("*.py"))
        local = {path.stem for path in local_files}
        local.update(path.parent.name for path in local_files if path.name == "__init__.py")
        allowed = sys.stdlib_module_names | local
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module]
                for name in names:
                    with self.subTest(file=str(path.relative_to(REPO)), line=node.lineno):
                        self.assertIn(name.split(".")[0], allowed)

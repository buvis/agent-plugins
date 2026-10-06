import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path("plugins/specflow")


class BoundaryTests(unittest.TestCase):
    def test_no_specflow_manifest_outside_the_package(self) -> None:
        tracked = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split("\0")
        for name in tracked:
            path = Path(name)
            if path.name != "plugin.json" or path.parent.is_relative_to(PACKAGE):
                continue
            with self.subTest(path=name):
                manifest = json.loads((ROOT / path).read_text(encoding="utf-8"))
                self.assertNotEqual(manifest.get("name"), "specflow")


if __name__ == "__main__":
    unittest.main()

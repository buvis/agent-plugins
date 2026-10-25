"""The ported link checker (T-076): what it scans, how a citation resolves, warnings, the usage contract, and the path handling."""

from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path

import support

SCRIPT = support.SCRIPTS.parent / "check_links.py"
FIXTURE = support.REPO / "tests/specflow/fixtures/cross-spec"


def load():
    module = support.load(SCRIPT)
    module.resolvable_numbers.cache_clear()
    return module


def copy_fixture(folder: str) -> Path:
    """A copy of the fixture whose own dangling citation is removed, so a test seeds its own."""
    root = Path(folder) / "repo"
    shutil.copytree(FIXTURE, root)
    (root / "docs/pm/specs/00001-alpha/requirements.md").write_text(
        "clean\n", encoding="utf-8"
    )
    return root


def targets(result: dict) -> list[str]:
    return [item["target"] for item in result["findings"]]


class CheckLinksTest(unittest.TestCase):
    def test_scans_the_specs_folder_and_intake_only(self) -> None:
        result = load().run(FIXTURE)
        files = {item["file"] for item in result["findings"] + result["warnings"]}
        self.assertTrue(files, "the fixture has findings")
        self.assertTrue(all(f.startswith("docs/pm/") for f in files), files)
        self.assertNotIn(
            "00099- (no spec or intake item)",
            targets(result),
            "docs/notes/ is not scanned",
        )

    def test_resolves_five_digit_citations_against_specs_and_intake(self) -> None:
        result = load().run(FIXTURE)
        self.assertEqual(targets(result), ["00009- (no spec or intake item)"])
        self.assertEqual(
            result["findings"][0]["file"], "docs/pm/specs/00001-alpha/requirements.md"
        )
        self.assertEqual(result["findings"][0]["line"], 14)

    def test_skips_placeholder_citations_and_strips_trailing_punctuation(self) -> None:
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            doc = root / "docs/pm/specs/00003-gamma/design.md"
            doc.write_text(
                "A pattern NNNNN-title, a glob 00004-*, and 00009-nope.\n",
                encoding="utf-8",
            )
            result = load().run(root)
        self.assertEqual(targets(result), ["00009- (no spec or intake item)"])

    def test_ignores_digits_after_a_digit_slash_dot_or_dash(self) -> None:
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            doc = root / "docs/pm/specs/00003-gamma/design.md"
            doc.write_text(
                "v1.00009-x, 2026-00009-, 10/00009-, and 100009-y are no citations.\n",
                encoding="utf-8",
            )
            result = load().run(root)
        self.assertEqual(targets(result), [])

    def test_exit_code_and_json_shape_include_scan_errors(self) -> None:
        dirty = support.run(SCRIPT, "--root", str(FIXTURE), "--json")
        self.assertEqual(dirty.returncode, 1)
        payload = json.loads(dirty.stdout)
        self.assertEqual(sorted(payload), ["findings", "scan_errors", "warnings"])
        self.assertEqual(payload["findings"][0]["citing_line"], "Dangling: 00009-nope.")
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            clean = support.run(SCRIPT, "--root", str(root), "--json")
            (root / "docs/pm/specs/00003-gamma/design.md").write_bytes(b"\xff\xfe")
            unreadable = support.run(SCRIPT, "--root", str(root), "--json")
        self.assertEqual(clean.returncode, 0)
        self.assertEqual(json.loads(clean.stdout)["findings"], [])
        self.assertEqual(unreadable.returncode, 1)
        errors = json.loads(unreadable.stdout)["scan_errors"]
        self.assertEqual(len(errors), 1)
        self.assertIn("docs/pm/specs/00003-gamma/design.md: unreadable", errors[0])

    def test_resolves_each_path_once(self) -> None:
        module = load()
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            doc = root / "docs/pm/specs/00003-gamma/design.md"
            doc.write_text("cite 00001-alpha and 00009-nope\n" * 50, encoding="utf-8")
            result = module.run(root)
        self.assertEqual(len(result["findings"]), 50)
        self.assertEqual(
            module.resolvable_numbers.cache_info().misses,
            1,
            "one directory walk per run",
        )

    def test_runs_under_unittest_with_local_fixtures(self) -> None:
        self.assertIsInstance(self, unittest.TestCase)
        self.assertTrue(
            (FIXTURE / ".agents/specflow.json").is_file(),
            "the fixture is local to the tests",
        )
        imports = [
            line
            for line in Path(__file__).read_text(encoding="utf-8").splitlines()
            if line.startswith(("import ", "from "))
        ]
        self.assertFalse([line for line in imports if "pytest" in line], imports)

    def test_warns_on_wiki_links_and_never_resolves_them(self) -> None:
        result = load().run(FIXTURE)
        wiki = [w for w in result["warnings"] if w["target"] == "[[memory-note]]"]
        self.assertEqual(len(wiki), 1)
        self.assertNotIn("[[memory-note]]", " ".join(targets(result)))
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            (root / "docs/pm/specs/00001-alpha/requirements.md").write_text(
                "only [[a-note]] here\n", encoding="utf-8"
            )
            only_warning = support.run(SCRIPT, "--root", str(root), "--json")
        self.assertEqual(
            only_warning.returncode, 0, "a warning never changes the exit code"
        )
        self.assertEqual(len(json.loads(only_warning.stdout)["warnings"]), 1)

    def test_warns_on_home_and_absolute_paths_and_never_resolves_them(self) -> None:
        result = load().run(FIXTURE)
        warned = {w["target"] for w in result["warnings"]}
        self.assertIn("~/.claude/notes.md", warned)
        self.assertIn("/Users/someone/x.md", warned)
        self.assertFalse(any("notes.md" in t or "x.md" in t for t in targets(result)))

    def test_symlink_escaping_the_root_is_a_scan_error_and_not_read(self) -> None:
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            outside = Path(folder) / "outside"
            outside.mkdir()
            (outside / "secret.md").write_text(
                "cites 00042-elsewhere\n", encoding="utf-8"
            )
            os.symlink(outside, root / "docs/pm/specs/00007-link")
            result = load().run(root)
        self.assertEqual(len(result["scan_errors"]), 1)
        self.assertIn(
            "leads outside the repository, not read", result["scan_errors"][0]
        )
        self.assertNotIn("00042- (no spec or intake item)", targets(result))

    def test_missing_root_or_refused_config_is_a_scan_error(self) -> None:
        missing = support.run(SCRIPT, "--root", "/no/such/repo", "--json")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("not a folder", json.loads(missing.stdout)["scan_errors"][0])
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            (root / ".agents/specflow.json").write_text(
                '{"specsDir": "/etc"}', encoding="utf-8"
            )
            refused = support.run(SCRIPT, "--root", str(root), "--json")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("is absolute", json.loads(refused.stdout)["scan_errors"][0])

    def test_a_linked_intake_folder_outside_the_root_is_never_indexed(self) -> None:
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            outside = Path(folder) / "outside"
            (outside / "00042-elsewhere").mkdir(parents=True)
            os.symlink(outside, root / "docs/pm/intake/new/group")
            (root / "docs/pm/specs/00001-alpha/requirements.md").write_text(
                "cites 00042-elsewhere\n", encoding="utf-8"
            )
            result = load().run(root)
        self.assertEqual(targets(result), ["00042- (no spec or intake item)"])
        self.assertEqual(len(result["scan_errors"]), 1)
        self.assertIn(
            "leads outside the repository, not read", result["scan_errors"][0]
        )

    @unittest.skipIf(os.geteuid() == 0, "root reads a folder without permission")
    def test_an_unreadable_intake_item_folder_is_a_scan_error(self) -> None:
        temp = support.temp_folder()
        self.addCleanup(temp.cleanup)
        root = copy_fixture(temp.name)
        item = root / "docs/pm/intake/processed/00003-gamma"
        item.chmod(0)
        self.addCleanup(item.chmod, 0o755)
        result = support.run(SCRIPT, "--root", str(root), "--json")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.returncode, 1)
        errors = json.loads(result.stdout)["scan_errors"]
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("docs/pm/intake/processed/00003-gamma: unreadable", errors[0])

    @unittest.skipIf(os.geteuid() == 0, "root reads a folder without permission")
    def test_an_unreadable_folder_under_the_scanned_tree_is_a_scan_error(
        self,
    ) -> None:
        temp = support.temp_folder()
        self.addCleanup(temp.cleanup)
        root = copy_fixture(temp.name)
        spec = root / "docs/pm/specs/00003-gamma"
        spec.chmod(0)
        self.addCleanup(spec.chmod, 0o755)
        result = support.run(SCRIPT, "--root", str(root), "--json")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.returncode, 1)
        errors = json.loads(result.stdout)["scan_errors"]
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("docs/pm/specs/00003-gamma: unreadable", errors[0])

    def test_a_numbered_wiki_link_is_a_warning_and_never_a_citation(self) -> None:
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            (root / "docs/pm/specs/00001-alpha/requirements.md").write_text(
                "[[00009-missing]]\n", encoding="utf-8"
            )
            result = support.run(SCRIPT, "--root", str(root), "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["findings"], [])
        self.assertEqual(
            [w["target"] for w in payload["warnings"]], ["[[00009-missing]]"]
        )
        self.assertEqual(result.returncode, 0)

    def test_a_link_back_to_a_base_folder_scans_its_files_once(self) -> None:
        with support.temp_folder() as folder:
            root = copy_fixture(folder)
            (root / "docs/pm/specs/index.md").write_text(
                "Dangling: 00009-nope.\n", encoding="utf-8"
            )
            os.symlink(root / "docs/pm/specs", root / "docs/pm/intake/new/specs")
            result = load().run(root)
        self.assertEqual(targets(result), ["00009- (no spec or intake item)"])


if __name__ == "__main__":
    unittest.main()

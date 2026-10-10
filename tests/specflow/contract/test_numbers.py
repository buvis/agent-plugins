"""Spec numbers, clashes, the Sources: line, and references in a configured folder (T-029)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import unittest
from pathlib import Path

import support
import validate_spec
from specflow_helper.checks import validate
from specflow_helper.config import load_config
from specflow_helper.deps import dependency_blockers
from specflow_helper.numbers import next_number, number_clashes


class NumbersTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.tmp / "repo"
        (self.repo / ".agents").mkdir(parents=True)
        self.config_file = self.repo / ".agents" / "specflow.json"
        self.write_config({})
        self.specs = self.repo / "docs" / "specs"

    def write_config(self, extra: dict) -> None:
        config = {"schemaVersion": 1, "root": "docs", "specsDir": "docs/specs", **extra}
        self.config_file.write_text(json.dumps(config))

    def config(self) -> dict:
        return load_config(self.repo)

    def folder(self, *parts: str) -> Path:
        path = self.repo.joinpath(*parts)
        path.mkdir(parents=True)
        return path

    def spec(self, name: str, sources: str | None = None) -> Path:
        text = support.REQUIREMENTS
        if sources is None:
            text = text.replace("Sources: docs/intake/processed/00042-sample\n", "")
        else:
            text = text.replace("docs/intake/processed/00042-sample", sources)
        return support.write_spec(self.specs / name, {"requirements.md": text})

    def rules(self, spec: Path) -> set[str]:
        return {f["rule"] for f in validate(self.repo, spec) if f["level"] == "error"}


class NextNumberTest(NumbersTest):
    def test_empty_repository_starts_at_one(self) -> None:
        self.assertEqual(next_number(self.repo, self.config()), "00001")

    def test_scan_covers_both_stages_groups_specs_and_number_scan_folders(self) -> None:
        self.folder("docs", "intake", "new", "00003-a")
        self.folder("docs", "intake", "processed", "plugin", "00007-grouped")
        self.folder("docs", "specs", "00005-spec")
        self.folder("docs", "specs", "native-kiro-spec")
        self.folder("docs", "prds", "done")
        (self.repo / "docs" / "prds" / "done" / "00011-old-prd.md").write_text("x")
        self.assertEqual(next_number(self.repo, self.config()), "00008")
        self.write_config({"numberScan": ["docs/prds"]})
        self.assertEqual(next_number(self.repo, self.config()), "00012")

    def test_items_deeper_than_one_group_do_not_count(self) -> None:
        self.folder("docs", "intake", "new", "g1", "g2", "00099-too-deep")
        self.assertEqual(next_number(self.repo, self.config()), "00001")

    def test_next_number_is_read_only_and_reachable_from_the_cli(self) -> None:
        self.folder("docs", "specs", "00004-x")
        cwd = Path.cwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, cwd)
        before = sorted(str(p) for p in self.repo.rglob("*"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(validate_spec.main(["next-number"]), 0)
        self.assertEqual(out.getvalue(), "00005\n")
        self.assertEqual(sorted(str(p) for p in self.repo.rglob("*")), before)


class ClashTest(NumbersTest):
    def test_two_intake_items_with_one_number_clash(self) -> None:
        self.folder("docs", "intake", "new", "00003-a")
        self.folder("docs", "intake", "processed", "grp", "00003-b")
        [finding] = number_clashes(self.repo, self.config())
        self.assertIn("number 00003 is used by two intake items", finding["message"])

    def test_two_spec_folders_with_one_number_clash(self) -> None:
        self.spec("00004-one", "docs/intake/processed/00004-one")
        self.spec("00004-two", "docs/intake/processed/00004-two")
        [finding] = number_clashes(self.repo, self.config())
        self.assertIn("spec folders", finding["message"])

    def test_item_and_spec_with_one_number_and_other_titles_do_not_clash(self) -> None:
        self.folder("docs", "intake", "processed", "00004-first-title")
        self.spec("00004-second-title", "docs/intake/processed/00004-first-title")
        self.assertEqual(number_clashes(self.repo, self.config()), [])

    def test_seeded_clash_is_found_by_validate(self) -> None:
        spec = self.spec("00004-one", "docs/intake/processed/00004-one")
        self.spec("00004-two", "docs/intake/processed/00004-two")
        self.assertIn("number-clashes", self.rules(spec))


class SourcesLineTest(NumbersTest):
    def test_sources_naming_the_own_item_passes(self) -> None:
        spec = self.spec("00004-x", "docs/intake/processed/plugin/00004-other-title/")
        self.assertNotIn("sources-line", self.rules(spec))

    def test_missing_sources_line_fails(self) -> None:
        self.assertIn("sources-line", self.rules(self.spec("00004-x")))

    def test_sources_naming_another_number_fails(self) -> None:
        spec = self.spec("00004-x", "docs/intake/processed/00005-y, spike/")
        findings = [f for f in validate(self.repo, spec) if f["rule"] == "sources-line"]
        self.assertIn("names intake item 00005-y", findings[0]["message"])

    def test_bugfix_sources_closes_the_introduction(self) -> None:
        spec = shutil.copytree(
            support.FIXTURES / "specs" / "00102-bugfix-sample", self.specs / "00102-bug"
        )
        self.assertNotIn("sources-line", self.rules(spec))
        text = (spec / "bugfix.md").read_text().replace("Sources:", "Notes:")
        (spec / "bugfix.md").write_text(
            text + "\nSources: docs/intake/processed/00102-x\n"
        )
        self.assertIn("sources-line", self.rules(spec))

    def test_kiro_native_spec_without_a_number_is_skipped(self) -> None:
        source = support.FIXTURES / "kiro" / "requirements-first"
        spec = shutil.copytree(source, self.specs / "iam")
        self.assertNotIn("sources-line", self.rules(spec))
        self.assertEqual(next_number(self.repo, self.config()), "00001")


class ReferenceTest(NumbersTest):
    def test_references_resolve_in_the_configured_specs_folder_only(self) -> None:
        self.folder("docs", "intake", "new", "00020-idea-only")
        self.spec("00021-a", "x/00021-a")
        self.spec("00021-b", "x/00021-b")
        self.spec("login-fix")
        main = self.spec("00030-main", "docs/intake/processed/00030-main")
        declared = "\nDepends on: 00020, 00021, folder:login-fix\n\n## Purpose"
        text = (
            (main / "requirements.md")
            .read_text()
            .replace("\n\n## Purpose", declared, 1)
        )
        (main / "requirements.md").write_text(text)
        reasons = {
            b["reference"]: b["reason"] for b in dependency_blockers(main, self.specs)
        }
        self.assertEqual(reasons["00020"], "missing target")
        self.assertTrue(reasons["00021"].startswith("ambiguous target"))
        self.assertTrue(
            reasons["folder:login-fix"].startswith("incomplete prerequisite")
        )


class ContractFileTest(unittest.TestCase):
    def test_reference_holds_the_five_intake_steps(self) -> None:
        text = (support.SKILL / "references" / "artifact-contract.md").read_text()
        for step in (
            "**Create an item.**",
            "**Scan again.**",
            "**Move the item.**",
            "**Write the fallback log.**",
            "**Take a file input.**",
        ):
            with self.subTest(step=step):
                self.assertIn(step, text)


if __name__ == "__main__":
    unittest.main()

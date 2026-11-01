"""Packaged finding parsing, lead stripping and grouping keep pinned semantics."""

from __future__ import annotations

import copy
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_contract import ROOT


PACKAGE = ROOT / "plugins" / "autopilot"
SCRIPTS = PACKAGE / "scripts"
HEADER = ("| Ref | Consensus | Severity | Issue | File | Found By |\n"
          "|-----|-----------|----------|-------|------|----------|\n")


def load_helper(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


def review(body: str) -> str:
    return f"# Review\n\nVerdict: 2 findings\n\n## Consolidated Findings\n\n{body}\n"


def finding(severity: str, file: str, issue: str, **extra: object) -> dict:
    return {"severity": severity, "file": file, "issue": issue, **extra}


class ReviewedRowsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.findings = load_helper("findings")

    def rows(self, text: str):
        return self.findings.reviewed_rows(text)

    def test_named_column_table_normalizes_refs_severity_and_escaped_pipes(self) -> None:
        text = review(
            HEADER
            + "| r1 | [3/3] | 🟠 High | Wrong Default \\| x | src/b.py:10 | Alice, Bob |\n"
            + "| R2 | [1/3] | medium | Missing test | lib/c.py | Blake |\n"
            + "| R10 | [2/3] | 🔴 Critical | Null deref | src/k.py | Carl |\n"
            + "\n## Next\n\n" + HEADER
            + "| R9 | [1/3] | 🔴 Critical | hidden | z.py | Carl |\n")
        rows, problem = self.rows(text)
        self.assertIsNone(problem)
        Row = self.findings.Row
        self.assertEqual(rows, [Row("R1", "high", "src/b.py:10", "Wrong Default | x"),
                                Row("R2", "medium", "lib/c.py", "Missing test"),
                                Row("R10", "critical", "src/k.py", "Null deref")])
        self.assertEqual([type(row) for row in rows], [Row] * 3)

    def test_reordered_table_without_ref_column_yields_empty_refs(self) -> None:
        text = review("| Task | Severity | File | Issue |\n|------|----------|------|-------|\n"
                      "| T3 | 🔴 Critical | src/k.py | Null deref |\n"
                      "| T4 | high | docs/a.md | Typo Here |\n")
        rows, problem = self.rows(text)
        self.assertIsNone(problem)
        self.assertEqual([tuple(row) for row in rows],
                         [("", "critical", "src/k.py", "Null deref"),
                          ("", "high", "docs/a.md", "Typo Here")])

    def test_bullet_findings_right_split_issue_pipes(self) -> None:
        text = review("- [2/3] 🟠 wrong | default | src/b.py:10 | Found by: Alice, Bob\n"
                      "- [1/3] 🟡 Slow loop | lib/x.py | Found by: Carl\n")
        rows, problem = self.rows(text)
        self.assertIsNone(problem)
        self.assertEqual([tuple(row) for row in rows],
                         [("", "high", "src/b.py:10", "wrong | default"),
                          ("", "medium", "lib/x.py", "Slow loop")])

    def test_empty_section_is_a_clean_review_and_missing_section_is_reported(self) -> None:
        self.assertEqual(self.rows(review("")), ([], None))
        for text in ("", "# Review\n\nVerdict: converged\n",
                     "# Review\n\n## Findings\n\n" + HEADER
                     + "| R1 | [1/3] | 🟠 High | x | a.py | Bob |\n"):
            with self.subTest(text=text[:40]):
                self.assertEqual(self.rows(text), ([], "no-section"))

    def test_malformed_tables_are_unreadable_instead_of_hiding_findings(self) -> None:
        good = "| R1 | [1/3] | 🟠 High | x | a.py | Bob |\n"
        self.assertEqual(len(self.rows(review(HEADER + good))[0]), 1)
        malformed = {
            "missing terminal pipe": HEADER + "| R1 | [1/3] | 🟠 High | x | a.py | Bob\n",
            "truncated row": HEADER + "| R1 | [1/3] | 🟠 High | x |\n",
            "duplicate refs": HEADER + good + "| R1 | [2/3] | 🟡 Medium | y | b.py | Eve |\n",
            "no file column": ("| Ref | Consensus | Severity | Issue | Found By |\n"
                               "|-----|-----------|----------|-------|----------|\n"
                               "| R1 | [1/3] | 🟠 High | x | Bob |\n"),
        }
        for label, body in malformed.items():
            with self.subTest(label=label):
                self.assertEqual(self.rows(review(body)), ([], "unreadable-table"))
        near_duplicate = HEADER + good + "| R10 | [2/3] | 🟡 Medium | y | b.py | Eve |\n"
        rows, problem = self.rows(review(near_duplicate))
        self.assertIsNone(problem)
        self.assertEqual([row.ref for row in rows], ["R1", "R10"])


class FindingKeyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.findings = load_helper("findings")

    def test_key_lowercases_issue_collapses_whitespace_and_keeps_file_case(self) -> None:
        key = self.findings.finding_key
        self.assertEqual(key(" 🟠 ", " src/B.py ", " Wrong  Default "),
                         ("high", "src/B.py", "wrong default"))
        self.assertEqual(key("🟡 Medium", "lib/x.py:4", "Slow\tLOOP \\| fast"),
                         ("medium", "lib/x.py:4", "slow loop | fast"))
        self.assertEqual(key("high", "a.py", "X"), key("🟠", "a.py", "x"))
        self.assertNotEqual(key("🟠", "src/b.py", "x"), key("🟠", "src/B.py", "x"))
        self.assertNotEqual(key("🟠", "src/b.py", "x"), key("🟡", "src/b.py", "x"))
        self.assertNotEqual(key("🟠", "src/b.py", "x"), key("🟠", "src/b.py", "xy"))

    def test_parsed_row_key_matches_reworded_case_and_spacing(self) -> None:
        text = review(HEADER + "| R1 | [3/3] | 🟠 High | Wrong Default \\| x "
                      "| src/b.py:10 | Alice |\n")
        (row,), problem = self.findings.reviewed_rows(text)
        self.assertIsNone(problem)
        self.assertEqual(row.issue, "Wrong Default | x")
        self.assertEqual(self.findings.finding_key(row.severity, row.file, row.issue),
                         self.findings.finding_key("🟠", "src/b.py:10", "wrong   default \\| X"))


class StripLeadTest(unittest.TestCase):
    def test_strips_lexical_leads_up_to_the_severity_emoji(self) -> None:
        strip = load_helper("gate_lead").strip_lead
        cases = {
            "1. - [ ] 🟠 x": "🟠 x",
            "2. 3. - [x] 🟡 z": "🟡 z",
            "<!-- c --> 🟡 y": "🟡 y",
            "ㅤ🟠 w": "🟠 w",
            "`code` 🟡 v": "🟡 v",
            "• ​🔴 bullet": "🔴 bullet",
            "🟠 1. kept": "🟠 1. kept",
            "": "",
        }
        for line, expected in cases.items():
            with self.subTest(line=line):
                self.assertEqual(strip(line), expected)

    def test_bare_brackets_are_not_leads(self) -> None:
        strip = load_helper("gate_lead").strip_lead
        self.assertEqual(strip("(🔴) z"), "(🔴) z")
        self.assertEqual(strip("- (🔴) z"), "(🔴) z")
        self.assertEqual(strip("- 🔴 z"), "🔴 z")


class FileKeyTest(unittest.TestCase):
    def test_citations_general_and_prose_keys(self) -> None:
        file_key = load_helper("rework_groups").file_key
        self.assertEqual(file_key("N/A"), "general")
        self.assertEqual(file_key("docs/x.md"), "prose")
        self.assertEqual(file_key("README.md"), "prose")
        self.assertEqual(file_key("src/a.py:10"), file_key("src/a.py"))
        self.assertEqual(file_key("src/a.py:10:3"), file_key("src/a.py"))
        for near_miss in ("N/A.py", "src/N/A", "docs/x.py"):
            with self.subTest(near_miss=near_miss):
                self.assertNotIn(file_key(near_miss), ("general", "prose"))
        for other in ("src/a.pyc", "src/ab.py", "lib/a.py"):
            with self.subTest(other=other):
                self.assertNotEqual(file_key(other), file_key("src/a.py"))


class GroupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.groups = load_helper("rework_groups")

    def run_group(self, findings: list[dict]) -> list[dict]:
        before = copy.deepcopy(findings)
        groups = self.groups.group(findings)
        self.assertEqual(findings, before, "group must not mutate its input")
        for item in groups:
            self.assertLessEqual({"name_hint", "critical", "findings"}, set(item))
            self.assertIsInstance(item["name_hint"], str)
        return groups

    def layout(self, groups: list[dict]) -> list[tuple[bool, list[str]]]:
        return [(item["critical"], [f["issue"] for f in item["findings"]]) for item in groups]

    def test_seven_findings_cap_general_shared_directory_and_prose(self) -> None:
        findings = [finding("🔴", "src/b.py", "C", ref="R1", found_by=["Alice"]),
                    finding("🟠", "src/a.py:10", "A"), finding("🟡", "src/c/d.py", "D"),
                    finding("🟡", "lib/e.py", "E"), finding("🟡", "N/A", "G"),
                    finding("⚪", "docs/x.md", "X"), finding("🟡", "tools/f.py", "F")]
        groups = self.run_group(findings)
        self.assertEqual(self.layout(groups), [(True, ["C"]), (False, ["A", "D"]),
                                               (False, ["E", "G"]), (False, ["F"]),
                                               (False, ["X"])])
        self.assertEqual(groups[0]["findings"], [findings[0]])
        self.assertEqual(self.groups.NON_CRITICAL_CAP, 4)

    def test_criticals_stay_singletons_in_order_and_skip_the_cap(self) -> None:
        findings = [finding("🟡", "a/x.py", "a1"), finding("🔴", "z/k.py", "K2"),
                    finding("🟡", "b/y.py", "b1"), finding("🔴", "a/x.py", "K1"),
                    finding("🟠", "c/z.py:4", "c1"), finding("🟡", "c/z.py:9", "c2"),
                    finding("⚪", "d/w.py", "d1"), finding("🔴", "z/k.py", "K3")]
        self.assertEqual(self.layout(self.run_group(findings)),
                         [(True, ["K2"]), (True, ["K1"]), (True, ["K3"]),
                          (False, ["c1", "c2"]), (False, ["a1"]), (False, ["b1"]),
                          (False, ["d1"])])
        self.assertEqual(self.run_group([]), [])

    def test_general_merges_into_smallest_code_group(self) -> None:
        findings = [finding("🟡", "a/x.py", "a1"), finding("🟡", "a/x.py", "a2"),
                    finding("🟡", "b/y.py", "b1"), finding("🟡", "b/y.py", "b2"),
                    finding("🟡", "c/z.py", "c1"), finding("🟡", "c/z.py", "c2"),
                    finding("🟠", "d/w.py", "d1"), finding("⚪", "N/A", "g1")]
        self.assertEqual(self.layout(self.run_group(findings)),
                         [(False, ["d1", "g1"]), (False, ["a1", "a2"]),
                          (False, ["b1", "b2"]), (False, ["c1", "c2"])])

    def test_deepest_shared_directory_merges_before_shallower(self) -> None:
        findings = [finding("🟡", "pkg/core/a.py", "a"), finding("🟠", "pkg/c.py", "c"),
                    finding("🟡", "pkg/core/b.py", "b"), finding("⚪", "lib/d.py", "d"),
                    finding("🟡", "tools/e.py", "e")]
        self.assertEqual(self.layout(self.run_group(findings)),
                         [(False, ["c"]), (False, ["a", "b"]), (False, ["e"]),
                          (False, ["d"])])

    def test_unrelated_directories_merge_smallest_lexical_pair(self) -> None:
        findings = [finding("🟡", "a/one.py", "a1"), finding("🟡", "a/one.py", "a2"),
                    finding("🟡", "b/two.py", "b1"), finding("🟡", "b/two.py", "b2"),
                    finding("🟠", "c/three.py", "c1"), finding("🟡", "d/four.py", "d1"),
                    finding("🟡", "e/five.py", "e1")]
        self.assertEqual(self.layout(self.run_group(findings)),
                         [(False, ["c1", "d1"]), (False, ["a1", "a2"]),
                          (False, ["b1", "b2"]), (False, ["e1"])])

    def test_rejects_findings_without_file_string_or_severity_emoji(self) -> None:
        invalid = ({"severity": "🟠", "issue": "no file"}, finding("🟠", None, "none"),
                   finding("high", "a.py", "word"), finding("🔵", "a.py", "blue"),
                   {"file": "a.py", "issue": "no severity"})
        for bad in invalid:
            with self.subTest(bad=bad):
                findings = [finding("🟡", "a.py", "ok"), bad]
                before = copy.deepcopy(findings)
                with self.assertRaises((ValueError, TypeError, KeyError)):
                    self.groups.group(findings)
                self.assertEqual(findings, before)


DECOY = ("import pathlib\n"
         "pathlib.Path(__file__).with_name(__name__ + '.imported').write_text('x')\n"
         "raise ImportError('decoy runtime module')\n")

PROBE = """\
import json, pathlib, sys
sys.path.append(sys.argv[1])
before = set(sys.modules)
import findings, gate_lead, rework_groups
text = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
rows, problem = findings.reviewed_rows(text)
groups = rework_groups.group([
    {"severity": {"high": "🟠", "medium": "🟡"}[r.severity], "file": r.file,
     "issue": r.issue, "ref": r.ref} for r in rows])
loaded = sorted({m.split(".")[0] for m in set(sys.modules) - before}
                - set(sys.stdlib_module_names))
print(json.dumps({"rows": rows, "problem": problem, "loaded": loaded,
                  "lead": gate_lead.strip_lead("1. [ ] 🟡 q"),
                  "groups": [[f["ref"] for f in g["findings"]] for g in groups]}))
"""


class HelperIsolationTest(unittest.TestCase):
    def snapshot(self, root: Path) -> dict:
        return {p.relative_to(root): (p.read_bytes() if p.is_file() else None,
                                      p.stat().st_mtime_ns) for p in root.rglob("*")}

    def test_helpers_run_relocated_with_stdlib_only_and_no_state_access(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        package = base / "portable distribution" / "plugins" / "autopilot"
        shutil.copytree(PACKAGE, package)
        project, home, probe_dir = base / "project", base / "home", base / "probe"
        live = project / "docs" / "dev" / "project-management" / "autopilot"
        live.mkdir(parents=True)
        (live / "state.json").write_text('{"queue": ["T1"]}', encoding="utf-8")
        home.mkdir()
        (probe_dir / "cli").mkdir(parents=True)
        for name in ("findings_section", "state", "statectl", "schema", "gate"):
            (probe_dir / f"{name}.py").write_text(DECOY, encoding="utf-8")
        (probe_dir / "cli" / "__init__.py").write_text(DECOY, encoding="utf-8")
        (probe_dir / "probe.py").write_text(PROBE, encoding="utf-8")
        review_file = base / "review.md"
        review_file.write_text(review(
            HEADER + "| r7 | [1/3] | 🟡 Medium | Slow | pkg/a.py:3 | Bob |\n"
            "| R8 | [2/3] | 🟠 High | Leak | pkg/a.py:9 | Eve |\n"), encoding="utf-8")
        watched = {root: self.snapshot(root) for root in (project, home, package.parent)}
        result = subprocess.run(
            [sys.executable, "-B", str(probe_dir / "probe.py"), str(package / "scripts"),
             str(review_file)], cwd=project, capture_output=True, timeout=60,
            env={"HOME": str(home), "PATH": str(home), "PYTHONNOUSERSITE": "1",
                 "LANG": "C.UTF-8"})
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        report = json.loads(result.stdout)
        self.assertEqual(report["rows"], [["R7", "medium", "pkg/a.py:3", "Slow"],
                                          ["R8", "high", "pkg/a.py:9", "Leak"]])
        self.assertIsNone(report["problem"])
        self.assertEqual(report["lead"], "🟡 q")
        self.assertEqual(report["groups"], [["R7", "R8"]])
        self.assertLessEqual(set(report["loaded"]), {"findings", "gate_lead", "rework_groups"})
        self.assertEqual(sorted(p.name for p in probe_dir.glob("*.imported")), [])
        self.assertEqual(list((probe_dir / "cli").glob("*.imported")), [])
        for root, before in watched.items():
            self.assertEqual(self.snapshot(root), before, f"helpers changed {root}")


if __name__ == "__main__":
    unittest.main()

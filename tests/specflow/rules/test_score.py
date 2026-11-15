"""Stored-record checks for the eval instruments; no signed-in host required."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/specflow/evals/runners"))
import run_claude
import run_codex
import run_kiro
import score

FIXTURES = ROOT / "tests/specflow/fixtures/results"


class InstructionEvidenceTest(unittest.TestCase):
    def test_fixture_imports_and_verified_plugin_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            workspace, plugin = root / "workspace", root / "plugin"
            workspace.mkdir()
            plugin.mkdir()
            expected = {"AGENTS.md": "See rules.md", "rules.md": "Fixture rules"}
            loaded = {
                str(workspace / name): {
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "imports": [str(workspace / "rules.md")]
                    if name == "AGENTS.md"
                    else [],
                }
                for name, text in expected.items()
            }
            loaded[str(plugin / "SKILL.md")] = {
                "sha256": hashlib.sha256(b"Plugin rules").hexdigest(),
                "imports": [],
            }
            report = run_claude.classify_instructions(
                loaded,
                complete=True,
                workspace=workspace,
                expected=expected,
                plugin=plugin,
                plugin_files={"SKILL.md": "Plugin rules"},
            )
            self.assertEqual(report["classification"], "clean")
            self.assertEqual(
                report["instructionFiles"], sorted(str(workspace / p) for p in expected)
            )

    def test_personal_ancestor_generated_and_changed_instructions_taint(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            workspace = root / "workspace"
            workspace.mkdir()
            for path in (
                root / "AGENTS.md",
                root / "home/CLAUDE.md",
                workspace / "generated.md",
                workspace / "AGENTS.md",
            ):
                with self.subTest(path=path):
                    report = run_claude.classify_instructions(
                        {
                            str(path): {
                                "sha256": hashlib.sha256(b"Changed").hexdigest(),
                                "imports": [],
                            }
                        },
                        complete=True,
                        workspace=workspace,
                        expected={"AGENTS.md": "Original"},
                        plugin=root / "plugin",
                        plugin_files={},
                    )
                    self.assertEqual(report["classification"], "tainted")

    def test_missing_inventory_or_import_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            for loaded, complete in (
                ({}, False),
                (
                    {
                        str(root / "AGENTS.md"): {
                            "sha256": hashlib.sha256(b"Rules").hexdigest(),
                            "imports": [str(root / "missing.md")],
                        }
                    },
                    True,
                ),
            ):
                with self.subTest(complete=complete):
                    report = run_claude.classify_instructions(
                        loaded,
                        complete=complete,
                        workspace=root,
                        expected={"AGENTS.md": "Rules"},
                        plugin=root / "plugin",
                        plugin_files={},
                    )
                    self.assertEqual(report["classification"], "unknown")

    def test_symlink_escape_is_classified_before_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "AGENTS.md").symlink_to(root / "personal.md")
            report = run_claude.classify_instructions(
                {
                    str(workspace / "AGENTS.md"): {
                        "sha256": hashlib.sha256(b"Rules").hexdigest(),
                        "imports": [],
                    }
                },
                complete=True,
                workspace=workspace,
                expected={"AGENTS.md": "Rules"},
                plugin=root / "plugin",
                plugin_files={},
            )
            normalized = run_claude.normalize(report, {str(root): "<home>"})
            self.assertEqual(normalized["classification"], "tainted")
            self.assertIn("<home>/personal.md", json.dumps(normalized))

    def test_continuation_and_explicit_edit_content_are_expected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            for text in ("Finished parent rules", "Explicit edit rules"):
                with self.subTest(text=text):
                    report = run_claude.classify_instructions(
                        {
                            str(root / "AGENTS.md"): {
                                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                                "imports": [],
                            }
                        },
                        complete=True,
                        workspace=root,
                        expected={"AGENTS.md": text},
                        plugin=root / "plugin",
                        plugin_files={},
                    )
                    self.assertEqual(report["classification"], "clean")

    def test_scoring_never_preserves_unverified_release_claim(self) -> None:
        record = score.read_json(FIXTURES / "manual.json")
        record["releaseEvidence"] = True
        score.score_record(record, FIXTURES / "evals")
        self.assertFalse(record["releaseEvidence"])


class ReleaseEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = score.read_json(FIXTURES / "manual.json")
        self.candidate = {
            key: self.record[key]
            for key in ("runtimeRevision", "fixtureRevision", "sessionRevision")
        }
        self.candidate["evalRevisions"] = {
            path.stem: score.object_id(path.read_bytes())
            for path in (FIXTURES / "rubrics").glob("SR-*.json")
        }
        self.boundary = {
            "scope": "installed-host-boundary",
            "host": self.record["host"],
            "hostVersion": self.record["hostVersion"],
            "configurationSha256": "a" * 64,
            "runtimeRevision": self.record["runtimeRevision"],
            "checks": {
                name: {"passed": True, "evidence": "synthetic-test:" + name}
                for name in score.RELEASE_BOUNDARY_CHECKS
            },
        }
        self.evidence = {
            "configurationSha256": "a" * 64,
            "boundarySha256": score.evidence_digest(self.boundary),
            "instructions": [
                {
                    "classification": "clean",
                    "complete": True,
                    "instructionFiles": [],
                    "entries": [],
                }
            ]
            * 2,
        }
        self.record["notes"] = score.EVIDENCE_PREFIX + json.dumps(self.evidence)

    def review(self) -> None:
        score.score_record(self.record, FIXTURES / "rubrics")
        score.score_record(
            self.record,
            FIXTURES / "rubrics",
            reviews={
                "evidenceSha256": self.record["rubricReview"]["evidenceSha256"],
                "verdicts": {
                    "SR-DLG-003:1": {
                        "verdict": "PASS",
                        "judge": "human:developer",
                        "reason": "Synthetic check",
                    }
                },
            },
        )

    def certify(self) -> bool:
        return score.certify_release(
            self.record, self.candidate, self.boundary, eval_dir=FIXTURES / "rubrics"
        )

    def test_complete_evidence_and_human_review_are_stable(self) -> None:
        self.assertFalse(self.certify())
        self.review()
        digest = self.record["rubricReview"]["evidenceSha256"]
        self.assertTrue(self.certify())
        self.assertTrue(self.certify())
        self.assertEqual(self.record["rubricReview"]["evidenceSha256"], digest)

    def test_sample_cannot_be_emptied_to_skip_human_review(self) -> None:
        with mock.patch.object(
            score,
            "model_judge",
            autospec=True,
            return_value={
                "verdict": "PASS",
                "judge": "model:judge",
                "reason": "Synthetic",
            },
        ):
            score.score_record(self.record, FIXTURES / "rubrics", judge_model="judge")
        self.record["rubricReview"]["sample"] = []
        self.assertFalse(self.certify())

    def test_shell_only_or_mismatched_boundary_cannot_certify(self) -> None:
        self.review()
        for field, value in (
            ("scope", "synthetic-shell-boundary-only"),
            ("hostVersion", "different"),
            ("configurationSha256", "b" * 64),
            ("checks", {}),
        ):
            with self.subTest(field=field):
                boundary = {**self.boundary, field: value}
                self.assertFalse(
                    score.certify_release(
                        self.record,
                        self.candidate,
                        boundary,
                        eval_dir=FIXTURES / "rubrics",
                    )
                )
                self.assertFalse(self.record["releaseEvidence"])

    def test_frozen_revision_or_incomplete_session_blocks_release(self) -> None:
        self.review()
        for key in (
            "runtimeRevision",
            "fixtureRevision",
            "sessionRevision",
            "evalRevisions",
        ):
            with self.subTest(key=key):
                candidate = {
                    **self.candidate,
                    key: {} if key == "evalRevisions" else "b" * 40,
                }
                self.assertFalse(
                    score.certify_release(
                        self.record,
                        candidate,
                        self.boundary,
                        eval_dir=FIXTURES / "rubrics",
                    )
                )
        self.record["messages"].pop()
        self.record["filesRead"].pop()
        self.assertFalse(self.certify())

    def test_unknown_inventory_or_changed_observations_invalidate_release(self) -> None:
        self.review()
        self.record["instructionMeasurement"] = "not-measured"
        self.assertFalse(self.certify())
        self.record["instructionMeasurement"] = "measured"
        self.evidence["instructions"][0]["complete"] = False
        self.record["notes"] = score.EVIDENCE_PREFIX + json.dumps(self.evidence)
        self.assertFalse(self.certify())

    def test_forged_clean_label_cannot_hide_generated_instruction(self) -> None:
        self.evidence["instructions"][0]["entries"] = [
            {
                "path": "<workspace>/generated.md",
                "sha256": hashlib.sha256(b"Rules").hexdigest(),
                "imports": [],
                "plugin": False,
                "classification": "allowed",
                "reason": "forged",
            }
        ]
        self.evidence["instructions"][0]["instructionFiles"] = [
            "<workspace>/generated.md"
        ]
        self.record["instructionFiles"] = ["<workspace>/generated.md"]
        self.record["notes"] = score.EVIDENCE_PREFIX + json.dumps(self.evidence)
        self.review()
        self.assertFalse(self.certify())


class ScoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads((FIXTURES / "manual.json").read_text())

    def test_passing_and_broken_eval_share_one_record(self) -> None:
        self.assertEqual(score.score_record(self.record, FIXTURES / "evals"), 1)
        self.assertEqual([s["passed"] for s in self.record["scores"]], [True, False])

    def test_manual_record_round_trip_and_schema(self) -> None:
        before = copy.deepcopy(self.record)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "record.json"
            path.write_text(json.dumps(self.record))
            self.assertEqual(score.main([str(path)], FIXTURES / "evals"), 1)
            after = json.loads(path.read_text())
        score.validate_record(after)
        after.pop("scores")
        self.assertEqual(after, before)

    def test_kinds_equal_schema(self) -> None:
        schema = score.read_json(score.SCHEMAS / "eval.schema.json")
        kinds = {
            s["properties"]["kind"]["const"]
            for s in schema["$defs"]["assertion"]["oneOf"]
        }
        self.assertEqual(score.KINDS, kinds)

    def test_unjudged_rubric_exits_one(self) -> None:
        self.assertEqual(score.score_record(self.record, FIXTURES / "rubrics"), 1)
        self.assertFalse(self.record["scores"][0]["passed"])

    def test_unknown_assertion_fails(self) -> None:
        passed, reason = score.assertion_result({"kind": "invented"}, self.record, {})
        self.assertFalse(passed)
        self.assertIn("unknown", reason)

    def test_not_run_has_no_scores(self) -> None:
        self.record["notRun"] = "host did not start"
        self.record["scores"] = []
        self.assertEqual(score.score_record(self.record, FIXTURES / "evals"), 1)
        self.assertNotIn("scores", self.record)

    def test_broken_session_fails_even_negative_assertions(self) -> None:
        self.record["brokenAt"] = 2
        self.assertEqual(score.score_record(self.record, FIXTURES / "evals"), 1)
        self.assertTrue(all(not s["passed"] for s in self.record["scores"]))

    def test_question_and_recommendation_rules(self) -> None:
        self.assertEqual(
            score.question_count("Choose?\n1. A?\n2. B?\n```\nwhy?\n```"), 1
        )
        self.assertEqual(score.question_count("Where? Who?"), 2)
        self.assertEqual(
            score.question_count("See https://example.invalid/?q=x. Continue?"), 1
        )
        self.assertTrue(score.recommended_first("Choose?\n1. A (Recommended)\n2. B"))
        self.assertFalse(score.recommended_first("Choose?\n1. A\n2. B (Recommended)"))

    def test_missing_turn_and_unmeasured_reads_cannot_pass_absence(self) -> None:
        assertion = {"kind": "message_lacks", "pattern": "secret", "turn": 5}
        with self.assertRaises(score.RecordError):
            score.assertion_result(assertion, self.record, {})
        self.record["readMeasurement"] = "not-measured"
        assertion = {"kind": "file_not_read", "path": "secret.txt"}
        with self.assertRaises(score.RecordError):
            score.assertion_result(assertion, self.record, {})

    def test_cli_unavailable_evidence_exits_two_without_writing_scores(self) -> None:
        for assertion in (
            {"kind": "file_read", "path": "result.txt"},
            {"kind": "file_not_read", "path": "secret.txt"},
            {"kind": "message_matches", "pattern": "Status", "turn": 99},
        ):
            with (
                self.subTest(assertion=assertion),
                tempfile.TemporaryDirectory() as folder,
            ):
                root = Path(folder)
                record = {**self.record, "readMeasurement": "not-measured"}
                path = root / "record.json"
                before = json.dumps(record)
                path.write_text(before)
                evaluation = {
                    "schemaVersion": 1,
                    "rule": "SR-DLG-001",
                    "session": record["session"],
                    "assertions": [assertion],
                }
                (root / "SR-DLG-001.json").write_text(json.dumps(evaluation))
                self.assertEqual(score.main([str(path)], root), 2)
                self.assertEqual(path.read_text(), before)

    def test_unavailable_reads_are_rejected_before_model_judging(self) -> None:
        self.record["readMeasurement"] = "not-measured"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rubric_eval = score.read_json(
                next((FIXTURES / "rubrics").glob("SR-*.json"))
            )
            evaluation = {
                "schemaVersion": 1,
                "rule": "SR-DLG-001",
                "session": self.record["session"],
                "assertions": [
                    rubric_eval["assertions"][0],
                    {"kind": "file_read", "path": "result.txt"},
                ],
            }
            (root / "SR-DLG-001.json").write_text(json.dumps(evaluation))
            with (
                mock.patch.object(
                    score,
                    "model_judge",
                    autospec=True,
                    return_value={
                        "verdict": "PASS",
                        "judge": "model:judge",
                        "reason": "Synthetic",
                    },
                ) as judge,
                self.assertRaisesRegex(score.RecordError, "reads not measured"),
            ):
                score.score_record(self.record, root, judge_model="judge")
            judge.assert_not_called()

    def test_validation_input_errors_are_not_failed_assertions(self) -> None:
        with (
            mock.patch.object(
                score,
                "validation_findings",
                autospec=True,
                side_effect=score.RecordError("revision unavailable"),
            ),
            self.assertRaisesRegex(score.RecordError, "revision unavailable"),
        ):
            score.assertion_result(
                {"kind": "validation_passes", "check": "requirement-ids"},
                self.record,
                {},
            )

    def test_compare_ignores_titles_but_not_approvals(self) -> None:
        other = copy.deepcopy(self.record)
        other["host"] = "codex"
        other["status"]["specs"][0]["nextTask"]["title"] = "Different prose"
        self.assertEqual(score.compare([self.record, other]), 0)
        other["status"]["specs"][0]["artifacts"]["tasks"] = "stale"
        self.assertEqual(score.compare([self.record, other]), 1)

    def test_all_file_kinds_include_unchanged_baseline_bytes(self) -> None:
        self.record["unchanged"] = [".kiro/specs/00001-gift-cards/requirements.md"]
        files = score.finished_files(self.record)
        path = self.record["unchanged"][0]
        for assertion in [
            {"kind": "file_exists", "path": path},
            {"kind": "file_unchanged", "path": path},
            {"kind": "file_matches", "path": path, "pattern": "Requirements"},
            {"kind": "file_lacks", "path": path, "pattern": "impossible sentinel"},
            {"kind": "file_absent", "path": "deleted.md"},
        ]:
            with self.subTest(assertion=assertion):
                self.assertTrue(
                    score.assertion_result(assertion, self.record, files)[0]
                )
        self.assertFalse(
            score.assertion_result(
                {"kind": "file_lacks", "path": "missing", "pattern": "secret"},
                self.record,
                files,
            )[0]
        )

    def test_message_turns_and_read_boundaries_are_one_based(self) -> None:
        self.record["filesRead"] = [["first.md"], ["second.md"]]
        assertions = [
            {"kind": "message_matches", "turn": 2, "pattern": "Status"},
            {"kind": "message_lacks", "turn": 1, "pattern": "Status"},
            {"kind": "file_read", "path": "first.md", "before_turn": 2},
            {"kind": "file_not_read", "path": "second.md", "before_turn": 2},
            {"kind": "question_count_at_most", "count": 1},
        ]
        for assertion in assertions:
            with self.subTest(assertion=assertion):
                self.assertTrue(score.assertion_result(assertion, self.record, {})[0])

    def test_validation_runs_on_reconstructed_workspace(self) -> None:
        files = score.tree_files(self.record["fixtureRevision"])
        self.assertTrue(
            score.assertion_result(
                {"kind": "validation_passes", "check": "requirement-ids"},
                self.record,
                files,
            )[0]
        )
        name = ".kiro/specs/00001-gift-cards/requirements.md"
        files[name] += "\n### REQ-001: Duplicate\n"
        self.assertTrue(
            score.assertion_result(
                {"kind": "validation_reports", "check": "requirement-ids"},
                self.record,
                files,
            )[0]
        )

    def test_invalid_records_and_unsafe_paths_are_rejected(self) -> None:
        for path in ["../outside", "/outside", ".git/config", "C:\\outside"]:
            with self.subTest(path=path), self.assertRaises(score.RecordError):
                score.safe_path(path)
        self.record["files"].append(self.record["files"][0])
        with self.assertRaises(score.RecordError):
            score.validate_record(self.record)

    def test_continuation_rebuilds_parent_changes_and_deletions(self) -> None:
        child = copy.deepcopy(self.record)
        child["session"] = "child"
        child["continuesRun"] = {
            "host": "kiro-ide",
            "session": "status-summary",
            "n": 1,
        }
        child["files"] = []
        child["unchanged"] = ["result.txt"]
        with tempfile.TemporaryDirectory() as folder:
            results = Path(folder)
            path = results / "kiro-ide/status-summary/1.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(self.record))
            self.assertEqual(
                score.finished_files(child, results),
                {"result.txt": "Status reported.\n"},
            )
            child["unchanged"] = []
            self.assertEqual(score.finished_files(child, results), {})

    def test_model_pass_needs_human_sample_and_changed_evidence_rejudges(self) -> None:
        verdict = {
            "verdict": "PASS",
            "judge": "model:judge",
            "reason": "Status present",
        }
        with mock.patch.object(
            score, "model_judge", return_value=verdict, autospec=True
        ):
            self.assertEqual(
                score.score_record(
                    self.record, FIXTURES / "rubrics", judge_model="judge"
                ),
                1,
            )
        review = {
            "evidenceSha256": self.record["rubricReview"]["evidenceSha256"],
            "verdicts": {
                "SR-DLG-003:1": {
                    "verdict": "PASS",
                    "judge": "human:developer",
                    "reason": "Checked",
                }
            },
        }
        self.assertEqual(
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review), 0
        )
        self.record["messages"][1] = "Changed answer"
        self.assertEqual(score.score_record(self.record, FIXTURES / "rubrics"), 1)
        self.assertEqual(self.record["rubricReview"]["verdicts"], {})

    def test_sample_error_requires_manual_review_of_all_rubrics(self) -> None:
        evaluations = [
            (
                {
                    "rule": f"SR-DLG-{i:03}",
                    "assertions": [{"kind": "rubric", "rubric": "Check"}],
                },
                "a" * 40,
            )
            for i in range(1, 21)
        ]
        verdict = {"verdict": "PASS", "judge": "model:judge", "reason": "Checked"}
        with mock.patch.object(
            score,
            "model_judge",
            side_effect=lambda *args: verdict.copy(),
            autospec=True,
        ):
            score.rubric_verdicts(self.record, evaluations, {}, "judge", None)
        state = self.record["rubricReview"]
        review = {
            "evidenceSha256": state["evidenceSha256"],
            "verdicts": {
                state["sample"][0]: {
                    "verdict": "FAIL",
                    "judge": "human:developer",
                    "reason": "Wrong",
                }
            },
        }
        scored = score.rubric_verdicts(self.record, evaluations, {}, None, review)
        self.assertFalse(self.record["rubricReview"]["manualAll"])
        review["verdicts"][state["sample"][1]] = {
            "verdict": "FAIL",
            "judge": "human:developer",
            "reason": "Second wrong judgment",
        }
        scored = score.rubric_verdicts(self.record, evaluations, {}, None, review)
        self.assertTrue(self.record["rubricReview"]["manualAll"])
        self.assertEqual(len(self.record["rubricReview"]["required"]), 20)
        self.assertFalse(any(v["passed"] for v in scored.values()))

    def test_pass_sample_has_minimum_and_rounds_up_without_rerolling(self) -> None:
        for count, expected in [(0, 0), (3, 3), (10, 10), (11, 10), (101, 11)]:
            with self.subTest(count=count):
                record = copy.deepcopy(self.record)
                evaluations = [
                    (
                        {
                            "rule": f"SR-DLG-{i:03}",
                            "assertions": [{"kind": "rubric", "rubric": "Check"}],
                        },
                        "a" * 40,
                    )
                    for i in range(1, count + 1)
                ]
                # One FAIL ensures the empty PASS population still has review state.
                evaluations.append(
                    (
                        {
                            "rule": "SR-DLG-999",
                            "assertions": [{"kind": "rubric", "rubric": "Fail"}],
                        },
                        "a" * 40,
                    )
                )
                verdicts = [
                    {"verdict": "PASS", "judge": "model:judge", "reason": "Checked"}
                    for _ in range(count)
                ] + [{"verdict": "FAIL", "judge": "model:judge", "reason": "Failed"}]
                with mock.patch.object(
                    score, "model_judge", side_effect=verdicts, autospec=True
                ):
                    score.rubric_verdicts(record, evaluations, {}, "judge", None)
                sample = record["rubricReview"]["sample"].copy()
                self.assertEqual(len(sample), expected)
                self.assertIn("SR-DLG-999:1", record["rubricReview"]["required"])
                score.rubric_verdicts(record, evaluations, {}, None, None)
                self.assertEqual(record["rubricReview"]["sample"], sample)

    def test_release_eligibility_does_not_invalidate_human_judgment(self) -> None:
        verdict = {"verdict": "PASS", "judge": "model:judge", "reason": "Checked"}
        with mock.patch.object(
            score, "model_judge", return_value=verdict, autospec=True
        ):
            score.score_record(self.record, FIXTURES / "rubrics", judge_model="judge")
        review = {
            "evidenceSha256": self.record["rubricReview"]["evidenceSha256"],
            "verdicts": {
                "SR-DLG-003:1": {
                    "verdict": "PASS",
                    "judge": "human:developer",
                    "reason": "Checked",
                }
            },
        }
        self.assertEqual(
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review), 0
        )
        self.record["releaseEvidence"] = True
        self.assertEqual(
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review), 0
        )
        with (
            mock.patch.object(score, "JUDGE_PROMPT", "Changed judging instructions"),
            self.assertRaisesRegex(score.RecordError, "different evidence"),
        ):
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review)
        self.record["instructionFiles"].append("<home>/AGENTS.md")
        with self.assertRaisesRegex(score.RecordError, "different evidence"):
            score.score_record(self.record, FIXTURES / "rubrics", reviews=review)

    def test_judge_requires_reported_model_and_no_tools(self) -> None:
        for model, tools, allowed in [
            ("other-model", [], True),
            ("tested", [], False),
            ("other-model", ["Read"], False),
        ]:
            events = [
                {"type": "system", "subtype": "init", "model": model, "tools": tools},
                {
                    "type": "result",
                    "result": json.dumps(
                        {"verdict": "PASS", "reason": "The reply meets the rubric"}
                    ),
                },
            ]
            result = subprocess.CompletedProcess(
                [], 0, "\n".join(json.dumps(e) for e in events), ""
            )
            with (
                self.subTest(model=model, tools=tools),
                mock.patch.object(
                    run_claude, "command", return_value=result, autospec=True
                ),
            ):
                if allowed:
                    verdict = score.model_judge("other-model", "Check", {}, "tested")
                    self.assertEqual(verdict["judge"], "model:other-model")
                else:
                    with self.assertRaises(score.RecordError):
                        score.model_judge("other-model", "Check", {}, "tested")

    def test_compare_rejects_missing_status_and_revision_mismatch(self) -> None:
        other = copy.deepcopy(self.record)
        other["host"] = "codex"
        other["status"] = None
        with self.assertRaises(score.RecordError):
            score.compare([self.record, other])
        other["sessionRevision"] = "0" * 40
        with self.assertRaises(score.RecordError):
            score.compare([self.record, other])

    def test_cli_rejects_invalid_schema_and_missing_evals(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "record.json"
            path.write_text(json.dumps({**self.record, "schemaVersion": 2}))
            self.assertEqual(score.main([str(path)], FIXTURES / "evals"), 2)
            path.write_text(json.dumps(self.record))
            self.assertEqual(score.main([str(path)], root), 2)


class RunnerTest(unittest.TestCase):
    def test_external_batch_exports_verified_resources_and_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            scratch = Path(folder).resolve()
            revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
            with run_claude.external_batch(revision, scratch=scratch) as batch:
                self.assertEqual(batch.parent, scratch)
                self.assertEqual(batch.stat().st_mode & 0o777, 0o700)
                self.assertTrue((batch / "control").is_dir())
                self.assertTrue((batch / "workspaces").is_dir())
                run_claude.verify_plugin(batch / "resources/specflow", revision)
            self.assertFalse(batch.exists())

    def test_external_batch_refuses_residue_and_ancestor_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            scratch = Path(folder).resolve()
            residue = scratch / "specflow-evals-leftover"
            residue.mkdir()
            with (
                self.assertRaisesRegex(run_claude.HostError, "residual"),
                run_claude.external_batch("a" * 40, scratch=scratch),
            ):
                self.fail("must not yield")
            residue.rmdir()
            (scratch / "AGENTS.md").write_text("Unexpected ancestor")
            with (
                self.assertRaisesRegex(run_claude.HostError, "ancestor"),
                run_claude.external_batch("a" * 40, scratch=scratch),
            ):
                self.fail("must not yield")
            self.assertEqual(list(scratch.glob("specflow-evals-*")), [])

    def test_instruction_inventory_is_captured_per_turn_before_generated_changes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder).resolve()
            (workspace / "AGENTS.md").write_text("Baseline")
            adapter = run_claude.Claude("tested-model")

            def turn(prompt: str, workspace: Path) -> tuple[str, list[str]]:
                if prompt == "Continue":
                    return "Done", []
                adapter.instruction_measurement = "measured"
                adapter.instruction_observations = {
                    str(workspace / "AGENTS.md"): {
                        "sha256": hashlib.sha256(b"Generated").hexdigest(),
                        "imports": [],
                    }
                }
                (workspace / "AGENTS.md").write_text("Generated")
                return "Done", []

            record = score.read_json(FIXTURES / "manual.json")
            record["messages"], record["filesRead"] = [], []
            with (
                mock.patch.object(adapter, "turn", side_effect=turn, autospec=True),
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude,
                    "capture_status",
                    return_value=record["status"],
                    autospec=True,
                ),
            ):
                run_claude.play_session(
                    adapter,
                    {"turns": [{"developer": "Work"}, {"developer": "Continue"}]},
                    workspace,
                    record,
                )
            evidence = json.loads(record["notes"].split(score.EVIDENCE_PREFIX)[1])
            self.assertEqual(evidence["instructions"][0]["classification"], "tainted")
            self.assertEqual(evidence["instructions"][1]["classification"], "unknown")
            self.assertEqual(record["instructionMeasurement"], "not-measured")

    def test_batch_deadline_covers_setup_and_scoring(self) -> None:
        for phase, expected_code in [("setup", 2), ("scoring", 1)]:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as folder:
                clock = [0.0]
                adapter = run_claude.Claude("tested-model")

                def expire(
                    *args: object, clock: list[float] = clock, **kwargs: object
                ) -> int:
                    clock[0] = run_claude.BATCH_TIMEOUT + 1
                    return 0

                with (
                    mock.patch.object(
                        score.time,
                        "monotonic",
                        side_effect=lambda clock=clock: clock[0],
                    ),
                    mock.patch.object(
                        adapter,
                        "preflight",
                        side_effect=expire if phase == "setup" else None,
                    ),
                    mock.patch.object(
                        adapter, "turn", return_value=("Reply", [])
                    ) as host,
                    mock.patch.object(
                        run_claude, "initialize_workspace", autospec=True
                    ),
                    mock.patch.object(run_claude, "verify_workspace", autospec=True),
                    mock.patch.object(
                        run_claude,
                        "capture_status",
                        return_value=score.read_json(FIXTURES / "manual.json")[
                            "status"
                        ],
                    ),
                    mock.patch.object(
                        score, "score_record", side_effect=expire, autospec=True
                    ),
                ):
                    code = run_claude.run_batch(adapter, "status-summary", Path(folder))
                self.assertEqual(code, expected_code)
                record = score.read_json(
                    Path(folder) / "claude-code/status-summary/1.json"
                )
                self.assertIn("deadline", record["notRun"])
                self.assertNotIn("scores", record)
                if phase == "setup":
                    host.assert_not_called()

    def test_sigterm_unwinds_and_restores_the_previous_handler(self) -> None:
        previous = signal.getsignal(signal.SIGTERM)
        with self.assertRaises(KeyboardInterrupt), run_claude.interruption_signals():
            signal.raise_signal(signal.SIGTERM)
        self.assertEqual(signal.getsignal(signal.SIGTERM), previous)

    def test_timeout_kills_a_descendant_that_ignores_termination(self) -> None:
        child = (
            "import signal,time; "
            "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
            "print('child-ready',flush=True); time.sleep(30)"
        )
        parent = (
            "import subprocess,sys,time; "
            f"subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(30)"
        )
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired) as caught:
            run_claude.command([sys.executable, "-c", parent], ROOT, timeout=1)
        self.assertIn(b"child-ready", caught.exception.output)
        # The child keeps the captured pipe open and ignores TERM. communicate
        # cannot finish this soon unless cleanup also terminates that descendant.
        self.assertLess(time.monotonic() - started, 15)

    def test_enclosing_deadline_limits_commands_without_starting_after_expiry(
        self,
    ) -> None:
        clock = [0.0]
        with mock.patch.object(
            score.time, "monotonic", side_effect=lambda clock=clock: clock[0]
        ):
            with score.deadline(50):
                clock[0] = 10
                with score.deadline(100):
                    self.assertEqual(score.remaining_timeout(600), 40)
                    clock[0] = 50
                    with (
                        mock.patch.object(run_claude.subprocess, "Popen") as start,
                        self.assertRaises(subprocess.TimeoutExpired),
                    ):
                        run_claude.command(["must-not-start"], ROOT)
                    start.assert_not_called()
            self.assertEqual(score.remaining_timeout(600), 600)

    def test_session_deadline_stops_between_turns_and_retains_reply(self) -> None:
        clock = [0.0]
        record = score.read_json(FIXTURES / "manual.json")
        record["messages"], record["filesRead"] = [], []
        adapter = run_claude.Claude("tested-model")

        def turn(prompt: str, workspace: Path) -> tuple[str, list[str]]:
            clock[0] = run_claude.SESSION_TIMEOUT + 1
            return "First reply", []

        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch.object(
                score.time, "monotonic", side_effect=lambda clock=clock: clock[0]
            ),
            mock.patch.object(run_claude, "verify_workspace", autospec=True),
            mock.patch.object(adapter, "turn", side_effect=turn, autospec=True) as host,
        ):
            run_claude.play_session(
                adapter,
                {"turns": [{"developer": "First"}, {"developer": "Second"}]},
                Path(folder),
                record,
            )
        self.assertEqual(host.call_count, 1)
        self.assertEqual(record["messages"], ["First reply"])
        self.assertIn("deadline", record["notRun"])

    def test_turn_limit_rejects_continuation_before_host_setup(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "parent.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "name": "parent",
                        "fixture": "sessions/status-summary",
                        "turns": [{"developer": "Start"}],
                    }
                )
            )
            (root / "child.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "name": "child",
                        "continues": "parent",
                        "turns": [{"developer": "Again"}] * 25,
                    }
                )
            )
            with self.assertRaisesRegex(score.RecordError, "turn limit"):
                run_claude.sessions_for("parent", root)

    def test_failed_workspace_setup_never_enters_host_batch(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight", autospec=True),
                mock.patch.object(adapter, "batch", autospec=True) as batch,
                mock.patch.object(
                    run_claude,
                    "initialize_workspace",
                    autospec=True,
                    side_effect=run_claude.HostError("workspace initialization denied"),
                ),
            ):
                code = run_claude.run_batch(adapter, "status-summary", Path(folder))
            self.assertEqual(code, 2)
            batch.assert_not_called()
            record = score.read_json(Path(folder) / "claude-code/status-summary/1.json")
            self.assertIn("initialization denied", record["notRun"])

    def test_interruption_leaves_a_valid_not_run_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(adapter, "turn", side_effect=KeyboardInterrupt),
                mock.patch.object(run_claude, "initialize_workspace"),
                mock.patch.object(run_claude, "verify_workspace"),
            ):
                self.assertEqual(
                    run_claude.run_batch(adapter, "status-summary", out), 2
                )
            record = score.read_json(out / "claude-code/status-summary/1.json")
            score.validate_record(record)
            self.assertIn("interrupted", record["notRun"])
            self.assertNotIn("scores", record)

    def test_batch_setup_failure_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            adapter = run_claude.Claude("tested-model")
            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(run_claude, "initialize_workspace", autospec=True),
                mock.patch.object(
                    adapter, "batch", side_effect=run_claude.HostError("setup failed")
                ),
            ):
                self.assertEqual(
                    run_claude.run_batch(adapter, "status-summary", Path(folder)), 2
                )
            record = score.read_json(Path(folder) / "claude-code/status-summary/1.json")
            self.assertEqual(record["notRun"], "setup failed")
            self.assertNotIn("scores", record)

    def test_batch_replays_conversation_then_forks_finished_workspace(self) -> None:
        """Synthetic CLI boundary; exercises the real batch, adapter, and scorer."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sessions = root / "sessions"
            sessions.mkdir()
            sessions.joinpath("status-summary.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "name": "status-summary",
                        "fixture": "sessions/status-summary",
                        "turns": [
                            {"developer": "Status"},
                            {"developer": "Next", "expects": "Status"},
                        ],
                    }
                )
            )
            sessions.joinpath("continued.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "name": "continued",
                        "continues": "status-summary",
                        "turns": [{"developer": "Read the finished workspace"}],
                    }
                )
            )
            evals = root / "evals"
            evals.mkdir()
            for i, name in enumerate(["status-summary", "continued"], 1):
                evals.joinpath(f"SR-DLG-{i:03}.json").write_text(
                    json.dumps(
                        {
                            "schemaVersion": 1,
                            "rule": f"SR-DLG-{i:03}",
                            "session": name,
                            "assertions": [
                                {
                                    "kind": "file_matches",
                                    "path": "result.txt",
                                    "pattern": "Status reported",
                                }
                            ],
                        }
                    )
                )
            conversation_turns = {}

            def cli(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                output = ""
                if args[:2] == ["git", "show"]:
                    # The fixture commits no host settings file.
                    return subprocess.CompletedProcess(args, 128, "", "")
                if args[:2] == ["git", "init"]:
                    (cwd / ".git").mkdir()
                elif args[:2] == ["git", "rev-parse"]:
                    output = (
                        str(cwd / ".git") if "--absolute-git-dir" in args else str(cwd)
                    )
                elif args[0] == "claude":
                    count = conversation_turns.get(cwd.name, 0)
                    if count and "--resume" not in args:
                        raise AssertionError("conversation was lost")
                    if not count and "--resume" in args:
                        raise AssertionError(
                            "continuation reused the parent conversation"
                        )
                    if cwd.name == "continued":
                        self.assertEqual(
                            (cwd / "result.txt").read_text(), "Status reported"
                        )
                    (cwd / "result.txt").write_text("Status reported")
                    self.assertEqual(
                        set(env) & {"HOME", "CLAUDE_CONFIG_DIR"},
                        {"HOME", "CLAUDE_CONFIG_DIR"},
                    )
                    self.assertNotIn(str(Path.home()), env["HOME"])
                    (cwd.parent.parent / "control/instructions.jsonl").write_text(
                        json.dumps({"hook_event_name": "SessionStart"}) + "\n"
                    )
                    conversation_turns[cwd.name] = count + 1
                    output = "\n".join(
                        json.dumps(e)
                        for e in [
                            {
                                "type": "system",
                                "subtype": "init",
                                "model": "tested-model",
                                "claude_code_version": "fixture-version",
                                "session_id": cwd.name,
                                "skills": ["specflow:spec-workflow"],
                            },
                            {
                                "type": "assistant",
                                "message": {
                                    "content": [
                                        {
                                            "type": "tool_use",
                                            "name": "Read",
                                            "input": {
                                                "file_path": str(cwd / "result.txt")
                                            },
                                        }
                                    ]
                                },
                            },
                            {
                                "type": "result",
                                "subtype": "success",
                                "result": "Status reported",
                                "total_cost_usd": 0.25 * (count + 1),
                            },
                        ]
                    )
                elif "validate_spec.py" in " ".join(args):
                    output = json.dumps(
                        score.read_json(FIXTURES / "manual.json")["status"]
                    )
                return subprocess.CompletedProcess(args, 0, output, "")

            adapter = run_claude.Claude("tested-model")
            adapter.version = "fixture-version"
            sign_in = mock.patch.dict(
                os.environ, {run_claude.AUTH_VARIABLE: "synthetic"}
            )
            sign_in.start()
            self.addCleanup(sign_in.stop)
            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(run_claude, "command", side_effect=cli),
            ):
                self.assertEqual(
                    run_claude.run_batch(
                        adapter,
                        "continued",
                        root / "results",
                        session_dir=sessions,
                        eval_dir=evals,
                    ),
                    0,
                )
            parent = score.read_json(root / "results/claude-code/status-summary/1.json")
            child = score.read_json(root / "results/claude-code/continued/1.json")
            self.assertEqual(len(parent["messages"]), 2)
            self.assertEqual(parent["readMeasurement"], "measured")
            self.assertEqual(parent["filesRead"], [["result.txt"], ["result.txt"]])
            self.assertEqual(
                child["continuesRun"],
                {"host": "claude-code", "session": "status-summary", "n": 1},
            )
            self.assertIn("result.txt", child["unchanged"])
            self.assertTrue(child["scores"][0]["passed"])
            self.assertNotIn(str(root), json.dumps([parent, child]))
            evaluation = score.read_json(evals / "SR-DLG-001.json")
            evaluation["assertions"][0]["pattern"] = "deliberately broken"
            score.write_json(evals / "SR-DLG-001.json", evaluation)
            conversation_turns.clear()
            with (
                mock.patch.object(adapter, "preflight", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=cli, autospec=True
                ),
            ):
                self.assertEqual(
                    run_claude.run_batch(
                        adapter,
                        "continued",
                        root / "results",
                        session_dir=sessions,
                        eval_dir=evals,
                    ),
                    2,
                )
            self.assertNotIn("continued", conversation_turns)
            child = score.read_json(root / "results/claude-code/continued/2.json")
            self.assertIn("parent", child["notRun"])
            self.assertNotIn("scores", child)

    INIT: ClassVar[dict] = {
        "type": "system",
        "subtype": "init",
        "model": "tested-model",
        "claude_code_version": "fixture-version",
        "session_id": "conversation",
        "skills": ["specflow:spec-workflow"],
    }
    DONE: ClassVar[dict] = {
        "type": "result",
        "subtype": "success",
        "result": "ok",
        "total_cost_usd": 0.1,
    }

    @contextlib.contextmanager
    def claude_turn(
        self, events: list[dict], log: list[dict]
    ) -> Iterator[tuple[run_claude.Claude, Path, mock.Mock]]:
        """Synthetic host process inside a real batch layout; no Claude runs."""
        with tempfile.TemporaryDirectory() as folder:
            batch = Path(folder).resolve()
            workspace = batch / "workspaces/session"
            for path in (workspace, batch / "control", batch / "resources/specflow"):
                path.mkdir(parents=True)
            adapter = run_claude.Claude("tested-model")
            adapter.plugin = batch / "resources/specflow"
            adapter.version = "fixture-version"

            def cli(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                if args[0] == "git":
                    # No host settings file is committed in this workspace.
                    return subprocess.CompletedProcess(args, 128, "", "")
                (batch / "control/instructions.jsonl").write_text(
                    "".join(json.dumps(e) + "\n" for e in log)
                )
                return subprocess.CompletedProcess(
                    args, 0, "\n".join(json.dumps(e) for e in events), ""
                )

            with (
                mock.patch.object(adapter, "preflight"),
                mock.patch.object(run_claude, "command", side_effect=cli) as command,
                mock.patch.dict(os.environ, {run_claude.AUTH_VARIABLE: "synthetic"}),
            ):
                yield adapter, workspace, command

    def test_claude_permission_denial_and_model_omission_are_failures(self) -> None:
        started = [{"hook_event_name": "SessionStart"}]
        for final in [
            {"is_error": True},
            {"permission_denials": ["Read"]},
            {"subtype": "error_max_turns"},
        ]:
            events = [self.INIT, {**self.DONE, **final}]
            with (
                self.subTest(final=final),
                self.claude_turn(events, started) as (adapter, workspace, _),
                self.assertRaisesRegex(run_claude.HostError, "did not succeed"),
            ):
                adapter.turn("Status", workspace)
        for init in [{"model": ""}, {"claude_code_version": "other"}, {"skills": []}]:
            events = [{**self.INIT, **init}, self.DONE]
            with (
                self.subTest(init=init),
                self.claude_turn(events, started) as (adapter, workspace, _),
                self.assertRaises(run_claude.HostError),
            ):
                adapter.turn("Status", workspace)

    def test_claude_launch_isolates_environment_and_denies_private_paths(self) -> None:
        started = [{"hook_event_name": "SessionStart"}]
        with (
            self.claude_turn([self.INIT, self.DONE], started) as (
                adapter,
                workspace,
                command,
            ),
            mock.patch.dict(os.environ, {"SYNTHETIC_SECRET": "leak"}),
        ):
            adapter.turn("Status", workspace)
            args, _, env = command.call_args.args
            batch = workspace.parent.parent
            settings = json.loads((batch / "control/settings.json").read_text())
        self.assertNotIn("SYNTHETIC_SECRET", env)
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], str(batch / "control/claude-home"))
        self.assertEqual(args[args.index("--permission-mode") + 1], "dontAsk")
        self.assertEqual(args[args.index("--setting-sources") + 1], "project,local")
        sandbox = settings["sandbox"]
        self.assertTrue(sandbox["enabled"] and sandbox["failIfUnavailable"])
        self.assertFalse(sandbox["allowUnsandboxedCommands"])
        self.assertEqual(
            sandbox["credentials"]["envVars"],
            [{"name": run_claude.AUTH_VARIABLE, "mode": "deny"}],
        )
        self.assertIn(str(batch / "control"), sandbox["filesystem"]["denyRead"])
        self.assertIn(str(batch / "workspaces"), sandbox["filesystem"]["denyRead"])
        self.assertIn(str(workspace), sandbox["filesystem"]["allowRead"])
        deny = settings["permissions"]["deny"]
        for rule in (
            f"Read(/{batch / 'control'}/**)",
            f"Read(/{Path.home().resolve()}/**)",
            f"Edit(/{batch / 'resources/specflow'}/**)",
        ):
            self.assertIn(rule, deny)
        self.assertFalse(settings["autoMemoryEnabled"])

    def test_claude_load_hook_measures_imports_and_rejects_missing_evidence(
        self,
    ) -> None:
        def load(path: Path, digest: str, parent: Path | None = None) -> dict:
            return {
                "hook_event_name": "InstructionsLoaded",
                "file_path": str(path),
                "sha256": digest,
                "parent_file_path": str(parent) if parent else None,
            }

        events = [self.INIT, self.DONE]
        with (
            self.claude_turn(events, []) as (adapter, workspace, _),
            self.assertRaisesRegex(run_claude.HostError, "ignored"),
        ):
            adapter.turn("Status", workspace)
        started = {"hook_event_name": "SessionStart"}
        with self.claude_turn(events, [started]) as (adapter, workspace, _):
            (workspace / "CLAUDE.md").write_text("fixture")
            adapter.turn("Status", workspace)
            # The host reported no load for a root instruction that exists.
            self.assertEqual(adapter.instruction_measurement, "not-measured")
        with tempfile.TemporaryDirectory() as folder:
            root, extra = Path(folder) / "CLAUDE.md", Path(folder) / "extra.md"
            log = [started, load(extra, "b" * 64, root), load(root, "a" * 64)]
            path = Path(folder) / "log.jsonl"
            path.write_text("".join(json.dumps(e) + "\n" for e in log))
            observations, hooked = run_claude.read_instruction_log(path)
            self.assertTrue(hooked)
            self.assertEqual(
                observations[str(root)], {"sha256": "a" * 64, "imports": [str(extra)]}
            )
            self.assertEqual(observations[str(extra)]["imports"], [])
            path.write_text(
                "".join(
                    json.dumps(e) + "\n"
                    for e in [started, load(root, "a" * 64), load(root, "c" * 64)]
                )
            )
            # Two contents for one path in a turn leave the hash unknown.
            self.assertIsNone(
                run_claude.read_instruction_log(path)[0][str(root)]["sha256"]
            )
            path.write_text("not json\n")
            self.assertEqual(run_claude.read_instruction_log(path), ({}, False))

    def test_claude_reads_name_shell_files_and_reject_opaque_commands(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / "notes.md").write_text("x")

            def stream(name: str, data: dict) -> list[dict]:
                block = {"type": "tool_use", "name": name, "input": data}
                return [{"message": {"content": [block]}}]

            named = stream("Bash", {"command": "cat notes.md"})
            self.assertEqual(
                run_claude.named_reads(named, workspace),
                ([str(workspace / "notes.md")], True),
            )
            for opaque in (
                stream("Bash", {"command": "cat *.md"}),
                stream("Bash", {"command": "grep -r token ."}),
                stream("Grep", {"pattern": "token"}),
            ):
                self.assertFalse(run_claude.named_reads(opaque, workspace)[1])

    def test_claude_probe_passes_only_on_observed_denials_and_intact_plugin(
        self,
    ) -> None:
        def host(
            leak: bool = False,
            allow: str = "",
            write: bool = False,
            unrelated: bool = False,
        ):
            def launch(
                adapter: run_claude.Claude, prompt: str, workspace: Path, budget: float
            ) -> list[dict]:
                payload = json.loads((workspace / "probe.json").read_text())
                control = workspace.parent.parent / "control"
                log = [{"hook_event_name": "SessionStart"}]
                for name, parent in (("imported.md", "CLAUDE.md"), ("CLAUDE.md", "")):
                    path = workspace / name
                    log.append(
                        {
                            "hook_event_name": "InstructionsLoaded",
                            "file_path": str(path),
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "parent_file_path": str(workspace / parent)
                            if parent
                            else None,
                        }
                    )
                (control / "instructions.jsonl").write_text(
                    "".join(json.dumps(e) + "\n" for e in log)
                )
                if write:
                    Path(payload["plugin_new"]).write_text("probe")
                blocks = []
                for number, (name, (tool, key)) in enumerate(
                    run_claude.NATIVE_PROBES.items()
                ):
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": str(number),
                            "name": tool,
                            "input": {"file_path": payload[key]},
                        }
                    )
                    blocks.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": str(number),
                            "is_error": name not in ("plugin-read", allow),
                            "content": Path(payload["control"]).read_text()
                            if leak
                            else "denied",
                        }
                    )
                shell = {
                    name: True
                    for name in score.RELEASE_BOUNDARY_CHECKS
                    if name.startswith("shell-")
                }
                shell.update(
                    {"helper-status": True, "tool-secret-environment-denied": True}
                )
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": "shell",
                        "name": "Bash",
                        "input": {"command": run_claude.PROBE_COMMAND},
                    }
                )
                blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": "shell",
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({payload["report"]: shell}),
                            }
                        ],
                    }
                )
                denials = [
                    {"tool_use_id": str(number)}
                    for number, name in enumerate(run_claude.NATIVE_PROBES)
                    if name not in ("plugin-read", allow) and not unrelated
                ]
                return [
                    {"message": "plain"},
                    {"message": {"content": blocks}},
                    {"type": "result", "permission_denials": denials},
                ]

            return launch

        def identify(adapter: run_claude.Claude) -> None:
            adapter.version, adapter.configuration_sha256 = "fixture-version", "c" * 64

        def failed(proof: dict) -> set[str]:
            return {n for n, c in proof["checks"].items() if c["passed"] is not True}

        with tempfile.TemporaryDirectory() as folder:
            scratch = Path(folder).resolve()
            for options, expected in (
                ({}, set()),
                (
                    {"allow": "native-control-read-denied"},
                    {"native-control-read-denied", "effective-settings"},
                ),
                (
                    {"write": True},
                    {
                        "native-plugin-write-denied",
                        "native-symlink-write-denied",
                        "shell-plugin-write-denied",
                        "shell-symlink-write-denied",
                        "effective-settings",
                    },
                ),
                (
                    # Tool errors the host did not list as permission denials.
                    {"unrelated": True},
                    {
                        *(
                            name
                            for name in run_claude.NATIVE_PROBES
                            if name != "plugin-read"
                        ),
                        "effective-settings",
                    },
                ),
            ):
                with (
                    self.subTest(options=options),
                    mock.patch.object(run_claude.Claude, "identify", identify),
                    mock.patch.object(run_claude.Claude, "launch", host(**options)),
                ):
                    proof = run_claude.boundary_probe("tested-model", scratch=scratch)
                    self.assertEqual(failed(proof), expected)
                    self.assertEqual(
                        set(proof["checks"]), set(score.RELEASE_BOUNDARY_CHECKS)
                    )
                    self.assertNotIn(str(scratch), json.dumps(proof))
            with (
                mock.patch.object(run_claude.Claude, "identify", identify),
                mock.patch.object(run_claude.Claude, "launch", host(leak=True)),
            ):
                leaked = failed(
                    run_claude.boundary_probe("tested-model", scratch=scratch)
                )
            self.assertIn("native-home-read-denied", leaked)
            self.assertEqual(list(scratch.iterdir()), [])

    def test_claude_refuses_host_settings_an_earlier_turn_wrote(self) -> None:
        started = [{"hook_event_name": "SessionStart"}]
        for name in run_claude.HOST_SETTINGS:
            with (
                self.subTest(name=name),
                self.claude_turn([self.INIT, self.DONE], started) as (
                    adapter,
                    workspace,
                    command,
                ),
            ):
                path = workspace / name
                path.parent.mkdir(exist_ok=True)
                path.write_text('{"hooks": {}}')
                with self.assertRaisesRegex(
                    run_claude.HostError, "differ from fixture"
                ):
                    adapter.turn("Status", workspace)
                self.assertFalse(
                    any(call.args[0][0] != "git" for call in command.call_args_list)
                )
        with self.claude_turn([self.INIT, self.DONE], started) as (_, workspace, _):
            settings = run_claude.claude_settings(workspace.parent.parent, workspace)
        # Literal expectation: an absolute permission path needs two slashes.
        self.assertIn(
            f"Edit(//{str(workspace).lstrip('/')}/.claude/settings.local.json)",
            settings["permissions"]["deny"],
        )
        self.assertIn(
            str(workspace / ".mcp.json"), settings["sandbox"]["filesystem"]["denyWrite"]
        )

    def test_shell_reads_are_unmeasured_when_a_read_cannot_be_named(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace, plugin = Path(folder) / "ws", Path(folder) / "plugin"
            for path in (workspace / "docs", plugin):
                path.mkdir(parents=True)
            (workspace / "docs/a.md").write_text("x")
            (plugin / "reference.md").write_text("x")
            self.assertEqual(
                run_claude.shell_reads(f"cat {plugin}/reference.md", workspace, plugin),
                ([str(plugin / "reference.md")], True),
            )
            for opaque in ("cd docs && cat a.md", 'cat "$f"', "cat `ls`", "cat docs/*"):
                with self.subTest(command=opaque):
                    self.assertFalse(run_claude.shell_reads(opaque, workspace)[1])

    def test_codex_launches_the_resolved_binary_behind_links_and_shims(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            real = root / "installs/0.1.0/bin"
            real.mkdir(parents=True)
            (real / "codex").write_text("binary")
            (root / "installs/latest").symlink_to(root / "installs/0.1.0")
            (root / "mise").write_text("manager")
            (root / "shim").symlink_to(root / "mise")
            via_link = root / "installs/latest/bin/codex"
            # No link may remain on the launched path.
            self.assertEqual(run_codex.codex_binary(str(via_link)), real / "codex")
            found = subprocess.CompletedProcess([], 0, f"{via_link}\n", "")
            with mock.patch.object(run_claude, "command", return_value=found):
                # The shim resolves to the manager, never to Codex itself.
                self.assertEqual(
                    run_codex.codex_binary(str(root / "shim")), real / "codex"
                )
            missing = subprocess.CompletedProcess([], 1, "", "")
            with (
                mock.patch.object(run_claude, "command", return_value=missing),
                self.assertRaises(run_claude.HostError),
            ):
                run_codex.codex_binary(str(root / "shim"))
            (root / "wrapper").write_text("not codex")
            with self.assertRaises(run_claude.HostError):
                run_codex.codex_binary(str(root / "wrapper"))

    def test_codex_configuration_digest_is_the_same_on_every_turn(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            for name in ("control", "workspaces", "resources/specflow"):
                (root / name).mkdir(parents=True)
            adapter = run_codex.Codex("requested-model")
            adapter.plugin = root / "resources/specflow"
            version = subprocess.CompletedProcess([], 0, "codex-cli 9.9.9\n", "")
            with (
                mock.patch.object(run_codex.shutil, "which", return_value="/bin/codex"),
                mock.patch.object(run_codex, "find_git", return_value=Path(__file__)),
                mock.patch.object(
                    run_codex, "codex_binary", return_value=Path("/opt/codex/bin/codex")
                ),
                mock.patch.object(run_claude, "command", return_value=version),
            ):
                adapter.identify()
                self.assertEqual(adapter.executable, "/opt/codex/bin/codex")
                self.assertEqual(adapter.runtime, [Path("/opt/codex/bin")])
                first = adapter.configuration_sha256
                # State a finished first turn leaves behind.
                adapter.conversation, adapter.model = "thread", "resolved-model"
                adapter.identify()
            self.assertEqual(adapter.configuration_sha256, first)
            self.assertEqual(adapter.version, "9.9.9")

    def test_claude_preflight_requires_proof_for_this_exact_configuration(self) -> None:
        adapter = run_claude.Claude("tested-model")
        revision = "a" * 40

        def identify() -> None:
            adapter.version = "fixture-version"
            adapter.configuration_sha256 = "c" * 64

        proof = {
            "scope": "installed-host-boundary",
            "host": "claude-code",
            "hostVersion": "fixture-version",
            "runtimeRevision": revision,
            "configurationSha256": "c" * 64,
            "runnerSha256": run_claude.runner_digest(adapter),
            "checks": {
                name: {"passed": True, "evidence": "observed"}
                for name in score.RELEASE_BOUNDARY_CHECKS
            },
        }
        with (
            mock.patch.object(adapter, "identify", side_effect=identify),
            mock.patch.object(run_claude, "package_revision", return_value=revision),
        ):
            for change in (
                None,
                {"scope": "synthetic-shell-boundary-only"},
                {"hostVersion": "other"},
                {"configurationSha256": "d" * 64},
                {"runtimeRevision": "b" * 40},
                {"runnerSha256": "e" * 64},
                {"checks": ["not a mapping"]},
                {
                    "checks": {
                        **proof["checks"],
                        "cleanup": {"passed": False, "evidence": "left"},
                    }
                },
            ):
                adapter.boundary = None if change is None else {**proof, **change}
                with (
                    self.subTest(change=change),
                    self.assertRaisesRegex(run_claude.HostError, "boundary proof"),
                ):
                    adapter.preflight()
            adapter.boundary = proof
            adapter.preflight()
        self.assertEqual(adapter.boundary_sha256, score.evidence_digest(proof))

    def test_command_timeout_kills_process_and_captures_failures(self) -> None:
        result = run_claude.command(
            [sys.executable, "-c", "import sys; print('failed'); sys.exit(7)"], ROOT
        )
        self.assertEqual((result.returncode, result.stdout.strip()), (7, "failed"))
        with self.assertRaises(subprocess.TimeoutExpired):
            run_claude.command(
                [sys.executable, "-c", "import time; time.sleep(10)"], ROOT, timeout=1
            )

    def test_git_failure_never_initializes_parent_or_invokes_host(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            failed = subprocess.CompletedProcess([], 1, "", "denied")
            with (
                mock.patch.object(run_claude, "command", return_value=failed),
                self.assertRaisesRegex(run_claude.HostError, "denied"),
            ):
                run_claude.initialize_workspace(workspace)
            self.assertEqual(list(workspace.iterdir()), [])

    def test_capture_rejects_symlinks_and_external_edit_paths(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / "link").symlink_to(ROOT)
            with self.assertRaises(run_claude.HostError):
                run_claude.snapshot(workspace)
            with self.assertRaises(run_claude.HostError):
                run_claude.write_files(workspace, {"link/forbidden": "no"})

    def test_normalization_includes_embedded_contents_and_keys(self) -> None:
        value = {
            "/home/user/work/file": [
                "read /home/user/work/file and /home/user/plugin/SKILL.md",
                {"text": "/home/user/private"},
            ]
        }
        result = run_claude.normalize(
            value,
            {
                "/home/user/work": "<workspace>",
                "/home/user/plugin": "<plugin>",
                "/home/user": "<home>",
            },
        )
        self.assertEqual(
            result,
            {
                "<workspace>/file": [
                    "read <workspace>/file and <plugin>/SKILL.md",
                    {"text": "<home>/private"},
                ]
            },
        )

    def test_package_hash_matches_git_and_detects_mismatch(self) -> None:
        expected = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        self.assertEqual(run_claude.package_revision(score.PLUGIN), expected)
        with self.assertRaisesRegex(run_claude.HostError, "differs"):
            run_claude.verify_plugin(score.PLUGIN, "0" * 40)

    def test_enclosing_repository_is_rejected_before_host_turn(self) -> None:
        with (
            tempfile.TemporaryDirectory() as folder,
            self.assertRaisesRegex(run_claude.HostError, "own .git"),
        ):
            run_claude.verify_workspace(Path(folder))

    def test_rerun_never_overwrites_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            first, number = run_claude.reserve_record(out, "codex", "sample")
            first.write_text("retained")
            second, next_number = run_claude.reserve_record(out, "codex", "sample")
            self.assertEqual((number, next_number), (1, 2))
            self.assertEqual(first.read_text(), "retained")
            self.assertNotEqual(first, second)

    def test_blocked_launch_records_not_run_without_starting_host(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            adapter = run_claude.Claude("test-model")
            with (
                mock.patch.object(
                    adapter, "turn", side_effect=AssertionError("must not launch")
                ),
                mock.patch.dict(os.environ),
            ):
                os.environ.pop(run_claude.AUTH_VARIABLE, None)
                self.assertEqual(
                    run_claude.run_batch(adapter, "status-summary", out), 2
                )
            record = score.read_json(out / "claude-code/status-summary/1.json")
            self.assertIn("sign-in", record["notRun"])
            self.assertNotIn("scores", record)
            self.assertFalse(record["releaseEvidence"])
            self.assertEqual(record["model"], "test-model")
            self.assertEqual(record["hostVersion"], "not-started")
            self.assertIsNone(record["status"])
            self.assertEqual(record["messages"], [])
            self.assertEqual(record["files"], [])
            self.assertEqual(record["instructionMeasurement"], "not-measured")
            score.validate_record(record)

    def test_edit_precedes_turn_and_expects_breaks_without_a_second_reply(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            record = score.read_json(FIXTURES / "manual.json")
            record["messages"], record["filesRead"] = [], []
            adapter = run_claude.Claude("test-model")
            session = {
                "turns": [
                    {
                        "developer": "Read it",
                        "edit": {"path": "note.md", "text": "second writer"},
                    },
                    {"developer": "Continue", "expects": "approve"},
                ]
            }

            def turn(prompt: str, root: Path) -> tuple[str, list[str]]:
                self.assertEqual((root / "note.md").read_text(), "second writer")
                return "Stop here", []

            with (
                mock.patch.object(adapter, "turn", side_effect=turn),
                mock.patch.object(run_claude, "verify_workspace"),
                mock.patch.object(
                    run_claude, "capture_status", return_value=record["status"]
                ),
            ):
                run_claude.play_session(adapter, session, workspace, record)
            self.assertEqual(record["brokenAt"], 2)
            self.assertEqual(record["messages"], ["Stop here"])
            self.assertEqual(
                record["files"], [{"path": "note.md", "text": "second writer"}]
            )


class CodexConversationTest(unittest.TestCase):
    """Synthetic exec JSONL only; no host, authentication, or policy proof."""

    def setUp(self) -> None:
        self.adapter = run_codex.Codex("requested-model")
        self.events = [
            {"type": "thread.started", "thread_id": "synthetic-thread"},
            {"type": "turn.started"},
            {
                "type": "item.completed",
                "item": {"id": "comment", "type": "agent_message", "text": "Working"},
            },
            {
                "type": "item.completed",
                "item": {"id": "final", "type": "agent_message", "text": "Finished"},
            },
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 12,
                    "cached_input_tokens": 3,
                    "output_tokens": 4,
                },
            },
        ]

    def accept(self) -> tuple[str, list[str]]:
        return self.adapter.accept_turn(
            subprocess.CompletedProcess(
                [], 0, "\n".join(json.dumps(e) for e in self.events), ""
            )
        )

    def test_final_reply_and_usage_without_invented_measurements(self) -> None:
        self.assertEqual(self.accept(), ("Finished", []))
        self.assertEqual(self.adapter.conversation, "synthetic-thread")
        self.assertEqual(self.adapter.usage, [self.events[-1]["usage"]])
        self.assertEqual(self.adapter.instruction_measurement, "not-measured")
        self.assertEqual(self.adapter.instruction_observations, {})
        self.assertEqual(self.adapter.version, "not-started")
        self.assertEqual(self.adapter.model, "requested-model")

    def test_resume_requires_same_thread_and_reset_starts_new_conversation(
        self,
    ) -> None:
        self.accept()
        self.accept()
        self.assertEqual(len(self.adapter.usage), 2)
        self.events[0]["thread_id"] = "wrong-thread"
        with self.assertRaises(run_claude.HostError):
            self.accept()
        self.assertEqual(self.adapter.conversation, "synthetic-thread")
        self.assertEqual(len(self.adapter.usage), 2)
        self.adapter.new_conversation()
        self.assertIsNone(self.adapter.conversation)
        self.assertEqual(self.adapter.usage, [])
        self.accept()
        self.assertEqual(self.adapter.conversation, "wrong-thread")

    def test_failed_or_malformed_stream_never_advances_state(self) -> None:
        for bad in (
            [],
            [None],
            [{"type": "unknown"}],
            self.events[:-1],
            self.events[1:],
            self.events + [self.events[-1]],
            self.events + [{"type": "error", "message": "private diagnostic"}],
            self.events[:-1] + [{"type": "turn.failed"}],
        ):
            with self.subTest(events=bad):
                self.events, original = bad, self.events
                with self.assertRaises(run_claude.HostError) as caught:
                    self.accept()
                self.assertNotIn("private diagnostic", str(caught.exception))
                self.assertIsNone(self.adapter.conversation)
                self.assertEqual(self.adapter.usage, [])
                self.events = original

    def test_invalid_reply_identity_usage_or_event_order_is_rejected(self) -> None:
        cases = [
            (0, "thread_id", ""),
            (0, "thread_id", 42),
            (-1, "usage", {}),
            (
                -1,
                "usage",
                {"input_tokens": True, "cached_input_tokens": 0, "output_tokens": 1},
            ),
        ]
        for index, key, value in cases:
            with self.subTest(key=key, value=value):
                original = copy.deepcopy(self.events)
                self.events[index][key] = value
                with self.assertRaises(run_claude.HostError):
                    self.accept()
                self.events = original
        self.events[3]["item"]["text"] = None
        with self.assertRaises(run_claude.HostError):
            self.accept()
        self.events[3]["item"]["text"] = "Finished"
        self.events[0], self.events[1] = self.events[1], self.events[0]
        with self.assertRaises(run_claude.HostError):
            self.accept()

    def test_nonzero_exit_and_invalid_json_discard_raw_streams(self) -> None:
        for code, raw in ((7, "private output"), (0, "private invalid JSON")):
            with self.subTest(code=code):
                with self.assertRaises(run_claude.HostError) as caught:
                    self.adapter.accept_turn(
                        subprocess.CompletedProcess([], code, raw, "private stderr")
                    )
                self.assertNotIn("private", str(caught.exception))
                self.assertIsNone(self.adapter.conversation)

    def test_direct_turn_stays_blocked_before_any_command(self) -> None:
        with (
            mock.patch.object(run_claude, "command", autospec=True) as command,
            self.assertRaises(run_claude.HostError),
        ):
            self.adapter.turn("request", ROOT)
        command.assert_not_called()

    def test_failing_command_is_work_and_its_named_files_are_reads(self) -> None:
        self.events[2]["item"] = {
            "type": "command_execution",
            "command": "bash -lc 'cat notes.md'",
            "status": "failed",
            "exit_code": 1,
        }
        self.assertEqual(self.accept()[0], "Finished")
        self.assertEqual(self.adapter.commands, ["bash -lc 'cat notes.md'"])

    def write_rollout(self, home: Path, records: list[dict]) -> None:
        folder = home / "sessions/2026/01/01"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "rollout-2026-01-01-synthetic-thread.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in records)
        )

    def test_live_turn_takes_identity_policy_and_instructions_from_host_record(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            workspace, home = root / "workspaces/session", root / "control/home"
            for path in (workspace, home):
                path.mkdir(parents=True)
            (workspace / "AGENTS.md").write_text("Fixture rule.\n")
            (workspace / "notes.md").write_text("x")
            adapter = self.adapter
            adapter.root, adapter.home, adapter.version = root, home, "9.9.9"
            adapter.git = Path("/usr/bin/git")
            adapter.runtime = [Path("/opt/codex/bin")]
            self.events[2]["item"] = {
                "type": "command_execution",
                "command": "bash -lc 'cat notes.md'",
                "status": "completed",
            }
            stream = "\n".join(json.dumps(e) for e in self.events)
            profile = {"type": "managed", "writable": [str(workspace)]}
            # The proof holds the proven profile with batch paths normalized.
            adapter.boundary = {
                "effectiveProfile": {"type": "managed", "writable": ["<workspace>"]}
            }

            def records(text: str, **context: object) -> list[dict]:
                agents = {"directory": str(workspace), "text": text}
                return [
                    {"type": "session_meta", "payload": {"cli_version": "9.9.9"}},
                    {
                        "type": "world_state",
                        "payload": {"full": True, "state": {"agents_md": agents}},
                    },
                    {
                        "type": "turn_context",
                        "payload": {
                            "model": "resolved-model",
                            "permission_profile": profile,
                            "sandbox_policy": {"type": "workspace-write"},
                            **context,
                        },
                    },
                ]

            def run(rollout: list[dict]) -> tuple[str, list[str]]:
                self.write_rollout(home, rollout)
                done = subprocess.CompletedProcess([], 0, stream, "")
                with (
                    mock.patch.object(adapter, "preflight"),
                    mock.patch.object(run_claude, "command", return_value=done),
                ):
                    return adapter.turn("request", workspace)

            self.assertEqual(
                run(records("Fixture rule.\n")),
                ("Finished", [str(workspace / "notes.md")]),
            )
            self.assertEqual(adapter.model, "resolved-model")
            self.assertEqual(adapter.read_measurement, "measured")
            digest = hashlib.sha256(b"Fixture rule.\n").hexdigest()
            self.assertEqual(
                adapter.instruction_observations,
                {str(workspace / "AGENTS.md"): {"sha256": digest, "imports": []}},
            )
            # The inventory rule is a proposed revision: never measured before approval.
            self.assertFalse(run_codex.ROLLOUT_INVENTORY_APPROVED)
            self.assertEqual(adapter.instruction_measurement, "not-measured")
            profile_text = (home / "specflow.config.toml").read_text()
            self.assertIn(f'"{workspace}" = "write"', profile_text)
            self.assertIn('":root" = "deny"', profile_text)
            self.assertIn("ignore_default_excludes = false", profile_text)
            # Codex re-executes its own binary inside the profile to load instructions.
            self.assertIn('"/opt/codex/bin" = "read"\n[permissions', profile_text)
            # A later delta replaces the text; different content is reported.
            changed = records("Fixture rule.\n")
            changed.append(
                {
                    "type": "world_state",
                    "payload": {
                        "full": False,
                        "state": {"agents_md": {"text": "Personal rule."}},
                    },
                }
            )
            run(changed)
            observed = adapter.instruction_observations[str(workspace / "AGENTS.md")]
            self.assertEqual(
                observed["sha256"], hashlib.sha256(b"Personal rule.").hexdigest()
            )
            for context in (
                # Not disabled, yet not the profile the proof covers.
                {"permission_profile": {"type": "managed", "writable": ["/"]}},
                {"permission_profile": {"type": "disabled"}},
                {"sandbox_policy": {"type": "danger-full-access"}},
                {"model": ""},
            ):
                with (
                    self.subTest(context=context),
                    self.assertRaises(run_claude.HostError),
                ):
                    run(records("Fixture rule.\n", **context))
            self.assertEqual(
                run_codex.instruction_evidence(None, workspace, None, b""), ({}, True)
            )
            self.assertEqual(
                run_codex.instruction_evidence(
                    None, workspace, workspace / "AGENTS.md", b"Fixture rule.\n"
                ),
                ({}, False),
            )

    def test_live_probe_needs_host_recorded_policy_denials_and_instructions(
        self,
    ) -> None:
        def host(profile: str = "managed", patch_status: str = "failed"):
            def launch(
                adapter: run_codex.Codex, prompt: str, workspace: Path
            ) -> subprocess.CompletedProcess:
                payload = json.loads((workspace / "probe.json").read_text())
                shell = {
                    name: True
                    for name in score.RELEASE_BOUNDARY_CHECKS
                    if name.startswith("shell-")
                }
                shell.update(
                    {
                        "helper-status": True,
                        "tool-secret-environment-denied": True,
                        "plugin-read": True,
                    }
                )
                items = [
                    {
                        "type": "command_execution",
                        "command": f"bash -lc '{run_claude.PROBE_COMMAND}'",
                        "aggregated_output": json.dumps({payload["report"]: shell}),
                        "status": "completed",
                    },
                    *(
                        {
                            "type": "file_change",
                            "status": patch_status,
                            "changes": [{"path": payload[key], "kind": "add"}],
                        }
                        for key in ("plugin_new", "link_new")
                    ),
                ]
                self.write_rollout(
                    adapter.home,
                    [
                        {"type": "session_meta", "payload": {"cli_version": "9.9.9"}},
                        {
                            "type": "world_state",
                            "payload": {
                                "full": True,
                                "state": {
                                    "agents_md": {
                                        "directory": str(workspace),
                                        "text": (workspace / "AGENTS.md").read_text(),
                                    },
                                    "skills": "specflow:spec-workflow",
                                },
                            },
                        },
                        {
                            "type": "turn_context",
                            "payload": {
                                "model": "resolved-model",
                                "permission_profile": {"type": profile},
                                "sandbox_policy": {"type": "workspace-write"},
                            },
                        },
                    ],
                )
                events = [
                    {"type": "thread.started", "thread_id": "synthetic-thread"},
                    *({"type": "item.completed", "item": item} for item in items),
                ]
                return subprocess.CompletedProcess(
                    [], 0, "\n".join(json.dumps(e) for e in events), ""
                )

            return launch

        def identify(adapter: run_codex.Codex) -> None:
            adapter.root = adapter.plugin.parent.parent
            adapter.version, adapter.configuration_sha256 = "9.9.9", "c" * 64
            adapter.git = Path("/usr/bin/git")

        @contextlib.contextmanager
        def install(adapter: run_codex.Codex, workspace: Path) -> Iterator[None]:
            adapter.home = adapter.root / "control/codex-home"
            adapter.home.mkdir()
            yield

        def failed(proof: dict) -> set[str]:
            return {n for n, c in proof["checks"].items() if c["passed"] is not True}

        with tempfile.TemporaryDirectory() as folder:
            scratch = Path(folder).resolve()
            for options, expected in (
                ({}, set()),
                ({"profile": "disabled"}, {"effective-settings"}),
                (
                    {"patch_status": "completed"},
                    {
                        "native-plugin-write-denied",
                        "native-symlink-write-denied",
                        "effective-settings",
                    },
                ),
            ):
                with (
                    self.subTest(options=options),
                    mock.patch.object(run_codex.Codex, "identify", identify),
                    mock.patch.object(run_codex.Codex, "install", install),
                    mock.patch.object(run_codex.Codex, "launch", host(**options)),
                ):
                    proof = run_codex.live_probe("tested-model", scratch=scratch)
                    self.assertEqual(failed(proof), expected)
                    self.assertEqual(
                        set(proof["checks"]), set(score.RELEASE_BOUNDARY_CHECKS)
                    )
                    self.assertEqual(proof["model"], "resolved-model")
                    self.assertNotIn(str(scratch), json.dumps(proof))
            self.assertEqual(list(scratch.iterdir()), [])

    def test_item_failures_and_invalid_nested_values_are_rejected(self) -> None:
        for item in (
            {"type": "error"},
            {"type": "file_change", "status": "failed"},
            {"type": "file_change", "status": "declined"},
            {"type": "file_change", "status": []},
            None,
        ):
            with self.subTest(item=item):
                self.events[2]["item"] = item
                with self.assertRaises(run_claude.HostError):
                    self.accept()
        self.events[2] = {"type": []}
        with self.assertRaises(run_claude.HostError):
            self.accept()


class CodexHomeTest(unittest.TestCase):
    """Synthetic sign-in and installer; no installed host or real credential used."""

    @staticmethod
    def provision(home: Path) -> None:
        assert list(home.iterdir()) == []
        fd = os.open(home / "auth.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write('{"synthetic": "fixture-only"}')

    def test_unprovisioned_or_nonprivate_sign_in_never_installs(self) -> None:
        for mode in (None, 0o644):
            with (
                self.subTest(mode=mode),
                self.environment() as (workspace, _sign_in, scratch),
            ):

                def provision(home: Path, mode: int | None = mode) -> None:
                    if mode is not None:
                        self.provision(home)
                        (home / "auth.json").chmod(mode)

                with (
                    mock.patch.object(run_claude, "verify_workspace", autospec=True),
                    mock.patch.object(
                        run_claude, "command", autospec=True
                    ) as installer,
                    self.assertRaisesRegex(run_claude.HostError, "independent sign-in"),
                    run_codex.temporary_home(
                        workspace, "0" * 40, scratch=scratch, provision=provision
                    ),
                ):
                    self.fail("invalid credentials must not reach installation")
                installer.assert_not_called()
                self.assertEqual(list(scratch.iterdir()), [])

    @contextlib.contextmanager
    def environment(self) -> Iterator[tuple[Path, Path, Path]]:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            workspace = root / "workspace"
            workspace.mkdir()
            sign_in = root / "auth.json"
            sign_in.write_text('{"synthetic": "fixture-only"}')
            scratch = root / "scratch"
            scratch.mkdir()
            yield workspace, sign_in, scratch

    def test_home_is_private_and_removed_after_success(self) -> None:
        with self.environment() as (workspace, sign_in, scratch):
            before = sign_in.read_bytes()
            observed = []

            def installer(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                home = Path(env["CODEX_HOME"])
                observed.append(home)
                self.assertEqual(cwd, workspace)
                self.assertEqual(home.stat().st_mode & 0o777, 0o700)
                self.assertEqual((home / "auth.json").stat().st_mode & 0o777, 0o600)
                self.assertEqual((home / "auth.json").read_bytes(), before)
                if args[1:3] == ["plugin", "add"]:
                    plugin = home / "plugins/cache/buvis-agent-plugins/specflow/0.1.0"
                    plugin.mkdir(parents=True)
                    (plugin / "plugin.json").write_text('{"name":"specflow"}')
                return subprocess.CompletedProcess(args, 0, "{}", "")

            expected_dir = workspace / "expected"
            expected_dir.mkdir()
            (expected_dir / "plugin.json").write_text('{"name":"specflow"}')
            revision = run_claude.package_revision(expected_dir)
            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=installer, autospec=True
                ),
                run_codex.temporary_home(
                    workspace, revision, scratch=scratch, provision=self.provision
                ) as home,
            ):
                self.assertEqual(len(observed), 2)
                self.assertEqual(list(home.glob("AGENTS*")), [])
                self.assertFalse((home / "config.toml").exists())
            self.assertFalse(home.exists())
            self.assertEqual(list(scratch.iterdir()), [])
            self.assertEqual(sign_in.read_bytes(), before)

    def test_installer_failures_and_interruptions_remove_home(self) -> None:
        for error in (OSError("installer failed"), KeyboardInterrupt()):
            with (
                self.subTest(error=type(error).__name__),
                self.environment() as (workspace, sign_in, scratch),
            ):
                with (
                    mock.patch.object(run_claude, "verify_workspace", autospec=True),
                    mock.patch.object(
                        run_claude, "command", side_effect=error, autospec=True
                    ),
                    self.assertRaises(type(error)),
                    run_codex.temporary_home(
                        workspace, "0" * 40, scratch=scratch, provision=self.provision
                    ),
                ):
                    self.fail("failed install must not yield a home")
                self.assertEqual(list(scratch.iterdir()), [])
                self.assertTrue(sign_in.exists())

    def test_mismatch_removes_home_and_cli_returns_two(self) -> None:
        with self.environment() as (workspace, sign_in, scratch):

            def installer(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                if args[1:3] == ["plugin", "add"]:
                    plugin = (
                        Path(env["CODEX_HOME"])
                        / "plugins/cache/buvis-agent-plugins/specflow/0.1.0"
                    )
                    plugin.mkdir(parents=True)
                    (plugin / "plugin.json").write_text('{"name":"wrong revision"}')
                return subprocess.CompletedProcess(args, 0, "{}", "")

            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=installer, autospec=True
                ),
                self.assertRaisesRegex(run_claude.HostError, "differs"),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                self.fail("mismatched package must not yield a home")
            self.assertEqual(list(scratch.iterdir()), [])
            adapter = run_codex.Codex("tested-model")
            adapter.provision = self.provision
            with (
                mock.patch.object(adapter, "preflight", autospec=True),
                mock.patch.object(run_claude, "initialize_workspace", autospec=True),
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=installer, autospec=True
                ),
                mock.patch.object(
                    run_codex.Path, "home", return_value=sign_in.parent, autospec=True
                ),
            ):
                auth_dir = sign_in.parent / ".codex"
                auth_dir.mkdir()
                (auth_dir / "auth.json").write_bytes(sign_in.read_bytes())
                code = run_claude.run_batch(
                    adapter, "status-summary", scratch / "results"
                )
            self.assertEqual(code, 2)
            record = score.read_json(scratch / "results/codex/status-summary/1.json")
            self.assertIn("differs", record["notRun"])
            self.assertNotIn("scores", record)

    def test_nonzero_installer_never_persists_its_output(self) -> None:
        with self.environment() as (workspace, _sign_in, scratch):
            failure = subprocess.CompletedProcess(
                [], 7, "synthetic-secret", "synthetic-secret"
            )
            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", return_value=failure, autospec=True
                ),
                self.assertRaisesRegex(
                    run_claude.HostError, r"^Codex plugin setup failed \(exit 7\)$"
                ),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                self.fail("failed install must not yield a home")
            self.assertEqual(list(scratch.iterdir()), [])

    def test_body_failure_and_missing_package_remove_home(self) -> None:
        with self.environment() as (workspace, _sign_in, scratch):

            def installer(
                args: list[str], cwd: Path, env: dict | None = None, timeout: int = 600
            ) -> subprocess.CompletedProcess:
                plugin = (
                    Path(env["CODEX_HOME"])
                    / "plugins/cache/buvis-agent-plugins/specflow/0.1.0"
                )
                plugin.mkdir(parents=True, exist_ok=True)
                (plugin / "plugin.json").write_text("{}")
                return subprocess.CompletedProcess(args, 0, "{}", "")

            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude, "command", side_effect=installer, autospec=True
                ),
                mock.patch.object(run_claude, "verify_plugin", autospec=True),
                self.assertRaisesRegex(run_claude.HostError, "turn failed"),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                raise run_claude.HostError("turn failed")
            self.assertEqual(list(scratch.iterdir()), [])
            with (
                mock.patch.object(run_claude, "verify_workspace", autospec=True),
                mock.patch.object(
                    run_claude,
                    "command",
                    return_value=subprocess.CompletedProcess([], 0, "{}", ""),
                    autospec=True,
                ),
                self.assertRaisesRegex(run_claude.HostError, "exactly one"),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                self.fail("missing package must not yield a home")
            self.assertEqual(list(scratch.iterdir()), [])

    def test_unverified_workspace_never_reads_sign_in_or_runs_installer(self) -> None:
        with self.environment() as (workspace, sign_in, scratch):
            sign_in.unlink()
            with (
                mock.patch.object(run_claude, "command", autospec=True) as command,
                self.assertRaisesRegex(run_claude.HostError, "own .git"),
                run_codex.temporary_home(
                    workspace, "0" * 40, scratch=scratch, provision=self.provision
                ),
            ):
                self.fail("unverified workspace must not yield a home")
            command.assert_not_called()
            self.assertEqual(list(scratch.iterdir()), [])

    def test_codex_entry_point_records_blockers_without_setup(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with (
                mock.patch.object(run_codex, "temporary_home", autospec=True) as setup,
                mock.patch.object(run_codex.Codex, "identify", autospec=True),
            ):
                self.assertEqual(
                    run_claude.main(
                        ["status-summary", "--model", "tested-model", "--out", folder],
                        adapter_type=run_codex.Codex,
                    ),
                    2,
                )
            setup.assert_not_called()
            record = score.read_json(Path(folder) / "codex/status-summary/1.json")
            self.assertIn("boundary proof", record["notRun"])
            self.assertFalse(record["releaseEvidence"])


class CodexBoundaryTest(unittest.TestCase):
    def test_instruction_probe_uses_only_rendering_and_cleans_private_state(
        self,
    ) -> None:
        calls = []

        def command(
            args: list[str], cwd: Path, env: dict, timeout: float
        ) -> subprocess.CompletedProcess:
            calls.append(args)
            self.assertFalse((Path(env["CODEX_HOME"]) / "auth.json").exists())
            if "--show-toplevel" in args:
                output = str(cwd)
            elif "--absolute-git-dir" in args:
                output = str(cwd / ".git")
            elif "--version" in args:
                output = (
                    "git version synthetic"
                    if args[0].endswith("/git")
                    else "codex-cli synthetic"
                )
            elif "prompt-input" in args:
                output = json.dumps(
                    [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": (cwd / "AGENTS.md").read_text(),
                                }
                            ],
                        }
                    ]
                )
            else:
                output = ""
            return subprocess.CompletedProcess(
                args, 0, output, "synthetic private diagnostic"
            )

        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(sys, "platform", "darwin"),
            mock.patch.object(
                run_claude, "command", autospec=True, side_effect=command
            ),
        ):
            report = run_codex.boundary_probe(
                Path(sys.executable),
                git_executable=Path("/usr/bin/git"),
                scratch=Path(folder),
                inspect_instructions=True,
            )
            self.assertEqual(list(Path(folder).iterdir()), [])
        self.assertTrue(report["passed"])
        self.assertTrue(report["cleanup"])
        self.assertFalse(report["releaseEvidence"])
        self.assertEqual(report["scope"], "instruction-rendering-only")
        self.assertEqual(report["instructionMeasurement"], "not-measured")
        self.assertNotIn("synthetic private diagnostic", json.dumps(report))
        self.assertFalse(
            any(
                "sandbox" in args or "exec" in args or "login" in args for args in calls
            )
        )

    def test_prompt_render_summary_keeps_text_private_and_inventory_unknown(
        self,
    ) -> None:
        marker = "synthetic-fixture-marker"
        raw = json.dumps(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": marker + " private text"}
                    ],
                }
            ]
        )
        report = run_codex.prompt_summary(raw, marker)
        self.assertTrue(report["fixtureIncluded"])
        self.assertEqual(report["instructionMeasurement"], "not-measured")
        self.assertFalse(report["releaseEvidence"])
        self.assertNotIn("private text", json.dumps(report))
        self.assertFalse(run_codex.prompt_summary("[]", marker)["fixtureIncluded"])
        self.assertFalse(
            run_codex.prompt_summary("not json", marker)["fixtureIncluded"]
        )
        self.assertFalse(
            run_codex.prompt_summary(
                json.dumps({marker: "not an input array"}), marker
            )["fixtureIncluded"]
        )

    def test_probe_allows_only_the_selected_git_executable(self) -> None:
        selected = Path("/synthetic/developer-tools/usr/bin/git")
        policy = run_codex.probe_config(
            {"workspace": "/synthetic/workspace", "plugin": "/synthetic/plugin"},
            git_executable=selected,
        )
        self.assertIn(f'{json.dumps(str(selected))} = "read"', policy)
        self.assertNotIn(f'{json.dumps(str(selected.parent))} = "read"', policy)
        self.assertIn('":root" = "deny"', policy)

    def test_probe_rejects_a_directory_as_git_runtime(self) -> None:
        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(sys, "platform", "darwin"),
            mock.patch.object(run_codex, "prepare_probe", autospec=True) as prepare,
        ):
            selected = Path(folder) / "git"
            selected.mkdir()
            with self.assertRaisesRegex(run_claude.HostError, "executable Git file"):
                run_codex.boundary_probe(Path(sys.executable), git_executable=selected)
            prepare.assert_not_called()

    def test_probe_checks_are_not_satisfied_without_a_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            payload = run_codex.prepare_probe(Path(folder))
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    "-c",
                    run_codex.PROBE_SCRIPT,
                    json.dumps(payload),
                ],
                cwd=payload["workspace"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            checks = json.loads(result.stdout)
            self.assertTrue(checks["workspace-read"])
            self.assertTrue(checks["workspace-write"])
            self.assertTrue(checks["plugin-read"])
            self.assertTrue(checks["helper-status"])
            self.assertFalse(checks["control-read-denied"])
            self.assertFalse(checks["plugin-write-denied"])
            self.assertFalse(checks["symlink-read-denied"])

    def test_missing_sentinel_does_not_count_as_permission_denial(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            payload = run_codex.prepare_probe(Path(folder))
            Path(payload["control"]).unlink()
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    "-c",
                    run_codex.PROBE_SCRIPT,
                    json.dumps(payload),
                ],
                cwd=payload["workspace"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertFalse(json.loads(result.stdout)["control-read-denied"])

    def test_incomplete_probe_report_cannot_pass(self) -> None:
        self.assertFalse(run_codex.probe_passed({"workspace-read": True}))
        complete = dict.fromkeys(run_codex.PROBE_CHECKS, True)
        self.assertTrue(run_codex.probe_passed(complete))
        complete["control-read-denied"] = False
        self.assertFalse(run_codex.probe_passed(complete))

    def test_probe_rejects_inherited_git_state_before_setup(self) -> None:
        with (
            mock.patch.dict(os.environ, {"GIT_DIR": "/synthetic/repository"}),
            mock.patch.object(run_codex, "prepare_probe", autospec=True) as prepare,
            self.assertRaisesRegex(run_claude.HostError, "GIT_"),
        ):
            run_codex.boundary_probe(
                Path("/synthetic/codex"), git_executable=Path("/synthetic/git")
            )
        prepare.assert_not_called()

    def test_probe_keeps_secrets_out_and_cleans_up_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            scratch = Path(folder)
            selected_git = scratch / "git"
            selected_git.write_text("synthetic binary, never executed")
            selected_git.chmod(0o700)
            calls = []

            def command(
                args: list[str], cwd: Path, env: dict, timeout: float
            ) -> subprocess.CompletedProcess:
                calls.append(args)
                self.assertNotIn("OPENAI_API_KEY", env)
                self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", env)
                self.assertFalse((Path(env["CODEX_HOME"]) / "auth.json").exists())
                self.assertEqual(
                    env["PATH"].split(os.pathsep)[0], str(scratch.resolve())
                )
                if "--show-toplevel" in args:
                    output = str(cwd)
                elif "--absolute-git-dir" in args:
                    output = str(cwd / ".git")
                elif "--version" in args:
                    output = (
                        "git version synthetic"
                        if args[0] == str(selected_git.resolve())
                        else "codex-cli synthetic"
                    )
                elif "sandbox" in args:
                    # Installed 0.167.0 rejects this global flag for sandbox.
                    self.assertNotIn("--strict-config", args)
                    self.assertIn("--include-managed-config", args)
                    self.assertEqual(
                        args[args.index("--permission-profile") + 1], "specflow-probe"
                    )
                    self.assertNotIn("macos", args)
                    return subprocess.CompletedProcess(args, 0, "{}", "")
                else:
                    output = ""
                return subprocess.CompletedProcess(args, 0, output, "")

            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "OPENAI_API_KEY": "synthetic",
                        "CLAUDE_CODE_OAUTH_TOKEN": "synthetic",
                    },
                    clear=True,
                ),
                mock.patch.object(sys, "platform", "darwin"),
                mock.patch.object(
                    run_claude, "command", autospec=True, side_effect=command
                ),
            ):
                report = run_codex.boundary_probe(
                    Path(sys.executable), git_executable=selected_git, scratch=scratch
                )
            self.assertFalse(report["passed"])
            self.assertFalse(report["releaseEvidence"])
            self.assertTrue(report["cleanup"])
            self.assertEqual(list(scratch.iterdir()), [selected_git])
            self.assertIn("<batch>", report["generatedPolicy"])
            self.assertNotIn(str(scratch), json.dumps(report))
            self.assertEqual(sum("sandbox" in args for args in calls), 1)

    def test_probe_cleans_up_on_interruption(self) -> None:
        with (
            tempfile.TemporaryDirectory() as folder,
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(sys, "platform", "darwin"),
            mock.patch.object(
                run_claude, "command", autospec=True, side_effect=KeyboardInterrupt
            ),
            self.assertRaises(KeyboardInterrupt),
        ):
            scratch = Path(folder)
            try:
                run_codex.boundary_probe(
                    Path(sys.executable),
                    git_executable=Path("/usr/bin/git"),
                    scratch=scratch,
                )
            finally:
                self.assertEqual(list(scratch.iterdir()), [])

    def test_probe_rejects_ancestor_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)
            (parent / "AGENTS.md").write_text("Synthetic ancestor instructions")
            with self.assertRaisesRegex(run_claude.HostError, "ancestor"):
                run_codex.prepare_probe(parent / "batch")

    def test_probe_rejects_broad_python_runtime(self) -> None:
        with (
            mock.patch.object(sys, "base_prefix", "/"),
            self.assertRaisesRegex(run_claude.HostError, "too broad"),
        ):
            run_codex.probe_config(
                {"workspace": "/synthetic/workspace", "plugin": "/synthetic/plugin"},
                git_executable=Path("/synthetic/git"),
            )


class KiroAdapterTest(unittest.TestCase):
    """Synthetic stream-json only; no host, sign-in, or policy proof."""

    SERVER = '[INFO] kas.server.starting {"product":"KAS","version":"0.1.2"}\n'

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name).resolve()
        self.workspace = self.root / "workspaces/session"
        for name in ("control", "resources/specflow", "workspaces/session/.kiro"):
            (self.root / name).mkdir(parents=True)
        run_claude.write_files(
            self.workspace,
            {
                "AGENTS.md": "Fixture rule.\n",
                ".kiro/steering/rule.md": "Steering rule.\n",
                "notes.md": "Notes.\n",
            },
        )
        self.adapter = run_kiro.Kiro("requested-model")
        self.adapter.cli = "kiro-cli 9.9.9"
        self.adapter.plugin = self.root / "resources/specflow"

    @staticmethod
    def update(**update: object) -> dict:
        return {
            "type": "sessionUpdate",
            "data": {"sessionId": "sess_one", "update": update},
        }

    def call(self, name: str, kind: str, status: str, **details: object) -> list[dict]:
        """A tool call and its final update; details: path, command, output."""
        raw = {k: v for k, v in details.items() if k in ("path", "command")}
        first = {"toolCallId": name, "kind": kind, "rawInput": raw}
        if "path" in details:
            first["locations"] = [{"path": details["path"]}]
        return [
            self.update(sessionUpdate="tool_call", **first),
            self.update(
                sessionUpdate="tool_call_update",
                toolCallId=name,
                status=status,
                rawOutput=details.get("output", {}),
            ),
        ]

    def context(self, *uris: str) -> dict:
        items = [{"uri": uri, "matched": True} for uri in uris]
        items.append({"uri": ".kiro/steering/**/*.md", "matched": False})
        usage = {
            "kind": "context_usage",
            "breakdown": {"contextFiles": {"items": items}},
        }
        return self.update(sessionUpdate="session_info_update", _meta={"kiro": usage})

    def events(
        self,
        *extra: dict,
        workspace: Path | None = None,
        model: str | None = "resolved-model",
        steering: bool = True,
        sandbox: str = "active",
    ) -> list[dict]:
        workspace = workspace or self.workspace
        loaded = [
            f"file://{workspace}/AGENTS.md",
            f"file://{workspace}/.kiro/steering/rule.md",
        ]
        inclusion = {"kind": "steering_inclusion", "steeringDocuments": loaded}
        models = ["auto", *([model] if model else [])]
        skill = {
            "name": "spec-workflow",
            "_meta": {
                "kiro": {
                    "type": "skill",
                    "resource": {
                        "source": {"origin": "power", "power": {"name": "specflow"}}
                    },
                }
            },
        }
        return [
            {"type": "runStarted", "data": {"payloadSchema": "acp", "engine": "v3"}},
            {
                "type": "sandboxStatus",
                "data": {
                    "sessionId": "sess_one",
                    "status": sandbox,
                    "backend": "seatbelt",
                    "networkMode": "default_blocked",
                },
            },
            self.update(availableCommands=[skill]),
            *(
                self.update(
                    configOptions=[{"id": "mode"}, {"id": "model", "currentValue": m}]
                )
                for m in models
                if model
            ),
            *(
                [
                    self.update(
                        sessionUpdate="session_info_update", _meta={"kiro": inclusion}
                    )
                ]
                if steering
                else []
            ),
            *extra,
            {
                "type": "runFinished",
                "data": {
                    "sessionId": "sess_one",
                    "status": "success",
                    "finalText": "Finished",
                    "finalTextTruncated": False,
                },
            },
        ]

    def accept(
        self,
        events: list[dict] | str,
        *,
        stderr: str = SERVER,
        code: int = 0,
        hashes: dict[str, str] | None = None,
    ) -> tuple[str, list[str]]:
        stdout = (
            events
            if isinstance(events, str)
            else "\n".join(json.dumps(e) for e in events)
        )
        if hashes is None:
            hashes = run_kiro.instruction_hashes(self.workspace, self.adapter.plugin)
        return self.adapter.accept_turn(
            subprocess.CompletedProcess([], code, stdout, stderr),
            self.workspace,
            hashes,
        )

    def test_turn_reports_identity_reads_and_pre_launch_instruction_hashes(
        self,
    ) -> None:
        hashes = run_kiro.instruction_hashes(self.workspace, self.adapter.plugin)
        # A later edit must not change what the turn is said to have loaded.
        (self.workspace / "AGENTS.md").write_text("Edited after launch.\n")
        events = self.events(
            *self.call("r", "read", "completed", path=str(self.workspace / "notes.md")),
            *self.call(
                "s",
                "execute",
                "failed",
                command="cat AGENTS.md",
                output={"exitCode": 1},
            ),
            *self.call("w", "edit", "completed", path=str(self.workspace / "new.md")),
            self.context("/elsewhere/personal.md"),
        )
        self.assertEqual(
            self.accept(events, hashes=hashes),
            (
                "Finished",
                [str(self.workspace / "notes.md"), str(self.workspace / "AGENTS.md")],
            ),
        )
        self.assertEqual(self.adapter.conversation, "sess_one")
        self.assertEqual(self.adapter.model, "resolved-model")
        self.assertEqual(self.adapter.version, "kiro-cli 9.9.9; KAS 0.1.2")
        self.assertEqual(self.adapter.host, "kiro-ide")
        self.assertEqual(self.adapter.read_measurement, "measured")
        self.assertEqual(self.adapter.instruction_measurement, "measured")
        digest = hashlib.sha256(b"Fixture rule.\n").hexdigest()
        self.assertEqual(
            self.adapter.instruction_observations,
            {
                str(self.workspace / "AGENTS.md"): {"sha256": digest, "imports": []},
                str(self.workspace / ".kiro/steering/rule.md"): {
                    "sha256": hashlib.sha256(b"Steering rule.\n").hexdigest(),
                    "imports": [],
                },
                # Not in the pre-launch snapshot: reported, never given a hash.
                "/elsewhere/personal.md": {"sha256": None, "imports": []},
            },
        )

    def test_turn_without_steering_telemetry_is_not_measured(self) -> None:
        events = self.events(
            self.context(str(self.workspace / "AGENTS.md")), steering=False
        )
        self.accept(events)
        # The context list is a proposed inventory: reported, not yet trusted.
        self.assertFalse(run_kiro.CONTEXT_INVENTORY_APPROVED)
        self.assertEqual(self.adapter.instruction_measurement, "not-measured")
        self.assertEqual(
            list(self.adapter.instruction_observations),
            [str(self.workspace / "AGENTS.md")],
        )

    def test_unnameable_reads_leave_reads_unmeasured(self) -> None:
        for call in (
            self.call("s", "execute", "completed", command="grep -r rule ."),
            self.call("x", "search", "completed", path=str(self.workspace)),
            self.call("d", "read", "completed", path=str(self.workspace)),
        ):
            with self.subTest(call=call[0]["data"]["update"]["kind"]):
                self.adapter.new_conversation()
                self.accept(self.events(*call))
                self.assertEqual(self.adapter.read_measurement, "not-measured")

    def test_failed_or_unproven_turn_never_advances_state(self) -> None:
        good = self.events()
        blocked = {"message": run_kiro.DENIAL + " (deny fs_read)"}
        lost = {"output": "sandbox-exec: sandbox_apply: Operation not permitted\n"}
        finished = dict(good[-1]["data"])
        cases = {
            "nonzero exit": {"events": good, "code": 1},
            "invalid JSON": {"events": "private diagnostic {"},
            "no final event": {"events": good[:-1]},
            "run error": {
                "events": [*good[:-1], {"type": "runError", "data": {}}, good[-1]]
            },
            "failed status": {
                "events": [
                    *good[:-1],
                    {"type": "runFinished", "data": {**finished, "status": "error"}},
                ]
            },
            "truncated reply": {
                "events": [
                    *good[:-1],
                    {
                        "type": "runFinished",
                        "data": {**finished, "finalTextTruncated": True},
                    },
                ]
            },
            "automatic model": {"events": self.events(model="auto")},
            "missing model": {"events": self.events(model=None)},
            "missing server version": {"events": good, "stderr": ""},
            "sandbox unavailable": {"events": self.events(sandbox="unavailable")},
            "sandbox not reported": {"events": [good[0], *good[2:]]},
            "sandbox warning": {
                "events": good,
                "stderr": self.SERVER + "[WARN] sandbox.unavailable private\n",
            },
            "sandbox could not start": {
                "events": self.events(
                    *self.call(
                        "s",
                        "execute",
                        "failed",
                        command="true",
                        output={**lost, "exitCode": 71},
                    )
                )
            },
            "denied read": {
                "events": self.events(
                    *self.call("r", "read", "failed", path="/private", output=blocked)
                )
            },
            "denied shell": {
                "events": self.events(
                    *self.call("s", "execute", "failed", command="ls", output=blocked)
                )
            },
            "unfinished call": {
                "events": self.events(
                    *self.call("s", "execute", "in_progress", command="sleep 9")
                )
            },
            "invalid inventory": {
                "events": self.events(
                    self.update(
                        _meta={
                            "kiro": {
                                "kind": "steering_inclusion",
                                "steeringDocuments": [None],
                            }
                        }
                    )
                )
            },
        }
        for label, case in cases.items():
            with self.subTest(case=label):
                with self.assertRaises(run_claude.HostError) as caught:
                    self.accept(
                        case["events"],
                        stderr=case.get("stderr", self.SERVER),
                        code=case.get("code", 0),
                    )
                self.assertNotIn("private", str(caught.exception))
                self.assertIsNone(self.adapter.conversation)
                self.assertEqual(self.adapter.version, "not-started")
                self.assertEqual(self.adapter.model, "requested-model")

    def test_resume_requires_same_session_and_server_version(self) -> None:
        self.accept(self.events())
        self.assertIn("--resume-id", self.adapter.arguments("next"))
        self.assertNotIn("--resume-id", self.adapter.arguments("next", template=True))
        other = json.loads(json.dumps(self.events()).replace("sess_one", "sess_two"))
        with self.assertRaises(run_claude.HostError):
            self.accept(other)
        with self.assertRaises(run_claude.HostError):
            self.accept(self.events(), stderr=self.SERVER.replace("0.1.2", "0.1.3"))
        self.assertEqual(self.adapter.conversation, "sess_one")
        self.assertEqual(self.adapter.version, "kiro-cli 9.9.9; KAS 0.1.2")
        self.adapter.new_conversation()
        self.accept(other)
        self.assertEqual(self.adapter.conversation, "sess_two")

    def test_generated_policy_denies_private_paths_and_power_writes(self) -> None:
        home = self.root / "control/kiro-home"
        power = home / "powers/installed/specflow"
        power.mkdir(parents=True)
        (self.root / "control/sentinel.txt").write_text("private")
        (home / "sessions").mkdir()
        other = self.root / "workspaces/other"
        other.mkdir(exist_ok=True)
        alias = home / "powers/installed/latest"
        alias.symlink_to(power)
        agent = run_kiro.kiro_agent(self.root, self.workspace, power)
        self.assertEqual(agent["tools"], ["read", "write", "shell"])
        self.assertEqual(agent["resources"], run_kiro.RESOURCES)
        self.assertIs(agent["includeMcpJson"], False)
        self.assertEqual(agent["mcpServers"], {})
        self.assertIs(agent["includePowers"], True)
        rules = agent["permissions"]["rules"]

        def matching(capability: str, effect: str) -> list[dict]:
            return [
                r
                for r in rules
                if r["capability"] == capability and r["effect"] == effect
            ]

        (read_deny,) = matching("fs_read", "deny")
        # The sandbox ignores `exclude`: a deny names the private entries beside
        # a readable path, never a folder that holds one.
        for path in (
            self.root / "home",
            self.root / "control/sentinel.txt",
            home / "sessions",
            other,
        ):
            self.assertIn(str(path), read_deny["match"])
        runtime = Path(sys.base_prefix).resolve()
        for kept in (self.workspace, power, runtime):
            for denied in read_deny["match"]:
                self.assertFalse(
                    kept == Path(denied) or kept.is_relative_to(denied),
                    f"{denied} hides {kept}",
                )
        # A denied link would hide the readable folder it points at.
        self.assertNotIn(str(alias), read_deny["match"])
        self.assertNotIn("exclude", read_deny)
        (write_allow,) = matching("fs_write", "allow")
        self.assertEqual(write_allow["match"], [str(self.workspace)])
        write_deny, configuration = matching("fs_write", "deny")
        # The Power sits below control and is not excepted from the write denial.
        self.assertIn(str(self.root / "control"), write_deny["match"])
        self.assertIn(str(self.root / "resources"), write_deny["match"])
        self.assertIn(str(other), write_deny["match"])
        self.assertNotIn(str(self.root / "workspaces"), write_deny["match"])
        # The digest form does not depend on which entries exist today.
        stable = run_kiro.kiro_agent(self.root, self.workspace, power, expand=False)
        self.assertNotIn(str(other), json.dumps(stable))
        self.assertIn(str(self.workspace / ".kiro/agents"), configuration["match"])
        self.assertEqual(
            {r["capability"] for r in rules if r["effect"] == "allow"},
            {"fs_read", "fs_write", "shell", "skill", "power"},
        )
        self.assertEqual(
            matching("mcp", "deny"), [{"capability": "mcp", "effect": "deny"}]
        )
        self.assertEqual(
            run_kiro.SANDBOX,
            {
                "enabled": True,
                "networkAccess": "DEFAULT_BLOCKED",
                "mcpSandboxing": True,
            },
        )
        home.mkdir(mode=0o700, exist_ok=True)
        run_kiro.write_configuration(home, self.root, self.workspace, power)
        for name in ("agents/specflow-eval.json", "settings/sandbox.json"):
            self.assertEqual((home / name).stat().st_mode & 0o777, 0o600)
        self.assertEqual(score.read_json(home / "agents/specflow-eval.json"), agent)
        self.assertEqual(
            score.read_json(home / "settings/sandbox.json"), run_kiro.SANDBOX
        )

    def test_launch_refuses_missing_batch_and_workspace_host_configuration(
        self,
    ) -> None:
        with (
            mock.patch.object(run_claude, "command") as command,
            self.assertRaisesRegex(run_claude.HostError, "not started"),
        ):
            self.adapter.turn("request", self.workspace)
        self.adapter.root = self.root
        self.adapter.home = self.root / "control/kiro-home"
        self.adapter.home.mkdir()
        (self.workspace / ".kiro/agents").mkdir()
        with (
            mock.patch.object(run_claude, "command") as command,
            self.assertRaisesRegex(run_claude.HostError, "Kiro configuration"),
        ):
            self.adapter.launch("request", self.workspace)
        (self.workspace / ".kiro/agents").rmdir()
        with (
            mock.patch.object(run_claude, "command") as command,
            self.assertRaisesRegex(run_claude.HostError, "inheritance setting"),
        ):
            self.adapter.launch("request", self.workspace)
        command.assert_not_called()

    def proof(self, **changes: object) -> dict:
        return {
            "scope": "installed-host-boundary",
            "host": "kiro-ide",
            "hostVersion": "kiro-cli 9.9.9; KAS 0.1.2",
            "configurationSha256": self.adapter.configuration_sha256,
            "runtimeRevision": score.git("rev-parse", "HEAD:plugins/specflow")
            .decode()
            .strip(),
            "runnerSha256": run_claude.runner_digest(self.adapter),
            "checks": {
                name: {"passed": True, "evidence": "synthetic"}
                for name in score.RELEASE_BOUNDARY_CHECKS
            },
            **changes,
        }

    def test_preflight_stays_blocked_without_a_matching_proof(self) -> None:
        version = subprocess.CompletedProcess([], 0, "kiro-cli 9.9.9\n", "")
        with (
            mock.patch.object(run_kiro.shutil, "which", return_value="/synthetic/kiro"),
            mock.patch.object(run_claude, "command", return_value=version),
        ):
            with self.assertRaisesRegex(run_claude.HostError, "launch blocked"):
                self.adapter.preflight()
            self.assertEqual(self.adapter.version, "kiro-cli 9.9.9")
            digest = self.adapter.configuration_sha256
            for changes in (
                {"hostVersion": "kiro-cli 1.0.0; KAS 0.1.2"},
                {"hostVersion": "kiro-cli 9.9.9"},
                {"configurationSha256": "0" * 64},
                {"runnerSha256": "0" * 64},
                {"checks": {}},
            ):
                with (
                    self.subTest(changes=changes),
                    self.assertRaisesRegex(run_claude.HostError, "launch blocked"),
                ):
                    self.adapter.boundary = self.proof(**changes)
                    self.adapter.preflight()
            self.adapter.boundary = self.proof()
            self.adapter.preflight()
            # The proven server version is adopted until a turn reports its own.
            self.assertEqual(self.adapter.version, "kiro-cli 9.9.9; KAS 0.1.2")
            self.assertIsNotNone(self.adapter.boundary_sha256)
            with self.assertRaisesRegex(run_claude.HostError, "proven"):
                self.accept(self.events(), stderr=self.SERVER.replace("0.1.2", "0.1.3"))
            self.accept(self.events())
            self.adapter.model = "another-model"
            self.adapter.preflight()
            self.assertEqual(self.adapter.configuration_sha256, digest)

    def test_install_verifies_setting_power_tree_sign_in_and_clean_home(self) -> None:
        def host(signed_in: int = 0, extra: str | None = None):
            def run(adapter: run_kiro.Kiro, *args: str) -> subprocess.CompletedProcess:
                code = 0
                if args[0] == "settings":
                    score.write_json(
                        adapter.home / "settings/cli.json", {args[1]: True}
                    )
                elif args[0] == "powers":
                    target = adapter.home / "powers/installed/specflow"
                    run_kiro.shutil.copytree(args[2], target)
                    if extra:
                        (adapter.home / extra).parent.mkdir(exist_ok=True)
                        (adapter.home / extra).write_text("Synthetic.\n")
                elif args[0] == "whoami":
                    code = signed_in
                return subprocess.CompletedProcess([], code, "private account", "")

            return run

        def install(**options: object) -> Path:
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder).resolve()
                (root / "control").mkdir()
                seed = root / "workspaces/seed"
                seed.mkdir(parents=True)
                source = root / "resources/specflow"
                run_kiro.shutil.copytree(score.PLUGIN, source)
                adapter = run_kiro.Kiro("requested-model")
                adapter.plugin = source
                with mock.patch.object(run_kiro.Kiro, "run", host(**options)):
                    with adapter.install(seed):
                        home = adapter.home
                        self.assertEqual(home.stat().st_mode & 0o777, 0o700)
                        self.assertEqual(
                            adapter.plugin, home / "powers/installed/specflow"
                        )
                        self.assertTrue((home / "agents/specflow-eval.json").is_file())
                        self.assertEqual(adapter.environment()["KIRO_HOME"], str(home))
                        self.assertNotIn(
                            "TOKEN=", json.dumps(sorted(adapter.environment()))
                        )
                    self.assertIsNone(adapter.home)
                    self.assertEqual(adapter.plugin, source)
                return root

        install()
        for options, message in (
            ({"signed_in": 1}, "not signed in"),
            ({"extra": "powers/installed/specflow/added.md"}, "differs"),
            ({"extra": "steering/personal.md"}, "global Kiro instructions"),
            ({"extra": "AGENTS.md"}, "global Kiro instructions"),
        ):
            with (
                self.subTest(options=options),
                self.assertRaisesRegex(run_claude.HostError, message) as caught,
            ):
                install(**options)
            self.assertNotIn("private account", str(caught.exception))

    def test_live_probe_needs_host_denials_sandbox_and_instructions(self) -> None:
        def host(**options: object):
            write_status = options.pop("write_status", "failed")

            def launch(
                adapter: run_kiro.Kiro, prompt: str, workspace: Path
            ) -> subprocess.CompletedProcess:
                payload = json.loads((workspace / "probe.json").read_text())
                shell = {
                    name: True
                    for name in score.RELEASE_BOUNDARY_CHECKS
                    if name.startswith("shell-")
                }
                for name in (
                    "helper-status",
                    "tool-secret-environment-denied",
                    "plugin-read",
                ):
                    shell[name] = True
                calls = self.call(
                    "shell",
                    "execute",
                    "completed",
                    command=run_kiro.PROBE_COMMAND,
                    output={"output": json.dumps({payload["report"]: shell})},
                )
                for name, (kind, key) in run_kiro.NATIVE_PROBES.items():
                    allowed = name == "plugin-read" or (
                        kind == "edit" and write_status == "completed"
                    )
                    calls += self.call(
                        name,
                        kind,
                        "completed" if allowed else "failed",
                        path=payload[key],
                        output={} if allowed else {"message": run_kiro.DENIAL + " (x)"},
                    )
                events = self.events(*calls, workspace=workspace, **options)
                return subprocess.CompletedProcess(
                    [], 0, "\n".join(json.dumps(e) for e in events), self.SERVER
                )

            return launch

        def identify(adapter: run_kiro.Kiro) -> None:
            adapter.root = adapter.plugin.parent.parent
            adapter.cli = adapter.version = "kiro-cli 9.9.9"
            adapter.configuration_sha256 = "c" * 64

        @contextlib.contextmanager
        def install(adapter: run_kiro.Kiro, workspace: Path) -> Iterator[None]:
            adapter.home = adapter.root / "control/kiro-home"
            adapter.home.mkdir()
            yield

        def failed(proof: dict) -> set[str]:
            return {n for n, c in proof["checks"].items() if c["passed"] is not True}

        writes = {"native-plugin-write-denied", "native-symlink-write-denied"}
        with tempfile.TemporaryDirectory() as folder:
            scratch = Path(folder).resolve()
            for options, expected in (
                ({}, set()),
                ({"sandbox": "unavailable"}, {"effective-settings"}),
                ({"write_status": "completed"}, {*writes, "effective-settings"}),
                (
                    {"steering": False},
                    {"instruction-inventory", "fixture-instructions"},
                ),
            ):
                with (
                    self.subTest(options=options),
                    mock.patch.object(run_kiro.Kiro, "identify", identify),
                    mock.patch.object(run_kiro.Kiro, "install", install),
                    mock.patch.object(run_kiro.Kiro, "launch", host(**options)),
                ):
                    proof = run_kiro.live_probe("tested-model", scratch=scratch)
                    self.assertEqual(failed(proof), expected)
                    self.assertEqual(
                        set(proof["checks"]), set(score.RELEASE_BOUNDARY_CHECKS)
                    )
                    self.assertEqual(proof["host"], "kiro-ide")
                    self.assertEqual(proof["model"], "resolved-model")
                    self.assertEqual(proof["hostVersion"], "kiro-cli 9.9.9; KAS 0.1.2")
                    self.assertNotIn(str(scratch), json.dumps(proof))
            self.assertEqual(list(scratch.iterdir()), [])


if __name__ == "__main__":
    unittest.main()

"""Frozen source inventory and destination assignments remain usable offline."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from test_contract import ROOT, load


TOOLS = ROOT / "tools" / "autopilot"
PIN = "e960ef1cc43e72bf92593b2f16c7a37c71ea7e48"
INVENTORY_SHA256 = "f55c98bba2b4b3c94ce588b6c616258186dd0bb2164800b2d34271acc25dfb5d"


class OfflineProvenanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pin = load(TOOLS / "source-pin.json")
        cls.inventory = load(TOOLS / "source-inventory.json")
        cls.mapping = load(TOOLS / "source-map.json")

    def test_pin_identifies_exact_repository_commit_and_date_without_checkout_path(self) -> None:
        self.assertEqual(self.pin, {
            "schema_version": 1,
            "source_repository": "https://github.com/buvis/claude-autopilot",
            "commit": PIN,
            "pinned_at": "2026-10-24",
        })
        for document in (self.inventory, self.mapping):
            self.assertEqual(document["schema_version"], 1)
            self.assertEqual(document["source_commit"], PIN)
        self.assertEqual(self.inventory["source_repository"], self.pin["source_repository"])
        inventory_bytes = (TOOLS / "source-inventory.json").read_bytes()
        self.assertEqual(hashlib.sha256(inventory_bytes).hexdigest(), INVENTORY_SHA256)
        self.assertEqual(self.mapping["source_inventory_sha256"], INVENTORY_SHA256)

    def test_inventory_covers_all_expanded_principal_configuration_and_code_ids_exactly(self) -> None:
        inventory = self.inventory
        groups = ("expanded_inventory_ids", "principal_inventory_ids",
                  "configuration_field_ids", "code_only_ids")
        expected = set()
        for name, count in zip(groups, (1034, 42, 302, 3)):
            with self.subTest(group=name):
                ids = inventory[name]
                self.assertEqual(len(ids), count)
                self.assertEqual(len(set(ids)), len(ids))
                self.assertFalse(expected.intersection(ids))
                expected.update(ids)
        principal = {f"P{n:02d}" for n in range(1, 12)}
        principal.update(f"R{n:02d}" for n in range(1, 32))
        self.assertEqual(set(inventory["principal_inventory_ids"]), principal)
        self.assertEqual(set(inventory["code_only_ids"]), {"CODE-R28", "CODE-R29", "CODE-R31"})
        self.assertEqual(set(inventory["expected_behavior_ids"]), expected)
        self.assertEqual(len(inventory["expected_behavior_ids"]), len(expected))
        ids = [row["source_behavior_id"] for row in inventory["behaviors"]]
        self.assertEqual(set(ids), expected)
        self.assertEqual(len(ids), len(expected))
        mapped = [row["source_behavior_id"] for row in self.mapping["behaviors"]]
        self.assertEqual(set(mapped), expected)
        self.assertEqual(len(mapped), len(expected))
        for category, count in (("expanded", 1034), ("principal", 42)):
            basis = inventory["inventory_basis"][category]
            self.assertEqual(basis["count"], count)
            self.assertRegex(basis["sha256"], r"^[0-9a-f]{64}$")
            self.assertFalse(PurePosixPath(basis["path"]).is_absolute())

    def test_all_source_files_assets_and_section_digests_remain_cross_linked(self) -> None:
        files = {row["source_path"]: row for row in self.inventory["source_files"]}
        self.assertEqual(len(files), 679)
        self.assertEqual(len(files), len(self.inventory["source_files"]))
        for path, row in files.items():
            with self.subTest(source=path):
                self.assertFalse(PurePosixPath(path).is_absolute())
                self.assertNotIn("..", PurePosixPath(path).parts)
                self.assertRegex(row["git_blob_id"], r"^[0-9a-f]{40}$")
                self.assertRegex(row["blob_sha256"], r"^[0-9a-f]{64}$")
                self.assertGreaterEqual(row["size_bytes"], 0)
        assets = self.inventory["assets"]
        ids = [row["source_asset_id"] for row in assets]
        self.assertEqual(len(ids), 92)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(set(ids), set(self.inventory["required_asset_ids"]))
        self.assertEqual(len(self.inventory["required_asset_ids"]), len(ids))
        for row in assets:
            with self.subTest(asset=row["source_asset_id"]):
                source = files[row["source_path"]]
                for field in ("git_blob_id", "blob_sha256"):
                    self.assertEqual(row[field], source[field])
                anchors = [section["anchor"] for section in row["sections"]]
                self.assertEqual(len(anchors), len(set(anchors)))
                for section in row["sections"]:
                    self.assertRegex(section["sha256"], r"^[0-9a-f]{64}$")
                    self.assertGreaterEqual(section["start_line"], 1)
                    self.assertGreaterEqual(section["end_line"], section["start_line"])

    def test_asset_assignments_cover_exact_source_ids_sections_and_adaptation_reasons(self) -> None:
        sources = {row["source_asset_id"]: row for row in self.inventory["assets"]}
        mapped = [row for row in self.mapping["assets"] if row["source_asset_id"] is not None]
        ids = [row["source_asset_id"] for row in mapped]
        self.assertEqual(set(ids), set(sources))
        self.assertEqual(len(ids), len(sources))
        for row in mapped:
            with self.subTest(asset=row["source_asset_id"]):
                source = sources[row["source_asset_id"]]
                self.assertEqual(row["source_blob_sha256"], source["blob_sha256"])
                path = PurePosixPath(row["destination_path"])
                self.assertEqual(path.parts[:2], ("plugins", "autopilot"))
                self.assertNotIn("..", path.parts)
                self.assertTrue(row["adaptation_reason"].strip())
                planned = row["section_plan"]
                expected = {s["anchor"]: s["sha256"] for s in source["sections"]}
                actual = {s["source_anchor"]: s["source_sha256"] for s in planned}
                self.assertEqual(actual, expected)
                self.assertEqual(len(planned), len(expected))
                for section in planned:
                    self.assertTrue(section["action"].strip())
                    self.assertTrue(section["reason"].strip())
                if row["disposition"] == "preserved":
                    self.assertEqual(row["destination_blob_sha256"], source["blob_sha256"])
                if row["disposition"] == "planned":
                    self.assertIn(row["planned_disposition"], {"preserved", "adapted", "gated"})
                self.assertTrue(row["acceptance_cases"])
                for case in row["acceptance_cases"]:
                    self.assertTrue(case["case_id"].strip())
                    self.assertTrue(case["expected_outcome"].strip())

    def test_every_behavior_has_pinned_anchors_explicit_owner_profiles_and_observable_scenarios(self) -> None:
        sources = {row["source_behavior_id"]: row for row in self.inventory["behaviors"]}
        bindings = {row["owner_repository"]: row for row in self.mapping["owner_bindings"]}
        self.assertEqual(set(bindings), {"buvis/agent-plugins", "buvis/ovcaq", "buvis/lantern"})
        self.assertEqual(len(bindings), len(self.mapping["owner_bindings"]))
        for owner in ("buvis/ovcaq", "buvis/lantern"):
            self.assertEqual(bindings[owner]["verified_local_project"], owner)
            self.assertRegex(bindings[owner]["basis_sha256"], r"^[0-9a-f]{64}$")
        for row in self.mapping["behaviors"]:
            with self.subTest(behavior=row["source_behavior_id"]):
                source = sources[row["source_behavior_id"]]
                self.assertEqual(row["source_anchors"], source["source_anchors"])
                self.assertTrue(row["source_anchors"])
                if "classification" in source:
                    self.assertEqual(row["classification"], source["classification"])
                self.assertIn(row["classification"], {"port", "redesign"})
                self.assertTrue(row["reason"].strip())
                self.assertIn(row["owner_repository"], bindings)
                self.assertRegex(row["delivery_prd"], r"^[0-9]{5}$")
                self.assertTrue(row["destination_procedure"].strip())
                self.assertTrue(row["destination_operation"].strip())
                profiles = row["required_profiles"]
                self.assertTrue(profiles)
                self.assertEqual(len(profiles), len(set(profiles)))
                self.assertEqual(set(profiles), set(row["evidence"]["profile_evidence"]))
                self.assertTrue(row["acceptance_cases"])
                for case in row["acceptance_cases"]:
                    self.assertTrue(case["case_id"].strip())
                    self.assertTrue(case["exercise"].strip())
                    self.assertTrue(case["expected_outcome"].strip())
                for related in row.get("related_deliveries", []):
                    self.assertIn(related["owner_repository"], bindings)
                    self.assertRegex(related["delivery_prd"], r"^[0-9]{5}$")
                    self.assertTrue(related["operation"].strip())

    def test_regressions_keep_exact_identity_source_digests_and_equivalent_target_scenarios(self) -> None:
        sources = {row["source_regression_id"]: row for row in self.inventory["regression_cases"]}
        self.assertEqual(len(sources), 4950)
        self.assertEqual(len(sources), len(self.inventory["regression_cases"]))
        self.assertEqual(set(sources), set(self.inventory["source_regression_ids"]))
        self.assertEqual(len(sources), len(self.inventory["source_regression_ids"]))
        mapped = self.mapping["regression_cases"]
        self.assertEqual({row["source_regression_id"] for row in mapped}, set(sources))
        self.assertEqual(len(mapped), len(sources))
        files = {row["source_path"]: row for row in self.inventory["source_files"]}
        owners = {row["owner_repository"] for row in self.mapping["owner_bindings"]}
        for row in mapped:
            with self.subTest(regression=row["source_regression_id"]):
                source = sources[row["source_regression_id"]]
                for field in ("source_path", "test_identity", "source_blob_sha256", "case_sha256"):
                    self.assertEqual(row[field], source[field])
                file = files[source["source_path"]]
                self.assertEqual(source["source_blob_sha256"], file["blob_sha256"])
                self.assertEqual(source["git_blob_id"], file["git_blob_id"])
                self.assertRegex(source["case_sha256"], r"^[0-9a-f]{64}$")
                if source["test_identity"] == "script-or-module":
                    self.assertEqual(source["case_sha256"], file["blob_sha256"])
                else:
                    self.assertGreaterEqual(source["start_line"], 1)
                    self.assertGreaterEqual(source["end_line"], source["start_line"])
                self.assertIn(row["disposition"], {"retained", "replaced", "obsolete"})
                self.assertIn(row["owner_repository"], owners)
                self.assertRegex(row["delivery_prd"], r"^[0-9]{5}$")
                self.assertTrue(row["expected_outcome"].strip())
                if row["disposition"] == "replaced":
                    self.assertTrue(row["equivalent_target_scenario"].strip())
                if row["disposition"] == "obsolete":
                    self.assertEqual(row["evidence"]["status"], "passed")

    def test_planned_assignments_cannot_claim_unattributed_passed_evidence(self) -> None:
        rows = self.mapping["behaviors"] + self.mapping["regression_cases"]
        for row in rows:
            identity = row.get("source_behavior_id", row.get("source_regression_id"))
            evidence = row["evidence"]
            receipts = [evidence, *evidence["profile_evidence"].values()]
            for receipt in receipts:
                with self.subTest(identity=identity, status=receipt["status"]):
                    self.assertIn(receipt["status"], {"planned", "unavailable", "failed", "passed"})
                    if receipt["status"] == "passed":
                        self.assertTrue(receipt["artifact_id"])
                        self.assertRegex(receipt["artifact_sha256"], r"^[0-9a-f]{64}$")
                        self.assertTrue(receipt["tested_package_revision"])
            if evidence["status"] == "passed":
                self.assertTrue(evidence["profile_evidence"])
                self.assertTrue(all(r["status"] == "passed"
                                    for r in evidence["profile_evidence"].values()))

    def test_resource_edges_declare_packaged_external_or_informational_obligations(self) -> None:
        kinds = {"packaged-resource", "external-capability", "informational-provenance"}
        self.assertEqual({row["kind"] for row in self.mapping["resource_edges"]}, kinds)
        for edge in self.mapping["resource_edges"]:
            with self.subTest(reference=edge["reference"]):
                if "source_path" in edge:
                    self.assertTrue(edge["source_path"])
                    self.assertGreaterEqual(edge["source_line"], 1)
                else:
                    self.assertIn(edge["source_behavior_id"], self.inventory["expected_behavior_ids"])
                    self.assertTrue(edge["source_anchors"])
                self.assertTrue(edge["reference"])
                if edge["kind"] == "packaged-resource":
                    path = PurePosixPath(edge["destination_path"])
                    self.assertEqual(path.parts[:2], ("plugins", "autopilot"))
                    self.assertNotIn("..", path.parts)
                    self.assertTrue(edge["failure_rule"].strip())
                elif edge["kind"] == "external-capability":
                    self.assertTrue(edge["capability"].strip())
                    self.assertTrue(edge["failure_rule"].strip())
                else:
                    self.assertTrue(edge["runtime_rule"].strip())


class ExplicitSourceAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue((TOOLS / "check-source.py").is_file(), "Public audit executable is missing")

    def test_audit_rejects_source_root_option_without_path_without_reading_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, HOME=directory, XDG_CONFIG_HOME=directory)
            result = subprocess.run(
                [sys.executable, str(TOOLS / "check-source.py"), "--source-root"],
                cwd=directory, env=env, capture_output=True, text=True, timeout=60,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((result.stdout + result.stderr).strip())

    def test_audit_reports_missing_pinned_objects_in_each_explicit_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            env = dict(os.environ, HOME=directory, XDG_CONFIG_HOME=directory)
            for name in ("source", "source-near-miss"):
                with self.subTest(source_root=name):
                    source = base / name
                    subprocess.run(["git", "init", "--quiet", str(source)],
                                   env=env, check=True, capture_output=True, timeout=60)
                    result = subprocess.run(
                        [sys.executable, str(TOOLS / "check-source.py"),
                         "--source-root", str(source)],
                        cwd=directory, env=env, capture_output=True, text=True, timeout=60,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertTrue((result.stdout + result.stderr).strip())


if __name__ == "__main__":
    unittest.main()

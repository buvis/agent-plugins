"""Public behavior captured before splitting the portable validators."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import validate

TEMPLATE = validate.ROOT / "templates" / "example-plugin"


class PluginFixture(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.plugin = self.root / "example-plugin"
        shutil.copytree(TEMPLATE, self.plugin)
        self.manifest_path = self.plugin / "plugin.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def write_manifest(self, changes: dict[str, object]) -> dict[str, object]:
        manifest = {**copy.deepcopy(self.manifest), **changes}
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest

    def assert_manifest_failure(self, message: str) -> None:
        with self.assertRaises(validate.ValidationError) as caught:
            validate.validate_manifest(self.plugin)
        self.assertIs(type(caught.exception), validate.ValidationError)
        self.assertEqual(str(caught.exception), f"{self.manifest_path}: {message}")


class ManifestCharacterization(PluginFixture):
    def test_accepted_manifest_is_returned_intact_without_writes(self) -> None:
        cases = [
            {},
            {"homepage": "", "repository": "", "keywords": [], "extensions": {}},
            {"description": " ", "license": " ", "author": {"name": " "}},
            {
                "author": {"name": "Author", "email": "", "url": ""},
                "keywords": ["", "日本語", "same", "same"],
                "extensions": {"example": {"nested": [None, 3, {"key": "value"}]}},
            },
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                expected = self.write_manifest(changes)
                before = self.manifest_path.read_bytes()
                self.assertEqual(validate.validate_manifest(self.plugin), expected)
                self.assertEqual(self.manifest_path.read_bytes(), before)

    def test_minimal_manifest(self) -> None:
        manifest = {
            key: self.manifest[key]
            for key in (
                "$schema",
                "name",
                "version",
                "description",
                "author",
                "license",
            )
        }
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(validate.validate_manifest(self.plugin), manifest)

    def test_name_length_boundary(self) -> None:
        self.plugin = self.plugin.rename(self.root / ("a" * 64))
        self.manifest_path = self.plugin / "plugin.json"
        expected = self.write_manifest({"name": "a" * 64})
        self.assertEqual(validate.validate_manifest(self.plugin), expected)
        self.write_manifest({"name": "a" * 65})
        self.assert_manifest_failure("invalid plugin name")

    def test_version_forms(self) -> None:
        for version in ("0.0.0", "1.2.3-alpha.01+build.5", "12.34.56", "1.2.3-01"):
            with self.subTest(version=version):
                expected = self.write_manifest({"version": version})
                self.assertEqual(validate.validate_manifest(self.plugin), expected)

    def test_field_rejections(self) -> None:
        cases = [
            ({"z": 0, "a": 0}, "unknown top-level fields: a, z"),
            ({"$schema": None}, "unsupported or missing $schema"),
            ({"name": None}, "name must be a non-empty string"),
            ({"name": ""}, "name must be a non-empty string"),
            ({"name": "bad--name"}, "invalid plugin name"),
            ({"name": "Bad"}, "invalid plugin name"),
            ({"name": "bad..name"}, "invalid plugin name"),
            ({"name": "different"}, "name must match the plugin directory"),
            ({"description": 0}, "description must be a string"),
            ({"homepage": None}, "homepage must be a string"),
            ({"repository": []}, "repository must be a string"),
            ({"license": False}, "license must be a string"),
            ({"version": None}, "repository policy requires a version"),
            ({"version": ""}, "repository policy requires a version"),
            ({"version": "01.2.3"}, "version must use Semantic Versioning"),
            ({"version": "1.2"}, "version must use Semantic Versioning"),
            ({"description": ""}, "repository policy requires a description"),
            ({"license": ""}, "repository policy requires a license"),
            ({"author": None}, "repository policy requires an author object"),
            ({"author": {"extra": 0}}, "author contains unknown fields"),
            ({"author": {}}, "author.name is required"),
            ({"author": {"name": ""}}, "author.name is required"),
            ({"author": {"name": "A", "email": 0}}, "author.email must be a string"),
            ({"author": {"name": "A", "url": None}}, "author.url must be a string"),
            ({"keywords": None}, "keywords must be an array"),
            ({"keywords": ["valid", 1]}, "keywords must contain only strings"),
            ({"extensions": []}, "extensions must be an object"),
            ({"extensions": {"x": []}}, "each extension value must be an object"),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes):
                self.write_manifest(changes)
                self.assert_manifest_failure(message)

    def test_required_fields_when_absent(self) -> None:
        cases = [
            ("$schema", "unsupported or missing $schema"),
            ("name", "name must be a non-empty string"),
            ("version", "repository policy requires a version"),
            ("description", "repository policy requires a description"),
            ("license", "repository policy requires a license"),
            ("author", "repository policy requires an author object"),
        ]
        for field, message in cases:
            with self.subTest(field=field):
                manifest = copy.deepcopy(self.manifest)
                del manifest[field]
                self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                self.assert_manifest_failure(message)

    def test_first_failure_across_checks(self) -> None:
        cases = [
            ({"z": 0, "$schema": None}, "unknown top-level fields: z"),
            ({"$schema": None, "name": ""}, "unsupported or missing $schema"),
            ({"name": "bad--name", "version": ""}, "invalid plugin name"),
            ({"description": 0, "homepage": 0}, "description must be a string"),
            ({"homepage": 0, "repository": 0}, "homepage must be a string"),
            ({"repository": 0, "license": 0}, "repository must be a string"),
            ({"license": 0, "version": None}, "license must be a string"),
            (
                {"version": None, "description": ""},
                "repository policy requires a version",
            ),
            (
                {"version": "bad", "description": ""},
                "version must use Semantic Versioning",
            ),
            (
                {"description": "", "license": ""},
                "repository policy requires a description",
            ),
            ({"license": "", "author": None}, "repository policy requires a license"),
            (
                {"author": None, "keywords": None},
                "repository policy requires an author object",
            ),
            ({"author": {"extra": 1, "name": ""}}, "author contains unknown fields"),
            ({"author": {"name": "", "email": 0}}, "author.name is required"),
            ({"keywords": [0], "extensions": []}, "keywords must contain only strings"),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes):
                self.write_manifest(changes)
                self.assert_manifest_failure(message)

    def test_author_field_order_is_insertion_order(self) -> None:
        for author, field in [
            ({"name": "A", "url": None, "email": 0}, "url"),
            ({"name": "A", "email": 0, "url": None}, "email"),
        ]:
            with self.subTest(author=author):
                self.write_manifest({"author": author})
                self.assert_manifest_failure(f"author.{field} must be a string")

    def test_missing_and_directory_manifest(self) -> None:
        self.manifest_path.unlink()
        self.assert_manifest_failure("missing required manifest")
        self.manifest_path.mkdir()
        self.assert_manifest_failure("missing required manifest")

    def test_escaping_manifest_precedes_json_validation(self) -> None:
        outside = self.root / "outside.json"
        outside.write_text("{", encoding="utf-8")
        self.manifest_path.unlink()
        self.manifest_path.symlink_to(outside)
        self.assert_manifest_failure("resolves outside plugin root")

    def test_json_errors(self) -> None:
        self.manifest_path.write_text("{", encoding="utf-8")
        self.assert_manifest_failure(
            "invalid JSON: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"
        )
        for value in (None, [], "text", 42, True):
            with self.subTest(value=value):
                self.manifest_path.write_text(json.dumps(value), encoding="utf-8")
                self.assert_manifest_failure("must contain a JSON object")

    def test_read_error_has_original_cause(self) -> None:
        failure = OSError("read denied")
        with (
            mock.patch.object(Path, "read_text", autospec=True, side_effect=failure),
            self.assertRaises(validate.ValidationError) as caught,
        ):
            validate.validate_manifest(self.plugin)
        self.assertEqual(
            str(caught.exception), f"{self.manifest_path}: invalid JSON: read denied"
        )
        self.assertIs(caught.exception.__cause__, failure)

    def test_invalid_utf8_propagates(self) -> None:
        self.manifest_path.write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError) as expected:
            b"\xff".decode("utf-8")
        with self.assertRaises(UnicodeDecodeError) as caught:
            validate.validate_manifest(self.plugin)
        self.assertEqual(caught.exception.args, expected.exception.args)
        self.assertEqual(str(caught.exception), str(expected.exception))

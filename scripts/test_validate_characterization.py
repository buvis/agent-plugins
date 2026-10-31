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


class McpCharacterization(PluginFixture):
    def setUp(self) -> None:
        super().setUp()
        self.mcp_path = self.plugin / "mcp.json"

    def write_config(self, config: object) -> None:
        self.mcp_path.write_text(json.dumps(config), encoding="utf-8")

    def write_servers(self, servers: object) -> None:
        self.write_config({"$schema": validate.MCP_SCHEMA, "mcpServers": servers})

    def assert_mcp_failure(self, message: str, name: str | None = "s") -> None:
        path = self.mcp_path if name is None else Path(f"{self.mcp_path}#{name}")
        with self.assertRaises(validate.ValidationError) as caught:
            validate.validate_mcp(self.plugin)
        self.assertIs(type(caught.exception), validate.ValidationError)
        self.assertEqual(str(caught.exception), f"{path}: {message}")

    def test_absent_empty_and_broken_link(self) -> None:
        self.assertIsNone(validate.validate_mcp(self.plugin))
        self.write_servers({})
        self.assertIsNone(validate.validate_mcp(self.plugin))
        self.mcp_path.unlink()
        self.mcp_path.symlink_to(self.root / "missing.json")
        self.assertIsNone(validate.validate_mcp(self.plugin))

    def test_valid_stdio_and_cwd_forms_without_writes(self) -> None:
        cases = [
            {"type": "stdio", "command": command}
            for command in ("node", " ", "./", "./bin/server", "./a/../server")
        ]
        cases.extend(
            {"type": "stdio", "command": "node", "cwd": cwd, "args": [], "env": {}}
            for cwd in (
                "./",
                "./dir",
                "./a/../b",
                "${PLUGIN_ROOT}",
                "${PLUGIN_DATA}",
                "${PLUGIN_ROOT}/bin",
                "${PLUGIN_DATA}/a/../b",
            )
        )
        cases.append(
            {
                "type": "stdio",
                "command": "node",
                "args": ["", "日本語"],
                "env": {"": "", "EXAMPLE": "synthetic"},
            }
        )
        for server in cases:
            with self.subTest(server=server):
                self.write_servers({"s": server})
                before = self.mcp_path.read_bytes()
                self.assertIsNone(validate.validate_mcp(self.plugin))
                self.assertEqual(self.mcp_path.read_bytes(), before)

    def test_valid_remote_transports_without_writes(self) -> None:
        for transport in ("streamable-http", "sse"):
            for url in (
                "https://example.com/mcp",
                "http://localhost/",
                "http://127.0.0.1/",
                "http://[::1]/",
            ):
                for headers in ({}, {"": "", "X-Example": "synthetic"}):
                    with self.subTest(transport=transport, url=url, headers=headers):
                        self.write_servers(
                            {"s": {"type": transport, "url": url, "headers": headers}}
                        )
                        before = self.mcp_path.read_bytes()
                        self.assertIsNone(validate.validate_mcp(self.plugin))
                        self.assertEqual(self.mcp_path.read_bytes(), before)

    def test_root_rejections(self) -> None:
        cases = [
            ([], "must contain a JSON object"),
            (None, "must contain a JSON object"),
            ({}, "must contain only $schema and mcpServers"),
            ({"mcpServers": {}}, "must contain only $schema and mcpServers"),
            (
                {"$schema": "bad", "mcpServers": {}, "extra": 0},
                "must contain only $schema and mcpServers",
            ),
            ({"$schema": "bad", "mcpServers": []}, "unsupported or missing $schema"),
            (
                {"$schema": validate.MCP_SCHEMA, "mcpServers": []},
                "mcpServers must be an object",
            ),
            (
                {"$schema": validate.MCP_SCHEMA, "mcpServers": None},
                "mcpServers must be an object",
            ),
        ]
        for config, message in cases:
            with self.subTest(config=config):
                self.write_config(config)
                self.assert_mcp_failure(message, name=None)

    def test_server_shape_and_transport(self) -> None:
        self.write_servers({"": None})
        self.assert_mcp_failure("server name must be non-empty", name="")
        for server, message in [
            (None, "server must be an object"),
            ([], "server must be an object"),
            ({}, "unknown MCP transport None"),
            ({"type": "other"}, "unknown MCP transport 'other'"),
            ({"type": False}, "unknown MCP transport False"),
        ]:
            with self.subTest(server=server):
                self.write_servers({"s": server})
                self.assert_mcp_failure(message)

    def test_stdio_rejections_and_field_order(self) -> None:
        cases = [
            ({"extra": 0, "command": None}, "stdio server contains unknown fields"),
            ({"command": None, "args": 0}, "stdio server requires command"),
            ({"command": ""}, "stdio server requires command"),
            ({"command": "./../bin"}, "command escapes the plugin root"),
            (
                {"command": "./a/../../bin", "args": 0},
                "command escapes the plugin root",
            ),
            ({"command": "./..\\bin"}, "command escapes the plugin root"),
            ({"command": "/bin/node"}, "command must be bare or start with ./"),
            ({"command": "a\\node"}, "command must be bare or start with ./"),
            ({"command": "a/node"}, "command must be bare or start with ./"),
            ({"args": None, "env": []}, "args must be strings"),
            ({"args": [1]}, "args must be strings"),
            ({"env": None, "cwd": None}, "env must be an object"),
            ({"env": {"PLUGIN_ROOT": 0}}, "env must not override reserved variables"),
            (
                {"env": {"PLUGIN_DATA": "synthetic", "X": 0}},
                "env must not override reserved variables",
            ),
            ({"env": {"X": 0}, "cwd": None}, "env keys and values must be strings"),
            ({"cwd": None}, "cwd must be a string"),
            ({"cwd": ""}, "cwd must be plugin-relative or rooted at a plugin variable"),
            (
                {"cwd": "."},
                "cwd must be plugin-relative or rooted at a plugin variable",
            ),
            (
                {"cwd": "/tmp"},
                "cwd must be plugin-relative or rooted at a plugin variable",
            ),
            (
                {"cwd": "${PLUGIN_ROOT}other"},
                "cwd must be plugin-relative or rooted at a plugin variable",
            ),
            ({"cwd": "./../outside"}, "cwd escapes its permitted root"),
            ({"cwd": "${PLUGIN_ROOT}/../outside"}, "cwd escapes its permitted root"),
            ({"cwd": "${PLUGIN_DATA}/..\\outside"}, "cwd escapes its permitted root"),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes):
                self.write_servers(
                    {"s": {"type": "stdio", "command": "node", **changes}}
                )
                self.assert_mcp_failure(message)
        self.write_servers({"s": {"type": "stdio"}})
        self.assert_mcp_failure("stdio server requires command")

    def test_remote_rejections_and_field_order(self) -> None:
        cases = [
            ({"extra": 0, "url": None}, "remote server contains unknown fields"),
            (
                {"url": None, "headers": []},
                "remote server URL must be a non-empty string",
            ),
            ({"url": ""}, "remote server URL must be a non-empty string"),
            ({"url": "/mcp"}, "remote URL must be absolute HTTP(S)"),
            ({"url": "ftp://example.com"}, "remote URL must be absolute HTTP(S)"),
            ({"url": "https:///missing"}, "remote URL must be absolute HTTP(S)"),
            (
                {"url": "http://name:synthetic@example.com/#frag"},
                "remote URL must not contain user information",
            ),
            (
                {"url": "http://example.com/#frag"},
                "remote URL must not contain a fragment",
            ),
            (
                {"url": "http://example.com/", "headers": []},
                "non-loopback MCP URLs must use HTTPS",
            ),
            ({"headers": None}, "headers must be an object"),
            ({"headers": {"X": 1}}, "header names and values must be strings"),
        ]
        for transport in ("streamable-http", "sse"):
            for changes, message in cases:
                with self.subTest(transport=transport, changes=changes):
                    self.write_servers(
                        {
                            "s": {
                                "type": transport,
                                "url": "https://example.com/",
                                **changes,
                            }
                        }
                    )
                    self.assert_mcp_failure(message)
            self.write_servers({"s": {"type": transport}})
            self.assert_mcp_failure("remote server URL must be a non-empty string")

    def test_server_iteration_order(self) -> None:
        for names in (("z", "a"), ("a", "z")):
            with self.subTest(names=names):
                self.write_servers({name: {"type": "bad"} for name in names})
                self.assert_mcp_failure("unknown MCP transport 'bad'", name=names[0])

    def test_directory_mcp(self) -> None:
        self.mcp_path.mkdir()
        self.assert_mcp_failure("must be a regular file", name=None)

    def test_escaping_mcp_precedes_json(self) -> None:
        outside = self.root / "outside.json"
        outside.write_text("{", encoding="utf-8")
        self.mcp_path.symlink_to(outside)
        self.assert_mcp_failure("resolves outside plugin root", name=None)

    def test_malformed_json_has_cause(self) -> None:
        self.mcp_path.write_text("{", encoding="utf-8")
        with self.assertRaises(validate.ValidationError) as caught:
            validate.validate_mcp(self.plugin)
        self.assertEqual(
            str(caught.exception),
            f"{self.mcp_path}: invalid JSON: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
        )
        self.assertIsInstance(caught.exception.__cause__, json.JSONDecodeError)

    def test_read_error_has_original_cause(self) -> None:
        self.write_servers({})
        failure = OSError("read denied")
        with (
            mock.patch.object(Path, "read_text", autospec=True, side_effect=failure),
            self.assertRaises(validate.ValidationError) as caught,
        ):
            validate.validate_mcp(self.plugin)
        self.assertEqual(
            str(caught.exception), f"{self.mcp_path}: invalid JSON: read denied"
        )
        self.assertIs(caught.exception.__cause__, failure)

    def test_uncaught_exception_types_and_messages(self) -> None:
        for transport, message in [
            ([], "unhashable type: 'list'"),
            ({}, "unhashable type: 'dict'"),
        ]:
            with self.subTest(transport=transport):
                self.write_servers({"s": {"type": transport}})
                with self.assertRaises(TypeError) as caught:
                    validate.validate_mcp(self.plugin)
                self.assertEqual(str(caught.exception), message)
        self.write_servers({"s": {"type": "sse", "url": "https://[invalid"}})
        with self.assertRaises(ValueError) as caught:
            validate.validate_mcp(self.plugin)
        self.assertEqual(str(caught.exception), "Invalid IPv6 URL")
        self.mcp_path.write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError) as expected:
            b"\xff".decode("utf-8")
        with self.assertRaises(UnicodeDecodeError) as caught:
            validate.validate_mcp(self.plugin)
        self.assertEqual(caught.exception.args, expected.exception.args)
        self.assertEqual(str(caught.exception), str(expected.exception))

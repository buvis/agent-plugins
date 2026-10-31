"""Source-size acceptance for the 00010 validator extraction."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

import validate

# Top-level function names at 6c16d03d7f5e878a3033de747866c931edcf12bf.
# Keep this data local: tests also run in checkouts without the base commit.
BASELINE_FUNCTIONS = {
    "require",
    "load_object",
    "is_string",
    "validate_manifest",
    "scalar",
    "frontmatter",
    "validate_skills",
    "contained_suffix",
    "validate_url",
    "validate_mcp",
    "validate_containment",
    "default_plugins",
    "main",
}
PUBLIC_VALIDATORS = {"validate_manifest", "validate_mcp"}
EXTRACTED_CHECKS = {
    "_validate_manifest_identity",
    "_validate_manifest_metadata",
    "_validate_manifest_author",
    "_validate_manifest_optional",
    "_validate_mcp_server",
    "_validate_stdio_server",
    "_validate_mcp_env",
    "_validate_mcp_cwd",
    "_validate_remote_server",
}


class ValidatorStructure(unittest.TestCase):
    def setUp(self) -> None:
        source = Path(validate.__file__).read_text(encoding="utf-8")
        self.functions = {
            node.name: node
            for node in ast.parse(source).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def test_expected_validators_and_checks_exist(self) -> None:
        self.assertEqual(
            (PUBLIC_VALIDATORS | EXTRACTED_CHECKS) - self.functions.keys(),
            set(),
        )

    def test_refactored_and_new_functions_fit_fifty_physical_lines(self) -> None:
        names = PUBLIC_VALIDATORS | (self.functions.keys() - BASELINE_FUNCTIONS)
        for name in sorted(names):
            with self.subTest(function=name):
                node = self.functions[name]
                self.assertLessEqual(node.end_lineno - node.lineno + 1, 50)

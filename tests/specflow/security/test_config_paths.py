"""Malformed configured paths fail closed through the public config loader."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "plugins/specflow/skills/spec-workflow/scripts"))
from specflow_helper.config import ConfigError, load_config


class ConfigPathTests(unittest.TestCase):
    def test_symlink_loop_is_a_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "loop").symlink_to("loop")
            (root / ".agents").mkdir()
            (root / ".agents/specflow.json").write_text(json.dumps({"root": "loop"}))
            with self.assertRaises(ConfigError):
                load_config(root)

    def test_all_configured_path_fields_refuse_escape(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".agents").mkdir()
            for field in ("root", "specsDir", "numberScan"):
                for value in ("../outside", "/outside", "C:\\outside"):
                    with self.subTest(field=field, value=value):
                        data = {field: [value] if field == "numberScan" else value}
                        (root / ".agents/specflow.json").write_text(json.dumps(data))
                        with self.assertRaises(ConfigError):
                            load_config(root)

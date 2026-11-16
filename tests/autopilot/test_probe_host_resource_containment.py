"""prepare()'s copy of the source plugin tree must not let a symlink inside
that tree hand the run a path outside it: a source-tree escape is refused
before anything is copied, and a live run that hits one never reports an
observation."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

CAPABILITIES = ("identity", "delegation", "isolation", "interception", "resources")
ROOT = Path(__file__).resolve().parents[2]
PROBE_HOST_PATH = ROOT / "tools" / "autopilot" / "probe-host.py"
PLUGIN_ROOT_EXPRS = {"claude": "${CLAUDE_PLUGIN_ROOT}", "codex": "${AUTOPILOT_PLUGIN_ROOT}"}


def _load_probe_host():
    spec = importlib.util.spec_from_file_location(
        "probe_host_under_test_containment", PROBE_HOST_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_valid_hooks(source: Path, host_id: str = "claude", script: str = "scripts/autopilot.py") -> None:
    """A minimal plugin tree whose bundle names a hooks asset whose one hook
    command names `script` under the host's plugin-root variable; the script
    itself exists only when it is the packaged `scripts/autopilot.py`."""
    hooks_dir = source / "compatibility" / host_id
    hooks_dir.mkdir(parents=True)
    command = (
        f'python3 "{PLUGIN_ROOT_EXPRS[host_id]}/{script}" --hook {host_id} --event PreToolUse'
    )
    document = {"hooks": {"PreToolUse": [
        {"matcher": "Bash", "hooks": [{"type": "command", "command": command}]}
    ]}}
    (hooks_dir / "hooks.json").write_text(json.dumps(document), encoding="utf-8")
    (source / "compatibility" / f"{host_id}.json").write_text(
        json.dumps({"host_id": host_id, "registration": {
            "asset": f"compatibility/{host_id}/hooks.json",
            "activation": "client-manifest-hooks-field"}}),
        encoding="utf-8",
    )
    packaged = source / "scripts" / "autopilot.py"
    packaged.parent.mkdir(parents=True, exist_ok=True)
    packaged.write_text("print('packaged')\n", encoding="utf-8")


class ProbeHostResourceContainmentTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.module = _load_probe_host()

    def _source_with_symlink(self, placement: str, *, target: Path) -> Path:
        source = self.root / f"source-{placement}-{target.name}"
        _write_valid_hooks(source)
        link = (
            source / "hooks"
            if placement == "top_level"
            else source / "nested" / "deep" / "asset"
        )
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target, target_is_directory=target.is_dir())
        return source

    def test_prepare_rejects_a_source_tree_whose_symlink_escapes_outside_it(self) -> None:
        outside = self.root / "outside-secret"
        outside.mkdir()
        (outside / "leak.txt").write_text("outside-secret-nonce", encoding="utf-8")
        for placement in ("top_level", "nested"):
            with self.subTest(placement=placement):
                source = self._source_with_symlink(placement, target=outside)
                self.module.SOURCE_PLUGIN = source
                run_dir = self.root / f"run-{placement}"
                run_dir.mkdir()
                with self.assertRaises(Exception):
                    self.module.prepare(run_dir, "claude")
                leaked = [
                    path
                    for path in run_dir.rglob("*")
                    if path.is_file() and "outside-secret-nonce" in path.read_text(errors="ignore")
                ]
                self.assertEqual(leaked, [], leaked)

    def test_prepare_accepts_a_source_tree_whose_symlink_stays_inside_it(self) -> None:
        for placement in ("top_level", "nested"):
            with self.subTest(placement=placement):
                source = self.root / f"source-inside-{placement}"
                _write_valid_hooks(source)
                inside_target = source / "compatibility"
                link = (
                    source / "hooks"
                    if placement == "top_level"
                    else source / "nested" / "deep" / "asset"
                )
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(inside_target, target_is_directory=True)
                self.module.SOURCE_PLUGIN = source
                run_dir = self.root / f"run-inside-{placement}"
                run_dir.mkdir()
                surface = self.module.prepare(run_dir, "claude")
                self.assertEqual(surface, "plugin-dir")
                self.assertTrue((run_dir / "plugin").exists())

    def test_run_live_marks_every_capability_not_observed_when_the_source_escapes(self) -> None:
        outside = self.root / "outside-secret-live"
        outside.mkdir()
        source = self._source_with_symlink("top_level", target=outside)
        self.module.SOURCE_PLUGIN = source
        run_dir = self.root / "live-run"
        result = self.module.run_live("claude", run_dir, self.root, 5.0)
        self.assertEqual(result["resource_check"], "failed")
        for capability in CAPABILITIES:
            with self.subTest(capability=capability):
                status = result["observed"][capability]
                self.assertEqual(status, {"status": "not_observed", "reason": "resource_escape"})


if __name__ == "__main__":
    unittest.main()

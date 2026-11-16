"""Live isolated probe runs against fake claude/codex hosts, split from test_host_argv."""

from __future__ import annotations

import json
import unittest

from probe_host_support import FAKE_STDOUT_MARK
from test_host_argv import (
    OBSERVED,
    PROBE_REFS,
    SOURCE_PLUGIN,
    TRACE_REL,
    LiveProbeCase,
    _DECOY_SENTINEL,
    _SENTINEL,
    _git,
    _refs,
    _resolve_in,
    _trace,
)


class ProbeHostLiveRunTest(LiveProbeCase):
    def test_relocated_host_probe_observes_identity_isolation_interception(self) -> None:
        source_manifest = SOURCE_PLUGIN / ".claude-plugin" / "plugin.json"
        manifest_before = source_manifest.read_bytes() if source_manifest.exists() else None
        runs = {}
        for host_id in ("claude", "codex"):
            with self.subTest(host_id=host_id):
                run = runs[host_id] = self.probe(host_id)
                record, run_dir = run["record"], run["run_dir"]
                self.assertEqual((record["schema_version"], record["certified"]), (2, False))
                self.assertEqual(record["static"]["host_id"], host_id)
                self.assertEqual(record["resource_check"], "passed")
                self.assertEqual(_resolve_in(run["root"], record["run_dir"]), run_dir.resolve())
                for capability in ("identity", "isolation", "interception", "resources"):
                    self.assertEqual(record["observed"][capability], OBSERVED, capability)
                self.assertEqual(
                    record["observed"]["delegation"],
                    OBSERVED if host_id == "claude"
                    else {"status": "not_observed", "reason": "capability_not_implemented"},
                )
                self.assert_invocations(host_id, run)
                self.assert_launches(host_id, run)
                self.assert_trace(host_id, run)
                self.assert_registration(host_id, run)
                self.assertEqual(_refs(run_dir / "remote.git") & PROBE_REFS, {"refs/heads/probe-control"})
                for leaked in (_SENTINEL, _DECOY_SENTINEL, FAKE_STDOUT_MARK):
                    self.assertNotIn(leaked, run["text"])
        manifest = runs["claude"]["run_dir"] / "plugin" / ".claude-plugin" / "plugin.json"
        self.assertEqual(
            json.loads(manifest.read_text(encoding="utf-8")),
            {"name": "autopilot", "hooks": "./compatibility/claude/hooks.json"},
        )
        after = source_manifest.read_bytes() if source_manifest.exists() else None
        self.assertEqual(after, manifest_before, "the probe edited the source package")
        codex_dir = runs["codex"]["run_dir"].resolve()
        self.assertEqual(runs["codex"]["record"]["registration_surface"], "project-layer")
        rendered = [
            (codex_dir / repo / ".codex" / "hooks.json").read_bytes()
            for repo in ("project", "control")
        ]
        asset = (SOURCE_PLUGIN / "compatibility" / "codex" / "hooks.json").read_bytes()
        self.assertEqual(rendered, [asset, asset])
        self.assertIn(b"${AUTOPILOT_PLUGIN_ROOT}", asset)
        self.assertNotIn(b"CLAUDE_PLUGIN_ROOT", asset)
        self.assertNotIn(str(codex_dir / "plugin").encode(), rendered[0])

    def test_probe_control_is_unbound_inside_a_bound_source_repo(self) -> None:
        for host_id, bound_source in (("claude", True), ("codex", True), ("claude", False)):
            with self.subTest(host_id=host_id, bound_source=bound_source):
                run = self.probe(host_id, bound_source=bound_source)
                run_dir = run["run_dir"]
                project, control, remote = (run_dir / name for name in ("project", "control", "remote.git"))
                self.assertTrue((project / ".autopilot" / "controller").is_dir())
                self.assertFalse((project / ".autopilot" / "controller").is_symlink())
                self.assertFalse((control / ".autopilot").exists())
                self.assertEqual(_git("--git-dir", str(remote), "rev-parse", "--is-bare-repository"), "true")
                for repo in (project, control):
                    self.assertTrue((repo / ".git").is_dir(), repo)
                    self.assertTrue((repo / TRACE_REL).parent.is_dir(), repo)
                    self.assertEqual(_git("-C", str(repo), "rev-list", "--count", "HEAD"), "1")
                    url = _git("-C", str(repo), "remote", "get-url", "probe-remote")
                    self.assertEqual((repo / url).resolve(), remote.resolve())
                control_lines = _trace(control / TRACE_REL)
                self.assertTrue(control_lines)
                self.assertEqual({line["bound"] for line in control_lines}, {False})
                self.assertEqual({line["bound"] for line in _trace(project / TRACE_REL)}, {True})
                self.assertEqual(_refs(remote) & PROBE_REFS, {"refs/heads/probe-control"})
                self.assertEqual(run["record"]["observed"]["interception"], OBSERVED)
                self.assertEqual((run["root"] / ".autopilot" / "controller").is_dir(), bound_source)


if __name__ == "__main__":
    unittest.main()

"""jobs.py design §4/§5: job request validation, recursion bounds, reviewer
isolation, child cleanup, standalone instructions and controller replies.

recursive_child_denied is now RecursionBoundTest (ancestry cycle, depth, and a
lineage record that survives stripped env). no_nested_driver_cli is
test_request_bind_close_never_spawn. reviewer_isolation is
ReviewerIsolationTest. Payload, derive_ancestry and bind shapes live in
test_jobs_payload.py and test_jobs_bind.py.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import json
import os
import signal
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parents[1]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
for _path in (SCRIPTS, TESTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

hosts = importlib.import_module("hosts")
jobs = importlib.import_module("jobs")
fakes = importlib.import_module("host_fakes")

DIFF = fakes.DIFF
PRD = fakes.PRD
MALFORMED_REPLY = {"accepted": False, "job_ref": None, "error": "malformed_controller_reply"}


class BuildJobRequestValidationTest(fakes.ProjectCase):
    def refuse_build(self, code: str = "invalid_request", **override) -> None:
        self.assert_refused(code, fakes.build, self.root, **override)

    def test_contract_constants(self) -> None:
        self.assertEqual(jobs.TIERS, ("haiku", "sonnet", "opus", "fable"))
        self.assertEqual(jobs.EFFORTS, ("low", "medium", "high", "xhigh", "max"))
        self.assertEqual((jobs.MAX_JOB_DEPTH, jobs.MAX_CHILD_DEPTH), (1, 1))
        self.assertEqual(jobs.MAX_INPUT_BYTES, 33554432)
        self.assertEqual(jobs.INTENT_SCHEMA, "autopilot.job-intent.v1")
        self.assertEqual(jobs.JOB_ENV, "AUTOPILOT_JOB_REQUEST")

    def test_carries_every_field_for_two_distinct_requests(self) -> None:
        fakes.seed(self.root, "docs/dev/tmp/plan.md", b"plan\n")
        cases = (
            dict(job_id="alice-review", role_id="consensus-reviewer", host_id="codex",
                 tier="opus", effort="high", inputs=[DIFF], excluded_input_kinds=[],
                 requester=fakes.native_session()),
            dict(job_id="blake-review", role_id="blind-reviewer", host_id="gemini",
                 tier="sonnet", effort="low",
                 inputs=[PRD, {"kind": "plan", "path": "docs/dev/tmp/plan.md"}],
                 excluded_input_kinds=["diff", "history"],
                 requester=fakes.native_session("codex", "cx-req-2", "hook_input")),
        )
        for fields in cases:
            with self.subTest(job_id=fields["job_id"]):
                request = fakes.build(self.root, **fields)
                for name in ("job_id", "role_id", "host_id", "tier", "effort", "requester"):
                    self.assertEqual(getattr(request, name), fields[name])
                self.assertEqual(request.ancestry, ())
                self.assertEqual(request.excluded_input_kinds, tuple(fields["excluded_input_kinds"]))
                expected = sorted(
                    (jobs.InputRef(kind=item["kind"], path=item["path"],
                                   sha256=fakes.sha256_hex((self.root / item["path"]).read_bytes()))
                     for item in fields["inputs"]),
                    key=lambda ref: (ref.kind, ref.path),
                )
                self.assertEqual(request.inputs, tuple(expected))

    def test_identity_strings_hold_1_to_256_utf8_bytes(self) -> None:
        for field in ("job_id", "role_id"):
            for value in ("x" * 256, "é" * 128, "r"):
                with self.subTest(field=field, accepted=len(value.encode("utf-8"))):
                    self.assertEqual(getattr(fakes.build(self.root, **{field: value}), field), value)
            for value in ("", "x" * 257, "é" * 128 + "a", "会" * 86):
                with self.subTest(field=field, refused=len(value.encode("utf-8"))):
                    self.refuse_build(**{field: value})

    def test_identity_strings_never_equal_a_provider_host_or_tier_name(self) -> None:
        reserved = {*hosts.PROVIDER_HOSTS, *hosts.ADAPTERS, *jobs.TIERS}
        self.assertTrue({"anthropic", "claude", "opus"} <= reserved)
        for field in ("job_id", "role_id"):
            for value in sorted(reserved):
                with self.subTest(field=field, value=value):
                    self.refuse_build(**{field: value})
            for value in ("claude-reviewer", "opus2", "xanthropic", "gemini-lens", "fable-review"):
                with self.subTest(field=field, near_miss=value):
                    self.assertEqual(getattr(fakes.build(self.root, **{field: value}), field), value)
        self.assertEqual(fakes.build(self.root, job_id="acme").job_id, "acme")
        with mock.patch.dict(hosts.PROVIDER_HOSTS, {"acme": "claude"}):
            self.refuse_build(job_id="acme")

    def test_accepts_every_registered_host_tier_and_effort(self) -> None:
        for field, values in (("host_id", tuple(hosts.ADAPTERS)), ("tier", jobs.TIERS),
                              ("effort", jobs.EFFORTS)):
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assertEqual(getattr(fakes.build(self.root, **{field: value}), field), value)

    def test_rejects_a_host_tier_or_effort_outside_its_table(self) -> None:
        for field, values in (
            ("host_id", ("claudex", "anthropic", "Codex", "codex ", "")),
            ("tier", ("Opus", "opus4", "son", "claude", "")),
            ("effort", ("", None, "High", "hig", "highest", "ultra")),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    self.refuse_build(**{field: value})

    def test_input_mappings_hold_exactly_kind_and_path(self) -> None:
        digest = fakes.sha256_hex(fakes.BASE_INPUTS[DIFF["path"]])
        self.assertEqual(len(fakes.build(self.root, inputs=[dict(DIFF)]).inputs), 1)
        for entry in ({"kind": "diff"}, {"path": DIFF["path"]}, {},
                      {**DIFF, "sha256": digest}, {**DIFF, "note": "x"}):
            with self.subTest(entry=entry):
                self.refuse_build(inputs=[entry])

    def test_input_kind_must_be_a_live_policy_input_kind(self) -> None:
        kinds = fakes.input_kinds()
        self.assertIn("diff", kinds)
        for kind in kinds:
            with self.subTest(kind=kind):
                request = fakes.build(self.root, inputs=[{"kind": kind, "path": DIFF["path"]}])
                self.assertEqual([ref.kind for ref in request.inputs], [kind])
        for kind in ("diffs", "dif", "Diff", "repo_tree", "mech-fact", ""):
            with self.subTest(kind=kind):
                self.refuse_build(inputs=[{"kind": kind, "path": DIFF["path"]}])

    def test_input_path_must_be_relative_posix_without_parent_steps(self) -> None:
        fakes.seed(self.temp, "outside.diff", b"outside\n")
        for path in (str(self.root / DIFF["path"]), "/etc/hosts", "../outside.diff",
                     "docs/../docs/dev/tmp/a.diff", "docs/dev/tmp/../tmp/a.diff", ""):
            with self.subTest(path=path):
                self.refuse_build(inputs=[{"kind": "diff", "path": path}])

    def test_input_must_resolve_to_a_regular_file_inside_project_root(self) -> None:
        outside = fakes.seed(self.temp, "outside.diff", b"outside\n")
        (self.root / "docs/dev/tmp/escape.diff").symlink_to(outside)
        (self.root / "docs/dev/tmp/inner.diff").symlink_to(self.root / DIFF["path"])
        (self.root / "docs/dev/tmp/folder").mkdir()
        for path in ("docs/dev/tmp/escape.diff", "docs/dev/tmp/missing.diff",
                     "docs/dev/tmp/folder", "docs/dev/tmp"):
            with self.subTest(path=path):
                self.refuse_build(inputs=[{"kind": "diff", "path": path}])
        inner = fakes.build(self.root, inputs=[{"kind": "diff", "path": "docs/dev/tmp/inner.diff"}])
        self.assertEqual(inner.inputs[0].path, "docs/dev/tmp/inner.diff")
        self.assertEqual(inner.inputs[0].sha256, fakes.sha256_hex(fakes.BASE_INPUTS[DIFF["path"]]))

    def test_input_digest_is_read_from_the_given_project_root(self) -> None:
        other = self.temp / "second"
        fakes.seed(other, DIFF["path"], b"second root bytes\n")
        here = fakes.build(self.root).inputs[0].sha256
        there = fakes.build(other).inputs[0].sha256
        self.assertEqual(there, fakes.sha256_hex(b"second root bytes\n"))
        self.assertNotEqual(here, there)

    def test_input_size_limit_is_inclusive_at_max_input_bytes(self) -> None:
        limit = jobs.MAX_INPUT_BYTES
        for name, size in (("at.bin", limit), ("over.bin", limit + 1)):
            with (self.root / "docs/dev/tmp" / name).open("wb") as stream:
                stream.truncate(size)
        at = fakes.build(self.root, inputs=[{"kind": "diff", "path": "docs/dev/tmp/at.bin"}])
        self.assertEqual(at.inputs[0].sha256, fakes.sha256_hex(bytes(limit)))
        self.refuse_build(inputs=[{"kind": "diff", "path": "docs/dev/tmp/over.bin"}])

    def test_inputs_are_sorted_by_kind_then_path(self) -> None:
        for relative in ("docs/dev/tmp/z.diff", "docs/dev/tmp/b.md", "docs/dev/tmp/a.md"):
            fakes.seed(self.root, relative, relative.encode("utf-8"))
        given = [
            {"kind": "prd", "path": "docs/dev/tmp/b.md"},
            {"kind": "diff", "path": "docs/dev/tmp/z.diff"},
            {"kind": "plan", "path": "docs/dev/tmp/a.md"},
            dict(DIFF),
        ]
        request = fakes.build(self.root, inputs=given)
        self.assertIsInstance(request.inputs, tuple)
        self.assertTrue(all(isinstance(ref, jobs.InputRef) for ref in request.inputs))
        self.assertEqual([(ref.kind, ref.path) for ref in request.inputs], [
            ("diff", "docs/dev/tmp/a.diff"), ("diff", "docs/dev/tmp/z.diff"),
            ("plan", "docs/dev/tmp/a.md"), ("prd", "docs/dev/tmp/b.md"),
        ])
        self.assertEqual(fakes.build(self.root, inputs=[]).inputs, ())

    def test_excluded_kinds_must_be_policy_input_kinds(self) -> None:
        accepted = fakes.build(self.root, excluded_input_kinds=["history", "plan"])
        self.assertEqual(accepted.excluded_input_kinds, ("history", "plan"))
        self.assertEqual(fakes.build(self.root, excluded_input_kinds=[]).excluded_input_kinds, ())
        for excluded in (["histories"], ["history", "Plan"], [""]):
            with self.subTest(excluded=excluded):
                self.refuse_build(excluded_input_kinds=excluded)

    def test_a_requester_without_a_native_session_is_refused(self) -> None:
        self.refuse_build("missing_native_session", requester=None)

    def test_request_is_isolated_from_later_caller_mutation(self) -> None:
        inputs = [dict(DIFF)]
        excluded = ["history"]
        request = fakes.build(self.root, inputs=inputs, excluded_input_kinds=excluded)
        before = request.to_payload()
        inputs[0]["path"] = PRD["path"]
        inputs.append(dict(PRD))
        excluded.append("plan")
        returned = request.to_payload()
        returned["inputs"].append(dict(PRD))
        returned["effort"] = "low"
        self.assertEqual(request.to_payload(), before)
        self.assertIsInstance(request.excluded_input_kinds, tuple)
        for target, field in ((request, "effort"), (request, "inputs"), (request.inputs[0], "sha256")):
            with self.subTest(field=field):
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    setattr(target, field, "x")


class RecursionBoundTest(fakes.ProjectCase):
    def entry(self, host_id: str = "claude", job_id: str = "earlier-job",
              session_id: str = "s-9") -> object:
        return jobs.AncestryEntry(host_id=host_id, job_id=job_id, session_id=session_id)

    def test_ancestry_at_max_job_depth_is_refused(self) -> None:
        self.assertEqual(fakes.build(self.root, ancestry=()).ancestry, ())
        for ancestry in ((self.entry(),), (self.entry(), self.entry("codex", "other", "s-8"))):
            with self.subTest(depth=len(ancestry)):
                self.assert_refused("recursion_depth", fakes.build, self.root, ancestry=ancestry)

    def test_an_ancestor_with_this_host_and_job_is_a_recursive_job(self) -> None:
        with mock.patch.object(jobs, "MAX_JOB_DEPTH", 4):
            for ancestry in (
                (self.entry("codex", "alice-review"),),
                (self.entry("gemini", "x"), self.entry("codex", "alice-review", "s-2"),
                 self.entry("claude", "y")),
            ):
                with self.subTest(ancestry=ancestry):
                    self.assert_refused("recursive_job", fakes.build, self.root, ancestry=ancestry)
            for ancestry in (
                (self.entry("codex", "alice-review2"),),
                (self.entry("codex", "alice"),),
                (self.entry("gemini", "alice-review"),),
                (self.entry("claude", "alice-review"), self.entry("codex", "blake-review")),
            ):
                with self.subTest(near_miss=ancestry):
                    self.assertEqual(fakes.build(self.root, ancestry=ancestry).ancestry, ancestry)

    def test_a_job_session_derives_depth_one_and_is_refused(self) -> None:
        job = fakes.build(self.root, host_id="gemini", job_id="blake-review")
        job_file = fakes.seed(self.root, "docs/dev/tmp/autopilot/blake.json",
                              json.dumps(job.to_payload()).encode("utf-8"))
        child = fakes.native_session("gemini", "gm-child-1")
        fakes.install_adapter(self, "gemini", session_from_environment=lambda env: child)
        ancestry = jobs.derive_ancestry({jobs.JOB_ENV: str(job_file)}, self.root)
        self.assertEqual(ancestry, (self.entry("gemini", "blake-review", "gm-child-1"),))
        self.assert_refused("recursion_depth", fakes.build, self.root, job_id="nested-review",
                            requester=child, ancestry=ancestry)

    def test_stripped_env_with_a_lineage_record_still_refuses(self) -> None:
        job = fakes.build(self.root)
        child = fakes.native_session("codex", "cx-child-1")
        jobs.bind_job_session(job.to_payload(), child=child, project_root=self.root)
        ancestry = jobs.derive_ancestry({}, self.root)
        self.assertEqual(ancestry, ())
        self.assert_refused("recursion_depth", fakes.build, self.root, job_id="nested-review",
                            requester=child, ancestry=ancestry)
        for near in (fakes.native_session("codex", "cx-child-10"),
                     fakes.native_session("gemini", "cx-child-1"),
                     fakes.native_session("codex", "cx-child-")):
            with self.subTest(near_miss=near):
                request = fakes.build(self.root, job_id="nested-review", requester=near)
                self.assertEqual(request.requester, near)

    def test_lineage_record_is_looked_up_under_the_given_project_root(self) -> None:
        other = self.temp / "other"
        for relative, data in fakes.BASE_INPUTS.items():
            fakes.seed(other, relative, data)
        child = fakes.native_session("claude", "cl-bound-7")
        elsewhere = fakes.build(other, host_id="claude")
        jobs.bind_job_session(elsewhere.to_payload(), child=child, project_root=other)
        self.assertEqual(fakes.build(self.root, requester=child).requester, child)
        self.assert_refused("recursion_depth", fakes.build, other, requester=child)


class ReviewerIsolationTest(fakes.ProjectCase):
    def test_payload_requests_a_fresh_cross_session_job_plan(self) -> None:
        for host_id, job_id in (("codex", "alice-review"), ("gemini", "blake-review")):
            with self.subTest(host_id=host_id):
                payload = fakes.build(self.root, host_id=host_id, job_id=job_id).to_payload()
                fixed = ("intent_schema", "operation", "required_capability", "execution", "isolation")
                self.assertEqual({key: payload[key] for key in fixed}, {
                    "intent_schema": "autopilot.job-intent.v1", "operation": "job.plan",
                    "required_capability": "workflow.jobs.v1", "execution": "cross-session",
                    "isolation": "fresh-session",
                })
                self.assertEqual((payload["host_id"], payload["job_id"]), (host_id, job_id))

    def test_an_excluded_input_kind_never_reaches_a_blind_reviewer(self) -> None:
        excluded = ["diff", "implementation-audit"]
        blind = fakes.build(self.root, role_id="blind-reviewer", inputs=[PRD],
                            excluded_input_kinds=excluded)
        self.assertEqual([ref.kind for ref in blind.inputs], ["prd"])
        self.assertEqual(blind.to_payload()["excluded_input_kinds"], excluded)
        for inputs in ([PRD, DIFF], [DIFF]):
            with self.subTest(inputs=inputs):
                self.assert_refused("invalid_request", fakes.build, self.root,
                                    inputs=inputs, excluded_input_kinds=excluded)
        plan = {"kind": "plan", "path": "docs/dev/tmp/plan.md"}
        fakes.seed(self.root, plan["path"], b"plan\n")
        self.assertEqual([ref.kind for ref in fakes.build(self.root, inputs=[DIFF, plan]).inputs],
                         ["diff", "plan"])
        self.assert_refused("invalid_request", fakes.build, self.root, inputs=[DIFF, plan],
                            excluded_input_kinds=["plan"])

    def test_controller_state_is_never_a_reviewer_input(self) -> None:
        for relative in ("docs/dev/project-management/autopilot/state.json",
                         "docs/dev/project-management/autopilot/ledger/dispatch-metrics.jsonl",
                         "docs/dev/project-management/autopilot/ledger/other.jsonl",
                         "docs/dev/project-management/autopilot/notes.md"):
            fakes.seed(self.root, relative, b"{}\n")
            with self.subTest(path=relative):
                self.assert_refused("invalid_request", fakes.build, self.root,
                                    inputs=[{"kind": "history", "path": relative}])
        near = "docs/dev/project-management/autopilot-notes/n.md"
        fakes.seed(self.root, near, b"notes\n")
        request = fakes.build(self.root, inputs=[{"kind": "history", "path": near}])
        self.assertEqual(request.inputs[0].path, near)

    def test_a_job_binds_only_a_distinct_session_of_its_own_host(self) -> None:
        payload = fakes.build(self.root, requester=fakes.native_session("codex", "cx-req-1")).to_payload()
        shared = fakes.build(self.root, requester=fakes.native_session("claude", "shared-1")).to_payload()
        before = fakes.files_under(self.root)
        for body, child, code in (
            (payload, fakes.native_session("claude", "cx-child-1"), "host_mismatch"),
            (payload, fakes.native_session("gemini", "cx-child-1"), "host_mismatch"),
            (payload, fakes.native_session("codex", "cx-req-1"), "same_session"),
            (shared, fakes.native_session("codex", "shared-1"), "same_session"),
        ):
            with self.subTest(child=child, code=code):
                self.assert_refused(code, jobs.bind_job_session, body, child=child,
                                    project_root=self.root)
        self.assertEqual(fakes.files_under(self.root), before)
        child = fakes.native_session("codex", "cx-req-10")
        bound = jobs.bind_job_session(payload, child=child, project_root=self.root)
        self.assertEqual(bound["child_session"]["session_id"], "cx-req-10")

    def test_a_changed_input_after_the_request_refuses_the_bind(self) -> None:
        payload = fakes.build(self.root, inputs=[DIFF, PRD]).to_payload()
        target = self.root / PRD["path"]
        target.write_bytes(b"# PRD 00014\n\nEdited after the request.\n")
        child = fakes.native_session("codex", "cx-child-1")
        before = fakes.files_under(self.root)
        self.assert_refused("input_digest_mismatch", jobs.bind_job_session, payload,
                            child=child, project_root=self.root)
        self.assertEqual(fakes.files_under(self.root), before)
        target.write_bytes(fakes.BASE_INPUTS[PRD["path"]])
        bound = jobs.bind_job_session(payload, child=child, project_root=self.root)
        self.assertEqual(bound["verified_inputs"], payload["inputs"])


class ChildCleanupTest(fakes.ProjectCase):
    def setUp(self) -> None:
        super().setUp()
        self.parent = fakes.native_session("claude", "parent-1")
        self.out = self.root / "docs/dev/tmp/children"
        self.out.mkdir(parents=True)

    def child(self, **override) -> dict:
        fields = {"child_id": "agent-1", "kind": "in-session", "parent_session_id": "parent-1",
                  "depth": 1}
        return {**fields, **override}

    def close(self, *, child: dict | None = None, outcome: str = "completed",
              raw: bytes = b"out\n", path: Path | None = None) -> dict:
        return jobs.close_native_child(
            parent=self.parent, child=self.child() if child is None else child, outcome=outcome,
            raw_output=raw, artifact_path=self.out / "agent-1.log" if path is None else path,
            project_root=self.root,
        )

    def test_writes_the_raw_output_once_and_reports_its_digest(self) -> None:
        for child_id, outcome, raw in (("agent-1", "completed", b"alpha\n"),
                                       ("agent-2", "cancelled", b"")):
            with self.subTest(child_id=child_id):
                path = self.out / f"{child_id}.log"
                result = self.close(child=self.child(child_id=child_id), outcome=outcome,
                                    raw=raw, path=path)
                self.assertEqual(set(result), {"schema_version", "child_id", "outcome",
                                               "artifact", "cleanup"})
                self.assertEqual(
                    (result["schema_version"], result["child_id"], result["outcome"],
                     result["cleanup"]),
                    (1, child_id, outcome, "completed"),
                )
                artifact = result["artifact"]
                self.assertEqual(set(artifact), {"path", "sha256", "bytes"})
                self.assertEqual((artifact["sha256"], artifact["bytes"]),
                                 (fakes.sha256_hex(raw), len(raw)))
                self.assertFalse(Path(artifact["path"]).is_absolute())
                self.assertEqual(artifact["path"], path.relative_to(self.root).as_posix())
                self.assertEqual(path.read_bytes(), raw)

    def test_accepts_only_completed_cancelled_or_failed(self) -> None:
        for index, outcome in enumerate(("completed", "cancelled", "failed")):
            with self.subTest(outcome=outcome):
                result = self.close(outcome=outcome, path=self.out / f"ok-{index}.log")
                self.assertEqual(result["outcome"], outcome)
        refused = self.out / "refused.log"
        for outcome in ("complete", "Completed", "cancel", "failed ", "killed", ""):
            with self.subTest(outcome=outcome):
                with self.assertRaises(jobs.JobRefused):
                    self.close(outcome=outcome, path=refused)
                self.assertFalse(os.path.lexists(refused))

    def test_refuses_a_child_that_is_not_this_sessions_in_session_child(self) -> None:
        path = self.out / "foreign.log"
        for override in ({"kind": "cross-session"}, {"kind": "in-session "}, {"kind": "in_session"},
                         {"parent_session_id": "parent-10"}, {"parent_session_id": "parent-"},
                         {"parent_session_id": "Parent-1"}):
            with self.subTest(override=override):
                self.assert_refused("foreign_child", self.close, child=self.child(**override),
                                    path=path)
                self.assertFalse(os.path.lexists(path))

    def test_refuses_a_child_deeper_than_max_child_depth(self) -> None:
        path = self.out / "deep.log"
        for depth in (2, 3):
            with self.subTest(depth=depth):
                self.assert_refused("recursion_depth", self.close, child=self.child(depth=depth),
                                    path=path)
                self.assertFalse(os.path.lexists(path))
        self.assertEqual(self.close(child=self.child(depth=1), path=path)["child_id"], "agent-1")

    def test_child_mapping_holds_exactly_its_four_keys(self) -> None:
        full = self.child()
        path = self.out / "shape.log"
        for broken in ({k: v for k, v in full.items() if k != "depth"},
                       {k: v for k, v in full.items() if k != "child_id"},
                       {**full, "request_id": "a" * 64}, {**full, "depth": "1"},
                       {**full, "child_id": 7}):
            with self.subTest(child=broken):
                with self.assertRaises(jobs.JobRefused):
                    self.close(child=broken, path=path)
                self.assertFalse(os.path.lexists(path))

    def test_refuses_a_second_write_to_the_same_artifact(self) -> None:
        path = self.out / "agent-1.log"
        self.close(raw=b"first\n", path=path)
        with self.assertRaises((OSError, jobs.JobRefused)):
            self.close(child=self.child(child_id="agent-2"), raw=b"second\n", path=path)
        self.assertEqual(path.read_bytes(), b"first\n")

    def test_refuses_an_artifact_in_controller_state_or_outside_the_root(self) -> None:
        autopilot = self.root / "docs/dev/project-management/autopilot"
        state = autopilot / "children"
        for folder in (state, autopilot / "ledger", autopilot / "a/b"):
            folder.mkdir(parents=True)
        for path in (state / "agent-1.log", autopilot / "agent-1.log",
                     autopilot / "ledger/agent-1.log", autopilot / "ledger/x.log",
                     autopilot / "a/b/x.log"):
            with self.subTest(path=path):
                with self.assertRaises(jobs.JobRefused):
                    self.close(path=path)
                self.assertFalse(os.path.lexists(path))
        outside = self.temp / "elsewhere"
        outside.mkdir()
        with self.assertRaises((OSError, jobs.JobRefused)):
            self.close(path=outside / "agent-1.log")
        self.assertEqual(sorted(outside.iterdir()), [])
        near = self.root / "docs/dev/project-management/autopilot-notes"
        near.mkdir(parents=True)
        self.assertEqual(self.close(path=near / "agent-1.log")["cleanup"], "completed")

    def test_never_follows_a_symlink_at_or_above_the_artifact(self) -> None:
        outside = self.temp / "elsewhere"
        outside.mkdir()
        (self.out / "dangling.log").symlink_to(outside / "planted.log")
        (self.out / "escape").symlink_to(outside, target_is_directory=True)
        for path in (self.out / "dangling.log", self.out / "escape" / "agent-1.log"):
            with self.subTest(path=path):
                with self.assertRaises((OSError, jobs.JobRefused)):
                    self.close(path=path)
        self.assertEqual(sorted(outside.iterdir()), [])


class StandaloneInstructionTest(fakes.ProjectCase):
    def install_argv(self, host_id: str, argv: list[str]) -> list:
        calls: list = []

        def build_job_argv(request: object) -> list[str]:
            calls.append(request)
            return list(argv)

        fakes.install_adapter(self, host_id, build_job_argv=build_job_argv)
        return calls

    def standalone(self, request: object, name: str = "job.json") -> dict:
        return jobs.request_job(request, seam=None, project_root=self.root,
                                request_file=self.root / "docs/dev/tmp" / name)

    def test_returns_the_launch_instruction_for_the_request(self) -> None:
        for host_id, tier, effort, argv in (("claude", "opus", "high", ["fake-claude", "--print"]),
                                            ("codex", "sonnet", "low", ["fake-codex", "exec"])):
            with self.subTest(host_id=host_id):
                calls = self.install_argv(host_id, argv)
                request = fakes.build(self.root, host_id=host_id, tier=tier, effort=effort)
                result = self.standalone(request, f"{host_id}-job.json")
                self.assertEqual(set(result), {"schema_version", "mode", "request", "instruction"})
                self.assertEqual((result["schema_version"], result["mode"], result["request"]),
                                 (1, "standalone", request.to_payload()))
                instruction = result["instruction"]
                self.assertEqual(set(instruction), {"host_id", "argv", "stdin", "env",
                                                    "manual_settings", "steps"})
                self.assertEqual((instruction["host_id"], instruction["argv"]), (host_id, argv))
                self.assertEqual(calls, [request])
                self.assertEqual(instruction["env"], {
                    "AUTOPILOT_JOB_REQUEST": str(self.root / "docs/dev/tmp" / f"{host_id}-job.json"),
                    "AUTOPILOT_DISPATCH_DEPTH": "1",
                })
                self.assertEqual(instruction["manual_settings"], {"tier": tier, "effort": effort})
                steps = instruction["steps"]
                self.assertIsInstance(steps, list)
                self.assertTrue(steps)
                self.assertTrue(all(isinstance(step, str) and step.strip() for step in steps))
                request_file = self.root / "docs/dev/tmp" / f"{host_id}-job.json"
                joined = "\n".join(steps)
                self.assertIn(str(request_file), joined)
                self.assertIn("--bind-job", joined)
                self.assertTrue(request_file.is_file())
                self.assertEqual(json.loads(request_file.read_text(encoding="utf-8")),
                                 request.to_payload())

    def test_dispatch_depth_is_the_requester_ancestry_plus_one(self) -> None:
        self.install_argv("codex", ["fake-codex"])
        ancestor = jobs.AncestryEntry(host_id="claude", job_id="earlier-job", session_id="s-1")
        with mock.patch.object(jobs, "MAX_JOB_DEPTH", 3):
            request = fakes.build(self.root, ancestry=(ancestor,))
            env = self.standalone(request)["instruction"]["env"]
        self.assertEqual(env["AUTOPILOT_DISPATCH_DEPTH"], "2")

    def test_stdin_binds_the_job_first_and_names_only_the_listed_inputs(self) -> None:
        self.install_argv("codex", ["fake-codex"])
        fakes.seed(self.root, "docs/dev/tmp/unlisted.diff", b"not for the reviewer\n")
        stdin = self.standalone(fakes.build(self.root, inputs=[DIFF, PRD]))["instruction"]["stdin"]
        bind = '--bind-job "$AUTOPILOT_JOB_REQUEST" --project-root'
        self.assertIn(bind, stdin)
        self.assertLess(stdin.index("scripts/autopilot.py"), stdin.index(bind))
        self.assertIn(str(self.root), stdin[stdin.index(bind):])
        for path in (DIFF["path"], PRD["path"]):
            with self.subTest(path=path):
                self.assertLess(stdin.index(bind), stdin.index(path))
        self.assertNotIn("unlisted.diff", stdin)

    def test_standalone_mode_needs_a_request_file(self) -> None:
        self.install_argv("codex", ["fake-codex"])
        request = fakes.build(self.root)
        self.assert_refused("invalid_request", jobs.request_job, request, seam=None,
                            project_root=self.root, request_file=None)
        self.assertEqual(self.standalone(request)["mode"], "standalone")

    def test_an_adapter_without_build_job_argv_is_refused(self) -> None:
        request = fakes.build(self.root, host_id="gemini")
        self.assert_refused("invalid_request", jobs._build_job_argv,
                            types.ModuleType("bare_adapter"), request)
        provided = types.ModuleType("argv_adapter")
        provided.build_job_argv = lambda req: ["fake-gemini", req.job_id]
        self.assertEqual(jobs._build_job_argv(provided, request), ["fake-gemini", "alice-review"])
        fakes.install_adapter(self, "gemini")
        self.assert_refused("invalid_request", self.standalone, request)

    def test_effort_is_required_and_never_in_argv(self) -> None:
        fields = fakes.job_fields(self.root)
        del fields["effort"]
        with self.assertRaises((TypeError, jobs.JobRefused)):
            jobs.build_job_request(**fields)
        for effort in ("", None):
            self.assert_refused("invalid_request", fakes.build, self.root, effort=effort)
        payload = fakes.build(self.root).to_payload()
        del payload["effort"]
        payload["request_id"] = fakes.canonical_request_id(payload)
        self.assert_refused("invalid_request", jobs.JobRequest.from_payload, payload)
        argv = ["fake-claude", "--print", "--output-format", "json"]
        self.install_argv("claude", argv)
        for effort in ("xhigh", "max", "medium"):
            with self.subTest(effort=effort):
                result = self.standalone(fakes.build(self.root, host_id="claude", effort=effort))
                instruction = result["instruction"]
                self.assertEqual(instruction["argv"], argv)
                for token in instruction["argv"]:
                    self.assertNotIn(effort, token)
                    self.assertNotIn("effort", token)
                self.assertEqual(instruction["manual_settings"]["effort"], effort)
                self.assertEqual(result["request"]["effort"], effort)


class ControllerModeTest(fakes.ProjectCase):
    def submit(self, request: object, reply: object) -> dict:
        return jobs.request_job(request, seam=fakes.ScriptedSeam(reply), project_root=self.root,
                                request_file=self.root / "docs/dev/tmp/job.json")

    def test_forwards_the_payload_and_nests_the_validated_reply(self) -> None:
        seam = fakes.FakeSeam(guard_rules={})
        first = fakes.build(self.root)
        second = fakes.build(self.root, job_id="blake-review", host_id="gemini")
        for index, request in enumerate((first, second), start=1):
            with self.subTest(job_id=request.job_id):
                result = jobs.request_job(request, seam=seam, project_root=self.root,
                                          request_file=None)
                self.assertEqual(result, {
                    "schema_version": 1, "mode": "controller", "request": request.to_payload(),
                    "reply": {"accepted": True, "job_ref": f"fake-job-{index}", "error": None},
                })
        self.assertEqual(seam.submitted_intents, [first.to_payload(), second.to_payload()])

    def test_reports_each_controller_rejection_as_is_without_fallback(self) -> None:
        codes = fakes.controller_error_codes()
        self.assertIn("missing_capability", codes)
        request = fakes.build(self.root)
        for code in codes:
            with self.subTest(code=code):
                reply = {"accepted": False, "job_ref": None, "error": code}
                result = self.submit(request, reply)
                self.assertEqual(result, {"schema_version": 1, "mode": "controller",
                                          "request": request.to_payload(), "reply": reply})

    def test_malformed_or_raising_replies_become_malformed_controller_reply(self) -> None:
        request = fakes.build(self.root)
        valid = {"accepted": True, "job_ref": "j-1", "error": None}
        self.assertEqual(self.submit(request, valid)["reply"], valid)
        for reply in (
            None, [], "accepted", {}, {"accepted": True, "job_ref": "j-1"},
            {**valid, "queue": "q1"}, {**valid, "job_ref": None}, {**valid, "job_ref": ""},
            {**valid, "job_ref": 7}, {**valid, "error": "invalid_request"},
            {"accepted": False, "job_ref": "j-1", "error": "invalid_request"},
            {"accepted": False, "job_ref": None, "error": None},
            {"accepted": False, "job_ref": None, "error": "invalid_requests"},
            {**valid, "accepted": 1}, {**valid, "accepted": "true"},
            RuntimeError("controller down"), OSError("socket closed"), ValueError("bad"),
        ):
            with self.subTest(reply=reply):
                result = self.submit(request, reply)
                self.assertEqual(result, {"schema_version": 1, "mode": "controller",
                                          "request": request.to_payload(), "reply": MALFORMED_REPLY})

    def test_seam_cannot_override_mode(self) -> None:
        request = fakes.build(self.root)
        for extra in ({"mode": "standalone"}, {"schema_version": 2}, {"request": {}},
                      {"instruction": {"argv": ["sh"]}}):
            with self.subTest(extra=extra):
                result = self.submit(request, {"accepted": True, "job_ref": "j-1", "error": None,
                                               **extra})
                self.assertEqual(result, {"schema_version": 1, "mode": "controller",
                                          "request": request.to_payload(), "reply": MALFORMED_REPLY})


_SPAWN_NAMES = (
    (subprocess, ("Popen", "run", "call", "check_call", "check_output", "getoutput",
                  "getstatusoutput")),
    (os, ("system", "fork", "forkpty", "posix_spawn", "posix_spawnp", "spawnv", "spawnve",
          "spawnl", "spawnle", "spawnvp", "spawnvpe", "execv", "execve", "execl", "execle",
          "execlp", "execlpe", "execvp", "execvpe", "kill", "killpg")),
    (signal, ("pthread_kill", "raise_signal")),
)
_OS_SPAWN_PREFIXES = ("exec", "spawn", "posix_spawn", "fork", "kill", "system")


class NoSpawnTest(fakes.ProjectCase):
    def arm_tripwires(self) -> dict:
        tripwires = {}
        for module, names in _SPAWN_NAMES:
            for name in names:
                if hasattr(module, name):
                    patcher = mock.patch.object(module, name, side_effect=AssertionError(name))
                    tripwires[f"{module.__name__}.{name}"] = patcher.start()
                    self.addCleanup(patcher.stop)
        self.assertTrue({"subprocess.Popen", "os.kill", "os.execv", "os.fork"} <= set(tripwires))
        return tripwires

    def test_request_bind_close_never_spawn(self) -> None:
        tripwires = self.arm_tripwires()
        fakes.install_adapter(self, "codex", build_job_argv=lambda request: ["fake-codex"])
        request = fakes.build(self.root)
        jobs.request_job(request, seam=None, project_root=self.root,
                         request_file=self.root / "docs/dev/tmp/job.json")
        jobs.request_job(request, seam=fakes.FakeSeam(guard_rules={}), project_root=self.root,
                         request_file=None)
        jobs.bind_job_session(request.to_payload(), child=fakes.native_session("codex", "cx-1"),
                              project_root=self.root)
        out = self.root / "docs/dev/tmp/children"
        out.mkdir()
        jobs.close_native_child(
            parent=fakes.native_session("claude", "parent-1"),
            child={"child_id": "agent-1", "kind": "in-session", "parent_session_id": "parent-1",
                   "depth": 1},
            outcome="cancelled", raw_output=b"partial\n", artifact_path=out / "agent-1.log",
            project_root=self.root,
        )
        self.assertEqual([name for name, wire in tripwires.items() if wire.called], [])

    def test_jobs_module_imports_no_process_or_signal_api(self) -> None:
        tree = ast.parse((SCRIPTS / "jobs.py").read_text(encoding="utf-8"))
        imported, from_os, os_attrs = set(), set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
                if node.module == "os":
                    from_os.update(alias.name for alias in node.names)
            elif (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                  and node.value.id == "os"):
                os_attrs.add(node.attr)
        self.assertEqual(imported & {"subprocess", "signal", "multiprocessing", "pty"}, set())
        spawning = {name for name in from_os | os_attrs if name.startswith(_OS_SPAWN_PREFIXES)}
        self.assertEqual(spawning, set())


if __name__ == "__main__":
    unittest.main()

"""The invalidation graph: every change against every downstream result, in both orders (T-023)."""

from __future__ import annotations

import unittest

import support
from specflow_helper.reconcile import reconcile
from specflow_helper.state import (
    artifact_status,
    derive_phase,
    load_state,
    stale_causes,
)

FILES = {"requirements": "requirements.md", "design": "design.md", "tasks": "tasks.md"}
TEXTS = {
    "requirements.md": support.REQUIREMENTS,
    "design.md": support.DESIGN,
    "tasks.md": support.TASKS,
}
S, A = "stale", "approved"

# (order, changed artifacts) -> expected statuses and causes.
TABLE = [
    ("requirements-first", (), {"requirements": A, "design": A, "tasks": A}, {}),
    (
        "requirements-first",
        ("requirements",),
        {"requirements": S, "design": S, "tasks": S},
        {
            "requirements": "requirements",
            "design": "requirements",
            "tasks": "requirements",
        },
    ),
    (
        "requirements-first",
        ("design",),
        {"requirements": A, "design": S, "tasks": S},
        {"design": "design", "tasks": "design"},
    ),
    (
        "requirements-first",
        ("tasks",),
        {"requirements": A, "design": A, "tasks": S},
        {"tasks": "tasks"},
    ),
    (
        "requirements-first",
        ("design", "tasks"),
        {"requirements": A, "design": S, "tasks": S},
        {"design": "design", "tasks": "design"},
    ),
    ("design-first", (), {"requirements": A, "design": A, "tasks": A}, {}),
    (
        "design-first",
        ("design",),
        {"requirements": S, "design": S, "tasks": S},
        {"design": "design", "requirements": "design", "tasks": "design"},
    ),
    (
        "design-first",
        ("requirements",),
        {"requirements": S, "design": A, "tasks": S},
        {"requirements": "requirements", "tasks": "requirements"},
    ),
    (
        "design-first",
        ("tasks",),
        {"requirements": A, "design": A, "tasks": S},
        {"tasks": "tasks"},
    ),
    (
        "design-first",
        ("requirements", "design"),
        {"requirements": S, "design": S, "tasks": S},
        {"design": "design", "requirements": "design", "tasks": "design"},
    ),
]


class InvalidationTest(support.TempTest):
    def build(self, order: str) -> tuple:
        spec = support.write_spec(self.tmp / order, TEXTS)
        state = support.approve(
            spec,
            support.new_state(workflowOrder=order),
            "requirements",
            "design",
            "tasks",
        )
        return spec, state

    def test_every_change_against_every_downstream_result(self) -> None:
        for order, changed, expected, causes in TABLE:
            with self.subTest(order=order, changed=changed):
                spec, state = self.build(order)
                for name in changed:
                    path = spec / FILES[name]
                    path.write_text(path.read_text() + "\nChanged.\n")
                before = {p.name: p.read_bytes() for p in spec.iterdir()}
                self.assertEqual(artifact_status(spec, state), expected)
                self.assertEqual(stale_causes(spec, state), causes)
                after = {p.name: p.read_bytes() for p in spec.iterdir()}
                self.assertEqual(after, before, "status must not alter any file")

    def test_recorded_stale_propagates_like_a_changed_hash(self) -> None:
        spec, state = self.build("requirements-first")
        state["artifacts"]["requirements"]["status"] = "stale"
        self.assertEqual(set(artifact_status(spec, state).values()), {S})

    def test_recorded_stale_outlives_the_upstream_reapproval(self) -> None:
        spec, _ = self.build("requirements-first")
        (spec / "requirements.md").write_text(support.REQUIREMENTS + "\nChanged.\n")
        reconcile(spec, dry_run=False)
        state = support.approve(spec, load_state(spec), "requirements")
        statuses = artifact_status(spec, state)
        self.assertEqual(statuses["requirements"], A)
        self.assertEqual((statuses["design"], statuses["tasks"]), (S, S))

    def test_upstream_reapproval_without_reconcile_never_revives_downstream(
        self,
    ) -> None:
        for order, edited, below in (
            ("requirements-first", "requirements", ("design", "tasks")),
            ("design-first", "design", ("requirements", "tasks")),
        ):
            with self.subTest(order=order):
                spec, state = self.build(order)
                path = spec / FILES[edited]
                path.write_text(path.read_text() + "\nChanged.\n")
                state = support.approve(spec, state, edited)
                statuses = artifact_status(spec, state)
                self.assertEqual(statuses[edited], A)
                self.assertEqual([statuses[name] for name in below], [S, S])
                causes = stale_causes(spec, state)
                self.assertEqual(
                    {name: causes[name] for name in below}, dict.fromkeys(below, edited)
                )

    def test_approval_without_an_upstream_binding_is_stale_until_approved_again(
        self,
    ) -> None:
        spec, state = self.build("requirements-first")
        del state["artifacts"]["tasks"]["upstreamSha256"]
        self.assertEqual(
            artifact_status(spec, state),
            {"requirements": A, "design": A, "tasks": S},
        )
        self.assertEqual(stale_causes(spec, state), {"tasks": "tasks"})
        state = support.approve(spec, state, "tasks")
        self.assertEqual(set(artifact_status(spec, state).values()), {A})

    def test_partial_upstream_binding_never_revives_after_upstream_reapproval(
        self,
    ) -> None:
        for order, first, second in (
            ("requirements-first", "requirements", "design"),
            ("design-first", "design", "requirements"),
        ):
            with self.subTest(order=order):
                spec, state = self.build(order)
                del state["artifacts"]["tasks"]["upstreamSha256"][first]
                self.assertEqual(stale_causes(spec, state), {"tasks": "tasks"})
                path = spec / FILES[first]
                path.write_text(path.read_text() + "\nChanged.\n")
                state = support.approve(spec, state, first, second)
                statuses = artifact_status(spec, state)
                self.assertEqual((statuses[first], statuses[second]), (A, A))
                self.assertEqual(statuses["tasks"], S)
                state = support.approve(spec, state, "tasks")
                self.assertEqual(set(artifact_status(spec, state).values()), {A})

    def test_first_artifact_of_the_order_needs_no_binding(self) -> None:
        spec, state = self.build("design-first")
        self.assertNotIn("upstreamSha256", state["artifacts"]["design"])
        self.assertEqual(set(artifact_status(spec, state).values()), {A})

    def test_draft_downstream_stays_draft(self) -> None:
        spec, state = self.build("requirements-first")
        state["artifacts"]["tasks"] = {"path": "tasks.md", "status": "draft"}
        (spec / "requirements.md").write_text(support.REQUIREMENTS + "\nChanged.\n")
        self.assertEqual(artifact_status(spec, state)["tasks"], "draft")

    def test_approved_plan_without_a_task_is_not_complete(self) -> None:
        spec, state = self.build("requirements-first")
        plan = "# Tasks: Sample\n\n## Completion criteria\n\n- [x] Done.\n"
        (spec / "tasks.md").write_text(plan)
        support.approve(spec, state, "tasks")
        statuses = artifact_status(spec, state)
        self.assertEqual(
            derive_phase(spec, statuses, "requirements-first"),
            "implementation",
        )

    def test_stale_upstream_closes_the_implementation_gate(self) -> None:
        for order in ("requirements-first", "design-first"):
            with self.subTest(order=order):
                spec, state = self.build(order)
                self.assertEqual(
                    derive_phase(spec, artifact_status(spec, state), order),
                    "implementation",
                )
                (spec / "design.md").write_text(support.DESIGN + "\nChanged.\n")
                phase = derive_phase(spec, artifact_status(spec, state), order)
                self.assertNotIn(phase, ("implementation", "verification", "complete"))


if __name__ == "__main__":
    unittest.main()

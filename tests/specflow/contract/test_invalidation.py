"""The invalidation graph: every change against every downstream result, in both orders (T-023)."""

from __future__ import annotations

import unittest

import support
from specflow_helper.state import artifact_status, derive_phase, stale_causes

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
        {"requirements": "requirements", "design": "requirements", "tasks": "requirements"},
    ),
    (
        "requirements-first",
        ("design",),
        {"requirements": A, "design": S, "tasks": S},
        {"design": "design", "tasks": "design"},
    ),
    ("requirements-first", ("tasks",), {"requirements": A, "design": A, "tasks": S}, {"tasks": "tasks"}),
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
    ("design-first", ("tasks",), {"requirements": A, "design": A, "tasks": S}, {"tasks": "tasks"}),
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
            spec, support.new_state(workflowOrder=order), "requirements", "design", "tasks"
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

    def test_draft_downstream_stays_draft(self) -> None:
        spec, state = self.build("requirements-first")
        state["artifacts"]["tasks"] = {"path": "tasks.md", "status": "draft"}
        (spec / "requirements.md").write_text(support.REQUIREMENTS + "\nChanged.\n")
        self.assertEqual(artifact_status(spec, state)["tasks"], "draft")

    def test_stale_upstream_closes_the_implementation_gate(self) -> None:
        for order in ("requirements-first", "design-first"):
            with self.subTest(order=order):
                spec, state = self.build(order)
                self.assertEqual(
                    derive_phase(spec, artifact_status(spec, state), order), "implementation"
                )
                (spec / "design.md").write_text(support.DESIGN + "\nChanged.\n")
                phase = derive_phase(spec, artifact_status(spec, state), order)
                self.assertNotIn(phase, ("implementation", "verification", "complete"))


if __name__ == "__main__":
    unittest.main()

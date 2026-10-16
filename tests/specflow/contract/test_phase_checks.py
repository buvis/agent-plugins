"""Seeded defects for the checks of 00006 (T-072, T-034, T-039)."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

import support
from specflow_helper.checks import validate
from test_checks import ChecksTest

SKETCH = support.FIXTURES / "sketch"


class SketchScreensTest(ChecksTest):
    """sketch-screens on an intake item's spike (T-072, INT-002.8)."""

    def sketch(self, *overlays: str) -> Path:
        item = self.repo / ".kiro" / "specflow" / "intake" / "new" / "00107-carts"
        shutil.copytree(SKETCH / "good", item / "spike")
        (item / "idea.md").write_text("Let customers save a cart.\n")
        for overlay in overlays:
            shutil.copytree(
                SKETCH / "malformed" / overlay, item / "spike", dirs_exist_ok=True
            )
        return item

    def messages(self, item: Path) -> list[str]:
        return [
            f["message"]
            for f in validate(self.repo, item, "intake")
            if f["rule"] == "sketch-screens"
        ]

    def test_well_formed_sketch_passes(self) -> None:
        item = self.sketch()
        self.assertEqual(self.messages(item), [])
        self.assertEqual(self.rules(item, "intake"), set())

    def test_intake_item_without_a_sketch_passes(self) -> None:
        item = self.sketch()
        shutil.rmtree(item / "spike")
        self.assertEqual(self.messages(item), [])

    def test_missing_screen_mockup_fails(self) -> None:
        item = self.sketch()
        (item / "spike" / "mockups" / "orders.html").unlink()
        self.assert_seeded(item, "sketch-screens", "intake")
        self.assertEqual(
            self.messages(item), ["screen orders has no spike/mockups/orders.html"]
        )

    def test_orphan_mockup_fails(self) -> None:
        item = self.sketch("orphan-mockup")
        self.assertEqual(
            self.messages(item),
            ["spike/mockups/profile.html belongs to no screen of spike/journey.md"],
        )

    def test_navigation_index_is_no_screen(self) -> None:
        item = self.sketch()
        (item / "spike" / "mockups" / "index.html").unlink()
        self.assertEqual(self.messages(item), [])

    def test_wrong_link_fails_with_its_edge(self) -> None:
        item = self.sketch("wrong-link")
        [message] = self.messages(item)
        self.assertIn("line 9: the action 'Check out' from cart", message)
        self.assertIn("checkout.html", message)

    def test_mermaid_line_of_no_accepted_kind_fails_with_its_line_number(self) -> None:
        item = self.sketch("bad-line")
        [message] = self.messages(item)
        self.assertTrue(message.startswith("line 9: click cart"), message)

    def test_screen_shared_across_journeys_needs_one_mockup(self) -> None:
        journey = (SKETCH / "good" / "journey.md").read_text()
        starts = [
            line for line in journey.splitlines() if line.strip().startswith("login")
        ]
        self.assertEqual(len(starts), 2)
        self.assertEqual(self.messages(self.sketch()), [])

    def test_check_runs_only_for_intake(self) -> None:
        spec = self.copy("00101-feature-sample")
        shutil.copytree(SKETCH / "good", spec / "spike")
        (spec / "spike" / "mockups" / "orders.html").unlink()
        self.assertNotIn("sketch-screens", self.rules(spec))


if __name__ == "__main__":
    unittest.main()

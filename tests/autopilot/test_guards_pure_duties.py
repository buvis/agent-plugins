"""Tests for the five pure guard duties in guards.py.

Each duty decides from its own named context keys alone, denies with a reason
naming the duty and the missing input when a key is absent or mistyped, and
gives `{"ok": True}` no special meaning (missing_guard_refused).
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

guards = importlib.import_module("guards")

GuardDuty = guards.GuardDuty

STORE = "docs/dev/project-management"

KNOWN_DIRS = frozenset(
    {
        "prds", "designs", "reviews", "plans", "autopilot", "meta", "discovery",
        "intake", "specs", "notes", "walkthroughs", "audit-results", "spikes",
    }
)  # fmt: skip
META_KEEPERS = (
    "project-capsule.md",
    "decisions.md",
    "troubleshooting.md",
    "assumptions.md",
    "agoge-profile.md",
    "ecc-cursor",
    "upstream-cursor",
)


def _run(duty, context):
    return guards.run_guard(duty, context, seam=None)


class _DutyTestCase(unittest.TestCase):
    duty: GuardDuty

    def assertAllowed(self, context) -> None:
        outcome = _run(self.duty, context)
        self.assertIs(outcome.duty, self.duty)
        self.assertIs(outcome.allowed, True, msg=f"{context!r} -> {outcome.reason}")
        self.assertIsNone(outcome.reason)
        self.assertIs(outcome.stateful, False)

    def assertDenied(self, context, *, names: str | None = None) -> None:
        outcome = _run(self.duty, context)
        self.assertIs(outcome.duty, self.duty)
        self.assertIs(outcome.allowed, False, msg=f"{context!r} should be denied")
        self.assertIsInstance(outcome.reason, str)
        self.assertIn(self.duty.value, outcome.reason)
        if names is not None:
            self.assertIn(names, outcome.reason)
        self.assertIs(outcome.stateful, False)

    def assertFailsClosed(self, context, key: str) -> None:
        self.assertDenied(context, names=key)


class DocumentLocationTest(_DutyTestCase):
    duty = GuardDuty.DOCUMENT_LOCATION

    def test_allows_a_path_outside_the_store(self) -> None:
        for path in ("src/app.py", "README.md", "/repo/docs/guide.md", "src/backlog/x.md"):
            with self.subTest(path=path):
                self.assertAllowed({"document_path": path})

    def test_allows_a_path_that_only_resembles_the_store_segment(self) -> None:
        for path in (
            f"{STORE}-old/prds/x.md",
            "docs/dev/project-management2/x.md",
            "docs/dev/project/prds/x.md",
        ):
            with self.subTest(path=path):
                self.assertAllowed({"document_path": path})

    def test_allows_a_prd_in_each_lifecycle_directory(self) -> None:
        for stage in ("backlog", "wip", "hold", "done"):
            for prefix in ("", "/home/me/repo/"):
                path = f"{prefix}{STORE}/prds/{stage}/00014-x.md"
                with self.subTest(path=path):
                    self.assertAllowed({"document_path": path})

    def test_allows_a_file_in_a_known_store_directory(self) -> None:
        for name in KNOWN_DIRS - {"prds", "meta"}:
            for rel in (f"{name}/note.md", f"{name}/sub/deep/note.md"):
                with self.subTest(path=rel):
                    self.assertAllowed({"document_path": f"{STORE}/{rel}"})

    def test_denies_a_top_level_directory_outside_the_closed_known_set(self) -> None:
        # decisions and audits are NOT store directories; audit-results is.
        for name in ("decisions", "audits", "audit-result", "audit_results", "Reviews", "spike"):
            with self.subTest(directory=name):
                self.assertDenied({"document_path": f"{STORE}/{name}/x.md"})
                self.assertDenied({"document_path": f"{STORE}/{name}/adr-1/x.md"})

    def test_allows_each_keeper_file_directly_under_meta(self) -> None:
        for name in META_KEEPERS:
            with self.subTest(name=name):
                self.assertAllowed({"document_path": f"{STORE}/meta/{name}"})

    def test_denies_a_near_miss_of_a_meta_keeper_name(self) -> None:
        for name in ("project-capsule.md.bak", "Decisions.md", "ecc-cursor.md", "upstream-cursor.md"):
            with self.subTest(name=name):
                self.assertDenied({"document_path": f"{STORE}/meta/{name}"})

    def test_denies_a_bare_file_at_the_store_root(self) -> None:
        for path in (f"{STORE}/notes.md", f"/repo/{STORE}/todo.md"):
            with self.subTest(path=path):
                self.assertDenied({"document_path": path})

    def test_denies_a_prd_outside_a_lifecycle_directory(self) -> None:
        for path in (
            f"{STORE}/prds/00014-x.md",
            f"{STORE}/prds/backlog",
            f"{STORE}/prds/draft/00014-x.md",
            f"{STORE}/prds/wip-old/00014-x.md",
            f"{STORE}/prds/WIP/00014-x.md",
        ):
            with self.subTest(path=path):
                self.assertDenied({"document_path": path})

    def test_denies_a_file_in_trash_or_a_foreign_store_directory(self) -> None:
        for path in (
            f"{STORE}/.trash/x.md",
            f"{STORE}/.trash/prds/wip/x.md",
            f"{STORE}/scratch/x.md",
            f"{STORE}/prd/wip/x.md",
            f"{STORE}/prdsx/wip/x.md",
        ):
            with self.subTest(path=path):
                self.assertDenied({"document_path": path})

    def test_denies_an_unknown_or_nested_meta_file(self) -> None:
        for path in (f"{STORE}/meta/random-notes.md", f"{STORE}/meta/sub/x.md", f"{STORE}/meta"):
            with self.subTest(path=path):
                self.assertDenied({"document_path": path})

    def test_denies_a_lifecycle_directory_at_the_repo_root(self) -> None:
        for path in ("backlog/00014-x.md", "wip/00014-x.md", "hold/x.md", "done/x.md"):
            with self.subTest(path=path):
                self.assertDenied({"document_path": path})

    def test_fails_closed_when_document_path_is_absent_or_mistyped(self) -> None:
        self.assertFailsClosed({}, "document_path")
        self.assertFailsClosed({"ok": True}, "document_path")
        for value in (None, 5, ["docs/x.md"], Path("src/app.py")):
            with self.subTest(value=value):
                self.assertFailsClosed({"document_path": value}, "document_path")

    def test_denies_a_traversal_that_resolves_to_the_store_root(self) -> None:
        traversal = f"{STORE}/prds/wip/../../x.md"
        resolved = f"{STORE}/x.md"
        self.assertDenied({"document_path": resolved})
        self.assertDenied({"document_path": traversal})
        self.assertDenied({"document_path": f"/repo/{STORE}/prds/wip/../../x.md"})

    def test_denies_a_traversal_that_resolves_to_a_foreign_store_directory(self) -> None:
        for path in (
            f"{STORE}/prds/wip/../../scratch/x.md",
            f"{STORE}/prds/wip/../../.trash/x.md",
            f"{STORE}/designs/../prds/00014-x.md",
        ):
            with self.subTest(path=path):
                self.assertDenied({"document_path": path})

    def test_allows_a_traversal_that_resolves_to_an_allowed_location(self) -> None:
        for path in (
            f"{STORE}/designs/../prds/wip/00014-x.md",
            f"{STORE}/prds/backlog/../wip/00014-x.md",
            f"{STORE}/prds/wip/../../designs/x.md",
        ):
            with self.subTest(path=path):
                self.assertAllowed({"document_path": path})

    def test_denies_a_path_that_still_climbs_after_normalisation(self) -> None:
        for path in (
            "../../etc/x.md",
            "../x.md",
            f"../{STORE}/prds/wip/x.md",
            f"../../{STORE}/prds/wip/x.md",
        ):
            with self.subTest(path=path):
                self.assertDenied({"document_path": path})

    def test_treats_dotdot_lookalike_segments_as_ordinary_names(self) -> None:
        for path in (
            f"{STORE}/prds/wip/..foo/x.md",
            f"{STORE}/designs/foo..bar/x.md",
            f"{STORE}/designs/..foo/x.md",
            "src/..foo/x.md",
        ):
            with self.subTest(path=path):
                self.assertAllowed({"document_path": path})
        self.assertDenied({"document_path": f"{STORE}/..foo/x.md"})
        self.assertDenied({"document_path": f"{STORE}/prds/..wip/x.md"})

    def test_collapses_single_dot_segments(self) -> None:
        self.assertAllowed({"document_path": f"{STORE}/./prds/wip/x.md"})
        self.assertAllowed({"document_path": f"{STORE}/prds/./wip/./x.md"})
        self.assertDenied({"document_path": f"{STORE}/./x.md"})
        self.assertDenied({"document_path": f"{STORE}/prds/./x.md"})


class DelegationTest(_DutyTestCase):
    duty = GuardDuty.DELEGATION

    def test_denies_dispatching_a_whole_phase_skill(self) -> None:
        for skill in (
            "autopilot:work",
            "autopilot:plan-tasks",
            "autopilot:design-solution",
            "autopilot:review-work-completion",
            "autopilot:run-autopilot",
            "git-ferry:catchup",
        ):
            with self.subTest(skill=skill):
                self.assertDenied({"dispatch_skill": skill})

    def test_allows_any_other_skill_and_persona_dispatch(self) -> None:
        for skill in ("autopilot:use-codex", "persona:devon", "tess", "git-ferry:status"):
            with self.subTest(skill=skill):
                self.assertAllowed({"dispatch_skill": skill})

    def test_matches_the_exact_skill_name_only(self) -> None:
        for skill in (
            "autopilot:work-item",
            "autopilot:worker",
            "my-autopilot:work",
            "autopilot:plan",
            "git-ferry:catchup-all",
            "autopilot",
            "",
        ):
            with self.subTest(skill=skill):
                self.assertAllowed({"dispatch_skill": skill})

    def test_fails_closed_when_dispatch_skill_is_absent_or_mistyped(self) -> None:
        self.assertFailsClosed({}, "dispatch_skill")
        self.assertFailsClosed({"ok": True}, "dispatch_skill")
        for value in (None, 7, ["autopilot:use-codex"]):
            with self.subTest(value=value):
                self.assertFailsClosed({"dispatch_skill": value}, "dispatch_skill")


class PostHandoffTest(_DutyTestCase):
    duty = GuardDuty.POST_HANDOFF

    def test_denies_a_guarded_skill_after_the_leave_row(self) -> None:
        for skill in ("autopilot:work", "autopilot:use-codex", "git-ferry:catchup"):
            with self.subTest(skill=skill):
                self.assertDenied({"requested_skill": skill, "leave_recorded": True})

    def test_allows_any_skill_before_the_leave_row(self) -> None:
        for skill in ("autopilot:work", "git-ferry:catchup", "persona:devon"):
            with self.subTest(skill=skill):
                self.assertAllowed({"requested_skill": skill, "leave_recorded": False})

    def test_allows_an_unguarded_skill_after_the_leave_row(self) -> None:
        for skill in ("persona:devon", "git-ferry:status", "xautopilot:work", "autopilot", ""):
            with self.subTest(skill=skill):
                self.assertAllowed({"requested_skill": skill, "leave_recorded": True})

    def test_matches_git_ferry_catchup_by_equality_only(self) -> None:
        self.assertAllowed({"requested_skill": "git-ferry:catchup-all", "leave_recorded": True})
        self.assertAllowed({"requested_skill": "git-ferry:catch", "leave_recorded": True})

    def test_a_leave_row_of_another_session_never_denies(self) -> None:
        for mine, theirs in (("s2", "s1"), ("run-b", "run-a")):
            with self.subTest(session=mine, leave_session=theirs):
                self.assertAllowed(
                    {
                        "requested_skill": "autopilot:work",
                        "leave_recorded": True,
                        "session": mine,
                        "leave_session": theirs,
                    }
                )

    def test_a_leave_row_of_the_same_session_denies(self) -> None:
        for session in ("s1", "run-a"):
            with self.subTest(session=session):
                self.assertDenied(
                    {
                        "requested_skill": "autopilot:work",
                        "leave_recorded": True,
                        "session": session,
                        "leave_session": session,
                    }
                )

    def test_denies_when_only_one_session_key_is_present(self) -> None:
        # Deliberate divergence from the source hook, which lets a malformed
        # marker pass because prose backs it up. A client-native guard has no
        # prose behind it, so it fails closed: it cannot show the leave row
        # belongs to a different session.
        for extra in ({"session": "s1"}, {"leave_session": "s1"}):
            with self.subTest(extra=extra):
                self.assertDenied(
                    {"requested_skill": "autopilot:work", "leave_recorded": True, **extra}
                )

    def test_denies_a_junk_session_value_as_proof_of_another_session(self) -> None:
        for junk in (None, "", 5, "  "):
            with self.subTest(session=junk):
                self.assertDenied(
                    {
                        "requested_skill": "autopilot:work",
                        "leave_recorded": True,
                        "session": junk,
                        "leave_session": "s1",
                    }
                )

    def test_denies_a_junk_leave_session_value_as_proof_of_another_session(self) -> None:
        for junk in (None, "", 5, "  "):
            with self.subTest(leave_session=junk):
                self.assertDenied(
                    {
                        "requested_skill": "autopilot:work",
                        "leave_recorded": True,
                        "session": "s1",
                        "leave_session": junk,
                    }
                )

    def test_allows_two_different_non_empty_session_strings(self) -> None:
        self.assertAllowed(
            {
                "requested_skill": "git-ferry:catchup",
                "leave_recorded": True,
                "session": "s2",
                "leave_session": "s1",
            }
        )

    def test_fails_closed_when_a_required_key_is_absent_or_mistyped(self) -> None:
        self.assertFailsClosed({}, "requested_skill")
        self.assertFailsClosed({"ok": True}, "requested_skill")
        self.assertFailsClosed({"leave_recorded": True}, "requested_skill")
        self.assertFailsClosed({"requested_skill": "autopilot:work"}, "leave_recorded")
        for value in (None, "true", 1):
            with self.subTest(leave_recorded=value):
                self.assertFailsClosed(
                    {"requested_skill": "persona:devon", "leave_recorded": value},
                    "leave_recorded",
                )
        for value in (None, 3):
            with self.subTest(requested_skill=value):
                self.assertFailsClosed(
                    {"requested_skill": value, "leave_recorded": False}, "requested_skill"
                )


class DepartureTest(_DutyTestCase):
    duty = GuardDuty.DEPARTURE

    def test_denies_when_no_leave_row_was_written(self) -> None:
        for last, leave in ((1, 5), (4, 9)):
            with self.subTest(last=last, leave=leave):
                self.assertDenied(
                    {
                        "leave_row_written": False,
                        "last_store_write_at": last,
                        "leave_row_at": leave,
                    }
                )

    def test_allows_a_leave_row_written_after_the_last_store_write(self) -> None:
        for last, leave in ((1, 2), (10, 11), (0, 100)):
            with self.subTest(last=last, leave=leave):
                self.assertAllowed(
                    {
                        "leave_row_written": True,
                        "last_store_write_at": last,
                        "leave_row_at": leave,
                    }
                )

    def test_allows_a_leave_row_written_at_the_same_moment(self) -> None:
        self.assertAllowed(
            {"leave_row_written": True, "last_store_write_at": 7, "leave_row_at": 7}
        )

    def test_denies_a_store_write_that_landed_after_the_leave_row(self) -> None:
        for last, leave in ((3, 2), (11, 10), (101, 0)):
            with self.subTest(last=last, leave=leave):
                self.assertDenied(
                    {
                        "leave_row_written": True,
                        "last_store_write_at": last,
                        "leave_row_at": leave,
                    }
                )

    def test_fails_closed_when_a_required_key_is_absent_or_mistyped(self) -> None:
        full = {"leave_row_written": True, "last_store_write_at": 1, "leave_row_at": 2}
        self.assertFailsClosed({}, "leave_row_written")
        self.assertFailsClosed({"ok": True}, "leave_row_written")
        for key in full:
            with self.subTest(missing=key):
                partial = {k: v for k, v in full.items() if k != key}
                self.assertFailsClosed(partial, key)
        for value in (None, "yes", 1):
            with self.subTest(leave_row_written=value):
                self.assertFailsClosed({**full, "leave_row_written": value}, "leave_row_written")


class ContextReinjectionTest(_DutyTestCase):
    duty = GuardDuty.CONTEXT_REINJECTION

    def test_allows_a_present_card_with_content(self) -> None:
        for body in ("card body", "x", "  indented card  \n"):
            with self.subTest(body=body):
                self.assertAllowed({"contract_card_present": True, "contract_card_body": body})

    def test_denies_when_the_card_is_not_present(self) -> None:
        for body in ("card body", ""):
            with self.subTest(body=body):
                self.assertDenied({"contract_card_present": False, "contract_card_body": body})

    def test_denies_a_present_card_with_an_empty_or_blank_body(self) -> None:
        for body in ("", " ", "\n\t  \n"):
            with self.subTest(body=body):
                self.assertDenied({"contract_card_present": True, "contract_card_body": body})

    def test_fails_closed_when_a_required_key_is_absent_or_mistyped(self) -> None:
        self.assertFailsClosed({}, "contract_card_present")
        self.assertFailsClosed({"ok": True}, "contract_card_present")
        self.assertFailsClosed({"contract_card_body": "card body"}, "contract_card_present")
        self.assertFailsClosed({"contract_card_present": True}, "contract_card_body")
        for value in (None, "yes", 1):
            with self.subTest(contract_card_present=value):
                self.assertFailsClosed(
                    {"contract_card_present": value, "contract_card_body": "card body"},
                    "contract_card_present",
                )
        for value in (None, 5, ["card"]):
            with self.subTest(contract_card_body=value):
                self.assertFailsClosed(
                    {"contract_card_present": True, "contract_card_body": value},
                    "contract_card_body",
                )


if __name__ == "__main__":
    unittest.main()

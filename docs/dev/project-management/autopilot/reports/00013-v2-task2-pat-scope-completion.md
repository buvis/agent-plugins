# AP00013 v2 task 2: Pat's omitted review scope, completed

2026-11-03. Cycle 2 of the same review, in the same conversation. No counter
reset, no new review cycle, no file excluded.

## What was omitted and how it was supplied

Cycle 1 (`reviews/00013-v2-task2-pat-partial-01.md`) carried the production
diff plus one sibling test file, and omitted this task's original test diff -
the tests that specify the production code under review. That omission was the
orchestrator's.

The complete scope was supplied to the existing tool-less Sonnet/high session
`29c0b516-5d37-4c52-939e-289e4bf0523c`, resumed with `-R`, as the two labelled
inputs the recovery report mandates, in that order:

1. `docs/dev/tmp/ap00013-v2/task2d/previously-omitted-tests.diff` (19857 bytes,
   the preserved artifact; task base `9dc395e2` through last-reviewed
   `c5ab4eaf`, both recovery test files). Rendered prompt 21086 bytes. Pat
   replied `ACKNOWLEDGED`, preserved as
   `reviews/00013-v2-task2-pat-02-omitted-scope-ack.md`.
2. The `c5ab4eaf..HEAD` delta over all three task-2 production modules, the
   CHANGELOG and both recovery test files, rendered through the installed
   `pat-rerun-prompt.md` with the original MEDIUM verbatim and a truthful
   `UNCHANGED_NOTE`. Rendered prompt 33632 bytes.

### Documented deviation: two messages, not one combined prompt

The card asked for one render carrying the combined `DELTA_DIFF`. Measured, that
is not possible within the installed budget: the preserved omitted diff (19857)
plus the delta at default context (30671) is 50528 bytes of diff alone, before
the template, against a 45000-byte target and a 50000-byte cap. Excluding a file
is forbidden by the same instruction.

Both inputs were therefore supplied as two sequential messages in the SAME
resumed conversation - the order the recovery report specifies ("two explicitly
labelled inputs in this order"), and the only arrangement that satisfies its
"without sending a single oversized prompt" while excluding nothing. The delta
is rendered at one line of context so every changed line of every in-scope file
fits; no changed line and no file was dropped. `autopilot.py` is absent from the
delta because it genuinely has no change in that range (its task-2 changes
landed before `c5ab4eaf` and were reviewed in cycle 1); the `UNCHANGED_NOTE`
says so explicitly rather than letting absence read as exclusion.

## Verdict

The sole MEDIUM (uncaught result-artifact sink errors,
`verification.py:300`) is **resolved**, grounded in the delta: the artifact sink
is opened before `_execute`, an open failure returns `sink-failed` before any
spawn, truncate/write failures map to `sink-write-failed`, close failures to
`sink-close-failed`, and an already-decided write failure is not overridden by a
close failure. Attempt record stamps `medium-retry:fixed`.

No CRITICAL, HIGH or MEDIUM findings. Five LOW findings, parser exit 0, recorded
in `reviews/00013-v2-task2-pat-02.md`. Per the installed ladder, LOW-only
proceeds to task completion. Two are re-emitted unresolved from cycle 1 (the
`_drain` OSError slug at :174, the forwarded `digest` parameter at :199) and
three are new observations on the cleanup fix.

## Carried forward to the completion review, not fixed here

The bounded-correction mandate forbids expansion, and the review ladder says
LOW-only proceeds. Two of the new LOWs are substantive enough that the fresh
completion-review lenses should see them named rather than buried in a list:

- **Ownership window (`verification.py` ~296).** `_open_result_sink` decides
  ownership from `artifact.exists()` taken BEFORE the open, then `_pin_sink_leaf`
  records identity from an `lstat` AFTER the open, via a second descent. The
  pinned inode is therefore not provably the inode this run opened, so a leaf
  created or swapped in between those two steps would be recorded as owned and
  later unlinked. Pat's remedy: take the identity from
  `os.fstat(sink.fileno())` and require the pinned `lstat` to match it, and have
  the opener report creation (an `O_EXCL` attempt) instead of an `exists()`
  pre-check. No test covers this window. This is a hole in the ownership test
  the whole correction rests on, and the strongest candidate for the next
  bounded change.
- **Partial artifact on a write/close failure (`verification.py` ~330).**
  `drop = art is None` means cleanup runs only when no record reached the
  writer. When `_write_artifact` itself fails, a leaf this run created is left
  behind empty or partial, and an existing artifact has already been truncated.
  This predates the cleanup fix (the committed `if art is None` had the same
  shape) and interacts with the committed "an existing artifact keeps its prior
  bytes" contract, so it is not a safe unilateral flip inside a bounded
  correction.

## Separately observed, out of scope

The `unsafe-artifact-path` refusal returns no `reason` key, unlike every other
refusal the gate emits, so `failure_shape` and any caller reading
`report["reason"]` raises `KeyError` on it. Found by Tess while building the
regressions; pre-existing, no live caller breaks today.

"""Pure cap_critical custody proposals.

Port of the pinned `cli/custody.py` pure pieces: the marker entry, its
op_id upsert, the hold-PRD text refresh and the deferred-decision migration
records. Nothing here reads or writes disk, locks, loads markers or journals,
or resolves custody; resolving custody requires the autopilot controller.
Stdlib only.
"""

from __future__ import annotations

import re

# frontmatter's head-line bound minus the two key lines refresh_hold_prd may
# add, so a block that closes within this bound still parses after refresh.
_BLOCK_HEAD_LINES = 20
_HEADING_PATTERNS = (r"#{1,6} Problem Statement\s*$", r"# ")


def upsert_entry(entries: list[dict], entry: dict) -> tuple[list[dict], bool]:
    """New list with `entry` replacing its op_id twin, else appended;
    second value True when appended."""
    op_id = entry["op_id"]
    if any(e.get("op_id") == op_id for e in entries):
        return [entry if e.get("op_id") == op_id else e for e in entries], False
    return [*entries, entry], True


def marker_entry(prd: str, batch: str, op_id: str, detail: str, capture: dict) -> dict:
    """The one custody marker entry: the four scalars plus every capture key
    copied verbatim, as a new dict."""
    return {"prd": prd, "batch": batch, "op_id": op_id, "detail": detail, **capture}


def _notice_prefix(batch: str) -> str:
    return f"> **Custody (cap_critical, batch {batch}):**"


def _refresh_block(lines: list[str], entry: dict) -> list[str]:
    """Replace or append the two custody keys in a frontmatter block that
    closes within _BLOCK_HEAD_LINES; prepend a fresh block otherwise."""
    keys = {
        "critical_on_master": f"critical_on_master: {entry['commit_range']}",
        "ledger": f"ledger: deferred/{entry['batch']}-deferred.json#{entry['op_id']}",
    }
    close = None
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:_BLOCK_HEAD_LINES], start=1):
            if line.strip() == "---":
                close = index
                break
    if close is None:
        return ["---", *keys.values(), "---", *lines]
    body = [keys.pop(line.partition(":")[0].strip(), line) for line in lines[1:close]]
    return [lines[0], *body, *keys.values(), *lines[close:]]


def _insert_notice(lines: list[str], notice: str) -> list[str]:
    """Insert `notice` after the Problem Statement heading, else after the
    first H1, else at the end - one blank line each side."""
    for pattern in _HEADING_PATTERNS:
        for index, line in enumerate(lines):
            if re.match(pattern, line):
                return [*lines[: index + 1], "", notice, "", *lines[index + 1 :]]
    body = lines[:-1] if lines and lines[-1] == "" else lines
    return [*body, "", notice, ""]


def refresh_hold_prd(text: str, entry: dict) -> str:
    """Upsert the custody frontmatter keys and this batch's notice line (the
    detail's whitespace runs collapsed so it stays one line); every other
    byte of `text` is preserved. Idempotent."""
    lines = _refresh_block(text.split("\n"), entry)
    prefix = _notice_prefix(entry["batch"])
    notice = (
        f"{prefix} {' '.join(entry['detail'].split())} Commits {entry['commit_range']} "
        f"({entry['commits']}) are live on {entry['branch']}. "
        "Resolving custody requires the autopilot controller: run autopilot custody resolve."
    )
    if any(line.startswith(prefix) for line in lines):
        lines = [notice if line.startswith(prefix) else line for line in lines]
    else:
        lines = _insert_notice(lines, notice)
    return "\n".join(lines)


def migration_records(snapshot: dict, op_id: str, prd: str) -> list[dict]:
    """One deferred record per dict in snapshot["deferred_decisions"], keyed
    "<op_id>-dd<i>" by its original index; a decision keeps its own type and
    cycle."""
    return [
        {
            **decision,
            "type": decision.get("type", "deferred_decision"),
            "cycle": decision.get("cycle", snapshot.get("cycle")),
            "prd": prd,
            "op_id": f"{op_id}-dd{index}",
        }
        for index, decision in enumerate(snapshot.get("deferred_decisions") or [])
        if isinstance(decision, dict)
    ]

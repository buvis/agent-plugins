"""Group decision-gate findings into rework tasks.

    group(findings) -> [{"name_hint", "critical", "findings"}, ...]

Port of the pinned `rework_groups`. Every critical finding is its own group
and never counts toward the cap. The rest are keyed by file (citation suffix
stripped, `N/A` read as `general`, markdown shared as `prose`). While more
than NON_CRITICAL_CAP non-critical groups remain, `general` merges into the
smallest code group first, then the pair with the deepest shared directory
merges (smallest combined pair, then keys, on a tie); a pair sharing no
directory merges as `mixed`. Output: critical groups in input order, then the
rest by worst severity, size (largest first) and key. Stdlib only.
"""

from __future__ import annotations

import re

NON_CRITICAL_CAP = 4

_CRITICAL = "\U0001f534"
_RANK = {_CRITICAL: 0, "\U0001f7e0": 1, "\U0001f7e1": 2, "⚪": 3}
# Every citation suffix the findings table uses, anchored at the end.
_LINE_SUFFIX = re.compile(r"(?:\s*\(lines?\s+\d[\d,\s-]*\)|:\d+(?:-\d+)?|#L\d+(?:-L?\d+)?)$")
# The table's own "no file" marker, bare or wrapping a citation.
_NOT_APPLICABLE = re.compile(r"n/a(\s*\(.*\))?", re.IGNORECASE)
_NOT_A_MERGE_TARGET = ("general", "prose")


def _citation_free(file: str) -> str:
    """`file` without repeated citation suffixes; any `N/A` shape is
    `general`."""
    key = file
    while True:
        stripped = _LINE_SUFFIX.sub("", key)
        if stripped == key:
            break
        key = stripped
    return "general" if _NOT_APPLICABLE.fullmatch(key) else key


def file_key(file: str) -> str:
    """The group key of a non-critical finding's file."""
    key = _citation_free(file)
    return "prose" if key.endswith(".md") else key


def _dirs(key: str) -> list[str]:
    """Directory components of a group key; a merged key ends with `/`."""
    parts = key.rstrip("/").split("/")
    return parts if key.endswith("/") else parts[:-1]


def _merge_pair(groups: list[dict]) -> tuple[int, int, int]:
    """(shared directory depth, i, j) of the closest pair: deepest shared
    directory, then smallest combined size, then keys."""
    best = None
    for i, a in enumerate(groups):
        for j in range(i + 1, len(groups)):
            b = groups[j]
            shared = 0
            for x, y in zip(_dirs(a["name_hint"]), _dirs(b["name_hint"])):
                if x != y:
                    break
                shared += 1
            pair_keys = sorted([a["name_hint"], b["name_hint"]])
            rank = (-shared, len(a["findings"]) + len(b["findings"]), pair_keys)
            if best is None or rank < best[0]:
                best = (rank, (shared, i, j))
    return best[1]


def _cap(groups: list[dict]) -> list[dict]:
    general = next((g for g in groups if g["name_hint"] == "general"), None)
    targets = [g for g in groups if g["name_hint"] not in _NOT_A_MERGE_TARGET]
    if len(groups) > NON_CRITICAL_CAP and general and targets:
        target = min(targets, key=lambda g: (len(g["findings"]), g["name_hint"]))
        merged = {**target, "findings": target["findings"] + general["findings"]}
        groups = [merged if g is target else g for g in groups if g is not general]
    while len(groups) > NON_CRITICAL_CAP:
        code = [g for g in groups if g["name_hint"] != "prose"]
        if len(code) < 2:
            # Fold `prose` into the one remaining code group; unreachable
            # while NON_CRITICAL_CAP is 4.
            if not code:
                break
            prose = next(g for g in groups if g["name_hint"] == "prose")
            groups = [{**code[0], "findings": code[0]["findings"] + prose["findings"]}]
            break
        shared, i, j = _merge_pair(code)
        a, b = code[i], code[j]
        prefix = _dirs(a["name_hint"])[:shared]
        merged = {
            "name_hint": "/".join(prefix) + "/" if prefix else "mixed",
            "critical": False,
            "findings": a["findings"] + b["findings"],
        }
        groups = [g for g in groups if g is not a and g is not b] + [merged]
    return groups


def group(findings: list[dict]) -> list[dict]:
    """Group `findings` into rework tasks without mutating them. Each finding
    needs a string `file` and a severity emoji; ValueError otherwise."""
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError(f"finding must be an object: {finding!r}")
        if not isinstance(finding.get("file"), str) or finding.get("severity") not in _RANK:
            raise ValueError(f"finding needs a file string and a severity emoji: {finding!r}")
    critical = []
    by_key: dict[str, list[dict]] = {}
    for finding in findings:
        if finding["severity"] == _CRITICAL:
            key = _citation_free(finding["file"])
            critical.append({"name_hint": key, "critical": True, "findings": [finding]})
            continue
        by_key.setdefault(file_key(finding["file"]), []).append(finding)
    rest = [
        {"name_hint": key, "critical": False, "findings": items}
        for key, items in by_key.items()
    ]
    # Merges concatenate buckets; restore input order inside every group.
    position = {id(f): n for n, f in enumerate(findings)}
    rest = [
        {**g, "findings": sorted(g["findings"], key=lambda f: position[id(f)])}
        for g in _cap(rest)
    ]
    rest.sort(
        key=lambda g: (
            min(_RANK[f["severity"]] for f in g["findings"]),
            -len(g["findings"]),
            g["name_hint"],
        )
    )
    return critical + rest

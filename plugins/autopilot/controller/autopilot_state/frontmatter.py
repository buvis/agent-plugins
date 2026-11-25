"""Flat, bounded PRD frontmatter parsing."""

from __future__ import annotations

from collections.abc import Collection, Mapping

type FrontmatterValue = str | int | bool

_HEAD_LINES = 20
_ENUMS: dict[str, tuple[str, tuple[str, ...], str]] = {
    "catchup": ("catchup_mode", ("run", "skip", "force"), "run"),
    "design": ("design_mode", ("run", "skip"), "run"),
}
_REWORK_CAP_DEFAULT = 2
_OPT_INS: dict[str, tuple[str, str, FrontmatterValue]] = {
    "design_gate": ("design_gate", "user", "user"),
    "pause_on_ambiguity": ("pause_on_ambiguity", "true", True),
}
_ELIGIBILITY_KEY = "eligibility"
_QUOTES = "\"'"

MALFORMED_WARNING = (
    "ovcaq: PRD frontmatter malformed; defaulting catchup_mode=run, "
    "rework_cap=2, design_mode=run"
)


def defaults() -> dict[str, FrontmatterValue]:
    """Return effective values for a PRD with no declarations."""
    fields: dict[str, FrontmatterValue] = {
        state_key: default for state_key, _allowed, default in _ENUMS.values()
    }
    fields["rework_cap"] = _REWORK_CAP_DEFAULT
    return fields


def _block(text: str) -> list[str] | None:
    lines = text.splitlines()[:_HEAD_LINES]
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    return None


def _pairs(body: list[str]) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in body:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        pairs[key.strip()] = value.strip()
    return pairs


def declarations(text: str) -> dict[str, str]:
    """Return the raw declarations of the first frontmatter block only.

    A `key: value` line in the PRD body is not a declaration and never appears
    here, so a caller capturing a declared value verbatim cannot pick one up.
    """
    body = _block(text)
    return {} if body is None else _pairs(body)


def _positive_integer(raw: str) -> int | None:
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _apply_enums(
    declared: Mapping[str, str],
    fields: dict[str, FrontmatterValue],
    warnings: list[str],
) -> None:
    for prd_key, (state_key, allowed, default) in _ENUMS.items():
        if prd_key not in declared:
            continue
        value = declared[prd_key]
        if value in allowed:
            fields[state_key] = value
        else:
            warnings.append(
                f"ovcaq: PRD frontmatter {prd_key}={value!r} is not one of "
                f"{'/'.join(allowed)}; defaulting to {default}"
            )


def parse(
    text: str,
    *,
    available_tiers: Collection[str] | None = None,
) -> tuple[dict[str, FrontmatterValue], list[str]]:
    """Parse the first frontmatter block into neutral effective fields."""
    fields = defaults()
    body = _block(text)
    if body is None:
        return fields, [MALFORMED_WARNING]

    declared = _pairs(body)
    warnings: list[str] = []
    _apply_enums(declared, fields, warnings)

    if "rework_cap" in declared:
        cap = _positive_integer(declared["rework_cap"])
        if cap is None:
            warnings.append(
                "ovcaq: PRD frontmatter "
                f"rework_cap={declared['rework_cap']!r} is not a positive integer; "
                f"defaulting to {_REWORK_CAP_DEFAULT}"
            )
        else:
            fields["rework_cap"] = cap

    for prd_key, (state_key, marker, opt_in_value) in _OPT_INS.items():
        if declared.get(prd_key) == marker:
            fields[state_key] = opt_in_value

    tier = declared.get("default_model")
    if tier is not None:
        if available_tiers is not None and tier in available_tiers:
            fields["tier"] = tier
        else:
            warnings.append(
                f"ovcaq: PRD frontmatter tier {tier!r} is unavailable; "
                "applying no tier floor"
            )

    return fields, warnings


def overwrite_warnings(
    existing: Mapping[str, object],
    effective: Mapping[str, FrontmatterValue],
) -> list[str]:
    """Report only effective values that replace a different prior value."""
    return [
        f"ovcaq: PRD frontmatter reset {key} {existing[key]} -> {value}"
        for key, value in effective.items()
        if key in existing and existing[key] != value
    ]


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in _QUOTES:
        return value[1:-1]
    return value


def command_for(prd_text: str) -> str | None:
    """Return the PRD's eligibility command, or None when it declares none."""
    body = _block(prd_text)
    if body is None:
        return None
    return _unquote(_pairs(body).get(_ELIGIBILITY_KEY, "").strip()) or None

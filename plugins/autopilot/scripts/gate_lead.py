"""Strip a finding-shaped line's lead up to its severity emoji.

Port of the pinned `gate_lead._strip_lead`. A lead is any run of characters in
Unicode categories P, S, Z, C or M (bare Ps/Pe brackets excluded), the Hangul
Filler U+3164, and the multi-character shapes: ordinals, checkboxes, HTML
comments, `<details>` blocks, inline code and markdown links. This is lexical
classification only, not review acceptance. Stdlib only.
"""

from __future__ import annotations

import re
import unicodedata

_SEVERITY_EMOJI = frozenset("\U0001f534\U0001f7e0\U0001f7e1⚪")
_NON_ALNUM_CATEGORIES = ("P", "S", "Z", "C", "M")
# Brackets are consumed only through the explicit shapes below, never one at
# a time, so a stray "(x)" does not expose the letter behind it.
_BRACKET_CATEGORIES = ("Ps", "Pe")
# Hangul Filler is category Lo but renders invisible.
_INVISIBLE_LEAD_EXTRA = frozenset("ㅤ")
# Unanchored on purpose: `.match(line, i)` anchors at `i`, `^` would not.
_LEAD_SHAPE_RES = (
    re.compile(r"\d+[.)]|[A-Za-z]+\)|\(\d+\)"),
    re.compile(r"\[[ xX]?\]"),
    re.compile(r"<!--.*?-->"),
    re.compile(r"<details>.*?</details>", re.IGNORECASE | re.DOTALL),
    re.compile(r"`[^`\n]*`"),
    re.compile(r"\[[^\]\n]*\]\([^)\n]*\)"),
)


def strip_lead(line: str) -> str:
    """`line` without its lead; may be empty."""
    i, n = 0, len(line)
    while i < n:
        for lead_re in _LEAD_SHAPE_RES:
            m = lead_re.match(line, i)
            if m:
                i = m.end()
                break
        else:
            ch = line[i]
            if ch in _SEVERITY_EMOJI:
                break
            category = unicodedata.category(ch)
            if ch in _INVISIBLE_LEAD_EXTRA or (
                category[0] in _NON_ALNUM_CATEGORIES
                and category not in _BRACKET_CATEGORIES
            ):
                i += 1
                continue
            break
    return line[i:]

"""The structural-rule checks of 00005 (T-071), registered in CHECKS of checks.py."""

from __future__ import annotations

import re
from functools import partial
from pathlib import Path

from .canonical import FENCE, canonical
from .checks import SPEC_PHASES, Context, check, error, read_text, rel
from .findings import Finding, finding
from .spec_text import prose, requirement_blocks
from .state import ORDERS, artifact_paths, spec_phase, workflow_order
from .status import unaccepted_markers

INLINE_CODE = re.compile(r"`[^`]*`")
PLACEHOLDER = re.compile(r"(?<![\w/])(?:TBD|TODO|N/A)(?![\w/])|\?\?\?")
NOT_APPLICABLE = re.compile(r"^\s*Not applicable:(.*)$")
WIKI_LINK = re.compile(r"\[\[[^\]\n]+\]\]")
# A slash after a word, a template slot (`<root>/`), or a glob (`*/`) starts no
# machine path, nor does a dot folder (`/.claude/` is a gitignore anchor).
# ponytail: no allow list for legitimate system paths such as /dev/null; add one
# when a real spec needs it (the Plan A ruling on RPB-C3 leaves room for it).
MACHINE_PATH = re.compile(
    r"(?<![\w.~:/\\\])>*])"
    r"(?:~[\w.-]*/[^\s`)]*|\$\{?HOME\}?/[^\s`)]*|/\w[\w.-]*(?:/[\w.-]+)*/?"
    r"|[A-Za-z]:\\[^\s`)]*)",
)


def existing_artifacts(ctx: Context) -> list[tuple[Path, str]]:
    """(path, text) of each canonical artifact that can be read."""
    paths = artifact_paths(ctx.spec_dir, ctx.state).values()
    return [(path, text) for path in paths if (text := read_text(path)) is not None]


@check("placeholders", SPEC_PHASES)
def placeholders(ctx: Context) -> list[Finding]:
    """TBD, TODO, ???, or N/A outside code; Not applicable: only in design.md, with a reason."""
    findings = []
    for path, text in existing_artifacts(ctx):
        found = partial(error, ctx, path, "placeholders")
        for n, line in prose(text):
            bare = INLINE_CODE.sub("", line)
            for token in PLACEHOLDER.findall(bare):
                message = f"line {n}: placeholder {token}"
                findings.append(
                    found(message, "Write the content, or mark a guess (guess).")
                )
            reason = NOT_APPLICABLE.match(bare)
            if reason and path.name != "design.md":
                message = f"line {n}: Not applicable: belongs to design.md only"
                fix = "Leave out the section that does not apply."
                findings.append(found(message, fix))
            elif reason and not reason[1].strip():
                findings.append(
                    found(
                        f"line {n}: Not applicable: gives no reason",
                        "Write the reason.",
                    )
                )
    return findings


@check("open-markers", SPEC_PHASES)
def open_markers(ctx: Context) -> list[Finding]:
    """Upstream markers that the phase artifact's approval does not accept by name (WF-002.7)."""
    chain = (*ORDERS[workflow_order(ctx.spec_dir, ctx.state)], "tasks")
    phase = (
        ctx.phase
        if ctx.phase in SPEC_PHASES
        else spec_phase(ctx.spec_dir, ctx.state)[1]
    )
    own = phase if phase in chain else "tasks"
    paths = artifact_paths(ctx.spec_dir, ctx.state)
    fix = (
        f"Resolve it, or record the developer's acceptance by name on the "
        f"{paths[own].name} approval."
    )
    return [
        error(
            ctx,
            paths[name],
            "open-markers",
            f"marker not accepted for the {paths[own].name} approval: {line.strip()}",
            fix,
        )
        for name, line in unaccepted_markers(
            ctx.state, own, chain[: chain.index(own)], paths
        )
    ]


@check("portable-links", SPEC_PHASES)
def portable_links(ctx: Context) -> list[Finding]:
    """Home-directory and absolute paths, and [[...]] links: they break on another machine.

    A path counts in inline code too; a link does not, since inline code names its syntax.
    """
    findings = []
    for path, text in existing_artifacts(ctx):
        for n, line in prose(text):
            hits = [
                *MACHINE_PATH.finditer(line),
                *WIKI_LINK.finditer(INLINE_CODE.sub("", line)),
            ]
            for match in hits:
                findings.append(
                    finding(
                        rel(ctx, path),
                        "portable-links",
                        f"line {n}: {match[0]} does not resolve on another machine",
                        "Use a repository-relative path, or name the source in words.",
                        "warning",
                    ),
                )
    return findings


@check("closed-fences", SPEC_PHASES)
def closed_fences(ctx: Context) -> list[Finding]:
    """A fence that never closes hides the rest of the file from the hash and the scans."""
    findings = []
    for path, text in existing_artifacts(ctx):
        fence, start = None, 0
        for n, line in enumerate(canonical(text).split("\n"), start=1):
            match = FENCE.match(line)
            if fence is None and match:
                fence, start = match[1], n
            elif (
                fence
                and match
                and match[1][0] == fence[0]
                and len(match[1]) >= len(fence)
            ):
                fence = None
        if fence:
            message = f"line {start}: code fence {fence} never closes"
            fix = f"Close it with {fence} on its own line."
            findings.append(error(ctx, path, "closed-fences", message, fix))
    return findings


@check("requirement-source", SPEC_PHASES)
def requirement_source(ctx: Context) -> list[Finding]:
    """A requirement with no Source: line; a warning, since Kiro writes none (VAL-001.12)."""
    path = artifact_paths(ctx.spec_dir, ctx.state)["requirements"]
    text = read_text(path)
    if path.name != "requirements.md" or text is None:
        return []
    return [
        finding(
            rel(ctx, path),
            "requirement-source",
            f"{ident} has no Source: line",
            "Add Source: with the idea, the Q&A entry, or the discovery finding it came from.",
            "warning",
        )
        for ident, block in requirement_blocks(text).items()
        if not any(line.startswith("Source:") for line in block)
    ]

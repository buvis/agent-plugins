"""Spec dependencies: the `Depends on:` grammar, resolution, and the implementation gate."""

from __future__ import annotations

import re
from pathlib import Path

from .canonical import canonical, scan_lines
from .state import StateError, load_state, spec_phase

RULE = "spec-dependencies"
NUMBER = re.compile(r"\d{5}")
FOLDER = re.compile(r"folder:(.*)")
FIX = "Write one unindented `Depends on:` line of five-digit numbers or folder:<name> items."


def finding(file: str, message: str, fix: str = FIX) -> dict[str, str]:
    return {
        "level": "error",
        "file": file,
        "rule": RULE,
        "message": message,
        "fix": fix,
    }


def valid_item(item: str) -> bool:
    if NUMBER.fullmatch(item):
        return True
    match = FOLDER.fullmatch(item)
    name = match[1] if match else ""
    return bool(name) and name not in (".", "..") and not any(c in name for c in ",/\\")


def parse_depends_on(
    text: str,
    *,
    bugfix: bool,
    file: str = "requirements.md",
) -> tuple[list[str], list[dict[str, str]]]:
    """The declared references, and declaration errors. Fences and indented fields declare nothing."""
    section: str | None = None
    placed: list[str] = []
    findings: list[dict[str, str]] = []
    for line, in_fence, _ in scan_lines(canonical(text)):
        if in_fence:
            continue
        if line.startswith("## "):
            section = line
        if not line.startswith("Depends on:"):
            continue
        allowed = section == "## Introduction" if bugfix else section is None
        if allowed:
            placed.append(line)
        else:
            where = (
                "the end of ## Introduction"
                if bugfix
                else "the header, before the first ## heading"
            )
            findings.append(
                finding(file, f"misplaced declaration: {line}", f"Move it to {where}."),
            )
    if len(placed) > 1:
        findings.append(
            finding(
                file,
                f"repeated declaration: {placed[1]}",
                "Keep one Depends on: line.",
            ),
        )
    if not placed:
        return [], findings
    value = placed[0].removeprefix("Depends on:").strip()
    if not value:
        findings.append(
            finding(
                file,
                "empty declaration",
                "Name a prerequisite or delete the line.",
            ),
        )
        return [], findings
    refs: list[str] = []
    for item in (part.strip() for part in value.split(",")):
        if not valid_item(item):
            findings.append(finding(file, f"unsupported reference {item!r}"))
        elif item not in refs:
            refs.append(item)
    return refs, findings


def requirements_file(spec_dir: Path) -> Path:
    bugfix = spec_dir / "bugfix.md"
    return bugfix if bugfix.exists() else spec_dir / "requirements.md"


def resolve_reference(ref: str, specs_dir: Path) -> tuple[Path | None, str | None]:
    """(target folder, None) or (None, reason) for one reference, in the specs folder only."""
    if not specs_dir.is_dir():
        return None, "missing target: no specs folder"
    folders = sorted(p for p in specs_dir.iterdir() if p.is_dir())
    if NUMBER.fullmatch(ref):
        found = [p for p in folders if p.name == ref or p.name.startswith(f"{ref}-")]
    else:
        found = [p for p in folders if p.name == ref.removeprefix("folder:")]
    if not found:
        return None, "missing target"
    if len(found) > 1:
        return None, "ambiguous target: " + ", ".join(p.name for p in found)
    if not found[0].resolve().is_relative_to(specs_dir.resolve()):
        return None, "target resolves outside the specs folder"
    return found[0], None


def declared(spec_dir: Path) -> tuple[list[str], list[dict[str, str]], str | None]:
    """(references, declaration findings, unreadable reason) of one spec."""
    path = requirements_file(spec_dir)
    if not path.exists():
        return [], [], None
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [], [], f"unreadable target: {error}"
    refs, findings = parse_depends_on(
        text,
        bugfix=path.name == "bugfix.md",
        file=path.name,
    )
    return refs, findings, None


def completeness(target: Path) -> str | None:
    """Why a direct prerequisite does not count as complete, or None."""
    try:
        _, phase = spec_phase(target, load_state(target))
    except StateError as error:
        return f"state cannot be reconciled: {error}"
    except (OSError, UnicodeDecodeError) as error:
        return f"unreadable target: {error}"
    return None if phase == "complete" else f"incomplete prerequisite (phase {phase})"


def dependency_blockers(spec_dir: Path, specs_dir: Path) -> list[dict[str, str]]:
    """Every reason the implementation gate of spec_dir is closed by its dependencies.

    Each reachable spec is read once and never written; phase and approvals are untouched.
    """
    blockers: list[dict[str, str]] = []
    done: set[Path] = set()

    def block(spec: Path, reference: str, reason: str, **extra: str) -> None:
        blockers.append(
            {
                "gate": "implementation",
                "spec": spec.name,
                "reference": reference,
                "reason": reason,
                **extra,
            },
        )

    def visit(node: Path, stack: list[Path]) -> list[str]:
        refs, findings, unreadable = declared(node)
        if unreadable:
            block(node, "Depends on:", unreadable)
        for item in findings:
            block(node, "Depends on:", item["message"])
        targets: list[tuple[str, Path]] = []
        for ref in refs:
            target, reason = resolve_reference(ref, specs_dir)
            if target is None:
                block(node, ref, reason or "missing target")
            elif target.resolve() not in [t.resolve() for _, t in targets]:
                targets.append((ref, target))
        on_stack = [s.resolve() for s in stack]
        for ref, target in targets:
            if target.resolve() == node.resolve():
                block(node, ref, "self-reference")
            elif target.resolve() in on_stack:
                names = [s.name for s in stack[on_stack.index(target.resolve()) :]]
                block(node, ref, "cycle", path=" → ".join([*names, target.name]))
            elif target.resolve() not in done:
                visit(target, [*stack, target])
        done.add(node.resolve())
        return [ref for ref, _ in targets]

    direct = visit(spec_dir, [spec_dir])
    for ref in direct:
        target, _ = resolve_reference(ref, specs_dir)
        if target is not None and target.resolve() != spec_dir.resolve():
            why = completeness(target)
            if why:
                block(spec_dir, ref, why)
    return blockers

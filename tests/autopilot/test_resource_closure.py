"""Script closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GATE_SIZE = 742
GATE_SHA = "2ea4600b2ec6756640e2e23a8d761160afc889c0a3c6af0caa6fac6d0edaec75"
SCRIPT = re.compile(r"(?:<plugin root>)?[A-Za-z0-9_./${}~+-]+\.(?:py|sh)\b")
COMMAND = re.compile(r"\b(?:python[23]?|bash|sh|pytest)(?:\s+-[A-Za-z]+)*$")
NAMED = set("""
await_reviewer_outputs.py card.py check_review_file.py
compute_mech_facts.py consolidate_findings.py detect_tautological_tests.py
fablectl.py fast_track_plan.py parse_review.py
record_dispatch.py render_prompt.py
""".split())


def source_text(p: Path) -> str:
    data = p.read_bytes()
    if p.name == "SKILL.md":
        end = data.index(b"\n---\n", 4) + 5
        if hashlib.sha256(data[end:end + GATE_SIZE]).hexdigest() == GATE_SHA:
            data = data[:end] + data[end + GATE_SIZE:]
    return data.decode()


def dependencies(pkg: Path) -> set[tuple[str, int, str]]:
    found = set()
    for p in sorted(p for p in pkg.rglob("*") if p.is_file()):
        src = p.relative_to(pkg).as_posix()
        try:
            lines = source_text(p).splitlines()
        except UnicodeDecodeError:
            continue
        worked = example = False
        for n, line in enumerate(lines, 1):
            if line.startswith("```"):
                example = not example if example else worked and line == "```markdown"
                worked = False
                continue
            if example:
                continue
            if line.strip():
                worked = line.strip() == "## A worked card"
            for match in SCRIPT.finditer(line):
                if re.search(r'"source_path"\s*:\s*"$', line[:match.start()]):
                    continue
                ref = match.group()
                prefix = line[:match.start()].rstrip("` ")
                cmd = (COMMAND.search(prefix)
                       or re.search(r"(?i)\b(?:run|invoke|execute|call)(?: the)?$", prefix)
                       or (match.start() and line[match.start() - 1] == "`"
                           and re.match(r"\s+(?:--|<|\$)", line[match.end():])))
                pos = sum(map(len, lines[:n-1])) + n - 1 + match.start()
                prose = next(s.group() for s in re.finditer(
                    r"(?s).+?(?:[.!?](?=\s)|\n\s*\n|$)", "\n".join(lines)) if s.start() <= pos < s.end())
                cite = (Path(ref).name.startswith("test_") or re.search(
                    r"decision model|does not use|hand-maintained model", prose))
                if cite and not cmd and "${CLAUDE_PLUGIN_ROOT}/" not in ref:
                    continue
                if ("${CLAUDE_PLUGIN_ROOT}/" in ref
                        or "/scripts/" in ref or ref.startswith("scripts/")
                        or cmd):
                    found.add((src, n, ref))
    return found


def inside(pkg: Path, ref: str) -> Path | None:
    p = pkg.parent.parent / ref
    return p if p.resolve().is_relative_to(pkg.resolve()) else None


def closure_errors(package: Path, edges: list[dict]) -> list[str]:
    index = {}
    for edge in edges:
        index.setdefault((edge.get("source_path"), edge.get("source_line"),
                            edge["reference"]), []).append(edge)
    errors = []
    for src, line, ref in sorted(dependencies(package)):
        tag = f"{src}:{line}: {ref}"
        rows = index.get((src, line, ref), [])
        if len(rows) != 1:
            errors.append(f"{tag}: edge count {len(rows)}")
            continue
        edge = rows[0]
        kind = edge["kind"]
        if kind == "packaged-resource":
            file = inside(package, edge.get("destination_path", ""))
            if file is None or not file.is_file() or file.name != Path(ref).name:
                errors.append(f"{tag}: missing/escaping script")
        elif kind == "external-capability":
            gate = inside(package, edge.get("gate_entry_point", ""))
            if not all(edge.get(k, "").strip() for k in ("capability", "failure_rule")):
                errors.append(f"{tag}: missing capability/failure")
            if gate is None or not gate.is_file() or gate.name != "SKILL.md":
                errors.append(f"{tag}: missing/escaping gate")
            elif source_text(gate) == gate.read_bytes().decode():
                errors.append(f"{tag}: bad gate")
        else:
            errors.append(f"{tag}: script classified {kind}")
        if not edge.get("failure_rule", "").strip() and kind == "packaged-resource":
            errors.append(f"{tag}: missing failure rule")
    return errors


class ResourceClosureTest(unittest.TestCase):
    def test_whole_tree_closure(self) -> None:
        edges = json.loads((ROOT / "tools/autopilot/source-map.json").read_text())["resource_edges"]
        errors = closure_errors(ROOT / "plugins/autopilot", edges)
        self.assertFalse(errors, f"{len(errors)} defects: {errors[:12]}")

    def test_named_and_discovered_helpers(self) -> None:
        names = {Path(ref).name for _, _, ref in dependencies(ROOT / "plugins/autopilot")}
        self.assertTrue((NAMED | {"record_item.py"}).issubset(names))

    def test_dependency_mutations(self) -> None:
        eq, yes = self.assertEqual, self.assertTrue
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "plugins/p"
            skill = pkg / "skills/e/SKILL.md"
            skill.parent.mkdir(parents=True)
            data = (ROOT / "plugins/autopilot/skills/work/SKILL.md").read_bytes()
            end = data.index(b"\n---\n", 4) + 5
            prefix = b"---\nname: e\n---\n" + data[end:end + GATE_SIZE]
            ref = "${CLAUDE_PLUGIN_ROOT}/skills/e/scripts/x.py"
            skill.write_bytes(prefix + f"python3 {ref}\n".encode())
            edge = {
                "source_path": "skills/e/SKILL.md", "source_line": 4,
                "reference": ref, "kind": "external-capability",
                "capability": "test", "failure_rule": "stop",
                "gate_entry_point": "plugins/p/skills/e/SKILL.md",
            }
            eq(closure_errors(pkg, [edge]), [])
            yes(closure_errors(pkg, []))
            for field, value in (("kind", "informational-provenance"),
                                 ("gate_entry_point", "plugins/p/../../outside/SKILL.md"),
                                 ("capability", ""), ("failure_rule", ""),
                                 ("kind", "packaged-resource")):
                with self.subTest(field=field):
                    yes(closure_errors(pkg, [edge | {field: value}]))
            for name in sorted(NAMED | {"record_item.py"}):
                with self.subTest(helper=name):
                    skill.write_bytes(prefix + f"python3 scripts/{name}\n".encode())
                    eq(len(dependencies(pkg)), 1)
                    yes(closure_errors(pkg, []))
            skill.write_bytes(prefix + b"python3 scripts/z.py\n")
            yes(closure_errors(pkg, [edge]))
            (pkg / "README.md").write_text(
                "scripts/x.py\nComparison: x.py.\nHistory: x.py.\n"
                "python3 x.py\nRun `x.py`\n`x.py <x>`\npython3 z.py\n"
                "does not use x.py.\nscripts/x.py\n"
                "```markdown\npython3 x.py\n```\n"
                "## A worked card\n\n```markdown\npython3 x.py\n```\n"
                "python3 x.py\nA helper `scripts/c.py`\nthis path does not use.\n")
            eq({n for src, n, _ in dependencies(pkg) if src == "README.md"},
               {1, 4, 5, 6, 7, 9, 11, 18})
            asset = pkg / "runtime.json"
            asset.write_text('{"source_path":"scripts/p.py","command":"python3 scripts/r.py"}')
            eq({r for src, _, r in dependencies(pkg) if src == asset.name},
               {"scripts/r.py"})
            yes(any(asset.name in e for e in closure_errors(pkg, [])))


if __name__ == "__main__":
    unittest.main()

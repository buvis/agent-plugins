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
NAMED = {
    "consolidate_findings.py", "compute_mech_facts.py", "render_prompt.py",
    "record_dispatch.py", "detect_tautological_tests.py", "check_review_file.py",
    "await_reviewer_outputs.py", "fast_track_plan.py", "card.py", "fablectl.py",
    "parse_review.py",
}


def source_text(path: Path) -> str:
    data = path.read_bytes()
    if path.name == "SKILL.md":
        end = data.index(b"\n---\n", 4) + 5
        gate = data[end:end + GATE_SIZE]
        if hashlib.sha256(gate).hexdigest() == GATE_SHA:
            data = data[:end] + data[end + GATE_SIZE:]
    return data.decode()


def dependencies(package: Path) -> set[tuple[str, int, str]]:
    expected = set()
    for path in sorted(package.rglob("*.md")):
        source = path.relative_to(package).as_posix()
        lines = source_text(path).splitlines()
        example = False
        for number, line in enumerate(lines, 1):
            if line.startswith("```markdown"):
                example = True
            elif line.startswith("```"):
                example = False
            if example:
                continue
            for match in SCRIPT.finditer(line):
                reference = match.group()
                prefix = line[:match.start()].rstrip("` ")
                command = COMMAND.search(prefix)
                context = " ".join(lines[max(0, number - 2):number + 2])
                citation = (Path(reference).name.startswith("test_")
                            or "decision model" in context or "does not use" in context
                            or "hand-maintained model" in context)
                if citation and not command and "${CLAUDE_PLUGIN_ROOT}/" not in reference:
                    continue
                if ("${CLAUDE_PLUGIN_ROOT}/" in reference
                        or "/scripts/" in reference or reference.startswith("scripts/")
                        or command or re.search(r"(?i)\b(?:run|invoke|execute|call)(?: the)?$", prefix)
                        or (match.start() > 0 and line[match.start() - 1] == "`"
                            and re.match(r"\s+(?:--|<|\$)", line[match.end():]))):
                    expected.add((source, number, reference))
    return expected


def inside(package: Path, reference: str) -> Path | None:
    path = package.parent.parent / reference
    return path if path.resolve().is_relative_to(package.resolve()) else None


def closure_errors(package: Path, edges: list[dict]) -> list[str]:
    indexed = {}
    for edge in edges:
        key = (edge.get("source_path"), edge.get("source_line"), edge["reference"])
        indexed.setdefault(key, []).append(edge)
    errors = []
    for source, line, reference in sorted(dependencies(package)):
        label = f"{source}:{line}: {reference}"
        rows = indexed.get((source, line, reference), [])
        if len(rows) != 1:
            errors.append(f"{label}: edge count {len(rows)}")
            continue
        edge = rows[0]
        kind = edge["kind"]
        if kind == "packaged-resource":
            target = inside(package, edge.get("destination_path", ""))
            if target is None or not target.is_file() or target.name != Path(reference).name:
                errors.append(f"{label}: packaged script missing or escaping")
        elif kind == "external-capability":
            gate = inside(package, edge.get("gate_entry_point", ""))
            if not edge.get("capability", "").strip() or not edge.get("failure_rule", "").strip():
                errors.append(f"{label}: missing capability/failure rule")
            if gate is None or not gate.is_file() or gate.name != "SKILL.md":
                errors.append(f"{label}: unavailable gate missing or escaping")
            else:
                data = gate.read_bytes()
                end = data.index(b"\n---\n", 4) + 5
                if hashlib.sha256(data[end:end + GATE_SIZE]).hexdigest() != GATE_SHA:
                    errors.append(f"{label}: gate not unconditional")
        else:
            errors.append(f"{label}: active script classified {kind}")
        if not edge.get("failure_rule", "").strip() and kind == "packaged-resource":
            errors.append(f"{label}: missing packaged failure rule")
    return errors


class ResourceClosureTest(unittest.TestCase):
    def test_whole_tree_closure(self) -> None:
        edges = json.loads((ROOT / "tools/autopilot/source-map.json").read_text())["resource_edges"]
        errors = closure_errors(ROOT / "plugins/autopilot", edges)
        self.assertEqual(errors[:12], [], f"{len(errors)} closure defects; first 12 shown")

    def test_named_and_discovered_helpers(self) -> None:
        names = {Path(ref).name for _, _, ref in dependencies(ROOT / "plugins/autopilot")}
        self.assertTrue((NAMED | {"record_item.py"}).issubset(names))

    def test_dependency_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "plugins/autopilot"
            skill = package / "skills/example/SKILL.md"
            skill.parent.mkdir(parents=True)
            shipped = ROOT / "plugins/autopilot/skills/work/SKILL.md"
            data = shipped.read_bytes()
            end = data.index(b"\n---\n", 4) + 5
            header = b"---\nname: example\n---\n"
            skill.write_bytes(header + data[end:end + GATE_SIZE]
                              + b"python3 ${CLAUDE_PLUGIN_ROOT}/skills/example/scripts/new_helper.py\n")
            reference = "${CLAUDE_PLUGIN_ROOT}/skills/example/scripts/new_helper.py"
            edge = {
                "source_path": "skills/example/SKILL.md", "source_line": 4,
                "reference": reference, "kind": "external-capability",
                "capability": "unavailable test helper", "failure_rule": "stop",
                "gate_entry_point": "plugins/autopilot/skills/example/SKILL.md",
            }
            self.assertEqual(closure_errors(package, [edge]), [])
            self.assertTrue(closure_errors(package, []))
            for field, value in (("kind", "informational-provenance"),
                                 ("gate_entry_point", "plugins/autopilot/../../outside/SKILL.md"),
                                 ("capability", ""), ("failure_rule", ""),
                                 ("kind", "packaged-resource")):
                with self.subTest(field=field):
                    changed = edge.copy()
                    changed[field] = value
                    self.assertTrue(closure_errors(package, [changed]))
            for name in sorted(NAMED | {"record_item.py"}):
                with self.subTest(helper=name):
                    skill.write_bytes(header + data[end:end + GATE_SIZE]
                                      + f"python3 scripts/{name}\n".encode())
                    self.assertEqual(len(dependencies(package)), 1)
                    self.assertTrue(closure_errors(package, []))
            skill.write_bytes(header + data[end:end + GATE_SIZE]
                              + b"python3 scripts/previously_unknown_helper.py\n")
            self.assertTrue(closure_errors(package, [edge]))
            note = package / "README.md"
            note.write_text("scripts/novel.py\nComparison: novel.py.\nHistory: novel.py.\n"
                            "python3 novel.py\nRun `novel.py`\n`novel.py <x>`\npython3 unknown.py\n")
            self.assertEqual({n for src, n, _ in dependencies(package) if src == "README.md"},
                             {1, 4, 5, 6, 7})


if __name__ == "__main__":
    unittest.main()

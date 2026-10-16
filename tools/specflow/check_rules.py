"""Rule inventory checks: every approved port-plan row and required criterion reaches a rule, its file, and its check.

Run from the repository root:

    python3 tools/specflow/check_rules.py [--area AREA[,AREA...]]

Prints one `error: <subject>: <message>` line per failure, one line per plan
with the rows it read, and one `<criterion> -> <rule> -> <check>` row per
covered pair. Exit 0 on a pass, 1 on a failure, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

# Before the helper is imported, so a run leaves no __pycache__ in the package.
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(
    0, str(HERE.parents[1] / "plugins/specflow/skills/spec-workflow/scripts")
)

from specflow_helper.checks import CHECKS
from specflow_helper.schema import check_schema
from specflow_helper.spec_text import prose

RULES = Path("tools/specflow/rules")
SKILLS = Path("plugins/specflow/skills")
WORKFLOW = SKILLS / "spec-workflow"
EVALS = Path("tests/specflow/evals")
EVAL_SCHEMAS = HERE.parents[1] / EVALS / "schemas"
HEADER = [
    "id",
    "source skill",
    "phase",
    "row",
    "classification",
    "reason",
    "code-only",
    "evidence",
]
CLASSES = ("port", "redesign", "drop", "struck")
CELL = re.compile(r"(?<!\\)\|")
CRITERION = re.compile(r"^[A-Z]+-[0-9]{3}\.[0-9]+$")
PLAN_SOURCE = re.compile(r"^([A-Z]):(.+)$")
PLAN_KEY = re.compile(r"[A-CE-QS-Z]")  # D and R name the decision and requirement forms
MD_TAG = re.compile(r"^\s*- \[(SR-[A-Z]{3}-[0-9]{3})\] ")
PY_TAG = re.compile(r"^\s*# \[(SR-[A-Z]{3}-[0-9]{3})\] ")


def load_json(root: Path, name: str, errors: list[str]) -> dict | None:
    """The file under tools/specflow/rules/, checked against its schema; None on any failure."""
    path = root / RULES / name
    subject = (RULES / name).as_posix()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{subject}: missing")
        return None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as problem:
        errors.append(f"{subject}: not readable JSON: {problem}")
        return None
    schema = json.loads(
        (HERE / "rules" / name.replace(".json", ".schema.json")).read_text(
            encoding="utf-8"
        )
    )
    problems = check_schema(data, schema)
    errors += [f"{subject}: {p}" for p in problems]
    if problems:
        return None
    if data["schemaVersion"] != 1:
        errors.append(f"{subject}: unsupported schemaVersion {data['schemaVersion']}")
        return None
    return data


def required_criteria(root: Path, errors: list[str]) -> list[str]:
    data = load_json(root, "criteria.json", errors)
    if data is None:
        return []
    ids = data["requiredCriteria"]
    if not ids:
        errors.append(f"{RULES.as_posix()}/criteria.json: empty list")
    seen: set[str] = set()
    for ident in ids:
        if not CRITERION.match(ident):
            errors.append(f"{ident}: malformed criterion ID")
        elif ident in seen:
            errors.append(f"{ident}: repeated in the criteria list")
        seen.add(ident)
    return list(dict.fromkeys(ids))


def plan_rows(root: Path, rel: str, errors: list[str]) -> dict[str, str]:
    """Row ID -> final classification, from every table under ## Inventory Matrix."""
    try:
        text = (root / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as problem:
        errors.append(f"{rel}: cannot be read: {problem}")
        return {}
    lines = [line for _, line in prose(text)]
    start = next(
        (i for i, line in enumerate(lines) if line.rstrip() == "## Inventory Matrix"),
        None,
    )
    if start is None:
        errors.append(f"{rel}: no ## Inventory Matrix section")
        return {}
    rows: dict[str, str] = {}
    tables = data_rows = 0
    in_table = False
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            in_table = False
            continue
        cells = [cell.strip() for cell in CELL.split(line.strip())[1:-1]]
        if not in_table:
            in_table, tables = True, tables + 1
            if cells != HEADER:
                errors.append(
                    f"{rel}: matrix table with another header: {line.strip()}"
                )
            continue
        if set(line.strip()) <= set("|-: "):
            continue
        data_rows += 1
        ident = cells[0] if cells else line.strip()
        if len(cells) != len(HEADER):
            errors.append(f"{rel} {ident}: row has {len(cells)} cells, not 8 cells")
        elif not cells[4]:
            errors.append(f"{rel} {ident}: empty classification")
        elif cells[4] not in CLASSES:
            errors.append(f"{rel} {ident}: unknown classification {cells[4]}")
        else:
            rows[ident] = cells[4]
    if not tables:
        errors.append(f"{rel}: no matrix table under ## Inventory Matrix")
    elif not data_rows:
        errors.append(f"{rel}: no row in the matrix tables under ## Inventory Matrix")
    return rows


def rule_path(root: Path, file: str) -> Path:
    if file == "SKILL.md":
        return root / WORKFLOW / "SKILL.md"
    if file.startswith("scripts/"):
        return root / WORKFLOW / file
    if file.startswith("convert-prd/"):
        return root / SKILLS / file
    return root / WORKFLOW / "references" / file


def file_tags(path: Path) -> list[str]:
    """Rule tags in a Markdown list item outside fences, or a script comment line."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    if path.suffix == ".md":
        return [m[1] for _, line in prose(text) if (m := MD_TAG.match(line))]
    return [m[1] for line in text.splitlines() if (m := PY_TAG.match(line))]


def package_tags(root: Path) -> dict[str, list[str]]:
    """Rule ID -> the package files that tag it."""
    found: dict[str, list[str]] = {}
    for path in sorted((root / SKILLS).rglob("*")):
        if path.is_file() and path.suffix in (".md", ".py"):
            for ident in file_tags(path):
                found.setdefault(ident, []).append(path.relative_to(root).as_posix())
    return found


def check_exists(root: Path, check: str) -> bool:
    if check.startswith("validator:"):
        return check.removeprefix("validator:") in CHECKS
    if check.startswith("evals/"):
        return (root / EVALS / check.removeprefix("evals/")).is_file()
    path, name = check.removeprefix("test:").split("::")
    try:
        tree = ast.parse((root / path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError):
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in ast.walk(tree)
    )


def record_problems(root: Path, path: Path, kind: str) -> list[str]:
    """Why one eval or session record is malformed; empty when it is sound."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as problem:
        return [f"not readable JSON: {problem}"]
    schema = (EVAL_SCHEMAS / f"{kind}.schema.json").read_text(encoding="utf-8")
    problems = check_schema(data, json.loads(schema))
    if problems:
        return problems
    field = "rule" if kind == "eval" else "name"
    if data[field] != path.stem:
        problems.append(f"{field} {data[field]} differs from the file name {path.name}")
    if kind == "eval":
        if not data["assertions"]:
            problems.append("no assertion")
        session = EVALS / "sessions" / f"{data['session']}.json"
        if not (root / session).is_file():
            problems.append(
                f"session {data['session']} has no file {session.as_posix()}"
            )
    return problems


def record_errors(root: Path) -> dict[str, list[str]]:
    """Problems of every eval and session record by path; examples/ is never read."""
    found = {}
    for kind, folder, pattern in (
        ("eval", root / EVALS, "SR-*.json"),
        ("session", root / EVALS / "sessions", "*.json"),
    ):
        for path in sorted(folder.glob(pattern)):
            found[path.relative_to(root).as_posix()] = record_problems(root, path, kind)
    return found


def rule_errors(rule: dict, required: set[str]) -> list[str]:
    """The inventory's own tests of one rule; they run under any area filter."""
    rid, check = rule["id"], rule.get("check")
    errors = [
        f"{rid}: criterion {c} is not in the required list"
        for c in rule.get("criteria", [])
        if c not in required
    ]
    if rule["file"].startswith("aws/"):
        errors.append(
            f"{rid}: file {rule['file']} is under aws/, which a catch-up edits"
        )
    if check is None:
        return [*errors, f"{rid}: no check"]
    if rule["kind"] == "structural" and check.startswith("evals/"):
        errors.append(
            f"{rid}: a structural rule needs a validator: or test: check, not {check}"
        )
    if rule["kind"] == "behavioral" and not check.startswith("evals/"):
        errors.append(f"{rid}: a behavioral rule needs an evals/ check, not {check}")
    if check.startswith("evals/") and check != f"evals/{rid}.json":
        errors.append(f"{rid}: {check} is the eval of another rule")
    return errors


def source_errors(rule: dict, plans: dict[str, dict[str, str]]) -> list[str]:
    errors = []
    for source in rule["sources"]:
        match = PLAN_SOURCE.match(source)
        if not match or match[1] in "DR":
            continue
        if match[1] not in plans:
            errors.append(f"{rule['id']}: source {source} names an unknown plan")
        elif match[2] not in plans[match[1]]:
            errors.append(f"{rule['id']}: source {source} names an unknown row")
        elif plans[match[1]][match[2]] in ("drop", "struck"):
            errors.append(
                f"{rule['id']}: source {source} is a {plans[match[1]][match[2]]} row"
            )
    return errors


def presence_errors(
    root: Path,
    rule: dict,
    tags: dict[str, list[str]],
    records: dict[str, list[str]],
) -> list[str]:
    """The file, tag, and check-existence tests that --area filters."""
    rid, path = rule["id"], rule_path(root, rule["file"])
    shown = path.relative_to(root).as_posix()
    errors = []
    if not path.exists():
        errors.append(f"{rid}: file {shown} does not exist")
    elif not path.is_file():
        errors.append(f"{rid}: {shown} is not a file")
    elif (count := file_tags(path).count(rid)) == 0:
        errors.append(f"{rid}: no tag [{rid}] in {shown}")
    elif count > 1:
        errors.append(f"{rid}: tag [{rid}] appears {count} times in {shown}")
    errors += [
        f"{rid}: tag also in {other}"
        for other in dict.fromkeys(tags.get(rid, []))
        if other != shown
    ]
    check = rule.get("check")
    if check and not check_exists(root, check):
        errors.append(f"{rid}: check {check} does not exist")
    elif (
        check
        and check.startswith("evals/")
        and records.get((EVALS / check.removeprefix("evals/")).as_posix())
    ):
        errors.append(f"{rid}: check {check} does not validate")
    return errors


def check(root: Path, areas: frozenset[str] | None) -> tuple[list[str], list[str]]:
    """Errors and info lines; areas None checks every rule's file, tag, and check."""
    errors: list[str] = []
    info: list[str] = []
    criteria = required_criteria(root, errors)
    inventory = load_json(root, "inventory.json", errors)
    if inventory is None:
        return errors, info
    rules = inventory["rules"]
    plans = {}
    for key, rel in inventory["plans"].items():
        if not PLAN_KEY.fullmatch(key) or not isinstance(rel, str) or not rel:
            errors.append(
                f"{RULES.as_posix()}/inventory.json: plans.{key}: a plan key is one"
                " capital letter other than D and R, its value a non-empty path"
            )
            continue
        plans[key] = plan_rows(root, rel, errors)
        info.append(f"plan {key}: {len(plans[key])} rows read from {rel}")
    covered = {
        m.groups() for r in rules for s in r["sources"] if (m := PLAN_SOURCE.match(s))
    }
    for key, rows in plans.items():
        errors += [
            f"{key}:{row}: {cls} row has no rule"
            for row, cls in rows.items()
            if cls in ("port", "redesign") and (key, row) not in covered
        ]
    seen: set[str] = set()
    for rule in rules:
        if rule["id"] in seen:
            errors.append(f"{rule['id']}: rule ID repeated")
        seen.add(rule["id"])
        errors += rule_errors(rule, set(criteria))
        errors += source_errors(rule, plans)
    for ident in criteria:
        mapped = [r for r in rules if ident in r.get("criteria", [])]
        if not mapped:
            errors.append(f"{ident}: no rule covers this required criterion")
        info += [
            f"{ident} -> {r['id']} -> {r.get('check', '(no check)')}" for r in mapped
        ]
    tags = package_tags(root)
    errors += [
        f"{ident}: tag in {files[0]} belongs to no rule"
        for ident, files in tags.items()
        if ident not in seen
    ]
    records = record_errors(root)
    errors += [f"{path}: {p}" for path, problems in records.items() for p in problems]
    for rule in rules:
        if areas is None or rule["id"].split("-")[1] in areas:
            errors += presence_errors(root, rule, tags, records)
    return errors, info


def inventory_areas(root: Path) -> set[str] | None:
    """The areas the inventory's rule IDs use; None when it cannot be read (check() reports why)."""
    try:
        rules = json.loads(
            (root / RULES / "inventory.json").read_text(encoding="utf-8")
        )["rules"]
        return {rule["id"].split("-")[1] for rule in rules}
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError):
        return None


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--area",
        help="comma-separated areas whose files and checks must exist, or none",
    )
    args = parser.parse_args(argv)
    root = root or Path.cwd()
    areas = None
    if args.area is not None:
        areas = frozenset(a for a in args.area.split(",") if a != "none")
        unknown = sorted(areas - (inventory_areas(root) or areas))
        if unknown:
            print(
                f"error: --area: no rule of area {', '.join(unknown)}", file=sys.stderr
            )
            return 2
    errors, info = check(root, areas)
    for line in info:
        print(line)
    for line in errors:
        print(f"error: {line}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

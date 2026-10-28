"""Report missing local PRD prerequisites without changing repository state."""

import argparse
import json
from pathlib import Path
import re


PREDECESSORS = {
    "00012": (),
    "00013": ("00012",),
    "00014": ("00012", "00013"),
    "00015": ("00013", "00014"),
    "00018": ("00012",),
    "00019": ("00018",),
    "00020": ("00019",),
    "00021": ("00020",),
    "00016": ("00015", "00020", "00021"),
    "00017": ("00016",),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prd", required=True)
    prd = parser.parse_args().prd
    if prd not in PREDECESSORS:
        print(json.dumps({"unknown_prd": prd}, sort_keys=True, separators=(",", ":")))
        return 1

    done = Path(__file__).resolve().parents[2] / "docs/dev/project-management/prds/done"
    completed = set()
    if done.is_dir():
        for entry in done.iterdir():
            match = re.fullmatch(r"([0-9]{5})-.+\.md", entry.name, flags=re.DOTALL)
            if match and entry.is_file():
                completed.add(match[1])
    missing = [item for item in PREDECESSORS[prd] if item not in completed]
    print(json.dumps({"prd": prd, "missing": missing}, sort_keys=True, separators=(",", ":")))
    return int(bool(missing))


if __name__ == "__main__":
    raise SystemExit(main())

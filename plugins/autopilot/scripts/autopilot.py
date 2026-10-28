#!/usr/bin/env python3
"""Expose the packaged review contracts without starting runtime services."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


_ROOT_KEYS = {
    "schema_version", "procedure", "reviewer_jobs", "rubric_sets",
    "doubt_label_map", "execution_profiles", "artifact_kinds",
    "input_kinds", "source_bindings", "policy_digest",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--list-capabilities", action="store_true")
    modes.add_argument("--export-policy", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.out is not None and not args.export_policy:
        parser.error("--out requires --export-policy")
    if args.list_capabilities:
        print('["review-policy-v1","review-evidence-v1","review-fixtures-v1"]')
        return 0

    try:
        policy_path = Path(__file__).resolve().parents[1] / "contracts" / "review-policy-v1.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict) or set(policy) != _ROOT_KEYS:
            raise ValueError("policy must contain exactly the review-policy-v1 root fields")
        if type(policy["schema_version"]) is not int or policy["schema_version"] != 1:
            raise ValueError("policy schema_version must be integer 1")
        pending = [policy]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
            elif isinstance(value, float):
                raise ValueError("policy numbers must be finite JSON integers")
        digest = policy["policy_digest"]
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("policy_digest must be a lowercase SHA-256 digest")
        payload = dict(policy)
        del payload["policy_digest"]
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=True, allow_nan=False).encode("utf-8")
        if hashlib.sha256(serialized).hexdigest() != digest:
            raise ValueError("policy_digest does not match the packaged policy")
        output = (json.dumps(policy, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
        if args.out is None:
            sys.stdout.buffer.write(output)
        else:
            args.out.write_bytes(output)
    except (OSError, ValueError) as error:
        print(f"autopilot: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

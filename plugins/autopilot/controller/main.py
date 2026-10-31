"""Syntax-neutral entry point; reject unsupported Python before runtime imports."""

import json
import sys


def emit(value: dict) -> int:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(raw) + 1 > 16777216:
        raw = b'{"ok":false,"revision":0,"result":null,"error_code":"recovery_required","retryable":false}'
        value = {"ok": False}
    sys.stdout.buffer.write(raw + b"\n")
    return 0 if value.get("ok", True) else 1


def main() -> int:
    if sys.version_info < (3, 12):
        return emit({"ok": False, "revision": 0, "result": None,
                     "error_code": "incompatible_contract", "retryable": False})
    import argparse
    from pathlib import Path

    class Parser(argparse.ArgumentParser):
        def error(self, unused: str) -> None:
            self.exit(2, "invalid controller arguments\n")

    parser = Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--json", action="store_true", required=True)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    commands.add_parser("contract", add_help=False, allow_abbrev=False)
    snapshot = commands.add_parser("snapshot", add_help=False, allow_abbrev=False)
    snapshot.add_argument("--project-root", required=True, type=Path)
    apply = commands.add_parser("apply", add_help=False, allow_abbrev=False)
    apply.add_argument("--project-root", required=True, type=Path)
    apply.add_argument("--request", required=True, type=Path)
    apply.add_argument("--actor-file", type=Path)
    arguments = parser.parse_args()
    from autopilot_state.protocol import execute

    return emit(execute(arguments.command, getattr(arguments, "project_root", None),
                        getattr(arguments, "request", None), getattr(arguments, "actor_file", None)))


if __name__ == "__main__":
    sys.exit(main())

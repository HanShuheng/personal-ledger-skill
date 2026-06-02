#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from personal_ledger_lib import commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal ledger CowAgent skill CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    propose = sub.add_parser("propose", help="Create a pending ledger record")
    propose.add_argument("--text", required=True)
    propose.add_argument("--date")
    propose.add_argument("--time")
    propose.add_argument("--type", choices=["expense", "income"])
    propose.add_argument("--amount")
    propose.add_argument("--currency")
    propose.add_argument("--category")
    propose.add_argument("--keywords")
    propose.add_argument("--description")

    sub.add_parser("confirm", help="Confirm pending record")
    sub.add_parser("cancel", help="Cancel pending record")

    recent = sub.add_parser("list", help="List recent records")
    recent.add_argument("--recent", type=int, default=10)

    summary = sub.add_parser("summary", help="Summarize records")
    summary.add_argument("--month")
    summary.add_argument("--category")

    update_last = sub.add_parser("update-last", help="Update pending or last record")
    update_last.add_argument("--date")
    update_last.add_argument("--time")
    update_last.add_argument("--type", choices=["expense", "income"])
    update_last.add_argument("--amount")
    update_last.add_argument("--currency")
    update_last.add_argument("--category")
    update_last.add_argument("--keywords")
    update_last.add_argument("--description")

    sub.add_parser("delete-last", help="Delete last confirmed record")

    export = sub.add_parser("export", help="Export monthly CSV")
    export.add_argument("--month")

    sub.add_parser("info", help="Show skill status")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    data = vars(args)
    command = data.pop("command")
    try:
        if command == "propose":
            output = commands.propose(data)
        elif command == "confirm":
            output = commands.confirm()
        elif command == "cancel":
            output = commands.cancel()
        elif command == "list":
            output = commands.list_recent(data["recent"])
        elif command == "summary":
            output = commands.summary(data.get("month"), data.get("category"))
        elif command == "update-last":
            output = commands.update_last(data)
        elif command == "delete-last":
            output = commands.delete_last()
        elif command == "export":
            output = commands.export(data.get("month"))
        elif command == "info":
            output = commands.info()
        else:
            parser.error(f"unknown command: {command}")
            return 2
        print(output)
        return 1 if output.startswith("ERROR") else 0
    except Exception as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

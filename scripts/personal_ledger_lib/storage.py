from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .config import Paths, ensure_data_dir


CSV_FIELDS = ["id", "date", "time", "type", "amount", "currency", "category", "keywords", "description", "source_text", "created_at", "updated_at"]


def ensure_csv(paths: Paths) -> None:
    ensure_data_dir(paths)
    if not paths.transactions_file.exists():
        with paths.transactions_file.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()


def read_transactions(paths: Paths) -> list[dict[str, str]]:
    ensure_csv(paths)
    with paths.transactions_file.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_transactions(paths: Paths, rows: list[dict[str, str]]) -> None:
    ensure_data_dir(paths)
    with paths.transactions_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def append_transaction(paths: Paths, record: dict[str, str]) -> dict[str, str]:
    ensure_csv(paths)
    now = datetime.now().isoformat(timespec="seconds")
    row = {
        **record,
        "id": record.get("id") or uuid4().hex[:12],
        "created_at": record.get("created_at") or now,
        "updated_at": now,
    }
    with paths.transactions_file.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return row


def load_pending(paths: Paths) -> dict[str, str] | None:
    if not paths.pending_file.exists():
        return None
    with paths.pending_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_pending(paths: Paths, record: dict[str, str]) -> None:
    ensure_data_dir(paths)
    with paths.pending_file.open("w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def clear_pending(paths: Paths) -> None:
    if paths.pending_file.exists():
        paths.pending_file.unlink()


def last_updated(paths: Paths) -> str:
    if not paths.transactions_file.exists():
        return "无"
    return datetime.fromtimestamp(Path(paths.transactions_file).stat().st_mtime).isoformat(timespec="seconds")

from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .config import get_paths, load_config
from .formatters import format_list, format_record, format_summary
from .parser import build_record, normalize_amount
from .storage import append_transaction, clear_pending, last_updated, load_pending, read_transactions, save_pending, write_transactions


def propose(args: dict[str, Any]) -> str:
    paths = get_paths()
    config = load_config(paths)
    record, errors = build_record(args, config)
    if errors:
        return "ERROR " + " ".join(errors)
    save_pending(paths, record)
    return f"INFO 准备记录：{format_record(record)}。回复确认即可写入；回复取消可放弃。"


def confirm() -> str:
    paths = get_paths()
    pending = load_pending(paths)
    if not pending:
        return "ERROR 没有待确认记录。"
    row = append_transaction(paths, pending)
    clear_pending(paths)
    return f"INFO 已写入：{format_record(row)}。"


def cancel() -> str:
    paths = get_paths()
    pending = load_pending(paths)
    clear_pending(paths)
    if not pending:
        return "INFO 没有待取消记录。"
    return f"INFO 已取消：{format_record(pending)}。"


def list_recent(recent: int) -> str:
    rows = read_transactions(get_paths())
    rows = sorted(rows, key=lambda r: (r.get("date", ""), r.get("time", ""), r.get("created_at", "")), reverse=True)
    return format_list(rows[:recent])


def summary(month: str | None = None, category: str | None = None) -> str:
    month = month or date.today().strftime("%Y-%m")
    rows = [r for r in read_transactions(get_paths()) if r.get("date", "").startswith(month)]
    if category:
        rows = [r for r in rows if r.get("category") == category]
    return format_summary(rows, month, category)


def update_last(updates: dict[str, Any]) -> str:
    paths = get_paths()
    pending = load_pending(paths)
    if pending:
        record = _apply_updates(pending, updates)
        save_pending(paths, record)
        return f"INFO 已更新待确认记录：{format_record(record)}。回复确认即可写入。"
    rows = read_transactions(paths)
    if not rows:
        return "ERROR 暂无流水可修改。"
    rows[-1] = _apply_updates(rows[-1], updates)
    rows[-1]["updated_at"] = datetime.now().isoformat(timespec="seconds")
    write_transactions(paths, rows)
    return f"INFO 已修改上一笔：{format_record(rows[-1])}。"


def delete_last() -> str:
    paths = get_paths()
    rows = read_transactions(paths)
    if not rows:
        return "ERROR 暂无流水可删除。"
    removed = rows.pop()
    write_transactions(paths, rows)
    return f"INFO 已删除上一笔：{format_record(removed)}。"


def export(month: str | None = None) -> str:
    paths = get_paths()
    month = month or date.today().strftime("%Y-%m")
    source = paths.transactions_file
    if not source.exists():
        read_transactions(paths)
    target = paths.data_dir / f"transactions-{month}.csv"
    rows = [r for r in read_transactions(paths) if r.get("date", "").startswith(month)]
    if rows:
        from .storage import write_transactions

        temp_paths = type(paths)(paths.workspace, paths.data_dir, paths.config_file, target, paths.pending_file)
        write_transactions(temp_paths, rows)
    else:
        shutil.copyfile(source, target)
    return f"INFO 已导出 {month} 账单：{target}"


def info() -> str:
    paths = get_paths()
    rows = read_transactions(paths)
    pending = load_pending(paths)
    return "\n".join(
        [
            "INFO personal-ledger-skill 状态：",
            f"- 版本：{__version__}",
            f"- workspace：{paths.workspace}",
            f"- CSV：{paths.transactions_file}",
            f"- 配置：{paths.config_file}",
            f"- pending：{paths.pending_file}",
            f"- 记录数：{len(rows)}",
            f"- 最近更新：{last_updated(paths)}",
            f"- 待确认：{'有' if pending else '无'}",
        ]
    )


def _apply_updates(record: dict[str, str], updates: dict[str, Any]) -> dict[str, str]:
    result = dict(record)
    for key in ["date", "time", "type", "currency", "category", "keywords", "description"]:
        if updates.get(key):
            result[key] = str(updates[key]).strip()
    amount = normalize_amount(updates.get("amount"))
    if amount:
        result["amount"] = amount
    return result

from __future__ import annotations

from collections import defaultdict


def money(amount: float | str, currency: str = "CNY") -> str:
    value = float(amount)
    unit = "元" if currency.upper() == "CNY" else currency.upper()
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{text} {unit}" if unit != "元" else f"{text}元"


def type_label(record_type: str) -> str:
    return "支出" if record_type == "expense" else "进账"


def format_record(record: dict[str, str]) -> str:
    parts = [
        record.get("date", ""),
        type_label(record.get("type", "expense")),
        money(record.get("amount", "0"), record.get("currency", "CNY")),
        f"分类 {record.get('category', '其他')}",
    ]
    if record.get("keywords"):
        parts.append(f"关键词 {record['keywords']}")
    if record.get("description"):
        parts.append(f"备注 {record['description']}")
    return "，".join(parts)


def format_list(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "INFO 暂无流水。"
    lines = ["INFO 最近流水："]
    for row in rows:
        lines.append(f"- {row.get('id')}: {format_record(row)}")
    return "\n".join(lines)


def format_summary(rows: list[dict[str, str]], month: str, category: str | None = None) -> str:
    expense = sum(float(r["amount"]) for r in rows if r["type"] == "expense")
    income = sum(float(r["amount"]) for r in rows if r["type"] == "income")
    by_category: dict[str, float] = defaultdict(float)
    for row in rows:
        if row["type"] == "expense":
            by_category[row.get("category", "其他")] += float(row["amount"])
    title = f"INFO {month}"
    if category:
        title += f" {category}"
    lines = [
        f"{title} 汇总：",
        f"- 总支出：{money(expense)}",
        f"- 总进账：{money(income)}",
        f"- 净额：{money(income - expense)}",
        f"- 笔数：{len(rows)}",
    ]
    if by_category:
        top = sorted(by_category.items(), key=lambda item: item[1], reverse=True)[:5]
        lines.append("- 支出分类 Top：")
        lines.extend(f"  - {name}: {money(value)}" for name, value in top)
    return "\n".join(lines)

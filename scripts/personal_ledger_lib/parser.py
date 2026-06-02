from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any


EXPENSE_WORDS = ("花", "支出", "消费", "买", "打车", "午饭", "晚饭", "早餐", "付", "付款")
INCOME_WORDS = ("收入", "进账", "到账", "收到", "工资", "奖金", "退款", "报销", "兼职")


def normalize_amount(value: str | float | int | None) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    amount = float(match.group())
    if amount <= 0:
        return None
    return f"{amount:.2f}".rstrip("0").rstrip(".")


def parse_amount(text: str) -> str | None:
    patterns = [
        r"(?:花了?|支出|消费|付款|付|收入|进账|到账|收到|退款|报销)?\s*(\d+(?:\.\d+)?)\s*(?:元|块|人民币|rmb|RMB)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return normalize_amount(match.group(1))
    return None


def parse_type(text: str, config: dict[str, Any] | None = None) -> str | None:
    normalized_text = normalize_text(text, config)
    income_words = tuple((config or {}).get("income_type_keywords") or INCOME_WORDS)
    expense_words = tuple((config or {}).get("expense_type_keywords") or EXPENSE_WORDS)
    income_score = sum(1 for word in income_words if matches_meaning(normalized_text, word, config))
    expense_score = sum(1 for word in expense_words if matches_meaning(normalized_text, word, config))
    if config:
        income_score += _category_group_score("income", normalized_text, config)
        expense_score += _category_group_score("expense", normalized_text, config)
    if income_score > expense_score and income_score > 0:
        return "income"
    if expense_score > income_score and expense_score > 0:
        return "expense"
    return None


def parse_date(value: str | None, today: date | None = None, config: dict[str, Any] | None = None) -> str:
    today = today or date.today()
    if not value:
        return today.isoformat()
    text = value.strip()
    aliases = (config or {}).get("relative_date_aliases") or {}
    today_aliases = set(aliases.get("today") or ["今天", "今日"])
    yesterday_aliases = set(aliases.get("yesterday") or ["昨天", "昨日"])
    before_yesterday_aliases = set(aliases.get("before_yesterday") or ["前天"])
    if text in today_aliases:
        return today.isoformat()
    if text in yesterday_aliases:
        return (today - timedelta(days=1)).isoformat()
    if text in before_yesterday_aliases:
        return (today - timedelta(days=2)).isoformat()
    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", text):
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    month_day = re.fullmatch(r"(\d{1,2})月(\d{1,2})(?:日|号)?", text)
    if month_day:
        month, day = map(int, month_day.groups())
        return date(today.year, month, day).isoformat()
    return text


def infer_category(record_type: str, text: str, config: dict[str, Any]) -> str:
    allowed = config["income_categories"] if record_type == "income" else config["expense_categories"]
    normalized_text = normalize_text(text, config)
    best_category = "其他"
    best_score = 0
    for category in allowed:
        score = _category_score(category, normalized_text, config)
        if score > best_score:
            best_category = category
            best_score = score
    if best_score > 0:
        return best_category
    return "其他"


def extract_keywords(text: str, amount: str | None = None, config: dict[str, Any] | None = None) -> str:
    cleaned = text
    if amount:
        cleaned = cleaned.replace(amount, "")
    strip_tokens = (config or {}).get("keyword_strip_tokens") or ["今天", "昨天", "前天", "花了", "花", "支出", "消费", "收入", "进账", "到账", "收到", "元", "块"]
    for token in strip_tokens:
        cleaned = cleaned.replace(token, " ")
    words = [w for w in re.split(r"[\s,，。；;]+", cleaned.strip()) if w]
    return " ".join(words[:6])


def build_record(args: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    text = (args.get("text") or "").strip()
    record_type = args.get("type") or parse_type(text, config)
    amount = normalize_amount(args.get("amount")) or parse_amount(text)
    errors: list[str] = []
    if record_type not in {"expense", "income"}:
        errors.append("缺少收支方向，请说明是支出还是进账。")
    if not amount:
        errors.append("缺少有效金额，请补充金额。")
    if errors:
        return {}, errors
    assert record_type is not None
    category = (args.get("category") or "").strip() or infer_category(record_type, text, config)
    keywords = (args.get("keywords") or "").strip() or extract_keywords(text, amount, config)
    currency = (args.get("currency") or config.get("default_currency") or "CNY").strip().upper()
    description = (args.get("description") or "").strip()
    source_text = text if config.get("save_source_text", True) else ""
    record = {
        "date": parse_date(args.get("date"), config=config),
        "time": args.get("time") or datetime.now().strftime("%H:%M:%S"),
        "type": record_type,
        "amount": amount,
        "currency": currency,
        "category": category,
        "keywords": keywords,
        "description": description,
        "source_text": source_text,
    }
    return record, []


def normalize_text(text: str, config: dict[str, Any] | None = None) -> str:
    normalized = re.sub(r"\s+", "", text.lower())
    normalized = re.sub(r"[，,。；;：:！!？?\[\]（）()【】\"'“”‘’、]", "", normalized)
    aliases = (config or {}).get("semantic_aliases") or {}
    for canonical, alias_list in aliases.items():
        for alias in alias_list:
            alias_text = re.sub(r"\s+", "", str(alias).lower())
            if alias_text:
                normalized = normalized.replace(alias_text, str(canonical).lower())
    return normalized


def matches_meaning(normalized_text: str, term: str, config: dict[str, Any] | None = None) -> bool:
    if not term:
        return False
    if term.startswith("re:"):
        return re.search(term[3:], normalized_text) is not None
    normalized_term = normalize_text(term, config)
    if normalized_term and normalized_term in normalized_text:
        return True
    aliases = (config or {}).get("semantic_aliases") or {}
    for canonical, alias_list in aliases.items():
        if normalized_term == normalize_text(str(canonical), config):
            return any(normalize_text(str(alias), config) in normalized_text for alias in alias_list)
    return False


def _score_rule(normalized_text: str, rule: dict[str, Any], config: dict[str, Any]) -> int:
    if not rule:
        return 0
    negative_terms = rule.get("none") or rule.get("negative") or []
    if any(matches_meaning(normalized_text, term, config) for term in negative_terms):
        return 0
    score = 0
    for term in rule.get("any") or []:
        if matches_meaning(normalized_text, term, config):
            score += int(rule.get("any_weight", 2))
    all_terms = rule.get("all") or []
    if all_terms and all(matches_meaning(normalized_text, term, config) for term in all_terms):
        score += int(rule.get("all_weight", 5))
    return score


def _category_group_score(record_type: str, normalized_text: str, config: dict[str, Any]) -> int:
    categories = config["income_categories"] if record_type == "income" else config["expense_categories"]
    return sum(_category_score(category, normalized_text, config) for category in categories)


def _category_score(category: str, normalized_text: str, config: dict[str, Any]) -> int:
    keyword_map = config.get("category_keywords", {})
    terms = [category, *keyword_map.get(category, [])]
    score = sum(2 for term in terms if matches_meaning(normalized_text, term, config))
    rule = (config.get("category_rules") or {}).get(category, {})
    return score + _score_rule(normalized_text, rule, config)

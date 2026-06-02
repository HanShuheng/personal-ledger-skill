from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPENSE_CATEGORIES = ["餐饮", "交通", "购物", "住房", "水电", "通讯", "娱乐", "学习", "医疗", "人情", "旅行", "运动", "其他"]
INCOME_CATEGORIES = ["工资", "奖金", "兼职", "红包", "退款", "理财", "报销", "其他"]


DEFAULT_CONFIG: dict[str, Any] = {
    "default_currency": "CNY",
    "always_confirm": True,
    "save_source_text": True,
    "expense_categories": EXPENSE_CATEGORIES,
    "income_categories": INCOME_CATEGORIES,
    "category_keywords": {
        "餐饮": ["餐饮", "饭", "早饭", "午饭", "晚饭", "夜宵", "早餐", "午餐", "晚餐", "咖啡", "奶茶", "饮料", "外卖", "餐厅", "饭店", "食堂", "买菜", "水果", "零食", "甜品", "火锅", "烧烤", "小吃", "下馆子", "请吃饭"],
        "交通": ["交通", "打车", "出租车", "网约车", "滴滴", "地铁", "公交", "公交车", "高铁", "火车", "动车", "机票", "飞机", "停车", "停车费", "加油", "油费", "过路费", "高速费", "共享单车", "骑行", "充电", "洗车", "保养"],
        "购物": ["购物", "衣服", "鞋", "包", "日用品", "生活用品", "淘宝", "京东", "拼多多", "超市", "便利店", "电器", "数码", "手机", "电脑", "家具", "家居", "化妆品", "护肤", "快递", "快递费"],
        "住房": ["住房", "房租", "租金", "物业", "物业费", "房贷", "月供", "维修", "家政", "保洁", "搬家", "中介费"],
        "水电": ["水电", "水费", "电费", "燃气", "燃气费", "煤气", "暖气", "取暖费"],
        "通讯": ["通讯", "话费", "手机费", "流量", "宽带", "网费", "电话费", "套餐", "运营商"],
        "娱乐": ["娱乐", "电影", "游戏", "演唱会", "音乐会", "话剧", "展览", "会员", "订阅", "KTV", "酒吧", "桌游", "剧本杀", "旅游娱乐", "门票"],
        "学习": ["学习", "书", "买书", "课程", "网课", "教材", "学费", "培训", "考试", "报名费", "资料", "文具", "论文", "讲座"],
        "医疗": ["医疗", "药", "买药", "医院", "挂号", "体检", "看病", "牙医", "口腔", "疫苗", "医保", "检查", "治疗", "药店"],
        "人情": ["人情", "红包", "礼金", "礼物", "请客", "份子钱", "随礼", "婚礼", "生日", "转账", "孝敬", "探望"],
        "旅行": ["旅行", "旅游", "酒店", "住宿", "民宿", "景区", "门票", "签证", "护照", "行李", "攻略", "度假"],
        "运动": ["运动", "健身", "健身房", "私教", "瑜伽", "游泳", "跑步", "球", "篮球", "足球", "羽毛球", "网球", "装备"],
        "其他": ["其他", "杂项", "临时", "未知"],
        "工资": ["工资", "薪水", "薪资", "发薪", "发工资", "工资到账", "公司打钱", "收入到账", "工资卡"],
        "奖金": ["奖金", "绩效", "年终奖", "提成", "分红", "奖励"],
        "兼职": ["兼职", "副业", "稿费", "劳务费", "外快", "接单", "咨询费"],
        "红包": ["红包", "收红包", "压岁钱", "礼金"],
        "退款": ["退款", "退回", "退钱", "返现", "赔付", "退货退款"],
        "理财": ["理财", "利息", "分红", "收益", "基金", "股票", "债券", "存款利息"],
        "报销": ["报销", " reimbursement", "公司报销", "差旅报销", "费用报销"],
    },
    "semantic_aliases": {
        "餐饮": ["吃饭", "用餐", "吃了一顿", "点外卖", "下馆子", "聚餐", "喝咖啡", "喝奶茶"],
        "交通": ["出行", "坐车", "坐地铁", "打车", "叫车", "开车", "坐飞机", "坐火车"],
        "购物": ["买东西", "购入", "下单", "网购", "剁手", "添置"],
        "住房": ["住处", "租房", "交房租", "房子", "家里维修"],
        "水电": ["交水电", "水电煤", "生活缴费"],
        "通讯": ["通信", "充话费", "交网费", "手机套餐"],
        "娱乐": ["玩", "休闲", "看电影", "看演出", "订阅会员"],
        "学习": ["读书", "上课", "报课", "买教材", "考试报名"],
        "医疗": ["看医生", "看病", "拿药", "买药", "做检查"],
        "人情": ["随份子", "送礼", "给红包", "请人吃饭"],
        "旅行": ["出门玩", "旅游", "出差住宿", "订酒店"],
        "运动": ["锻炼", "撸铁", "打球", "游泳", "跑步"],
        "工资": ["发薪", "发工资", "公司打钱", "工资入账", "薪资到账"],
        "奖金": ["发奖金", "绩效到账", "年终奖到账"],
        "兼职": ["副业收入", "接单收入", "稿费到账", "劳务到账"],
        "红包": ["收到红包", "收了红包", "压岁钱"],
        "退款": ["退钱", "钱退回来了", "退款到账", "退货返钱"],
        "理财": ["收益到账", "利息到账", "基金收益", "股票分红"],
        "报销": ["公司报销", "报销到账", "差旅报销"],
    },
    "expense_type_keywords": ["花", "花了", "支出", "消费", "用了", "付", "付款", "支付", "买", "买了", "下单", "扣款", "刷卡", "转出"],
    "income_type_keywords": ["收入", "进账", "到账", "收到", "收款", "入账", "转入", "工资", "奖金", "退款", "报销", "兼职", "返现"],
    "relative_date_aliases": {
        "today": ["今天", "今日"],
        "yesterday": ["昨天", "昨日"],
        "before_yesterday": ["前天"],
    },
    "keyword_strip_tokens": ["今天", "今日", "昨天", "昨日", "前天", "刚刚", "刚才", "花了", "花", "支出", "消费", "用了", "付了", "付款", "支付", "买了", "买", "收入", "进账", "到账", "收到", "收款", "入账", "元", "块", "人民币"],
}


@dataclass(frozen=True)
class Paths:
    workspace: Path
    data_dir: Path
    config_file: Path
    transactions_file: Path
    pending_file: Path


def get_paths() -> Paths:
    workspace = Path(os.environ.get("COW_WORKSPACE", "~/cow")).expanduser()
    data_dir = workspace / "personal_ledger"
    return Paths(
        workspace=workspace,
        data_dir=data_dir,
        config_file=data_dir / "config.json",
        transactions_file=data_dir / "transactions.csv",
        pending_file=data_dir / "pending_confirm.json",
    )


def ensure_data_dir(paths: Paths | None = None) -> Paths:
    paths = paths or get_paths()
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    return paths


def load_config(paths: Paths | None = None) -> dict[str, Any]:
    paths = paths or get_paths()
    config = _copy_default_config()
    if paths.config_file.exists():
        with paths.config_file.open("r", encoding="utf-8") as f:
            user_config = json.load(f)
        config = _merge_config(config, user_config)
    return config


def _copy_default_config() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_CONFIG, ensure_ascii=False))


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged

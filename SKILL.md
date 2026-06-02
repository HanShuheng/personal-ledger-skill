---
name: personal-ledger-skill
description: 通过聊天自然语言记录个人支出和进账，支持确认后写入 CSV、最近流水、月度汇总、修改/删除上一笔、导出账单和状态查询。
license: MIT
compatibility: CowAgent 技能系统；Python 3.10+；CSV 本地存储；默认使用 COW_WORKSPACE 隔离运行数据。
metadata:
  author: HanShuheng
  version: 0.1.1
  language: zh-CN
  category: productivity
  tags:
    - ledger
    - expense
    - income
    - csv
    - cowagent
  entrypoint: scripts/personal_ledger.py
  config_file: ~/cow/personal_ledger/config.json
  runtime_data_dir: ~/cow/personal_ledger
  timezone: Asia/Shanghai
  requires:
    bins: ["python3"]
    env: []
    python_packages: []
allowed-tools: terminal file
---

# personal-ledger-skill

这是 CowAgent 的个人消费记账 Skill。用户用自然语言描述支出或进账时，先生成待确认记录；只有用户回复确认后，脚本才写入 CSV。

## 能力边界

- 记录个人支出和进账流水。
- 写入前总是确认，避免误记账。
- 首次使用必须先完善基础信息；未完善前，本插件不可用于记账、确认、查询、修改、删除或导出。
- 支持修改待确认记录，例如“改成 35”“分类改成交通”。
- 支持查询本月汇总、分类汇总、最近流水。
- 支持修改或删除上一笔已确认流水。
- 支持导出指定月份 CSV。
- 默认数据目录为 `~/cow/personal_ledger/`，可通过 `COW_WORKSPACE` 隔离多实例。
- 分类、字段映射、触发词、日期别名等会因用户习惯变化的数据必须兼容用户自定义，不应要求用户修改代码。
- 自然语言解析不能只做一一文字匹配；应先使用 `semantic_aliases` 归一化同义说法，再结合分类关键词和 `category_rules` 评分判断。
- v1 不做账户余额、复式记账、支付账单导入、银行/微信/支付宝抓取。

## 隐私提醒

本 Skill 默认保存 `source_text` 原始用户输入，里面可能包含商户、地点、备注等个人敏感信息。用户如不想保存原始输入，可在 `~/cow/personal_ledger/config.json` 设置：

```json
{
  "save_source_text": false
}
```

## 用户意图与命令

### 首次使用：完善基础信息

用户第一次使用或任何命令返回“基础信息尚未完善”时，必须先引导用户补充：

- 记账主体/称呼。
- 基础币种，例如 `CNY`。
- 时区，例如 `Asia/Shanghai`。
- 是否确认已知晓本插件会在本地保存个人流水、备注和原始输入等敏感信息。

没有完成这些信息前，不要调用记账、确认、查询、修改、删除或导出命令；如果用户继续要求使用，继续提示完善基础信息。

用户提供完整信息后执行：

```bash
python {baseDir}/scripts/personal_ledger.py setup-profile --user-name "<记账主体或称呼>" --base-currency CNY --timezone Asia/Shanghai --privacy-acknowledged
```

如果用户明确要求不保存原始输入：

```bash
python {baseDir}/scripts/personal_ledger.py setup-profile --user-name "<记账主体或称呼>" --base-currency CNY --timezone Asia/Shanghai --privacy-acknowledged --save-source-text false
```

### 记支出

用户可能会说：

```text
今天午饭花了32
昨天打车18.5
买书128，学习
```

执行：

```bash
python {baseDir}/scripts/personal_ledger.py propose --text "<用户原话>" --date "<日期>" --type expense --amount "<金额>" --category "<分类>" --keywords "<关键词>"
```

如果 CowAgent 没有抽出某些字段，可以只传 `--text`，Python 会做兜底解析：

```bash
python {baseDir}/scripts/personal_ledger.py propose --text "<用户原话>"
```

### 记进账

用户可能会说：

```text
今天工资到账12000
收到退款59
报销 245
```

执行：

```bash
python {baseDir}/scripts/personal_ledger.py propose --text "<用户原话>" --date "<日期>" --type income --amount "<金额>" --category "<分类>" --keywords "<关键词>"
```

### 确认或取消

用户说“确认”“对”“记上”“写入”时执行：

```bash
python {baseDir}/scripts/personal_ledger.py confirm
```

用户说“取消”“不对”“别记了”时执行：

```bash
python {baseDir}/scripts/personal_ledger.py cancel
```

### 修改待确认或上一笔

用户在确认前说“改成 35”“分类改成交通”“备注改成公司报销”时执行：

```bash
python {baseDir}/scripts/personal_ledger.py update-last --amount 35
python {baseDir}/scripts/personal_ledger.py update-last --category 交通
python {baseDir}/scripts/personal_ledger.py update-last --description 公司报销
```

如果没有待确认记录，该命令会修改上一笔已确认流水。

### 查询最近流水

用户说“最近10笔”“最近几笔账”时执行：

```bash
python {baseDir}/scripts/personal_ledger.py list --recent 10
```

### 月度汇总

用户说“本月花了多少”“这个月餐饮多少”时执行：

```bash
python {baseDir}/scripts/personal_ledger.py summary --month 2026-06
python {baseDir}/scripts/personal_ledger.py summary --month 2026-06 --category 餐饮
```

### 删除上一笔

用户说“删除上一笔”“刚才那笔删掉”时执行：

```bash
python {baseDir}/scripts/personal_ledger.py delete-last
```

### 导出账单

用户说“导出本月账单”“生成 CSV 路径”时执行：

```bash
python {baseDir}/scripts/personal_ledger.py export --month 2026-06
```

### 状态

用户说“记账 skill 状态”时执行：

```bash
python {baseDir}/scripts/personal_ledger.py info
```

## 字段规则

CSV 字段：

```text
id,date,time,type,amount,currency,category,keywords,description,source_text,created_at,updated_at
```

- `type` 只能是 `expense` 或 `income`。
- `amount` 必须是大于 0 的数字。
- `currency` 默认 `CNY`。
- `category` 未命中时使用 `其他`。
- `keywords` 保存商户、物品、场景等轻量关键词。
- `source_text` 默认保存原始输入，可通过配置关闭。

## 错误处理

- 缺金额：返回追问文案，不写入 pending。
- 缺收支方向：返回追问文案，不写入 pending。
- 没有待确认记录时确认：返回错误说明。
- 空账本查询：返回暂无流水或 0 汇总。

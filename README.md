# personal-ledger-skill

CowAgent 个人消费记账 Skill。它把微信/聊天里的自然语言记录为本地 CSV 流水，适合轻量个人记账。

> 本项目只用于个人记账自动化，不提供金融、税务、会计或投资建议。账本数据可能包含个人敏感信息，请自行备份和保护。

## 功能

- 自然语言记录支出：`今天午饭花了32`、`昨天打车18.5`。
- 自然语言记录进账：`今天工资到账12000`、`收到退款59`。
- 写入前总是确认，用户回复“确认/记上”后才写 CSV。
- 确认前可修改金额、分类、备注。
- 查询最近流水、本月汇总、分类汇总。
- 修改或删除上一笔流水。
- 导出指定月份 CSV。
- 运行数据放在 CowAgent workspace，支持 `COW_WORKSPACE` 多实例隔离。

## 安装

通过 CowAgent CLI：

```bash
cow skill install HanShuheng/personal-ledger-skill
```

手动安装：

```bash
mkdir -p ~/cow/skills
git clone https://github.com/HanShuheng/personal-ledger-skill.git ~/cow/skills/personal-ledger-skill
```

本 Skill v1 不需要第三方 Python 依赖。

## 数据目录

默认写入：

```text
~/cow/personal_ledger/
├── config.json
├── pending_confirm.json
└── transactions.csv
```

如果设置了 `COW_WORKSPACE`，则写入：

```text
$COW_WORKSPACE/personal_ledger/
```

CSV 字段：

```text
id,date,time,type,amount,currency,category,keywords,description,source_text,created_at,updated_at
```

## CLI 用法

```bash
python scripts/personal_ledger.py propose --text "今天午饭花了32"
python scripts/personal_ledger.py confirm
python scripts/personal_ledger.py cancel
python scripts/personal_ledger.py list --recent 10
python scripts/personal_ledger.py summary --month 2026-06
python scripts/personal_ledger.py summary --month 2026-06 --category 餐饮
python scripts/personal_ledger.py update-last --amount 35
python scripts/personal_ledger.py delete-last
python scripts/personal_ledger.py export --month 2026-06
python scripts/personal_ledger.py info
```

## 配置

默认不需要配置。要关闭原始输入保存，可创建 `~/cow/personal_ledger/config.json`：

```json
{
  "save_source_text": false
}
```

完整示例见 `examples/config.example.json`。

分类、分类关键词、语义别名、分类规则、收支方向触发词、相对日期别名和关键词清理词都支持用户自定义。用户只需要在配置里写要覆盖或补充的部分，不需要修改 Python 代码。

解析不是简单的一一文字匹配：脚本会先把 `semantic_aliases` 里的同义说法归一化，再对候选分类打分。例如“下馆子 88”可以归到餐饮支出，“公司打钱 12000”可以归到工资进账。

## 本地开发

运行测试：

```bash
python -m unittest discover -s tests
```

手工 smoke test：

```bash
tmpdir="$(mktemp -d)"
COW_WORKSPACE="$tmpdir" python scripts/personal_ledger.py propose --text "今天午饭花了32"
COW_WORKSPACE="$tmpdir" python scripts/personal_ledger.py confirm
COW_WORKSPACE="$tmpdir" python scripts/personal_ledger.py summary --month "$(date +%Y-%m)"
```

## 设计取舍

v1 只做个人流水，不做账户体系、余额、复式记账、支付平台导入或自动抓取。CSV 是权威账本，所有统计都从 CSV 实时计算。

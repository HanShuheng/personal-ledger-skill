from __future__ import annotations

import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "personal_ledger.py"
sys.path.insert(0, str(ROOT / "scripts"))

from personal_ledger_lib.config import DEFAULT_CONFIG, load_config
from personal_ledger_lib.parser import build_record, parse_amount, parse_type


class ParserTest(unittest.TestCase):
    def test_parse_amount_and_type(self) -> None:
        self.assertEqual(parse_amount("今天午饭花了32"), "32")
        self.assertEqual(parse_amount("昨天打车18.5"), "18.5")
        self.assertEqual(parse_type("今天工资到账12000"), "income")
        self.assertEqual(parse_type("买书128"), "expense")

    def test_build_record_missing_required_fields(self) -> None:
        record, errors = build_record({"text": "今天午饭"}, {"default_currency": "CNY", "save_source_text": True, "expense_categories": ["其他"], "income_categories": ["其他"], "category_keywords": {}})
        self.assertEqual(record, {})
        self.assertTrue(errors)

    def test_learning_category_fallback(self) -> None:
        config = {
            "default_currency": "CNY",
            "save_source_text": True,
            "expense_categories": ["餐饮", "交通", "购物", "学习", "其他"],
            "income_categories": ["其他"],
            "category_keywords": {"购物": ["购物"], "学习": ["书", "课程", "教材"]},
        }
        record, errors = build_record({"text": "买书128，学习"}, config)
        self.assertEqual(errors, [])
        self.assertEqual(record["category"], "学习")

    def test_user_custom_keywords_are_configurable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            config_dir = workspace / "personal_ledger"
            config_dir.mkdir(parents=True)
            (config_dir / "config.json").write_text(
                """
{
  "expense_categories": ["宠物", "其他"],
  "category_keywords": {"宠物": ["猫粮"]},
  "expense_type_keywords": ["猫粮"],
  "keyword_strip_tokens": ["今天", "猫粮", "元"]
}
""".strip(),
                encoding="utf-8",
            )
            old_workspace = os.environ.get("COW_WORKSPACE")
            os.environ["COW_WORKSPACE"] = str(workspace)
            try:
                config = load_config()
            finally:
                if old_workspace is None:
                    os.environ.pop("COW_WORKSPACE", None)
                else:
                    os.environ["COW_WORKSPACE"] = old_workspace
        record, errors = build_record({"text": "今天猫粮99"}, config)
        self.assertEqual(errors, [])
        self.assertEqual(record["type"], "expense")
        self.assertEqual(record["category"], "宠物")

    def test_semantic_aliases_infer_type_and_category(self) -> None:
        expense_record, expense_errors = build_record({"text": "今晚下馆子88"}, DEFAULT_CONFIG)
        self.assertEqual(expense_errors, [])
        self.assertEqual(expense_record["type"], "expense")
        self.assertEqual(expense_record["category"], "餐饮")

        income_record, income_errors = build_record({"text": "公司打钱12000"}, DEFAULT_CONFIG)
        self.assertEqual(income_errors, [])
        self.assertEqual(income_record["type"], "income")
        self.assertEqual(income_record["category"], "工资")


class CliTest(unittest.TestCase):
    def run_cli(self, workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["COW_WORKSPACE"] = str(workspace)
        return subprocess.run([sys.executable, str(CLI), *args], env=env, text=True, capture_output=True, check=False)

    def test_propose_confirm_summary_and_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            proposed = self.run_cli(workspace, "propose", "--text", "今天午饭花了32")
            self.assertEqual(proposed.returncode, 0, proposed.stderr + proposed.stdout)
            self.assertIn("准备记录", proposed.stdout)
            self.assertFalse((workspace / "personal_ledger" / "transactions.csv").exists())

            confirmed = self.run_cli(workspace, "confirm")
            self.assertEqual(confirmed.returncode, 0, confirmed.stderr + confirmed.stdout)
            self.assertIn("已写入", confirmed.stdout)

            csv_path = workspace / "personal_ledger" / "transactions.csv"
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["type"], "expense")
            self.assertEqual(rows[0]["amount"], "32")
            self.assertEqual(rows[0]["category"], "餐饮")

            summary = self.run_cli(workspace, "summary", "--month", rows[0]["date"][:7])
            self.assertIn("总支出：32元", summary.stdout)

            listed = self.run_cli(workspace, "list", "--recent", "10")
            self.assertIn("最近流水", listed.stdout)

    def test_update_pending_cancel_and_delete_last(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self.assertEqual(self.run_cli(workspace, "propose", "--text", "昨天打车18.5").returncode, 0)
            updated = self.run_cli(workspace, "update-last", "--amount", "35", "--category", "交通")
            self.assertIn("已更新待确认记录", updated.stdout)
            self.assertEqual(self.run_cli(workspace, "confirm").returncode, 0)

            deleted = self.run_cli(workspace, "delete-last")
            self.assertIn("已删除上一笔", deleted.stdout)
            listed = self.run_cli(workspace, "list")
            self.assertIn("暂无流水", listed.stdout)

    def test_income_export_and_info(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self.assertEqual(self.run_cli(workspace, "propose", "--text", "今天工资到账12000").returncode, 0)
            self.assertEqual(self.run_cli(workspace, "confirm").returncode, 0)
            csv_path = workspace / "personal_ledger" / "transactions.csv"
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))

            exported = self.run_cli(workspace, "export", "--month", rows[0]["date"][:7])
            self.assertIn("已导出", exported.stdout)
            self.assertTrue((workspace / "personal_ledger" / f"transactions-{rows[0]['date'][:7]}.csv").exists())

            info = self.run_cli(workspace, "info")
            self.assertIn("记录数：1", info.stdout)


if __name__ == "__main__":
    unittest.main()

# Changelog

## 0.1.1 - 2026-06-02

- 新增首次使用基础信息门槛；未完善前阻断记账、确认、查询、修改、删除和导出。
- 新增 `setup-profile` 命令，用于设置记账主体、基础币种、时区和隐私确认。
- `info` 现在显示基础信息完成状态和缺失字段。

## 0.1.0 - 2026-06-02

- 初始版本。
- 支持 propose/confirm/cancel/list/summary/update-last/delete-last/export/info。
- 使用 CowAgent workspace 下的 `personal_ledger` 目录保存 CSV、配置和待确认记录。
- 添加 README、SKILL.md、示例配置和单元测试。

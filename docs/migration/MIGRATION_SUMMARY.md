# Tushare DB — 迁移完成总结

> 完成日期：2026-04-26
> PG 源：PostgreSQL 16.13 (localhost:5432, market_db) — 171 张逻辑表（63 张有数据）
> CH 目标：ClickHouse 24.8 (localhost:8123, tushare) — 149 张数据表，46.4M 行

---

## 最终结果

| 指标 | 数值 |
|------|------|
| CH 数据表 | 149 张 |
| CH 总行数 | 46,370,075 |
| PG→CH 迁移表数 | 55 张 |
| PG→CH 迁移行数 | ~20.6M 行 |
| API 回填表 | 约 94 张（由 bootstrap/scheduler 驱动） |

### Top 20 表（按行数）

| 表名 | 行数 | 来源 |
|------|------|------|
| tushare_daily_basic | 11,932,778 | API 回填 |
| tushare_adj_factor | 7,584,253 | API 回填 |
| tushare_moneyflow | 7,449,872 | API 回填 |
| tushare_stock_daily | 7,442,501 | PG→CH 迁移 |
| tushare_stk_factor_pro | 7,327,235 | PG→CH 迁移 |
| tushare_stock_weekly | 1,538,761 | PG→CH 迁移 |
| tushare_index_weight | 551,558 | PG→CH 迁移 |
| tushare_margin_detail | 456,000 | PG→CH 迁移 |
| tushare_stock_monthly | 357,979 | PG→CH 迁移 |
| tushare_cyq_perf | 239,077 | PG→CH 迁移 |
| tushare_ths_daily | 228,000 | PG→CH 迁移 |
| tushare_limit_list_d | 153,134 | PG→CH 迁移 |
| tushare_dc_daily | 150,277 | PG→CH 迁移 |
| tushare_income | 123,800 | PG→CH 迁移 |
| tushare_cashflow | 123,676 | PG→CH 迁移 |
| tushare_balancesheet | 122,180 | PG→CH 迁移 |
| tushare_fina_indicator | 118,565 | PG→CH 迁移 |
| tushare_top_list | 96,809 | PG→CH 迁移 |
| tushare_top_inst | 95,831 | PG→CH 迁移 |
| tushare_fund_daily | 89,098 | PG→CH 迁移 |

---

## 迁移过程回顾

### Phase 1：环境准备与探测
- 安装 psycopg3，确认 PG/CH 连通
- 探测 PG 141 张逻辑表，CH 162 张表

### Phase 2：核心表迁移（P0）
- stock_daily (7.4M)、daily_basic、moneyflow、balancesheet、cashflow、income、fina_indicator、top_list
- 8 张表完成，行数与 PG 完全一致

### Phase 3：全量 PG 扫描发现新表
- 从 141 → 171 张表，发现 27 张此前未覆盖的表
- Bootstrap 建表 + 迁移全部完成（stk_factor_pro 7.3M、stock_monthly 358K、margin_detail 456K 等）

### Phase 4：修复排序键导致的数据丢失
- 发现 6 张表排序键错误，FINAL 去重后从千行缩减到 1 行：
  - cn_cpi (507→1)、hibor (119→1)、libor (121→1)、shibor (2001→1)、shibor_lpr (74→1)、margin (3829→1)
- 原因：`ORDER BY (date)` 等单列排序键导致同日数据合并为 1 行
- 修复：重建表，使用复合排序键如 `ORDER BY (month)` 或 `ORDER BY (trade_date, exchange_id)`
- 重新迁移后全部恢复正确

### Phase 5：其他 Bug 修复
- `index_weight`：错误添加 phantom `ts_code` 列，导致 551K→153 行（错误去重），重建为正确 551,558 行
- `stock_company` / `index_basic`：clickhouse_connect Nullable(Date) 序列化 bug，改用直接 SQL VALUES INSERT
- `field_resolver.py`：增加 Decimal NaN/Inf → None 处理
- 排序键列不能为 Nullable（CH 限制），已正确区分

---

## 遇到的问题与解决方案

| 问题 | 根因 | 解决方案 |
|------|------|----------|
| `ILLEGAL_COLUMN`: Nullable 列作排序键 | CH 不允许 Nullable 列作为 ORDER BY 键 | 排序键列用非 Nullable 类型，其他列 Nullable |
| FINAL 去重后千行→1 行 | ORDER BY 列区分度不足 | 使用复合排序键 (date + identifier) |
| Decimal NaN 写入失败 | PG 返回 Decimal('NaN')，CH 不支持 | normalize_value() 将 NaN/Inf 转为 None |
| Nullable(Date) 序列化 TypeError | clickhouse_connect 库 bug | 直接 SQL VALUES INSERT + date.isoformat() |
| index_weight 数据错误 | bootstrap 添加了不存在的 ts_code 列 | 按 PG 实际列重建，使用 index_code+con_code+trade_date |

---

## 可清理的一次性文件

数据迁移已收尾，以下文件为一次性使用，可安全删除：

**scripts/（8 个）：**
- `bootstrap_new_tables.py` — 新表建表
- `create_missing_table.py` — 单表补建
- `fix_nullable_sort.py` — Nullable 排序键修复
- `migrate.py` — 迁移主脚本
- `migrate_last_two.py` — 最后两张表直接 SQL 插入
- `rebuild_failed_tables.py` — 9 张失败表重建
- `rebuild_failed_tables_v2.py` — 5 张表重建（ts_code-only）
- `rebuild_stock_company.py` — stock_company/index_basic 重建

**docs/migration/（4 个）：**
- `amount_conversion_report.md` — 金额单位转换分析
- `field_diff_report.md` — 字段差异报告
- `missing_tables.md` — 缺失表清单
- `partition_dup_check.md` — 分区重复检查

**建议保留：**
- `src/tushare_db/migration/` — 迁移框架（未来可复用）
- `config/migration/tables.yaml` — 表配置
- `docs/migration/migration_log.md` — 审计日志
- `docs/migration/EXECUTION_PLAN.md` — 执行计划参考
- `tests/unit/test_migration_*.py` — 迁移测试

---

## 剩余待办

| ID | 任务 | 状态 | 优先级 |
|----|------|------|--------|
| R5 | fina_mainbz / top10_holders / stk_holdertrade API 回填 | 部分进行中 | P1 |
| R6 | 5 交易日 scheduler 增量验证 | 待时间窗口 | P0 |
| R7 | weekly_reconcile + verify_row_counts 实跑 | 待时间窗口 | P1 |
| R10 | GitHub Actions 跑通 | 待执行 | P1 |
| R13 | Tushare token 失效测试 | 待执行 | P2 |
| R14 | clickhouse_data 卷损坏重跑 | 待执行 | P2 |

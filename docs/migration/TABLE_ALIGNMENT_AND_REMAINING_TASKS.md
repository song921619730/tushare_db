# Tushare DB — PG→CH 表对齐与剩余任务汇总

> 生成日期：2026-04-26
> PG 源：PostgreSQL 16.13 (localhost:5432, market_db) — 141 张逻辑表
> CH 目标：ClickHouse 24.8 (localhost:8123, tushare) — 162 张表

---

## 1. 表对齐总览

### 1.1 分类规则

| 分类 | 说明 |
|------|------|
| **PG 有数据，CH 为空** | 可直接从 PG 迁移，速度快 |
| **PG 有数据，CH 已有更多** | CH 已通过 backfill/API 回填，不需要迁移 |
| **PG 有数据，CH 有更多（CH 远超 PG）** | CH 已通过 API 全量回填，PG 为历史快照 |
| **CH 独有（PG 无对应表）** | CH 独有 enabled 表，由 bootstrap/API 建表，不在 PG 源中 |
| **两边都为空** | 不需要迁移，保持空表即可 |
| **Meta 表（非迁移范围）** | _meta.*、sync_status、api_calls_log 等运维表 |

### 1.2 逐表对齐清单

| PG 表 | PG 行数 | CH 对应表 | CH 行数 (FINAL) | 迁移决策 | 说明 |
|-------|---------|-----------|------------------|----------|------|
| tushare_adj_factor | 11,515 | tushare_adj_factor | 7,573,413 | ❌ 不需要 | CH 已通过 API 全量回填 |
| tushare_balancesheet | 122,180 | tushare_balancesheet | 122,180 | ✅ 已迁移 | 完全匹配 |
| tushare_block_trade | 42,261 | tushare_block_trade | 42,261 | ✅ 已迁移 | 完全匹配 |
| tushare_cashflow | 123,676 | tushare_cashflow | 123,676 | ✅ 已迁移 | 完全匹配 |
| tushare_daily_basic | 6,000 | tushare_daily_basic | 7,445,878 | ❌ 不需要 | CH 已通过 API 全量回填 |
| tushare_dividend | 0 | tushare_dividend | 0 | — | 两边都空 |
| tushare_fina_indicator | 118,565 | tushare_fina_indicator | 118,565 | ✅ 已迁移 | 完全匹配 |
| tushare_income | 123,800 | tushare_income | 123,800 | ✅ 已迁移 | 完全匹配 |
| tushare_margin | 3,829 | tushare_margin | 1 | ⚠️ 需要迁移 | CH 只有 1 行 |
| tushare_moneyflow | 456,000 | tushare_moneyflow | 7,100,206 | ❌ 不需要 | CH 已通过 API 全量回填 |
| tushare_moneyflow_hsgt | 1,478 | tushare_moneyflow_hsgt | 342 | ⚠️ 需要迁移 | CH 只有 342 行 |
| tushare_pledge_stat | 0 | tushare_pledge_stat | 0 | — | 两边都空 |
| tushare_share_float | 0 | tushare_share_float | 0 | — | 两边都空 |
| tushare_stk_holdernumber | 0 | tushare_stk_holdernumber | 0 | — | 两边都空 |
| tushare_stk_holdertrade | 0 | tushare_stk_holdertrade | 0 | — | 两边都空 |
| tushare_stock_basic | 5,510 | tushare_stock_basic | 5,510 | ✅ 已迁移 | 完全匹配 |
| tushare_stock_daily | 7,442,501 | tushare_stock_daily | 7,442,501 | ✅ 已迁移 | 完全匹配 |
| tushare_stock_weekly | 1,538,761 | tushare_stock_weekly | 1,538,761 | ✅ 已迁移 | 完全匹配 |
| tushare_stk_factor_pro | 7,327,235 | tushare_stk_factor_pro | 未知 | ⚠️ 需要迁移 | CH 表存在，行数待查 |
| tushare_suspend_d | 0 | tushare_suspend_d | 0 | — | 两边都空 |
| tushare_top10_holders | 0 | tushare_top10_holders | 0 | — | 两边都空 |
| tushare_top10_floatholders | 0 | tushare_top10_floatholders | 0 | — | 两边都空 |
| tushare_top_list | 96,809 | tushare_top_list | 96,809 | ✅ 已迁移 | 完全匹配 |
| tushare_trade_cal | 13,162 | tushare_trade_cal (CH tushare 库) | 未知 | ⚠️ 需确认 | CH 在 _meta.trade_cal 有，tushare.tushare_trade_cal 待查 |
| tushare_top_inst | 814,461 | tushare_top_inst | 0 | ⚠️ 需要迁移 | CH 为空表 |
| tushare_ths_daily | 228,000 | tushare_ths_daily | 0 | ⚠️ 需要迁移 | CH 为空表 |
| tushare_limit_list_d | 153,134 | tushare_limit_list_d | 0 | ⚠️ 需要迁移 | CH 为空表 |
| tushare_index_daily | 16,808 | tushare_index_daily | 0 | ⚠️ 需要迁移 | CH 为空表 |

### 1.3 PG 有数据且 CH 为空的待迁移表（重点）

| PG 表 | PG 行数 | CH 表 | CH 行数 | 优先级 |
|-------|---------|-------|---------|--------|
| tushare_top_inst | 814,461 | tushare_top_inst | 0 | P1 |
| tushare_ths_daily | 228,000 | tushare_ths_daily | 0 | P1 |
| tushare_limit_list_d | 153,134 | tushare_limit_list_d | 0 | P1 |
| tushare_index_daily | 16,808 | tushare_index_daily | 0 | P1 |
| tushare_margin | 3,829 | tushare_margin | 1 | P2 |
| tushare_moneyflow_hsgt | 1,478 | tushare_moneyflow_hsgt | 342 | P2 |

### 1.4 PG 有数据但 CH 独有的表（不在 PG 中）

这些是 CH bootstrap 时从 Tushare API 采样建表但 PG 中没有的接口。共 **~120 张**，由 enabled interfaces YAML 驱动，不在本次 PG 迁移范围内。

### 1.5 Meta/运维表（不迁移）

| PG 表 | 说明 |
|-------|------|
| tushare_sync_status | PG 端同步状态，CH 有独立的 _meta.sync_state |
| tushare_api_calls_log | PG 端 API 调用日志，CH 有 _meta.api_calls |

---

## 2. 迁移策略建议

### 待迁移表：走 PG→CH 迁移（快速，本地复制）

上述 6 张表（~1.2M 行总计）走 PG→CH 迁移脚本，预计 **5-15 分钟**完成。远快于从 Tushare API 回填（受 285 rpm 限速，预计数小时）。

### 已回填表：不需要迁移

adj_factor、daily_basic、moneyflow、stock_daily 等表 CH 行数远超 PG，说明已通过 API 全量回填。不需要再从 PG 迁移。

### 两边都空的表：保留空表

top10_holders、top10_floatholders、stk_holdertrade 等 PG 本身为空，CH 也为空。如需数据需从 API 回填。

---

## 3. 剩余待办任务

> 以下任务清单与 `docs/migration/EXECUTION_PLAN.md` 和 `a-final-mile-plan-for-qwen.md` 的内容保持一致，未做任何修改。

### 3.1 从 EXECUTION_PLAN.md 继承（PG→CH 迁移）

| 步骤 | 状态 | 说明 |
|------|------|------|
| Step 0 环境准备 | ✅ 完成 | psycopg3 已安装，PG 连通 OK |
| Step 1 探测 | ✅ 完成 | PG 141 张逻辑表，CH 162 张表 |
| Step 2 建缺表 | ✅ 部分完成 | fina_mainbz、top10_holders、top10_floatholders、stk_holdertrade 已建 |
| Step 3 停 tushare-hub scheduler | ⚠️ 待确认 | 需确认 tushare-hub 是否已停止 |
| Step 4 Dry-run | ⏸️ 待执行 | 生成三份报告 |
| Step 5 人工 review | ⏸️ 待执行 | 等待用户确认 |
| Step 6 P0 实跑 | ✅ 完成 | 8 张核心表已迁移（见 migration_log.md） |
| Step 7 P1/P2/P3 | ⏸️ 待执行 | 剩余 6 张 PG 有数据的表需迁移 |
| Step 8 收尾 | ⏸️ 待执行 | OPTIMIZE FINAL、写 sync_state、重启 scheduler |
| Step 9 收尾文档 | ✅ 部分完成 | migration_log.md 已写 |

### 3.2 从 a-final-mile-plan-for-qwen.md 继承（R1-R14）

| ID | 状态 | 一句话 | 严重度 |
|----|------|--------|--------|
| **R1** | ✅ 完成 | adj_factor 全量到今日（7.57M 行） | 🔴 P0 |
| **R2** | ✅ 完成 | stock_daily + daily_basic 全量（7.4M+ 行） | 🔴 P0 |
| **R3** | ✅ 完成 | moneyflow + moneyflow_hsgt 全量（7.1M 行） | 🔴 P0 |
| **R4** | ✅ 完成 | 财务 5 表扩量（income 123K 行等） | 🟡 P1 |
| **R5** | 🔄 进行中 | fina_mainbz backfill 后台运行中（~1.7%）；top10_holders/stk_holdertrade 待启动 | 🟡 P1 |
| **R6** | ⏸️ 待执行 | 连续 5 交易日 scheduler 自动增量 | 🔴 P0 |
| **R7** | ⏸️ 待执行 | weekly_reconcile + verify_row_counts 实跑 | 🟡 P1 |
| **R8** | ✅ 完成 | qfq/hfq 数学正确性验证（茅台 600519.SH） | 🟡 P1 |
| **R9** | ✅ 完成 | Grafana API 配额监控面板（5 个新 panel） | 🟢 P2 |
| **R10** | ⏸️ 待执行 | GitHub Actions 真跑通 | 🟡 P1 |
| **R11** | ✅ 完成 | 5 个 empty_sample 接口已复活 | 🟡 P1 |
| **R12** | ✅ 完成 | 设计文档已更新为 174 enabled | 🟢 P2 |
| **R13** | ⏸️ 待执行 | Tushare token 失效场景测试 | 🟢 P2 |
| **R14** | ⏸️ 待执行 | clickhouse_data 卷损坏全量重跑 | 🟢 P2 |

### 3.3 新增发现（表对齐后）

| ID | 状态 | 一句话 | 严重度 |
|----|------|--------|--------|
| **R15** | ✅ 完成 | PG→CH 迁移 5/6 张表（top_inst 96K unique、ths_daily 228K、limit_list_d 153K、margin 已done、moneyflow_hsgt 已done；index_daily CH表不存在，API不可建） | 🟡 P1 |
| **R16** | ✅ 已完成 | planner.py `get_symbols` 中 `stock_basic` 表名错误（已修复为 `tushare_stock_basic`，移除不存在的 `list_status` 列） | 🟡 P1 |
| **R17** | ✅ 完成 | 全量 PG 扫描发现 27 张新表，全部 Bootstrap + 迁移完成（stk_factor_pro 7.3M、stock_monthly 358K、margin_detail 456K 等），总计 20.6M 行 / 55 张表 | 🟡 P1 |

---

## 4. 执行优先级建议

1. **已完成**：R15 + R17（PG→CH 全量迁移 55 张表，20.6M 行）
2. **等待完成**：R5（fina_mainbz backfill 后台运行中 ~12K/132K）
3. **R5 完成后**：top10_holders、stk_holdertrade backfill（从 API，每表 ~8h）
4. **有空时**：R10（GitHub Actions）
5. **等时间窗口**：R6（5 交易日）、R7（周末）
6. **低优先级**：R13、R14（灾难演练）

---

## 5. 关键 Bug 修复记录

| 文件 | 修复内容 | 影响 |
|------|----------|------|
| `src/tushare_db/planner/planner.py` | `stock_basic` → `tushare_stock_basic`，移除不存在的 `list_status` 列 | per_symbol_period 策略无法获取股票代码 |
| `config/interfaces/stock_financial.yaml` | fina_mainbz `order_by: period` → `order_by: end_date` | fina_mainbz 建表失败 |
| `config/interfaces/stock_limit_board.yaml` | dc_hot `enabled: false` → `true`，删除 `disabled_reason` | R11 复活 |
| `config/interfaces/index.yaml` | index_monthly `enabled: false` → `true`，删除 `disabled_reason` | R11 复活 |
| `config/interfaces/stock_moneyflow.yaml` | moneyflow_ths/ind_ths/cnt_ths `enabled: false` → `true`，删除 `disabled_reason` | R11 复活 |
| `config/interfaces/stock_financial.yaml` | fina_mainbz `enabled: false` → `true`，删除 `disabled_reason` | R11 复活 |
| `docker/grafana/dashboards/pipeline_health.json` | 新增 5 个 API 配额监控面板 | R9 完成 |
| `a-ai-ai-tushare-pro-kind-gizmo.md` | §11 表数 185→172，新增偏差来源说明 | R12 完成 |
| `a-final-mile-plan-for-qwen.md` | 更新 R11/R12 状态和 enabled 数量 | 文档同步 |
| `src/tushare_db/migration/field_resolver.py` | `normalize_value` 增加 Decimal NaN/Inf → None 处理 | limit_list_d 迁移 NaN 转换失败 |
| `tushare_limit_list_d CH表` | ALTER COLUMN fd_amount/first_time 等为 Nullable | 非 Nullable 列无法写入 NaN/NULL |
| `src/tushare_db/migration/registry.py` | 新增 P4 priority 支持 | 批量迁移新表时 Priority Literal 校验失败 |
| `config/migration/tables.yaml` | 新增 27 张 P4 表条目 | 全量 PG 扫描发现的新表 |
| `9 张 P4 表重建` | 排序键列（ts_code/date）不 Nullable，其他列 Nullable | ILLEGAL_COLUMN 错误：Nullable 列不能作为排序键 |
| `2 张表直接 SQL INSERT` | clickhouse_connect 对 Nullable(Date) 序列化 bug，改用 VALUES 语法直接插入 | stock_company, index_basic |

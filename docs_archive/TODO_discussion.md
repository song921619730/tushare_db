# 决策记录：Tushare Pro 数据仓库

> 整理自 2026-04-25 对话，已收敛到 [a-ai-ai-tushare-pro-kind-gizmo.md](a-ai-ai-tushare-pro-kind-gizmo.md) 权威文档。

---

## 已决策（全部 ✓，已同步至主计划文档）

### 1. ai_reader 用户权限放松

- **决策**：去掉 `max_rows_to_read`、`max_memory_usage`、`max_execution_time`，仅保留 `readonly=2`
- **理由**：自用环境，唯一使用者是本人控制的 AI 客户端
- **MCP 侧**：`query_sql` 不再注入 LIMIT，把决定权交给调用方

### 2. 调度方案：四批次 + 周六长尾

- **决策**：新版四批次框架（A/B/C/D），`per_symbol_period` 长尾接口（fina_mainbz, top10_holders, top10_floatholders, stk_holdertrade 等）移至周六 02:00 独立 job，不进工作日批次
- **解决老版风险**：A 批次 ~62 接口 30–60min 窗口不会被长尾级联拖慢
- **调度表**：

| 批次 | 时间 | 覆盖 | ~接口数 |
|:----:|:----:|------|:-------:|
| A | 17:00 工作日 | stock_daily, index, etf, futures, options, bonds | ~62 |
| B | 18:00 工作日 | stock_moneyflow, stock_reference（除 per_symbol_period）| ~18 |
| C | 19:00 工作日 | stock_limit_board, stock_special（除 per_symbol_period）| ~32 |
| D | 19:45 工作日 | macro, financial period_loop, tmt, wealth, forex, spot | ~36 |
| Saturday | 02:00 周六 | per_symbol_period 长尾 | ~6 |
| refresh_trade_cal | 06:00 每日 | trade_cal + stock_basic + stock_company | — |
| weekly_reconcile | 02:00 周日 | gap_detector P0/P1 扫描补洞 | — |
| verify_row_counts | 03:00 每日 | 核对 T-1 行数 | — |

### 3. WSL2 文件系统布局

- **决策**：ClickHouse 数据用 named volume `clickhouse_data` 落 WSL2 ext4，不 bind mount Windows 目录
- **保留 Windows 挂载**：`./config/`（只读）、`./data/logs/`（顺序写，便于本机查看）、`./data/samples/`（开发用）
- **理由**：MergeTree 小文件随机 IO 在 Windows 挂载上慢 30–50%

### 4. APScheduler JobStore

- **决策**：MemoryJobStore，零文件依赖
- **理由**：job 定义在代码里可重建；幂等保障靠 `_meta.sync_state` 不在 APScheduler
- **风险**：`database is locked` 问题彻底消除

### 5. 回补五层顺序

| 层 | 内容 |
|---|------|
| Layer 0 | trade_cal, stock_basic, stock_company, index_basic, fund_basic 等参考表 |
| Layer 1 | daily, daily_basic, adj_factor, stk_limit, weekly, monthly, suspend_d 等日行情 |
| Layer 2 | moneyflow, moneyflow_hsgt, margin, margin_detail, block_trade, limit_list_d 等 |
| Layer 3 | income, balancesheet, cashflow, fina_indicator, dividend 等财务（period_loop）+ per_symbol_period 长尾 |
| Layer 4 | ths_daily, dc_daily, kpl_list, ccass_hold, cyq_perf, stk_factor_pro 等概念板块/特色 |
| Layer 5 | cn_gdp, cn_cpi, shibor, sf_month, fx_daily, sge_daily, bo_daily 等宏观/外汇/现货/文娱 |

**执行节奏**：周末 Day1 白天 Layer 0–2，Day1 夜间 Layer 3 长尾，Day2 白天 Layer 4–5 + weekly_reconcile 补洞。

### 6. 实施阶段（7 个 PR，连续编号）

| PR | 内容 | 主要 Skills/Agents |
|----|------|---------------------|
| **PR1 骨架** | pyproject + docker-compose + ClickHouse 配置 + 全部 227 个 YAML + config/loader + meta/bootstrap + cli init | docker-patterns, clickhouse-io, planner |
| **PR2 采集引擎** | rate_limiter + tushare_client + schema/inferer/ddl_builder/evolver + sink + sample_apis + runner/worker + planner/strategies | tdd-guide, python-reviewer |
| **PR3 回补 + 检查点** | runner/backfill（--layer / --priority）+ meta/sync_state + CLI + SIGKILL 续跑 e2e | tdd-guide, python-reviewer, e2e-runner |
| **PR4 调度 + 增量** | scheduler/jobs（A/B/C/D + 周六长尾 + 健康检查）+ scheduler/service（MemoryJobStore）+ runner/incremental | tdd-guide, python-reviewer |
| **PR5 访问层** | mcp_server + ai_reader 用户（仅 readonly=2）+ 本机+LAN 验证 | mcp-server-patterns, security-reviewer |
| **PR6 验证与监控** | verify/*（gap_detector, row_counts, checksums）+ Grafana + weekly_reconcile + cli verify | doc-updater, e2e-runner |
| **PR7 前端仪表盘** | Vue 3 + Naive UI + ECharts 单文件应用，直连 ClickHouse HTTP | frontend-patterns |

**全流程**：每次代码写完调 python-reviewer；构建问题用 build-error-resolver；架构变更用 architect。

### 7. 声明式 batch 字段扩展

InterfaceSpec YAML 的 `batch` 字段值扩展为：`A | B | C | D | saturday`，`saturday` 专供 `per_symbol_period` 策略接口使用。

---

## 新版 vs 老版 关键差异参考

| 维度 | 老版 | 新版（已实施） |
|------|------|---------------|
| 调度 | 8 个细粒度 job（16:00–22:00） | 4 批次 + 周六长尾 + 3 辅助 job |
| ai_reader 安全 | max_rows_to_read=1e8, max_memory_usage=4GB | 仅 readonly=2 |
| per_symbol_period | 混入工作日 job | 周六 02:00 独立 job |
| WSL2 数据路径 | 未明确 | named volume → WSL2 ext4 |
| APScheduler | 未明确（默认 SQLite） | MemoryJobStore |
| PR 数量 | 7（跳 PR6） | 7（连续 PR1–PR7） |
| 验证计划 | 7 条 | 8 条（新增关机补跑测试） |
| 回补 CLI | 无分层 | `--layer 0\|1\|2\|3\|4\|5` |
| MCP 工具 | tavily_search 占位 | 移除（已有独立 MCP）；保留语义化核心工具 |
| 脏数据处理 | 未覆盖漏发场景 | verify_row_counts 行数=0 记 WARN；批次延迟兜底 1h 重试 |

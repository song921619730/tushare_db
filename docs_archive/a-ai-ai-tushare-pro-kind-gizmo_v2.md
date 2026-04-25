# Tushare Pro A 股本地数据仓库（ClickHouse）

## Context

在 `F:\AIcoding_space\VsCode\tushare_db\` 从零搭建一个 A 股数据仓库，服务本机 AI 与局域网 AI 的批量回测/分析需求。目标：无延迟、高并发、支撑亿级行时间序列批量回测。

- Tushare Pro 共 227 个接口：10k 积分实际可用 **84 normal (500/min) + 98 special (300/min) = 182 个**，45 个付费接口先注册 `enabled:false` 占位
- 历史数据回补至 2020-01-01（7 个接口起点特殊：bak_basic=20160101、stk_account_old=20080101、fund_sales_vol=20210101、hm_detail=20220801、stk_nineturn=20230101、moneyflow_dc=20230911、limit_list_ths=20231101）
- 每个交易日盘后按 Tushare 官方推荐的 A/B/C/D 四批次自动增量，断点续传，完整审计日志
- 三份参考 MD 在仓库根：`tushare_interfaces.md`、`tushare_10k_interfaces.md`、`tushare_rate_limits.md`（**限速/批次的权威依据**）
- `e:\Astock\python` 的 AKshare 脚本用户已删除，不需要兼容或迁移
- **不做数据备份**，数据损坏时依赖重跑（单次 P0+P1 回补 12–24h 可接受）

## 确认的技术选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 平台 | Windows 11 + Docker Desktop + WSL2 | 一键 `docker compose up`，隔离干净，用户已装 |
| 数据库 | ClickHouse 24.8（Docker） | 列存 + MergeTree 按 `(ts_code, trade_date)` 排序，亿级回测聚合亚秒级，ZSTD+Gorilla+DoubleDelta 压缩后 6 年数据 10–25 GB |
| 调度 | APScheduler + SQLAlchemyJobStore(SQLite) | 进程内常驻，持久化 jobstore，misfire_grace_time 兜底开机补漏 |
| 访问层 | ClickHouse 原生 HTTP(8123)/TCP(9000) + MCP Server | 双通道：原生协议零延迟 LAN 直连，MCP 给 AI 自然语言入口 |
| 语言/SDK | Python 3.11, tushare, clickhouse-connect, structlog, pydantic v2, click, tenacity, mcp | 成熟栈 |
| 容器编排 | docker-compose：clickhouse + pipeline + mcp + grafana | 资源隔离，重启策略自动恢复 |

## 目录结构

```
F:\AIcoding_space\VsCode\tushare_db\
├── pyproject.toml
├── docker-compose.yml
├── .env.example                          # TUSHARE_TOKEN, CH_PIPELINE_PASSWORD, CH_AI_PASSWORD
├── docker\clickhouse\{config.xml, users.xml, init\001_create_databases.sql}
├── docker\pipeline\Dockerfile
├── config\
│   ├── settings.yaml                     # CH 连接、超时、重试、并发度
│   └── interfaces\                       # 227 接口声明式注册（按分类分文件）
│       ├── _schema.yaml                  # InterfaceSpec 字段文档
│       ├── stock_basic.yaml / stock_daily.yaml / stock_financial.yaml
│       ├── stock_limit_board.yaml / stock_moneyflow.yaml / stock_reference.yaml
│       ├── stock_special.yaml / index.yaml / bonds.yaml / etf.yaml
│       ├── fund.yaml / futures.yaml / options.yaml / forex.yaml
│       ├── spot.yaml / macro.yaml / tmt.yaml / wealth.yaml
│       └── paid.yaml                     # 45 个付费接口，enabled:false
├── src\tushare_db\
│   ├── cli.py                            # init/backfill/update/status/resume/verify/scheduler-run/mcp-serve/probe
│   ├── logging_setup.py                  # structlog JSON + 轮转
│   ├── config\{loader.py, models.py}
│   ├── core\{rate_limiter.py, tushare_client.py, clock.py, errors.py}
│   ├── planner\{strategies.py, work_units.py, planner.py}
│   ├── schema\{inferer.py, ddl_builder.py, evolver.py, type_map.py}
│   ├── sink\{clickhouse_sink.py, dedupe.py}
│   ├── meta\{bootstrap.py, sync_state.py, sync_runs.py, api_calls.py}
│   ├── runner\{worker.py, executor.py, backfill.py}
│   ├── scheduler\{jobs.py, service.py}
│   ├── mcp_server\{server.py, tools.py}
│   └── verify\{row_counts.py, gap_detector.py, checksums.py}
├── scripts\{sample_api_responses.py, bootstrap_schemas.py, seed_trade_cal.py}
├── tests\{unit, integration, e2e}\
└── data\{clickhouse\, logs\, samples\, apscheduler.sqlite}
```

## 核心机制

### 1. 声明式接口注册（InterfaceSpec）
每个接口一个 YAML 条目，字段包括：`name`, `table`, `enabled`, `priority(P0-P3)`, `mode(full|incremental)`, `freq_bucket(normal|special)`, `start_date`, `fetch_strategy{kind, date_field, step, symbol_source}`, `pagination`, `partition_key`, `order_by`, `dedupe_key`, `required_params`, `fields(auto|list)`, `schema_overrides`, `batch(A|B|C|D)`。引擎零硬编码，加/改接口只改 YAML。

### 2. 工作单元规划（planner/strategies.py）
六种策略覆盖 227 接口：
- `full_once`：单次调用（stock_basic, index_basic 等 34 个 full 表）
- `date_loop`：按交易日循环（daily, daily_basic, moneyflow, adj_factor 等，按 `tushare_trade_cal` 跳过非交易日）
- `period_loop`：按季度末循环（income/balancesheet/cashflow 用 `period=YYYYMMDD` 单次拿全市场，6 年 × 4 季 = 24 次调用）
- `monthly_window`：月窗口（fund_nav, index_weight）
- `per_symbol_period`：按股票循环（fina_mainbz, top10_holders 等少量无 period 汇总的接口）
- `offset_paging`：单次超大返回的内部翻页

规划器用 `scope_key` 作为每单元的幂等键，写入 `_meta.sync_state`。

### 3. 双令牌桶限速（core/rate_limiter.py）
依据 `tushare_rate_limits.md`：
- `NORMAL_BUCKET` 500/min（保守配 450/min 做缓冲），覆盖 84 个接口
- `SPECIAL_BUCKET` 300/min（配 270/min），覆盖 98 个接口
- `collections.deque` + `threading.Lock` 滑动窗口，跨 `ThreadPoolExecutor` 共享（normal=8 worker, special=4 worker）
- HTTP 429 触发整桶 60s 冷却，tenacity 指数退避 2→4→8…≤60s，重试状态码 429/500/502/503/504

### 4. ClickHouse Schema 策略
- **样本驱动推断 + 人工覆盖**：`scripts/sample_api_responses.py` 调各接口一次存 `data/samples/*.json` → `schema/inferer.py` 按字段名/类型启发式生成 DDL → `config/schemas/overrides/` 可手动微调
- **引擎**：默认 `ReplacingMergeTree(_version)` 保证重跑幂等
- **分区**：日行情 `toYYYYMM(trade_date)`，财务 `toYYYY(end_date)`，参考表 `tuple()`
- **列压缩**：`ts_code` → `LowCardinality(String)`，日期 `CODEC(DoubleDelta, ZSTD(3))`，价格 `CODEC(Gorilla, ZSTD(3))`
- **Schema 演化**：启动时 `schema/evolver.py` diff `system.columns` 与最新样本，只做 `ADD COLUMN`，未知列先落 `_extra String` 下次升级

### 5. 检查点与审计（`_meta` 数据库）
- `_meta.sync_state(interface, scope_key, status, rows, last_success_date, _version)` — 单元级幂等标记（ReplacingMergeTree）
- `_meta.sync_runs(run_id, interface, scope, started_at, units_total, units_done, status)` — run 级
- `_meta.api_calls(run_id, interface, params_hash, started_at, duration_ms, status, rows, error_msg)` — **每次 HTTP 调用的完整审计日志**（TTL 90 天）

**续跑语义**：启动时将 heartbeat 过期（>10 min）的 `running` 行标为 `partial` → planner 重算全部单元 → `done` 跳过、`failed` 按指数退避重试；ClickHouse INSERT 原子 + ReplacingMergeTree 保重放不重复。

### 6. 日志（logging_setup.py）
structlog → JSON 渲染 → 双 handler：
- `data/logs/app.log`（应用事件，50MB × 20 份轮转）
- `data/logs/api_audit.log`（API 调用事件文件侧备份，与 `_meta.api_calls` 互为备份）
- 每条 record 带 `run_id / interface / scope_key / params_hash`

### 7. 调度 — 严格对齐官方 A/B/C/D 批次
`scheduler/jobs.py`，Asia/Shanghai 时区，所有 job 进门查 `tushare_trade_cal` 非交易日直接 skip：

| 批次 | 时间 (CST) | 覆盖分类 | 接口数 | 主要表 |
|:----:|:----------:|----------|:------:|--------|
| **A** Daily Quotes | 17:00 | stock_daily, index, etf, futures, options, bonds | ~62 | daily, weekly, adj_factor, stk_limit, daily_basic, index_daily, fund_daily, cb_daily, opt_daily, fut_daily 等 |
| **B** Money Flow & Reference | 18:00 | stock_moneyflow, stock_reference | 22 | moneyflow, moneyflow_hsgt, margin, margin_detail, block_trade, top10_holders 等 |
| **C** Special & Limit Board | 19:00 | stock_limit_board, stock_special | 35 | ths_daily, dc_daily, kpl_list, limit_list_d, cyq_perf, stk_factor_pro, ccass_hold 等 |
| **D** Macro / Financial / TMT / Others | 19:45 | macro, stock_financial, tmt, wealth, forex, spot | 40 | income/balancesheet/cashflow（按新公告触发）, cn_cpi/gdp/pmi, shibor, sf_month 等 |
| refresh_trade_cal | 06:00 每日 | 刷新 trade_cal + stock_basic + stock_company | — | 周末也跑，保证日历表最新 |
| weekly_reconcile | 02:00 周日 | gap_detector 全量 P0/P1 扫描补洞 | — | 修复任何被跳过的交易日 |
| verify_row_counts | 03:00 每日 | 核对 T-1 行数、写入 verify 表 | — | 健康检查 |

每个 job 创建一个 `_meta.sync_runs`，按 `batch` 字段过滤接口，驱动 planner 生成单元。`misfire_grace_time=3600, coalesce=True` 保证开机补漏一次。

### 8. CLI
```
tushare-db init                            # 建库建元表建 DDL
tushare-db probe                           # 小量调用每个接口探测权限，自动标 enabled/disabled
tushare-db sample-apis --only daily,income # 抓样本填 data/samples/
tushare-db rebuild-schema --interface daily
tushare-db backfill --priority P0          # 历史回补
tushare-db backfill --interface daily --from 20200101 --to 20240101
tushare-db backfill --all
tushare-db update --batch A                # 手动触发某批次
tushare-db update --incremental
tushare-db status [--interface X --detail]
tushare-db resume
tushare-db verify --priority P0
tushare-db scheduler-run                   # 常驻调度（容器默认 entrypoint）
tushare-db mcp-serve --host 0.0.0.0 --port 7800
```

### 9. 局域网访问层
**ClickHouse**：`listen_host=0.0.0.0`，暴露 `8123`(HTTP) + `9000`(native TCP)

三个用户（`docker/clickhouse/users.xml`）：
- `pipeline` — 密码来自 env，读写 `tushare.*` 和 `_meta.*`
- `ai_reader` — 只读 `GRANT SELECT ON tushare.*`；`readonly=2, max_execution_time=30s, max_rows_to_read=1e8, max_memory_usage=4GB`
- `grafana` — 只读 `_meta.*` + `system.*`，给监控面板

**MCP Server 工具集**：`list_interfaces` / `describe_table` / `query_sql`（强制 SELECT/WITH/SHOW/DESCRIBE 前缀，注入 LIMIT） / `get_ohlcv(ts_code, start, end, adjust)` / `get_financials` / `get_index_components` / `get_moneyflow` / `trade_calendar` / `coverage_report`

连接串：
- 原生: `clickhouse://ai_reader:***@<host>:9000/tushare`
- HTTP: `http://ai_reader:***@<host>:8123/?database=tushare`
- MCP SSE: `http://<host>:7800/sse`

### 10. 规模预估
- **表数**：182 可用 + 45 付费占位 + 3 元表 ≈ 230
- **行数**：150–250M（主力是 stock_daily / moneyflow / daily_basic / adj_factor 各 ~8M，ths_daily / dc_daily 约 20–40M）
- **压缩存储**：10–25 GB，未压缩 80–200 GB；规划 **50 GB 可用空间**留余量
- **回补耗时**：P0+P1 约 12–24h；少数 `per_symbol_period` 接口是长尾（~14h/个），建议周末跑完 P2/P3
- **内存**：ClickHouse 容器 limit 12GB，host 16GB RAM 为下限

## 关键依赖（pyproject.toml）

```toml
[project]
dependencies = [
  "tushare>=1.4.20", "clickhouse-connect>=0.7.19",
  "apscheduler>=3.10.4", "sqlalchemy>=2.0",
  "pydantic>=2.7", "pydantic-settings>=2.3",
  "pyyaml>=6.0", "click>=8.1", "rich>=13.7",
  "structlog>=24.1", "tenacity>=8.3", "httpx>=0.27",
  "pandas>=2.2", "pyarrow>=16.0", "xxhash>=3.4",
  "mcp>=1.0", "python-dotenv>=1.0",
  "prometheus-client>=0.20", "pytz>=2024.1",
]
[project.optional-dependencies]
dev = ["pytest>=8.2", "pytest-cov>=5.0", "pytest-asyncio>=0.23",
       "responses>=0.25", "vcrpy>=6.0",
       "testcontainers[clickhouse]>=4.5",
       "ruff>=0.4", "mypy>=1.10"]
```

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| Tushare 列集静默变化 | schema_evolver 只做 ADD COLUMN，未知列落 `_extra String` 并 WARN |
| 429 风控 | tenacity 指数退避 + 整桶 60s 冷却；bucket 容量取官方 90% 作缓冲 |
| `per_symbol_period` 长尾 | 支持 `--parallel-symbols N`；单元级检查点重启零浪费 |
| `ai_reader` 被滥用扫全表 | readonly=2, max_execution_time=30, max_rows_to_read 限额；MCP 工具强制 LIMIT 注入 |
| APScheduler SQLite jobstore 丢失 | docker volume 持久；job 定义在代码中可重建，数据层依赖 `_meta` 幂等重跑 |
| 接口权限与 10k 默认清单不一致 | `tushare-db probe` 在 init 后探测每接口真实权限，自动更新 YAML `enabled` 字段 |
| 数据卷损坏 | **接受重跑**（用户已确认）；P0/P1 可在 24h 内恢复 |

## 验证计划

1. **单元测试**：rate_limiter（注入假时钟）、planner strategies（断言单元数/参数）、schema inferer（金样本 DDL diff）
2. **集成测试**（testcontainers + responses mock）：造 2 天假数据全流程，重跑 2 次断言 0 重复
3. **回补正确性**：`daily` 接口 3 个月跑 2 遍 → `countDistinct(ts_code, trade_date) == count(*)`；抽一天对比实时 Tushare 返回
4. **增量幂等**：`update --batch A` 连跑 2 次，第二次 `rows=0`，`cityHash64()` 全表哈希不变
5. **崩溃续跑**：`backfill income 2020-2023` 子进程 30s 后 SIGKILL，重启跑到完，行数 == 单次干净跑基线
6. **补洞**：随机删 2 个 trade_date 行，`verify` 应全部检出并重取
7. **访问层**：本机 Claude 通过 MCP `get_ohlcv("000001.SZ","20240101","20240301")` 返回正确行；LAN 机器 `clickhouse-client` 用 `ai_reader` 执行 INSERT 被拒
8. **调度**：关机 2 天后开机，17:00–19:45 四批次在 `misfire_grace_time` 内各自补跑一次

## 实施阶段（建议 PR 拆分）

1. **PR1 骨架**：pyproject + docker-compose + ClickHouse 配置 + `config/interfaces/*.yaml`（全部 227 条从三份 MD 批量转换）+ `config/loader.py` + `meta/bootstrap.py` + `cli init` —— 验收：`docker compose up -d` + `tushare-db init` 成功建 230 张空表
2. **PR2 采集引擎**：`core/rate_limiter` + `core/tushare_client` + `schema/inferer` + `sink/clickhouse_sink` + `scripts/sample_api_responses.py` + `runner/worker.py` + `planner/strategies.py` + `cli probe` —— 验收：`backfill --interface daily --from 20240101 --to 20240110` 单接口跑通
3. **PR3 回补 + 检查点**：`runner/backfill.py` + `meta/sync_state` + `cli backfill/status/resume` + SIGKILL 续跑测试 —— 验收：P0 全量回补成功
4. **PR4 调度 + 增量**：`scheduler/jobs.py`（对齐 A/B/C/D 批次）+ `scheduler/service.py` + `runner/incremental` —— 验收：盘后四批次定时 job 正确跑完当日增量
5. **PR5 访问层**：`mcp_server/*` + ClickHouse `ai_reader` 用户 + 示例 AI 客户端连接验证 —— 验收：本机 Claude 和一台 LAN 机器都能无感查询
6. **PR6 验证与监控**：`verify/*` + Grafana dashboard（`_meta.*` + `system.parts` + `tushare_bucket_*`）+ weekly_reconcile —— 验收：每日健康检查自动运行并留痕

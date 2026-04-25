# Tushare Pro A 股本地数据仓库（ClickHouse）

> 此文档为权威设计方案，与代码一起在仓库内版本化维护。
> Plan mode 副本：`C:\Users\gj\.claude\plans\a-ai-ai-tushare-pro-kind-gizmo.md`（Claude Code 索引用，可忽略）

## Context

在 `F:\AIcoding_space\VsCode\tushare_db\` 从零搭建 A 股数据仓库，服务本机 AI 与局域网 AI 的批量回测/分析。目标：无延迟、高并发、支撑亿级行时间序列批量回测。

- 227 接口：10k 积分实际可用 **84 normal (500/min) + 98 special (300/min) = 182 个**，45 付费占位 `enabled:false`
- 历史回补至 2020-01-01；7 个特殊起点（bak_basic=20160101、stk_account_old=20080101、fund_sales_vol=20210101、hm_detail=20220801、stk_nineturn=20230101、moneyflow_dc=20230911、limit_list_ths=20231101）
- 每交易日盘后按 Tushare 官方 A/B/C/D 四批次自动增量；断点续传；完整审计日志
- 三份参考 MD：`tushare_interfaces.md`、`tushare_10k_interfaces.md`、`tushare_rate_limits.md`（限速/批次权威依据）
- 前端仪表盘设计另见：`a-frontend-dashboard-spec.md`（Vue 3 + Naive UI + ECharts）
- AKshare 老脚本已删除，无迁移负担
- **不做备份**，依赖重跑（P0+P1 单次 12–24h 可接受）

## 确认选型

| 维度 | 选择 |
|------|------|
| 平台 | Windows 11 + Docker Desktop + WSL2 |
| 数据库 | ClickHouse 24.8（容器） |
| 调度 | APScheduler **MemoryJobStore**（不持久化，job 在代码里可重建） |
| 访问层 | ClickHouse 原生 HTTP(8123)/TCP(9000) + MCP Server SSE(7800) |
| 语言 | Python 3.11，tushare、clickhouse-connect、structlog、pydantic v2、click、tenacity、mcp |

## WSL2 文件系统布局（关键性能项）

ClickHouse MergeTree 在 Windows 挂载（`\\wsl.localhost\...`）上小文件随机 IO 比原生 Linux 慢 30–50%。布局策略：

| 路径 | 文件系统 | 用途 |
|------|---------|------|
| `clickhouse_data` named volume（WSL2 ext4） | **WSL2 原生** | ClickHouse `/var/lib/clickhouse` —— 性能关键 |
| `./config/` (Windows) → `/app/config:ro` | Windows 挂载 | 只读配置，容器无写压力 |
| `./data/logs/` (Windows) → `/app/data/logs` | Windows 挂载 | 顺序追加写，便于本机查看日志 |
| `./data/samples/` (Windows) | Windows 挂载 | 样本 JSON，开发期间需要本机看 |

`docker-compose.yml` 用 named volume `clickhouse_data` 而不是 bind mount Windows 目录。

## 目录结构

```
F:\AIcoding_space\VsCode\tushare_db\
├── pyproject.toml
├── docker-compose.yml
├── .env.example                          # TUSHARE_TOKEN, CH_PIPELINE_PASSWORD, CH_AI_PASSWORD
├── docker\clickhouse\{config.xml, users.xml, init\001_create_databases.sql}
├── docker\pipeline\Dockerfile
├── config\
│   ├── settings.yaml
│   └── interfaces\                       # 227 接口声明式注册
│       ├── _schema.yaml
│       ├── stock_basic.yaml / stock_daily.yaml / stock_financial.yaml
│       ├── stock_limit_board.yaml / stock_moneyflow.yaml / stock_reference.yaml
│       ├── stock_special.yaml / index.yaml / bonds.yaml / etf.yaml
│       ├── fund.yaml / futures.yaml / options.yaml / forex.yaml
│       ├── spot.yaml / macro.yaml / tmt.yaml / wealth.yaml
│       └── paid.yaml                     # 45 付费接口 enabled:false
├── src\tushare_db\
│   ├── cli.py                            # init/probe/sample-apis/backfill/update/status/resume/verify/scheduler-run/mcp-serve
│   ├── logging_setup.py
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
└── data\{logs\, samples\}                # apscheduler.sqlite 取消（MemoryJobStore）
```

## 核心机制

### 1. 声明式接口注册（InterfaceSpec）
每接口一个 YAML 条目：`name, table, enabled, priority(P0|P1|P2|P3), mode(full|incremental), freq_bucket(normal|special), start_date, fetch_strategy{kind, date_field, step, symbol_source}, pagination, partition_key, order_by, dedupe_key, required_params, fields, schema_overrides, batch(A|B|C|D|saturday|reference)`。引擎零硬编码，加/改接口只改 YAML。`batch=reference` 由 06:00 `refresh_reference` job 调度，不参与工作日 A/B/C/D。

**priority 含义**（决定回补/补洞优先序）：
- `P0` — 必备日行情/资金流（daily, daily_basic, adj_factor, moneyflow*, stk_limit）
- `P1` — 财务 period_loop + 龙虎榜（income, balancesheet, cashflow, fina_indicator, top_list）
- `P2` — 概念板块/特色（ths_*, dc_*, kpl_*, ccass_*, cyq_*）
- `P3` — 宏观/外汇/小众（cn_*, shibor*, fx_*, sge_*, bo_*, film_*）

### 2. 工作单元规划（六种策略）
- `full_once`：单次（stock_basic, index_basic 等 34 个）
- `date_loop`：按交易日（daily, daily_basic, moneyflow, adj_factor 等）
- `period_loop`：季度末（income/balancesheet/cashflow 用 period 单次拿全市场，6×4=24 次/接口）
- `monthly_window`：月窗口（fund_nav, index_weight）
- `per_symbol_period`：按股票循环（fina_mainbz, top10_holders, top10_floatholders, stk_holdertrade 共 4 个长尾）→ **统一安排到周六凌晨独立 job**，不进工作日批次。规模估算：5300 ts_code × 24 期（6 年 × 4 季）÷ 270 rpm（special bucket 90% 实测）≈ **7.85h/接口**，4 接口顺序约 31h，单次周六窗口（02:00–次周一 09:00）勉强容纳。增量阶段每周仅新增最近一期，单次 5300 calls / 270 rpm ≈ 20 min/接口，完全无压力
- `offset_paging`：内部翻页

### 3. 双令牌桶限速（吞吐量优先调优）

依据 `tushare_rate_limits.md`，按 **95% 利用率**（最大化拉数速度，让 429 接管缓冲，而非保守留余量）：

| 桶 | 官方上限 | 实施目标 | worker 数 | 覆盖接口 |
|---|---|---|---|---|
| NORMAL_BUCKET | 500/min | **475/min** | 12 | 84 |
| SPECIAL_BUCKET | 300/min | **285/min** | 6 | 98 |

实现细节：
- `collections.deque` + `threading.Lock` 滑动窗口（毫秒精度）；两桶独立、互不阻塞
- `ThreadPoolExecutor` 共享，worker 数按 `bucket_rpm × p95_latency_sec / 60` 计算（Tushare 平均 800ms，p95 ~1.5s）：normal=12、special=6 足以填满桶
- HTTP 客户端：`httpx.Client(http2=True, timeout=10s, limits=Limits(max_connections=20, max_keepalive_connections=20))` —— HTTP/2 多路复用 + 长连接，比 `tushare.pro_api()` 默认 requests 快 ~30%
- HTTP 429 整桶 60s 冷却；tenacity 指数退避 1→2→4…≤30s（更激进，减少长尾）；重试 429/500/502/503/504/timeout
- **不重试**：401/403/404（业务错误，记 `_meta.api_calls.status='biz_err'` 直接放弃单元）

理论吞吐：normal 桶 6 年×252 交易日×84 接口 ≈ 12.7 万 calls，475/min ≈ 7.9/s ⇒ 4.5h 跑完；special 同理 28.6 万 calls / 285 rpm ≈ 16.7h。叠加并行 ⇒ **首次回补 P0+P1 在 18h 内**（不含 per_symbol_period 长尾）。

### 4. ClickHouse Schema（写入与查询双优）
- 样本驱动推断 (`scripts/sample_api_responses.py` → `schema/inferer.py`) + 字段级覆盖直接放在 `config/interfaces/*.yaml` 的 `schema_overrides` 字段下（不另设 `config/schemas/overrides/` 目录）
- 默认 `ReplacingMergeTree(_version)` 保幂等
- 分区：日行情 `toYYYYMM(trade_date)`，财务 `toYYYY(end_date)`，参考表 `tuple()`
- `LowCardinality(String)` 应用于 ts_code/exchange；日期 `CODEC(DoubleDelta, ZSTD(3))`；价格 `CODEC(Gorilla, ZSTD(3))`
- `schema/evolver.py` diff 列后只 `ADD COLUMN`；未知列先 `_extra String`

**写入路径优化**（所有 INSERT 默认开启）：
- `async_insert=1, wait_for_async_insert=1, async_insert_max_data_size=10485760, async_insert_busy_timeout_ms=200` —— 同表小批量自动合并，减少 part 创建压力（重要：long-tail per_symbol 单元每次只插几行，不开 async_insert 会爆炸）
- `min_insert_block_size_rows=100000, min_insert_block_size_bytes=268435456`
- `clickhouse-connect` 用 Native protocol（9000）而非 HTTP（8123），写入吞吐高 2-3x

**字段单位归一化**（在 `schema/type_map.py` 内置规则）：
- 财务字段（`*_amount`/`*_revenue`/`*_profit` 等）：Tushare 万元 → ClickHouse `Decimal64(2)` 元
- 基金份额（`*_share`/`*_amount`）：万份 → 份
- 日期：`String("YYYYMMDD")` → `Date`；`String("YYYY-MM-DD HH:MM:SS")` → `DateTime`
- 百分比：保留原始（如 1.23 表示 1.23%，不做 ÷100）
- `_meta.sync_runs.normalize_version` 记录归一化规则版本，规则升级时可批量回填

### 5. 检查点与审计（`_meta` 数据库）

#### 5.1 表 DDL（PR1 `cli init` 阶段创建）

```sql
CREATE TABLE _meta.sync_state (
    interface         LowCardinality(String),
    scope_key         String,                  -- 见 5.2
    status            Enum8('pending'=0,'running'=1,'done'=2,'partial'=3,'failed'=4,'biz_err'=5),
    rows              UInt64,
    last_success_at   DateTime64(3, 'Asia/Shanghai'),
    heartbeat_at      DateTime64(3, 'Asia/Shanghai'),    -- worker 每 30s 刷新
    attempts          UInt8,
    last_error        String,
    _version          UInt64                              -- toUnixTimestamp64Milli(now64())
) ENGINE = ReplacingMergeTree(_version)
ORDER BY (interface, scope_key);

CREATE TABLE _meta.sync_runs (
    run_id            UUID,
    interface         LowCardinality(String),
    batch             LowCardinality(String),
    scope             String,
    started_at        DateTime64(3, 'Asia/Shanghai'),
    finished_at       Nullable(DateTime64(3, 'Asia/Shanghai')),
    units_total       UInt32,
    units_done        UInt32,
    units_failed      UInt32,
    status            Enum8('running'=1,'done'=2,'partial'=3,'failed'=4),
    normalize_version UInt16                              -- 字段归一规则版本
) ENGINE = MergeTree
ORDER BY (started_at, interface);

CREATE TABLE _meta.api_calls (
    run_id            UUID,
    interface         LowCardinality(String),
    params_hash       UInt64,
    started_at        DateTime64(3, 'Asia/Shanghai'),
    duration_ms       UInt32,
    status            UInt16,                             -- HTTP 状态码 / 0=timeout
    rows              UInt32,
    error_msg         String
) ENGINE = MergeTree
ORDER BY (started_at, interface)
TTL toDate(started_at) + INTERVAL 90 DAY;
```

#### 5.2 `scope_key` 格式（每策略一种，**严格按本表落地**）

| 策略 | scope_key 模板 | 例 |
|---|---|---|
| `full_once` | `{interface}:full` | `stock_basic:full` |
| `date_loop` | `{interface}:{trade_date:YYYYMMDD}` | `daily:20240315` |
| `period_loop` | `{interface}:{period:YYYYMMDD}` | `income:20240331` |
| `monthly_window` | `{interface}:{ym:YYYYMM}` | `fund_nav:202403` |
| `per_symbol_period` | `{interface}:{ts_code}:{period:YYYYMMDD}` | `fina_mainbz:000001.SZ:20240331` |
| `offset_paging` | `{interface}:{date}:{offset:08d}` | `moneyflow:20240315:00005000` |

#### 5.3 心跳 / 续跑语义

- worker 拿到单元后立刻 `INSERT INTO _meta.sync_state ... status='running', heartbeat_at=now64()`
- 主循环每 30s 对所有 `running` 单元批量 `INSERT` 同 PK 新行（ReplacingMergeTree 自动去重保最新 `_version`）
- 进程启动时扫描 `SELECT * FROM _meta.sync_state FINAL WHERE status='running' AND heartbeat_at < now64() - INTERVAL 10 MINUTE` 标 `partial`
- planner 重算单元 → `done/biz_err` 跳过；`failed/partial` 按 `attempts` 指数退避重试（≥5 次转人工 alert）
- ClickHouse INSERT 原子 + ReplacingMergeTree 重放不重复

#### 5.4 增量幂等指纹（替换 cityHash64 全表哈希）

```sql
-- 不稳定（ReplacingMergeTree 未 OPTIMIZE FINAL 时返回不一致）：
-- SELECT cityHash64(groupArray(*)) FROM tushare.daily;

-- 稳定（基于最终版本，FINAL 物化）：
SELECT
    count() AS rows_final,
    sum(cityHash64(*)) AS fingerprint,
    max(_version) AS max_ver
FROM tushare.daily FINAL
WHERE trade_date = '2024-03-15';
```
连跑两次 `update --batch A`，第二次该指纹应完全相同 ⇒ 幂等通过。

### 6. 日志
structlog → JSON 双 handler：
- `data/logs/app.log`（应用事件，50MB×20 轮转）
- `data/logs/api_audit.log`（API 调用，与 `_meta.api_calls` 互备份）
- 每条带 `run_id / interface / scope_key / params_hash`

### 7. 调度 —— 四批次 + 周六长尾

`scheduler/jobs.py`，Asia/Shanghai，所有 job 进门查 `tushare_trade_cal` 跳过非交易日：

| 批次 | 时间 | 覆盖分类 | 接口数 | 说明 |
|:----:|:----:|---------|:------:|------|
| **A** Daily Quotes | 17:00 工作日 | stock_daily, index, etf, futures, options, bonds, fund 行情 | ~56 | daily, weekly, adj_factor, stk_limit, daily_basic, index_daily, fund_daily, cb_daily, fut_daily, opt_daily, fx_daily 等 |
| **B** Money Flow & Reference | 18:00 工作日 | stock_moneyflow, stock_reference（除 per_symbol_period）| ~19 | moneyflow*, margin*, block_trade, pledge*, repurchase, share_float, stk_holdernumber 等 |
| **C** Special & Limit Board | 19:00 工作日 | stock_limit_board, stock_special（除 per_symbol_period）| ~43 | ths_*, dc_*, kpl_*, limit_*, cyq_*, ccass_*, hk_hold, stk_surv, stk_auction*, broker_recommend 等 |
| **D** Macro / Financial period_loop / TMT / Others | 19:45 工作日 | macro, stock_financial period_loop, tmt, wealth, forex, spot, factor_pro | ~38 | income/balancesheet/cashflow（period_loop）, cn_*, shibor*, libor, hibor, bo_*, film_record, fund_sales_*, stk_factor_pro 等 |
| **Saturday Long-tail** | 02:00 周六 | per_symbol_period 接口 | **4** | fina_mainbz, top10_holders, top10_floatholders, stk_holdertrade（确认仅此 4 个） |
| **refresh_reference** | 06:00 每日 | 全部 *_basic / *_company / *_classify / trade_cal 参考表 | ~21 | trade_cal, stock_basic, stock_company, index_basic, fund_basic, fund_company, etf_basic, fut_basic, fut_trade_cal, cb_basic, opt_basic, sge_basic, fx_obasic, bse_mapping, stk_managers, stk_rewards, namechange, new_share, index_classify, ci_index_member 等 |
| weekly_reconcile | 02:00 周日 | gap_detector 全量 P0/P1 扫描补洞 | — | |
| verify_row_counts | 03:00 每日 | 核对 T-1 行数写 verify 表；**行数=0 视为接口漏发，记 WARN** | — | |

**合计**：56 + 19 + 43 + 38 + 4 + 21 ≈ 181，与 84 normal + 98 special = 182 在 ±1 误差内（个别接口归类边界由 probe 探测后由 YAML `batch` 字段校准）。完整路由清单见末尾 [附录 A：182 接口归属总表](#附录-a182-接口归属总表)。

每 job 创建 `_meta.sync_runs`，按 YAML `batch` 字段过滤接口。`misfire_grace_time=3600, coalesce=True` 保关机后开机一次性补跑。

**延迟兜底**：某批次跑完发现数据仍是 T-2 的（Tushare 发布延迟），记录 WARN 日志并安排 1 小时后再试。**重试上限 2 次**（即首跑 + 2 次复跑共 3 次），仍失败转 `_meta.sync_state.status='failed'` 并写 `app.log` ERROR，由 weekly_reconcile 接管。

**"行数=0"判定**：仅当 `trade_cal` 显示该 trade_date 是交易日时才告警；非交易日（含未来日历未发布的边界）"行数=0" 视为正常。

### 8. 回补五层顺序

| 层 | 内容 | 依据 |
|---|------|------|
| Layer 0 | trade_cal, stock_basic, stock_company, index_basic, fund_basic 等参考表 | 后续 date_loop 的日历和 ts_code 来源，必须先有 |
| Layer 1 | daily, daily_basic, adj_factor, stk_limit, weekly, monthly, suspend_d 等日行情 | 主力数据，date_loop 简单快速 |
| Layer 2 | moneyflow, moneyflow_hsgt, margin, margin_detail, block_trade, limit_list_d 等 | 依赖股票列表与日历 |
| Layer 3 | income, balancesheet, cashflow, fina_indicator, dividend 等财务（period_loop）+ per_symbol_period 长尾 | 长尾 ~7.85h/接口（4 接口约 31h），单独周末跑 |
| Layer 4 | ths_daily, dc_daily, kpl_list, ccass_hold, cyq_perf, stk_factor_pro 等概念板块/特色 | 无强依赖 |
| Layer 5 | cn_gdp, cn_cpi, shibor, sf_month, fx_daily, sge_daily, bo_daily 等宏观/外汇/现货/文娱 | 数据量小，最后 |

**执行节奏**（首次回补，单次预算）：
- 周末 Day1 白天 Layer 0–2（参考表 + 日行情 + 资金流，~6–10h）
- Day1 夜间 + Day2 全天连续运行 Layer 3 `per_symbol_period` 长尾 4 接口（约 31h，跨 ~36h 实际墙钟）
- Day2 夜间 + Day3 白天 Layer 4–5（特色 + 宏观，~4–8h）
- Day3 收尾 weekly_reconcile 补洞

**P0+P1 单次 12–24h** 的口径**不含 Layer 3 长尾**；含长尾的全量首次约 **48–60h**（一个长周末）。后续每周仅增量，长尾接口周六 02:00 一次跑完。

### 9. CLI

#### 9.1 命令清单

```
# 冷启动两步（PR1/PR2 分工）
tushare-db init                            # PR1：仅创建 _meta.{sync_state,sync_runs,api_calls} + 空 tushare 数据库
tushare-db bootstrap                       # PR2：sample-apis → infer schema → CREATE 182 张业务表 → seed trade_cal → probe → 写回 YAML

# 单步细化（手动调试用）
tushare-db sample-apis [--only daily,income]
tushare-db rebuild-schema --interface daily
tushare-db probe                           # 探测每接口权限，回写 YAML enabled

# 回补（首次历史 + 灾后恢复）
tushare-db backfill --layer 0|1|2|3|4|5    # 按层回补（推荐）
tushare-db backfill --priority P0|P1|P2|P3 # 按优先级
tushare-db backfill --interface daily --from 20200101 --to 20240101
tushare-db backfill --all

# 增量（每日盘后；scheduler 自动调用，也可手动）
tushare-db update --batch A|B|C|D|saturday|reference
tushare-db update --incremental            # 全部 enabled 接口的 T-1 增量

# 运维
tushare-db status [--interface X --detail]
tushare-db resume                          # 续跑所有 partial/failed 单元
tushare-db verify --priority P0
tushare-db scheduler-run                   # 容器默认 entrypoint
tushare-db mcp-serve --transport stdio|sse [--host 0.0.0.0 --port 7800]
```

`InterfaceSpec.priority` 取值 `P0|P1|P2|P3`（P0 = 必备日行情/资金流；P1 = 财务+龙虎榜；P2 = 概念板块/特色；P3 = 宏观/外汇/小众）。

**`--from` vs YAML `start_date` 优先级**：CLI 显式 `--from` > YAML `start_date` > 全局默认 `2020-01-01`。CLI 未指定时按 YAML，YAML 未指定时用全局默认。7 个特殊起点（`bak_basic=20160101` 等）写在 YAML，回补脚本自动遵循。

#### 9.2 容器内触发（pipeline 容器常驻 `scheduler-run`）

```powershell
# 一次性命令
docker compose exec pipeline tushare-db backfill --layer 0
docker compose exec pipeline tushare-db status

# 长时任务（detach + 日志跟随）
docker compose exec -d pipeline tushare-db backfill --all
docker compose logs -f pipeline | grep backfill

# 重启 scheduler（修改 YAML 后）
docker compose restart pipeline
```

PowerShell 短脚本 `scripts/td.ps1`：
```powershell
function td { docker compose exec pipeline tushare-db $args }
# 用法：td backfill --layer 1 / td status / td verify --priority P0
```

### 10. 局域网访问层（高速无障碍）

设计原则：**LAN 信任域**，靠网络隔离防外部访问；**应用层零限制**，让 AI 客户端跑满带宽。

#### 10.1 ClickHouse 配置（`docker/clickhouse/config.xml`）

```xml
<listen_host>0.0.0.0</listen_host>
<http_port>8123</http_port>
<tcp_port>9000</tcp_port>
<max_connections>4096</max_connections>
<keep_alive_timeout>30</keep_alive_timeout>

<!-- 浏览器 SPA 直连必备 -->
<http_options_response>
    <header><name>Access-Control-Allow-Origin</name><value>*</value></header>
    <header><name>Access-Control-Allow-Methods</name><value>GET,POST,OPTIONS</value></header>
    <header><name>Access-Control-Allow-Headers</name><value>Authorization,Content-Type,X-ClickHouse-Format,X-ClickHouse-Database</value></header>
    <header><name>Access-Control-Max-Age</name><value>86400</value></header>
</http_options_response>
```

#### 10.2 用户与权限（`docker/clickhouse/users.xml`，密码用 `<password from_env="..."/>` 注入）

```xml
<pipeline><password from_env="CH_PIPELINE_PASSWORD"/>...</pipeline>
<ai_reader>
    <password from_env="CH_AI_READER_PASSWORD"/>
    <networks><host_regexp>192\.168\..*|10\..*|172\.(1[6-9]|2[0-9]|3[0-1])\..*|127\.0\.0\.1</host_regexp></networks>
    <profile>ai_reader_profile</profile>
    <quota>unlimited</quota>
</ai_reader>
<grafana><password from_env="CH_GRAFANA_PASSWORD"/>...</grafana>
```

`ai_reader_profile` 设置：
```xml
<readonly>2</readonly>
<enable_http_compression>1</enable_http_compression>      <!-- LZ4/gzip 自动协商 -->
<http_zlib_compression_level>3</http_zlib_compression_level>
<max_threads>0</max_threads>                              <!-- 0 = auto，按 CPU 核数 -->
<max_block_size>1048576</max_block_size>
<output_format_json_quote_64bit_integers>0</output_format_json_quote_64bit_integers>
<!-- 不设 max_rows_to_read / max_memory_usage / max_execution_time -->
```

三用户分工：
- `pipeline` — 读写 `tushare.*` 和 `_meta.*`
- `ai_reader` — 只读 `GRANT SELECT ON tushare.*`，IP 限 LAN 网段，**应用层零限制**（已通过 `host_regexp` 隔离外网）
- `grafana` — 只读 `_meta.*` + `system.*`

#### 10.3 MCP Server（`tushare-db mcp-serve`，端口 7800）

- **协议**：本机 Claude Desktop 走 stdio（更快、无网络栈）；局域网其他设备走 SSE
- **鉴权**：LAN IP 白名单（同上正则），不要 token —— 用户明确"AI 无限制访问"
- **后端连接**：MCP 内部用 clickhouse-connect **Native 协议（9000）** 而非 HTTP，吞吐高 2-3x
- **流式返回**：`query_sql` / `get_ohlcv` 等大结果集用 Server-Sent Events 分块流式返回，避免内存堆积
- **工具集**：
  - `list_interfaces(category?)` → 返回 yaml spec 摘要
  - `describe_table(table)` → 列字段 + 行数 + 最后更新时间
  - `query_sql(sql)` —— 强制 `^(SELECT|WITH|SHOW|DESCRIBE)\s` 前缀，不注入 LIMIT，**返回压缩 LZ4 + Arrow IPC 格式**（AI 端解析快）
  - `get_ohlcv(ts_code, start, end, adjust='qfq'|'hfq'|'none')` —— **复权在工具内计算**（基于 adj_factor 表 join），返回开/高/低/收/成交量，免去客户端各自实现
  - `get_financials(ts_code, statement, periods?)` / `get_index_components(index_code, date)` / `get_moneyflow(ts_code, start, end)` / `trade_calendar(start, end)`
  - `coverage_report(interface?, priority?)` →
    ```json
    {"interface":"daily","status":"healthy","last_sync":"2026-04-25T17:32:11+08:00","rows":12483920,"missing_dates":[],"sync_state_partial":0,"sync_state_failed":0}
    ```

#### 10.4 连接串

| 用途 | 串 |
|---|---|
| AI 批量分析（推荐） | `clickhouse+native://ai_reader:***@<host>:9000/tushare?compression=lz4` |
| Web 前端 / curl | `http://ai_reader:***@<host>:8123/?database=tushare&enable_http_compression=1` |
| MCP（本机） | `tushare-db mcp-serve --transport stdio` |
| MCP（局域网） | `http://<host>:7800/sse` |

#### 10.5 Windows 防火墙（一次性配置）

PowerShell 管理员执行：
```powershell
New-NetFirewallRule -DisplayName "ClickHouse-LAN" -Direction Inbound -LocalPort 8123,9000 -Protocol TCP -Action Allow -RemoteAddress "192.168.0.0/16","10.0.0.0/8","172.16.0.0/12"
New-NetFirewallRule -DisplayName "MCP-LAN" -Direction Inbound -LocalPort 7800 -Protocol TCP -Action Allow -RemoteAddress "192.168.0.0/16","10.0.0.0/8","172.16.0.0/12"
```

#### 10.6 前端凭证暴露

`Tushare_DB_Web/index.html` 嵌入 `ai_reader` 密码即明文。**评估**：(a) 仅在 LAN 内分发，配合 `host_regexp` 已隔离外网；(b) 该用户只读、零写权限，最坏情况是数据被读取（公开市场数据，非敏感）。**接受此风险**，不引入额外 OAuth。生产化时改为前端调用本地代理（mcp-serve）由其转发查询。

### 11. 规模预估
- 表数 = **185**（182 enabled + 3 元表）；付费 45 接口仅注册 spec，enable 时按需建表
- 行数 150–250M
- 压缩 10–25 GB，未压缩 80–200 GB；规划 **80 GB 余量**（保留三倍峰值缓冲，避免长跑撑爆）
- P0+P1 回补 12–18h（不含长尾，475/285 rpm 95% 利用率下）；per_symbol_period 长尾 **~7.85h/接口**（4 接口顺序 ~31h）；首次全量 48–60h
- ClickHouse 容器 mem limit 12GB；host 16GB RAM 下限
- 增量稳态：每日 A/B/C/D 四批次合计 ≤30 min（仅当日新增 trade_date）

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| Tushare 列集静默变化 | schema_evolver 只 ADD COLUMN，未知列落 `_extra String` 并 WARN |
| 429 风控 | 整桶 60s 冷却 + 指数退避；bucket 容量取 95%（最大化吞吐，少量 429 由退避吸收） |
| per_symbol_period 长尾 | 移出工作日批次到周六；支持 `--parallel-symbols N`（受 special bucket 限速，最多并发 6）；单元级检查点重启零浪费 |
| WSL2 Windows 挂载性能差 | ClickHouse 数据用 named volume 落 WSL2 ext4，不挂 Windows 目录 |
| 接口权限与默认清单不一致 | `tushare-db probe` 在 init 后探测真实权限自动更新 YAML |
| 数据卷损坏 | 接受重跑（用户已确认） |
| APScheduler jobstore 锁竞争 | **MemoryJobStore，零文件依赖**；job 定义在代码可重建；幂等保障在 `_meta.sync_state` |
| 硬盘空间撑爆 | `system.disks` 每小时检查；剩余 < 20 GB 时 scheduler 自动暂停新 backfill 并 alert |
| Tushare token 失效/被封 | 连续 5 次 401/403 → scheduler 自动暂停所有非 reference job；保留 `app.log` 详细堆栈；人工换 token 后 `tushare-db scheduler-run` 自动恢复 |
| probe/sample 配额消耗 | 单次约 227 + 182 = 409 calls，按 475 rpm 一次跑完不到 1 分钟；不计入每日积分（按 call 计数无配额） |
| Tushare 服务侧延迟 | 调度延迟兜底重试上限 2 次；超时则 weekly_reconcile 接管 |

## 监控与数据保留

#### 监控（Grafana → ClickHouse `_meta.*` + `system.*`，不引入 prometheus-client）

`docker/grafana/dashboards/` 内置 3 个 JSON dashboard，provisioning 自动加载：

| Dashboard | 关键 panel | 数据源 SQL |
|---|---|---|
| `pipeline_health.json` | 桶利用率、429 频次、API p99 延迟、failed 单元数 | `SELECT toStartOfMinute(started_at) m, count()/60 rps FROM _meta.api_calls WHERE started_at>now()-3600 GROUP BY m` |
| `data_coverage.json` | 各接口 last_success_at、行数趋势、缺日清单 | `SELECT interface, max(last_success_at), sum(rows) FROM _meta.sync_state FINAL GROUP BY interface` |
| `clickhouse_io.json` | parts 数、合并队列、磁盘使用、内存 | `SELECT * FROM system.parts/system.merges/system.disks` |

#### 数据保留窗口

| 制品 | 保留 | 落地 |
|---|---|---|
| `_meta.api_calls` | 90 天 | TTL 自动清理 |
| `_meta.sync_runs` | 365 天 | TTL `toDate(started_at) + INTERVAL 365 DAY` |
| `_meta.sync_state` | 永久 | 数据规模 ~10 万行可忽略 |
| `data/logs/app.log` | 50MB × 20 = 1GB | structlog RotatingFileHandler |
| `data/logs/api_audit.log` | 50MB × 20 = 1GB | 同上 |
| `data/samples/*.json` | 永久 | 体积小，便于 schema diff 回溯 |

## 验证计划

1. 单元：
   - rate_limiter 注入假时钟 + **多线程并发回归**（10 worker 同步抢 token，断言 1 分钟内实际 calls ≤ 桶上限）
   - planner strategies（六种 scope_key 格式生成断言）
   - schema inferer 金样本 diff
2. 集成（testcontainers + responses mock）：造 2 天假数据，重跑 2 次断言 0 重复
3. 回补正确性：daily 3 个月跑 2 遍，`countDistinct(ts_code, trade_date) == count(*)`，抽日对比实时返回
4. 增量幂等（**改用稳健指纹**）：`update --batch A` 连跑 2 次，第二次 `rows=0`，且
   ```sql
   SELECT count(), sum(cityHash64(*)), max(_version) FROM tushare.daily FINAL WHERE trade_date = today() - 1
   ```
   两次结果完全一致
5. 崩溃续跑：`backfill income 2020-2023` 子进程 30s 后 SIGKILL，重启跑完，行数 == 单次基线
6. 补洞：随机删 2 个 trade_date 行，`verify` 应全部检出并重取
7. 访问层：
   - 本机 Claude（stdio）通过 MCP `get_ohlcv` 返回正确行（含复权计算）
   - LAN 机器 `clickhouse-client --user=ai_reader` 执行 SELECT 成功、INSERT 被拒
   - LAN 浏览器 fetch ClickHouse 8123 with `Origin: http://...` 返回 200（CORS 通）
8. 关机补跑：关机 2 天后开机，A/B/C/D 在 `misfire_grace_time` 内各补跑一次
9. **吞吐量基准**：`backfill --interface daily --from 20240101 --to 20240630` 实测 elapsed ≤ `(125 trade_dates × 84 接口 ÷ 475 rpm) × 1.1` ≈ 24 min；超出该数 1.5x 触发性能回归告警

## 实施阶段（含 Skills/Agents 使用）

| PR | 内容 | 主要 Skills/Agents |
|----|------|---------------------|
| **PR1 骨架** | pyproject + docker-compose（ClickHouse 用 WSL2 named volume，含 healthcheck/depends_on/restart）+ ClickHouse 配置 + 全部 227 个 `config/interfaces/*.yaml` + `config/loader.py` + `meta/bootstrap.py` + `cli init`。**仅建 `_meta.*` 元表 + 空 `tushare` 数据库**；业务表 DDL 留到 PR2 sample → infer 后批量 CREATE，**不在 PR1 创建 230 张占位表**（避免无 schema 强行建表的回填代价） | docker-patterns, clickhouse-io, planner |
| **PR2 采集引擎** | `core/rate_limiter` + `core/tushare_client` + `schema/inferer/ddl_builder/evolver` + `sink/clickhouse_sink` + `scripts/sample_api_responses.py` + `runner/worker.py` + `planner/strategies.py` + `cli probe/sample-apis/rebuild-schema`。**业务表 DDL 在本 PR 内 sample → infer → 批量 CREATE**（仅 `enabled:true` 的 182 张；付费 45 张仅注册 spec 不建表） | tdd-guide, python-reviewer |
| **PR3 回补 + 检查点** | `runner/backfill.py`（支持 --layer 与 --priority）+ `meta/sync_state` + `cli backfill/status/resume` + SIGKILL 续跑 e2e 测试 | tdd-guide, python-reviewer, e2e-runner |
| **PR4 调度 + 增量** | `scheduler/jobs.py`（A/B/C/D + 周六长尾 + 健康检查）+ `scheduler/service.py`（MemoryJobStore）+ `runner/incremental` | tdd-guide, python-reviewer |
| **PR5 访问层** | `mcp_server/*` + ClickHouse `ai_reader` 用户（仅 readonly=2）+ 本机+LAN 客户端验证 | mcp-server-patterns, security-reviewer |
| **PR6 验证与监控** | `verify/*`（gap_detector, row_counts, checksums）+ Grafana dashboard（`_meta.*` + `system.parts` + 限速指标）+ weekly_reconcile + `cli verify` | doc-updater, e2e-runner |
| **PR7 前端仪表盘** | 见 `a-frontend-dashboard-spec.md`：Vue 3 + Naive UI + ECharts 单文件应用，直连 ClickHouse HTTP | frontend-patterns |

**全流程**：每次代码写完调 python-reviewer；构建/类型问题用 build-error-resolver；架构变更用 architect。

## 待办（已全部决议）

- 调度方案：四批次 + 周六长尾 ✓
- WSL2 文件系统：ClickHouse 落 WSL2 ext4 named volume ✓
- APScheduler jobstore：MemoryJobStore ✓
- ai_reader 权限放宽（仅 readonly=2）✓
- 五层回补顺序 ✓

如果在实施过程中发现接口权限与 10k 默认清单偏差较大（比如已扩包了某些 special 接口），由 `tushare-db probe` 自动调整 YAML 即可，不需要重设计。

## 关键依赖（pyproject.toml）

```toml
[project]
requires-python = ">=3.11"
dependencies = [
  "tushare>=1.4.20",
  "clickhouse-connect>=0.7.19",
  "httpx[http2]>=0.27",
  "apscheduler>=3.10.4",
  "pydantic>=2.7", "pydantic-settings>=2.3",
  "pyyaml>=6.0", "click>=8.1", "rich>=13.7",
  "structlog>=24.1", "tenacity>=8.3",
  "pandas>=2.2", "pyarrow>=16.0", "xxhash>=3.4",
  "mcp>=1.0", "python-dotenv>=1.0",
  "prometheus-client>=0.20", "pytz>=2024.1",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2", "pytest-cov>=5.0", "pytest-asyncio>=0.23",
  "responses>=0.25", "vcrpy>=6.0",
  "testcontainers[clickhouse]>=4.5",
  "ruff>=0.4", "mypy>=1.10",
]
```

锁定方式：**`uv` + `uv.lock`** （CI 与本地一致，安装快）。

## docker-compose 编排

```yaml
services:
  clickhouse:
    image: clickhouse/clickhouse-server:24.8
    restart: unless-stopped
    ports: ["8123:8123", "9000:9000"]
    volumes:
      - clickhouse_data:/var/lib/clickhouse           # WSL2 ext4 named volume
      - ./docker/clickhouse/config.xml:/etc/clickhouse-server/config.d/00-custom.xml:ro
      - ./docker/clickhouse/users.xml:/etc/clickhouse-server/users.d/00-users.xml:ro
      - ./docker/clickhouse/init:/docker-entrypoint-initdb.d:ro
    environment:
      CH_PIPELINE_PASSWORD: ${CH_PIPELINE_PASSWORD}
      CH_AI_READER_PASSWORD: ${CH_AI_READER_PASSWORD}
      CH_GRAFANA_PASSWORD: ${CH_GRAFANA_PASSWORD}
    deploy:
      resources:
        limits: {memory: 12G}
    healthcheck:
      test: ["CMD-SHELL", "wget --quiet --tries=1 -O /dev/null http://localhost:8123/ping || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 5

  pipeline:
    build: ./docker/pipeline
    restart: unless-stopped
    ports: ["7800:7800"]                              # MCP SSE 与 scheduler 同进程
    depends_on:
      clickhouse: {condition: service_healthy}
    volumes:
      - ./config:/app/config:ro
      - ./data/logs:/app/data/logs
      - ./data/samples:/app/data/samples
    environment:
      TUSHARE_TOKEN: ${TUSHARE_TOKEN}
      CH_HOST: clickhouse
      CH_PIPELINE_PASSWORD: ${CH_PIPELINE_PASSWORD}
    command: ["sh", "-c", "tushare-db scheduler-run & tushare-db mcp-serve --transport sse --host 0.0.0.0 --port 7800 && wait"]

  grafana:
    image: grafana/grafana:11.0.0
    restart: unless-stopped
    ports: ["3000:3000"]
    depends_on:
      clickhouse: {condition: service_healthy}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./docker/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./docker/grafana/dashboards:/var/lib/grafana/dashboards:ro

volumes:
  clickhouse_data:
  grafana_data:
```

**MCP 与 scheduler 同进程**：节省内存 + 共享配置；如未来需独立扩容再拆。

`.env.example`：
```
TUSHARE_TOKEN=your_10k_token_here
CH_PIPELINE_PASSWORD=change_me_pipeline
CH_AI_READER_PASSWORD=change_me_ai_reader
CH_GRAFANA_PASSWORD=change_me_grafana
```

## 附录 A：182 接口归属总表

> 由 `tools/dump_interface_routing.py` 从 `config/interfaces/*.yaml` 自动生成，本表为初版基线，最终以 YAML 为准。`tushare-db probe` 会在 init 后回写校准。

| interface | bucket | strategy | batch |
|---|---|---|---|
| stock_basic | normal | full_once | reference |
| trade_cal | normal | full_once | reference |
| stock_company | normal | full_once | reference |
| stock_hsgt | normal | full_once | reference |
| fund_basic | normal | full_once | reference |
| fund_company | normal | full_once | reference |
| etf_basic | normal | full_once | reference |
| etf_index | normal | full_once | reference |
| index_basic | normal | full_once | reference |
| fut_basic | normal | full_once | reference |
| fut_trade_cal | normal | full_once | reference |
| cb_basic | normal | full_once | reference |
| opt_basic | normal | full_once | reference |
| sge_basic | normal | full_once | reference |
| fx_obasic | normal | full_once | reference |
| bse_mapping | normal | full_once | reference |
| stk_managers | normal | full_once | reference |
| stk_rewards | normal | full_once | reference |
| namechange | normal | full_once | reference |
| new_share | normal | date_loop | reference |
| index_classify | special | full_once | reference |
| ci_index_member | special | full_once | reference |
| daily | normal | date_loop | A |
| weekly | normal | date_loop | A |
| monthly | normal | date_loop | A |
| adj_factor | normal | date_loop | A |
| daily_basic | special | date_loop | A |
| suspend_d | normal | date_loop | A |
| stk_limit | special | date_loop | A |
| stk_premarket | special | date_loop | A |
| bak_basic | special | full_once | A |
| bak_daily | special | date_loop | A |
| stk_weekly_monthly | special | date_loop | A |
| stk_week_month_adj | special | date_loop | A |
| ggt_daily | special | date_loop | A |
| ggt_top10 | special | date_loop | A |
| hsgt_top10 | special | date_loop | A |
| ggt_monthly | special | date_loop | A |
| index_daily | special | date_loop | A |
| index_weekly | special | date_loop | A |
| index_monthly | special | date_loop | A |
| index_dailybasic | special | date_loop | A |
| index_weight | special | monthly_window | A |
| index_member_all | special | full_once | A |
| sw_daily | special | date_loop | A |
| ci_daily | special | date_loop | A |
| daily_info | special | date_loop | A |
| sz_daily_info | special | date_loop | A |
| idx_factor_pro | special | date_loop | A |
| index_global | special | date_loop | A |
| cb_daily | normal | date_loop | A |
| cb_issue | normal | date_loop | A |
| cb_share | normal | date_loop | A |
| cb_rate | normal | period_loop | A |
| cb_price_chg | normal | date_loop | A |
| bond_blk | normal | date_loop | A |
| bond_blk_detail | normal | date_loop | A |
| repo_daily | normal | date_loop | A |
| yc_cb | normal | date_loop | A |
| eco_cal | normal | date_loop | A |
| bc_otcqt | normal | date_loop | A |
| bc_bestotcqt | normal | date_loop | A |
| fund_daily | normal | date_loop | A |
| fund_adj | normal | date_loop | A |
| fund_nav | normal | monthly_window | A |
| fund_div | normal | date_loop | A |
| fund_portfolio | normal | period_loop | A |
| fund_share | normal | date_loop | A |
| fund_manager | normal | full_once | A |
| fut_daily | normal | date_loop | A |
| fut_holding | normal | date_loop | A |
| fut_wsr | normal | date_loop | A |
| fut_settle | normal | date_loop | A |
| fut_mapping | normal | full_once | A |
| fut_weekly_detail | normal | date_loop | A |
| fut_weekly_monthly | normal | date_loop | A |
| fut_index_daily | normal | date_loop | A |
| opt_daily | normal | date_loop | A |
| sge_daily | normal | date_loop | A |
| fx_daily | normal | date_loop | A |
| moneyflow | special | date_loop | B |
| moneyflow_hsgt | special | date_loop | B |
| moneyflow_ind_ths | special | date_loop | B |
| moneyflow_ind_dc | special | date_loop | B |
| moneyflow_mkt_dc | special | date_loop | B |
| moneyflow_ths | special | date_loop | B |
| moneyflow_dc | special | date_loop | B |
| moneyflow_cnt_ths | special | date_loop | B |
| margin | special | date_loop | B |
| margin_detail | special | date_loop | B |
| margin_secs | special | date_loop | B |
| slb_len | special | date_loop | B |
| repurchase | special | date_loop | B |
| pledge_stat | special | date_loop | B |
| pledge_detail | special | date_loop | B |
| share_float | special | date_loop | B |
| block_trade | special | date_loop | B |
| stk_holdernumber | special | date_loop | B |
| limit_list_d | special | date_loop | C |
| limit_list_ths | special | date_loop | C |
| limit_step | special | date_loop | C |
| limit_cpt_list | special | date_loop | C |
| top_list | special | date_loop | C |
| top_inst | special | date_loop | C |
| ths_index | special | full_once | C |
| ths_daily | special | date_loop | C |
| ths_member | special | full_once | C |
| ths_hot | special | date_loop | C |
| dc_index | special | full_once | C |
| dc_daily | special | date_loop | C |
| dc_member | special | full_once | C |
| dc_hot | special | date_loop | C |
| hm_list | special | full_once | C |
| hm_detail | special | date_loop | C |
| kpl_list | special | date_loop | C |
| kpl_concept_cons | special | full_once | C |
| tdx_index | special | full_once | C |
| tdx_member | special | full_once | C |
| tdx_daily | special | date_loop | C |
| stk_auction | special | date_loop | C |
| stk_auction_o | special | date_loop | C |
| stk_auction_c | special | date_loop | C |
| hk_hold | special | date_loop | C |
| ccass_hold | special | date_loop | C |
| ccass_hold_detail | special | date_loop | C |
| stk_surv | special | date_loop | C |
| stk_nineturn | special | date_loop | C |
| cyq_perf | special | date_loop | C |
| cyq_chips | special | date_loop | C |
| report_rc | special | date_loop | C |
| broker_recommend | special | date_loop | C |
| stk_ah_comparison | special | date_loop | C |
| stock_st | special | date_loop | C |
| cn_gdp | normal | period_loop | D |
| cn_cpi | normal | period_loop | D |
| cn_ppi | normal | period_loop | D |
| cn_pmi | normal | period_loop | D |
| cn_m | normal | period_loop | D |
| sf_month | normal | period_loop | D |
| shibor | normal | date_loop | D |
| shibor_lpr | normal | date_loop | D |
| shibor_quote | normal | date_loop | D |
| libor | normal | date_loop | D |
| hibor | normal | date_loop | D |
| wz_index | normal | period_loop | D |
| gz_index | normal | period_loop | D |
| us_tycr | normal | period_loop | D |
| us_tbr | normal | period_loop | D |
| us_trycr | normal | period_loop | D |
| us_tltr | normal | period_loop | D |
| us_trltr | normal | period_loop | D |
| income | special | period_loop | D |
| balancesheet | special | period_loop | D |
| cashflow | special | period_loop | D |
| fina_indicator | special | period_loop | D |
| fina_audit | special | period_loop | D |
| dividend | special | period_loop | D |
| forecast | special | period_loop | D |
| express | special | period_loop | D |
| disclosure_date | special | full_once | D |
| bo_daily | normal | date_loop | D |
| bo_weekly | normal | date_loop | D |
| bo_monthly | normal | date_loop | D |
| bo_cinema | normal | date_loop | D |
| film_record | normal | date_loop | D |
| teleplay_record | normal | date_loop | D |
| tmt_twincome | normal | date_loop | D |
| tmt_twincomedetail | normal | date_loop | D |
| fund_sales_ratio | normal | date_loop | D |
| fund_sales_vol | normal | date_loop | D |
| stk_factor_pro | special | date_loop | D |
| cb_factor_pro | special | date_loop | D |
| fund_factor_pro | special | date_loop | D |
| ft_limit | special | date_loop | D |
| etf_share_size | special | date_loop | D |
| fina_mainbz | special | per_symbol_period | saturday |
| top10_holders | special | per_symbol_period | saturday |
| top10_floatholders | special | per_symbol_period | saturday |
| stk_holdertrade | special | per_symbol_period | saturday |
| stk_account_old | normal | period_loop | D |
| stk_account | normal | period_loop | D |
| stk_holdernumber | special | period_loop | B |

**7 个特殊起点接口**已在表中（bak_basic / stk_account_old=20080101 / fund_sales_vol / hm_detail / stk_nineturn / moneyflow_dc / limit_list_ths），其 `start_date` 写入对应 YAML，回补脚本自动识别。

**汇总**：reference 22 + A 58 + B 18 + C 35 + D 43 + saturday 4 = **180**（与权威值 182 相差 ≤2 在 probe 探测后通过 YAML 校正；本表初版仅作开工依据）。

## 备注：已知遗留细节（不阻塞开工）

| # | 问题 | 影响 | 解决时机 |
|---|------|------|---------|
| 1 | `dc_daily` 特殊起点日期缺失（应与 moneyflow_dc 同为 20230911） | planner 多算 ~750 个无效单元，多浪费约 25 分钟 API 调用 | PR1 写 YAML 时补上 |
| 2 | `per_symbol_period` 是否确认只有 4 个（当前：fina_mainbz, top10_holders, top10_floatholders, stk_holdertrade） | 若有第 5 个混入工作日批次，该接口 14h 拖住整条线 | PR2 planner 按 `fetch_strategy.kind` 动态判断，自动归入 saturday |
| 3 | Layer 0 品种基础表是否补全（bond_basic, etf_basic, fut_basic, opt_basic） | 无实质影响，`batch=reference` 自动覆盖 | PR1 写 YAML 时补全 |
| 4 | 7 个特殊起点接口的 batch 归属需明确 | 无实质影响，probe 自动校准 | PR1 写 YAML 时标注 |

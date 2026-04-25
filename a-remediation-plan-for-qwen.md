# Tushare DB — 项目剩余 25% 工作 + 缺陷修复指南

> 面向：VSCode + Claude Code 插件 + Qwen 3.6 Plus（执行者）
> 文档作者：Sonnet 4.6（审计者）
> 生成日期：2026-04-25
>
> 用途：在 `data/logs/completion_report.md` 声称"PR1-PR7 全部完成"之后，对源码做了一次完整审计。本文档列出**所有**与设计文档（`a-ai-ai-tushare-pro-kind-gizmo.md`）不符的缺陷、bug，以及**Qwen 必须如何修**。
>
> **阅读顺序**：先看 §0 全景表 → 按 P0/P1/P2 优先级顺序修 → §10 验证清单。

---

## 0. 全景：23 个待办事项

| ID | 严重度 | 类别 | 文件 | 一句话描述 |
|----|--------|------|------|-----------|
| **B1** | 🔴 **P0** | 数据正确性 | `runner/worker.py:267` | `_normalize_items` 不调用 `normalize_value`，所有 Decimal64(2) 财务值差 10000 倍 |
| **B2** | 🔴 **P0** | 性能 | `runner/executor.py:32` | `max_workers=1`，12/6 worker 设计形同虚设，回补慢 5-8 倍 |
| **B3** | 🔴 **P0** | 功能不可用 | `mcp_server/tools.py:32` | `_get_client` 用 9000 端口，但 `clickhouse_connect` 仅支持 HTTP（8123），MCP 全部工具连不上 |
| **B4** | 🔴 **P0** | 功能错误 | `mcp_server/tools.py:115-148` | `get_ohlcv` 引用了 `tushare_stock_daily` 中不存在的列 `d.adj_factor`，qfq/hfq 必报错 |
| **B5** | 🔴 **P0** | 类型映射 | `schema/type_map.py:20-24` | `_FINANCIAL_AMOUNT_SUFFIXES` 把 `total_` 同时当前缀和后缀，`total_share`（数量字段）会被误标 Decimal64(2) |
| **B6** | 🔴 **P0** | 部署 | `docker-compose.yml` | 缺 dashboard nginx 服务，前端 SPA 因 CORS 跑不起来 |
| **B7** | 🟡 P1 | 容器健壮性 | `docker-compose.yml:38` | `scheduler-run & mcp-serve && wait` 进程托管脆弱，子进程 crash 不会让容器退出 |
| **B8** | 🟡 P1 | 冷启动竞态 | `scheduler/jobs.py:64` | scheduler 在 `bootstrap` 之前启动会因 `_meta.trade_cal` 为空而静默跳过所有批次 |
| **B9** | 🟡 P1 | 设计偏差 | `mcp_server/tools.py` | MCP 响应未实现 LZ4 + Arrow IPC（设计 §10），返回纯 JSON |
| **B10** | 🟡 P1 | 模块化 | `cli.py:417-500` | backfill 编排和 `_get_layer` 内联在 CLI，未独立成 `runner/backfill.py`，无法被调度器复用 |
| **B11** | 🟡 P1 | bootstrap 缺口 | bootstrap 153/182 表 | 设计 §11 要求 ≥175 张，缺 29 张可能影响下游查询 |
| **B12** | 🟡 P1 | 错误处理 | `core/tushare_client.py` | tenacity 对通用 `TushareError` 也重试，500/503 等服务端错误会被遮蔽 |
| **B13** | 🟡 P1 | 测试 | `tests/integration/` 目录空 | 设计要求 60/30/10 金字塔，集成测试 0 |
| **B14** | 🟡 P1 | 测试 | `tests/unit/test_sync_state_heartbeat.py` | 仅断言 SQL 字符串 + mock 线程，未真实测试 worker 心跳与 DB 交互 |
| **B15** | 🟡 P1 | 覆盖率 | 总体 | 总覆盖率 20%，未达 80%（核心模块达标但 CLI/MCP/verify 几乎为零） |
| **B16** | 🟡 P1 | Tushare 客户端 | `core/tushare_client.py` | 401/403/404 抛 `TushareAuthError` 但 `503` 抛通用 `TushareError`，分类粒度不够 |
| **B17** | 🟢 P2 | 设计偏差 | `verify/checksums.py:62` | 用 `sum(cityHash64(*))` 而非设计 §5.4 推荐的 `argMax + groupBitXor`（行序敏感） |
| **B18** | 🟢 P2 | 探针 | `cli.py probe` | 探测后只打印结果，**未回写 YAML enabled 字段**（设计 §9 要求） |
| **B19** | 🟢 P2 | Schema 演进 | `schema/evolver.py` | 仅支持 ADD COLUMN，未支持影子表迁移（重命名 / 类型变更） |
| **B20** | 🟢 P2 | 监控 | `docker/grafana/` | 未声明 `GF_INSTALL_PLUGINS=grafana-clickhouse-datasource`，3 个 dashboard 加载失败 |
| **B21** | 🟢 P2 | 数据校验 | `verify/gap_detector.py` | gap 检测只对 daily 类，财务表 / 周末数据未覆盖 |
| **B22** | 🟢 P2 | 文档差异 | `data/samples/` 161 份 vs 153 表 | 报告数与实际不一致，需对账（多 8 份样本可能是脏数据） |
| **B23** | 🟢 P2 | 前端 | `dashboard/index.html` | 默认 `localhost:8123` 硬编码，缺自动注入连接串 |

---

## 1. P0 致命问题（不修就不能用）

### B1. 财务值差 10000 倍 ⚠️ 最致命

**位置**：`src/tushare_db/runner/worker.py:267-281`

**现状**：
```python
def _normalize_items(fields: list[str], items: list[list]) -> list[list]:
    """Normalize date strings from YYYYMMDD to datetime.date for ClickHouse Date type."""
    normalized = []
    date_indices = [i for i, f in enumerate(fields) if "date" in f.lower() or "ann_date" in f.lower()]

    for item in items:
        row = list(item)
        for idx in date_indices:
            if idx < len(row) and row[idx] and isinstance(row[idx], str):
                val = row[idx].strip()
                if len(val) == 8 and val.isdigit():
                    row[idx] = datetime.strptime(val, "%Y%m%d").date()
        normalized.append(row)

    return normalized
```

**问题**：
- 只处理日期归一化，**完全没调用 `type_map.normalize_value()`**
- `schema/type_map.py:95-123` 已经写好 `normalize_value()`（万元→元、万份→份），但是死代码

**影响**：
- 所有 `Decimal64(2)` 字段（`total_revenue`, `n_income`, `total_assets`, `total_mv`, `circ_mv`, `oper_cost`, `total_profit` 等）按"万元"原值入库
- 实际查询时金额比真实值小 10000 倍
- 多因子打分、ROE 排名、PE/PB 计算、市值筛选**全部错误**
- Qwen 之前没发现是因为没真正跑过财务查询对账

**修复**（diff 风格）：

需要给 `_normalize_items` 增加 schema 感知能力。最简方案是从 ClickHouse `system.columns` 查列类型，再调 `normalize_value`：

```python
# src/tushare_db/runner/worker.py

from tushare_db.schema.type_map import normalize_value

# 在文件顶部增加缓存
_COLUMN_TYPE_CACHE: dict[str, dict[str, str]] = {}


def _get_column_types(
    ch_client: clickhouse_connect.driver.Client,
    table: str,
    database: str = "tushare",
) -> dict[str, str]:
    """Lazy-load column types for a table; cache per-process."""
    cache_key = f"{database}.{table}"
    if cache_key in _COLUMN_TYPE_CACHE:
        return _COLUMN_TYPE_CACHE[cache_key]

    result = ch_client.query(
        f"SELECT name, type FROM system.columns "
        f"WHERE database = '{database}' AND table = '{table}'"
    )
    type_map = {row[0]: row[1] for row in result.result_rows}
    _COLUMN_TYPE_CACHE[cache_key] = type_map
    return type_map


def _normalize_items(
    fields: list[str],
    items: list[list],
    column_types: dict[str, str] | None = None,  # 新增参数
) -> list[list]:
    """Normalize values: dates + 万元→元 + 万份→份."""
    normalized = []
    date_indices = [i for i, f in enumerate(fields) if "date" in f.lower()]
    column_types = column_types or {}

    for item in items:
        row = list(item)

        # 1. Date normalization (existing)
        for idx in date_indices:
            if idx < len(row) and row[idx] and isinstance(row[idx], str):
                val = row[idx].strip()
                if len(val) == 8 and val.isdigit():
                    row[idx] = datetime.strptime(val, "%Y%m%d").date()

        # 2. 万元/万份 normalization (NEW)
        for idx, field_name in enumerate(fields):
            ch_type = column_types.get(field_name, "")
            if ch_type.startswith("Decimal64") or ch_type.startswith("Nullable(Decimal64"):
                row[idx] = normalize_value(field_name, ch_type.replace("Nullable(", "").rstrip(")"), row[idx])

        normalized.append(row)

    return normalized
```

并修改 `execute_unit` 调用点（约 worker.py:223 行附近）：

```python
        # Normalize dates in items
-       normalized_items = _normalize_items(fields, items)
+       column_types = _get_column_types(ch_client, unit.table)
+       normalized_items = _normalize_items(fields, items, column_types=column_types)
```

**测试方案**：
1. 单元测试：mock `column_types={"total_revenue": "Decimal64(2)"}`，传入 `[[100.5]]`，断言结果 `[[1005000.0]]`
2. 集成测试：真起 ClickHouse，写入一条 `tushare_income` 记录，查询验证值已 ×10000

**回滚风险**：低。如果 `column_types` 拿不到（表不存在），fallback 为只做日期归一化，不会写错数据，只是没归一化。

---

### B2. 单线程吞吐 → 全量回补慢 5-8 倍

**位置**：`src/tushare_db/runner/executor.py:32`

**现状**：
```python
def execute_batch(
    units: list[WorkUnit],
    tushare_client: TushareClient,
    ch_client: clickhouse_connect.driver.Client,
    run_id: uuid.UUID | None = None,
    max_workers: int = 1,  # ⚠️ 设计要求 normal=12 / special=6
) -> tuple[int, int, int]:
```

**问题**：
- 设计文档 §3 + §11 要求 normal bucket 12 worker，special bucket 6 worker，95% 限流利用率
- 实际单线程跑 → 全量历史回补预计从 18 小时变成 100+ 小时
- 注释说"clickhouse_connect HTTP client 不支持并发"，但其实 clickhouse_connect ≥ 0.7 是线程安全的（每个 client 实例内部有连接池）

**修复方案**（最稳妥：每 worker 独立 client）：

```python
# src/tushare_db/runner/executor.py

from __future__ import annotations

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import clickhouse_connect
import clickhouse_connect.driver
import structlog

from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.strategies import WorkUnit
from tushare_db.runner.worker import execute_unit

logger = structlog.get_logger()

_thread_local = threading.local()


def _get_thread_ch_client() -> clickhouse_connect.driver.Client:
    """Return a thread-local ClickHouse client (connection pool per worker)."""
    if not hasattr(_thread_local, "client"):
        _thread_local.client = clickhouse_connect.get_client(
            host=os.environ.get("CH_HOST", "localhost"),
            port=int(os.environ.get("CH_HTTP_PORT", "8123")),
            username="pipeline",
            password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
            database="tushare",
        )
    return _thread_local.client


def execute_batch(
    units: list[WorkUnit],
    tushare_client: TushareClient,
    ch_client: clickhouse_connect.driver.Client,  # 仅作主线程兜底，不传给 worker
    run_id: uuid.UUID | None = None,
    max_workers: int | None = None,
) -> tuple[int, int, int]:
    """Execute work units concurrently with per-worker ClickHouse clients.

    Each worker thread holds its own clickhouse_connect.Client (thread-local),
    avoiding shared-state races on the HTTP client.
    """
    if run_id is None:
        run_id = uuid.uuid4()

    # 按 bucket 切分 normal/special 单元，分别走 12 / 6 worker
    normal_units = [u for u in units if u.bucket == "normal"]
    special_units = [u for u in units if u.bucket == "special"]

    done_count = 0
    failed_count = 0
    total_rows = 0

    def _run(unit_list, workers):
        nonlocal done_count, failed_count, total_rows
        if not unit_list:
            return

        def _wrapped(unit):
            client = _get_thread_ch_client()
            return execute_unit(unit, tushare_client, client, run_id)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_wrapped, u): u for u in unit_list}
            for fut in as_completed(futures):
                unit = futures[fut]
                try:
                    result = fut.result()
                    if result >= 0:  # 0 行也算成功
                        done_count += 1
                        total_rows += max(result, 0)
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error("Unit crashed", interface=unit.interface,
                                 scope_key=unit.scope_key, error=str(e))

    # 默认 12 / 6，可通过 env 调整
    nw = int(os.environ.get("TUSHARE_NORMAL_WORKERS", "12"))
    sw = int(os.environ.get("TUSHARE_SPECIAL_WORKERS", "6"))
    if max_workers is not None:  # 显式覆盖
        nw = sw = max_workers

    _run(normal_units, nw)
    _run(special_units, sw)

    logger.info("Batch complete", total=len(units),
                done=done_count, failed=failed_count, rows=total_rows)
    return len(units), done_count, failed_count
```

**注意事项**：
- 入参 `ch_client` 仍保留以维持调用约定，但不传给 worker
- 测试 `test_idempotent_replay.py` 与 `test_sigkill_resume.py` 可能依赖单线程顺序，需检查
- 必须复测 `core/rate_limiter.py` 的并发独立性（已有 `test_rate_limiter_concurrent.py` 覆盖）

**测试方案**：
1. 在 ClickHouse 容器中跑 `tushare-db backfill --interface daily --from 20240101 --to 20240131`，对比 `max_workers=1` vs `max_workers=12` 的耗时
2. 用 `responses` mock 100 个 unit，断言完成时间 < 单线程 / 8

---

### B3. MCP 端口错误 → 所有工具连不上

**位置**：`src/tushare_db/mcp_server/tools.py:32`

**现状**：
```python
def _get_client() -> clickhouse_connect.driver.Client:
    """Get ClickHouse client for MCP queries (native protocol)."""
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_TCP_PORT", "9000")),  # ⚠️ 错误！9000 是 Native，但 clickhouse_connect 只支持 HTTP
        ...
    )
```

**问题**：
- `clickhouse_connect` 自 0.7 起仅支持 HTTP 协议
- 9000 端口是 ClickHouse Native TCP，clickhouse_connect 连进去会失败
- 所有 MCP 工具（query_sql, get_ohlcv, list_interfaces, ...）实际无法工作
- 注释里的 "(native protocol)" 是错的

**修复**：

```python
def _get_client() -> clickhouse_connect.driver.Client:
    """Get ClickHouse client for MCP queries (HTTP protocol)."""
    import clickhouse_connect

    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),  # ✅ HTTP 8123
        user="ai_reader",
        password=os.environ.get("CH_AI_READER_PASSWORD", ""),
        database="tushare",
    )
```

并删掉误导性注释，确认 `CH_TCP_PORT` 在 `.env.example` 不再被提及。

**测试方案**：
1. 起 docker → `tushare-db mcp-serve --transport sse --port 7800`
2. `curl http://localhost:7800/sse` 看 SSE 握手
3. 通过 MCP 协议调用 `query_sql("SELECT 1")` 应返回 `[{"1": 1}]`

---

### B4. get_ohlcv 引用不存在的列 + 复权公式错误

**位置**：`src/tushare_db/mcp_server/tools.py:115-148`

**现状**：
```python
sql = (
    f"SELECT d.trade_date, "
    f"round(d.open * f.adj_factor / d.adj_factor, 4) as open, "  # ⚠️ d.adj_factor 不存在
    ...
    f"FROM tushare.tushare_stock_daily d "
    f"ANY LEFT JOIN (SELECT ts_code, adj_factor FROM tushare.tushare_adj_factor "
    f"WHERE ts_code = '{ts_code}' ORDER BY trade_date DESC LIMIT 1) f "
    f"ON d.ts_code = f.ts_code "
    ...
)
```

**问题**：
1. **`tushare_stock_daily` 没有 `adj_factor` 列**（Tushare daily 接口不返回它），SQL 直接报 `Unknown identifier`
2. 即使列存在，子查询 `f` 只取了"最新一行"——所有 d.row 都对同一个 f.adj_factor，公式失去**逐日 adj_factor** 的意义
3. 设计 §10 + futureplan 食谱 Q1 的正确公式是：

   ```sql
   d.open * af.adj_factor / latest.adj_factor  -- qfq
   d.open * af.adj_factor                       -- hfq
   ```

   其中 `af` 是逐日 JOIN，`latest` 是该 ts_code 最新一行（cross join）

**修复**：

```python
@mcp.tool()
def get_ohlcv(
    ts_code: str,
    start_date: str,
    end_date: str,
    adjust: str = "qfq",
) -> list[dict[str, Any]]:
    """Get OHLCV with proper qfq/hfq via per-row adj_factor JOIN."""
    client = _get_client()
    try:
        if adjust == "none":
            sql = (
                f"SELECT trade_date, open, high, low, close, vol, amount, pct_chg "
                f"FROM tushare.tushare_stock_daily FINAL "
                f"WHERE ts_code = '{ts_code}' "
                f"AND trade_date >= '{start_date}' AND trade_date <= '{end_date}' "
                f"ORDER BY trade_date"
            )
        elif adjust == "qfq":
            sql = (
                f"WITH latest AS ("
                f"  SELECT adj_factor FROM tushare.tushare_adj_factor FINAL "
                f"  WHERE ts_code = '{ts_code}' ORDER BY trade_date DESC LIMIT 1"
                f") "
                f"SELECT d.trade_date, "
                f"round(d.open  * af.adj_factor / latest.adj_factor, 4) AS open, "
                f"round(d.high  * af.adj_factor / latest.adj_factor, 4) AS high, "
                f"round(d.low   * af.adj_factor / latest.adj_factor, 4) AS low, "
                f"round(d.close * af.adj_factor / latest.adj_factor, 4) AS close, "
                f"d.vol, d.amount, d.pct_chg "
                f"FROM tushare.tushare_stock_daily FINAL d "
                f"INNER JOIN tushare.tushare_adj_factor FINAL af "
                f"  ON d.ts_code = af.ts_code AND d.trade_date = af.trade_date "
                f"CROSS JOIN latest "
                f"WHERE d.ts_code = '{ts_code}' "
                f"AND d.trade_date >= '{start_date}' AND d.trade_date <= '{end_date}' "
                f"ORDER BY d.trade_date"
            )
        elif adjust == "hfq":
            sql = (
                f"SELECT d.trade_date, "
                f"round(d.open  * af.adj_factor, 4) AS open, "
                f"round(d.high  * af.adj_factor, 4) AS high, "
                f"round(d.low   * af.adj_factor, 4) AS low, "
                f"round(d.close * af.adj_factor, 4) AS close, "
                f"d.vol, d.amount, d.pct_chg "
                f"FROM tushare.tushare_stock_daily FINAL d "
                f"INNER JOIN tushare.tushare_adj_factor FINAL af "
                f"  ON d.ts_code = af.ts_code AND d.trade_date = af.trade_date "
                f"WHERE d.ts_code = '{ts_code}' "
                f"AND d.trade_date >= '{start_date}' AND d.trade_date <= '{end_date}' "
                f"ORDER BY d.trade_date"
            )
        else:
            raise ValueError(f"adjust must be qfq/hfq/none, got {adjust!r}")

        return _safe_query(client, sql)
    finally:
        client.close()
```

**关键修正**：
- INNER JOIN `tushare_adj_factor` 是**逐日**对齐
- qfq 用 `WITH latest AS (...)` + CROSS JOIN 取最新基准
- 全部 ReplacingMergeTree 表加 `FINAL`
- 用 INNER JOIN 而非 LEFT JOIN（停牌日 daily 与 adj_factor 都无数据，不该补 NULL）

**测试方案**：
1. 准备一只有送转的股票（如 `600519.SH`）
2. 调用 `get_ohlcv("600519.SH", "20100101", "20250101", adjust="qfq")`
3. 断言：起点价 < 终点价（除权后回视）；终点价 ≈ 实际收盘
4. 调用 hfq，断言：起点价 = 原始价；终点价 > 原始价

---

### B5. Decimal64 后缀清单冲突

**位置**：`src/tushare_db/schema/type_map.py:20-24`

**现状**：
```python
_FINANCIAL_AMOUNT_SUFFIXES = (
    "_amount", "_revenue", "_profit", "_cost", "_income",
    "_expense", "_asset", "_liability", "_equity",
    "total_",  # ⚠️ 既当前缀又当后缀
)
```

**问题**：
- `_needs_financial_normalization` 同时检查 endswith 和 startswith `total_`
- `total_share`（A 股总股本，单位"股"，**不是金额**）会被误标 `Decimal64(2)` 并 ×10000
- 类似的：`total_market_value` 是金额（×10000 对），但 `total_share` / `total_holders` 不是

**修复**：

```python
# src/tushare_db/schema/type_map.py

# Suffixes that ALWAYS denote 万元 amounts
_FINANCIAL_AMOUNT_SUFFIXES = (
    "_amount", "_revenue", "_profit", "_cost", "_income",
    "_expense", "_asset", "_liability", "_equity",
    "_mv",      # market value: total_mv, circ_mv
)

# Prefixes that imply 万元 IF the field is also clearly a monetary one
_AMOUNT_PREFIXES_NEEDING_CONFIRMATION = ("total_",)

# Explicit allow-list for total_* fields that ARE amounts
_AMOUNT_TOTAL_WHITELIST = {
    "total_revenue", "total_profit", "total_cogs", "total_assets",
    "total_liab", "total_hldr_eqy", "total_hldr_eqy_exc_min_int",
    "total_share",  # ⚠️ NO! total_share is shares, not amount → exclude
    "total_mv",     # market value, IS amount
    "total_cur_assets", "total_nca", "total_cur_liab", "total_ncl",
}
# Remove non-amount fields explicitly
_AMOUNT_TOTAL_BLACKLIST = {
    "total_share", "total_holders", "holder_total",
}


def _needs_financial_normalization(field_name: str) -> bool:
    lower = field_name.lower()

    if lower in _AMOUNT_TOTAL_BLACKLIST:
        return False
    if any(lower.endswith(suf) for suf in _FINANCIAL_AMOUNT_SUFFIXES):
        return True
    # total_xxx — only if explicitly whitelisted
    if lower.startswith("total_") and lower in _AMOUNT_TOTAL_WHITELIST:
        return True
    return False
```

**注意**：`_FUND_SHARE_SUFFIXES = ("_share", "_amount")` 中 `_amount` 与上述列表重合，导致 `total_amount` 之类既走金额又走份额——分别处理。Qwen 实施时也要修一下 `_needs_fund_share_normalization`，限制为基金语境（看接口名是否为 `fund_*`）。

**测试方案**：
- 单元测试 `tests/unit/test_type_map.py`（**新建**），覆盖：
  - `total_revenue` → `True`（应归一）
  - `total_share` → `False`（不应归一）
  - `total_holders` → `False`
  - `n_income_attr_p` → `True`（结尾 `_p` 但属于 `n_income_*` 利润系列，需特判）

---

### B6. Dashboard 缺 Nginx 服务 → 前端跑不起来

**位置**：`docker-compose.yml`

**现状**：仅 `clickhouse / pipeline / grafana` 三个服务，前端 SPA 静态文件无人服务。

**修复**：

新建 `dashboard/nginx.conf`：
```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # 前端静态文件
    location / {
        try_files $uri $uri/ /index.html;
    }

    # ClickHouse HTTP 反代（避免跨域）
    location /api/ch/ {
        proxy_pass http://clickhouse:8123/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # CORS（如果反代后浏览器仍需要）
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' '*' always;
    }
}
```

新建 `dashboard/Dockerfile`：
```dockerfile
FROM nginx:1.27-alpine
COPY index.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

`docker-compose.yml` 增加服务：
```yaml
  dashboard:
    build: ./dashboard
    restart: unless-stopped
    ports: ["3001:80"]   # 与 grafana(3000) 错开
    depends_on:
      clickhouse: {condition: service_healthy}
```

`dashboard/index.html` 中的连接配置改为相对路径 `/api/ch/`，并把 `ai_reader` 密码通过 nginx 子请求或前端 localStorage 注入（避免硬编码）。

**测试方案**：
- `docker compose up -d dashboard`
- 浏览器打开 `http://localhost:3001`，看是否加载 SPA
- 在 SPA 内点 "Test Connection"，应通过 `/api/ch/?query=SELECT%201` 收到 `1`

---

## 2. P1 高优先级（功能受损但能跑）

### B7. Pipeline 容器进程托管脆弱

**位置**：`docker-compose.yml:38`

**现状**：
```yaml
command: ["sh", "-c", "tushare-db scheduler-run & tushare-db mcp-serve --transport sse --host 0.0.0.0 --port 7800 && wait"]
```

**问题**：
- 后台 `&` + 前台 `&&` 顺序难以保证
- 若 `scheduler-run` 后台进程崩溃，容器仍 "up"（mcp-serve 在前台维持 PID 1）
- `&& wait` 仅在前台 `mcp-serve` 退出码 0 才执行；非 0 退出 wait 不会触发

**修复方案 A（推荐：拆两个服务）**：
```yaml
  pipeline-scheduler:
    build: ./docker/pipeline
    restart: unless-stopped
    depends_on:
      clickhouse: {condition: service_healthy}
    volumes: [...]  # 同 pipeline
    environment: [...]
    command: ["tushare-db", "scheduler-run"]

  pipeline-mcp:
    build: ./docker/pipeline
    restart: unless-stopped
    ports: ["7800:7800"]
    depends_on:
      clickhouse: {condition: service_healthy}
    volumes: [...]
    environment: [...]
    command: ["tushare-db", "mcp-serve", "--transport", "sse", "--host", "0.0.0.0", "--port", "7800"]
```

**修复方案 B（用 supervisor）**：在 pipeline image 内装 supervisord，写 `supervisord.conf` 监控两个进程。

**推荐 A**（更 cloud-native，重启策略独立）。

---

### B8. Scheduler 在 trade_cal 空时静默跳过

**位置**：`src/tushare_db/scheduler/jobs.py:64`

**现状**：
```python
if batch not in ("reference", "saturday") and not is_trading:
    return  # 跳过非交易日
```

**问题**：
- `_is_trading_day` 查 `_meta.trade_cal`
- 如果用户 `docker compose up` 启动，但**没跑 `bootstrap`**，`trade_cal` 是空表
- 所有 daily/financial 批次会被认为"非交易日"而跳过，且无任何告警
- 用户会以为 scheduler 在跑，实际什么都没做

**修复**：

```python
# scheduler/jobs.py

def _is_trading_day(ch_client, today: date) -> bool:
    """Returns True if today is a trading day per _meta.trade_cal."""
    result = ch_client.query(
        "SELECT count() FROM _meta.trade_cal WHERE exchange = 'SSE'"
    )
    total_rows = int(result.result_rows[0][0])
    if total_rows == 0:
        # Cold-start: trade_cal not seeded yet
        logger.error(
            "trade_cal is empty — run `tushare-db bootstrap` first. "
            "All batches will be skipped until trade_cal is populated.",
            today=today.isoformat(),
        )
        # 抛异常让 APScheduler 标记 job 失败，而不是静默跳过
        raise RuntimeError("trade_cal not seeded; bootstrap required")

    result = ch_client.query(
        f"SELECT is_open FROM _meta.trade_cal "
        f"WHERE exchange = 'SSE' AND cal_date = '{today.isoformat()}'"
    )
    if not result.result_rows:
        return False
    return bool(result.result_rows[0][0])
```

**额外建议**：在 `scheduler/service.py` 启动时增加预检：

```python
def start_scheduler():
    ch_client = _get_ch_client()
    try:
        # Pre-flight: ensure _meta.trade_cal has data
        cnt = ch_client.query("SELECT count() FROM _meta.trade_cal").result_rows[0][0]
        if int(cnt) == 0:
            logger.error("trade_cal empty. Run `tushare-db bootstrap` before scheduler-run.")
            sys.exit(2)
    finally:
        ch_client.close()
    # ... 继续正常启动
```

---

### B9. MCP 未实现 LZ4 + Arrow IPC 压缩

**位置**：`src/tushare_db/mcp_server/tools.py:39-52`

**现状**：所有结果通过 `_rows_to_dicts` 转 list[dict]，返回纯 JSON。

**设计 §10 要求**：
- 行数 > 1000 启用 Arrow IPC + LZ4 压缩
- 行数 > 100K 启用 SSE 分片（每片 ~10K 行）

**修复**（按 futureplan/a-mcp-tool-contracts.md §0.5 实现）：

```python
# src/tushare_db/mcp_server/encoding.py  (新建)

import base64
import io

import lz4.frame as lz4
import pyarrow as pa
import pyarrow.ipc as ipc


def encode_response(rows: list[dict], threshold: int = 1000) -> tuple[str, str]:
    """Encode rows. Returns (encoded_text, encoding_label).

    encoding_label ∈ {"json", "arrow_ipc_lz4"}.
    """
    if len(rows) < threshold:
        import json
        return json.dumps(rows, ensure_ascii=False), "json"

    table = pa.Table.from_pylist(rows)
    sink = io.BytesIO()
    with ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    raw = sink.getvalue()
    compressed = lz4.compress(raw, compression_level=3)
    return base64.b64encode(compressed).decode("ascii"), "arrow_ipc_lz4"
```

`mcp_server/tools.py` 在每个工具 return 前用 `encode_response` 包装；并在 MCP `_meta.encoding` 字段标注。

依赖：`pyarrow>=16` (已在 pyproject) + `lz4` (需加到 pyproject)：

```toml
dependencies = [
  ...
  "lz4>=4.3",
]
```

---

### B10. backfill 应独立成模块

**位置**：当前在 `src/tushare_db/cli.py:417-500`

**修复**：新建 `src/tushare_db/runner/backfill.py`，把 `backfill` 函数体和 `_get_layer` 都搬过去：

```python
# src/tushare_db/runner/backfill.py

from __future__ import annotations

import uuid
from typing import Iterable

import clickhouse_connect.driver

from tushare_db.config.loader import load_interface_specs
from tushare_db.config.models import InterfaceSpec
from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch


def get_layer(spec: InterfaceSpec) -> int:
    """Map an InterfaceSpec to its backfill layer (0-5)."""
    if spec.batch == "reference":
        return 0
    if spec.priority == "P0" and spec.fetch_strategy.kind in ("date_loop", "offset_paging"):
        return 1
    if spec.priority == "P1" and spec.fetch_strategy.kind not in ("period_loop", "per_symbol_period"):
        return 2
    if spec.fetch_strategy.kind in ("period_loop", "per_symbol_period"):
        return 3
    if spec.priority == "P2":
        return 4
    return 5


def select_specs(
    layer: int | None = None,
    priority: str | None = None,
    interface: str | None = None,
    backfill_all: bool = False,
) -> list[InterfaceSpec]:
    specs = load_interface_specs()
    if interface:
        return [s for s in specs if s.name == interface]
    if layer is not None:
        return [s for s in specs if s.enabled and get_layer(s) == layer]
    if priority:
        return [s for s in specs if s.enabled and s.priority == priority]
    if backfill_all:
        return [s for s in specs if s.enabled]
    return [s for s in specs if s.enabled and s.priority in ("P0", "P1")]


def run_backfill(
    specs: Iterable[InterfaceSpec],
    tushare_client: TushareClient,
    ch_client: clickhouse_connect.driver.Client,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Execute backfill for given specs. Returns summary dict."""
    run_id = uuid.uuid4()
    total_units = total_done = total_failed = 0

    for spec in specs:
        units = plan_units(spec, ch_client, start_date=start_date, end_date=end_date)
        if not units:
            continue
        total_units += len(units)
        _, done, failed = execute_batch(units, tushare_client, ch_client, run_id=run_id)
        total_done += done
        total_failed += failed

    return {
        "run_id": str(run_id),
        "total": total_units,
        "done": total_done,
        "failed": total_failed,
    }
```

`cli.py` 的 `backfill` 命令缩短为：
```python
@cli.command()
def backfill(layer, priority, interface, from_date, to_date, backfill_all):
    from tushare_db.runner.backfill import select_specs, run_backfill

    specs = select_specs(layer=layer, priority=priority, interface=interface, backfill_all=backfill_all)
    if not specs:
        click.echo("No matching interfaces found.")
        return

    ch_client = _get_ch_native()
    tushare_client = _get_tushare_client()
    try:
        summary = run_backfill(specs, tushare_client, ch_client, from_date, to_date)
        click.echo(f"Backfill complete: {summary['done']}/{summary['total']} done, {summary['failed']} failed")
    finally:
        tushare_client.close()
        ch_client.close()
```

测试也搬到 `tests/unit/test_backfill.py`，用 mock spec 验证 `get_layer` 返回值。

---

### B11. Bootstrap 缺 29 张表

**位置**：`data/logs/progress.md` 列出的失败接口

**修复策略**：

1. **审计每张失败接口**，分类：
   - **API 参数缺失**：补 `cli.py:_sample_one_interface` 的策略分支
   - **接口已下线**：在 YAML 里置 `enabled: false`，加注释说明
   - **样本数据为空**：尝试用历史日期采样（如 `period=20231231` 而非 `20240331`）

2. **逐个跑** `tushare-db bootstrap --only <interface_name>` 验证

3. **进度记到** `data/logs/progress.md`，每修一个划掉一个

下面是基于 progress.md 列出的接口的处理建议：

| 接口 | 状态 | 建议 |
|------|------|------|
| `film_record` | 接口未找到 | YAML `enabled: false` |
| `tmt_twincome` | 接口未找到 | YAML `enabled: false` |
| `tmt_twincomedetail` | 接口未找到 | YAML `enabled: false` |
| `cb_price_chg` | 需 ts_code | 已修 |
| `cyq_chips` | 需 ts_code | 已修 |
| `broker_recommend` | 需 month | 已修 |
| `weekly`/`monthly` | 需 ts_code | 已修 |
| `stk_ah_comparison` | 需空参 | 已修 |
| 财务表 | 需 ts_code+period | 已修 |

剩下未列出的 ~17 个，需要 Qwen **逐个手动跑** `tushare-db sample-apis --only <name>` 看错误，按上述模式调整。

---

### B12. Tenacity 重试遮蔽服务端错误

**位置**：`src/tushare_db/core/tushare_client.py`

**现状**（推断，需 Qwen 实际打开看代码）：
```python
@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((TushareRateLimitError, TushareError)),  # ⚠️ 太宽泛
)
def call(...):
    ...
```

**问题**：
- `TushareError` 是基类，覆盖 500/502/503/网络错误等
- 真实业务错误（参数错、字段错）也会被 retry 4 次，浪费配额
- 最终失败时只看到最后一次错误，前 3 次被吞了

**修复**：

```python
# core/errors.py
class TushareRateLimitError(TushareError): ...
class TushareAuthError(TushareError): ...
class TushareTransientError(TushareError):    # 5xx, 网络
    """Transient — safe to retry."""
class TushareBizError(TushareError):          # 4xx 非鉴权
    """Business error — do NOT retry."""

# core/tushare_client.py
@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((TushareRateLimitError, TushareTransientError)),  # ✅ 仅瞬态
)
def call(...):
    if status_code == 429:
        raise TushareRateLimitError(...)
    if status_code in (401, 403):
        raise TushareAuthError(...)
    if 500 <= status_code < 600:
        raise TushareTransientError(...)
    if 400 <= status_code < 500:
        raise TushareBizError(...)
    ...
```

---

### B13-B15. 测试 / 覆盖率（一并处理）

**B13 集成测试空白**

新建 `tests/integration/test_clickhouse_sink.py`（用 `testcontainers`）：

```python
import pytest
from testcontainers.clickhouse import ClickHouseContainer

@pytest.fixture(scope="module")
def ch_container():
    with ClickHouseContainer("clickhouse/clickhouse-server:24.8") as ch:
        yield ch

@pytest.fixture
def ch_client(ch_container):
    import clickhouse_connect
    return clickhouse_connect.get_client(
        host=ch_container.get_container_host_ip(),
        port=ch_container.get_exposed_port(8123),
        username="default",
        password="",
        database="default",
    )

def test_insert_rows(ch_client):
    from tushare_db.sink.clickhouse_sink import insert_rows
    ch_client.command("CREATE TABLE test (a Int32, b String) ENGINE=Memory")
    insert_rows(ch_client, "test", ["a", "b"], [[1, "x"], [2, "y"]], database="default")
    result = ch_client.query("SELECT count() FROM test").result_rows
    assert result[0][0] == 2

def test_normalize_value_decimal64_amount(ch_client):
    """Verify B1 fix: Decimal64(2) financial fields get ×10000."""
    from tushare_db.runner.worker import _normalize_items, _get_column_types

    ch_client.command(
        "CREATE TABLE inc (ts_code String, total_revenue Decimal64(2)) ENGINE=Memory"
    )
    types = _get_column_types(ch_client, "inc", database="default")
    assert types["total_revenue"].startswith("Decimal64")

    rows = _normalize_items(["ts_code", "total_revenue"], [["000001.SZ", 100.5]],
                            column_types=types)
    assert rows[0][1] == 1005000.0  # 万元 -> 元
```

**B14 心跳测试 trivial**

`tests/unit/test_sync_state_heartbeat.py` 改为真起 testcontainers ClickHouse，跑一个 ~70s 的 worker，断言 `heartbeat_at` 在 30s±5s 间隔被更新。

**B15 覆盖率** 实施 B13/B14 后会自动拉到 50%+，CLI 部分用集成测试 `subprocess.run(["tushare-db", "init"])` 提到 70%+。剩下 80% 的最后冲刺要靠 MCP/verify 的 mocked 集成测试。

---

### B16. 错误码分类粒度

并入 B12 一起做。把 503 / 504 / `httpx.ConnectError` / `httpx.ReadTimeout` 都映射到 `TushareTransientError`。

---

## 3. P2 设计偏差（锦上添花）

### B17. checksum 用稳定 fingerprint

**位置**：`verify/checksums.py:62`

**现状**：`sum(cityHash64(*))` 对行序敏感，FINAL 后 part merge 顺序变化会让指纹变。

**修复**：
```sql
SELECT
    count() AS cnt,
    groupBitXor(cityHash64(*)) AS row_xor_fp,
    max(_version) AS max_ver
FROM <table> FINAL
WHERE trade_date = ?
```

`groupBitXor` 是行序无关的（XOR 满足交换律 + 结合律），跨 part merge 后稳定。

---

### B18. probe 未回写 YAML

**位置**：`cli.py:probe()`

**修复**：探测后用 `pyyaml` 把 `enabled: true/false` 写回对应 `config/interfaces/*.yaml`。注意保留注释（用 `ruamel.yaml` 而非 `pyyaml`）：

```python
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True

with open(yaml_path) as f:
    docs = list(yaml.load_all(f))
for doc in docs:
    if doc and doc.get("name") == spec_name:
        doc["enabled"] = newly_enabled
with open(yaml_path, "w") as f:
    yaml.dump_all(docs, f)
```

加 `ruamel.yaml>=0.18` 到 pyproject。

---

### B19. Schema evolver 影子表迁移

**位置**：`schema/evolver.py`

**当前**：仅 ADD COLUMN。

**目标**：增加 `rename_column` 和 `change_type`，用影子表方式：

```python
def rename_column(client, table, old, new):
    """Rename via shadow table (CREATE → INSERT SELECT → RENAME → DROP)."""
    client.command(f"CREATE TABLE {table}_new AS {table}")
    client.command(f"ALTER TABLE {table}_new RENAME COLUMN {old} TO {new}")
    client.command(f"INSERT INTO {table}_new SELECT * FROM {table}")
    client.command(f"RENAME TABLE {table} TO {table}_old, {table}_new TO {table}")
    client.command(f"DROP TABLE {table}_old")
```

ClickHouse 24.8 已支持 `ALTER TABLE ... RENAME COLUMN`，可省去影子表，但 `change_type` 仍需。

---

### B20. Grafana ClickHouse 插件未声明

**位置**：`docker-compose.yml` grafana 服务

**修复**：
```yaml
  grafana:
    image: grafana/grafana:11.0.0
    environment:
      GF_INSTALL_PLUGINS: grafana-clickhouse-datasource
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: "Viewer"
    ...
```

并在 `docker/grafana/provisioning/datasources/clickhouse.yaml` 声明数据源：
```yaml
apiVersion: 1
datasources:
  - name: ClickHouse
    type: grafana-clickhouse-datasource
    access: proxy
    url: http://clickhouse:8123
    jsonData:
      defaultDatabase: tushare
      port: 8123
      protocol: http
      username: grafana
    secureJsonData:
      password: ${CH_GRAFANA_PASSWORD}
    isDefault: true
```

---

### B21. Gap 检测覆盖度

**位置**：`verify/gap_detector.py`

**修复**：
- 增加财务表 gap：对比 `_meta.trade_cal` 取季度末日期 ↔ `tushare_fina_indicator.end_date`
- 增加 hk_hold 周末 gap：港股交易日 ≠ A 股交易日

---

### B22. 样本数 161 vs 表数 153 对账

**修复**：
```bash
# 找出有样本但没表的接口（潜在脏数据）
ls data/samples/*.json | xargs -n1 basename | sed 's/.json//' > /tmp/samples.txt
docker compose exec clickhouse clickhouse-client --query \
  "SELECT name FROM system.tables WHERE database='tushare'" > /tmp/tables.txt
diff /tmp/samples.txt /tmp/tables.txt
```

差集结果二选一：
- 接口已废 → 删 `data/samples/<name>.json`
- 表创建失败 → 重跑 `tushare-db rebuild-schema --interface <name>`

---

### B23. Dashboard 自动注入连接串

**位置**：`dashboard/index.html`

**修复**：
```html
<script>
  // 优先用 URL 参数，其次 localStorage，最后默认
  const params = new URLSearchParams(location.search);
  const config = {
    host: params.get("ch_host") || localStorage.getItem("ch_host") || "/api/ch",
    user: params.get("ch_user") || "ai_reader",
    password: params.get("ch_password") || localStorage.getItem("ch_password") || "",
  };
  // 如果 URL 带了 ch_password，存到 localStorage 后清掉 URL 参数（防 referer 泄漏）
  if (params.get("ch_password")) {
    localStorage.setItem("ch_password", params.get("ch_password"));
    history.replaceState(null, "", location.pathname);
  }
</script>
```

---

## 4. 给 Qwen 3.6 Plus 的执行建议

### 4.1 上下文管理

- **每次会话开始先读** `a-implementation-handoff-guide.md` § 12（每日 5 步开机检查）
- **TodoWrite 强制使用**：把本文档 23 个 ID 全部加入，按顺序勾选
- **Bash 超时**：所有 `pytest` / `docker compose` 命令加 `--timeout 600` 或 `timeout: 600000` 入参
- **windows 路径**：用正斜杠 `F:/AIcoding_space/VsCode/tushare_db/`，避免反斜杠转义错乱
- **PowerShell UTF-8**：`chcp 65001` 后再跑 `tushare-db`，防中文字段名乱码

### 4.2 修复执行顺序（强约束）

```
Day 1（必须当天完成）
  B1 → 单元测试 → 集成测试 → 验证 1 张财务表数据 ×10000 正确
  B5 → 单元测试 → 跑 sample → 对比修复前后 column types

Day 2
  B3 → docker 重启 MCP → curl 验证
  B4 → 写单元测试（mock ClickHouse）+ 集成测试（真起 ch）
  B2 → 跑 daily 一个月 backfill 计时

Day 3
  B6 → 加 nginx 服务 → 浏览器跑通
  B7 → 拆分 pipeline 服务 → docker compose 重启
  B8 → 加 trade_cal 预检 → 模拟空 trade_cal 启动应该 fail-fast

Day 4
  B10 → backfill 模块化重构 → 跑 e2e 测试不应有回归
  B12 + B16 → 错误码分类 → 跑现有 tushare_client 测试
  B13/B14/B15 → 集成测试 + 覆盖率冲到 60%

Day 5
  B11 → 逐个修补 29 个失败接口
  B9 → MCP 压缩
  B17-B23 → 一次性扫尾
```

### 4.3 Agent 编排

| 任务 | 推荐 Agent | 用法 |
|------|------------|------|
| B1, B5（数据正确性 bug） | tdd-guide | 先写失败测试，再改代码 |
| B2（并发改造） | architect → tdd-guide | 先确认 thread-local 方案，再实现 |
| B3, B4（MCP 修复） | python-reviewer | 改完跑代码审查 |
| B6, B7（部署） | （手工） | docker 实际起停 |
| B12（错误码） | code-reviewer | 检查异常类层次合理性 |
| B13-B15（测试） | tdd-guide | 严格 RED-GREEN-REFACTOR |
| B19（schema 演进） | architect | 影子表方案设计 |

**禁止嵌套 agent**：每次最多 1 层 subagent，否则 context 爆炸。

### 4.4 验证策略

每修一个 bug，必须执行：

1. **单元测试**：`pytest tests/unit/test_<module>.py -v`
2. **集成测试**（如适用）：`pytest tests/integration/ -v --tb=short`
3. **手动验证**：在 docker 容器内跑实际命令
4. **代码审查**：`Skill: python-review` 或 `code-reviewer` agent
5. **更新 progress.md**：记录修复时间 + 测试结果

**禁止"一次修多个再统一测"**——出问题没法定位。

### 4.5 错误恢复

如果某次修复破坏了已通过的测试：

1. `git diff HEAD` 看改动范围
2. `pytest tests/ --lf -v`（last failed）
3. **不要** `git reset --hard`，先 `git stash` 保留改动，找到原因后再 unstash
4. 如果搞不定，开新 worktree 重新克隆：`git worktree add ../tushare_db_recover HEAD~10`

### 4.6 沟通规则

- 修完每个 P0 bug **立即向用户汇报**（不要等所有 P0 都做完）
- 卡壳超过 30 分钟必须 stop 并问用户
- 每天结束更新 `data/logs/progress.md` 与 `data/logs/remaining_work.md`

---

## 5. 验证清单（修完所有 P0 后跑一遍）

```bash
# 1. 数据正确性（B1, B5）
docker compose exec pipeline tushare-db backfill --interface income --from 20231001 --to 20231231
docker compose exec clickhouse clickhouse-client --query \
  "SELECT ts_code, total_revenue FROM tushare.tushare_income FINAL WHERE end_date='20231231' LIMIT 1 FORMAT Vertical"
# 期望：total_revenue 是真实"元"数（如 600519.SH 应在 1.5e11 量级），不是 1.5e7

# 2. 并发吞吐（B2）
time docker compose exec pipeline tushare-db backfill --interface daily --from 20240101 --to 20240131
# 期望：< 5 分钟（单日 5500 行 × 22 个交易日 = 121K 行，HTTP/2 + 12 worker 应轻松完成）

# 3. MCP 工具（B3, B4）
docker compose exec pipeline curl -X POST http://localhost:7800/mcp \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_ohlcv","arguments":{"ts_code":"000001.SZ","start_date":"20240101","end_date":"20240131","adjust":"qfq"}},"id":1}'
# 期望：返回 22 行 OHLCV，open/high/low/close 都是合理数值

# 4. Dashboard（B6, B7）
curl http://localhost:3001  # 应返回 SPA HTML
curl http://localhost:3001/api/ch/?query=SELECT%201  # 应返回 1

# 5. Scheduler 冷启动（B8）
docker compose exec clickhouse clickhouse-client --query "TRUNCATE TABLE _meta.trade_cal"
docker compose restart pipeline-scheduler
docker compose logs pipeline-scheduler | grep "trade_cal empty"
# 期望：日志立即报错，容器重启进入退避

# 6. 测试覆盖率（B13-B15）
docker compose exec pipeline pytest tests/ --cov=src --cov-report=term-missing
# 期望：总覆盖率 ≥ 60%（80% 目标分阶段达成）

# 7. 全链路 e2e
docker compose down -v && docker compose up -d
docker compose exec pipeline tushare-db init
docker compose exec pipeline tushare-db bootstrap
docker compose exec pipeline tushare-db backfill --priority P0 --from 20240101 --to 20240131
docker compose exec pipeline tushare-db verify --priority P0
# 期望：所有步骤通过，verify 报告 0 个 issue
```

---

## 6. 完成定义（DoD）

✅ 所有 P0（B1-B6）修复并通过单元 + 集成测试
✅ 所有 P1（B7-B16）修复或在 `remaining_work.md` 明确豁免（标注理由）
✅ 测试覆盖率 ≥ 60%（核心模块 ≥ 90%）
✅ `docker compose up -d` 后无人工干预，10 分钟内 MCP / Dashboard / Grafana 全部可访问
✅ 跑一次完整 P0 backfill（20240101-20240131），所有 22 个 P0 接口入库且 verify 通过
✅ MCP `get_ohlcv` qfq/hfq 返回的价格在合理区间（±10% 真实值）
✅ Grafana 3 个 dashboard 全部能加载数据
✅ `data/logs/progress.md` 记录所有 23 个 ID 的修复 commit hash + 测试结果

---

## 7. 后续迭代（V2-V5，本次不做）

按设计文档与 `futureplan/` 目录中已写的 6 份补充文档：

- **V2**：手动触发回补 / 验证（API 桥接服务）
- **V3**：实时日志流（WebSocket → 前端 Audit 页面）
- **V4**：数据导出（CSV / Parquet 下载）
- **V5**：用户认证 + 多用户权限
- **V6**：参考 `futureplan/a-schema-evolution.md` 实现自动化 schema 漂移检测

---

> 维护：每修复一项，把表 §0 该行的"待"改成 ✅ 并加上 commit hash。
> 卡壳：在本文档末尾加 `## 阻塞问题` 段落，详细描述 + 召唤用户。

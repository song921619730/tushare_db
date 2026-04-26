# Tushare Hub (PostgreSQL) → Tushare DB (ClickHouse) 迁移执行计划

> 文档版本：v1.0
> 编制日期：2026-04-26
> 编制者：Sonnet 4.6
> 执行者：VSCode + Claude Code + Qwen 3.6 Plus
> 上游需求文档：`F:\AIcoding_space\projects\tushare-hub\docs\migration_to_tushare_db.md` (v1.0, 2026-04-26)
> 上游设计骨架：`F:\AIcoding_space\VsCode\tushare_db\f-aicoding-space-projects-tushare-hub-do-declarative-dragonfly.md`
>
> **核心价值**：tushare-hub 的 PostgreSQL 已存有 ~1570 万行历史数据。直接迁入 ClickHouse 可**跳过 `a-final-mile-plan-for-qwen.md` 阶段一 R1-R5 的全量数据回填**，节省 ~50 小时和数十万次 Tushare API 调用。
>
> **执行原则**：本次任务只新增文件、不改现有代码；PG 全程只读；CH 当前为空表（如非空，迁移前不要清空——靠 _version 去重）。

---

## 0. TL;DR + 执行流程图

### 0.1 一页流程

```
┌──────────────────────────────────────────────────────────────┐
│ Step 0  环境准备：装 psycopg3、配 PG_* env、连通性测试         │
├──────────────────────────────────────────────────────────────┤
│ Step 1  探测：PG 实际表清单（含分区子表）+ CH 现有表清单         │
│         → 生成 missing_tables.md（PG 有但 CH 没有的表）          │
├──────────────────────────────────────────────────────────────┤
│ Step 2  建缺表：用 schema/ddl_builder + inferer 或手写 DDL      │
├──────────────────────────────────────────────────────────────┤
│ Step 3  ⚠️ 停 tushare-hub scheduler（防 PG 仍在写入）            │
├──────────────────────────────────────────────────────────────┤
│ Step 4  Dry-run（不写数据）：                                    │
│         → 生成 field_diff_report.md（每表的字段差异）            │
│         → 生成 amount_conversion_report.md（×10000 列清单）      │
│         → 生成 partition_dup_check.md（跨年重复行）              │
├──────────────────────────────────────────────────────────────┤
│ Step 5  ⚠️ 用户人工 review 三个报告，确认后加 --confirm 标记      │
├──────────────────────────────────────────────────────────────┤
│ Step 6  P0 实跑（8 张核心表）：先跑 stock_basic 71k 行试通路 →   │
│         再跑 stock_daily 730 万行 → 三层校验 → OPTIMIZE FINAL    │
├──────────────────────────────────────────────────────────────┤
│ Step 7  P1（财务 5 表） → P2（资金流） → P3（其余）              │
├──────────────────────────────────────────────────────────────┤
│ Step 8  收尾：                                                   │
│         (1) OPTIMIZE TABLE FINAL（数据表，非 _meta）              │
│         (2) 写 _meta.sync_state 标记每张表 status=done           │
│             ⚠️ 不写则 pipeline 启动后会从头重拉                  │
│         (3) 写 _meta.migration_state 标记 done                  │
│         (4) 重启 tushare-db pipeline-scheduler，验证增量正常      │
├──────────────────────────────────────────────────────────────┤
│ Step 9  收尾文档：                                               │
│         migration_log.md（每表行数、耗时、校验结果）              │
└──────────────────────────────────────────────────────────────┘
```

### 0.2 时间预算

| 阶段 | 耗时 |
|------|------|
| Step 0-2（准备 + 建缺表） | 1-2 小时 |
| Step 3-5（停机 + dry-run + 人工 review） | 1 小时 + 等用户 |
| Step 6 P0 stock_daily 730 万行 | 30-60 分钟 |
| Step 6 P0 其余 7 张（小表） | 10 分钟合计 |
| Step 7 P1+P2+P3 共 ~30 张 | 1-2 小时合计 |
| Step 8-9 收尾 | 30 分钟 |
| **总计** | **4-6 小时**（不含人工 review 等待） |

---

## 1. 前置条件与环境准备

### 1.1 PG 连通性自检（**只读，不改任何东西**）

在 tushare-db 项目目录下：
```bash
# 1. 安装 psycopg3
uv add "psycopg[binary]>=3.1"

# 2. 测试连接（先在 .env 配好 PG_* 变量）
python -c "
import os, psycopg
conn = psycopg.connect(
    host=os.environ['PG_HOST'],
    port=int(os.environ.get('PG_PORT', 5432)),
    user=os.environ['PG_USER'],
    password=os.environ['PG_PASSWORD'],
    dbname=os.environ['PG_DB'],
)
with conn.cursor() as cur:
    cur.execute('SELECT version()')
    print('PG OK:', cur.fetchone()[0])
    cur.execute(\"SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'tushare_%'\")
    print('PG tables:', cur.fetchone()[0])
conn.close()
"
```

**期望输出**：PG 14+ 版本、tables ≥ 47。

### 1.2 CH 连通性自检

```bash
# 用 tushare-db 的 pipeline 用户
docker compose exec clickhouse clickhouse-client \
  --user pipeline --password "$CH_PIPELINE_PASSWORD" \
  --query "SELECT count() FROM system.tables WHERE database='tushare'"
# 期望：≥ 169（已 bootstrap 过的）
```

### 1.3 .env 文件新增项

`F:\AIcoding_space\VsCode\tushare_db\.env` **末尾追加**（不修改现有 CH_* 与 TUSHARE_TOKEN）：
```bash
# PostgreSQL source for migration (READ-ONLY)
# 从 F:\AIcoding_space\projects\tushare-hub\.env 复制 POSTGRES_* 的值过来
PG_HOST=
PG_PORT=5432
PG_USER=
PG_PASSWORD=
PG_DB=
```

⚠️ **不要修改 tushare-hub 的 .env**。tushare-hub 项目自身保留原样。

### 1.4 依赖

`pyproject.toml` 中**仅追加一行**（dependencies 列表内）：
```toml
"psycopg[binary]>=3.1",
```

不需要删除任何现有依赖。psycopg2 与 psycopg3 import 名称不同（`import psycopg2` vs `import psycopg`），可共存。

### 1.5 磁盘评估

```bash
# 评估 CH 数据卷剩余空间
docker compose exec clickhouse df -h /var/lib/clickhouse
# 预估 PG ~30-50 GB → CH 压缩后 ~10-15 GB
# 当前 ClickHouse 数据卷应至少剩余 30 GB
```

### 1.6 ⚠️ 强制约束

- **PG 全程只读**：不允许任何 INSERT/UPDATE/DELETE/DDL on PG
- **CH 当前应为空或仅有少量数据**：迁移会 INSERT 新行，靠 _version 去重；无需提前 TRUNCATE
- **迁移前停 tushare-hub scheduler**：`docker stop <hub_container>` 或 `docker compose -p tushare-hub stop scheduler`
- **迁移期间不要启动 tushare-db pipeline-scheduler**：避免 sync_state 竞争写入

---

## 2. 项目结构与目录骨架

### 2.1 待新增文件树

```
F:\AIcoding_space\VsCode\tushare_db\
├── scripts/
│   └── migrate.py                              ★ 新建：CLI 入口
├── src/tushare_db/migration/                   ★ 新建模块
│   ├── __init__.py
│   ├── registry.py                             ★ tables.yaml loader
│   ├── pg_reader.py                            ★ psycopg server-side cursor
│   ├── type_mapper.py                          ★ PG type → CH type
│   ├── field_resolver.py                       ★ 字段对齐 + 单位转换 + 列重命名
│   ├── version_calc.py                         ★ _version 计算
│   ├── writer.py                               ★ 包装 insert_rows，自管 _version
│   ├── validator.py                            ★ 三层校验
│   ├── state.py                                ★ _meta.migration_state 读写
│   └── sync_state_writer.py                    ★ 收尾写 _meta.sync_state
├── config/migration/                           ★ 新建配置目录
│   └── tables.yaml                             ★ 迁移表清单
├── tests/unit/
│   ├── test_migration_type_mapper.py           ★
│   ├── test_migration_field_resolver.py        ★
│   └── test_migration_version_calc.py          ★
├── tests/integration/
│   └── test_migration_e2e.py                   ★ stock_basic 全量 testcontainers
└── docs/migration/
    ├── EXECUTION_PLAN.md                       ★ 本文档
    ├── missing_tables.md                       ☆ Step 1 生成
    ├── field_diff_report.md                    ☆ Step 4 dry-run 生成
    ├── amount_conversion_report.md             ☆ Step 4 dry-run 生成
    ├── partition_dup_check.md                  ☆ Step 4 dry-run 生成
    └── migration_log.md                        ☆ Step 9 收尾生成
```

★ = 执行 AI 创建；☆ = 执行过程中由脚本自动生成。

### 2.2 关键模块职责一句话

| 模块 | 职责 | 关键函数 |
|------|------|---------|
| `registry.py` | 加载 tables.yaml 并校验 | `load_tables() -> list[TableSpec]` |
| `pg_reader.py` | 流式读 PG，处理分区表合并 | `iter_pg_rows(conn, spec, columns) -> Iterator[list[tuple]]` |
| `type_mapper.py` | PG 类型 → CH 类型映射 | `pg_type_to_ch(pg_type: str, col_name: str) -> str` |
| `field_resolver.py` | 字段对齐 + 列重命名 + 单位归一化 | `resolve_columns(...)`、`normalize_value(col, val, table)` |
| `version_calc.py` | 从 PG row 算 _version (ms timestamp) | `calc_version(row: dict) -> int` |
| `writer.py` | 批量写 CH，自管 _version，重试 | `write_batch(ch_client, table, columns, rows, versions)` |
| `validator.py` | 行数/抽样/聚合三层校验 | `validate_row_count()`、`validate_sample()`、`validate_aggregates()` |
| `state.py` | _meta.migration_state CRUD | `mark_running()`、`mark_done()`、`mark_failed()`、`get_status()` |
| `sync_state_writer.py` | 收尾写 _meta.sync_state 防重拉 | `write_sync_state_done(ch_client, spec)` |

---

## 3. 配置驱动设计：tables.yaml 格式

### 3.1 完整 Schema

```yaml
# config/migration/tables.yaml
# 每条目代表一张需迁移的 PG 表 → CH 表
- pg_table: tushare_stock_daily              # PG 中的逻辑表名（无年份后缀）
  ch_table: tushare_stock_daily              # CH 中的目标表名
  ch_database: tushare                       # CH 数据库名
  priority: P0                               # P0 / P1 / P2 / P3
  partitioned: true                          # PG 是否按年份分区
  partition_pattern: "tushare_stock_daily_{year}"  # 子表命名模板
  partition_years: [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
  include_default_partition: true            # 是否合并 _default 分区
  date_column: trade_date                    # 用于 PARTITION BY、对账
  batch_size: 100000                         # 单批读 PG / 写 CH 行数
  expected_rows: 7327237                     # 来自需求文档，sanity check
  column_renames:                            # 可选：PG 列名 → CH 列名
    end_date: cal_date
    index_code: ts_code
  drop_pg_columns: []                        # 显式丢弃的 PG 列（除 created_at/updated_at）
  notes: "多年份分区，跨年数据可能重复，靠 _version 去重"
```

### 3.2 Pydantic Loader

```python
# src/tushare_db/migration/registry.py
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, ConfigDict


class TableSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pg_table: str
    ch_table: str
    ch_database: str = "tushare"
    priority: Literal["P0", "P1", "P2", "P3"]
    partitioned: bool = False
    partition_pattern: str | None = None
    partition_years: list[int] = Field(default_factory=list)
    include_default_partition: bool = False
    date_column: str | None = None
    batch_size: int = 100_000
    expected_rows: int | None = None
    column_renames: dict[str, str] = Field(default_factory=dict)
    drop_pg_columns: list[str] = Field(default_factory=list)
    notes: str = ""


def load_tables(path: Path | str = "config/migration/tables.yaml") -> list[TableSpec]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [TableSpec(**item) for item in raw]


def filter_by_priority(specs: list[TableSpec], priority: str) -> list[TableSpec]:
    return [s for s in specs if s.priority == priority]
```

---

## 4. 迁移表清单（YAML 完整内容）

> 以下清单基于 tushare-hub `src/models/__init__.py` 注册的 47 张表 + 对账后发现的 CH 已有 enabled 表。
> **执行 AI 第一步必须**：跑一次 `SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'tushare_%' AND table_name NOT LIKE '%_20%' AND table_name NOT LIKE '%_default'` 拿到 PG 真实表清单，与下表交叉验证，发现不一致**立即停下问用户**。

### 4.1 P0 — 核心日行情（8 张）

```yaml
- pg_table: tushare_stock_basic
  ch_table: tushare_stock_basic
  priority: P0
  partitioned: false
  batch_size: 100000
  expected_rows: 5500
  notes: "全市场股票列表，最小表，先跑试通路"

- pg_table: tushare_trade_cal
  ch_table: tushare_trade_cal              # 目标在 _meta.trade_cal 还是 tushare.tushare_trade_cal? 见 §4.4
  ch_database: _meta                        # ⚠️ 注意：tushare-db 的 trade_cal 在 _meta 库
  priority: P0
  partitioned: false
  batch_size: 100000
  expected_rows: 13000

- pg_table: tushare_stock_daily
  ch_table: tushare_stock_daily
  priority: P0
  partitioned: true
  partition_pattern: "tushare_stock_daily_{year}"
  partition_years: [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
  include_default_partition: true
  date_column: trade_date
  batch_size: 100000
  expected_rows: 7327237
  notes: "最大表，先跑这张验证内存与时长基线"

- pg_table: tushare_stock_weekly
  ch_table: tushare_stock_weekly
  priority: P0
  partitioned: true
  partition_pattern: "tushare_stock_weekly_{year}"
  partition_years: [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
  include_default_partition: true
  date_column: trade_date
  batch_size: 100000

- pg_table: tushare_adj_factor
  ch_table: tushare_adj_factor
  priority: P0
  partitioned: true
  partition_pattern: "tushare_adj_factor_{year}"
  partition_years: [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
  include_default_partition: true
  date_column: trade_date
  batch_size: 100000

- pg_table: tushare_daily_basic
  ch_table: tushare_daily_basic
  priority: P0
  partitioned: false                        # 假设非分区，第一步探测确认
  date_column: trade_date
  batch_size: 100000

- pg_table: tushare_stk_limit
  ch_table: tushare_stk_limit
  priority: P0
  date_column: trade_date
  batch_size: 100000

- pg_table: tushare_suspend_d
  ch_table: tushare_suspend_d
  priority: P0
  date_column: trade_date
  batch_size: 100000
```

### 4.2 P1 — 财务（5 张）

```yaml
- pg_table: tushare_income
  ch_table: tushare_income
  priority: P1
  date_column: end_date
  batch_size: 100000

- pg_table: tushare_balancesheet
  ch_table: tushare_balancesheet
  priority: P1
  date_column: end_date
  batch_size: 100000

- pg_table: tushare_cashflow
  ch_table: tushare_cashflow
  priority: P1
  date_column: end_date
  batch_size: 100000

- pg_table: tushare_fina_indicator
  ch_table: tushare_fina_indicator
  priority: P1
  date_column: end_date
  batch_size: 100000

- pg_table: tushare_dividend
  ch_table: tushare_dividend
  priority: P1
  date_column: end_date
  batch_size: 100000
```

### 4.3 P2 — 资金流 + 龙虎榜（约 8 张）

```yaml
- pg_table: tushare_moneyflow
  ch_table: tushare_moneyflow
  priority: P2
  date_column: trade_date
  batch_size: 100000

- pg_table: tushare_moneyflow_hsgt
  ch_table: tushare_moneyflow_hsgt
  priority: P2
  date_column: trade_date
  batch_size: 100000

- pg_table: tushare_top_list
  ch_table: tushare_top_list
  priority: P2
  date_column: trade_date
  batch_size: 100000

- pg_table: tushare_margin
  ch_table: tushare_margin
  priority: P2
  date_column: trade_date

- pg_table: tushare_block_trade
  ch_table: tushare_block_trade
  priority: P2
  date_column: trade_date

- pg_table: tushare_share_float
  ch_table: tushare_share_float
  priority: P2
  date_column: float_date

- pg_table: tushare_stk_holdernumber
  ch_table: tushare_stk_holdernumber
  priority: P2
  date_column: ann_date

- pg_table: tushare_pledge_stat
  ch_table: tushare_pledge_stat
  priority: P2
  date_column: end_date
```

### 4.4 P3 — 其余表（约 26 张）

> 由执行 AI 在第一步探测后补全。模板：
```yaml
- pg_table: <name>
  ch_table: <name>
  priority: P3
  date_column: <date_col_or_null>
  batch_size: 50000          # 小表用更小 batch
```

### 4.5 列重命名清单（dragonfly §6 已识别）

| 涉及表 | PG 列 | CH 列 | 处理 |
|--------|-------|-------|------|
| tushare_fund_nav | end_date | cal_date | 写入 column_renames |
| tushare_index_weight | index_code | ts_code | 写入 column_renames |
| tushare_index_weight | con_code | (无对应) | 写入 drop_pg_columns |
| tushare_cb_call | call_date | trade_date | 写入 column_renames |

### 4.6 trade_cal 特殊性

⚠️ **tushare-db 的 `trade_cal` 在 `_meta.trade_cal`**（见 cli.py:159 的 `CREATE TABLE IF NOT EXISTS _meta.trade_cal`），而非 `tushare.tushare_trade_cal`。迁移时 `ch_database: _meta` + `ch_table: trade_cal`。同时确认 PG 中 trade_cal 的列名是 `cal_date` 还是 `trade_date`，不同则加 column_renames。

---

## 5. PG 读取实现规范

### 5.1 Server-Side Cursor

```python
# src/tushare_db/migration/pg_reader.py
from contextlib import contextmanager
from typing import Iterator
import psycopg


@contextmanager
def pg_connection():
    """Yield a read-only PG connection from env."""
    import os
    with psycopg.connect(
        host=os.environ["PG_HOST"],
        port=int(os.environ.get("PG_PORT", 5432)),
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        dbname=os.environ["PG_DB"],
        autocommit=False,         # 只读不需要 autocommit
    ) as conn:
        # 强制只读
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
        yield conn


def iter_pg_rows(
    conn,
    table: str,
    columns: list[str],
    batch_size: int = 100_000,
    where: str | None = None,
    order_by: str | None = None,
) -> Iterator[list[tuple]]:
    """
    Stream rows in batches via server-side cursor.

    Yields: list of tuples, each tuple in `columns` order.
    """
    cols_sql = ", ".join(f'"{c}"' for c in columns)
    sql = f"SELECT {cols_sql} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"

    # 命名 cursor = server-side
    with conn.cursor(name=f"migrate_{table}") as cur:
        cur.itersize = batch_size
        cur.execute(sql)

        batch = []
        for row in cur:
            batch.append(row)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
```

### 5.2 分区表处理

```python
def iter_partitioned_table(
    conn,
    spec,                    # TableSpec
    columns: list[str],
) -> Iterator[tuple[str, list[tuple]]]:
    """
    For partitioned PG tables, yield (partition_name, batch) pairs.
    Iterates partitions in chronological order: _2020, _2021, ..., _default last.
    """
    partition_tables = []
    for year in spec.partition_years:
        partition_tables.append(spec.partition_pattern.format(year=year))
    if spec.include_default_partition:
        partition_tables.append(f"{spec.pg_table}_default")

    for partition in partition_tables:
        # 探测分区是否存在 + 行数
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_name = %s LIMIT 1", (partition,)
            )
            if not cur.fetchone():
                continue
            cur.execute(f"SELECT count(*) FROM {partition}")
            row_count = cur.fetchone()[0]
            if row_count == 0:
                continue

        # 流式读
        for batch in iter_pg_rows(
            conn, partition, columns, batch_size=spec.batch_size,
            order_by=f"ts_code, {spec.date_column}" if spec.date_column else "ts_code",
        ):
            yield partition, batch
```

### 5.3 分区重复行预检（**必须做**）

```python
def check_partition_duplicates(conn, spec) -> dict[str, int]:
    """
    跨分区重复行预检。返回 {partition_name: duplicate_row_count}.
    """
    if not spec.partitioned or not spec.include_default_partition:
        return {}

    primary_key = "ts_code, " + (spec.date_column or "trade_date")
    results = {}

    for year in spec.partition_years[-2:]:  # 仅检查最近 2 年（最可能跨分区）
        partition_a = spec.partition_pattern.format(year=year)
        partition_b = f"{spec.pg_table}_default"

        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT count(*) FROM (
                    SELECT {primary_key} FROM {partition_a}
                    INTERSECT
                    SELECT {primary_key} FROM {partition_b}
                ) t
            """)
            dup = cur.fetchone()[0]
            if dup > 0:
                results[f"{partition_a} ∩ {partition_b}"] = dup

    return results
```

**报告输出**：写到 `docs/migration/partition_dup_check.md`，**有重复必须告警，让用户决定是否继续**。

### 5.4 空表与 NULL

- 空表：`SELECT 1 FROM t LIMIT 1` 先探测，0 行则 skip 并写 `_meta.migration_state.status='done'`、`rows_migrated=0`
- NULL 透传：psycopg3 默认返回 None，CH 可空列直接写

---

## 6. 字段类型映射与列对齐

### 6.1 完整类型映射表

```python
# src/tushare_db/migration/type_mapper.py
from __future__ import annotations

# 默认低基数列名（命中则用 LowCardinality(String)）
_LOW_CARDINALITY_FIELDS = {
    "ts_code", "exchange", "market", "area", "industry",
    "list_status", "is_hs", "curr_type",
}

# PG 类型 → CH 类型映射
def pg_type_to_ch(pg_type: str, col_name: str) -> str:
    """
    Convert PostgreSQL data type to ClickHouse type string.
    pg_type: lowercase PG type name (e.g. 'character varying', 'numeric').
    """
    pg_type = pg_type.lower().strip()
    col_lower = col_name.lower()

    # String / VARCHAR / TEXT
    if pg_type in ("character varying", "varchar", "text", "char", "character"):
        if col_lower in _LOW_CARDINALITY_FIELDS:
            return "LowCardinality(String)"
        return "String"

    # Integer
    if pg_type in ("smallint", "int2"):
        return "Int16"
    if pg_type in ("integer", "int", "int4"):
        return "Int32"
    if pg_type in ("bigint", "int8"):
        return "Int64"

    # Boolean
    if pg_type in ("boolean", "bool"):
        return "UInt8"

    # Numeric / Decimal — 全部用 Float64 规避溢出
    if pg_type.startswith("numeric") or pg_type.startswith("decimal"):
        return "Float64"
    if pg_type in ("real", "double precision", "float4", "float8"):
        return "Float64"

    # Date / Time
    if pg_type == "date":
        return "Date"
    if pg_type in ("timestamp", "timestamp without time zone", "timestamp with time zone"):
        return "DateTime64(3)"

    # JSON
    if pg_type in ("json", "jsonb"):
        return "String"

    # Default fallback
    return "String"
```

### 6.2 字段对齐 + 列重命名

```python
# src/tushare_db/migration/field_resolver.py
from __future__ import annotations

# 强制丢弃的 PG 列
_FORCE_DROP_COLUMNS = {"created_at", "updated_at"}


def resolve_columns(
    pg_cols: list[str],
    ch_cols: list[str],
    renames: dict[str, str] | None = None,
    drop_pg_cols: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """
    返回 (pg_in, ch_in)，长度相同，位置对齐。

    Steps:
      1. 过滤 PG 强制丢弃列（created_at/updated_at + drop_pg_cols）
      2. PG 列按 renames 映射到 CH 列名
      3. 与 CH 列取交集（CH 缺的列即 PG 有但 CH 不存在 → 跳过）
      4. CH 多的列保持原状（写入时不出现于 columns 参数即可，CH 默认值填入）
    """
    renames = renames or {}
    drop_set = _FORCE_DROP_COLUMNS | set(drop_pg_cols or [])

    pg_clean = [c for c in pg_cols if c not in drop_set]
    ch_set = set(ch_cols)

    pg_in: list[str] = []
    ch_in: list[str] = []
    for pg_col in pg_clean:
        ch_col = renames.get(pg_col, pg_col)
        if ch_col in ch_set:
            pg_in.append(pg_col)
            ch_in.append(ch_col)

    return pg_in, ch_in
```

### 6.3 字段对账报告（dry-run 输出）

```python
def diff_fields(pg_cols: list[str], ch_cols: list[str], renames: dict) -> dict:
    """生成 pg_only / ch_only / both 三组."""
    drop_set = _FORCE_DROP_COLUMNS
    pg_clean = set(c for c in pg_cols if c not in drop_set)
    pg_renamed = {renames.get(c, c) for c in pg_clean}
    ch_set = set(ch_cols)

    return {
        "both": sorted(pg_renamed & ch_set),
        "pg_only_drop": sorted(pg_renamed - ch_set),
        "ch_only_default": sorted(ch_set - pg_renamed),
    }
```

`docs/migration/field_diff_report.md` 模板：
```markdown
# Field Diff Report — 2026-04-26

## tushare_stock_daily

| 类别 | 列名 |
|------|------|
| both (15) | ts_code, trade_date, open, high, low, close, ... |
| pg_only_drop (2) | created_at, updated_at |
| ch_only_default (1) | _version |

## tushare_fund_nav

| 类别 | 列名 |
|------|------|
| renames applied | end_date → cal_date |
| both (12) | ts_code, cal_date, unit_nav, ... |
| pg_only_drop (3) | created_at, updated_at, some_pg_only_col |

...
```

---

## 7. 金额与份额单位转换（⚠️ 致命坑）

### 7.1 背景

**tushare-db 的 `schema/type_map.py`** 已实现 `normalize_value()`：从 Tushare API 读到的"万元/万份"原始值会被 ×10000 转为"元/份"再写入 ClickHouse。但**迁移脚本绕过了这条链路**，必须在 ETL 中独立实现。

### 7.2 完整规则（直接抄到 `field_resolver.py`）

```python
# src/tushare_db/migration/field_resolver.py 续

from decimal import Decimal
from typing import Any


# 万元/万份 → 元/份的归一化字段模式（包含匹配）
_NORMALIZE_X10000_PATTERNS: list[str] = [
    "amount",      # *_amount: 所有成交额
    "revenue",     # total_revenue, oper_revenue
    "profit",      # net_profit, oper_profit, total_profit
    "income",      # net_income, total_income, op_income (但不含"earnings_per_share")
    "cost",        # total_cost, op_cost
    "expense",     # admin_expense, sell_expense, fin_expense
    "asset",       # total_assets, current_assets
    "liability",   # total_liab, current_liab
    "equity",      # total_equity, total_hldr_eqy
    "mv",          # total_mv, circ_mv, float_mv
    "capital",     # reg_capital, paid_capital
    "surplus",     # cap_rese, surplus_rese, undist_profit
    "tax",         # income_tax (但不含"_tax_rate")
    "ebit",
    "ebitda",
    "fcff",
    "fcfe",
    "interest",    # interest expense/income
    "debt",        # net_debt, lt_debt, st_debt
    "dividend",    # dividend amount
]

# 排除规则（即使模式匹配也不转换）
_EXCLUDE_SUFFIXES = (
    "_pct", "_rate", "_ratio", "_price", "_days",
    "_yoy", "_qoq", "_cost_ratio", "_tax_rate",
    "_per_share", "_share_pct",
)
_EXCLUDE_FULL_NAMES = {
    "vol", "amount_vol",   # 成交量/成交额单位是股/手，不是万元
    "turnover_rate",
    "pe", "pe_ttm", "pb", "ps", "ps_ttm",
}


def should_normalize(column_name: str, table_name: str = "") -> bool:
    """是否需要 ×10000."""
    col = column_name.lower()
    if col in _EXCLUDE_FULL_NAMES:
        return False
    if col.endswith(_EXCLUDE_SUFFIXES):
        return False
    # *_vol 全部排除（成交量）
    if col == "vol" or col.endswith("_vol"):
        return False
    # 基金份额特例：仅 fund_* 表的 *_share / *_amount 才是万份
    if "share" in col:
        if not table_name.startswith(("tushare_fund_", "fund_")):
            return False
    for pat in _NORMALIZE_X10000_PATTERNS:
        if pat in col:
            return True
    return False


def normalize_value(column_name: str, value: Any, table_name: str = "") -> Any:
    """对单个值应用 ×10000."""
    if value is None:
        return None
    if not should_normalize(column_name, table_name):
        return value
    if isinstance(value, (int, float)):
        return value * 10_000
    if isinstance(value, Decimal):
        return float(value) * 10_000
    return value


def normalize_row(
    row: tuple, columns: list[str], table_name: str = ""
) -> tuple:
    """对一整行应用 normalize_value，返回新 tuple."""
    return tuple(
        normalize_value(col, val, table_name)
        for col, val in zip(columns, row)
    )
```

### 7.3 dry-run 报告（人工确认必读）

`docs/migration/amount_conversion_report.md` 模板：
```markdown
# Amount Conversion Report — 2026-04-26

## ⚠️ 必须人工确认

下表列出了所有被自动判定为"需要 ×10000"的字段。请逐表 review，
**有疑问的字段必须在加 `--confirm` 实跑前提出**。

## tushare_income (P1 财务)

| 列名 | 是否归一化 | 决策依据 |
|------|----------|---------|
| total_revenue | ✅ ×10000 | matches "revenue" |
| oper_revenue | ✅ ×10000 | matches "revenue" |
| n_income | ✅ ×10000 | matches "income" |
| ebit | ✅ ×10000 | matches "ebit" |
| total_cogs | ✅ ×10000 | matches "cost" (gross? 待确认) |
| basic_eps | ❌ 保留 | excluded: _per_share |
| t_compr_income | ✅ ×10000 | matches "income" |

## tushare_daily_basic

| 列名 | 是否归一化 | 决策依据 |
|------|----------|---------|
| total_mv | ✅ ×10000 | matches "mv" |
| circ_mv | ✅ ×10000 | matches "mv" |
| pe_ttm | ❌ 保留 | excluded: pe_ttm |
| turnover_rate | ❌ 保留 | excluded: turnover_rate |

...
```

### 7.4 校验阶段对账规则

```python
# 聚合校验时：
pg_sum = pg.execute(f"SELECT SUM({col}) FROM {pg_table}")
ch_sum = ch.execute(f"SELECT SUM({col}) FROM {ch_table} FINAL")

if should_normalize(col, table):
    expected = pg_sum * 10_000
    diff_pct = abs(ch_sum - expected) / abs(expected) if expected else 0
    assert diff_pct < 0.0001  # < 0.01%
else:
    diff_pct = abs(ch_sum - pg_sum) / abs(pg_sum) if pg_sum else 0
    assert diff_pct < 0.0001
```

---

## 8. _version 计算规则

### 8.1 实现

```python
# src/tushare_db/migration/version_calc.py
from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo


_TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")


def calc_version(row: dict) -> int:
    """
    Compute _version (ms timestamp) from row's updated_at / created_at.

    Priority:
      1. row['updated_at'] if not None
      2. row['created_at'] if not None
      3. current time
    """
    for col in ("updated_at", "created_at"):
        v = row.get(col)
        if v is not None:
            return _to_ms(v)
    return int(time.time() * 1000)


def _to_ms(dt: datetime) -> int:
    """Convert (possibly naive) datetime to Asia/Shanghai ms timestamp."""
    if dt.tzinfo is None:
        # PG TIMESTAMP without time zone → 假定为中国时间
        dt = dt.replace(tzinfo=_TZ_SHANGHAI)
    return int(dt.timestamp() * 1000)
```

### 8.2 时区抽样验证（**首跑前必做**）

```python
def verify_timezone_assumption(conn, sample_table: str = "tushare_stock_daily") -> bool:
    """
    Sample 10 rows; assert updated_at is within ±2 days of trade_date.
    If updated_at consistently 8 hours earlier → PG stores UTC, not local.
    """
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT trade_date, updated_at
            FROM {sample_table}
            WHERE updated_at IS NOT NULL
            LIMIT 10
        """)
        for trade_date, updated_at in cur.fetchall():
            delta_hours = (updated_at.replace(tzinfo=None) - trade_date).total_seconds() / 3600
            if not (-48 < delta_hours < 48):
                print(f"⚠️  Timezone mismatch: trade_date={trade_date} updated_at={updated_at}")
                return False
    return True
```

如果验证失败：在 `_to_ms` 里把 tzinfo 改为 `ZoneInfo("UTC")`。

---

## 9. 写入实现规范

### 9.1 复用 `insert_rows()`（不用 `insert_with_version()`）

`src/tushare_db/sink/clickhouse_sink.py:49` 的 `insert_rows()` 接收：
- `client`
- `table`（不带 db 前缀）
- `columns: list[str]`
- `rows: list[list[Any]]`
- `database: str`

**注意**：`insert_rows()` 不自动加 `_version`。本场景必须自己把 `_version` 加到 columns 列表末尾、每行末尾追加一个 ms timestamp。

### 9.2 Writer 实现

```python
# src/tushare_db/migration/writer.py
from __future__ import annotations

from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

from tushare_db.sink.clickhouse_sink import insert_rows
from tushare_db.migration.field_resolver import normalize_row
from tushare_db.migration.version_calc import calc_version

logger = structlog.get_logger()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def write_batch(
    ch_client,
    table: str,
    database: str,
    pg_columns: list[str],
    ch_columns: list[str],
    pg_rows: list[tuple],
    pg_to_dict_keys: list[str],   # 用于 calc_version：包含 updated_at/created_at
    full_pg_row_dicts: list[dict],
) -> int:
    """
    Convert PG rows → CH rows, attach _version, insert.

    Returns rows inserted.
    """
    # Map PG cols → positions in tuple
    col_index = {col: i for i, col in enumerate(pg_columns)}

    ch_rows: list[list[Any]] = []
    for pg_row, full_dict in zip(pg_rows, full_pg_row_dicts):
        # 1. 取 PG 中需要的列
        sub_row = tuple(pg_row[col_index[c]] for c in pg_columns)
        # 2. ×10000 单位归一化（按 PG 列名判断）
        normalized = normalize_row(sub_row, pg_columns, table_name=table)
        # 3. 计算 _version
        version = calc_version(full_dict)
        # 4. 拼成 CH 行（CH 列名顺序 + _version）
        ch_rows.append(list(normalized) + [version])

    columns_with_version = ch_columns + ["_version"]

    inserted = insert_rows(
        ch_client,
        table=table,
        columns=columns_with_version,
        rows=ch_rows,
        database=database,
    )

    logger.info(
        "batch_written",
        table=f"{database}.{table}",
        rows=inserted,
    )
    return inserted
```

### 9.3 关于 `pg_rows: list[tuple]` vs `full_pg_row_dicts: list[dict]`

`iter_pg_rows` 返回 tuple（按 columns 顺序）。但 `calc_version` 需要 `updated_at` / `created_at`，所以**读 PG 时要多读这两列**（`columns + ["updated_at", "created_at"]`），然后构造 dict 给 `calc_version`，再切片回去给 normalize/insert。

更简单的做法：在 `pg_reader.iter_pg_rows` 内部就把"含 timestamp 的完整列"和"用于 CH 写入的列"分开返回：
```python
def iter_pg_rows_v2(
    conn, table, ch_target_columns: list[str], batch_size: int,
) -> Iterator[tuple[list[tuple], list[dict]]]:
    """Returns (rows_in_ch_col_order, full_dicts_with_timestamps)."""
    full_columns = ch_target_columns + ["updated_at", "created_at"]
    # ... server-side cursor query SELECT full_columns
    # 每批 yield (rows_sliced_to_first_N, [dict(zip(full_columns, r)) for r in rows])
```

---

## 10. 断点续传与状态表

### 10.1 `_meta.migration_state` DDL

```sql
CREATE TABLE IF NOT EXISTS _meta.migration_state (
    pg_table         String,
    ch_table         String,
    ch_database      String,
    status           Enum8('pending'=0,'running'=1,'done'=2,'failed'=3),
    rows_migrated    UInt64,
    pg_row_count     UInt64,
    started_at       DateTime64(3, 'Asia/Shanghai'),
    finished_at      Nullable(DateTime64(3, 'Asia/Shanghai')),
    duration_sec     UInt32,
    error_msg        String,
    _version         UInt64
) ENGINE = ReplacingMergeTree(_version)
ORDER BY pg_table;
```

### 10.2 state.py

```python
# src/tushare_db/migration/state.py
from __future__ import annotations

import time
from datetime import datetime, timezone


def ensure_state_table(ch_client) -> None:
    """Create _meta.migration_state if not exists."""
    ch_client.command("""
        CREATE TABLE IF NOT EXISTS _meta.migration_state (
            pg_table String,
            ch_table String,
            ch_database String,
            status Enum8('pending'=0,'running'=1,'done'=2,'failed'=3),
            rows_migrated UInt64,
            pg_row_count UInt64,
            started_at DateTime64(3, 'Asia/Shanghai'),
            finished_at Nullable(DateTime64(3, 'Asia/Shanghai')),
            duration_sec UInt32,
            error_msg String,
            _version UInt64
        ) ENGINE = ReplacingMergeTree(_version) ORDER BY pg_table
    """)


def get_status(ch_client, pg_table: str) -> str | None:
    """Return current status, or None if no record."""
    result = ch_client.query(
        f"SELECT status FROM _meta.migration_state FINAL WHERE pg_table='{pg_table}'"
    )
    if not result.result_rows:
        return None
    return str(result.result_rows[0][0])


def mark_running(ch_client, spec, pg_row_count: int) -> None:
    _insert(ch_client, spec, "running", 0, pg_row_count, None, "")


def mark_done(ch_client, spec, rows_migrated: int, started_at: datetime) -> None:
    duration = int((datetime.now(timezone.utc) - started_at).total_seconds())
    _insert(ch_client, spec, "done", rows_migrated, 0, duration, "")


def mark_failed(ch_client, spec, error: str) -> None:
    _insert(ch_client, spec, "failed", 0, 0, 0, error[:500])


def _insert(ch_client, spec, status: str, rows: int, pg_count: int,
            duration: int | None, error: str) -> None:
    version = int(time.time() * 1000)
    now = datetime.now(timezone.utc)
    ch_client.insert(
        table="migration_state",
        data=[(
            spec.pg_table, spec.ch_table, spec.ch_database,
            status, rows, pg_count, now, now if status == "done" else None,
            duration or 0, error, version,
        )],
        column_names=[
            "pg_table", "ch_table", "ch_database", "status", "rows_migrated",
            "pg_row_count", "started_at", "finished_at", "duration_sec",
            "error_msg", "_version",
        ],
        database="_meta",
    )
```

### 10.3 主流程使用

```python
# scripts/migrate.py 内
status = get_status(ch_client, spec.pg_table)
if status == "done":
    logger.info("skip_already_done", table=spec.pg_table)
    continue
if status == "running":
    logger.warning("table_was_running_resuming", table=spec.pg_table)
    # 重置为 pending（或继续重跑——靠 _version 去重）

mark_running(ch_client, spec, pg_row_count)
try:
    rows_migrated = run_migration(spec, conn, ch_client)
    mark_done(ch_client, spec, rows_migrated, started_at)
except Exception as e:
    mark_failed(ch_client, spec, str(e))
    raise
```

---

## 11. 校验方案

### 11.1 三层校验

```python
# src/tushare_db/migration/validator.py
from __future__ import annotations

import random
from typing import Any
import structlog

logger = structlog.get_logger()


# Layer 1: 行数
def validate_row_count(pg_conn, ch_client, spec) -> dict:
    pg_count = _pg_total_rows(pg_conn, spec)
    ch_count = _ch_count(ch_client, spec)

    return {
        "layer": "row_count",
        "pg_count": pg_count,
        "ch_count": ch_count,
        "diff": ch_count - pg_count,
        "passed": ch_count == pg_count,
    }


def _pg_total_rows(pg_conn, spec) -> int:
    """Sum rows across all partitions (or single table)."""
    if not spec.partitioned:
        with pg_conn.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {spec.pg_table}")
            return cur.fetchone()[0]

    total = 0
    for year in spec.partition_years:
        partition = spec.partition_pattern.format(year=year)
        with pg_conn.cursor() as cur:
            try:
                cur.execute(f"SELECT count(*) FROM {partition}")
                total += cur.fetchone()[0]
            except Exception:
                continue
    if spec.include_default_partition:
        with pg_conn.cursor() as cur:
            try:
                cur.execute(f"SELECT count(*) FROM {spec.pg_table}_default")
                total += cur.fetchone()[0]
            except Exception:
                pass
    return total


def _ch_count(ch_client, spec) -> int:
    result = ch_client.query(
        f"SELECT count() FROM {spec.ch_database}.{spec.ch_table} FINAL"
    )
    return int(result.result_rows[0][0])


# Layer 2: 抽样
def validate_sample(pg_conn, ch_client, spec, sample_size: int = 1000) -> dict:
    """
    Random sample by primary key, compare each cell.
    Returns {passed, total, mismatches: list[dict]}.
    """
    if not spec.date_column:
        return {"layer": "sample", "passed": True, "total": 0, "skipped": "no date column"}

    # 1. 从 PG 抽 sample_size 个 (ts_code, date) 主键
    with pg_conn.cursor() as cur:
        # 用 TABLESAMPLE 或 ORDER BY random() — random() 慢但更准
        if spec.partitioned:
            partition = f"{spec.pg_table}_{spec.partition_years[-1]}"
            cur.execute(f"""
                SELECT ts_code, {spec.date_column}
                FROM {partition}
                ORDER BY random()
                LIMIT {sample_size}
            """)
        else:
            cur.execute(f"""
                SELECT ts_code, {spec.date_column}
                FROM {spec.pg_table}
                ORDER BY random()
                LIMIT {sample_size}
            """)
        keys = cur.fetchall()

    mismatches = []
    for ts_code, date_val in keys:
        # 2. 从 PG 拿完整行
        # 3. 从 CH 拿完整行
        # 4. 逐字段比较（注意 ×10000 转换）
        # ... (见下面 _compare_row)
        pass

    return {"layer": "sample", "total": len(keys), "passed": len(mismatches) == 0,
            "mismatches": mismatches[:10]}


# Layer 3: 聚合
def validate_aggregates(pg_conn, ch_client, spec, numeric_cols: list[str]) -> dict:
    """
    For each numeric column: sum, min, max, count_distinct(ts_code).
    """
    from tushare_db.migration.field_resolver import should_normalize

    results = []
    for col in numeric_cols:
        with pg_conn.cursor() as cur:
            cur.execute(f"SELECT sum({col}), min({col}), max({col}) FROM {spec.pg_table}")
            pg_sum, pg_min, pg_max = cur.fetchone()

        ch_result = ch_client.query(
            f"SELECT sum({col}), min({col}), max({col}) "
            f"FROM {spec.ch_database}.{spec.ch_table} FINAL"
        )
        ch_sum, ch_min, ch_max = ch_result.result_rows[0]

        # ×10000 比例对账
        scale = 10_000 if should_normalize(col, spec.pg_table) else 1
        expected_sum = float(pg_sum or 0) * scale
        diff_pct = abs(float(ch_sum or 0) - expected_sum) / max(abs(expected_sum), 1)

        results.append({
            "col": col,
            "pg_sum": pg_sum, "ch_sum": ch_sum, "scale": scale,
            "diff_pct": diff_pct,
            "passed": diff_pct < 0.0001,
        })

    return {"layer": "aggregate", "cols": results,
            "passed": all(r["passed"] for r in results)}
```

### 11.2 单表校验主流程

```python
def validate_table(pg_conn, ch_client, spec) -> bool:
    r1 = validate_row_count(pg_conn, ch_client, spec)
    if not r1["passed"]:
        logger.error("row_count_mismatch", **r1)
        return False

    r2 = validate_sample(pg_conn, ch_client, spec)
    if not r2["passed"]:
        logger.error("sample_mismatch", **r2)
        return False

    # 选关键数值列（可在 tables.yaml 配 validate_columns，否则取所有 Float64 列）
    numeric_cols = _get_numeric_columns(ch_client, spec)
    r3 = validate_aggregates(pg_conn, ch_client, spec, numeric_cols)
    if not r3["passed"]:
        logger.error("aggregate_mismatch", **r3)
        return False

    return True
```

---

## 12. 执行流程（按优先级分批）

### 12.1 Step 0：环境准备

```bash
# 已在 §1 完成
✅ PG 连通性
✅ CH 连通性
✅ .env 加 PG_*
✅ uv add psycopg[binary]
✅ 磁盘 ≥ 30 GB
```

### 12.2 Step 1：探测真实表清单

```bash
python -c "
from tushare_db.migration.pg_reader import pg_connection
with pg_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('''
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_name LIKE 'tushare_%'
            ORDER BY table_name
        ''')
        for row in cur.fetchall():
            print(row[0])
" > docs/migration/pg_tables_actual.txt
```

```bash
docker compose exec clickhouse clickhouse-client --query "
  SELECT name FROM system.tables
  WHERE database='tushare' ORDER BY name
" > docs/migration/ch_tables_actual.txt
```

**对账输出 `missing_tables.md`**：
```python
# 简单对账逻辑
pg_tables = set(open("docs/migration/pg_tables_actual.txt").read().splitlines())
ch_tables = set(open("docs/migration/ch_tables_actual.txt").read().splitlines())

# PG 有 CH 没有 —— 需要补建
need_create = pg_tables - ch_tables - {f"{t}_{y}" for t in [...] for y in range(2019, 2028)}

# 写到 missing_tables.md
```

### 12.3 Step 2：建缺表

**两条路径**：

**路径 A（推荐）：从 Tushare 采样 + 推断**
```bash
docker compose exec pipeline-scheduler tushare-db sample-apis --only <missing_table>
docker compose exec pipeline-scheduler tushare-db rebuild-schema --interface <missing_table>
```

**路径 B（备选，无 token 或不想消耗配额）：从 PG schema 自动生成 DDL**

新建 `scripts/migrate_schemas.py`：
```python
"""Generate CH DDL from PG information_schema."""
import os
import psycopg
from tushare_db.migration.type_mapper import pg_type_to_ch
from tushare_db.sink.clickhouse_sink import get_native_client


def gen_ddl(pg_conn, pg_table: str, ch_database: str = "tushare") -> str:
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (pg_table,))
        cols = cur.fetchall()

    column_defs = []
    for name, pg_type, nullable in cols:
        if name in ("created_at", "updated_at"):
            continue
        ch_type = pg_type_to_ch(pg_type, name)
        if nullable == "YES" and not ch_type.startswith("LowCardinality"):
            ch_type = f"Nullable({ch_type})"
        column_defs.append(f"    `{name}` {ch_type}")

    column_defs.append("    `_version` UInt64")

    # 推断 PARTITION BY 和 ORDER BY
    has_trade_date = any(c[0] == "trade_date" for c in cols)
    has_ts_code = any(c[0] == "ts_code" for c in cols)
    partition_by = "toYYYYMM(trade_date)" if has_trade_date else "tuple()"
    order_by = "(ts_code, trade_date)" if (has_trade_date and has_ts_code) else "tuple()"

    return f"""
CREATE TABLE IF NOT EXISTS {ch_database}.{pg_table} (
{',\n'.join(column_defs)}
) ENGINE = ReplacingMergeTree(_version)
PARTITION BY {partition_by}
ORDER BY {order_by}
"""


if __name__ == "__main__":
    with psycopg.connect(...) as conn:
        ch = get_native_client(...)
        for missing in open("docs/migration/missing_tables.md").read().splitlines():
            ddl = gen_ddl(conn, missing)
            print(ddl)
            ch.command(ddl)
```

### 12.4 Step 3：⚠️ 停 tushare-hub scheduler

```bash
# 找到 tushare-hub 的容器名（在另一个 compose 项目下）
cd F:/AIcoding_space/projects/tushare-hub
docker compose stop scheduler          # 或 docker compose down

# 验证 PG 不再有写入：5 分钟后看 max(updated_at)
docker compose exec clickhouse clickhouse-client --query "SELECT now()"
sleep 300
psql -c "SELECT max(updated_at) FROM tushare_stock_basic"
# 期望：max(updated_at) 没增长
```

### 12.5 Step 4：Dry-run 三份报告

```bash
docker compose exec pipeline-scheduler python scripts/migrate.py dry-run
```

`migrate.py dry-run` 内部：
1. 遍历 tables.yaml 每个 spec
2. 对每张表跑 `diff_fields()` → 写 field_diff_report.md
3. 对每张表的列扫一遍 `should_normalize()` → 写 amount_conversion_report.md
4. 对分区表跑 `check_partition_duplicates()` → 写 partition_dup_check.md
5. 不写任何 CH 数据

### 12.6 Step 5：⚠️ 用户人工 review

执行 AI 必须**停下来等用户确认**：
```
✋ Dry-run 完成。请人工 review 以下三份报告：
   1. docs/migration/field_diff_report.md
   2. docs/migration/amount_conversion_report.md
   3. docs/migration/partition_dup_check.md

Review 完成后，确认无误，请回复"go"。如有疑问，请指出具体表/列。
```

### 12.7 Step 6：P0 实跑

```bash
# 6.1 先跑最小表试通路（71k 行）
docker compose exec pipeline-scheduler python scripts/migrate.py run \
  --priority P0 --only tushare_stock_basic --confirm

# 6.2 验证
docker compose exec pipeline-scheduler python scripts/migrate.py validate \
  --only tushare_stock_basic
# 期望：row_count ✅ sample ✅ aggregate ✅

# 6.3 跑大表 stock_daily 730 万行
docker compose exec -d pipeline-scheduler python scripts/migrate.py run \
  --priority P0 --only tushare_stock_daily --confirm
# 后台跑，预计 30-60 分钟

# 6.4 监控
watch -n 60 'docker compose exec clickhouse clickhouse-client --query \
  "SELECT count() FROM tushare.tushare_stock_daily FINAL"'

# 6.5 跑剩余 P0 6 张表
docker compose exec pipeline-scheduler python scripts/migrate.py run \
  --priority P0 --confirm

# 6.6 全量 P0 校验
docker compose exec pipeline-scheduler python scripts/migrate.py validate \
  --priority P0

# 6.7 OPTIMIZE FINAL（仅 P0 数据表，非 _meta）
for tbl in stock_basic stock_daily stock_weekly adj_factor daily_basic stk_limit suspend_d; do
  docker compose exec clickhouse clickhouse-client --query \
    "OPTIMIZE TABLE tushare.tushare_$tbl FINAL"
done
```

### 12.8 Step 7：P1/P2/P3

```bash
docker compose exec pipeline-scheduler python scripts/migrate.py run --priority P1 --confirm
docker compose exec pipeline-scheduler python scripts/migrate.py validate --priority P1

docker compose exec pipeline-scheduler python scripts/migrate.py run --priority P2 --confirm
docker compose exec pipeline-scheduler python scripts/migrate.py validate --priority P2

docker compose exec pipeline-scheduler python scripts/migrate.py run --priority P3 --confirm
docker compose exec pipeline-scheduler python scripts/migrate.py validate --priority P3
```

### 12.9 Step 8：收尾（**关键**）

#### 8.1 OPTIMIZE FINAL 全量数据表

```bash
docker compose exec pipeline-scheduler python scripts/migrate.py optimize --all
```

实现：
```python
@cli.command()
@click.option("--all", "all_tables", is_flag=True)
def optimize(all_tables):
    specs = load_tables()
    for spec in specs:
        ch_client.command(
            f"OPTIMIZE TABLE {spec.ch_database}.{spec.ch_table} FINAL"
        )
        click.echo(f"OPTIMIZED {spec.ch_database}.{spec.ch_table}")
```

#### 8.2 ⚠️ 写 _meta.sync_state（**防 pipeline 重拉全量**）

```python
# src/tushare_db/migration/sync_state_writer.py
from __future__ import annotations

import time
from datetime import datetime, timezone


def write_sync_state_done(ch_client, spec) -> None:
    """
    Write a 'done' record to _meta.sync_state for each migrated table.
    Without this, pipeline scheduler will see no sync history and re-pull
    historical data from Tushare API.

    For partitioned tables (date_loop strategy), write one record per
    distinct trade_date that exists in CH:
    """
    ch_table_full = f"{spec.ch_database}.{spec.ch_table}"

    if not spec.date_column:
        # 非时间序列表：写一条 scope_key='full'
        _insert_sync_state(
            ch_client,
            interface=spec.pg_table.replace("tushare_", ""),
            scope_key="full",
            rows=_get_total_rows(ch_client, ch_table_full),
        )
        return

    # 时间序列表：每个 trade_date 写一条
    result = ch_client.query(
        f"SELECT {spec.date_column}, count() FROM {ch_table_full} FINAL "
        f"GROUP BY {spec.date_column}"
    )
    for trade_date, cnt in result.result_rows:
        scope_key = f"{spec.pg_table.replace('tushare_', '')}:{trade_date.strftime('%Y%m%d')}"
        _insert_sync_state(
            ch_client,
            interface=spec.pg_table.replace("tushare_", ""),
            scope_key=scope_key,
            rows=int(cnt),
        )


def _insert_sync_state(ch_client, interface: str, scope_key: str, rows: int) -> None:
    version = int(time.time() * 1000)
    now = datetime.now(timezone.utc)
    ch_client.insert(
        table="sync_state",
        data=[(interface, scope_key, "done", rows, now, now, 0, "", version)],
        column_names=[
            "interface", "scope_key", "status", "rows",
            "last_success_at", "heartbeat_at", "attempts",
            "last_error", "_version",
        ],
        database="_meta",
    )


def _get_total_rows(ch_client, ch_table_full: str) -> int:
    return int(ch_client.query(f"SELECT count() FROM {ch_table_full} FINAL").result_rows[0][0])
```

```bash
# 收尾命令
docker compose exec pipeline-scheduler python scripts/migrate.py write-sync-state --all
```

#### 8.3 重启 tushare-db pipeline-scheduler

```bash
docker compose restart pipeline-scheduler

# 等 30s 后看日志，确认 scheduler 没跑全量回补
docker compose logs --tail 100 pipeline-scheduler

# 期望看到：
#   - "trade_cal pre-check OK, 13161 rows"
#   - "Skipping batch A: not a trading day" (周末) 或 "Skipping daily incremental: T-1 already done"
#   - **不应**看到：长时间运行的 backfill
```

#### 8.4 验证次日增量

等到下一个交易日 17:00 后：
```bash
docker compose exec clickhouse clickhouse-client --query "
  SELECT batch, status, started_at, units_total, units_done
  FROM _meta.sync_runs
  WHERE started_at > today() - 1
  ORDER BY started_at DESC
"
# 期望：batch=A status=done，单元数与往常一致（不是几千几万的全量）
```

### 12.10 Step 9：收尾文档

`docs/migration/migration_log.md` 模板：
```markdown
# Migration Log — 2026-04-26

## 总览
- 开始时间：2026-04-26 14:00
- 结束时间：2026-04-26 19:35
- 总耗时：5h 35min
- PG 总行数：15,728,xxx
- CH 总行数：15,728,xxx（去重前）
- 校验通过：47/47

## 逐表

| pg_table | priority | rows | 耗时 | row_count | sample | aggregate |
|----------|---------|------|------|-----------|--------|-----------|
| stock_basic | P0 | 5,432 | 12s | ✅ | ✅ | ✅ |
| stock_daily | P0 | 7,327,237 | 42min | ✅ | ✅ | ✅ |
...

## 已写入 _meta.sync_state

| interface | scope_keys 数 | rows |
|-----------|--------------|------|
| stock_daily | 1500 | 7,327,237 |
| adj_factor | 1500 | 4,xxx,xxx |
...

## 后续监控

- pipeline-scheduler 重启后第一个交易日（2026-04-29）增量正常
- 5 个交易日后再次 `verify --priority P0` 应全过
```

---

## 13. 风险清单与应对

| 风险 | 等级 | 详细应对 |
|------|------|---------|
| **金额单位未转换** | 🔴 致命 | §7 已定义；dry-run 必须产 amount_conversion_report.md；校验阶段聚合 SUM 按 ×10000 比例对比；偏差 > 0.01% 立即停 |
| **跨年分区重复行** | 🔴 高 | §5.3 强制预检；如有重复且 updated_at 相同→去重结果不确定→**必须告知用户**让其决定 |
| **PG TIMESTAMP 时区** | 🟡 中 | §8.2 抽样验证；trade_date='2024-06-01' 的 updated_at 应在 2024-06-01 ±2 天，否则 PG 存的是 UTC |
| **Decimal64(2) 溢出** | 🟡 中 | §6.1 强制 NUMERIC → Float64（不用 Decimal64(2)）；如 CH 已建表用了 Decimal64(2)，先 ALTER 或重建 |
| **clickhouse-connect HTTP 大批量超时** | 🟢 低 | batch_size ≤ 100k，超时 60s（默认），retry 3 次（§9.2）|
| **网络中断导致部分写入** | 🟢 低 | _version + ReplacingMergeTree 天然幂等；重跑同 batch 不会重复 |
| **OPTIMIZE 阻塞读** | 🟢 低 | 收尾阶段集中跑，不要每张表都跑（§12.9） |
| **迁移后 pipeline 重拉全量** | 🔴 高 | §12.9 必须 write_sync_state；不写则 pipeline 看到 sync_state 空，从 2020-01-01 重拉 |
| **PG 在迁移期间仍在写入** | 🔴 高 | §12.4 强制 stop tushare-hub scheduler；用 max(updated_at) 5 分钟前后对比验证 |
| **PG DATE 导出格式** | 🟢 低 | psycopg3 返回 datetime.date，clickhouse_connect 自动接受；E2E 测试覆盖 |
| **psycopg2/3 共存** | 🟢 低 | import 名称不同（psycopg2 vs psycopg），可共存；不动 tushare-hub 的依赖 |
| **stock_daily 730 万行 OOM** | 🟢 低 | server-side cursor + batch_size=100k；内存峰值 < 500MB |
| **CH 缺表** | 🟡 中 | §12.3 两条路径（API 采样 / PG schema 推断）；如缺表 > 20 张用路径 B |
| **trade_cal 在 _meta 而非 tushare** | 🟡 中 | §4.6 明确 ch_database='_meta'；勿误写到 tushare 库 |
| **column_renames 遗漏** | 🟡 中 | §4.5 已识别 4 处；dry-run 的 field_diff_report.md 会暴露 pg_only_drop 列，人工 review 时如发现"明显应该映射但被丢弃"的列，立即加进 column_renames |
| **TUSHARE_TOKEN 失效**（如需 §12.3 路径 A） | 🟡 中 | 用路径 B（PG schema 推断），不依赖 token |
| **_meta.sync_state 写入冲突** | 🟢 低 | sync_state 是 ReplacingMergeTree，重复写按最新 _version 取胜；不会导致冲突 |

---

## 14. 测试要求

### 14.1 单元测试（≥ 80% 覆盖核心模块）

`tests/unit/test_migration_type_mapper.py`：
```python
import pytest
from tushare_db.migration.type_mapper import pg_type_to_ch


@pytest.mark.parametrize("pg_type,col,expected", [
    ("character varying", "ts_code", "LowCardinality(String)"),
    ("character varying", "name", "String"),
    ("integer", "x", "Int32"),
    ("bigint", "x", "Int64"),
    ("numeric", "x", "Float64"),
    ("numeric(18,4)", "x", "Float64"),
    ("date", "trade_date", "Date"),
    ("timestamp without time zone", "x", "DateTime64(3)"),
    ("boolean", "is_open", "UInt8"),
    ("jsonb", "data", "String"),
])
def test_pg_type_to_ch(pg_type, col, expected):
    assert pg_type_to_ch(pg_type, col) == expected
```

`tests/unit/test_migration_field_resolver.py`：
```python
import pytest
from tushare_db.migration.field_resolver import (
    resolve_columns, should_normalize, normalize_value,
)


def test_resolve_columns_basic():
    pg_in, ch_in = resolve_columns(
        pg_cols=["ts_code", "trade_date", "open", "created_at", "updated_at"],
        ch_cols=["ts_code", "trade_date", "open", "_version"],
    )
    assert pg_in == ["ts_code", "trade_date", "open"]
    assert ch_in == ["ts_code", "trade_date", "open"]


def test_resolve_columns_with_rename():
    pg_in, ch_in = resolve_columns(
        pg_cols=["ts_code", "end_date", "unit_nav"],
        ch_cols=["ts_code", "cal_date", "unit_nav"],
        renames={"end_date": "cal_date"},
    )
    assert pg_in == ["ts_code", "end_date", "unit_nav"]
    assert ch_in == ["ts_code", "cal_date", "unit_nav"]


@pytest.mark.parametrize("col,expected", [
    ("total_revenue", True),
    ("total_mv", True),
    ("circ_mv", True),
    ("net_profit", True),
    ("vol", False),               # 成交量
    ("turnover_rate", False),     # 比率
    ("pe_ttm", False),
    ("basic_eps", False),         # _per_share 排除
    ("amount", True),
    ("buy_elg_amount", True),
])
def test_should_normalize(col, expected):
    assert should_normalize(col, "tushare_income") == expected


def test_normalize_value():
    assert normalize_value("total_revenue", 1000) == 10_000_000
    assert normalize_value("total_revenue", None) is None
    assert normalize_value("vol", 1000) == 1000


def test_share_only_normalizes_for_fund_tables():
    """*_share 仅在 fund_* 表里归一化."""
    assert should_normalize("total_share", "tushare_fund_portfolio") is True
    assert should_normalize("total_share", "tushare_stock_basic") is False
```

`tests/unit/test_migration_version_calc.py`：
```python
from datetime import datetime
from tushare_db.migration.version_calc import calc_version


def test_calc_version_uses_updated_at():
    row = {
        "updated_at": datetime(2024, 6, 1, 10, 30, 0),
        "created_at": datetime(2024, 5, 1, 10, 30, 0),
    }
    v = calc_version(row)
    # 中国时间 2024-06-01 10:30 → UTC 02:30
    assert v == int(datetime(2024, 6, 1, 2, 30, 0).timestamp() * 1000)


def test_calc_version_falls_back_to_created():
    row = {"updated_at": None, "created_at": datetime(2024, 5, 1, 10, 30, 0)}
    v = calc_version(row)
    assert v > 0


def test_calc_version_falls_back_to_now():
    row = {"updated_at": None, "created_at": None}
    v = calc_version(row)
    assert v > 1700000000000
```

### 14.2 集成测试

`tests/integration/test_migration_e2e.py`：
```python
import pytest
from testcontainers.clickhouse import ClickHouseContainer

@pytest.mark.integration
def test_stock_basic_full_migration(tmp_path):
    """End-to-end: mock PG → CH via testcontainers, validate 3 layers."""
    # 1. 起 ClickHouse 容器
    # 2. 准备 mock PG 数据（用 sqlite 或 pg testcontainer，10 行）
    # 3. 跑 migrate.py run --only mock_table
    # 4. validate_row_count / validate_sample / validate_aggregates
    # 5. 断言 CH 中数据 = PG 中数据 × 转换规则
    ...
```

### 14.3 不需要测试每张表

配置驱动 = 一个测过的代码路径处理所有表。stock_basic 集成测试通了，等于其他 46 张表的代码路径都通了。

---

## 15. 执行 Checklist（最终验收）

执行 AI 跑完逐项打钩（**全部 ✅ 才算 done**）：

### 15.1 准备阶段
- [ ] `pyproject.toml` 加 `psycopg[binary]>=3.1`，`uv sync` 通过
- [ ] `.env` 加 PG_* 变量（host/port/user/password/db）
- [ ] PG 连通性测试通过（§1.1）
- [ ] CH 连通性测试通过（§1.2）
- [ ] CH 数据卷剩余 ≥ 30 GB
- [ ] PG 实际表清单与 §4 对账（`pg_tables_actual.txt` 已生成）
- [ ] missing_tables.md 已生成
- [ ] 19 张（或实际数量）CH 缺表已建好（用路径 A 或 B）
- [ ] tushare-hub scheduler 已停止；5 分钟后 max(updated_at) 不再增长

### 15.2 Dry-run 阶段
- [ ] field_diff_report.md 已生成
- [ ] amount_conversion_report.md 已生成
- [ ] partition_dup_check.md 已生成（如有重复行已与用户确认）
- [ ] PG TIMESTAMP 时区已抽样验证（§8.2）
- [ ] 用户已 review 三份报告，给出 "go" 确认

### 15.3 实跑阶段
- [ ] P0 stock_basic（71k 行）跑通 + 三层校验通过（试通路）
- [ ] P0 stock_daily（730 万行）跑通 + 三层校验通过
- [ ] P0 剩余 6 张表全部 done + 三层校验通过
- [ ] P1 5 张财务表全部 done + 三层校验通过
- [ ] P2 8 张资金流表全部 done + 三层校验通过
- [ ] P3 ~26 张其余表全部 done + 三层校验通过

### 15.4 收尾阶段
- [ ] 所有数据表已 OPTIMIZE TABLE FINAL
- [ ] 所有迁移表已写入 _meta.sync_state（每个 trade_date 一条）
- [ ] _meta.migration_state 中所有表 status='done'
- [ ] tushare-db pipeline-scheduler 重启成功
- [ ] 重启后日志显示**不会**触发全量 backfill
- [ ] migration_log.md 已生成（含每表行数/耗时/校验结果）

### 15.5 验证次日增量（T+1 工作日）
- [ ] 17:00 batch A 自动跑完，单元数 ≈ 当日新增（不是历史全量）
- [ ] 18:00 batch B 跑完
- [ ] 19:00 batch C 跑完
- [ ] 19:45 batch D 跑完
- [ ] 抽样对比：CH 新增的 trade_date 数据 与 Tushare 网页一致

---

## 16. 不在本次范围内（明确边界）

- ❌ tushare-hub 项目的修改（仅停 scheduler，不改代码）
- ❌ tushare-db 现有 `runner/` `planner/` `meta/` `scheduler/` 任何代码的修改
- ❌ ClickHouse 现有表的 ALTER（如 Decimal64(2) 改 Float64 — 见 §13；如必须改，先与用户确认）
- ❌ 港股 / 美股 / 分钟行情 / 新闻类付费接口
- ❌ pipeline-scheduler 的修改

**唯一对主项目的影响**：
| 变更 | 文件 | 影响 |
|------|------|------|
| 新增 | `scripts/migrate.py` | 独立 CLI |
| 新增 | `scripts/migrate_schemas.py`（可选） | 独立 |
| 新增 | `src/tushare_db/migration/` 整个目录 | 与现有模块零耦合 |
| 新增 | `config/migration/tables.yaml` | 与现有 config/interfaces/ 并列 |
| 新增 | `tests/unit/test_migration_*.py` | 独立 |
| 新增 | `tests/integration/test_migration_e2e.py` | 独立 |
| 修改 | `pyproject.toml` | 仅加一行 psycopg |
| 修改 | `.env` | 仅加 PG_* |

迁移完成后，如不再需要：删除 `src/tushare_db/migration/` + `config/migration/` + `scripts/migrate*.py` + `tests/*test_migration*` + 回滚 .env 的 PG_*，即可零残留。

---

## 17. 出错处理 FAQ

### Q1：跑到一半 docker compose down 了，怎么办？
重启 docker compose up -d，**不需要清空 CH 数据**。直接重跑 `python scripts/migrate.py run`，已 done 的表会跳过，running/failed 的表会重试（_version 去重）。

### Q2：某张表 row_count 校验失败，CH 比 PG 少？
1. 看 `_meta.migration_state` 的 error_msg
2. 检查 batch 日志（structlog 输出有 batch_id）
3. 确认 PG 没有 NULL 主键（NULL 主键 ReplacingMergeTree 行为不可预测）
4. 重置 state 并重跑：
   ```sql
   ALTER TABLE _meta.migration_state DELETE WHERE pg_table='xxx'
   ```
   ```bash
   docker compose exec pipeline-scheduler python scripts/migrate.py run --only xxx --confirm
   ```

### Q3：聚合校验偏差 > 0.01%？
1. 用 SQL 抽 5 行手动比对：
   ```sql
   -- PG
   SELECT ts_code, total_revenue FROM tushare_income
   WHERE ts_code='600519.SH' AND end_date='2023-12-31';
   -- CH
   SELECT ts_code, total_revenue FROM tushare.tushare_income FINAL
   WHERE ts_code='600519.SH' AND end_date='2023-12-31';
   ```
2. 如果 CH 值正好是 PG 值的 10000 倍 → 单位转换正确，可能是聚合时 NULL 处理不同
3. 如果 CH 值 = PG 值（没 ×10000）→ `should_normalize()` 漏判，加白名单
4. 如果 CH 值 ≠ PG 值的 10000 倍且不等于 PG 值 → 业务 bug，立即停

### Q4：scheduler 重启后跑全量回补怎么办（最坏情况）？
1. 立即 `docker compose stop pipeline-scheduler`
2. 检查 `_meta.sync_state` 是否真的写入了：
   ```sql
   SELECT count() FROM _meta.sync_state FINAL WHERE interface='daily'
   ```
3. 如果 0 → 重跑 `python scripts/migrate.py write-sync-state --all`
4. 重启 scheduler，再观察

### Q5：dry-run 时 PG 连接被服务端断开（statement_timeout）？
- 加大 PG 的 `statement_timeout`（在 .env 里加 `PGOPTIONS='-c statement_timeout=600000'`）
- 或把 dry-run 拆小（每张表单独跑）

### Q6：testcontainers 在 Windows 上起不来？
- 集成测试在 WSL2 或 CI 跑，Windows 主机不必跑
- 单元测试不依赖 Docker，所有平台可跑

### Q7：内存不够，stock_daily OOM？
- batch_size 从 100000 降到 50000
- 或在 docker-compose.yml 给 pipeline 容器加 mem_limit: 4g

### Q8：write-sync-state 跑很久？
正常。stock_daily 1500 个 trade_date × 7327237 行 = 1500 条 sync_state 记录。每条 INSERT 单独写很慢。**优化**：改用批量 insert：
```python
# sync_state_writer.py 优化
def write_sync_state_batch(ch_client, records: list[tuple]):
    ch_client.insert(
        table="sync_state", data=records,
        column_names=[...], database="_meta",
    )
```

### Q9：跑完后 CH 磁盘比预期大很多？
- 跑 `OPTIMIZE TABLE ... FINAL`（§12.9）
- 检查 `system.parts` 中是否有未合并的小 part：
  ```sql
  SELECT table, count() AS parts FROM system.parts
  WHERE database='tushare' GROUP BY table HAVING parts > 50
  ```
- 大量小 part → batch_size 太小，下次调大

### Q10：用户说"不要停 tushare-hub scheduler"？
- 这违反 §13 高风险约束。**必须告知用户**：
  1. 不停 scheduler → 迁移期间 PG 新写入的数据不会同步到 CH
  2. 迁移完后这些数据需要补：`tushare-db backfill --interface <name> --from <migrate_start> --to <migrate_end>`
- 用户接受后，记录在 migration_log.md 的"已知数据窗口差"段落

---

## 18. 文档自检（执行 AI 必读）

写完 `migrate.py` 和 `migration/*.py` 后，自检：

1. [ ] `Read` 一遍本 EXECUTION_PLAN.md，确认每节都理解
2. [ ] `Read` `src/tushare_db/sink/clickhouse_sink.py:49` 的 `insert_rows` 签名，确认 `writer.py` 调用正确
3. [ ] `Read` `src/tushare_db/schema/type_map.py` 的 `_FINANCIAL_AMOUNT_SUFFIXES`，确认 `field_resolver.py` 的 `_NORMALIZE_X10000_PATTERNS` 与之**逻辑等价**（不要遗漏字段）
4. [ ] 跑 `pytest tests/unit/test_migration_*.py -v`，全部通过
5. [ ] 跑 `pytest tests/integration/test_migration_e2e.py -v`（如 Docker 可用）
6. [ ] dry-run 一次，三份报告都生成
7. [ ] 读三份报告，确认列出来的列符合预期
8. [ ] 与用户确认后再 `--confirm` 实跑

---

## 19. 关键决策点（需要用户确认）

执行 AI 在以下时刻**必须停下来等用户**：

| 决策点 | 何时 | 给用户看什么 |
|--------|------|-------------|
| **D1** | Step 1 后 | missing_tables.md，由用户确认是否补建 |
| **D2** | Step 4 dry-run 后 | 三份报告，确认字段映射、单位转换、跨年重复 |
| **D3** | Step 4 后，若 partition_dup_check 有重复 | 重复行清单，由用户决定是否继续 |
| **D4** | Step 6 P0 试通路（stock_basic）后 | 单表的三层校验结果，由用户确认是否继续大表 |
| **D5** | Step 7 P3 后 | 全量 migration_log.md，由用户确认是否进入 Step 8 收尾 |
| **D6** | Step 8 重启 scheduler 后 | scheduler 启动日志，由用户确认是否真的没跑全量 |

---

## 20. 总时长与交付物

### 总时长
- 编码：1-2 天（执行 AI 写完 `migration/` 模块 + 测试）
- 执行：4-6 小时（自动化部分）+ 等用户 review 时长（不可控）

### 交付物
1. `scripts/migrate.py`
2. `src/tushare_db/migration/` 整个模块（10 个文件）
3. `config/migration/tables.yaml`（47+ 条目）
4. `tests/unit/test_migration_*.py` × 3
5. `tests/integration/test_migration_e2e.py`
6. `docs/migration/` 下的 4 份生成报告
7. CH 中 ~1570 万行数据 + sync_state 标记
8. tushare-db pipeline-scheduler 正常运行

---

> **最后**：本文档与原 dragonfly 计划比，新增了：
> - §0 一页流程图与时间预算
> - §10 完整 state.py 代码
> - §17 10 个 FAQ（出错处理）
> - §19 6 个用户决策点
> - §3.2 完整 Pydantic loader
> - §6.1 完整 type_mapper
> - §7.2 完整 field_resolver（含 fund 表特例）
> - §8.2 时区抽样验证函数
> - §9 关于"为什么不用 insert_with_version"的明确说明
> - §11.1 完整 validator 三层实现
> - §12.9 完整 sync_state_writer
>
> 执行 AI 拿到本文档可以**不再回头读 dragonfly 或上游需求文档**，即可独立完成全部迁移工作。

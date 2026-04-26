# Tushare Hub → Tushare DB 迁移执行文档 — 编写计划

## Context

用户已经在 `F:\AIcoding_space\projects\tushare-hub\docs\migration_to_tushare_db.md` 写好了**需求文档**（v1.0，2026-04-26），描述了把 PG 47 张表 / ~1570 万行历史数据迁到 ClickHouse 的整体目标。

**这次任务不是写迁移代码本身**，而是：把那份偏需求/规则的文档，转成一份**给本地 AI 直接执行的"详细骨架"级执行文档**，落到 tushare-db 项目下，由另一个 AI 读完后能直接动手写 `scripts/migrate.py` 与配套模块。

约束条件（已与用户确认）：
- 输出路径：`tushare_db/docs/migration/EXECUTION_PLAN.md`（新建 migration 子目录）
- 详细程度：**详细骨架**——含目录结构、关键函数签名、伪代码、类型映射表、checklist；不嵌完整可运行代码
- 范围策略：**通用框架 + 配置驱动**（PG 注册的 47 张核心表，加上对账发现的额外匹配表），由 YAML 注册表驱动，按 P0→P3 优先级分批跑
- 字段不一致策略：**以 CH DDL 为基准**，PG 多余字段丢弃，CH 缺的列直接跳过（与 pipeline 保持一致）

## 已完成的探索结论（写文档时直接引用，不要再让执行 AI 重新探索）

### tushare-db 侧（目标）
- 包路径：[src/tushare_db/](src/tushare_db/)，CLI 用 click，日志用 structlog
- 复用点：
  - [src/tushare_db/sink/clickhouse_sink.py:29](src/tushare_db/sink/clickhouse_sink.py:29) — `get_native_client()`（HTTP 8123）
  - [src/tushare_db/sink/clickhouse_sink.py:49](src/tushare_db/sink/clickhouse_sink.py:49) — `insert_rows()` 批量插入（**迁移复用此函数**，不用 `insert_with_version()` 因为需保留 PG timestamp 作 _version）
  - [src/tushare_db/logging_setup.py](src/tushare_db/logging_setup.py) — `setup_logging()` + `structlog.get_logger()`
  - [src/tushare_db/cli.py:39](src/tushare_db/cli.py:39) — `_get_ch_native()` 模式（CH_HOST/CH_PIPELINE_PASSWORD env）
- DDL 是**运行时 Python 推断**生成（[src/tushare_db/schema/ddl_builder.py:18](src/tushare_db/schema/ddl_builder.py:18)），没有 .sql 文件
- 引擎统一 `ReplacingMergeTree(_version)`，`_version UInt64`，时序表 `PARTITION BY toYYYYMM(trade_date)`
- 包管理：uv，Python ≥ 3.11；已装 clickhouse-connect、pandas、pyarrow、click、structlog、tenacity；**需新增 psycopg[binary]**
- 测试：pytest（unit/integration/e2e），integration 用 testcontainers[clickhouse]

### tushare-hub 侧（源）
- 配置：`src/config.py` + `.env`（POSTGRES_HOST/PORT/USER/PASSWORD/DB），驱动 psycopg2 + SQLAlchemy
- 表注册表：`src/models/__init__.py`（47 张）
- DDL：`init/001-system-tables.sql` ~ `init/010-*.sql`
- 分区表（RANGE by trade_date 2019–2027，命名 `tushare_stock_daily_2020`）：
  - tushare_stock_daily（含 _2020.._2027 + _default）
  - tushare_stock_weekly（同上）
  - tushare_adj_factor（同上）
  - 备注：需求文档第 22 行的"adj_factor 6,000 行"看起来与"多次分区"矛盾，执行文档里要让 AI 抽样确认实际行数后再决定批次
- 所有表都有 `created_at`/`updated_at TIMESTAMP`，迁移时需过滤。`_version` 用 Python 从 updated_at/created_at 转 ms 时间戳（详见 §8）

## 我将写的执行文档结构

输出文件：`F:\AIcoding_space\VsCode\tushare_db\docs\migration\EXECUTION_PLAN.md`（注意当前在 worktree，写到 worktree 路径下的同名文件）

文档目录大纲（中文，与源文档一致），每节预期内容：

### 0. TL;DR + 执行流程图
一页之内能看完的高层流程：环境检查 → 建缺表 → 字段对账 → P0 dry-run → P0 实跑 → 校验 → P1..P3 → OPTIMIZE FINAL → 验收。给执行 AI 一个"先看这里"的入口。

### 1. 前置条件与环境准备
- PG / CH 连通性自检命令（不修改任何东西）
- 依赖：`uv add psycopg[binary]`（或 psycopg2-binary，给出取舍：psycopg3 已支持 server-side cursor 且与现有依赖不冲突，推荐 psycopg3）
- env 变量清单（PG_* 新增、CH_* 复用现有）
- 磁盘评估：CH 数据目录预估增量（按 PG 全量 ~30-50 GB 估算压缩后 ~10-15 GB）
- ⚠️ 强调：**CH 当前为空表，无需备份；PG 全程只读，不要写任何东西回 PG**

### 2. 项目结构与目录骨架
列出待新建的文件树：
```
scripts/
  migrate.py                       # click 入口
src/tushare_db/migration/
  __init__.py
  registry.py                      # 加载 config/migration/tables.yaml
  pg_reader.py                     # psycopg server-side cursor + 分区合并
  type_mapper.py                   # PG type → CH type 转换函数
  field_resolver.py                # PG/CH 字段交集、列名对齐、列重命名
  version_calc.py                  # _version 推算（updated_at→created_at→now）
  writer.py                        # 包装 insert_rows()，加 batch 重试（不用 insert_with_version，因为要保留 PG 的 timestamp 作 _version）
  validator.py                     # 行数 + 抽样 + 聚合校验
  state.py                         # _meta.migration_state 表读写（断点续传）
  sync_state_writer.py             # 迁移完成后写 sync_state，防止 pipeline 重拉全量
config/migration/
  tables.yaml                      # 迁移表配置（PG 注册表 + 对账发现的匹配表）
tests/unit/test_migration_*.py
tests/integration/test_migration_e2e.py
docs/migration/
  EXECUTION_PLAN.md                # 本文档
  field_diff_report.md             # 由 AI 在执行中生成
  amount_conversion_report.md      # 由 AI 在执行中生成（§7）
  migration_log.md                 # 由 AI 在执行中生成
```
对每个新建模块给出**关键函数签名**和**职责一句话描述**。

#### 补充：建缺表方案

§12 预备阶段需要建 19 张 CH 缺表（PG 有但 CH 没有 DDL 的表）。执行方式：

```
CH 缺表检测: SELECT name FROM system.tables WHERE database='tushare' → 对比 tables.yaml → 缺表清单
```

对每张缺表：
1. 调一次 Tushare API 采样（10 行，用现有 `tushare_client.call()`）
2. 用现有 `schema/inferer.py` 推断类型
3. 用现有 `schema/ddl_builder.py` 生成 `CREATE TABLE ... ENGINE = ReplacingMergeTree(_version) ORDER BY ...`
4. 对 `trade_date` / `cal_date` / `end_date` 等日期字段补 `PARTITION BY toYYYYMM(date_col)`

**注意**：如果不想调 API（如 token 积分不足），可从 PG 的 model 定义（`src/models/*.py`）手动推导字段类型，手写 DDL。

如果缺表数量太多（>20 张），建议考虑写一个 `scripts/migrate_schemas.py`：读 PG `information_schema.columns` → 映射为 CH 类型 → 生成 DDL 并执行。

### 3. 配置驱动设计：tables.yaml 格式
给出完整 schema：
```yaml
- pg_table: tushare_stock_daily
  ch_table: tushare_stock_daily
  ch_database: tushare
  priority: P0
  partitioned: true
  partition_pattern: "tushare_stock_daily_{year}"
  partition_years: [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
  include_default_partition: true
  date_column: trade_date
  batch_size: 100000
  expected_rows: 7327237      # 来自需求文档，做 sanity check
  field_overrides:            # 可选：处理列名不一致
    pg_only_drop: [some_pg_field]
  column_renames:             # 可选：PG 列名 → CH 列名映射
    end_date: cal_date
    index_code: ts_code
  notes: "多年份分区，跨年数据可能在多个分区写入相同行（去重靠 _version）"
```
然后给一段 Python pseudocode：如何用 pydantic 模型加载并校验。

### 4. 迁移表清单（生成出完整 YAML 内容）
直接在文档里把所有迁移表的 YAML 条目列全。对照需求文档 §2.1 的分类逐一列出，每条带 priority、partitioned、expected_rows。执行 AI 需以 PG models/__init__.py 注册表为起点，再补充对账发现的额外匹配表。这部分让执行 AI 拷贝即用，不用自己再梳理表清单。

### 5. PG 读取实现规范
- **server-side cursor**：psycopg3 `with conn.cursor(name='migrate_cur') as cur` + `itersize=batch_size`
- **分区表合并策略**：不要 UNION ALL（OOM 风险），改为**逐分区顺序读** + **按 ts_code 排序**让 CH 在同一 partition 落盘
- **分区重复预检（⚠️ 必须做）**：跨分区表（如 stock_daily_2025 + stock_daily_default）可能存在 `(ts_code, trade_date)` 重复行（如 2025-12-31 同时在两个分区）。迁移前执行：
  ```sql
  -- 对每个分区表的 _default 分区检查
  SELECT ts_code, trade_date, COUNT(*) AS dup
  FROM tushare_stock_daily_default
  GROUP BY 1,2 HAVING COUNT(*) > 1;
  ```
  如有重复行，及时告知用户。两条记录的 `updated_at` 可能相同（同一次采集写入），ReplacingMergeTree 无法保证保留哪条。
- **空表处理**：`SELECT 1 FROM t LIMIT 1` 先探测，0 行直接 skip 并写 state
- **NULL 透传**：psycopg3 默认 None；CH 列若为 Nullable 直接写
- 给出关键函数签名：
  ```python
  def iter_pg_rows(
      conn, table: str, columns: list[str],
      batch_size: int, where: str | None = None
  ) -> Iterator[list[tuple]]: ...
  ```

### 6. 字段类型映射与列对齐
- **完整类型映射表**（扩展需求文档 §3.1）：
  | PG 类型 | CH 类型 | 转换函数 | 备注 |
  | VARCHAR | String / LowCardinality(String) | str | ts_code/symbol/name 用 LowCardinality |
  | BIGINT | Int64 | int | |
  | INTEGER | Int32 | int | |
  | NUMERIC(p,s) | Float64 | 直接 float | 金额字段 ×10000 后可能溢出 Decimal64(2)，优先用 Float64。如果 CH DDL 已为某些表使用 Decimal64(2)，须确认该表的金额值不会超 9.22×10¹⁶ |
  | DATE | Date | date | |
  | TIMESTAMP | — | 用于 _version 计算 | |
  | BOOLEAN | UInt8 | int(bool) | |
  | TEXT | String | str | |
  | JSONB | String | json.dumps | 仅极少数表 |
- **列对齐函数**（含重命名）：
  ```python
  def resolve_columns(
      pg_cols: list[str], ch_cols: list[str], renames: dict
  ) -> tuple[list[str], list[str]]:
      """
      返回 (PG 查询的列名, CH 写入的列名)。
      步骤：1) 过滤 created_at/updated_at；2) PG 列按 renames 映射；3) 与 CH 列取交集。
      created_at 和 updated_at 必须强制丢弃，不参与对齐。
      """
  ```
  注意：第 163 行是精简签名，§6 后半段有完整实现。
- **列重命名**（⚠️ 仅匹配同名交集不够，以下表列名不一致，必须显式映射）：

  | PG 列 | CH 列 | 涉及表 |
  |---|---|---|
  | `end_date` | `cal_date` | tushare_fund_nav |
  | `index_code` | `ts_code` | tushare_index_weight |
  | `con_code` | 无对应，丢弃 | tushare_index_weight |
  | `call_date` | `trade_date` | tushare_cb_call |

  tables.yaml 加 `column_renames` 字段：
  ```yaml
  column_renames:
    end_date: cal_date
    index_code: ts_code
  ```

  `field_resolver.resolve_columns()` 加入列重命名步骤：
  ```python
  def resolve_columns(pg_cols, ch_cols, renames: dict) -> tuple[list[str], list[str]]:
      """
      返回 (PG 查询的列名列表, CH 写入的列名列表)。
      步骤：1) PG 列按 renames 映射；2) 过滤 created_at/updated_at；3) 与 CH 列取交集。
      """
      # 1. 先过滤 created_at / updated_at（CH 不需要）
      pg_clean = [c for c in pg_cols if c not in ('created_at', 'updated_at')]
      # 2. 按 renames 映射后与 CH 列取交集
      ch_cols_set = set(ch_cols)
      pg_in = [c for c in pg_clean if renames.get(c, c) in ch_cols_set]
      ch_in = [c for c in ch_cols if c in {renames.get(x, x) for x in pg_in}]
      return pg_in, ch_in
  ```
  注意：`created_at` 和 `updated_at` 必须强制过滤，不参与对齐。
- **字段对账**：第一次跑前生成 `field_diff_report.md`，按表列出 `pg_only` / `ch_only` / `both` 三栏

### 7. 金额与份额单位转换（⚠️ 致命坑，遗漏则回测数据全错）

**背景**：tushare-db 的 `schema/type_map.py` 在写入 API 数据时，会自动把 Tushare 原始值（万元/万份）转为元/份。但迁移 PG 数据时绕过了这个逻辑，必须手动在 ETL 中完成转换。

**核心规则**：PG 存的是**原始值（万元/万份）**，CH 预期存储**转换后的值（元/份）**。

**哪些字段需要转换**（参考 [src/tushare_db/schema/type_map.py](src/tushare_db/schema/type_map.py) 中的 `NORMALIZE_FIELDS` 逻辑）：

| 字段模式 | 原始单位 | 目标单位 | 乘数 | 涉及表举例 |
|---------|---------|---------|------|-----------|
| `*_amount` | 万元 | 元 | ×10,000 | moneyflow（buy_elg_amount 等） |
| `*_revenue`, `*_profit`, `*_cost`, `*_income`, `*_expense` | 万元 | 元 | ×10,000 | income（total_revenue, oper_revenue 等） |
| `*_asset`, `*_liability`, `*_equity` | 万元 | 元 | ×10,000 | balancesheet（total_assets, total_liab 等） |
| `total_*`（白名单内的） | 万元 | 元 | ×10,000 | cashflow, fina_indicator 等 |
| `*_mv`, `circ_mv`, `total_mv`, `float_mv` | 万元 | 元 | ×10,000 | daily_basic, stock_basic |
| `*_share`（基金类） | 万份 | 份 | ×10,000 | fund_portfolio, fund_share |
| `*_vol`（资金流向类） | 股 | 股 | **×1（不转换）** | moneyflow |
| `*_price`, `*_rate`, `*_pct`, `*_ratio` | 原始 | 原始 | **×1（不转换）** | 所有表 |

**实现方式**（写入 `field_resolver.py`）：

```python
# 万元/万份 → 元/份的归一化字段模式
NORMALIZE_X10000_PATTERNS: list[str] = [
    "amount",      # *_amount: 所有成交额类
    "revenue",     # total_revenue, oper_revenue, revenue 等
    "profit",      # net_profit, oper_profit, total_profit 等
    "income",      # net_income, total_income, op_income 等
    "cost",        # total_cost, op_cost 等
    "expense",     # admin_expense, sell_expense, fin_expense 等
    "asset",       # total_assets, current_assets, non_current_assets 等
    "liability",   # total_liab, current_liab, non_current_liab 等
    "equity",      # total_equity, total_hldr_eqy_exc_min_int 等
    "mv",          # total_mv, circ_mv, float_mv
    "capital",     # reg_capital, paid_capital
    "surplus",     # cap_rese, surplus_rese, undist_profit
    "tax",         # income_tax
    "ebit",        # ebit, ebitda
    "fcff",        # fcff, fcfe
    "interest",    # interest
    "debt",        # net_debt, lt_debt, st_debt
    "dividend",    # div as dividend
    "share",       # 基金份额：fund_portfolio.*_share, fund_share.*_share
]

def should_normalize(column_name: str, table_name: str) -> bool:
    """
    判断一个列是否需要 ×10,000 单位转换。
    
    排除规则（即使模式匹配也不转换）：
    - 以 _pct, _rate, _ratio, _price, _cost_ratio 结尾的比率/单价字段
    - vol, *_vol：成交量（股），不转换
    - *_yoy, *_qoq：同比/环比比率，不转换
    - *_days：天数，不转换
    - *_tax_rate：税率百分比，不转换
    """
    _exclude_suffixes = (
        "_pct", "_rate", "_ratio", "_price", "_days",
        "_yoy", "_qoq", "_cost_ratio", "_tax_rate",
        "vol",          # 排除 vol 和 *_vol（成交量）
    )
    if column_name.endswith(_exclude_suffixes):
        return False
    for pat in NORMALIZE_X10000_PATTERNS:
        if pat in column_name:
            return True
    return False

def normalize_value(column_name: str, value, table_name: str) -> Any:
    """对单个字段值应用单位转换。"""
    if value is None:
        return None
    if not should_normalize(column_name, table_name):
        return value
    if isinstance(value, (int, float, Decimal)):
        return value * 10_000
    return value  # 非数值类型直接原样返回
```

**执行要求**（写入 EXECUTION_PLAN.md）：

1. 在 `field_resolver.py` 中实现上述 `should_normalize()` + `normalize_value()`
2. 迁移过程中对每一行的每个数值列调用 `normalize_value(col, val, table)`
3. 第一次跑前，生成一份 `amount_conversion_report.md`，逐表列出哪些列被标记为"需要 ×10000"，让用户人工确认后再实跑
4. 校验阶段（§11），聚合对账用公式：`CH.SUM(amount_col) ≈ PG.SUM(amount_col) × 10000`，偏差容差 < 0.01%

### 8. _version 计算规则
对应需求文档 §3.2，给出明确实现：
```python
def calc_version(row: dict) -> int:
    for col in ('updated_at', 'created_at'):
        v = row.get(col)
        if v is not None:
            return int(v.timestamp() * 1000)
    return int(time.time() * 1000)
```
**坑点提示**：PG 的 TIMESTAMP 默认无时区，psycopg3 返回 naive datetime。需要：

1. **先验证时区假设**：抽样 10 条 `updated_at` 值，看绝对值是否与数据的 trade_date 接近（如 trade_date = '2024-06-01'，updated_at 应接近 '2024-06-01 xx:xx:xx'，而非 '2024-05-31 16:xx:xx'）。确认 PG 存的是中国时间而非 UTC。
2. 确认后用 `dt.replace(tzinfo=ZoneInfo('Asia/Shanghai')).timestamp() * 1000` 转 ms。

### 9. 写入实现规范
- **不用 `insert_with_version()`** — 它会**强制覆盖** `_version` 为当前时间戳，不符合本场景（要保留 PG 的 updated_at 时间戳作 version）。**必须直连 `insert_rows()`**，自己管理 `_version` 列。注意：`insert_rows()` 不自动添加 `_version`，传入的每一行必须自行携带 `_version` 字段。
- batch 的列顺序必须与 `resolve_columns()` 返回的 CH 列名严格对应，最后一列是 `_version`
- batch 失败重试用现成的 tenacity（`@retry(stop=stop_after_attempt(3), wait=wait_exponential())`）
- 每批写入后 log: `table={t} batch={i} rows={n} cumulative={c}`

### 10. 断点续传与状态表
建议在 CH 内建一张 `_meta.migration_state`：
```sql
CREATE TABLE _meta.migration_state (
  pg_table String,
  status Enum8('pending'=0,'running'=1,'done'=2,'failed'=3),
  rows_migrated UInt64,
  pg_row_count UInt64,
  started_at DateTime,
  finished_at Nullable(DateTime),
  error_msg Nullable(String),
  _version UInt64
) ENGINE = ReplacingMergeTree(_version) ORDER BY pg_table
```
执行流程：每张表开始前查 state；done 跳过；running/failed 走重试逻辑。

### 11. 校验方案
三层校验，全部跑完才能算"done"：
1. **行数**：`SELECT count() FROM ch.t FINAL` vs `SELECT count(*) FROM pg.t`，允许差异 0
2. **抽样对账**：`ts_code, trade_date` 主键随机抽 1000 行，按列名匹配逐字段比对（容差：Float64 精度截断后比较）
3. **聚合一致性**：核心数值列 `sum / min / max / count(distinct ts_code)` 对账。金额/份额列须按 §7 规则校验：`CH.SUM(col) ≈ PG.SUM(col) × 10000`，偏差 < 0.01%
- 给出 `validator.py` 三个函数签名

### 12. 执行流程（按优先级分批）
对应需求文档 §6。每个阶段一个 checklist：

- **预备**：补建 §2 中 19 张 CH 缺表（用 `schema/inferer.py` 采样建表或手写 DDL）
- **停机**（⚠️ 必须做）：停止 tushare-hub 的 scheduler（`docker stop <hub_container>` 或 `docker-compose stop scheduler`），确保迁移期间 PG 不再有新写入
- **字段对账**：跑一次 dry-run（不写数据），生成 `field_diff_report.md` + `amount_conversion_report.md`
- **人工确认**：用户 review 两个报告，确认字段映射和金额转换规则后，标记 `--confirm` 允许实跑
- **P0 阶段**（8 张核心表）：先跑 stock_basic / trade_cal 这种小表试通路 → 再 stock_daily 大表 → 全量校验 → OPTIMIZE TABLE FINAL
- **P1 / P2 / P3** 同模板
- **收尾**（⚠️ 必须做，防止 pipeline 重拉全量）：
  1. 统一 OPTIMIZE FINAL（仅数据表，非 _meta 表）
  2. 写 `migration_log.md`，含每张表的最终行数、耗时、校验结果
  3. **写 `_meta.sync_state` 记录**：为每张迁移完成的表，插入对应 status='done'、最后交易日期的记录，防止 pipeline 启动后认为从未同步、从头拉全量。具体字段：
     ```
     interface = <表名>
     scope_key = "all"     # 或 "historical"
     status = "done"
     rows = <CH 实际行数>
     last_success_at = NOW()
     ```
  4. 写 `_meta.migration_state` 标记所有表为 'done'
  5. 确认 pipeline-scheduler 启动后能正常增量

### 13. 风险清单与应对（扩展需求文档 §5）
在原表基础上新增几条容易踩的：
| 风险 | 等级 | 应对 |
|---|---|---|
| **金额单位未转换**（万元→元） | **致命** | 见 §7，必须对所有匹配模式的数值列 ×10000；跑前必须产 `amount_conversion_report.md` 人工确认；校验阶段聚合 SUM 按 ×10000 比例对比 |
| **跨年数据重复**（stock_daily 2025-12-31 在 _2025 和 _default 都有？） | **高** | §5 分区重复预检已强制检查。如有重复且 updated_at 相同，去重结果不确定。用户确认后决定是否保留一条或全部迁移靠 _version 去重 |
| **PG TIMESTAMP 时区** | 中 | 统一假设服务器本地时区（中国），§8 抽样验证可提前排除 |
| **DECIMAL 精度截断** | 中 | 在 `field_diff_report.md` 里明确列出哪些列发生了 18,3→18,2 截断；用 Float64 方案则免疫 |
| **clickhouse-connect HTTP 大批量超时** | 低 | batch_size ≤ 100k，超时 60s，重试 3 次 |
| **网络中断导致部分写入** | 低 | _version + ReplacingMergeTree 天然幂等，重跑同 batch 不会出错 |
| **OPTIMIZE 阻塞读** | 低 | 在迁移完成后单独时间窗口跑，不要每张表都跑 |
| **迁移后 pipeline 重拉全量** | **高** | 收尾阶段必须写 `_meta.sync_state` 记录。否则 pipeline 看到 sync_state 为空，会从最早日期开始全量重拉，浪费 API 积分和时间 |
| **stock_daily 730 万行内存** | 低 | server-side cursor + 100k batch；内存峰值 < 500MB |
| **PG 在迁移期间仍在写入** | **高** | 如果 tushare-hub 的 scheduler 还在跑，迁移过程中 PG 可能写入新数据。迁移完成后，这些新数据不会同步到 CH。**应对**：迁移前停止 tushare-hub scheduler，迁移完成并写入 sync_state 后再启动 tushare-db scheduler。或者接受一个短暂的"数据窗口差"，由增量同步补足 |
| **PG DATE 导出格式** | 中 | psycopg3 读 DATE 列返回 `datetime.date` 对象。ClickHouse `clickhouse_connect` 能接受 Python `date` 对象自动转 'YYYY-MM-DD'，无需额外转换。但建议在执行文档中明确验证这一点 |
| **Decimal64(2) 溢出风险** | 中 | 金额字段 ×10000 后，原 DECIMAL(18,4) 的 18 位整数变成 22 位，可能超出 Decimal64(2) 的范围（Decimal64(2) 最大 ~9.22×10¹⁶）。需检查 CH 中相关表是否用了 Float64（不受精度限制）或 Decimal256 替代。如果已经用了 Float64 则无此问题。§6 的类型映射表须改为"**优先 Float64，不用 Decimal64(2)**"以规避溢出 |
| **_meta.sync_state 表结构匹配** | 低 | CH 的 `_meta.sync_state` 是 ReplacingMergeTree(_version)，写入时需携带 `_version`。执行文档须明确 sync_state_writer.py 用 `insert_with_version()` 或自行管理 _version |

### 14. 测试要求
- 单测：type_mapper、field_resolver、version_calc 必须 ≥ 80% 覆盖（项目规则要求）
- 集成测：用 testcontainers 起一个临时 CH，跑 stock_basic 全量（71k 行），验证三层校验通过
- 不要为所有表都写测试——配置驱动的好处是测一个就等于测全部

### 15. 执行 Checklist（最终验收）
让 AI 跑完逐项打钩：
- [ ] `.env` 已加 PG_* 变量，连通性测试通过
- [ ] 19 张 CH 缺表已建好
- [ ] tushare-hub scheduler 已停止，迁移期间 PG 不再写入
- [ ] `amount_conversion_report.md` 已生成，所有 ×10000 列已人工确认
- [ ] `field_diff_report.md` 已生成并 review
- [ ] P0 8 张表全部 done，三层校验全过
- [ ] P1/P2/P3 同上
- [ ] OPTIMIZE TABLE FINAL 已对所有迁移表执行
- [ ] `migration_log.md` 含每张表的最终行数、耗时、校验结果
- [ ] tushare-db pipeline scheduler 启动后能正常增量（不重复迁移历史数据）

### 16. 不在本次范围内（明确边界）
- 增量同步逻辑的修改：迁移完成后由 pipeline-scheduler 接管，但迁移脚本需写入 sync_state 记录（见 §12 收尾步骤，**这是本次范围内**）
- 停止/重启 tushare-hub scheduler：这是用户的运维操作，迁移脚本不处理（但需在 §12 明确告知用户）
- 港股 / 美股 / 分钟行情 / 新闻类付费接口（需求文档 §2.2 已排除）
- pipeline-scheduler 的修改

---

## 验证方式

写完文档后：
1. `Read` 一遍 EXECUTION_PLAN.md 自检结构完整、能从头读到尾
2. 对照需求文档 §2-§7 七节，确认每节都在执行文档里有覆盖且有更具体的落地方案
3. 关键路径（PG 连接 / CH writer / 迁移表 YAML）要给到执行 AI 可以直接拷贝/调用的最小信息量
4. 不实际跑代码，也不实际建表——本次任务的产出物**只有这一份 markdown**

---

## 执行中可能遇到的问题（待解决清单）

> 以下为编写 EXECUTION_PLAN.md 的执行 AI 需关注并给出明确方案的遗留问题，**执行前必须全部闭环**。

### E1. psycopg3 与现有 psycopg2 冲突

tushare-hub 依赖 `psycopg2-binary`，而本文档推荐 psycopg3。两个包的 import 名称不同（`import psycopg2` vs `import psycopg`），可以共存，但需注意：

- **建议方案**：在 `pyproject.toml` 中声明 `psycopg[binary]>=3.1`（与 psycopg2 不冲突）
- **风险**：如果执行环境已用 `pip install psycopg2` 覆盖了，可能互相干扰
- **要求**：EXECUTION_PLAN.md 中明确安装和验证步骤，不修改 tushare-hub 的依赖

### E2. PG 连接 `.env` 路径不明确

文档说"PG_* 新增"，但 PG 配置来自 tushare-hub 项目（`F:\AIcoding_space\projects\tushare-hub\.env`）。tushare_db 项目自身的 `.env` 也可能需要加 PG 变量。

- **建议方案**：EXECUTION_PLAN.md 明确：在 tushare_db 的 `.env` 中新增 `PG_HOST`/`PG_PORT`/`PG_USER`/`PG_PASSWORD`/`PG_DB`，值从 tushare-hub 的 `.env` 复制。不修改 tushare-hub 的任何文件
- **环境变量名**：统一用 `PG_*` 前缀（与 `CH_*` 保持一致），避免与 tushare-hub 的 `POSTGRES_*` 混淆

### E3. 建缺表时采样 API 来源不明确

文档说"调一次 Tushare API 采样（10 行，用现有 `tushare_client.call()`）"，但 tushare_db 的客户端在 `src/tushare_db/core/tushare_client.py`，而 tushare-hub 的客户端在 `F:\AIcoding_space\projects\tushare-hub\src\tushare_client.py`，两者 API 不同。

- **建议方案**：明确使用 **tushare_db 的** `src/tushare_db/core/tushare_client.py`（需要 `TUSHARE_TOKEN` env），采样目的是拿 10 行示例数据供 `schema/inferer.py` 推断类型
- **备选方案**：如果不想调 API（token 积分不足），改从 PG `information_schema.columns` 直接获取列名+类型，映射为 CH DDL

### E4. `tushare_client.py` 的路径引用可能误导

§2 复用点列了多个文件路径，但有些是 tushare-db 侧的，有些是 tushare-hub 侧的。执行 AI 可能混淆哪个项目的代码可以复用。

- **建议方案**：EXECUTION_PLAN.md 中明确"复用点"全部指 **tushare_db 项目**（`F:\AIcoding_space\VsCode\tushare_db\`）下的文件，不引用 tushare-hub 的代码

### E5. 校验方案的跨库对比怎么做

§11 说 `SELECT count() FROM ch.t FINAL` vs `SELECT count(*) FROM pg.t`。但 PG 和 CH 的 count 在不同数据库、不同连接里，怎么"对比"？

- **建议方案**：`validator.py` 的校验函数同时接收 PG connection 和 CH client，分别执行查询，在 Python 内存中对比结果
- **抽样对账**需要：PG `WHERE ts_code=xxx AND trade_date=xxx LIMIT 1` 与 CH `WHERE ts_code=xxx AND trade_date=xxx` 分别拉一行，逐字段比对

### E6. `_meta.sync_state` 的具体表结构未给出

§12 收尾阶段要求写 sync_state，但文档只给了几个字段名，没有完整的 `INSERT INTO ...` 语句或表 DDL。

- **建议方案**：EXECUTION_PLAN.md 中给出 `_meta.sync_state` 的完整 DDL（如果不存在的话）或确认现有表结构。`sync_state_writer.py` 须明确写入的完整列列表和类型

### E7. `insert_rows()` 的列顺序与 dataclass/dict 映射关系

§9 说"列顺序必须与 resolve_columns 返回的 CH 列名严格对应"。`clickhouse_connect` 的 `insert_rows()` 支持按列名自动对齐（`column_names` 参数），还是需要手动排序成 tuple？

- **建议方案**：查阅现有 `sink/clickhouse_sink.py` 中 `insert_rows()` 的签名，确认其接受的参数形式（list of dict vs list of tuple），并明确 `writer.py` 的调用方式

### E8. PG 分区表数量可能不止 3 张

§tushare-hub 侧 第 34-37 行只列了 3 张分区表（stock_daily, stock_weekly, adj_factor）。但实际可能存在更多。

- **建议方案**：EXECUTION_PLAN.md 要求在"预备"阶段执行 `SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'tushare_%' AND table_name LIKE '%_20%'` 探测所有分区子表，而不是硬编码 3 张

---

## ⚠️ 对项目代码结构的影响声明

**本次迁移不修改任何现有代码。** 所有变更均为新增文件或仅增配置：

| 变更类型 | 涉及文件/目录 | 影响 |
|---------|-------------|------|
| **新增** | `scripts/migrate.py` | CLI 入口，独立运行 |
| **新增** | `src/tushare_db/migration/` | 全新模块，与 runner/planner/schema/meta 无耦合 |
| **新增** | `config/migration/tables.yaml` | 迁移配置，与 `config/interfaces/*.yaml` 并列独立 |
| **新增** | `tests/unit/test_migration_*.py` | 新增测试，不影响现有测试 |
| **修改** | `pyproject.toml` | 仅新增 `psycopg[binary]>=3.1` 依赖 |
| **修改** | `.env` | 仅新增 `PG_*` 环境变量 |

**不碰的部分**：pipeline scheduler、MCP server、`config/interfaces/*.yaml`、`runner/`、`planner/`、`meta/`、ClickHouse 现有表结构。

迁移完成后，如不再需要，整个 `src/tushare_db/migration/` 和 `config/migration/` 可安全删除，对主项目零残留。

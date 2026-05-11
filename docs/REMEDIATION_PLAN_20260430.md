# 修复方案 — 2026-04-30（交接给 AI 执行）

> 本文档基于 [DATABASE_STATUS_20260430.md](DATABASE_STATUS_20260430.md) 与 [ROOT_CAUSE_ANALYSIS_20260430.md](ROOT_CAUSE_ANALYSIS_20260430.md)。
> 阅读对象：另一个独立 AI（无本仓库上下文）。所有命令、文件路径、行号、SQL、补丁均给到可直接执行的粒度。
> 工作目录基准：`F:/AIcoding_space/VsCode/tushare_db`（容器内对应 `/app`）。

---

## 0. 执行前置条件 / 环境约定

1. **Shell**：Windows + Git Bash。所有命令使用 Unix 语法。`docker`/`docker compose` 均可用。
2. **必需环境变量**（`.env` 已存在；如缺失从 `.env.example` 拷贝）：`TUSHARE_TOKEN`、`CH_HOST`、`CH_PIPELINE_PASSWORD`、`CH_AI_READER_PASSWORD`。
3. **数据库连接**（容器外）：HTTP 端口 `8123`，用户 `pipeline`（写）/ `ai_reader`（读），数据库 `tushare`、`_meta`。
4. **容器内代码路径**：`/app/src/tushare_db/...`。本地路径：`src/tushare_db/...`。
5. **关键事实**：scheduler 容器内运行的是**旧镜像**，本地 `src/` 已包含新代码（per_symbol、_normalize_items 完整逻辑等）。**P0 之一就是重建镜像**。
6. **修复顺序**：`P0 → P1 → P2 → P3`。每个 P0 步骤完成后，必须执行 §11 的「验证步骤」确认问题不会回归。
7. **禁止**：
   - 不要 `--no-verify` 提交；
   - 不要 `git push --force`；
   - 改 ClickHouse schema 前先 `BACKUP TABLE` 或确认数据可重新拉取；
   - 不要在 `_meta.sync_state` 上用 `DELETE`，改用 `ALTER TABLE _meta.sync_state UPDATE` 或写入新 row（这是 ReplacingMergeTree(`_version`)）。

---

## 1. P0-A：补齐 `moneyflow_*` 三张表的缺失列（解决 1,213 个失败）

### 1.1 背景
- 上游 Tushare 返回了表中不存在的列，写入抛 `Unrecognized column ...`。
- 三个接口在 `config/interfaces/stock_moneyflow.yaml` 中已 `enabled: false`，需要先补 schema，再开启 backfill。
- 本仓库现有的 `evolve_schema()`（[src/tushare_db/schema/evolver.py:44](../src/tushare_db/schema/evolver.py)）功能正确，但 worker 异常路径（[src/tushare_db/runner/worker.py:370-373](../src/tushare_db/runner/worker.py)）没接线，所以历史失败堆积。本次先用手工 DDL 修，并在 P0-D 接线自动演进。

### 1.2 SQL 变更（对 ClickHouse 直接执行）

任选其一：
- 容器内：`docker compose exec clickhouse clickhouse-client --user pipeline --password "$CH_PIPELINE_PASSWORD" --multiquery --query "<SQL>"`
- 本机：`curl -u pipeline:$CH_PIPELINE_PASSWORD 'http://localhost:8123/?database=tushare' --data-binary "<SQL>"`

```sql
ALTER TABLE tushare.tushare_moneyflow_ths
  ADD COLUMN IF NOT EXISTS name LowCardinality(String) AFTER ts_code;

ALTER TABLE tushare.tushare_moneyflow_cnt_ths
  ADD COLUMN IF NOT EXISTS lead_stock LowCardinality(String) AFTER ts_code;

ALTER TABLE tushare.tushare_moneyflow_ind_ths
  ADD COLUMN IF NOT EXISTS industry LowCardinality(String) AFTER ts_code;
```

> 类型选 `LowCardinality(String)`，因为这些是中等基数的中文名（同板块下高度重复）。如不确定基数，用 `String`。

### 1.3 配置变更：开启接口

文件：`config/interfaces/stock_moneyflow.yaml`

将 `name: moneyflow_ths` / `moneyflow_cnt_ths` / `moneyflow_ind_ths` 三段中：
```yaml
enabled: false   # → 改为
enabled: true
```

### 1.4 重置失败 scope，触发 resume

ClickHouse 端：把 `_meta.sync_state` 中这三个接口的 `failed` 改为 `pending`，让 resume 重跑。

```sql
ALTER TABLE _meta.sync_state
UPDATE status = 'pending', last_error = '', _version = toUInt64(now64(3))
WHERE interface IN ('moneyflow_ths', 'moneyflow_cnt_ths', 'moneyflow_ind_ths')
  AND status = 'failed';
```

> 等待 mutation 完成：`SELECT * FROM system.mutations WHERE is_done = 0 FORMAT Vertical;`

### 1.5 触发回填

```bash
docker compose exec pipeline-scheduler tushare-db resume
# 或者一次跑指定接口（如有 CLI 支持）
# tushare-db backfill --interface moneyflow_ths
```

### 1.6 验证

```sql
SELECT interface, count() AS n
FROM _meta.sync_state FINAL
WHERE interface IN ('moneyflow_ths','moneyflow_cnt_ths','moneyflow_ind_ths')
GROUP BY interface, status WITH TOTALS;

SELECT count(), uniqExact(ts_code), min(trade_date), max(trade_date)
FROM tushare.tushare_moneyflow_ths;
```

期望：`failed` 计数趋于 0；表行数从 1 上升至与历史交易日 × 标的数相符的量级。

---

## 2. P0-B：重建 scheduler / mcp 镜像（解决 587 + 2 + 2 = 591 个失败）

### 2.1 背景
容器跑的是旧版 `planner.py`（无 `per_symbol` 分支）和旧版 `_normalize_items`（日期/Nullable 处理不全）。本地 `src/` 已修复，重新打镜像即可吸收。

### 2.2 重建并重启

```bash
# 在仓库根目录执行
docker compose build --no-cache pipeline-scheduler pipeline-mcp
docker compose up -d --force-recreate pipeline-scheduler pipeline-mcp
docker compose logs -f --tail=200 pipeline-scheduler
```

### 2.3 容器内代码核验（务必执行）

```bash
docker compose exec pipeline-scheduler python -c "
import inspect, tushare_db.planner.planner as p, tushare_db.runner.worker as w
src_p = inspect.getsource(p.plan_units)
src_w = inspect.getsource(w._normalize_items)
assert 'per_symbol' in src_p and 'per_symbol_period' in src_p, 'planner missing per_symbol branch'
assert '_EPOCH_DATE' in src_w, 'worker missing epoch fallback'
assert 'datetime_type_indices' in src_w, 'worker missing DateTime separation'
print('OK')
"
```

输出必须为 `OK`，否则镜像没重建成功（检查 `.dockerignore` / build cache）。

### 2.4 重置因 `Unknown strategy: per_symbol` 失败的 scope

```sql
ALTER TABLE _meta.sync_state
UPDATE status = 'pending', last_error = '', _version = toUInt64(now64(3))
WHERE status = 'failed'
  AND (last_error LIKE '%Unknown strategy: per_symbol%' OR last_error = '')
  AND interface = 'fina_audit';
```

> 注：`last_error = ''` 的空错误记录就是这一类，需要一并放回 pending。

### 2.5 修 `_schema.yaml` 枚举（一致性 / 防回归）

文件：`config/interfaces/_schema.yaml` 第 12 行：

```yaml
# 改前
kind: full_once|date_loop|period_loop|monthly_window|per_symbol_period|offset_paging
# 改后
kind: full_once|date_loop|period_loop|monthly_window|per_symbol|per_symbol_period|offset_paging
```

### 2.6 验证

```bash
# 跑一个最小 fina_audit scope 看是否走 per_symbol_period 路径
docker compose exec pipeline-scheduler tushare-db resume --dry-run | head -50
docker compose exec pipeline-scheduler tushare-db resume
# 等 ~10 分钟后：
```
```sql
SELECT status, count() FROM _meta.sync_state FINAL
WHERE interface = 'fina_audit' GROUP BY status;
```
期望 `failed` 显著下降，`done` 上升。

---

## 3. P0-C：修复 `etf_index.pub_date` / `index_basic.base_date` Nullable 问题（解决 2 个失败）

### 3.1 背景
非 Nullable 的 `Date` 列收到 None 触发 `Unable to create Python array`。由于这些字段在业务上确实可能缺失，**正确解法是改成 `Nullable(Date)`**，而不是默认填 1970-01-01。

### 3.2 SQL 变更

```sql
-- etf_index.pub_date
ALTER TABLE tushare.tushare_etf_index
  MODIFY COLUMN pub_date Nullable(Date);

-- index_basic.base_date
ALTER TABLE tushare.tushare_index_basic
  MODIFY COLUMN base_date Nullable(Date);
```

> `MODIFY COLUMN` 在 ReplacingMergeTree 上是 metadata-only 的轻量 mutation（仅当目标是同基类型 + Nullable 包装时），不会重写数据。等待：
> ```sql
> SELECT * FROM system.mutations WHERE is_done = 0 FORMAT Vertical;
> ```

### 3.3 同步配置（防止后续重建表回退）

文件：`config/interfaces/etf.yaml` 与 `config/interfaces/index.yaml`，在对应接口的 `schema_overrides` 中显式声明：

```yaml
schema_overrides:
  pub_date: Nullable(Date)
```
```yaml
schema_overrides:
  base_date: Nullable(Date)
```

> 找到对应行：
> - [config/interfaces/etf.yaml:19](../config/interfaces/etf.yaml) `name: etf_index`
> - [config/interfaces/index.yaml:67](../config/interfaces/index.yaml) `name: index_basic`

### 3.4 重置失败并 resume

```sql
ALTER TABLE _meta.sync_state
UPDATE status = 'pending', last_error = '', _version = toUInt64(now64(3))
WHERE interface IN ('etf_index','index_basic') AND status = 'failed';
```
```bash
docker compose exec pipeline-scheduler tushare-db resume
```

### 3.5 验证
```sql
SELECT count(), countIf(pub_date IS NULL) FROM tushare.tushare_etf_index;
SELECT count(), countIf(base_date IS NULL) FROM tushare.tushare_index_basic;
```
两条 `count()` 应均 > 0，无错误堆栈复发。

---

## 4. P0-D：在 `execute_unit` 中接入自动 schema 演进（防止 §1 类问题再发生）

### 4.1 目标行为
当 ClickHouse 写入抛出形如 `Code: 16. Unrecognized column 'X'` 或 `Code: 47. Missing columns: 'X'` 时：
1. 解析错误，提取列名集合；
2. 用本批 row 的样本推断列类型（`schema/type_inference.py` 已有，复用）；
3. 调 `evolve_schema()`（[src/tushare_db/schema/evolver.py:44](../src/tushare_db/schema/evolver.py)）补列；
4. 调 `invalidate_column_cache()` 失效缓存（[src/tushare_db/runner/worker.py:381](../src/tushare_db/runner/worker.py)）；
5. 重新执行一次 `_normalize_items` + `insert_with_version`；最多重试 1 次，成功则正常 `mark_done`，失败则按原异常路径 `mark_failed`。

### 4.2 文件改动

#### 4.2.1 新增：错误识别 + 列推断辅助
位置：`src/tushare_db/schema/evolver.py` 末尾。

```python
import re as _re

_UNRECOGNIZED_RE = _re.compile(r"(?:Unrecognized column|Missing columns:|There is no column with name)\s*['\"`]?([A-Za-z_][A-Za-z0-9_]*)")

def parse_missing_columns(err_msg: str) -> list[str]:
    """Extract missing column names from a ClickHouse error message.

    Handles common phrasings:
      - "Unrecognized column 'foo'"
      - "Missing columns: 'foo' 'bar'"
      - "There is no column with name 'foo'"
    """
    return list(dict.fromkeys(_UNRECOGNIZED_RE.findall(err_msg or "")))
```

#### 4.2.2 修改：`execute_unit` 异常路径加自动演进

文件：`src/tushare_db/runner/worker.py`

在 [worker.py:300-310](../src/tushare_db/runner/worker.py)（`insert_with_version` 调用处）外层加一次「missing column → evolve → 重试」分支。最小补丁草案（伪 diff，AI 落地时按实际行号调整）：

```python
# 新增 import（顶部）
from tushare_db.schema.evolver import evolve_schema, parse_missing_columns
from tushare_db.schema.type_inference import infer_column_types  # 复用现成模块；若名字不同请按实际查找

# 替换 worker.py:304-310 这段：
try:
    insert_with_version(ch_client, table=unit.table, columns=fields, rows=normalized_items)
except Exception as insert_err:
    missing = parse_missing_columns(str(insert_err))
    if not missing:
        raise
    logger.warning("Auto-evolving schema", table=unit.table, missing=missing)
    inferred = infer_column_types(fields, items)  # {name: ch_type}
    desired = [(c, inferred.get(c, "Nullable(String)")) for c in missing]
    evolve_schema(ch_client, database="tushare", table=unit.table, desired_columns=desired)
    invalidate_column_cache(database="tushare", table=unit.table)
    # 重新归一化（列集合可能变了）+ 二次写入
    column_types = _get_column_types(ch_client, unit.table)
    normalized_items = _normalize_items(fields, items, column_types=column_types)
    insert_with_version(ch_client, table=unit.table, columns=fields, rows=normalized_items)
```

> **注意**：`infer_column_types` 是否存在请先 grep 验证：
> ```bash
> ```
> 如不存在，`desired = [(c, "Nullable(String)") for c in missing]` 作为最保守 fallback（始终安全，可后续迁移类型）。

#### 4.2.3 单测（必加）

文件：`tests/runner/test_worker_schema_evolve.py`（新建）。

```python
def test_parse_missing_columns_unrecognized():
    msg = "DB::Exception: Code: 16. Unrecognized column 'name' (UNKNOWN_IDENTIFIER)"
    from tushare_db.schema.evolver import parse_missing_columns
    assert parse_missing_columns(msg) == ["name"]

def test_parse_missing_columns_multi():
    msg = "Missing columns: 'lead_stock' 'industry' while processing query"
    from tushare_db.schema.evolver import parse_missing_columns
    assert parse_missing_columns(msg) == ["lead_stock", "industry"]
```

并加一个 mock 写入失败 → evolve → 重试成功 的集成测试（mock `ch_client.insert` 第一次抛 missing column 异常，第二次成功）。

### 4.3 上线步骤

1. 跑 `pytest -k schema_evolve` 通过；
2. `docker compose build --no-cache pipeline-scheduler && docker compose up -d --force-recreate pipeline-scheduler`；
3. 故意删一列做端到端：
   ```sql
   ALTER TABLE tushare.tushare_moneyflow_ths DROP COLUMN name;
   ```
   然后 `tushare-db resume`，确认日志出现 `Auto-evolving schema, missing=['name']`，`name` 列自动加回，scope 进入 `done`。

---

## 5. P1：`stk_managers` / `fund_company` 日期序列化错误（2 个失败）

### 5.1 背景
旧版 `_normalize_items` 在容器中没有完整的日期解析逻辑。本地 [worker.py:457-522](../src/tushare_db/runner/worker.py) 的步骤 1 / 1b / 1c 已覆盖。**P0-B 重建镜像后这两条应自动恢复**。

### 5.2 验证步骤
镜像重建后：
```sql
ALTER TABLE _meta.sync_state
UPDATE status = 'pending', last_error = '', _version = toUInt64(now64(3))
WHERE interface IN ('stk_managers','fund_company') AND status = 'failed';
```
```bash
docker compose exec pipeline-scheduler tushare-db resume
```
```sql
SELECT count() FROM tushare.tushare_stk_managers;
SELECT count() FROM tushare.tushare_fund_company;
SELECT * FROM _meta.sync_state FINAL WHERE interface IN ('stk_managers','fund_company') AND status='failed';
```
两表 row 数应远 > 1，第三条查询应为空。

### 5.3 兜底：若仍失败
在 `_parse_date_string` 中处理常见脏数据：`"-"`、`"null"`、`"None"`、`"0000-00-00"` 全部当成空。补丁：

文件：`src/tushare_db/runner/worker.py`，在 [worker.py:578-583](../src/tushare_db/runner/worker.py) 函数开头加：

```python
def _parse_date_string(val: str) -> "datetime.date":
    val = val.strip()
    if not val or val.lower() in {"-", "null", "none", "nan", "0000-00-00", "00000000"}:
        raise ValueError("empty/sentinel date string")
    ...
```

并把对应的非 Nullable Date 列在 schema_overrides 中改为 `Nullable(Date)`：
- `stk_managers.begin_date` / `end_date`
- `fund_company.setup_date` / `end_date`

---

## 6. P1：`fina_audit` SSL / 读超时（67 个失败）

### 6.1 调整 TushareClient 超时

文件：`src/tushare_db/core/tushare_client.py`（搜索 `httpx.Client(`）。

把 `timeout=10` 改为 `timeout=httpx.Timeout(connect=15, read=60, write=15, pool=10)`。
重建镜像。

### 6.2 接口级降速（可选，更稳）

文件：`config/settings.yaml`（或对应 `interfaces/_overrides`），为 `fina_audit` 加：
```yaml
overrides:
  fina_audit:
    rpm_override: 120     # special bucket 默认 285，半速以容忍重试
    timeout_seconds: 60
```
对应代码若不支持，回退方案：在 `TushareClient.call()` 里读 `spec.fetch_strategy.extra` 字段做注入。

### 6.3 重置 + resume

```sql
ALTER TABLE _meta.sync_state
UPDATE status='pending', last_error='', _version=toUInt64(now64(3))
WHERE interface='fina_audit'
  AND status='failed'
  AND (last_error LIKE '%handshake operation timed out%'
    OR last_error LIKE '%read operation timed out%');
```
```bash
docker compose exec pipeline-scheduler tushare-db resume
```

### 6.4 `fut_weekly_monthly` SSL 1 例
同样 resume 即可，无需改代码。

---

## 7. P2：33 张「仅 1 行」表的回填排查

### 7.1 共性原因
- bootstrap 用 1 条样本建表，但 backfill 计划/执行没跑成功（参数错、策略错或 API 真返空）。

### 7.2 逐张排查脚本

```sql
-- 列出所有"仅 1 行"表的同步状态分布
SELECT s.interface, s.status, count() AS n, max(s.last_error) AS sample_err
FROM _meta.sync_state s FINAL
WHERE s.interface IN (
  'bse_mapping','cb_call','cb_issue','cb_share','cn_pmi','eco_cal','fund_company',
  'fund_manager','fund_sales_ratio','fund_sales_vol','fut_holding','fut_weekly_detail',
  'fut_wsr','ggt_daily','ggt_monthly','gz_index','hm_list','index_classify',
  'moneyflow_mkt_dc','new_share','report_rc','sf_month','shibor_quote','st',
  'stk_account_old','teleplay_record','us_tbr','us_trltr','us_tltr','us_trycr',
  'us_tycr','wz_index','yc_cb'
)
GROUP BY s.interface, s.status ORDER BY s.interface, s.status;
```

### 7.3 三类处理

| 现象 | 处置 |
|------|------|
| 该接口在 `sync_state` 中**完全没有记录** | 说明 planner 从未生成 unit。检查 `config/interfaces/*.yaml` 中 `enabled` / `start_date` / `fetch_strategy.kind`，然后 `tushare-db backfill --interface <name>`。 |
| 全是 `failed` | 看 `last_error`，分类：API 返回空（接受）、策略错（改 yaml）、参数缺（改 yaml `required_params`）。 |
| 全是 `done` 但行数 = 1 | 说明 API 真返空 / 不需多次抓。可视为正常（如 `index_classify` 是参考表）。在 `enabled: false` 之前先确认上游不再变化，否则保留 `incremental` 模式仅做日变更监控。 |

### 7.4 已知低 RPM（5 RPM 限速）

参考记忆 `remaining_missing.md`：少数美股表 / 港股通 / 港股深表受 5RPM 限速。对这些接口在 P1 阶段已应用降速，回填批次 `--workers 1 --sleep 1` 即可：
```bash
docker compose exec pipeline-scheduler tushare-db backfill --interface us_tycr --workers 1
```

---

## 8. P3：20 张「2-100 行」表

### 8.1 目标
确认它们是 **真小表**（参考数据 / 低频）还是 **同步丢数据**。判定方法：

```sql
SELECT
  s.interface,
  countIf(status='done') AS done_n,
  countIf(status='failed') AS fail_n,
  sum(rows) AS total_rows
FROM _meta.sync_state s FINAL
WHERE s.interface IN (
 'ths_member','bond_blk','bond_blk_detail','limit_step','daily_info','index_dailybasic',
 'kpl_concept_cons','sge_basic','ggt_top10','sz_daily_info','hsgt_top10','limit_cpt_list',
 'index_global','tdx_member','suspend_d','repo_daily','kpl_list','limit_list_ths',
 'fx_obasic','hm_detail'
)
GROUP BY s.interface ORDER BY total_rows;
```

- `done_n` 高 + `total_rows` 低：上游确实数据少，正常。
- `done_n` 低（远少于交易日数）：策略错或 cron 没跑过。检查 `_meta.sync_runs` 历史。

---

## 9. ClickHouse → schema 一致性自查（每次发版前）

加一个 CI 任务（`scripts/check_schema_drift.py`，可后续单独 ticket）：
1. 拉所有 `tushare.*` 表的列；
2. 拿 `config/interfaces/*.yaml` + `data/samples/*.json` 推断期望列；
3. 输出 diff，CI fail 即阻断发版。

本次只先列出口径，不要求实现。

---

## 10. 验证步骤汇总（每个修复后跑一次）

### 10.1 同步健康
```sql
SELECT status, count() FROM _meta.sync_state FINAL GROUP BY status;
-- 期望：running ≪ 10，failed 持续下降，done 持续上升
```

### 10.2 错误聚类
```sql
SELECT
  multiIf(
    last_error LIKE '%Unrecognized column%','schema_drift',
    last_error LIKE '%Unknown strategy%','planner_strategy',
    last_error LIKE '%handshake%','ssl_timeout',
    last_error LIKE '%read operation timed out%','read_timeout',
    last_error LIKE '%Unable to create Python array%','nullable_violation',
    last_error LIKE '%unsupported operand type%','date_serialization',
    last_error = '','empty_error',
    'other'
  ) AS bucket,
  count() AS n,
  groupUniqArrayIf(interface, 1)[1:5] AS sample_ifaces
FROM _meta.sync_state FINAL
WHERE status='failed'
GROUP BY bucket ORDER BY n DESC;
```

### 10.3 容器代码核验（每次 build 后）
见 §2.3 脚本。

### 10.4 回归测试
```bash
pytest -x --cov=src tests/
```
覆盖率不应低于现有基线（按 `common/testing.md` 要求 ≥ 80%）。

---

## 11. 回滚 / 应急

| 操作 | 回滚命令 |
|------|----------|
| `ALTER ... ADD COLUMN` | `ALTER TABLE ... DROP COLUMN <name>` |
| `MODIFY COLUMN ... Nullable(Date)` | `ALTER TABLE ... MODIFY COLUMN <c> Date`（需保证无 NULL；否则先 `UPDATE <c>=toDate('1970-01-01') WHERE <c> IS NULL`） |
| 镜像重建后行为异常 | `docker compose pull` + 切回上一个 commit `git revert HEAD && docker compose build --no-cache && up -d --force-recreate` |
| `sync_state` 误重置 | ReplacingMergeTree 保留多版本：`SELECT * FROM _meta.sync_state WHERE interface=... ORDER BY _version DESC` 可看历史 |

---

## 12. 交付物清单（执行 AI 完成后产出）

1. **代码改动**（最少）：
   - `src/tushare_db/schema/evolver.py` ← 新增 `parse_missing_columns`
   - `src/tushare_db/runner/worker.py` ← 接入自动演进 + （兜底）`_parse_date_string` 脏数据处理
   - `src/tushare_db/core/tushare_client.py` ← 超时调整
   - `config/interfaces/_schema.yaml` ← 枚举补 `per_symbol`
   - `config/interfaces/stock_moneyflow.yaml` ← 三接口 `enabled: true`
   - `config/interfaces/etf.yaml` / `index.yaml` ← `schema_overrides` 显式 Nullable
   - `tests/runner/test_worker_schema_evolve.py` ← 新增
2. **DDL 执行记录**：所有 `ALTER TABLE` 语句的产出日志。
3. **Resume 报告**：每个 P0/P1 修复后 §10.1、§10.2 的 SQL 输出。
4. **镜像版本**：`docker compose images pipeline-scheduler` 输出 + 容器内 §2.3 脚本输出。
5. **Git 提交**：按 `<type>: <desc>` 单步提交，使用 conventional commits（feat/fix/refactor/chore），不要 `--amend`、不要 `--no-verify`。

---

## 13. 附：常用片段速查

```bash
# 进入 ClickHouse
docker compose exec clickhouse clickhouse-client --user pipeline --password "$CH_PIPELINE_PASSWORD"

# 查 mutation 进度
docker compose exec clickhouse clickhouse-client --user pipeline --password "$CH_PIPELINE_PASSWORD" \
  --query "SELECT database, table, mutation_id, is_done FROM system.mutations WHERE NOT is_done"

# 看 scheduler 日志（最后 200 行）
docker compose logs --tail=200 pipeline-scheduler

# 触发一次强制 resume（dry-run）
docker compose exec pipeline-scheduler tushare-db resume --dry-run

# 单接口手动 backfill
docker compose exec pipeline-scheduler tushare-db backfill --interface <name>
```

---

> 任何步骤报错请把：(1) 具体命令 (2) 完整 stderr (3) `_meta.sync_state FINAL` 中相应行（含 `last_error` / `attempts` / `heartbeat_at`）三项一并贴出，不要自行重试超过 2 次。

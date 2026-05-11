# 修复后验证报告 + 剩余问题

> 输入：用户完成 REMAINING_ISSUES_20260429.md §5 全部修复后的总结
> 验证范围：YAML 配置 + Python 代码 + 新增脚本/SQL/单测 + 审计脚本输出
> 验证时间：2026-04-30
> 结论：**已修项 100% 验证通过；但发现 6 个剩余/潜在问题需要后续处理**

---

## 0. 验证结果速览

### 0.1 已修项验证（全部通过 ✅）

| 维度 | 验证方式 | 结果 |
|---|---|---|
| **34 个接口策略修正** | 写脚本对账每个接口 YAML.kind vs 期望 | **34/34 OK**（fina_audit 是 period_loop / dividend 是 per_symbol / stk_holdertrade 是 per_symbol / cb_call/cb_issue/eco_cal/ggt_monthly/report_rc 等都对） |
| **审计脚本** | `python scripts/audit_strategy_param_mismatch.py` | exit 0；**0 BUGs + 3 WARNs**（3 WARN 全是已 disabled 的 bo_cinema/bo_daily/bo_monthly，不影响） |
| **N2 限速超时 30s→120s** | `grep "timeout" tushare_client.py:121-142` | `def call(..., timeout: float = 120.0, ...)` 已正确设置默认值，传到 `self._limiter.acquire(bucket, timeout)` |
| **N3 CH 连接池 8→32** | `grep maxsize` worker.py + clickhouse_sink.py | 两处都有 `pool_mgr_options={"maxsize": 32, "num_pools": 8}` |
| **新文件存在性** | ls 检查 | `scripts/audit_strategy_param_mismatch.py` ✅、`scripts/migrate_ccass_hold_shareholding.sql` ✅、`tests/unit/test_strategy_param_audit.py` ✅ |
| **reset-state CLI 命令** | `grep -c reset-state cli.py` → 2 | 命令已注册 |
| **ccass_hold YAML** | `grep -A 1 schema_overrides stock_special.yaml` | `shareholding: Nullable(String)` ✅ |

### 0.2 待验证项（用户尚未跑过运行时）

最新日志是 `logs/fina_audit_run_20260429_230236.log`（昨晚 23:02），**全部修复完成后没有跑过任何回填**。所以以下是"代码层修对了，运行时还没跑"的状态：
- 真实 fina_audit 是否只规划 25 个 unit
- 真实 dividend 是否只规划 ~5,500 个 unit
- 真实 ccass_hold ALTER TABLE 是否执行
- Rate limiter timeout 数量是否下降
- ClickHouse 连接池警告是否消失

→ 见本文档 §3 「上线前必须执行的 7 步实战验证」

---

## 1. 发现的剩余 / 潜在问题

### 1.1 问题 V1（HIGH）：bo_monthly 的 monthly_window 策略与 API 参数不匹配

**审计脚本输出**：

```
WARN bo_monthly: monthly_window but no 'month'. ['date']
```

**根因**：`monthly_window` 策略在 `src/tushare_db/planner/strategies.py:144-155` 生成的 params 是 `{"month": ym}`，但 `bo_monthly` API 实际只接受 `['date']` 参数（不是 `month`）。

```python
# strategies.py:151
units.append(
    WorkUnit(
        ...
        params={"month": ym},   # ← 但 bo_monthly API 只认 'date'
        ...
    )
)
```

**当前为什么没炸**：因为 `bo_monthly` `enabled: false`。但**如果将来启用，会立刻命中跟 dividend 一样的"参数被忽略 / 拉到全量数据 / 重复 INSERT"问题**。

#### 1.1.1 修复方案

把 `bo_monthly` 改为 `date_loop` + `date_field: date`（跟同组 `bo_cinema`/`bo_daily` 保持一致）：

```yaml
# config/interfaces/macro.yaml
---
name: bo_monthly
table: tushare_bo_monthly
enabled: false                                  # 保持禁用
priority: P3
mode: incremental
freq_bucket: special
fetch_strategy:
  kind: date_loop                               # ← monthly_window → date_loop
  date_field: date                              # ← API 参数名是 date 不是 trade_date / month
partition_key: toYYYYMM(date)
order_by: ts_code, date
required_params: [date]
fields: []
schema_overrides: {}
batch: B
```

或者把 `bo_monthly` 改为 `full_once` + static_params（和 `bo_weekly` 一致）：

```yaml
fetch_strategy:
  kind: full_once
  static_params:
    start_date: '20200101'
    end_date: '20260430'   # 或脚本动态填充
```

**推荐**：`date_loop` + `date_field: date` —— 让审计脚本通过。

---

### 1.2 问题 V2（HIGH）：dividend / stk_holdertrade / 等接口表中**残留 25× 重复数据**

**根因**：strategy 修对了之后，**新一轮回填只写 1× 数据**。但是：
- 过去 `per_symbol_period` 时代写入的 25× 重复行**仍然在 ClickHouse 表里**
- ReplacingMergeTree 后台 merge 会去重，但**节奏不可控**（可能几小时、几天才合并完一个 partition）
- 在 merge 完成前，普通 SELECT 不加 `FINAL` 看到的还是 25× 数据

**用户感知**：修完之后查 dividend 表，看到的还是 137K+ 行（旧数据）+ 5500 新行。即使 ReplacingMergeTree 标记了哪些是旧版本，去重发生在后台。

#### 1.2.1 修复方案

新增 `scripts/cleanup_duplicate_data.sql`：

```sql
-- ============================================================
-- 清理 strategy 错配时代写入的重复数据
-- 在 reset-state + backfill 完成后执行
-- ============================================================

-- 检查去重前 vs 去重后行数（修复前这两个数字应该差 25×）
SELECT
    'tushare_dividend' AS table,
    count() AS rows_before_dedup,
    uniqExact(ts_code, end_date, ann_date) AS rows_after_dedup,
    count() / nullIf(uniqExact(ts_code, end_date, ann_date), 0) AS dup_ratio
FROM tushare.tushare_dividend
UNION ALL SELECT 'tushare_stk_holdertrade', count(),
    uniqExact(ts_code, ann_date, holder_name, in_de),
    count() / nullIf(uniqExact(ts_code, ann_date, holder_name, in_de), 0)
FROM tushare.tushare_stk_holdertrade
UNION ALL SELECT 'tushare_fina_audit', count(),
    uniqExact(ts_code, end_date, ann_date),
    count() / nullIf(uniqExact(ts_code, end_date, ann_date), 0)
FROM tushare.tushare_fina_audit;

-- 强制 merge（去重）— 慢，但执行后再查询数据正确
OPTIMIZE TABLE tushare.tushare_dividend FINAL;
OPTIMIZE TABLE tushare.tushare_stk_holdertrade FINAL;
OPTIMIZE TABLE tushare.tushare_fina_audit FINAL;

-- 再次检查 — 期望 dup_ratio 接近 1
SELECT 'after_optimize' AS phase,
       count() AS rows
FROM tushare.tushare_dividend;

-- 注意：OPTIMIZE TABLE FINAL 在大表上会很慢（几分钟到几小时）
-- 对于 dividend ~140K 行规模，预计 1-3 分钟
-- 对于 stk_holdertrade（更大），预计 10-30 分钟
```

执行：

```bash
clickhouse-client --multiquery < scripts/cleanup_duplicate_data.sql
```

> **警告**：OPTIMIZE FINAL 会**临时占用大量 IO**，建议在低峰期跑。如果表非常大，可以分 partition 跑：
>
> ```sql
> OPTIMIZE TABLE tushare.tushare_dividend PARTITION '202001' FINAL;
> OPTIMIZE TABLE tushare.tushare_dividend PARTITION '202002' FINAL;
> ...
> ```

---

### 1.3 问题 V3（MEDIUM）：planner 缺少运行时 strategy/param 校验（fail-fast）

**根因**：审计脚本是**离线**的，CI 时跑。但运行时（scheduler 触发 / 手动 backfill）**没有任何防御**。如果将来：
- 有人改了 YAML 但忘了跑 audit
- MCP search-index 升级后接口参数变了
- 新加的接口 strategy 选错

→ 会**直接进入跟 dividend 一样的循环**，又要等用户从日志里发现。

#### 1.3.1 修复方案

在 `src/tushare_db/planner/planner.py:plan_units()` 入口加一道运行时校验：

```python
# planner.py 顶部加导入
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def _load_mcp_params() -> dict[str, list[str]]:
    """Load MCP search-index for runtime strategy/param validation."""
    from pathlib import Path
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "vendor" / "tushare-mcp" / "search-index@0.2.1.min.json",
        Path(__file__).resolve().parent.parent.parent.parent / "search-index.min.json",
    ]
    for path in candidates:
        if path.exists():
            data = json.load(open(path, encoding="utf-8"))
            return {
                item["name"]: [p for p in item.get("inputParams", []) if p not in ("limit", "offset")]
                for item in data["index"]
            }
    return {}  # MCP index unavailable — skip validation


def _validate_strategy_against_mcp(spec: InterfaceSpec) -> None:
    """Fail-fast if strategy/MCP params disagree."""
    mcp = _load_mcp_params()
    if spec.name not in mcp:
        return  # paid/VIP API — no MCP metadata
    params = mcp[spec.name]
    strategy = spec.fetch_strategy.kind
    if strategy in ("period_loop", "per_symbol_period") and "period" not in params:
        raise ValueError(
            f"[{spec.name}] strategy={strategy} but API has no 'period' param. "
            f"API params={params}. Fix YAML before retrying."
        )
    if strategy == "monthly_window" and "month" not in params:
        raise ValueError(
            f"[{spec.name}] strategy=monthly_window but API has no 'month' param. "
            f"API params={params}. Did you mean date_loop with date_field={params[0] if params else 'date'}?"
        )


# plan_units 入口（line 78）增加校验
def plan_units(spec, client, start_date=None, end_date=None):
    _validate_strategy_against_mcp(spec)   # ← 新增这一行
    strategy = spec.fetch_strategy.kind
    ...
```

**单元测试**：在 `tests/unit/test_planner_executor.py` 加：

```python
def test_plan_units_rejects_strategy_param_mismatch():
    """Planner must fail fast on strategy/MCP-params mismatch."""
    from tushare_db.config.models import InterfaceSpec, FetchStrategy
    spec = InterfaceSpec(
        name="dividend",
        table="tushare_dividend",
        priority="P0",
        mode="incremental",
        freq_bucket="normal",
        fetch_strategy=FetchStrategy(kind="per_symbol_period"),  # 故意错配
        order_by="ts_code, end_date",
        batch="A",
    )
    import pytest
    with pytest.raises(ValueError, match="no 'period' param"):
        plan_units(spec, client=None)  # 应在 _validate_strategy_against_mcp 抛错
```

---

### 1.4 问题 V4（MEDIUM）：跨进程并发争抢 special 桶 token

**根因**：N2 把 `Rate limiter timeout` 从 30s 调到 120s，**这是症状缓解，不是根因修复**。真正的根因：

1. `DualRateLimiter` 是**进程内**的（threading.Lock + deque），多个 Python 进程不共享配额
2. `scripts/retry_dividend.py`、`scripts/resume_fina_audit.py`、`scripts/resume_fund_slow.py`、`tushare-db scheduler-run`、`tushare-db backfill ...`，每跑一个就新建一个独立的 limiter
3. 5 个并发进程 × 4 worker × special 桶（285 RPM），**实际 RPM 上限是 285×5=1425**，远超 Tushare 真实限制

REPORT_20260429.md §四 说"清理本机 16 个 Python 残留进程"——这反映了用户经常多脚本并发，是**已知未解决**的问题。

#### 1.4.1 修复方案 A（轻量）：开跑前互斥锁

`src/tushare_db/core/concurrency_lock.py` 已存在（`retry_dividend.py:34` 有 `lock.acquire()`），但没强制所有脚本/CLI 用它。把 `tushare-db backfill` / `scheduler-run` / 各个 `scripts/resume_*.py` / `scripts/retry_*.py` **全部入口**包一层 ConcurrencyLock：

```python
# scripts/resume_fina_audit.py 顶部
from tushare_db.core.concurrency_lock import ConcurrencyLock
lock = ConcurrencyLock()
if not lock.try_acquire(timeout=5):
    print("Another backfill/retry is running. Exiting.")
    sys.exit(2)
try:
    # ... existing logic
finally:
    lock.release()
```

#### 1.4.2 修复方案 B（严格）：限速桶用 Redis / ClickHouse 持久化

进程间共享桶状态，把 `DualRateLimiter` 内的 `deque[float]` 替换为 Redis Sorted Set（或 ClickHouse 的 `_meta.api_calls` 表 + 时间窗 SELECT）。

```python
# 伪代码：基于 ClickHouse 的跨进程限速
def acquire_cross_process(bucket: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    rpm = 475 if bucket == "normal" else 285
    while time.monotonic() < deadline:
        # 查询过去 60 秒该桶的调用数
        result = ch.query(f"""
            SELECT count() FROM _meta.api_calls
            WHERE bucket = '{bucket}'
              AND ts > now() - INTERVAL 60 SECOND
        """)
        if result.result_rows[0][0] < rpm:
            ch.insert("_meta.api_calls", [(bucket, datetime.utcnow())])
            return True
        time.sleep(1)
    return False
```

→ 工作量大，但彻底解决多进程问题。**先用方案 A 兜底**。

---

### 1.5 问题 V5（LOW）：监控指标缺失

**根因**：当前没有任何"修复有效"的量化指标，只能 grep 日志。如果用户改完后又出现限流 / 重复，没法立刻看出来。

#### 1.5.1 修复方案：每日健康指标

新增 `scripts/daily_health_check.py`：

```python
"""Daily pipeline health check. Run via cron after midnight."""
from __future__ import annotations
import os
import sys
from pathlib import Path
import clickhouse_connect

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

EXPECTED = {
    "dividend":         {"max_units": 6000,  "max_dup_ratio": 1.5},
    "fina_audit":       {"max_units": 30,    "max_dup_ratio": 1.5},
    "stk_holdertrade":  {"max_units": 6000,  "max_dup_ratio": 1.5},
    "ccass_hold":       {"max_units": 2000,  "max_dup_ratio": 1.5},
}


def check() -> int:
    ch = clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
    )

    errors: list[str] = []
    for interface, expect in EXPECTED.items():
        # 1. sync_state unit 数量
        result = ch.query(
            f"SELECT count() FROM _meta.sync_state WHERE interface = '{interface}'"
        )
        units = result.result_rows[0][0]
        if units > expect["max_units"]:
            errors.append(f"{interface}: {units} units (max {expect['max_units']}) — strategy may be wrong")

        # 2. failed unit 占比
        result = ch.query(
            f"SELECT count(), countIf(status='failed') FROM _meta.sync_state "
            f"WHERE interface = '{interface}'"
        )
        total, failed = result.result_rows[0]
        if total > 0 and failed / total > 0.10:
            errors.append(f"{interface}: {failed}/{total} ({failed/total:.1%}) failed")

    # 3. 表去重率
    for tbl in ["tushare_dividend", "tushare_stk_holdertrade", "tushare_fina_audit"]:
        try:
            result = ch.query(f"""
                SELECT count(), uniqExact(ts_code, end_date)
                FROM tushare.{tbl}
            """)
            rows, uniq = result.result_rows[0]
            if uniq > 0 and rows / uniq > 1.5:
                errors.append(f"{tbl}: dup ratio {rows/uniq:.1f}× — run OPTIMIZE TABLE FINAL")
        except Exception as e:
            errors.append(f"{tbl}: query failed — {e}")

    # 4. 限流错误数
    log_path = Path("data/logs/app.log")
    if log_path.exists():
        recent_errors = sum(
            1 for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-50000:]
            if "Rate limiter timeout" in line
        )
        if recent_errors > 50:
            errors.append(f"Rate limiter timeout: {recent_errors} occurrences in last 50K log lines")

    if errors:
        print("=== HEALTH CHECK FAILED ===")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("=== HEALTH CHECK OK ===")
    return 0


if __name__ == "__main__":
    sys.exit(check())
```

接入 Windows 计划任务或 cron：

```bash
# 每天 06:00 跑
python scripts/daily_health_check.py >> logs/health_$(date +%Y%m%d).log 2>&1
```

---

### 1.6 问题 V6（LOW）：ccass_hold 列迁移可能产生脏数据

**根因**：`scripts/migrate_ccass_hold_shareholding.sql` 包含：

```sql
ALTER TABLE tushare.tushare_ccass_hold MODIFY COLUMN shareholding Nullable(String);
```

`Date → Nullable(String)` 转换时：
- 原来 `Date` 列里的合法日期会变成 `'2024-03-15'` 这样的字符串
- 但 Tushare API 实际返回的 shareholding 是**数字字符串**（如 `"123456789"` 表示持股数量）
- 转换后表里会**混有日期字符串和数字字符串**

#### 1.6.1 修复方案

在 ALTER 之后清掉错误数据，让下次回填重写：

```sql
-- 在 ALTER 之后追加：
-- 1. 标记格式异常的行（shareholding 包含 '-' 是日期格式，不是数字）
SELECT count() FROM tushare.tushare_ccass_hold
WHERE shareholding LIKE '%-%';

-- 2. 删除这些异常行（让下次 backfill 重写正确的数字字符串）
ALTER TABLE tushare.tushare_ccass_hold
DELETE WHERE shareholding LIKE '%-%';

-- 3. 等待 mutation 完成
SELECT * FROM system.mutations
WHERE database = 'tushare' AND table = 'tushare_ccass_hold' AND is_done = 0;

-- 4. 清 sync_state 让对应日期重新规划
ALTER TABLE _meta.sync_state DELETE
WHERE interface = 'ccass_hold' AND scope_key IN (
    -- 这些是被 DELETE 影响的 trade_date，需先从 ccass_hold 表查
    SELECT DISTINCT formatDateTime(trade_date, '%Y%m%d') AS scope_key
    FROM tushare.tushare_ccass_hold WHERE 1=0  -- 占位，实际可手动填
);
-- 或者直接清全部失败的 ccass_hold：
ALTER TABLE _meta.sync_state DELETE
WHERE interface = 'ccass_hold' AND status = 'failed';
```

**更稳的做法**：直接 `DROP TABLE` + `bootstrap` + `backfill`，全表重灌。但代价是丢历史时间戳。

---

## 2. 状态矩阵（更新）

| ID | 问题 | 状态 | 备注 |
|---|---|---|---|
| H1-H6 | REPORT 已修项 | ✅ 仍然修着 | |
| R1（31 个策略错配）| ✅ 已修 | 27 个改 strategy，4 个 disable |
| R2（stk_holdertrade）| ✅ 已修 | per_symbol |
| R3（dividend）| ✅ 已修 | per_symbol |
| R4（ccass_hold）| ⚠️ 部分 | YAML 改了；ALTER TABLE 待执行 |
| R5（防回归脚本）| ✅ 已修 | audit + unit test 都有 |
| N1（fina_audit 策略）| ✅ 已修 | period_loop |
| N2（限速超时）| ✅ 已修 | 30s → 120s |
| N3（CH 连接池）| ✅ 已修 | 8 → 32 |
| N4（reset-state CLI）| ✅ 已修 | cli.py 注册了 |
| **V1**（bo_monthly monthly_window 错配）| ❌ 新发现 | §1.1 |
| **V2**（重复数据残留）| ❌ 新发现 | §1.2 — 需要 OPTIMIZE FINAL |
| **V3**（运行时 strategy 校验）| ❌ 新发现 | §1.3 — fail-fast 没接 |
| **V4**（跨进程限速桶）| ❌ 已知未修 | §1.4 — 需要 ConcurrencyLock 或 Redis |
| **V5**（每日健康指标）| ❌ 新发现 | §1.5 — 监控盲区 |
| **V6**（ccass 迁移脏数据）| ❌ 新发现 | §1.6 — ALTER 后需清理 |

---

## 3. 上线前必须执行的 7 步实战验证

> 用户改了所有代码与配置，但**还没真正跑过任何回填**。下面是上线前的最小验证序列。

### Step 1：CLI 命令能加载

```bash
cd F:/AIcoding_space/VsCode/tushare_db
tushare-db reset-state --help
# 期望：显示帮助信息，不报 import 错
tushare-db --version 2>&1 | head -3
# 期望：能正常输出
```

### Step 2：审计脚本最终再跑一次

```bash
python scripts/audit_strategy_param_mismatch.py
# 期望：exit 0；0 BUGs + 3 WARNs（bo_*）

pytest tests/unit/test_strategy_param_audit.py -v
# 期望：通过
```

### Step 3：执行 ccass_hold 列迁移

```bash
clickhouse-client --multiquery < scripts/migrate_ccass_hold_shareholding.sql
```

**核查 SQL 输出**：
- 第 1 行 SELECT：确认列 type 改成了 `Nullable(String)`
- 第 3 行 SELECT：count() 应该跟改之前一样（或略多，因为 NULL 行）
- 必要时执行 §1.6 的"清理异常行"

### Step 4：清 sync_state 残留

```bash
tushare-db reset-state --interface fina_audit --confirm
tushare-db reset-state --interface stk_holdertrade --confirm
tushare-db reset-state --interface ccass_hold --confirm
```

**核查**：每条命令应输出"Found N rows... Deleted."。

### Step 5：fina_audit dry-run 验证 unit 数

最关键的一步：**不跑数据，只看 plan 出多少 unit**。

```bash
# 临时用 dry-run 模式
python -c "
import os, sys
sys.path.insert(0, 'src')
os.environ['CH_HOST'] = 'localhost'
from dotenv import load_dotenv; load_dotenv()
import clickhouse_connect
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units

ch = clickhouse_connect.get_client(host='localhost', port=8123, username='pipeline', password=os.environ.get('CH_PIPELINE_PASSWORD',''))
specs = {s.name: s for s in load_interface_specs()}
units = plan_units(specs['fina_audit'], ch)
print(f'fina_audit planned units: {len(units)}')
units = plan_units(specs['dividend'], ch)
print(f'dividend planned units: {len(units)}')
units = plan_units(specs['stk_holdertrade'], ch)
print(f'stk_holdertrade planned units: {len(units)}')
"
```

**期望输出**：

```
fina_audit planned units: 25            ← 不再是 137,775
dividend planned units: ~5500           ← 不再是 137,775
stk_holdertrade planned units: ~5500    ← 不再是 137,775
```

如果数字仍然是 137K，**立即停止**，去 §1.3 加运行时校验。

### Step 6：小规模真实回填

```bash
# fina_audit 全量（25 unit，10 秒内跑完）
tushare-db backfill --interface fina_audit
# 期望：done=25, failed=0, 用时 < 60s

# 监控限速：另开终端
tail -f data/logs/app.log | grep -E "Rate limiter timeout|Connection pool is full"
# 期望：无输出
```

### Step 7：24h 后健康检查

```bash
# 表去重率
clickhouse-client -q "
SELECT 'dividend' AS t, count() AS rows, uniqExact(ts_code, end_date) AS uniq, count()/uniqExact(ts_code,end_date) AS dup
FROM tushare.tushare_dividend
UNION ALL SELECT 'fina_audit', count(), uniqExact(ts_code,end_date), count()/nullIf(uniqExact(ts_code,end_date),0)
FROM tushare.tushare_fina_audit
UNION ALL SELECT 'stk_holdertrade', count(), uniqExact(ts_code,ann_date), count()/nullIf(uniqExact(ts_code,ann_date),0)
FROM tushare.tushare_stk_holdertrade
"
# 期望：dup ratio 全部 < 1.5 — 否则跑 OPTIMIZE TABLE FINAL（§1.2）

# sync_state 每接口行数
clickhouse-client -q "
SELECT interface, count() AS units, countIf(status='done') AS done, countIf(status='failed') AS failed
FROM _meta.sync_state
WHERE interface IN ('dividend','fina_audit','stk_holdertrade','ccass_hold')
GROUP BY interface
ORDER BY interface
"
# 期望：units 与 §3 Step 5 的 plan 数量一致

# 限速错误数
grep -c "Rate limiter timeout" data/logs/app.log
# 期望：< 10（修复前是几百）
```

---

## 4. 优先级建议

按"修复价值 / 实施成本"排序：

| 优先级 | 任务 | 时间 | 来源 |
|---|---|---|---|
| **必须立刻** | §3 上线前 7 步实战验证 | 30 min | 修复后必跑 |
| **必须立刻** | V1 修 bo_monthly 策略 | 1 min | §1.1 |
| **强烈推荐** | V2 跑 OPTIMIZE TABLE FINAL 清重复 | 30 min | §1.2 |
| **强烈推荐** | V3 planner 加运行时校验 | 30 min | §1.3 |
| **建议** | V4-A 在所有脚本入口加 ConcurrencyLock | 1 hour | §1.4 |
| **建议** | V5 daily_health_check.py + cron | 1 hour | §1.5 |
| **可选** | V6 ccass_hold 异常数据清理 | 视实测脏数据量 | §1.6 |
| **可选** | V4-B 跨进程限速桶（Redis）| 1 day | §1.4 |

---

## 5. 总结

REMAINING_ISSUES_20260429.md 里的 8 个问题**全部修对了**。审计脚本零 BUG，配置层完整，代码层已就位。

但还有：
- **1 个新策略错配**（bo_monthly，已禁用所以暂时不炸）
- **3 个修复后必做的"扫尾"**（OPTIMIZE 清重复 / 运行时校验 / 健康监控）
- **1 个已知未解决**（跨进程限速桶）
- **1 个迁移副作用**（ccass_hold ALTER 可能产生脏数据）

最关键的是 **§3 的 7 步实战验证**——你已经把所有代码改对了，但**还没真跑一次**。Step 5 的 dry-run 验证（5 行 Python）是上线前唯一能预先确认"修对了没"的方法。**强烈建议先跑 Step 1-5 再 commit / 部署**。

---

## 附录：本文档与其他文档的关系

```
HANDOFF_MCP_CONFIG_FIX.md (规划)
    └── §16 运行时故障五大类
        └── REPORT_20260429.md (一半执行)
            └── REMAINING_ISSUES_20260429.md (剩余 9 项)
                └── 用户完成 8 项修复 + dividend 已修 = 9/9 ✅
                    └── POST_FIX_VERIFICATION_20260430.md ← 本文档
                        ├── §0 验证 8/8 都对了
                        ├── §1 新发现 6 个剩余/潜在问题（V1-V6）
                        └── §3 上线前 7 步必跑验证
```

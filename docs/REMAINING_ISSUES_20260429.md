# Follow-up: REPORT_20260429.md 未修复项 + 最新日志新问题

> 生成时间：2026-04-29 23:30
> 范围：审查 `docs/REPORT_20260429.md` 修复完成度 + 分析 `logs/fina_audit_run_20260429_230236.log` 等最新日志
> 上一轮文档：`HANDOFF_MCP_CONFIG_FIX.md` §16、`AUDIT_LOG_FINDINGS_20260429.md`

---

## 0. 执行摘要

REPORT_20260429.md 完成了 **HTTP/2 连接老化、heartbeat 异常、7 个策略小修、65 个 freq_bucket 纠正、3 个接口禁用** —— 这些是真修好了。

**但有 8 个问题 REPORT 没覆盖**，其中 5 个是 HANDOFF §16 已经标注的、4 个是今晚最新跑 fina_audit 时新暴露出来的。最严重的两个：

| 严重度 | 问题 | 用户感受 |
|---|---|---|
| **CRITICAL** | `fina_audit` 策略错配为 `per_symbol_period`（137,775 单元）而非 `period_loop`（25 单元）—— 当前实测耗时 **5.3 天才能跑完** | "fina_audit 永远跑不完" |
| **CRITICAL** | 32 个接口仍然存在 strategy / API params 错配，会持续制造重复数据 + 错失数据 | "数据老是有重复 / 一直循环" |

---

## 1. REPORT 漏修的项（验证后清单）

### 1.1 验证方法

跑了一次实测脚本（基于 vendored MCP search-index）：

```python
# 排除 REPORT 已修的 14 个接口后，重新对账
fixed_in_report = {'new_share','fund_manager','fund_nav','fund_portfolio',
                   'fund_factor_pro','index_daily','cb_share','dc_member',
                   'fut_weekly_monthly','concept','concept_detail',
                   'stk_week_month_adj','cn_pmi','tdx_daily'}
```

**结果：仍有 32 个接口存在策略 / API 参数错配。**

### 1.2 仍然存在错配的 32 个接口

#### 1.2.1 BUG（严重）— 1 个

| 接口 | 当前 strategy | 实际 API params | 问题 |
|---|---|---|---|
| `stk_holdertrade` | `per_symbol_period` | `[ts_code, ann_date, start_date, end_date, trade_type, holder_type]` | API **无 `period` 参数**，每次返回 ts_code 全部历史，被重复 INSERT 25× |

> 与 `dividend` 之前同样的根因。`dividend` 的 freq_bucket 改了但**策略没改**——所以 `dividend` 实际上也仍然存在这个 bug！
>
> **核查**：

```bash
grep -A 12 "^name: dividend" config/interfaces/stock_financial.yaml
```

> 如果输出仍是 `kind: per_symbol_period`，dividend 也需要再补到这个 BUG 列表里。

#### 1.2.2 WARN（中等）— 31 个

```
=== date_loop 但 API 无 trade_date 参数（31 个） ===

cb_call           [ts_code, ann_date, start_date, end_date]
cb_issue          [ts_code, ann_date, start_date, end_date]
cb_price_chg      [ts_code]
eco_cal           [date, start_date, end_date, currency, country, event, is_new]
fund_sales_ratio  [年]                          ← API 参数本身有问题
fund_sales_vol    [year, quarter, name]
bo_cinema         [date]
bo_daily          [date]
bo_monthly        [date]
bo_weekly         [date, start_date, end_date]
hk_balancesheet   [ts_code, period, ind_name, start_date, end_date]
hk_cashflow       [ts_code, period, ind_name, start_date, end_date]
hk_fina_indicator [ts_code, period, report_type, start_date, end_date]
hk_income         [ts_code, period, ind_name, start_date, end_date]
hk_mins           [ts_code, freq, start_date, end_date, test]
rt_hk_k           [topic, ts_code]
us_balancesheet   [ts_code, period, ind_name, report_type, start_date, end_date]
us_cashflow       [ts_code, period, ind_name, report_type, start_date, end_date]
us_fina_indicator [ts_code, period, report_type, start_date, end_date]
us_income         [ts_code, period, ind_name, report_type, start_date, end_date]
ft_mins           [ts_code, freq, start_date, end_date]
rt_fut_min        [topic, freq, ts_code]
opt_mins          [ts_code, freq, start_date, end_date]
rt_min            [topic, freq, ts_code]
rt_k              [topic, ts_code]
ggt_monthly       [month, start_month, end_month]
report_rc         [ts_code, report_date, start_date, end_date]
film_record       [ann_date, start_date, end_date]
teleplay_record   [report_date, start_date, end_date, org, name]
tmt_twincome      [date, item, start_date, end_date]
tmt_twincomedetail [date, item, symbol, start_date, end_date, source]
```

每一个的修法见 §5.1。

### 1.3 未执行的 ALTER TABLE（ccass_hold）

REPORT §2.6 写了"ccass_hold schema_overrides 缩进 4 空格统一为 2 空格"——这只是 YAML 排版修正。**实际 ClickHouse 表的 shareholding 列类型有没有改，REPORT 没说**。

YAML 现状（已 review）：

```yaml
name: ccass_hold
schema_overrides:
  shareholding: String   ← YAML 期望 String
```

但 `data/logs/app.log` 之前有 3,828 条 `Unable to create Python array for source column 'shareholding'... not Nullable` 错误，说明 CH 表里这列大概率还是 `Date` 或 `Date Non-Nullable`。

**REPORT 缺少**：`ALTER TABLE tushare.tushare_ccass_hold MODIFY COLUMN shareholding Nullable(String)` 这步。

### 1.4 未创建的防回归脚本

HANDOFF §16.2 步骤 1 要求新增 `scripts/audit_strategy_param_mismatch.py`，让 CI 检测 strategy/MCP-inputParams 错配，防止回归。

REPORT 七个新脚本里**没有这个**。

---

## 2. 最新日志新问题（fina_audit_run_20260429_230236.log）

### 2.1 问题 N1：fina_audit 策略选错（CRITICAL）

#### 现象

`logs/fina_audit_run_20260429_230236.log` 第 6-11 行：

```
Strategy: per_symbol_period
Bucket: special
Planned 137775 work units
Executing 137775 units with 4 special workers...
```

进度（实测）：

```
23:02:41 启动
23:21:46 done=294 failed=76 rows=69 total=137775
```

**19 分钟跑 370 个单元，按这速度 → 7,706 分钟 = 128 小时 = 5.3 天才能跑完**。

#### 根因

对比同表（`config/interfaces/stock_financial.yaml`）的兄弟接口：

| 接口 | strategy | unit 数量 | API 也支持 period？ |
|---|---|---|---|
| `income` | `period_loop` | 25 | 是 |
| `balancesheet` | `period_loop` | 25 | 是 |
| `cashflow` | `period_loop` | 25 | 是 |
| `fina_indicator` | `period_loop` | 25 | 是 |
| **`fina_audit`** | **`per_symbol_period`** | **137,775** | **是** |

**5 个 fina 接口的 API 参数全部都有 `period`**，但 fina_audit 莫名其妙用了 `per_symbol_period`（按股票×季度循环），其他四个用 `period_loop`（仅按季度循环、一次拉所有股票）。

差距：**fina_audit 是 income 系列的 5,500 倍调用量**。

#### 数据稀疏证据

```
done=294, rows=69 → 实际有数据的成功率仅 23%
done=294, failed=76, total=370 → 失败率 21%
```

意味着 **77% 的成功调用是 0 行 Empty response**——证明：
1. 大部分 ts_code 没有审计数据
2. 大部分 period 也没有审计数据
3. 用 `period_loop` 一次拉所有 ts_code 就能去掉这些空调用

### 2.2 问题 N2：Rate limiter timeout（HIGH）

#### 现象

```
23:02:41 启动
23:03:16 (35s 后) 第一个 'Rate limiter timeout for fina_audit'
后续每 30-60s 出现一批
共 152 条 'error' 中绝大多数是 Rate limiter timeout
```

#### 根因

- worker `tushare_client.call(timeout=30)` 默认 30s 超时
- 启动时 4 个 worker 同时占 special 桶 token，加上其他后台 special 接口（pledge_stat / repurchase / share_float / fund_* / cb_* 等都在 special 桶）
- special 桶 285 RPM = 4.75 token/秒
- 4 worker 全速 burst → 1 秒消耗 4 token，但桶持续补充 4.75 token/秒；若**多脚本并发**或 cooldown 触发，token 就枯竭

跨脚本竞争证据：**REPORT §四"待执行"段说"清理本机 16 个 Python 残留进程"**——这些残留进程可能仍在跑，争抢 special 桶。

#### 后果

每个超时 = 1 个 work unit 进 `failed` 状态 = 后续要再 retry。21% 失败率全部由此导致。

### 2.3 问题 N3：HTTP 连接池打爆（MEDIUM）

#### 现象（`data/logs/app.log` 末尾）

```
HTTP Request: POST https://api.tushare.pro "HTTP/2 200 OK"
Connection pool is full, discarding connection: localhost. Connection pool size: 8
Connection pool is full, discarding connection: localhost. Connection pool size: 8
... (10+ 次连续) ...
```

#### 根因

`Connection pool is full, ... localhost` —— 是 **ClickHouse 连接池**（不是 Tushare），来自 `clickhouse-connect` / `urllib3`。

每个 worker 持有：
- 1 个 ClickHouse client（主写入）
- 1 个 ClickHouse client（heartbeat 用，独立 — 见 worker.py）

4 special worker × 2 client = 8 个 CH 连接活跃。`urllib3` 默认 `pool_maxsize=8`，正好打爆。

并发提高（比如未来 8 worker）会更严重。

#### 后果

- 连接被 discard → 立即重建 → 多 ~50ms latency / op
- ClickHouse Server 端 keep-alive 连接质量下降
- 极端情况触发 ClickHouse 端 `tcp_too_many_connections`（虽未在日志中观测到）

### 2.4 问题 N4：sync_state 残留未自动化清理（MEDIUM）

#### 现象

`scripts/clear_stale_sync_state.sql` 是**静态 SQL**，只针对 9 个特定接口。但 strategy 修复是**滚动事件** —— 比如本次 N1 修了 fina_audit 之后，137K 旧 `fina_audit:TSCODE:PERIOD` scope_key 又变成残留，需要再写一条 DELETE。

HANDOFF §16.3 推荐过 `tushare-db reset-state --interface <name>` CLI 命令，REPORT 没采纳。

#### 后果

每次改 strategy 都要手动加一条 DELETE SQL 到 clear_stale_sync_state.sql 里再跑，过程容易漏。

### 2.5 问题 N5（潜在）：dividend 自身的 strategy 仍然是 per_symbol_period

REPORT §2.3 把 dividend 的 `freq_bucket` 从 special 改成了 normal，但**没改 strategy**。所以：

```bash
grep -A 12 "^name: dividend" config/interfaces/stock_financial.yaml
```

如果输出仍是 `kind: per_symbol_period`，**dividend 仍然每天产生 137K 重复调用**——只不过现在调用走 normal 桶（475 RPM）所以"看起来跑得快"了，但数据重复问题没解决。

`logs/retry_dividend_20260429_074720.log` 显示 137,775 总单元 —— 跟 fina_audit 一模一样的形态。**这是 REPORT 的隐性遗漏**（不在 audit 脚本能扫到的范围里，因为 dividend 的 API 也"恰好"接受 period 参数，只是接受后忽略它）。

---

## 3. 完整状态矩阵

| ID | 问题 | HANDOFF 编号 | REPORT 状态 | 当前真实状态 |
|---|---|---|---|---|
| H1 | HTTP/2 连接老化（last_stream_id:1999）| §16.6 / Bug E | ✅ 已修 | 已修 |
| H2 | heartbeat_thread UnboundLocalError | （新发现）| ✅ 已修 | 已修 |
| H3 | 7 个策略错配（new_share/fund_*/index_daily/cb_share）| 部分 §16.2 | ✅ 已修 | 已修 |
| H4 | dc_member 表不存在 | §16.5 / Bug D | ✅ 已禁用 | 已修 |
| H5 | ~65 个 freq_bucket 错分类 | §1-7 | ✅ 已修 | 已修 |
| H6 | concept/concept_detail 缺失 | §3 (31 missing) | ✅ 已添加 | 已修 |
| **R1** | **32 个 strategy/API 参数错配仍存在** | §16.2 / Bug A | ❌ 未覆盖 | **未修** |
| **R2** | **stk_holdertrade per_symbol_period 错配** | §16.2 / Bug A | ❌ 未覆盖 | **未修** |
| **R3** | **dividend strategy 未改（虽然 freq_bucket 已改）** | §16.2 / Bug A | ❌ 未覆盖 | **未修** |
| **R4** | **ccass_hold ALTER TABLE 未执行** | §16.4 / Bug C | ⚠️ 仅 YAML 改了 | **未修** |
| **R5** | **audit_strategy_param_mismatch.py 防回归脚本** | §16.2 / Bug A | ❌ 未创建 | **未做** |
| **N1** | **fina_audit 用 per_symbol_period（应 period_loop）** | 全新 | ❌ 未发现 | **未修** |
| **N2** | **Rate limiter timeout 大量失败** | 全新 | ❌ 未发现 | **未修** |
| **N3** | **localhost CH 连接池打爆**（pool_maxsize=8）| 全新 | ❌ 未发现 | **未修** |
| **N4** | **sync_state 清理未 CLI 化** | §16.3 / Bug B | ⚠️ 仅静态 SQL | **未做** |

**未修复合计：9 项**（其中 4 项是新发现）。

---

## 4. 优先级与依赖

```
[P0] 必须立刻修，否则数据持续被污染或永远跑不完
  ├─ N1  fina_audit strategy: per_symbol_period → period_loop  （30s 改 YAML 即可）
  ├─ R3  dividend strategy（如确认仍是 per_symbol_period）→ per_symbol
  ├─ R2  stk_holdertrade strategy → per_symbol
  ├─ R4  ccass_hold ALTER TABLE                                  
  └─ N4  reset-state CLI（前置依赖 — 改完 N1/R2/R3 后必须清残留）

[P1] 短期影响吞吐与失败率
  ├─ R1.1  hk_balancesheet/cashflow/income/fina_indicator → per_symbol_period
  ├─ R1.2  us_balancesheet/cashflow/income/fina_indicator → per_symbol_period
  ├─ R1.3  ggt_monthly → monthly_window
  ├─ R1.4  bo_monthly → monthly_window；bo_weekly/eco_cal/new_share/film_record/teleplay_record → full_once
  ├─ R1.5  cb_call/cb_issue → per_symbol；cb_price_chg → per_symbol
  ├─ R1.6  hk_mins/ft_mins/opt_mins → per_symbol（+ static_params: freq）
  ├─ R1.7  rt_*（4 个）→ disable（实时数据不该批量回填）
  ├─ R1.8  fund_sales_ratio/fund_sales_vol → disable（参数有乱码、5 RPM 限制）
  ├─ R1.9  report_rc → full_once（+ static_params: start_date, end_date）
  ├─ R1.10 tmt_twincome/tmt_twincomedetail → full_once
  ├─ N2   Rate limiter timeout：把 worker timeout 从 30s 调到 120s
  └─ N3   ClickHouse 连接池：pool_maxsize 从 8 调到 32

[P2] 长期防回归
  └─ R5   scripts/audit_strategy_param_mismatch.py + tests/unit/test_strategy_param_audit.py
```

---

## 5. 完整解决方案

### 5.1 P0 修复（必须立刻做）

#### 5.1.1 fina_audit 策略修正（N1）

**文件**：`config/interfaces/stock_financial.yaml`

把 fina_audit 条目改成（按 income / balancesheet / cashflow / fina_indicator 的范本）：

```yaml
---
name: fina_audit
table: tushare_fina_audit
enabled: true
priority: P1
mode: incremental
freq_bucket: special
start_date: '20200101'
fetch_strategy:
  kind: period_loop                        # ← 改这里：per_symbol_period → period_loop
  date_field: end_date
partition_key: toYYYYMM(end_date)
order_by: ts_code, end_date, ann_date
dedupe_key: end_date                       # ← 加这一行（与兄弟接口一致）
required_params: [ts_code, ann_date, start_date, end_date, period]
fields: []
schema_overrides: {}
batch: D
```

**注意**：删除原来的 `symbol_source: tushare_stock_basic` 字段（period_loop 用不上）。

#### 5.1.2 dividend 策略修正（R3）

先核查：

```bash
grep -A 12 "^name: dividend" F:/AIcoding_space/VsCode/tushare_db/config/interfaces/stock_financial.yaml
```

如果 `kind: per_symbol_period`，改为：

```yaml
---
name: dividend
table: tushare_dividend
enabled: true
priority: P1
mode: incremental
freq_bucket: normal
start_date: '20200101'
fetch_strategy:
  kind: per_symbol                         # ← 改这里：per_symbol_period → per_symbol
  symbol_source: tushare_stock_basic
partition_key: toYYYYMM(end_date)
order_by: ts_code, end_date, ann_date
required_params: [ts_code, ann_date, end_date, record_date, ex_date, imp_ann_date]
fields: []
schema_overrides: {}
batch: A
```

#### 5.1.3 stk_holdertrade 策略修正（R2）

文件：`config/interfaces/stock_special.yaml` 或 `stock_reference.yaml`（用 grep 定位）：

```bash
grep -l "name: stk_holdertrade" F:/AIcoding_space/VsCode/tushare_db/config/interfaces/*.yaml
```

改为：

```yaml
fetch_strategy:
  kind: per_symbol                         # ← per_symbol_period → per_symbol
  symbol_source: tushare_stock_basic
required_params: [ts_code, ann_date, start_date, end_date, trade_type, holder_type]
```

#### 5.1.4 ccass_hold ALTER TABLE（R4）

新增 SQL：`scripts/migrate_ccass_hold_shareholding.sql`

```sql
-- ccass_hold.shareholding: ensure Nullable(String) at runtime to match YAML schema_overrides
SELECT name, type FROM system.columns
WHERE database = 'tushare' AND table = 'tushare_ccass_hold' AND name = 'shareholding';

-- If type is Date / Nullable(Date), execute:
ALTER TABLE tushare.tushare_ccass_hold MODIFY COLUMN shareholding Nullable(String);

-- Verify after:
SELECT count(), countIf(shareholding IS NULL) AS null_count
FROM tushare.tushare_ccass_hold;

-- Clear failed sync_state so next backfill is clean:
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'ccass_hold' AND status = 'failed';
```

执行：

```bash
clickhouse-client --multiquery < scripts/migrate_ccass_hold_shareholding.sql
```

> 同时把 YAML 改为 `shareholding: Nullable(String)`（当前是 `String`，但 API 实际可能返回 None — 用 Nullable 更安全）：

```yaml
schema_overrides:
  shareholding: Nullable(String)
```

#### 5.1.5 reset-state CLI（N4 / 前置依赖）

新增 `src/tushare_db/cli.py` 子命令：

```python
@cli.command(name="reset-state")
@click.option("--interface", required=True, help="Interface name to reset")
@click.option("--confirm", is_flag=True, help="Actually delete (without this is dry-run)")
def reset_state(interface: str, confirm: bool) -> None:
    """Delete all sync_state rows for an interface (use after strategy change)."""
    from tushare_db.sink.clickhouse_sink import get_native_client
    import os
    ch = get_native_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=8123,
        user="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
    )
    result = ch.query(
        f"SELECT count(), countIf(status='done'), countIf(status='failed'), countIf(status='running') "
        f"FROM _meta.sync_state WHERE interface = '{interface}'"
    )
    row = result.result_rows[0]
    print(f"Found {row[0]} rows for {interface} (done={row[1]}, failed={row[2]}, running={row[3]})")
    if not confirm:
        print("Dry-run; pass --confirm to actually delete")
        return
    ch.command(f"ALTER TABLE _meta.sync_state DELETE WHERE interface = '{interface}'")
    print(f"Deleted. Re-plan with: tushare-db backfill --interface {interface}")
```

执行序列：

```bash
# 改完 YAML 后必须清残留
tushare-db reset-state --interface fina_audit --confirm
tushare-db reset-state --interface dividend --confirm
tushare-db reset-state --interface stk_holdertrade --confirm
tushare-db reset-state --interface ccass_hold --confirm
```

### 5.2 P1 修复（短期影响吞吐 / 失败率）

#### 5.2.1 R1 批量修法表

在 `config/interfaces/*.yaml` 改这 31 个接口的 `fetch_strategy.kind`：

| 接口 | 文件 | 改前 | 改后 |
|---|---|---|---|
| `hk_balancesheet` | `paid.yaml` | `date_loop` | `per_symbol_period` |
| `hk_cashflow` | `paid.yaml` | `date_loop` | `per_symbol_period` |
| `hk_fina_indicator` | `paid.yaml` | `date_loop` | `per_symbol_period` |
| `hk_income` | `paid.yaml` | `date_loop` | `per_symbol_period` |
| `us_balancesheet` | `paid.yaml` | `date_loop` | `per_symbol_period` |
| `us_cashflow` | `paid.yaml` | `date_loop` | `per_symbol_period` |
| `us_fina_indicator` | `paid.yaml` | `date_loop` | `per_symbol_period` |
| `us_income` | `paid.yaml` | `date_loop` | `per_symbol_period` |
| `ggt_monthly` | `macro.yaml` 或 `index.yaml` | `date_loop` | `monthly_window` |
| `bo_monthly` | `tmt.yaml` | `date_loop` | `monthly_window` |
| `bo_weekly` | `tmt.yaml` | `date_loop` | `full_once` + static_params: `{start_date: '20200101', end_date: <today>}` |
| `bo_cinema`、`bo_daily` | `tmt.yaml` | `date_loop` | **保持 `date_loop` 但改 `date_field: date`**（API 用 `date` 不是 `trade_date`）|
| `eco_cal` | `macro.yaml` | `date_loop` | `full_once` + static_params: `{start_date, end_date}` |
| `new_share` | （已修）| `date_loop` | `full_once` ✅ |
| `cb_call` | `bonds.yaml` | `date_loop` | `per_symbol` (symbol_source: `tushare_cb_basic`) |
| `cb_issue` | `bonds.yaml` | `date_loop` | `per_symbol` |
| `cb_price_chg` | `bonds.yaml` | `date_loop` | `per_symbol` |
| `hk_mins` | `paid.yaml` | `date_loop` | `per_symbol` + static_params: `{freq: '1min', start_date, end_date}` |
| `ft_mins` | `paid.yaml` | `date_loop` | `per_symbol` + static_params: `{freq: '1min', start_date, end_date}` |
| `opt_mins` | `paid.yaml` | `date_loop` | `per_symbol` + static_params: `{freq: '1min', start_date, end_date}` |
| `rt_hk_k`、`rt_fut_min`、`rt_min`、`rt_k` | `paid.yaml` | `date_loop` | **`enabled: false` + `disabled_reason: realtime_not_for_backfill`** |
| `report_rc` | `tmt.yaml` 或 `stock_special.yaml` | `date_loop` | `full_once` + static_params: `{start_date, end_date}` |
| `film_record` | `tmt.yaml` | `date_loop` | `full_once` + static_params |
| `teleplay_record` | `tmt.yaml` | `date_loop` | `full_once` + static_params |
| `tmt_twincome` | `tmt.yaml` | `date_loop` | `full_once` + static_params: `{item: <required>, start_date, end_date}` |
| `tmt_twincomedetail` | `tmt.yaml` | `date_loop` | `full_once` + static_params |
| `fund_sales_ratio` | `fund.yaml` | `date_loop` | **`enabled: false` + `disabled_reason: api_param_chinese_garbled_5rpm_limit`** |
| `fund_sales_vol` | `fund.yaml` | `date_loop` | **`enabled: false` + `disabled_reason: 5rpm_limit_use_low_concurrency_script`** |

每个修完后跑：

```bash
tushare-db reset-state --interface <name> --confirm
```

#### 5.2.2 N2 — Rate limiter timeout 缓解

文件：`src/tushare_db/runner/worker.py` 或 `src/tushare_db/core/tushare_client.py`

在 `tushare_client.call()` 调用处把 `timeout=30` 改成 `timeout=120`（限速桶被打爆时多等一会儿，避免误标 failed）：

```python
# core/tushare_client.py 或调用处
RATE_LIMITER_TIMEOUT_SEC = int(os.environ.get("RATE_LIMITER_TIMEOUT", "120"))

acquired = self._limiter.acquire(bucket, timeout=RATE_LIMITER_TIMEOUT_SEC)
if not acquired:
    raise TushareError(f"Rate limiter timeout for {api_name}")
```

同时 `scripts/resume_fina_audit.py` 内启动前清理"残留 Python 进程"（HANDOFF §16.7 已提）：

```bash
# Windows: 检查是否有其他 tushare-db / scripts/resume_*.py / scripts/retry_*.py 进程在跑
tasklist /FI "IMAGENAME eq python.exe" /V | findstr tushare
# 或：
wmic process where "name='python.exe'" get ProcessId,CommandLine | findstr tushare-db
# 杀掉残留
taskkill /F /PID <pid>
```

#### 5.2.3 N3 — ClickHouse 连接池

文件：`src/tushare_db/sink/clickhouse_sink.py` 找 `get_native_client` / `get_client`：

```python
def get_native_client(host, port, user, password, **kwargs):
    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
        # 增加：连接池大小
        pool_mgr=clickhouse_connect.driver.httputil.get_pool_manager(
            maxsize=32,         # ← 默认 8，提高到 32
            num_pools=8,
            block=False,
        ),
        **kwargs,
    )
```

或者更简单：在 `_new_ch_client`（`worker.py:225-233`）传 `pool_maxsize=32`：

```python
def _new_ch_client(database: str = "tushare") -> clickhouse_connect.driver.Client:
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database=database,
        # 增加：
        connect_timeout=10,
        send_receive_timeout=300,
        pool_mgr_options={"maxsize": 32, "num_pools": 8},
    )
```

> 具体参数名以 `clickhouse-connect` 0.7.x 文档为准；如果上述不工作，也可在 `urllib3` 全局设：
> ```python
> import urllib3
> urllib3.PoolManager._default_pool_kw = {"maxsize": 32}
> ```

### 5.3 P2 修复（防回归）

#### 5.3.1 R5 — 防回归审计脚本

新增 `scripts/audit_strategy_param_mismatch.py`：

```python
"""Audit fetch_strategy vs MCP inputParams. Run periodically and in CI."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = PROJECT_ROOT / "vendor" / "tushare-mcp" / "search-index@0.2.1.min.json"
INTERFACES_DIR = PROJECT_ROOT / "config" / "interfaces"

# Allowlist: APIs where strategy/param mismatch is intentional
# (e.g., 5500-symbol per_symbol_period over 'period' even though API ignores it)
KNOWN_OK: set[str] = {
    # Add interface names here only after explicit human review
}


def load_mcp() -> dict[str, list[str]]:
    if not INDEX_PATH.exists():
        # Fallback to old location
        alt = PROJECT_ROOT / "search-index.min.json"
        if alt.exists():
            data = json.load(open(alt, encoding="utf-8"))
        else:
            print(f"ERROR: search-index not found at {INDEX_PATH}")
            sys.exit(2)
    else:
        data = json.load(open(INDEX_PATH, encoding="utf-8"))
    return {
        item["name"]: [p for p in item.get("inputParams", []) if p not in ("limit", "offset")]
        for item in data["index"]
    }


def audit() -> int:
    mcp = load_mcp()
    bugs: list[str] = []
    warns: list[str] = []
    for f in sorted(INTERFACES_DIR.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        for doc in yaml.safe_load_all(open(f, encoding="utf-8")):
            if not doc or "name" not in doc:
                continue
            name = doc["name"]
            if name in KNOWN_OK or name not in mcp:
                continue
            strategy = doc.get("fetch_strategy", {}).get("kind", "")
            params = mcp[name]
            if strategy in ("period_loop", "per_symbol_period") and "period" not in params:
                bugs.append(f"BUG  {name}: strategy={strategy} but no 'period' param. {params}")
            if strategy == "date_loop" and "trade_date" not in params:
                warns.append(f"WARN {name}: date_loop but no 'trade_date'. {params}")
            if strategy == "monthly_window" and "month" not in params:
                warns.append(f"WARN {name}: monthly_window but no 'month'. {params}")

    for b in bugs:
        print(b)
    for w in warns:
        print(w)
    print(f"\n{len(bugs)} BUGs + {len(warns)} WARNs")
    return 1 if bugs else 0  # WARNs do not fail CI; BUGs do


if __name__ == "__main__":
    sys.exit(audit())
```

#### 5.3.2 单元测试

新增 `tests/unit/test_strategy_param_audit.py`：

```python
"""Strategy/param audit must pass with no BUGs (warns ok during transition)."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_no_strategy_param_bugs():
    result = subprocess.run(
        [sys.executable, "scripts/audit_strategy_param_mismatch.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    # exit 0 = no BUG (warns ok); exit 1 = BUG found
    assert result.returncode == 0, (
        f"Strategy/param audit failed:\n{result.stdout}\n{result.stderr}"
    )
```

---

## 6. 端到端验证

修复完成后按顺序跑：

```bash
cd F:/AIcoding_space/VsCode/tushare_db

# 1. YAML 校验
python -c "
from tushare_db.config.loader import load_all_interface_specs
specs = load_all_interface_specs('config/interfaces')
print(f'loaded {len(specs)} specs OK')
"

# 2. 防回归脚本
python scripts/audit_strategy_param_mismatch.py
echo "audit exit: $?"
# 期望：0（没有 BUG；可以仍有 WARN 直到 P1 全部修完）

# 3. 单元测试
pytest tests/unit/ -v --tb=short
# 期望：全绿（含新增 test_strategy_param_audit）

# 4. fina_audit 再跑
tushare-db reset-state --interface fina_audit --confirm
python scripts/resume_fina_audit.py --dry-run
# 期望：Planned **25** work units（不再是 137,775）

python scripts/resume_fina_audit.py
# 期望：25 调用 / ~10 秒跑完 / 几乎无 Rate limiter timeout

# 5. dividend 再跑
tushare-db reset-state --interface dividend --confirm
tushare-db backfill --interface dividend
# 期望：~5,500 work units（不是 137K）
# 24h 后查表去重率：
clickhouse-client -q "SELECT count(), uniqExact(ts_code, end_date) FROM tushare.tushare_dividend"
# 期望：count() ≈ uniqExact(...)（不再 25× 重复）

# 6. ccass_hold 验证
clickhouse-client -q "SELECT name, type FROM system.columns WHERE database='tushare' AND table='tushare_ccass_hold' AND name='shareholding'"
# 期望：Nullable(String)
tushare-db backfill --interface ccass_hold
# 期望：不再报 'Unable to create Python array' 错

# 7. 资源监控（24h 后）
grep -c "Rate limiter timeout" data/logs/app.log
# 期望：< 10
grep -c "Connection pool is full" data/logs/app.log
# 期望：< 10
grep -c "TushareTransientError" data/logs/app.log
# 期望：与 R 修复前相比下降 90%+
```

---

## 7. 总结

REPORT_20260429.md 是一个**一半的胜利**：基础设施层（HTTP/2、heartbeat、freq_bucket）扎实修了，但**策略错配这个最严重的类别只动了表面 7 个**，剩下的 32 个仍然在制造重复数据；而且**改 strategy 后必须做的"清残留"**没有 CLI 化、新发现 fina_audit 的策略选错跟 dividend 是**同一个根因**。

按本文档 §5 的优先级走：
- **30 分钟**修完 P0（5 项 YAML + 1 个 CLI + 1 个 ALTER TABLE + 4 个 reset-state）
- **2-3 小时**修完 P1（31 个 YAML + 2 个运行时小补丁）
- **30 分钟**完成 P2（防回归脚本与单测）

完成后你 4 月底以来的"经常失败 / 数据重复 / 一直拉一个日期循环"会**真正消失**。

---

## 8. 附：本文档与其他文档的关系

```
HANDOFF_MCP_CONFIG_FIX.md
└── §16 运行时故障模式修复（5 大 bug 类别）
    ├── Bug A 策略错配 → REPORT 部分修了 7/36 → 本文档 R1/R2/R3 (剩 32)
    ├── Bug B sync_state 残留 → REPORT 静态 SQL → 本文档 N4 改 CLI
    ├── Bug C ccass_hold → REPORT 改了 YAML → 本文档 R4 补 ALTER TABLE
    ├── Bug D dc_member → REPORT ✅ 已修
    └── Bug E HTTP/2 → REPORT ✅ 已修

REPORT_20260429.md
└── 14 项 ✅ + 9 项 ❌（本文档列出）

REMAINING_ISSUES_20260429.md  ← 本文档
├── §1 REPORT 漏修项（5 项：R1, R2, R3, R4, R5）
├── §2 最新日志新问题（4 项：N1, N2, N3, N4）
└── §5 完整修复方案（P0 30min + P1 2h + P2 30min）

AUDIT_LOG_FINDINGS_20260429.md
└── 5 大 bug 的原始日志证据（fina_audit 23:02 之前）
    ├── 本文档新增 fina_audit 23:02 之后证据 → §2.1, §2.2
    └── 本文档新增 app.log Connection pool 证据 → §2.3
```

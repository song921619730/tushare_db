# 根因分析 — 2026-04-30

## 一、Schema 缺失列（1,213 个失败）

### 涉及接口
- `moneyflow_ths` — 缺失 `name` 列（431 个失败）
- `moneyflow_cnt_ths` — 缺失 `lead_stock` 列（391 个失败）
- `moneyflow_ind_ths` — 缺失 `industry` 列（391 个失败）

### 根因
**Schema 演进代码存在但未接线。**

数据流：`worker.py:execute_unit()` → `_normalize_items()` → `insert_with_version()` → `clickhouse_sink.insert_rows()` → `client.insert()`

当 ClickHouse 返回 `Unrecognized column 'name'` 错误时，`worker.py:370-373` 的 catch-all 异常处理器只做了 `mark_failed()` 就退出了：

```python
except Exception as e:
    mark_failed(ch_client, unit, str(e), attempt)
    return -4
```

**缺失的环节**：没有代码在 "Unrecognized column" 错误时触发 `evolve_schema()` 自动添加列。

### 代码状态
| 组件 | 文件 | 状态 |
|------|------|------|
| `evolve_schema()` | `src/tushare_db/schema/evolver.py:44` | 已实现，从未被调用 |
| `invalidate_column_cache()` | `src/tushare_db/runner/worker.py:381` | 已实现，仅由 evolver 调用 |
| `insert_with_version()` | `src/tushare_db/sink/clickhouse_sink.py:95` | 不做错误处理，不触发演进 |
| `execute_unit()` | `src/tushare_db/runner/worker.py:238` | 统一 catch，不区分错误类型 |

### 附加说明
这三个接口在 config 中已经 `enabled: false`，说明之前尝试过同步但因 API 返回 0 行被禁用了。失败记录是之前运行留下的。表已经存在但 schema 不包含这些列，需要手动 `ALTER TABLE ADD COLUMN`。

---

## 二、`per_symbol` 策略未注册（587 个失败）

### 根因
**Scheduler 容器运行的是旧版代码，不包含 `per_symbol` 策略分支。**

本地代码（`src/tushare_db/planner/planner.py`）的策略分发：
```
full_once → date_loop/offset_paging → period_loop → monthly_window → per_symbol → per_symbol_period
```

容器内运行的代码的策略分发（通过 `inspect.getsource` 确认）：
```
full_once → date_loop/offset_paging → period_loop → monthly_window → per_symbol_period
```

**`per_symbol` 分支在容器中被跳过**，直接落到 `raise ValueError("Unknown strategy: per_symbol")`。

### 修复方案
重建并重启 `pipeline-scheduler` 容器。本地代码已经正确处理了 `per_symbol`。

### 附加发现
`config/interfaces/_schema.yaml` 第 12 行的 `kind` 枚举中缺少 `per_symbol`：
```yaml
kind: full_once|date_loop|period_loop|monthly_window|per_symbol_period|offset_paging
#                                                                 ^^^^^^^^ 缺少 per_symbol
```

---

## 三、日期列序列化错误（`stk_managers`, `fund_company`）

### 涉及接口
| 接口 | 错误列 | 表中类型 |
|------|--------|----------|
| `stk_managers` | `begin_date` | `Date` |
| `fund_company` | `setup_date`, `end_date` | `Date` |

### 错误信息
```
TypeError: unsupported operand type(s) for -: 'str' and 'datetime.date'
```

### 根因分析

`_normalize_items()` (worker.py:428) 通过两个来源识别日期列：

1. **类型匹配**（worker.py:440-448）：查询 `system.columns` 获取 ClickHouse 类型，如果是 `Date` 则加入 `date_type_indices`
2. **名称启发**（worker.py:451）：列名包含 "date" 则加入 `name_date_indices`

**但问题在于**：`_normalize_items` 被调用时传入的 `column_types` 是从 `_get_column_types(ch_client, unit.table)` 获取的。

经核实，`stk_managers` 的 `begin_date` 列在 ClickHouse 中确实是 `Date` 类型，`_get_column_types` 会正确返回 `{"begin_date": "Date", ...}`。因此 `_parse_date_string()` 会被调用。

**然而错误仍然发生**，说明 ClickHouse 的 `client.insert()` 在序列化时仍然收到了字符串。最可能的原因：

1. `_parse_date_string()` 对某些日期格式抛出 `ValueError`，被 catch 后设为 `None`（worker.py:474）
2. 但 `None` 值传入 ClickHouse `Date` 列（非 Nullable）时也会失败
3. **另一种可能**：容器运行的 `_normalize_items` 代码比本地旧，还没有完整的日期处理逻辑

### 验证
Scheduler 容器运行的是旧版代码（per_symbol 缺失证明），很可能 `_normalize_items` 也是旧版，缺乏完整的日期字符串解析逻辑。

---

## 四、Nullable 列 None 值错误（2 个失败）

### 涉及接口
| 接口 | 错误列 | 表定义 |
|------|--------|--------|
| `etf_index` | `pub_date` | `Date` (非 Nullable) |
| `index_basic` | `base_date` | `Date` (非 Nullable) |

### 错误信息
```
Unable to create Python array for source column `pub_date`.
This is usually caused by trying to insert None values into a ClickHouse column that is not Nullable
```

### 根因

`_normalize_items()` 的步骤 3（worker.py:536-559）会为**非 Nullable 列**的 None 值填充默认值：
- `String` → `""`
- `Int/Decimal` → `0`
- `Date` → `_EPOCH_DATE` (1970-01-01)

但步骤 1c（worker.py:505-522）会将 **1970 年之前的日期**设为 `None`（如果是 Nullable）或 `_EPOCH_DATE`（如果是非 Nullable）。

**问题在于步骤顺序**：
1. 步骤 1：日期解析 → 可能产生 `None`（无法解析的字符串）
2. 步骤 1c：pre-1970 处理 → 可能产生 `None`（Nullable 列）或 `_EPOCH_DATE`（非 Nullable）
3. 步骤 3：填充默认值 → **会处理步骤 1 和 1c 产生的 `None`**

对于非 Nullable 的 Date 列，如果 API 返回空字符串，步骤 1 解析失败设为 `None`，然后步骤 3 应该填充 `_EPOCH_DATE`。

**但如果 API 返回的日期字符串解析后早于 1970 年**（步骤 1c 处理），对于非 Nullable Date 列会被设为 `_EPOCH_DATE`，这应该是正确的。

**真正的问题**：API 可能返回了既不是有效日期也不是空值的异常数据（如 `"-"`、`"null"` 等字符串），`_parse_date_string` 抛出异常后设为 `None`，但步骤 3 的 Date 默认值填充逻辑可能被跳过了。

经检查 worker.py:558-559：
```python
elif base_type == "Date":
    row[idx] = _EPOCH_DATE
```

这段代码在步骤 3 中，但前提是 `val is not None` 的 continue 之后才会执行。

等等，让我重新看逻辑（worker.py:536-559）：
```python
for idx, field_name in enumerate(fields):
    ...
    ch_type = column_types.get(field_name, "")
    if not ch_type or ch_type.startswith("Nullable("):
        continue                    # ← Nullable 列跳过
    val = row[idx]
    if isinstance(val, str) and not val.strip():
        row[idx] = None
        val = None
    if val is not None:
        continue                    # ← 非 None 值跳过
    # 到这里说明是 None，填充默认值
    if base_type == "Date":
        row[idx] = _EPOCH_DATE      # ← 应该会执行
```

逻辑看起来正确。那问题出在哪里？

**可能原因**：容器运行的 `_normalize_items` 是旧版代码，步骤 3 可能不存在或不完整。需要重建容器验证。

---

## 五、fina_audit SSL 超时（67 个失败）

### 根因
Tushare Pro API 在高并发调用时 SSL 握手超时。这是网络层面的问题。

当前 TushareClient 使用：
- `httpx.Client(http2=True, timeout=10s)` — 超时设置为 10 秒
- tenacity 重试：最多 4 次，指数退避（1s-30s）
- 限速器：normal 475 RPM, special 285 RPM

**但 `fina_audit` 使用 `per_symbol` 策略**，需要为每只股票调用 API，调用密集度高。

10 秒超时对于某些 SSL 握手可能不够，尤其在网络拥塞时。

### 修复方案
增加 `fina_audit` 接口的超时时间（配置 `timeout: 30` 或更高），并降低调用频率。

---

## 六、33 个仅 1 行的表

### 根因
这些表在 `bootstrap` 阶段通过 API 采样创建了表结构（仅有 1 条采样数据），但 **backfill 从未成功执行**：

1. 部分接口（如 `moneyflow_ths`）因 API 返回 0 行被标记 `enabled: false`
2. 部分接口（如美股系列）的 backfill 可能因策略或参数问题未执行
3. 部分参考表（如 `index_classify`, `bse_mapping`）的 backfill 策略是 `full_once`，但可能因 API 调用失败中断

### 验证方法
检查 `_meta.sync_state` 中这些接口对应的 scope 状态。

---

## 总结：需要做的修复

| # | 修复项 | 影响范围 | 复杂度 |
|---|--------|----------|--------|
| 1 | 在 `execute_unit` 中接入 schema 演进：捕获 "Unrecognized column" 错误 → `evolve_schema` → 重试 insert | 1,213 个失败 + 未来防护 | 中 |
| 2 | 重建 pipeline-scheduler 容器镜像（包含 `per_symbol` 策略和最新版 `_normalize_items`） | 587 + 2 + 2 个失败 | 低 |
| 3 | 修复 `_schema.yaml` 枚举，添加 `per_symbol` | 配置一致性 | 低 |
| 4 | 对 `etf_index`/`index_basic` 执行 `ALTER TABLE MODIFY COLUMN ... Nullable(Date)` | 2 个失败 | 低 |
| 5 | 对 `moneyflow_*` 表执行 `ALTER TABLE ADD COLUMN` 补全缺失列 | 1,213 个失败 | 低 |
| 6 | 增加 `fina_audit` 超时配置 + 限速 | 67 个失败 | 低 |
| 7 | 排查 33 个仅 1 行表的 backfill 历史，逐个修复 | 33 个接口 | 高 |
| 8 | 处理 587 个空的 `fina_audit` 失败（per_symbol 策略修复后 resume 即可） | 587 个失败 | 低 |

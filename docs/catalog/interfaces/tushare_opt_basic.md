# opt_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | opt_basic |
| 表名 | `tushare_opt_basic` |
| 优先级 | P2 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 24,438 |

## 字段列表 (19 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |
| 2 | `opt_code` | String |  |

### 日期 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `maturity_date` | Date |  |
| 2 | `list_date` | Date |  |
| 3 | `delist_date` | Date |  |
| 4 | `last_edate` | Date |  |
| 5 | `last_ddate` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (11个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `exchange` | LowCardinality(String) |  |
| 2 | `name` | LowCardinality(String) |  |
| 3 | `per_unit` | Float64 |  |
| 4 | `opt_type` | String |  |
| 5 | `call_put` | String |  |
| 6 | `exercise_type` | String |  |
| 7 | `exercise_price` | Float64 |  |
| 8 | `s_month` | String |  |
| 9 | `list_price` | Float64 |  |
| 10 | `quote_unit` | String |  |
| 11 | `min_price_chg` | String |  |

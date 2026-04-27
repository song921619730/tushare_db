# fx_obasic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fx_obasic |
| 表名 | `tushare_fx_obasic` |
| 优先级 | P3 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | toYYYYMM(trade_date) |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 138 |

## 字段列表 (13 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (11个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `classify` | String |  |
| 3 | `exchange` | LowCardinality(String) |  |
| 4 | `min_unit` | Float64 |  |
| 5 | `max_unit` | Float64 |  |
| 6 | `pip` | Float64 |  |
| 7 | `pip_cost` | Decimal(18, 2) |  |
| 8 | `traget_spread` | Float64 |  |
| 9 | `min_stop_distance` | Float64 |  |
| 10 | `trading_hours` | String |  |
| 11 | `break_time` | String |  |

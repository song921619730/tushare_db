# bak_daily

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | bak_daily |
| 表名 | `tushare_bak_daily` |
| 优先级 | P3 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | A |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 5,517 |

## 字段列表 (32 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 估值指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pe` | Float64 |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Float64 |  |
| 2 | `amount` | Float64 |  |

### 股本/市值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_share` | Decimal(18, 4) |  |
| 2 | `float_share` | Decimal(18, 4) |  |
| 3 | `float_mv` | Decimal(18, 2) |  |
| 4 | `total_mv` | Decimal(18, 2) |  |

### 比率/率 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol_ratio` | Float64 |  |

### 数值 (21个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `pct_change` | Float64 |  |
| 3 | `close` | Float64 |  |
| 4 | `change` | Float64 |  |
| 5 | `open` | Float64 |  |
| 6 | `high` | Float64 |  |
| 7 | `low` | Float64 |  |
| 8 | `pre_close` | Float64 |  |
| 9 | `turn_over` | Float64 |  |
| 10 | `swing` | Float64 |  |
| 11 | `selling` | Float64 |  |
| 12 | `buying` | Float64 |  |
| 13 | `industry` | LowCardinality(String) |  |
| 14 | `area` | LowCardinality(String) |  |
| 15 | `avg_price` | Float64 |  |
| 16 | `strength` | Float64 |  |
| 17 | `activity` | Float64 |  |
| 18 | `avg_turnover` | Float64 |  |
| 19 | `attack` | Float64 |  |
| 20 | `interval_3` | String |  |
| 21 | `interval_6` | String |  |

# opt_daily

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | opt_daily |
| 表名 | `tushare_opt_daily` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | normal |
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
| 行数 | 15,000 |

## 字段列表 (14 个字段)

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

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Float64 |  |
| 2 | `amount` | Float64 |  |

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `exchange` | LowCardinality(String) |  |
| 2 | `pre_settle` | Float64 |  |
| 3 | `pre_close` | Float64 |  |
| 4 | `open` | Float64 |  |
| 5 | `high` | Float64 |  |
| 6 | `low` | Float64 |  |
| 7 | `close` | Float64 |  |
| 8 | `settle` | Float64 |  |
| 9 | `oi` | Float64 |  |

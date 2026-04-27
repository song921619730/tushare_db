# ths_daily

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ths_daily |
| 表名 | `tushare_ths_daily` |
| 优先级 | P1 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | C |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 229,232 |

## 字段列表 (13 个字段)

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
| 2 | `turnover_rate` | Float64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `open` | Float64 |  |
| 2 | `high` | Float64 |  |
| 3 | `low` | Float64 |  |
| 4 | `close` | Float64 |  |
| 5 | `pre_close` | Float64 |  |
| 6 | `avg_price` | Float64 |  |
| 7 | `change` | Float64 |  |
| 8 | `pct_change` | Float64 |  |

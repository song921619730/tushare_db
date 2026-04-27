# sge_daily

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | sge_daily |
| 表名 | `tushare_sge_daily` |
| 优先级 | P3 |
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
| 行数 | 14,041 |

## 字段列表 (15 个字段)

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
| 1 | `vol` | Nullable(Float64) |  |
| 2 | `amount` | Nullable(Float64) |  |

### 数值 (10个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `close` | Nullable(Float64) |  |
| 2 | `open` | Nullable(Float64) |  |
| 3 | `high` | Nullable(Float64) |  |
| 4 | `low` | Nullable(Float64) |  |
| 5 | `price_avg` | Nullable(Float64) |  |
| 6 | `change` | Nullable(Float64) |  |
| 7 | `pct_change` | Nullable(Float64) |  |
| 8 | `oi` | Nullable(Float64) |  |
| 9 | `settle_vol` | Nullable(Float64) |  |
| 10 | `settle_dire` | String |  |

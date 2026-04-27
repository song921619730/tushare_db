# fx_daily

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fx_daily |
| 表名 | `tushare_fx_daily` |
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
| 行数 | 28,000 |

## 字段列表 (12 个字段)

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

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `bid_open` | Float64 |  |
| 2 | `bid_close` | Float64 |  |
| 3 | `bid_high` | Float64 |  |
| 4 | `bid_low` | Float64 |  |
| 5 | `ask_open` | Float64 |  |
| 6 | `ask_close` | Float64 |  |
| 7 | `ask_high` | Float64 |  |
| 8 | `ask_low` | Float64 |  |
| 9 | `tick_qty` | Int64 |  |

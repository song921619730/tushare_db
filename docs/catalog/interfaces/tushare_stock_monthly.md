# stock_monthly

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | monthly |
| 表名 | `tushare_stock_monthly` |
| 优先级 | P1 |
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
| 行数 | 357,979 |

## 字段列表 (14 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | String |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |
| 2 | `switch_date` | Nullable(Date) |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Nullable(Float64) |  |
| 2 | `amount` | Nullable(Float64) |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_return` | Nullable(Float64) |  |

### 数值 (7个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `open` | Nullable(Float64) |  |
| 2 | `high` | Nullable(Float64) |  |
| 3 | `low` | Nullable(Float64) |  |
| 4 | `close` | Nullable(Float64) |  |
| 5 | `pct_chg` | Nullable(Float64) |  |
| 6 | `turnover` | Nullable(Float64) |  |
| 7 | `accumulated_nav` | Nullable(Float64) |  |

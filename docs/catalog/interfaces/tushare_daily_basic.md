# daily_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | daily_basic |
| 表名 | `tushare_daily_basic` |
| 优先级 | P0 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | B |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 11,926,529 |

## 字段列表 (19 个字段)

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

### 估值指标 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pe` | Nullable(Float64) |  |
| 2 | `pb` | Nullable(Float64) |  |
| 3 | `ps` | Nullable(Float64) |  |
| 4 | `dv_ratio` | Nullable(Float64) |  |
| 5 | `dv_ttm` | Nullable(Float64) |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `turnover_rate` | Nullable(Float64) |  |
| 2 | `volume_ratio` | Nullable(Float64) |  |

### 股本/市值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_share` | Decimal(18, 4) |  |
| 2 | `float_share` | Decimal(18, 4) |  |
| 3 | `free_share` | Decimal(18, 4) |  |
| 4 | `total_mv` | Decimal(18, 2) |  |
| 5 | `circ_mv` | Decimal(18, 2) |  |

### 数值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `close` | Float64 |  |
| 2 | `turnover_rate_f` | Nullable(Float64) |  |
| 3 | `pe_ttm` | Nullable(Float64) |  |
| 4 | `ps_ttm` | Nullable(Float64) |  |

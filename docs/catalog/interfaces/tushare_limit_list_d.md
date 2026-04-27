# limit_list_d

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | limit_list_d |
| 表名 | `tushare_limit_list_d` |
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
| 行数 | 153,233 |

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

### 成交量/额 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `amount` | Float64 |  |

### 股本/市值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `float_mv` | Nullable(Decimal(18, 2)) |  |
| 2 | `total_mv` | Nullable(Decimal(18, 2)) |  |

### 比率/率 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `turnover_ratio` | Float64 |  |

### 数值 (12个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `industry` | Nullable(String) |  |
| 2 | `name` | Nullable(String) |  |
| 3 | `close` | Float64 |  |
| 4 | `pct_chg` | Float64 |  |
| 5 | `limit_amount` | Nullable(Decimal(18, 2)) |  |
| 6 | `fd_amount` | Nullable(Decimal(18, 2)) |  |
| 7 | `first_time` | Nullable(String) |  |
| 8 | `last_time` | Nullable(String) |  |
| 9 | `open_times` | Int64 |  |
| 10 | `up_stat` | Nullable(String) |  |
| 11 | `limit_times` | Int64 |  |
| 12 | `limit` | Nullable(String) |  |

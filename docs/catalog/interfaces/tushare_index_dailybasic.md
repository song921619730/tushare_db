# index_dailybasic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | index_dailybasic |
| 表名 | `tushare_index_dailybasic` |
| 优先级 | P1 |
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
| 行数 | 12 |

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

### 估值指标 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pe` | Float64 |  |
| 2 | `pb` | Float64 |  |

### 成交量/额 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `turnover_rate` | Float64 |  |

### 股本/市值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_mv` | Decimal(18, 2) |  |
| 2 | `float_mv` | Decimal(18, 2) |  |
| 3 | `total_share` | Decimal(18, 4) |  |
| 4 | `float_share` | Decimal(18, 4) |  |
| 5 | `free_share` | Decimal(18, 4) |  |

### 数值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `turnover_rate_f` | Float64 |  |
| 2 | `pe_ttm` | Float64 |  |

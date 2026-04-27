# daily_info

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | daily_info |
| 表名 | `tushare_daily_info` |
| 优先级 | P2 |
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

### 估值指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pe` | Float64 |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `amount` | Float64 |  |
| 2 | `vol` | Float64 |  |

### 股本/市值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_share` | Decimal(18, 4) |  |
| 2 | `float_share` | Decimal(18, 4) |  |
| 3 | `total_mv` | Decimal(18, 2) |  |
| 4 | `float_mv` | Decimal(18, 2) |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_name` | String |  |
| 2 | `com_count` | Int64 |  |
| 3 | `trans_count` | String |  |
| 4 | `tr` | Float64 |  |
| 5 | `exchange` | LowCardinality(String) |  |

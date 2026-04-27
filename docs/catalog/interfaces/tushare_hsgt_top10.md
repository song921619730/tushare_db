# hsgt_top10

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | hsgt_top10 |
| 表名 | `tushare_hsgt_top10` |
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
| 行数 | 20 |

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

### 成交量/额 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `amount` | Float64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `close` | Float64 |  |
| 3 | `change` | Float64 |  |
| 4 | `rank` | Int64 |  |
| 5 | `market_type` | Int64 |  |
| 6 | `net_amount` | Decimal(18, 2) |  |
| 7 | `buy` | Float64 |  |
| 8 | `sell` | Float64 |  |

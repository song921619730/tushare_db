# ggt_top10

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ggt_top10 |
| 表名 | `tushare_ggt_top10` |
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
| 行数 | 13 |

## 字段列表 (18 个字段)

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
| 1 | `amount` | String |  |

### 数值 (14个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `close` | Float64 |  |
| 3 | `p_change` | Float64 |  |
| 4 | `rank` | Int64 |  |
| 5 | `market_type` | Int64 |  |
| 6 | `net_amount` | Decimal(18, 2) |  |
| 7 | `sh_amount` | Decimal(18, 2) |  |
| 8 | `sh_net_amount` | Decimal(18, 2) |  |
| 9 | `sh_buy` | Float64 |  |
| 10 | `sh_sell` | Float64 |  |
| 11 | `sz_amount` | Decimal(18, 2) |  |
| 12 | `sz_net_amount` | Decimal(18, 2) |  |
| 13 | `sz_buy` | Float64 |  |
| 14 | `sz_sell` | Float64 |  |

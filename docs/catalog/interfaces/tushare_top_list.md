# top_list

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | top_list |
| 表名 | `tushare_top_list` |
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
| 行数 | 96,885 |

## 字段列表 (16 个字段)

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
| 1 | `turnover_rate` | Float64 |  |
| 2 | `amount` | Float64 |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `float_values` | Float64 |  |

### 数值 (10个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `close` | Float64 |  |
| 3 | `pct_change` | Float64 |  |
| 4 | `l_sell` | Float64 |  |
| 5 | `l_buy` | Float64 |  |
| 6 | `l_amount` | Decimal(18, 2) |  |
| 7 | `net_amount` | Decimal(18, 2) |  |
| 8 | `net_rate` | Float64 |  |
| 9 | `amount_rate` | Float64 |  |
| 10 | `reason` | String |  |

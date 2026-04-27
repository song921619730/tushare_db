# limit_list_ths

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | limit_list_ths |
| 表名 | `tushare_limit_list_ths` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | C |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20231101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 68 |

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
| 1 | `turnover_rate` | Float64 |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `free_float` | Float64 |  |

### 数值 (14个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `price` | Float64 |  |
| 3 | `pct_chg` | Float64 |  |
| 4 | `open_num` | Int64 |  |
| 5 | `lu_desc` | String |  |
| 6 | `limit_type` | String |  |
| 7 | `tag` | String |  |
| 8 | `status` | String |  |
| 9 | `limit_order` | Float64 |  |
| 10 | `limit_amount` | Decimal(18, 2) |  |
| 11 | `lu_limit_order` | String |  |
| 12 | `limit_up_suc_rate` | Float64 |  |
| 13 | `turnover` | String |  |
| 14 | `market_type` | String |  |

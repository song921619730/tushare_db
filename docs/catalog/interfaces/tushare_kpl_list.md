# kpl_list

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | kpl_list |
| 表名 | `tushare_kpl_list` |
| 优先级 | P2 |
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
| 行数 | 68 |

## 字段列表 (25 个字段)

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
| 1 | `amount` | Float64 |  |
| 2 | `turnover_rate` | Float64 |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `free_float` | Float64 |  |

### 数值 (19个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `lu_time` | String |  |
| 3 | `ld_time` | String |  |
| 4 | `open_time` | String |  |
| 5 | `last_time` | String |  |
| 6 | `lu_desc` | String |  |
| 7 | `tag` | String |  |
| 8 | `theme` | String |  |
| 9 | `net_change` | Float64 |  |
| 10 | `bid_amount` | Decimal(18, 2) |  |
| 11 | `status` | String |  |
| 12 | `bid_change` | String |  |
| 13 | `bid_turnover` | String |  |
| 14 | `lu_bid_vol` | String |  |
| 15 | `pct_chg` | String |  |
| 16 | `bid_pct_chg` | String |  |
| 17 | `rt_pct_chg` | String |  |
| 18 | `limit_order` | Float64 |  |
| 19 | `lu_limit_order` | Float64 |  |

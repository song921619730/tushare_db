# moneyflow_dc

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | moneyflow_dc |
| 表名 | `tushare_moneyflow_dc` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | C |
| 采集策略 | offset_paging |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20230911 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 5,000 |

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

### 数值 (13个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `pct_change` | Float64 |  |
| 3 | `close` | Float64 |  |
| 4 | `net_amount` | Decimal(18, 2) |  |
| 5 | `net_amount_rate` | Float64 |  |
| 6 | `buy_elg_amount` | Decimal(18, 2) |  |
| 7 | `buy_elg_amount_rate` | Float64 |  |
| 8 | `buy_lg_amount` | Decimal(18, 2) |  |
| 9 | `buy_lg_amount_rate` | Float64 |  |
| 10 | `buy_md_amount` | Decimal(18, 2) |  |
| 11 | `buy_md_amount_rate` | Float64 |  |
| 12 | `buy_sm_amount` | Decimal(18, 2) |  |
| 13 | `buy_sm_amount_rate` | Float64 |  |

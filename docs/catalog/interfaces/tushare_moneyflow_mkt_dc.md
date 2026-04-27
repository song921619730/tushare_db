# moneyflow_mkt_dc

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | moneyflow_mkt_dc |
| 表名 | `tushare_moneyflow_mkt_dc` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | C |
| 采集策略 | offset_paging |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 1 |

## 字段列表 (16 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (14个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `close_sh` | Float64 |  |
| 2 | `pct_change_sh` | Float64 |  |
| 3 | `close_sz` | Float64 |  |
| 4 | `pct_change_sz` | Float64 |  |
| 5 | `net_amount` | Decimal(18, 2) |  |
| 6 | `net_amount_rate` | Float64 |  |
| 7 | `buy_elg_amount` | Decimal(18, 2) |  |
| 8 | `buy_elg_amount_rate` | Float64 |  |
| 9 | `buy_lg_amount` | Decimal(18, 2) |  |
| 10 | `buy_lg_amount_rate` | Float64 |  |
| 11 | `buy_md_amount` | Decimal(18, 2) |  |
| 12 | `buy_md_amount_rate` | Float64 |  |
| 13 | `buy_sm_amount` | Decimal(18, 2) |  |
| 14 | `buy_sm_amount_rate` | Float64 |  |

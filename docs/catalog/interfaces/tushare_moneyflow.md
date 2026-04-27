# moneyflow

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | moneyflow |
| 表名 | `tushare_moneyflow` |
| 优先级 | P1 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | B |
| 采集策略 | offset_paging |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 7,475,714 |

## 字段列表 (21 个字段)

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

### 数值 (18个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `buy_sm_vol` | Int64 |  |
| 2 | `buy_sm_amount` | Decimal(18, 2) |  |
| 3 | `sell_sm_vol` | Int64 |  |
| 4 | `sell_sm_amount` | Decimal(18, 2) |  |
| 5 | `buy_md_vol` | Int64 |  |
| 6 | `buy_md_amount` | Decimal(18, 2) |  |
| 7 | `sell_md_vol` | Int64 |  |
| 8 | `sell_md_amount` | Decimal(18, 2) |  |
| 9 | `buy_lg_vol` | Int64 |  |
| 10 | `buy_lg_amount` | Decimal(18, 2) |  |
| 11 | `sell_lg_vol` | Int64 |  |
| 12 | `sell_lg_amount` | Decimal(18, 2) |  |
| 13 | `buy_elg_vol` | Int64 |  |
| 14 | `buy_elg_amount` | Decimal(18, 2) |  |
| 15 | `sell_elg_vol` | Int64 |  |
| 16 | `sell_elg_amount` | Decimal(18, 2) |  |
| 17 | `net_mf_vol` | Int64 |  |
| 18 | `net_mf_amount` | Decimal(18, 2) |  |

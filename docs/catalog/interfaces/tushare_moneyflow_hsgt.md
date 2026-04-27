# moneyflow_hsgt

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | moneyflow_hsgt |
| 表名 | `tushare_moneyflow_hsgt` |
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
| 行数 | 350 |

## 字段列表 (8 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ggt_ss` | Nullable(Float64) |  |
| 2 | `ggt_sz` | Nullable(Float64) |  |
| 3 | `hgt` | Nullable(Float64) |  |
| 4 | `sgt` | String |  |
| 5 | `north_money` | Nullable(Float64) |  |
| 6 | `south_money` | Nullable(Float64) |  |

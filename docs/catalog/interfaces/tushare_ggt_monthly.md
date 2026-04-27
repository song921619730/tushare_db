# ggt_monthly

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ggt_monthly |
| 表名 | `tushare_ggt_monthly` |
| 优先级 | P3 |
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
| 行数 | 1 |

## 字段列表 (10 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 股本/市值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_buy_amt` | Float64 |  |
| 2 | `total_buy_vol` | Float64 |  |
| 3 | `total_sell_amt` | Float64 |  |
| 4 | `total_sell_vol` | Float64 |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `month` | String |  |
| 2 | `day_buy_amt` | Float64 |  |
| 3 | `day_buy_vol` | Float64 |  |
| 4 | `day_sell_amt` | Float64 |  |
| 5 | `day_sell_vol` | Float64 |  |

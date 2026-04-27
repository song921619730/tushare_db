# fut_weekly_detail

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fut_weekly_detail |
| 表名 | `tushare_fut_weekly_detail` |
| 优先级 | P3 |
| 模式 | incremental |
| 频率分桶 | normal |
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

## 字段列表 (18 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `week_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 增长率/同比 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol_yoy` | Float64 |  |
| 2 | `amout_yoy` | Float64 |  |
| 3 | `cumvol_yoy` | Float64 |  |
| 4 | `cumamt_yoy` | Float64 |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Int64 |  |
| 2 | `amount` | Float64 |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `cumvol` | Int64 |  |

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `exchange` | LowCardinality(String) |  |
| 2 | `prd` | String |  |
| 3 | `name` | LowCardinality(String) |  |
| 4 | `cumamt` | Float64 |  |
| 5 | `open_interest` | Int64 |  |
| 6 | `interest_wow` | Float64 |  |
| 7 | `mc_close` | Float64 |  |
| 8 | `close_wow` | Float64 |  |
| 9 | `week` | String |  |

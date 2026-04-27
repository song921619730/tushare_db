# top_inst

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | top_inst |
| 表名 | `tushare_top_inst` |
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
| 行数 | 95,907 |

## 字段列表 (11 个字段)

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

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `exalter` | String |  |
| 2 | `buy` | Float64 |  |
| 3 | `buy_rate` | Float64 |  |
| 4 | `sell` | Float64 |  |
| 5 | `sell_rate` | Float64 |  |
| 6 | `net_buy` | Float64 |  |
| 7 | `side` | String |  |
| 8 | `reason` | String |  |

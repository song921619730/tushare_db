# stk_nineturn

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | stk_nineturn |
| 表名 | `tushare_stk_nineturn` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | C |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20230101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 0 |

## 字段列表 (14 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | DateTime |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Float64 |  |
| 2 | `amount` | Float64 |  |

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `freq` | String |  |
| 2 | `open` | Float64 |  |
| 3 | `high` | Float64 |  |
| 4 | `low` | Float64 |  |
| 5 | `close` | Float64 |  |
| 6 | `up_count` | Float64 |  |
| 7 | `down_count` | Float64 |  |
| 8 | `nine_up_turn` | String |  |
| 9 | `nine_down_turn` | String |  |

# index_weekly

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | index_weekly |
| 表名 | `tushare_index_weekly` |
| 优先级 | P1 |
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
| 行数 | 1,000 |

## 字段列表 (12 个字段)

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
| 1 | `vol` | String |  |
| 2 | `amount` | String |  |

### 数值 (7个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `close` | Float64 |  |
| 2 | `open` | Float64 |  |
| 3 | `high` | Float64 |  |
| 4 | `low` | Float64 |  |
| 5 | `pre_close` | Float64 |  |
| 6 | `change` | Float64 |  |
| 7 | `pct_chg` | Float64 |  |

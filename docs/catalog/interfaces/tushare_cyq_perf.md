# cyq_perf

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cyq_perf |
| 表名 | `tushare_cyq_perf` |
| 优先级 | P1 |
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
| 行数 | 7,536,060 |

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

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `his_low` | Float64 |  |
| 2 | `his_high` | Float64 |  |
| 3 | `cost_5pct` | Float64 |  |
| 4 | `cost_15pct` | Float64 |  |
| 5 | `cost_50pct` | Float64 |  |
| 6 | `cost_85pct` | Float64 |  |
| 7 | `cost_95pct` | Float64 |  |
| 8 | `weight_avg` | Float64 |  |
| 9 | `winner_rate` | Float64 |  |

# ths_hot

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ths_hot |
| 表名 | `tushare_ths_hot` |
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
| 行数 | 0 |

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
| 1 | `data_type` | String |  |
| 2 | `ts_name` | String |  |
| 3 | `rank` | Int64 |  |
| 4 | `pct_change` | Float64 |  |
| 5 | `current_price` | Float64 |  |
| 6 | `hot` | Float64 |  |
| 7 | `concept` | String |  |
| 8 | `rank_time` | DateTime |  |
| 9 | `rank_reason` | String |  |

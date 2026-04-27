# top10_floatholders

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | top10_floatholders |
| 表名 | `tushare_top10_floatholders` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | saturday |
| 采集策略 | per_symbol_period |
| 排序键 | ts_code, end_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 117,503 |

## 字段列表 (10 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `end_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `hold_float_ratio` | Float64 |  |

### 比率/率 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `hold_ratio` | Float64 |  |

### 数值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `holder_name` | String |  |
| 2 | `hold_amount` | Decimal(18, 2) |  |
| 3 | `hold_change` | Float64 |  |
| 4 | `holder_type` | String |  |

# stk_holdertrade

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | stk_holdertrade |
| 表名 | `tushare_stk_holdertrade` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | saturday |
| 采集策略 | per_symbol_period |
| 排序键 | ts_code, ann_date |
| 分区键 | tuple() |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 22,012 |

## 字段列表 (12 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 股本/市值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `after_share` | Decimal(18, 4) |  |
| 2 | `total_share` | Decimal(18, 4) |  |

### 比率/率 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `change_ratio` | Float64 |  |
| 2 | `after_ratio` | Float64 |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `holder_name` | String |  |
| 2 | `holder_type` | String |  |
| 3 | `in_de` | String |  |
| 4 | `change_vol` | Float64 |  |
| 5 | `avg_price` | Float64 |  |

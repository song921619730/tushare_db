# share_float

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | share_float |
| 表名 | `tushare_share_float` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | B |
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

## 字段列表 (8 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `float_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 股本/市值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `float_share` | Decimal(18, 4) |  |
| 2 | `float_ratio` | Float64 |  |
| 3 | `share_type` | Nullable(String) |  |

### 数值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `holder_name` | Nullable(String) |  |

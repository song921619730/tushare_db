# margin_detail

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | margin_detail |
| 表名 | `tushare_margin_detail` |
| 优先级 | P1 |
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
| 行数 | 460,394 |

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
| 1 | `rzye` | Nullable(Float64) |  |
| 2 | `rqye` | Nullable(Float64) |  |
| 3 | `rzmre` | Nullable(Float64) |  |
| 4 | `rqyl` | Nullable(Float64) |  |
| 5 | `rzche` | Nullable(Float64) |  |
| 6 | `rqchl` | Nullable(Float64) |  |
| 7 | `rqmcl` | Nullable(Float64) |  |
| 8 | `rzrqye` | Nullable(Float64) |  |

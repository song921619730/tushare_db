# dc_index

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | dc_index |
| 表名 | `tushare_dc_index` |
| 优先级 | P1 |
| 模式 | full |
| 频率分桶 | special |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 1,018 |

## 字段列表 (14 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |
| 2 | `leading_code` | String |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 成交量/额 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `turnover_rate` | Float64 |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_mv` | Decimal(18, 2) |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `leading` | String |  |
| 3 | `pct_change` | Float64 |  |
| 4 | `leading_pct` | Float64 |  |
| 5 | `up_num` | Int64 |  |
| 6 | `down_num` | Int64 |  |
| 7 | `idx_type` | String |  |
| 8 | `level` | String |  |

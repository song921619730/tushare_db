# forecast

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | forecast |
| 表名 | `tushare_forecast` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | D |
| 采集策略 | period_loop |
| 日期字段 | end_date |
| 排序键 | ts_code, end_date |
| 分区键 | toYYYYMM(end_date) |
| 起始日期 | 20200101 |

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

### 日期 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `end_date` | Date |  |
| 3 | `first_ann_date` | Date |  |
| 4 | `update_flag` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `type` | String |  |
| 2 | `p_change_min` | Float64 |  |
| 3 | `p_change_max` | Float64 |  |
| 4 | `net_profit_min` | Float64 |  |
| 5 | `net_profit_max` | Float64 |  |
| 6 | `last_parent_net` | Float64 |  |
| 7 | `summary` | String |  |
| 8 | `change_reason` | String |  |

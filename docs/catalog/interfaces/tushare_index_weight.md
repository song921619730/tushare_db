# index_weight

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | index_weight |
| 表名 | `tushare_index_weight` |
| 优先级 | P1 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | A |
| 采集策略 | monthly_window |
| 排序键 | ts_code, cal_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 551,558 |

## 字段列表 (5 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `index_code` | String |  |
| 2 | `con_code` | String |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `weight` | Nullable(Float64) |  |

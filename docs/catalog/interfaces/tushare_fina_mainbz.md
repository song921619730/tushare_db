# fina_mainbz

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fina_mainbz |
| 表名 | `tushare_fina_mainbz` |
| 优先级 | P1 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | saturday |
| 采集策略 | per_symbol_period |
| 排序键 | ts_code, end_date |
| 分区键 | toYYYYMM(end_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 35,734 |

## 字段列表 (9 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |
| 2 | `bz_code` | String |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `end_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `bz_item` | String |  |
| 2 | `bz_sales` | Float64 |  |
| 3 | `bz_profit` | Decimal(18, 2) |  |
| 4 | `bz_cost` | Decimal(18, 2) |  |
| 5 | `curr_type` | String |  |

# dividend

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | dividend |
| 表名 | `tushare_dividend` |
| 优先级 | P1 |
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

## 字段列表 (15 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (7个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `end_date` | Date |  |
| 2 | `ann_date` | Date |  |
| 3 | `record_date` | Date |  |
| 4 | `ex_date` | Date |  |
| 5 | `pay_date` | Date |  |
| 6 | `div_listdate` | Date |  |
| 7 | `imp_ann_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `div_proc` | Nullable(String) |  |
| 2 | `stk_div` | Nullable(Float64) |  |
| 3 | `stk_bo_rate` | Nullable(Float64) |  |
| 4 | `stk_co_rate` | Nullable(Float64) |  |
| 5 | `cash_div` | Nullable(Float64) |  |
| 6 | `cash_div_tax` | Nullable(Float64) |  |

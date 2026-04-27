# fund_sales_ratio

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fund_sales_ratio |
| 表名 | `tushare_fund_sales_ratio` |
| 优先级 | P3 |
| 模式 | incremental |
| 频率分桶 | normal |
| 批次 | D |
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

## 字段列表 (7 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `year` | Int64 |  |
| 2 | `bank` | Float64 |  |
| 3 | `sec_comp` | Float64 |  |
| 4 | `fund_comp` | Float64 |  |
| 5 | `indep_comp` | Float64 |  |
| 6 | `rests` | Float64 |  |

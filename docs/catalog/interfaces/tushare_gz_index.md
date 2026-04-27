# gz_index

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | gz_index |
| 表名 | `tushare_gz_index` |
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

## 字段列表 (8 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `d10_rate` | Float64 |  |
| 2 | `m1_rate` | Float64 |  |
| 3 | `m3_rate` | Float64 |  |
| 4 | `m6_rate` | Float64 |  |
| 5 | `m12_rate` | Float64 |  |
| 6 | `long_rate` | Float64 |  |

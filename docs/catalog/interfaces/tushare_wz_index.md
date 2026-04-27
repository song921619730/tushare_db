# wz_index

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | wz_index |
| 表名 | `tushare_wz_index` |
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

## 字段列表 (14 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (12个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `comp_rate` | Float64 |  |
| 2 | `center_rate` | Float64 |  |
| 3 | `micro_rate` | Float64 |  |
| 4 | `cm_rate` | Float64 |  |
| 5 | `sdb_rate` | Float64 |  |
| 6 | `om_rate` | Float64 |  |
| 7 | `aa_rate` | Float64 |  |
| 8 | `m1_rate` | Float64 |  |
| 9 | `m3_rate` | Float64 |  |
| 10 | `m6_rate` | Float64 |  |
| 11 | `m12_rate` | Float64 |  |
| 12 | `long_rate` | Float64 |  |

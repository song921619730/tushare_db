# cn_pmi

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cn_pmi |
| 表名 | `tushare_cn_pmi` |
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
| 行数 | 0 |

## 字段列表 (66 个字段)

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `UPDATE_BY` | String |  |
| 2 | `UPDATE_TIME` | DateTime |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (63个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `PMI010700` | Float64 |  |
| 2 | `PMI010801` | Float64 |  |
| 3 | `PMI010803` | Float64 |  |
| 4 | `PMI011500` | Float64 |  |
| 5 | `PMI010703` | Float64 |  |
| 6 | `PMI011300` | Float64 |  |
| 7 | `PMI011700` | Float64 |  |
| 8 | `PMI020601` | Float64 |  |
| 9 | `CREATE_TIME` | DateTime |  |
| 10 | `PMI020300` | Float64 |  |
| 11 | `PMI020900` | Float64 |  |
| 12 | `PMI010100` | Float64 |  |
| 13 | `PMI010400` | Float64 |  |
| 14 | `PMI010402` | Float64 |  |
| 15 | `PMI010601` | Float64 |  |
| 16 | `PMI010503` | Float64 |  |
| 17 | `PMI011400` | Float64 |  |
| 18 | `PMI020302` | Float64 |  |
| 19 | `PMI020500` | Float64 |  |
| 20 | `PMI020502` | Float64 |  |
| 21 | `CREATE_BY` | String |  |
| 22 | `PMI020101` | Float64 |  |
| 23 | `PMI010403` | Float64 |  |
| 24 | `PMI020100` | Float64 |  |
| 25 | `PMI020602` | Float64 |  |
| 26 | `ID` | Int64 |  |
| 27 | `PMI010500` | Float64 |  |
| 28 | `PMI010603` | Float64 |  |
| 29 | `PMI020501` | Float64 |  |
| 30 | `PMI010501` | Float64 |  |
| 31 | `PMI010800` | Float64 |  |
| 32 | `PMI020200` | Float64 |  |
| 33 | `PMI010702` | Float64 |  |
| 34 | `PMI010802` | Float64 |  |
| 35 | `PMI020102` | Float64 |  |
| 36 | `PMI020202` | Float64 |  |
| 37 | `PMI020400` | Float64 |  |
| 38 | `PMI020401` | Float64 |  |
| 39 | `PMI021000` | Float64 |  |
| 40 | `PMI010401` | Float64 |  |
| 41 | `PMI010600` | Float64 |  |
| 42 | `PMI010701` | Float64 |  |
| 43 | `PMI010900` | Float64 |  |
| 44 | `PMI012000` | Float64 |  |
| 45 | `PMI020301` | Float64 |  |
| 46 | `MONTH` | String |  |
| 47 | `PMI011200` | Float64 |  |
| 48 | `PMI011600` | Float64 |  |
| 49 | `PMI010200` | Float64 |  |
| 50 | `PMI010602` | Float64 |  |
| 51 | `PMI011100` | Float64 |  |
| 52 | `PMI011800` | Float64 |  |
| 53 | `PMI011900` | Float64 |  |
| 54 | `PMI020402` | Float64 |  |
| 55 | `PMI020800` | Float64 |  |
| 56 | `PMI010000` | Float64 |  |
| 57 | `PMI010300` | Float64 |  |
| 58 | `PMI020201` | Float64 |  |
| 59 | `PMI030000` | Float64 |  |
| 60 | `PMI011000` | Float64 |  |
| 61 | `PMI020600` | Float64 |  |
| 62 | `PMI020700` | Float64 |  |
| 63 | `PMI010502` | Float64 |  |

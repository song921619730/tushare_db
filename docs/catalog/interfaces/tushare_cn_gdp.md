# cn_gdp

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cn_gdp |
| 表名 | `tushare_cn_gdp` |
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
| 行数 | 176 |

## 字段列表 (10 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 增长率/同比 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `gdp_yoy` | Nullable(Decimal(8, 2)) |  |
| 2 | `pi_yoy` | Nullable(Decimal(8, 2)) |  |
| 3 | `si_yoy` | Nullable(Decimal(8, 2)) |  |
| 4 | `ti_yoy` | Nullable(Decimal(8, 2)) |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `quarter` | String |  |
| 2 | `gdp` | Nullable(Decimal(18, 4)) |  |
| 3 | `pi` | Nullable(Decimal(18, 4)) |  |
| 4 | `si` | Nullable(Decimal(18, 4)) |  |
| 5 | `ti` | Nullable(Decimal(18, 4)) |  |

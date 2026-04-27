# margin

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | margin |
| 表名 | `tushare_margin` |
| 优先级 | P1 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | B |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 3,829 |

## 字段列表 (13 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 增长率/同比 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `rzye_yoy` | Nullable(Decimal(18, 4)) |  |
| 2 | `rqmcl_yoy` | Nullable(Decimal(18, 4)) |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `rqyl_total` | Nullable(Decimal(18, 4)) |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `exchange_id` | String |  |
| 2 | `rzye` | Nullable(Decimal(18, 4)) |  |
| 3 | `rqmcl` | Nullable(Decimal(18, 4)) |  |
| 4 | `rzmre` | Nullable(Decimal(18, 4)) |  |
| 5 | `rqyl` | Nullable(Decimal(18, 4)) |  |
| 6 | `rzche` | Nullable(Decimal(18, 4)) |  |
| 7 | `rqchl` | Nullable(Decimal(18, 4)) |  |
| 8 | `rzrqye` | Nullable(Decimal(18, 4)) |  |

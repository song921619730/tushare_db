# fut_settle

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fut_settle |
| 表名 | `tushare_fut_settle` |
| 优先级 | P3 |
| 模式 | incremental |
| 频率分桶 | normal |
| 批次 | A |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 870 |

## 字段列表 (11 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 比率/率 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `b_hedging_margin_rate` | Float64 |  |
| 2 | `s_hedging_margin_rate` | Float64 |  |
| 3 | `long_margin_rate` | Float64 |  |
| 4 | `short_margin_rate` | Float64 |  |

### 数值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `settle` | Float64 |  |
| 2 | `trading_fee_rate` | Float64 |  |
| 3 | `trading_fee` | Float64 |  |
| 4 | `delivery_fee` | Float64 |  |

# repurchase

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | repurchase |
| 表名 | `tushare_repurchase` |
| 优先级 | P2 |
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
| 行数 | 1 |

## 字段列表 (10 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `end_date` | Date |  |
| 3 | `exp_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Float64 |  |
| 2 | `amount` | Float64 |  |

### 数值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `proc` | String |  |
| 2 | `high_limit` | Float64 |  |
| 3 | `low_limit` | Float64 |  |

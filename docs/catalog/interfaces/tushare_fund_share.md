# fund_share

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fund_share |
| 表名 | `tushare_fund_share` |
| 优先级 | P2 |
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
| 行数 | 1,574 |

## 字段列表 (6 个字段)

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

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `fd_share` | Decimal(18, 4) |  |

### 数值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `fund_type` | String |  |
| 2 | `market` | LowCardinality(String) |  |

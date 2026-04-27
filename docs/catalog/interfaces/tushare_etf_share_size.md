# etf_share_size

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | etf_share_size |
| 表名 | `tushare_etf_share_size` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
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
| 行数 | 1,488 |

## 字段列表 (7 个字段)

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

### 股本/市值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_share` | Decimal(18, 4) |  |
| 2 | `total_size` | Float64 |  |

### 数值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `etf_name` | String |  |
| 2 | `exchange` | LowCardinality(String) |  |

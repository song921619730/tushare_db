# ft_limit

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ft_limit |
| 表名 | `tushare_ft_limit` |
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
| 行数 | 870 |

## 字段列表 (9 个字段)

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

### 比率/率 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `m_ratio` | Float64 |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `up_limit` | Float64 |  |
| 3 | `down_limit` | Float64 |  |
| 4 | `cont` | String |  |
| 5 | `exchange` | LowCardinality(String) |  |

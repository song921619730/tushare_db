# repo_daily

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | repo_daily |
| 表名 | `tushare_repo_daily` |
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
| 行数 | 44 |

## 字段列表 (13 个字段)

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

### 成交量/额 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `amount` | Float64 |  |

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `repo_maturity` | String |  |
| 2 | `pre_close` | Float64 |  |
| 3 | `open` | Float64 |  |
| 4 | `high` | Float64 |  |
| 5 | `low` | Float64 |  |
| 6 | `close` | Float64 |  |
| 7 | `weight` | Float64 |  |
| 8 | `weight_r` | Float64 |  |
| 9 | `num` | Int64 |  |

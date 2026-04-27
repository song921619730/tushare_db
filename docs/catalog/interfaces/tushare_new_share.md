# new_share

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | new_share |
| 表名 | `tushare_new_share` |
| 优先级 | P1 |
| 模式 | incremental |
| 频率分桶 | normal |
| 批次 | reference |
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

## 字段列表 (13 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |
| 2 | `sub_code` | String |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ipo_date` | Date |  |
| 2 | `issue_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 估值指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pe` | Float64 |  |

### 成交量/额 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `amount` | Float64 |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `market_amount` | Decimal(18, 2) |  |
| 3 | `price` | Float64 |  |
| 4 | `limit_amount` | Decimal(18, 2) |  |
| 5 | `funds` | Float64 |  |
| 6 | `ballot` | Float64 |  |

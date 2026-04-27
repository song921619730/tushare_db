# bak_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | bak_basic |
| 表名 | `tushare_bak_basic` |
| 优先级 | P3 |
| 模式 | full |
| 频率分桶 | special |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |
| 起始日期 | 20160101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 5,517 |

## 字段列表 (25 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |
| 2 | `list_date` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 估值指标 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pe` | Float64 |  |
| 2 | `pb` | Float64 |  |

### 增长率/同比 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `rev_yoy` | Float64 |  |
| 2 | `profit_yoy` | Float64 |  |

### 股本/市值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `float_share` | Decimal(18, 4) |  |
| 2 | `total_share` | Decimal(18, 4) |  |
| 3 | `total_assets` | Decimal(18, 2) |  |
| 4 | `reserved_pershare` | Float64 |  |

### 数值 (13个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `industry` | LowCardinality(String) |  |
| 3 | `area` | LowCardinality(String) |  |
| 4 | `liquid_assets` | Float64 |  |
| 5 | `fixed_assets` | Float64 |  |
| 6 | `reserved` | Float64 |  |
| 7 | `eps` | Float64 |  |
| 8 | `bvps` | Float64 |  |
| 9 | `undp` | Float64 |  |
| 10 | `per_undp` | Float64 |  |
| 11 | `gpr` | Float64 |  |
| 12 | `npr` | Float64 |  |
| 13 | `holder_num` | Int64 |  |

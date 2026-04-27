# tdx_index

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | tdx_index |
| 表名 | `tushare_tdx_index` |
| 优先级 | P2 |
| 模式 | full |
| 频率分桶 | special |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 481 |

## 字段列表 (10 个字段)

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

### 股本/市值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_share` | Decimal(18, 4) |  |
| 2 | `float_share` | Decimal(18, 4) |  |
| 3 | `total_mv` | Decimal(18, 2) |  |
| 4 | `float_mv` | Decimal(18, 2) |  |

### 数值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `idx_type` | String |  |
| 3 | `idx_count` | Int64 |  |

# ccass_hold_detail

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ccass_hold_detail |
| 表名 | `tushare_ccass_hold_detail` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | C |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 922 |

## 字段列表 (8 个字段)

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
| 1 | `col_shareholding` | String |  |
| 2 | `col_shareholding_percent` | String |  |

### 数值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `col_participant_id` | String |  |
| 3 | `col_participant_name` | String |  |

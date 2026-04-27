# report_rc

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | report_rc |
| 表名 | `tushare_report_rc` |
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
| 行数 | 1 |

## 字段列表 (22 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `report_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 估值指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pe` | Float64 |  |

### 回报指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `roe` | Float64 |  |

### 数值 (17个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `report_title` | String |  |
| 3 | `report_type` | String |  |
| 4 | `classify` | String |  |
| 5 | `org_name` | String |  |
| 6 | `author_name` | String |  |
| 7 | `quarter` | String |  |
| 8 | `op_rt` | Float64 |  |
| 9 | `op_pr` | Float64 |  |
| 10 | `tp` | Float64 |  |
| 11 | `np` | Float64 |  |
| 12 | `eps` | Float64 |  |
| 13 | `rd` | Float64 |  |
| 14 | `ev_ebitda` | Float64 |  |
| 15 | `rating` | String |  |
| 16 | `max_price` | Float64 |  |
| 17 | `min_price` | Float64 |  |

# fut_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fut_basic |
| 表名 | `tushare_fut_basic` |
| 优先级 | P2 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | toYYYYMM(trade_date) |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 20,000 |

## 字段列表 (16 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |
| 2 | `fut_code` | String |  |

### 日期 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `list_date` | Date |  |
| 2 | `delist_date` | Date |  |
| 3 | `last_ddate` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (10个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `symbol` | String |  |
| 2 | `exchange` | LowCardinality(String) |  |
| 3 | `name` | LowCardinality(String) |  |
| 4 | `multiplier` | Float64 |  |
| 5 | `trade_unit` | String |  |
| 6 | `per_unit` | Float64 |  |
| 7 | `quote_unit` | String |  |
| 8 | `quote_unit_desc` | String |  |
| 9 | `d_mode_desc` | String |  |
| 10 | `d_month` | String |  |

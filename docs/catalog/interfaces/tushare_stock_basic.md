# stock_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | stock_basic |
| 表名 | `tushare_stock_basic` |
| 优先级 | P0 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 11,020 |

## 字段列表 (11 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `list_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `symbol` | String |  |
| 2 | `name` | LowCardinality(String) |  |
| 3 | `area` | LowCardinality(String) |  |
| 4 | `industry` | LowCardinality(String) |  |
| 5 | `cnspell` | String |  |
| 6 | `market` | LowCardinality(String) |  |
| 7 | `act_name` | String |  |
| 8 | `act_ent_type` | String |  |

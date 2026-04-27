# sge_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | sge_basic |
| 表名 | `tushare_sge_basic` |
| 优先级 | P3 |
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
| 行数 | 26 |

## 字段列表 (15 个字段)

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

### 比率/率 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `margin_rate` | Float64 |  |

### 数值 (11个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_name` | String |  |
| 2 | `trade_type` | String |  |
| 3 | `t_unit` | Float64 |  |
| 4 | `p_unit` | Float64 |  |
| 5 | `min_change` | Float64 |  |
| 6 | `price_limit` | Float64 |  |
| 7 | `min_vol` | Int64 |  |
| 8 | `max_vol` | Int64 |  |
| 9 | `trade_mode` | String |  |
| 10 | `liq_rate` | Float64 |  |
| 11 | `trade_time` | String |  |

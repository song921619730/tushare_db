# ci_index_member

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ci_index_member |
| 表名 | `tushare_ci_index_member` |
| 优先级 | P2 |
| 模式 | full |
| 频率分桶 | special |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | toYYYYMM(trade_date) |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 5,000 |

## 字段列表 (12 个字段)

### 标识 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `l1_code` | String |  |
| 2 | `l2_code` | String |  |
| 3 | `l3_code` | String |  |
| 4 | `ts_code` | LowCardinality(String) |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `in_date` | Date |  |
| 2 | `out_date` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `l1_name` | String |  |
| 2 | `l2_name` | String |  |
| 3 | `l3_name` | String |  |
| 4 | `name` | LowCardinality(String) |  |
| 5 | `is_new` | String |  |

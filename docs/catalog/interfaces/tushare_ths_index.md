# ths_index

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ths_index |
| 表名 | `tushare_ths_index` |
| 优先级 | P1 |
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
| 行数 | 1,724 |

## 字段列表 (7 个字段)

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

### 数值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `count` | Int64 |  |
| 3 | `exchange` | LowCardinality(String) |  |
| 4 | `type` | String |  |

# stk_managers

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | stk_managers |
| 表名 | `tushare_stk_managers` |
| 优先级 | P1 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 0 |

## 字段列表 (12 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `begin_date` | Date |  |
| 3 | `end_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (7个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `gender` | String |  |
| 3 | `lev` | String |  |
| 4 | `title` | String |  |
| 5 | `edu` | String |  |
| 6 | `national` | String |  |
| 7 | `birthday` | String |  |

# stock_hsgt

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | stock_hsgt |
| 表名 | `tushare_stock_hsgt` |
| 优先级 | P1 |
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
| 行数 | 1,747 |

## 字段列表 (6 个字段)

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

### 数值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `type` | String |  |
| 2 | `name` | LowCardinality(String) |  |
| 3 | `type_name` | String |  |

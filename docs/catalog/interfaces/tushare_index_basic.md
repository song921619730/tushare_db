# index_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | index_basic |
| 表名 | `tushare_index_basic` |
| 优先级 | P0 |
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
| 行数 | 8,000 |

## 字段列表 (14 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | String |  |

### 日期 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `base_date` | Nullable(Date) |  |
| 2 | `list_date` | Nullable(Date) |  |
| 3 | `exp_date` | Nullable(Date) |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | Nullable(String) |  |
| 2 | `fullname` | Nullable(String) |  |
| 3 | `market` | Nullable(String) |  |
| 4 | `publisher` | Nullable(String) |  |
| 5 | `index_type` | Nullable(String) |  |
| 6 | `category` | Nullable(String) |  |
| 7 | `base_point` | Nullable(Decimal(12, 4)) |  |
| 8 | `weight_rule` | Nullable(String) |  |
| 9 | `description` | Nullable(String) |  |

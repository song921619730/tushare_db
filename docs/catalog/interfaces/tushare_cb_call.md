# cb_call

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cb_call |
| 表名 | `tushare_cb_call` |
| 优先级 | P3 |
| 模式 | incremental |
| 频率分桶 | normal |
| 批次 | A |
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

## 字段列表 (12 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `call_date` | Date |  |
| 3 | `payment_date` | Date |  |
| 4 | `call_reg_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `call_type` | String |  |
| 2 | `is_call` | String |  |
| 3 | `call_price` | Float64 |  |
| 4 | `call_price_tax` | Float64 |  |
| 5 | `call_vol` | Float64 |  |
| 6 | `call_amount` | Decimal(18, 2) |  |

# ggt_daily

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ggt_daily |
| 表名 | `tushare_ggt_daily` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
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

## 字段列表 (6 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `buy_amount` | Decimal(18, 2) |  |
| 2 | `buy_volume` | Float64 |  |
| 3 | `sell_amount` | Decimal(18, 2) |  |
| 4 | `sell_volume` | Float64 |  |

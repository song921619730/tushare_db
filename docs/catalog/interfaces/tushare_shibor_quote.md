# shibor_quote

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | shibor_quote |
| 表名 | `tushare_shibor_quote` |
| 优先级 | P3 |
| 模式 | incremental |
| 频率分桶 | normal |
| 批次 | D |
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

## 字段列表 (19 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (17个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `bank` | String |  |
| 2 | `on_b` | Float64 |  |
| 3 | `on_a` | Float64 |  |
| 4 | `1w_b` | Float64 |  |
| 5 | `1w_a` | Float64 |  |
| 6 | `2w_b` | Float64 |  |
| 7 | `2w_a` | Float64 |  |
| 8 | `1m_b` | Float64 |  |
| 9 | `1m_a` | Float64 |  |
| 10 | `3m_b` | Float64 |  |
| 11 | `3m_a` | Float64 |  |
| 12 | `6m_b` | Float64 |  |
| 13 | `6m_a` | Float64 |  |
| 14 | `9m_b` | Float64 |  |
| 15 | `9m_a` | Float64 |  |
| 16 | `1y_b` | Float64 |  |
| 17 | `1y_a` | Float64 |  |

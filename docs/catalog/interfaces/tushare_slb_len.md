# slb_len

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | slb_len |
| 表名 | `tushare_slb_len` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | B |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 0 |

## 字段列表 (7 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ob` | Float64 |  |
| 2 | `auc_amount` | Decimal(18, 2) |  |
| 3 | `repo_amount` | Decimal(18, 2) |  |
| 4 | `repay_amount` | Decimal(18, 2) |  |
| 5 | `cb` | Float64 |  |

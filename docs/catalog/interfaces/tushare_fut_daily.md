# fut_daily

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fut_daily |
| 表名 | `tushare_fut_daily` |
| 优先级 | P2 |
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
| 行数 | 2,000 |

## 字段列表 (16 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | String |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Nullable(Decimal(18, 2)) |  |
| 2 | `amount` | Nullable(Decimal(18, 3)) |  |

### 数值 (11个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pre_settle` | Nullable(Decimal(12, 4)) |  |
| 2 | `open` | Nullable(Decimal(12, 4)) |  |
| 3 | `high` | Nullable(Decimal(12, 4)) |  |
| 4 | `low` | Nullable(Decimal(12, 4)) |  |
| 5 | `close` | Nullable(Decimal(12, 4)) |  |
| 6 | `settle` | Nullable(Decimal(12, 4)) |  |
| 7 | `change1` | Nullable(Decimal(12, 4)) |  |
| 8 | `change2` | Nullable(Decimal(12, 4)) |  |
| 9 | `oi` | Nullable(Decimal(18, 2)) |  |
| 10 | `oi_chg` | Nullable(Decimal(18, 2)) |  |
| 11 | `delv_settle` | Nullable(Decimal(12, 4)) |  |

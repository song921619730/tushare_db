# hibor

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | hibor |
| 表名 | `tushare_hibor` |
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
| 行数 | 119 |

## 字段列表 (10 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `on` | Nullable(Decimal(18, 4)) |  |
| 2 | `1w` | Nullable(Decimal(18, 4)) |  |
| 3 | `2w` | Nullable(Decimal(18, 4)) |  |
| 4 | `1m` | Nullable(Decimal(18, 4)) |  |
| 5 | `2m` | Nullable(Decimal(18, 4)) |  |
| 6 | `3m` | Nullable(Decimal(18, 4)) |  |
| 7 | `6m` | Nullable(Decimal(18, 4)) |  |
| 8 | `1y` | Nullable(Decimal(18, 4)) |  |

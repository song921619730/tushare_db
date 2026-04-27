# cn_m

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cn_m |
| 表名 | `tushare_cn_m` |
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
| 行数 | 579 |

## 字段列表 (8 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 增长率/同比 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `m2_yoy` | Nullable(Decimal(8, 2)) |  |
| 2 | `m1_yoy` | Nullable(Decimal(8, 2)) |  |
| 3 | `m0_yoy` | Nullable(Decimal(8, 2)) |  |

### 数值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `month` | String |  |
| 2 | `m2` | Nullable(Decimal(18, 4)) |  |
| 3 | `m1` | Nullable(Decimal(18, 4)) |  |
| 4 | `m0` | Nullable(Decimal(18, 4)) |  |

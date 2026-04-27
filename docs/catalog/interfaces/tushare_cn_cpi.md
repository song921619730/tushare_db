# cn_cpi

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cn_cpi |
| 表名 | `tushare_cn_cpi` |
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
| 行数 | 507 |

## 字段列表 (5 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 增长率/同比 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `base_yoy` | Nullable(Decimal(18, 4)) |  |

### 数值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `month` | String |  |
| 2 | `cpi` | Nullable(Decimal(18, 4)) |  |
| 3 | `base_mom` | Nullable(Decimal(18, 4)) |  |

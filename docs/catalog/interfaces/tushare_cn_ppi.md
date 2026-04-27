# cn_ppi

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cn_ppi |
| 表名 | `tushare_cn_ppi` |
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
| 行数 | 414 |

## 字段列表 (5 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 增长率/同比 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ppi_yoy` | Nullable(Decimal(8, 2)) |  |

### 数值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `month` | String |  |
| 2 | `ppi` | Nullable(Decimal(8, 2)) |  |
| 3 | `ppi_mom` | Nullable(Decimal(8, 2)) |  |

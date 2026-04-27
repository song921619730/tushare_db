# trade_cal

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | trade_cal |
| 表名 | `tushare_trade_cal` |
| 优先级 | P0 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | exchange, cal_date |
| 分区键 | tuple() |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 13,162 |

## 字段列表 (5 个字段)

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `cal_date` | Date |  |
| 2 | `pretrade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `exchange` | LowCardinality(String) |  |
| 2 | `is_open` | Int64 |  |

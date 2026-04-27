# fut_holding

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fut_holding |
| 表名 | `tushare_fut_holding` |
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
| 行数 | 1 |

## 字段列表 (10 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 成交量/额 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Int64 |  |

### 数值 (7个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `symbol` | String |  |
| 2 | `broker` | String |  |
| 3 | `vol_chg` | Int64 |  |
| 4 | `long_hld` | Int64 |  |
| 5 | `long_chg` | Int64 |  |
| 6 | `short_hld` | Int64 |  |
| 7 | `short_chg` | Int64 |  |

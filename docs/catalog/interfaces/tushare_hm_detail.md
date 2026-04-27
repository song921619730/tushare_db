# hm_detail

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | hm_detail |
| 表名 | `tushare_hm_detail` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | C |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20220801 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 74 |

## 字段列表 (9 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_name` | String |  |
| 2 | `buy_amount` | Decimal(18, 2) |  |
| 3 | `sell_amount` | Decimal(18, 2) |  |
| 4 | `net_amount` | Decimal(18, 2) |  |
| 5 | `hm_name` | String |  |
| 6 | `hm_orgs` | String |  |

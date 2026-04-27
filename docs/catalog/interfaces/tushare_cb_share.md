# cb_share

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cb_share |
| 表名 | `tushare_cb_share` |
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
| 行数 | 0 |

## 字段列表 (16 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `publish_date` | Date |  |
| 2 | `end_date` | Date |  |

### 技术指标 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `remain_size` | Float64 |  |
| 2 | `_version` | UInt64 |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_shares` | Float64 |  |

### 比率/率 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `convert_ratio` | Float64 |  |
| 2 | `acc_convert_ratio` | Float64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `bond_short_name` | String |  |
| 2 | `issue_size` | Float64 |  |
| 3 | `convert_price_initial` | Float64 |  |
| 4 | `convert_price` | Float64 |  |
| 5 | `convert_val` | Float64 |  |
| 6 | `convert_vol` | Float64 |  |
| 7 | `acc_convert_val` | Float64 |  |
| 8 | `acc_convert_vol` | Float64 |  |

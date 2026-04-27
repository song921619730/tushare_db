# cb_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cb_basic |
| 表名 | `tushare_cb_basic` |
| 优先级 | P3 |
| 模式 | incremental |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 1,126 |

## 字段列表 (15 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | String |  |
| 2 | `stk_code` | Nullable(String) |  |

### 日期 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `list_date` | Nullable(Date) |  |
| 2 | `delist_date` | Nullable(Date) |  |
| 3 | `convert_start_date` | Nullable(Date) |  |
| 4 | `convert_end_date` | Nullable(Date) |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `bond_short_name` | Nullable(String) |  |
| 2 | `stk_name` | Nullable(String) |  |
| 3 | `issue_amount` | Nullable(Decimal(18, 4)) |  |
| 4 | `maturity` | Nullable(Decimal(5, 2)) |  |
| 5 | `coupon_rate` | Nullable(Decimal(6, 4)) |  |
| 6 | `turn_price` | Nullable(Decimal(10, 3)) |  |
| 7 | `convert_end_val` | Nullable(Decimal(10, 3)) |  |
| 8 | `rating` | Nullable(String) |  |

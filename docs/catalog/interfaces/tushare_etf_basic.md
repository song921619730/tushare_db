# etf_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | etf_basic |
| 表名 | `tushare_etf_basic` |
| 优先级 | P1 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | toYYYYMM(trade_date) |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 3,253 |

## 字段列表 (15 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | String |  |

### 日期 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `found_date` | Nullable(Date) |  |
| 2 | `due_date` | Nullable(Date) |  |
| 3 | `list_date` | Nullable(Date) |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (10个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | Nullable(String) |  |
| 2 | `management` | Nullable(String) |  |
| 3 | `custodian` | Nullable(String) |  |
| 4 | `fund_type` | Nullable(String) |  |
| 5 | `issue_amount` | Nullable(Decimal(18, 4)) |  |
| 6 | `m_fee` | Nullable(Decimal(6, 4)) |  |
| 7 | `c_fee` | Nullable(Decimal(6, 4)) |  |
| 8 | `benchmark` | Nullable(String) |  |
| 9 | `status` | Nullable(String) |  |
| 10 | `exchange` | Nullable(String) |  |

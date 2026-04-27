# fund_basic

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fund_basic |
| 表名 | `tushare_fund_basic` |
| 优先级 | P1 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 15,000 |

## 字段列表 (13 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | String |  |

### 日期 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `issue_date` | Nullable(Date) |  |
| 2 | `due_date` | Nullable(Date) |  |
| 3 | `list_date` | Nullable(Date) |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | Nullable(String) |  |
| 2 | `type` | Nullable(String) |  |
| 3 | `manager` | Nullable(String) |  |
| 4 | `issue_amount` | Nullable(Decimal(18, 4)) |  |
| 5 | `m_fee` | Nullable(Decimal(6, 4)) |  |
| 6 | `c_fee` | Nullable(Decimal(6, 4)) |  |
| 7 | `benchmark` | Nullable(String) |  |
| 8 | `status` | Nullable(String) |  |

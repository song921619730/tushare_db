# stock_company

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | stock_company |
| 表名 | `tushare_stock_company` |
| 优先级 | P0 |
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
| 行数 | 6,272 |

## 字段列表 (17 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | String |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `setup_date` | Nullable(Date) |  |

### 技术指标 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `email` | Nullable(String) |  |
| 2 | `_version` | UInt64 |  |

### 数值 (13个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `exchange` | Nullable(String) |  |
| 2 | `com_name` | Nullable(String) |  |
| 3 | `chairman` | Nullable(String) |  |
| 4 | `manager` | Nullable(String) |  |
| 5 | `secretary` | Nullable(String) |  |
| 6 | `reg_capital` | Nullable(Decimal(18, 4)) |  |
| 7 | `province` | Nullable(String) |  |
| 8 | `city` | Nullable(String) |  |
| 9 | `website` | Nullable(String) |  |
| 10 | `office` | Nullable(String) |  |
| 11 | `employees` | Nullable(Decimal(18, 2)) |  |
| 12 | `main_business` | Nullable(String) |  |
| 13 | `business_scope` | Nullable(String) |  |

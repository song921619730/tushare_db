# fund_company

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fund_company |
| 表名 | `tushare_fund_company` |
| 优先级 | P2 |
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
| 行数 | 0 |

## 字段列表 (18 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `org_code` | String |  |
| 2 | `credit_code` | String |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `setup_date` | Date |  |
| 2 | `end_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (13个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `shortname` | String |  |
| 3 | `province` | String |  |
| 4 | `city` | String |  |
| 5 | `address` | String |  |
| 6 | `phone` | String |  |
| 7 | `office` | String |  |
| 8 | `website` | String |  |
| 9 | `chairman` | String |  |
| 10 | `manager` | String |  |
| 11 | `reg_capital` | Float64 |  |
| 12 | `employees` | Float64 |  |
| 13 | `main_business` | String |  |

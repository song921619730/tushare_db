# stk_account_old

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | stk_account_old |
| 表名 | `tushare_stk_account_old` |
| 优先级 | P3 |
| 模式 | full |
| 频率分桶 | special |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |
| 起始日期 | 20080101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 1 |

## 字段列表 (10 个字段)

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `date` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 股本/市值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_sh` | Float64 |  |
| 2 | `total_sz` | Float64 |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `new_sh` | Int64 |  |
| 2 | `new_sz` | Int64 |  |
| 3 | `active_sh` | Float64 |  |
| 4 | `active_sz` | Float64 |  |
| 5 | `trade_sh` | Float64 |  |
| 6 | `trade_sz` | Float64 |  |

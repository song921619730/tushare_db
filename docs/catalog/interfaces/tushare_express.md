# express

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | express |
| 表名 | `tushare_express` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | D |
| 采集策略 | period_loop |
| 日期字段 | end_date |
| 排序键 | ts_code, end_date |
| 分区键 | toYYYYMM(end_date) |
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

### 日期 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `end_date` | Date |  |
| 3 | `update_flag` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 回报指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `diluted_roe` | Float64 |  |

### 增长率/同比 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `yoy_net_profit` | Decimal(18, 2) |  |

### 股本/市值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_profit` | Decimal(18, 2) |  |
| 2 | `total_assets` | Decimal(18, 2) |  |
| 3 | `total_hldr_eqy_exc_min_int` | Decimal(18, 2) |  |

### 数值 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `revenue` | Float64 |  |
| 2 | `operate_profit` | Decimal(18, 2) |  |
| 3 | `n_income` | Decimal(18, 2) |  |
| 4 | `diluted_eps` | Float64 |  |
| 5 | `bps` | String |  |
| 6 | `perf_summary` | String |  |

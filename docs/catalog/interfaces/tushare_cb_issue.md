# cb_issue

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cb_issue |
| 表名 | `tushare_cb_issue` |
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

## 字段列表 (24 个字段)

### 标识 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |
| 2 | `onl_code` | String |  |
| 3 | `shd_ration_code` | String |  |

### 日期 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `res_ann_date` | Date |  |
| 3 | `onl_date` | Date |  |
| 4 | `shd_ration_date` | Date |  |
| 5 | `shd_ration_record_date` | Date |  |
| 6 | `shd_ration_pay_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 比率/率 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `shd_ration_name` | String |  |
| 2 | `shd_ration_price` | Float64 |  |
| 3 | `shd_ration_ratio` | Float64 |  |
| 4 | `shd_ration_size` | Float64 |  |

### 数值 (10个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `plan_issue_size` | String |  |
| 2 | `issue_size` | Float64 |  |
| 3 | `issue_price` | Float64 |  |
| 4 | `issue_type` | String |  |
| 5 | `onl_name` | String |  |
| 6 | `onl_size` | Float64 |  |
| 7 | `onl_pch_vol` | Float64 |  |
| 8 | `onl_pch_num` | Int64 |  |
| 9 | `onl_pch_excess` | Float64 |  |
| 10 | `offl_size` | Float64 |  |
